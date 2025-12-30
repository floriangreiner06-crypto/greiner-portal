#!/usr/bin/env python3
"""
Werkstatt-Zeiten Sync Script (PostgreSQL)
==========================================
Berechnet Leistungsgrade aus Locosoft-Daten

WICHTIG:
- Verwendet DISTINCT ON (PostgreSQL native) um Duplikate zu eliminieren
- Verwendet order_number aus loco_labours (nicht aus loco_invoices!)
- Betrieb wird aus loco_employees geholt

Erstellt: 2025-12-04 (TAG 90)
Updated: 2025-12-23 (TAG 136) - PostgreSQL Migration
Laeuft nach: locosoft_mirror (19:00)
Geplant: 19:15
"""

import os
import sys
import logging
from datetime import datetime

# Projekt-Pfad
sys.path.insert(0, '/opt/greiner-portal')

import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# KONFIGURATION
# =============================================================================

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'drive_portal',
    'user': 'drive_user',
    'password': 'DrivePortal2024'
}

# Versuche .env zu laden
try:
    from dotenv import load_dotenv
    load_dotenv('/opt/greiner-portal/config/.env')
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'drive_portal'),
        'user': os.getenv('DB_USER', 'drive_user'),
        'password': os.getenv('DB_PASSWORD', 'DrivePortal2024')
    }
except ImportError:
    pass


def ensure_view_exists(cursor):
    """Erstellt View v_times_clean (dedupliziert) - PostgreSQL Version

    WICHTIG: DISTINCT ON ist PostgreSQL-native Syntax!
    Gleicher Mechaniker + gleiche Start/Endzeit = 1 Stempelung
    (Locosoft erzeugt Duplikate wenn mehrere Positionen gestempelt werden)
    """
    cursor.execute("DROP VIEW IF EXISTS v_times_clean CASCADE")
    logger.info("Erstelle View v_times_clean (dedupliziert)...")
    cursor.execute("""
        CREATE OR REPLACE VIEW v_times_clean AS
        SELECT DISTINCT ON (employee_number, start_time, end_time)
            employee_number,
            order_number,
            start_time,
            end_time,
            duration_minutes
        FROM loco_times
        WHERE end_time IS NOT NULL
        AND duration_minutes > 0
        AND order_number >= 1000
        AND type = 2
        ORDER BY employee_number, start_time, end_time, order_number
    """)


