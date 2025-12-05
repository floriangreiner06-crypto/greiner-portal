#!/usr/bin/env python3
"""
Werkstatt-Zeiten Sync Script
============================
Berechnet Leistungsgrade aus Locosoft-Daten

WICHTIG: 
- Verwendet v_times_clean (DISTINCT ohne order_position) um Duplikate zu eliminieren
- Verwendet order_number aus loco_labours (nicht aus loco_invoices!)
- Betrieb wird aus loco_employees geholt

Erstellt: 2025-12-04 (TAG 90)
Updated: 2025-12-04 - Betriebsfilter hinzugefügt
Läuft nach: locosoft_mirror (19:00)
Geplant: 19:15
"""

import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'


def ensure_view_exists(cursor):
    """Stellt sicher, dass die bereinigte View existiert (ohne Duplikate)"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='view' AND name='v_times_clean'
    """)
    if not cursor.fetchone():
        logger.info("Erstelle View v_times_clean...")
        cursor.execute("""
            CREATE VIEW v_times_clean AS
            SELECT DISTINCT 
                employee_number, 
                order_number, 
                start_time, 
                end_time, 
                duration_minutes
            FROM loco_times
            WHERE end_time IS NOT NULL
            AND duration_minutes > 0
            AND order_number >= 1000
        """)


def sync_werkstatt_zeiten():
    """Hauptfunktion: Synchronisiert Werkstatt-Leistungsdaten"""
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    logger.info("=" * 60)
    logger.info("WERKSTATT-ZEITEN SYNC gestartet")
    logger.info("=" * 60)
    
    try:
        # 1. View sicherstellen
        logger.info("[1/5] Prüfe View v_times_clean...")
        ensure_view_exists(cursor)
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM v_times_clean")
        logger.info(f"    Bereinigte Stempel-Einträge: {cursor.fetchone()[0]}")
        
        # 2. Stempelzeit pro Auftrag (ohne Sammelaufträge >100 Stempelungen)
        logger.info("[2/5] Berechne Stempelzeit pro Auftrag...")
        cursor.execute("""
            SELECT order_number, SUM(duration_minutes) as minuten
            FROM v_times_clean
            GROUP BY order_number
            HAVING COUNT(*) <= 100
        """)
        stempel_map = {r[0]: r[1] for r in cursor.fetchall()}
        logger.info(f"    Aufträge mit Stempelzeit: {len(stempel_map)}")
        
        # 3. Tabelle werkstatt_auftraege_abgerechnet
        logger.info("[3/5] Aktualisiere werkstatt_auftraege_abgerechnet...")
        cursor.execute("DROP TABLE IF EXISTS werkstatt_auftraege_abgerechnet")
        cursor.execute("""
            CREATE TABLE werkstatt_auftraege_abgerechnet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rechnungs_datum DATE,
                rechnungs_nr INTEGER,
                rechnungs_typ INTEGER,
                auftrags_nr INTEGER,
                betrieb INTEGER,
                kennzeichen TEXT,
                serviceberater_nr INTEGER,
                serviceberater_name TEXT,
                lohn_netto REAL DEFAULT 0,
                teile_netto REAL DEFAULT 0,
                gesamt_netto REAL DEFAULT 0,
                summe_aw REAL DEFAULT 0,
                summe_stempelzeit_min REAL DEFAULT 0,
                leistungsgrad REAL,
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
            WHERE i.invoice_date >= date('now', '-12 months')
            AND i.job_amount_net > 0
        """)
        rechnungen = cursor.fetchall()
        
        # AW und order_number aus labours (WICHTIG!)
        cursor.execute("""
            SELECT invoice_number, invoice_type, 
                   SUM(time_units) as aw,
                   MAX(order_number) as order_nr
            FROM loco_labours 
            WHERE is_invoiced = 1
            GROUP BY invoice_number, invoice_type
        """)
        labours_map = {(r[0], r[1]): (r[2], r[3]) for r in cursor.fetchall()}
        
        # Stammdaten
        cursor.execute("SELECT employee_number, name FROM loco_employees WHERE is_latest_record = 1")
        sb_namen = {r[0]: r[1] for r in cursor.fetchall()}
        
        cursor.execute("SELECT internal_number, license_plate FROM loco_vehicles")
        kfz_map = {r[0]: r[1] for r in cursor.fetchall()}
        
        insert_count = 0
        for r in rechnungen:
            rech_nr, rech_typ = r[1], r[2]
            
            labours_data = labours_map.get((rech_nr, rech_typ), (0, None))
            aw = labours_data[0] or 0
            auftr_nr = labours_data[1]
            
            if not auftr_nr or auftr_nr < 1000:
                continue
            
            stempel = stempel_map.get(auftr_nr, 0) or 0
            
            lg = None
            if stempel > 0 and aw > 0:
                lg = round((aw * 6) / stempel * 100, 1)
            
            cursor.execute("""
                INSERT OR IGNORE INTO werkstatt_auftraege_abgerechnet (
                    rechnungs_datum, rechnungs_nr, rechnungs_typ, auftrags_nr, betrieb,
                    kennzeichen, serviceberater_nr, serviceberater_name,
                    lohn_netto, teile_netto, gesamt_netto,
                    summe_aw, summe_stempelzeit_min, leistungsgrad, storniert
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                r[0], rech_nr, rech_typ, auftr_nr, r[3],
                kfz_map.get(r[4]), r[9], sb_namen.get(r[9]),
                r[5], r[6], r[7],
                aw, stempel, lg, 1 if r[8] else 0
            ))
            insert_count += 1
        
        conn.commit()
        logger.info(f"    Eingefügt: {insert_count} Rechnungen")
        
        # 4. Tabelle werkstatt_leistung_daily MIT BETRIEB
        logger.info("[4/5] Berechne Mechaniker-Tagesleistung...")
        cursor.execute("DROP TABLE IF EXISTS werkstatt_leistung_daily")
        cursor.execute("""
            CREATE TABLE werkstatt_leistung_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datum DATE,
                mechaniker_nr INTEGER,
                mechaniker_name TEXT,
                betrieb_nr INTEGER,
                ist_aktiv INTEGER DEFAULT 1,
                anzahl_auftraege INTEGER DEFAULT 0,
                vorgabezeit_aw REAL DEFAULT 0,
                stempelzeit_min REAL DEFAULT 0,
                anwesenheit_min REAL DEFAULT 0,
                leistungsgrad REAL,
                produktivitaet REAL,
                umsatz REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(datum, mechaniker_nr)
            )
        """)
        
        # Mitarbeiter-Betrieb Mapping aus loco_employees
        # NUR aktive Mitarbeiter (leave_date NULL oder in Zukunft)
        cursor.execute("""
            SELECT employee_number, subsidiary, leave_date
            FROM loco_employees 
            WHERE is_latest_record = 1
        """)
        emp_betrieb = {r[0]: r[1] for r in cursor.fetchall()}
        
        # Aktive Mitarbeiter (für Filterung)
        cursor.execute("""
            SELECT employee_number
            FROM loco_employees 
            WHERE is_latest_record = 1
            AND (leave_date IS NULL OR leave_date > date('now'))
        """)
        aktive_mitarbeiter = {r[0] for r in cursor.fetchall()}
        logger.info(f"    Aktive Mitarbeiter: {len(aktive_mitarbeiter)}")
        
        # Stempelzeit pro Tag/Mechaniker (Type 2 = produktive Auftragszeit, DISTINCT wg. Duplikaten)
        cursor.execute("""
            SELECT 
                DATE(start_time) as datum,
                employee_number,
                COUNT(DISTINCT order_number) as auftraege,
                SUM(duration_minutes) as stempel_min
            FROM v_times_clean
            WHERE start_time >= date('now', '-12 months')
            GROUP BY DATE(start_time), employee_number
        """)
        tages_stempel = {(r[0], r[1]): (r[2], r[3]) for r in cursor.fetchall()}
        
        # Anwesenheitszeit pro Tag/Mechaniker (Type 1 = Tages-Anwesenheit, nur 1 pro Tag)
        cursor.execute("""
            SELECT 
                DATE(start_time) as datum,
                employee_number,
                SUM(duration_minutes) as anwesenheit_min
            FROM loco_times
            WHERE type = 1
            AND end_time IS NOT NULL
            AND duration_minutes > 0
            AND start_time >= date('now', '-12 months')
            GROUP BY DATE(start_time), employee_number
        """)
        tages_anwesenheit = {(r[0], r[1]): r[2] for r in cursor.fetchall()}
        logger.info(f"    Anwesenheits-Einträge: {len(tages_anwesenheit)}")
        
        # AW pro Mechaniker/Tag
        cursor.execute("""
            SELECT 
                DATE(i.invoice_date) as datum,
                l.mechanic_no,
                SUM(l.time_units) as aw,
                SUM(l.net_price_in_order) as umsatz
            FROM loco_labours l
            JOIN loco_invoices i ON l.invoice_number = i.invoice_number AND l.invoice_type = i.invoice_type
            WHERE i.invoice_date >= date('now', '-12 months')
            AND l.is_invoiced = 1
            AND l.mechanic_no IS NOT NULL AND l.mechanic_no > 0
            GROUP BY DATE(i.invoice_date), l.mechanic_no
        """)
        mech_aw = {(r[0], r[1]): (r[2] or 0, r[3] or 0) for r in cursor.fetchall()}
        
        # Namen
        cursor.execute("SELECT employee_number, name FROM loco_employees WHERE is_latest_record = 1")
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
            
            # Produktivität: Stempelzeit / Anwesenheit * 100
            prod = None
            if anwesenheit and anwesenheit > 0 and stempel and stempel > 0:
                prod = round(stempel / anwesenheit * 100, 1)
            
            # Betrieb aus Mitarbeiter-Stammdaten
            betrieb = emp_betrieb.get(mech_nr)
            
            # Ist Mitarbeiter aktiv?
            ist_aktiv = 1 if mech_nr in aktive_mitarbeiter else 0
            
            cursor.execute("""
                INSERT OR IGNORE INTO werkstatt_leistung_daily (
                    datum, mechaniker_nr, mechaniker_name, betrieb_nr, ist_aktiv, anzahl_auftraege,
                    vorgabezeit_aw, stempelzeit_min, anwesenheit_min, leistungsgrad, produktivitaet, umsatz
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
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
            SELECT COUNT(*), ROUND(AVG(leistungsgrad),1)
            FROM werkstatt_auftraege_abgerechnet 
            WHERE leistungsgrad IS NOT NULL AND leistungsgrad > 0 AND leistungsgrad < 500
        """)
        r = cursor.fetchone()
        logger.info(f"\n✓ Aufträge mit Leistungsgrad: {r[0]}, Durchschnitt: {r[1]}%")
        
        cursor.execute("""
            SELECT COUNT(DISTINCT mechaniker_nr), ROUND(AVG(leistungsgrad),1)
            FROM werkstatt_leistung_daily 
            WHERE leistungsgrad IS NOT NULL AND leistungsgrad > 0 AND leistungsgrad < 500
        """)
        r = cursor.fetchone()
        logger.info(f"✓ Mechaniker: {r[0]}, Durchschnitt: {r[1]}%")
        
        # Betriebe zählen
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