def sync_werkstatt_zeiten():
    """Hauptfunktion: Synchronisiert Werkstatt-Leistungsdaten"""

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    logger.info("=" * 60)
    logger.info("WERKSTATT-ZEITEN SYNC (PostgreSQL)")
    logger.info(f"Datenbank: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    logger.info("=" * 60)

    try:
        # 1. View sicherstellen
        logger.info("[1/5] Pruefe View v_times_clean...")
        ensure_view_exists(cursor)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM v_times_clean")
        logger.info(f"    Bereinigte Stempel-Eintraege: {cursor.fetchone()[0]}")

        # 2. Stempelzeit pro Auftrag (ohne Sammelauftraege >100 Stempelungen)
        logger.info("[2/5] Berechne Stempelzeit pro Auftrag...")
        cursor.execute("""
            SELECT order_number, SUM(duration_minutes) as minuten
            FROM v_times_clean
            GROUP BY order_number
            HAVING COUNT(*) <= 100
        """)
        stempel_map = {r[0]: r[1] for r in cursor.fetchall()}
        logger.info(f"    Auftraege mit Stempelzeit: {len(stempel_map)}")

        # 3. Tabelle werkstatt_auftraege_abgerechnet
        logger.info("[3/5] Aktualisiere werkstatt_auftraege_abgerechnet...")
        cursor.execute("DROP TABLE IF EXISTS werkstatt_auftraege_abgerechnet CASCADE")
        cursor.execute("""
            CREATE TABLE werkstatt_auftraege_abgerechnet (
                id SERIAL PRIMARY KEY,
                rechnungs_datum DATE,
                rechnungs_nr INTEGER,
                rechnungs_typ INTEGER,
                auftrags_nr INTEGER,
                betrieb INTEGER,
                kennzeichen TEXT,
                serviceberater_nr INTEGER,
                serviceberater_name TEXT,
                lohn_netto NUMERIC(12,2) DEFAULT 0,
                teile_netto NUMERIC(12,2) DEFAULT 0,
                gesamt_netto NUMERIC(12,2) DEFAULT 0,
                summe_aw NUMERIC(12,2) DEFAULT 0,
                summe_stempelzeit_min NUMERIC(12,2) DEFAULT 0,
                leistungsgrad NUMERIC(8,2),
                storniert INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(rechnungs_nr, rechnungs_typ)
            )
        """)

        # Rechnungen laden
        cursor.execute("""
            SELECT
                i.invoice_date, i.invoice_number, i.invoice_type,
                i.subsidiary, i.vehicle_number,
                i.job_amount_net, i.part_amount_net, i.total_net, i.is_canceled,
                o.order_taking_employee_no
            FROM loco_invoices i
            LEFT JOIN loco_orders o ON i.order_number = o.number AND i.subsidiary = o.subsidiary
            WHERE i.invoice_date >= CURRENT_DATE - INTERVAL '12 months'
            AND i.job_amount_net > 0
        """)
        rechnungen = cursor.fetchall()

        # AW und order_number aus labours (WICHTIG!)
        cursor.execute("""
            SELECT invoice_number, invoice_type,
                   SUM(time_units) as aw,
                   MAX(order_number) as order_nr
            FROM loco_labours
            WHERE is_invoiced = true
            GROUP BY invoice_number, invoice_type
        """)
        labours_map = {(r[0], r[1]): (r[2], r[3]) for r in cursor.fetchall()}

        # Stammdaten
        cursor.execute("SELECT employee_number, name FROM loco_employees WHERE is_latest_record = true")
        sb_namen = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.execute("SELECT internal_number, license_plate FROM loco_vehicles")
        kfz_map = {r[0]: r[1] for r in cursor.fetchall()}

        insert_count = 0
        for r in rechnungen:
            rech_nr, rech_typ = r[1], r[2]

            labours_data = labours_map.get((rech_nr, rech_typ), (0, None))
            aw = float(labours_data[0] or 0)
            auftr_nr = labours_data[1]

            if not auftr_nr or auftr_nr < 1000:
                continue

            stempel = float(stempel_map.get(auftr_nr, 0) or 0)

            lg = None
            if stempel > 0 and aw > 0:
                lg = round((aw * 6) / stempel * 100, 1)

            cursor.execute("""
                INSERT INTO werkstatt_auftraege_abgerechnet (
                    rechnungs_datum, rechnungs_nr, rechnungs_typ, auftrags_nr, betrieb,
                    kennzeichen, serviceberater_nr, serviceberater_name,
                    lohn_netto, teile_netto, gesamt_netto,
                    summe_aw, summe_stempelzeit_min, leistungsgrad, storniert
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (rechnungs_nr, rechnungs_typ) DO NOTHING
            """, (
                r[0], rech_nr, rech_typ, auftr_nr, r[3],
                kfz_map.get(r[4]), r[9], sb_namen.get(r[9]),
                r[5], r[6], r[7],
                aw, stempel, lg, 1 if r[8] else 0
            ))
            insert_count += 1

        conn.commit()
        logger.info(f"    Eingefuegt: {insert_count} Rechnungen")

        # 4. Tabelle werkstatt_leistung_daily MIT BETRIEB
        logger.info("[4/5] Berechne Mechaniker-Tagesleistung...")
        cursor.execute("DROP TABLE IF EXISTS werkstatt_leistung_daily CASCADE")
        cursor.execute("""
            CREATE TABLE werkstatt_leistung_daily (
                id SERIAL PRIMARY KEY,
                datum DATE,
                mechaniker_nr INTEGER,
                mechaniker_name TEXT,
                betrieb_nr INTEGER,
                ist_aktiv INTEGER DEFAULT 1,
                anzahl_auftraege INTEGER DEFAULT 0,
                vorgabezeit_aw NUMERIC(12,2) DEFAULT 0,
                stempelzeit_min NUMERIC(12,2) DEFAULT 0,
                anwesenheit_min NUMERIC(12,2) DEFAULT 0,
                leistungsgrad NUMERIC(8,2),
                produktivitaet NUMERIC(8,2),
                umsatz NUMERIC(12,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(datum, mechaniker_nr)
            )
        """)

        # Mitarbeiter-Betrieb Mapping aus loco_employees
        cursor.execute("""
            SELECT employee_number, subsidiary, leave_date
            FROM loco_employees
            WHERE is_latest_record = true
        """)
        emp_betrieb = {r[0]: r[1] for r in cursor.fetchall()}

        # Aktive Mitarbeiter (fuer Filterung)
        cursor.execute("""
            SELECT employee_number
            FROM loco_employees
            WHERE is_latest_record = true
            AND (leave_date IS NULL OR leave_date > CURRENT_DATE)
        """)
        aktive_mitarbeiter = {r[0] for r in cursor.fetchall()}
        logger.info(f"    Aktive Mitarbeiter: {len(aktive_mitarbeiter)}")

        # Stempelzeit pro Tag/Mechaniker
        cursor.execute("""
            SELECT
                DATE(start_time) as datum,
                employee_number,
                COUNT(DISTINCT order_number) as auftraege,
                SUM(duration_minutes) as stempel_min
            FROM v_times_clean
            WHERE start_time >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY DATE(start_time), employee_number
        """)
        tages_stempel = {(str(r[0]), r[1]): (r[2], float(r[3] or 0)) for r in cursor.fetchall()}

        # Anwesenheitszeit pro Tag/Mechaniker (Type 1 = Tages-Anwesenheit)
        cursor.execute("""
            SELECT
                DATE(start_time) as datum,
                employee_number,
                SUM(duration_minutes) as anwesenheit_min
            FROM loco_times
            WHERE type = 1
            AND end_time IS NOT NULL
            AND duration_minutes > 0
            AND start_time >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY DATE(start_time), employee_number
        """)
        tages_anwesenheit = {(str(r[0]), r[1]): float(r[2] or 0) for r in cursor.fetchall()}
        logger.info(f"    Anwesenheits-Eintraege: {len(tages_anwesenheit)}")

        # AW pro Mechaniker/Tag
        cursor.execute("""
            SELECT
                DATE(i.invoice_date) as datum,
                l.mechanic_no,
                SUM(l.time_units) as aw,
                SUM(l.net_price_in_order) as umsatz
            FROM loco_labours l
            JOIN loco_invoices i ON l.invoice_number = i.invoice_number AND l.invoice_type = i.invoice_type
            WHERE i.invoice_date >= CURRENT_DATE - INTERVAL '12 months'
            AND l.is_invoiced = true
            AND l.mechanic_no IS NOT NULL AND l.mechanic_no > 0
            GROUP BY DATE(i.invoice_date), l.mechanic_no
        """)
        mech_aw = {(str(r[0]), r[1]): (float(r[2] or 0), float(r[3] or 0)) for r in cursor.fetchall()}

        # Namen
        cursor.execute("SELECT employee_number, name FROM loco_employees WHERE is_latest_record = true")
        emp_namen = {r[0]: r[1] for r in cursor.fetchall()}

        alle_keys = set(tages_stempel.keys()) | set(mech_aw.keys()) | set(tages_anwesenheit.keys())
        for datum, mech_nr in alle_keys:
            auftraege, stempel = tages_stempel.get((datum, mech_nr), (0, 0))
            aw, umsatz = mech_aw.get((datum, mech_nr), (0, 0))
            anwesenheit = tages_anwesenheit.get((datum, mech_nr), 0)

            if not stempel and not aw and not anwesenheit:
                continue

            # Leistungsgrad: AW*6 / Stempelzeit * 100
            lg = None
            if stempel and stempel > 0 and aw > 0:
                lg = round((aw * 6) / stempel * 100, 1)

            # Produktivitaet: Stempelzeit / Anwesenheit * 100
            prod = None
            if anwesenheit and anwesenheit > 0 and stempel and stempel > 0:
                prod = round(stempel / anwesenheit * 100, 1)

            # Betrieb aus Mitarbeiter-Stammdaten
            betrieb = emp_betrieb.get(mech_nr)

            # Ist Mitarbeiter aktiv?
            ist_aktiv = 1 if mech_nr in aktive_mitarbeiter else 0

            cursor.execute("""
                INSERT INTO werkstatt_leistung_daily (
                    datum, mechaniker_nr, mechaniker_name, betrieb_nr, ist_aktiv, anzahl_auftraege,
                    vorgabezeit_aw, stempelzeit_min, anwesenheit_min, leistungsgrad, produktivitaet, umsatz
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (datum, mechaniker_nr) DO NOTHING
            """, (datum, mech_nr, emp_namen.get(mech_nr), betrieb, ist_aktiv, auftraege, aw, stempel, anwesenheit, lg, prod, umsatz))

        conn.commit()

        # 5. Indizes
        logger.info("[5/5] Erstelle Indizes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_waa_datum ON werkstatt_auftraege_abgerechnet(rechnungs_datum)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_waa_betrieb ON werkstatt_auftraege_abgerechnet(betrieb)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wld_datum ON werkstatt_leistung_daily(datum)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wld_mech ON werkstatt_leistung_daily(mechaniker_nr)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wld_betrieb ON werkstatt_leistung_daily(betrieb_nr)")
        conn.commit()

        # Statistik
        cursor.execute("""
            SELECT COUNT(*), ROUND(AVG(leistungsgrad)::numeric,1)
            FROM werkstatt_auftraege_abgerechnet
            WHERE leistungsgrad IS NOT NULL AND leistungsgrad > 0 AND leistungsgrad < 500
        """)
        r = cursor.fetchone()
        logger.info(f"\nAuftraege mit Leistungsgrad: {r[0]}, Durchschnitt: {r[1]}%")

        cursor.execute("""
            SELECT COUNT(DISTINCT mechaniker_nr), ROUND(AVG(leistungsgrad)::numeric,1)
            FROM werkstatt_leistung_daily
            WHERE leistungsgrad IS NOT NULL AND leistungsgrad > 0 AND leistungsgrad < 500
        """)
        r = cursor.fetchone()
        logger.info(f"Mechaniker: {r[0]}, Durchschnitt: {r[1]}%")

        # Betriebe zaehlen
        cursor.execute("""
            SELECT betrieb_nr, COUNT(DISTINCT mechaniker_nr)
            FROM werkstatt_leistung_daily
            WHERE betrieb_nr IS NOT NULL
            GROUP BY betrieb_nr
        """)
        for r in cursor.fetchall():
            logger.info(f"  Betrieb {r[0]}: {r[1]} Mechaniker")

        logger.info("\n" + "=" * 60)
        logger.info("WERKSTATT-ZEITEN SYNC abgeschlossen")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fehler: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    sync_werkstatt_zeiten()
