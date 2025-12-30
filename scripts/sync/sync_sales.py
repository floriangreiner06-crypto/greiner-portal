#!/usr/bin/env python3
"""
============================================================================
SALES-SYNC V5: Mit korrigierter Deckungsbeitrag-Berechnung (PostgreSQL)
============================================================================
Erstellt: 11.11.2025
Aktualisiert: 2025-12-23 (TAG 136 - PostgreSQL Migration)
Fix: calc_usage_value_encr_internal zum Einsatzwert addiert
Formel: (VK-Preis/1.19) - Einsatzwert - Var.Kosten + VKU
============================================================================
"""

import sys
import os
import psycopg2
from datetime import datetime

# Projekt-Pfad
sys.path.insert(0, '/opt/greiner-portal')

# =============================================================================
# KONFIGURATION
# =============================================================================

# Ziel-Datenbank (unsere PostgreSQL)
TARGET_DB_CONFIG = {
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
    TARGET_DB_CONFIG = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'drive_portal'),
        'user': os.getenv('DB_USER', 'drive_user'),
        'password': os.getenv('DB_PASSWORD', 'DrivePortal2024')
    }
except ImportError:
    pass


def log(message, level="INFO"):
    """Simple logging"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level:5}] {message}")

def load_env():
    """Liest .env Datei"""
    env = {}
    with open('/opt/greiner-portal/config/.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
    return env

def sync_sales():
    """Synchronisiert Sales von Locosoft nach PostgreSQL mit DB-Berechnung"""

    log("=== SALES SYNC V5 MIT DECKUNGSBEITRAG (PostgreSQL) ===")
    log("Fix TAG83: calc_usage_value_encr_internal zum Einsatzwert addiert")

    # 1. Credentials laden
    log("Lade Credentials...")
    env = load_env()

    loco_creds = {
        'host': env['LOCOSOFT_HOST'],
        'port': int(env['LOCOSOFT_PORT']),
        'database': env['LOCOSOFT_DATABASE'],
        'user': env['LOCOSOFT_USER'],
        'password': env['LOCOSOFT_PASSWORD']
    }

    # 2. Verbindungen oeffnen
    log(f"Verbinde zu Locosoft ({loco_creds['host']})...")
    loco_conn = psycopg2.connect(**loco_creds)
    loco_cursor = loco_conn.cursor()

    log(f"Verbinde zu Greiner Portal PostgreSQL ({TARGET_DB_CONFIG['host']})...")
    target_conn = psycopg2.connect(**TARGET_DB_CONFIG)
    target_cursor = target_conn.cursor()

    # 3. Sales aus Locosoft laden MIT DECKUNGSBEITRAG-KOMPONENTEN
    log("Lade Sales aus Locosoft (mit Deckungsbeitrag)...")
    loco_cursor.execute("""
        SELECT
            dv.dealer_vehicle_number,
            dv.dealer_vehicle_type,
            v.vin,
            dv.vehicle_number as internal_number,
            dv.out_invoice_date,
            dv.out_invoice_number::TEXT,
            dv.out_sale_price,
            dv.out_sale_type,
            dv.out_subsidiary,
            dv.out_sales_contract_date,
            dv.out_make_number,
            dv.mileage_km,
            dv.out_salesman_number_1,
            dv.buyer_customer_no::TEXT,
            m.description as model_description,

            -- Deckungsbeitrag-Komponenten
            COALESCE(dv.calc_basic_charge, 0) as fahrzeuggrundpreis,
            COALESCE(dv.calc_accessory, 0) as zubehoer,
            COALESCE(dv.calc_extra_expenses, 0) as fracht_brief_neben,
            COALESCE(dv.calc_cost_internal_invoices, 0) as kosten_intern_rg,

            -- NEU TAG83: Einsatzerhoehung interne Rechnungen
            COALESCE(dv.calc_usage_value_encr_internal, 0) as einsatz_erhoehung_intern,

            -- Verkaufsunterstuetzung (claimed = gefordert)
            COALESCE(
                (SELECT SUM(claimed_amount)
                 FROM public.dealer_sales_aid dsa
                 WHERE dsa.dealer_vehicle_type = dv.dealer_vehicle_type
                 AND dsa.dealer_vehicle_number = dv.dealer_vehicle_number),
                0
            ) as verkaufsunterstuetzung

        FROM dealer_vehicles dv
        LEFT JOIN vehicles v
            ON dv.dealer_vehicle_number = v.dealer_vehicle_number
            AND dv.dealer_vehicle_type = v.dealer_vehicle_type
        LEFT JOIN models m
            ON dv.out_model_code = m.model_code
            AND dv.out_make_number = m.make_number
        WHERE dv.out_sales_contract_date IS NOT NULL
          AND dv.out_sales_contract_date >= '2020-01-01'
          AND dv.out_sales_contract_date <= '2030-12-31'
        ORDER BY dv.out_sales_contract_date;
    """)

    sales = loco_cursor.fetchall()
    log(f"Gefunden: {len(sales)} Verkaeufe in Locosoft")

    # 4. Zaehler
    inserted = 0
    updated = 0
    errors = 0

    # 5. Sales synchronisieren
    log("Synchronisiere Sales mit Deckungsbeitrag-Berechnung...")
    for row in sales:
        try:
            (dealer_vehicle_number, dealer_vehicle_type, vin, internal_number,
             out_invoice_date, out_invoice_number, out_sale_price, out_sale_type,
             out_subsidiary, out_sales_contract_date, make_number, mileage_km,
             salesman_number, buyer_customer_no, model_description,
             fahrzeuggrundpreis, zubehoer, fracht_brief_neben,
             kosten_intern_rg, einsatz_erhoehung_intern, verkaufsunterstuetzung) = row

            # TAG 144: dealer_vehicle_number/type sind TEXT in unserer DB, aber INTEGER in Locosoft
            dealer_vehicle_number = str(dealer_vehicle_number) if dealer_vehicle_number else None
            dealer_vehicle_type = str(dealer_vehicle_type) if dealer_vehicle_type else None

            # Decimal-Werte zu float/int konvertieren
            out_sale_price = float(out_sale_price) if out_sale_price else None
            make_number = int(make_number) if make_number else None
            mileage_km = int(mileage_km) if mileage_km else None
            salesman_number = int(salesman_number) if salesman_number else None
            out_subsidiary = int(out_subsidiary) if out_subsidiary else None
            internal_number = int(internal_number) if internal_number else None

            # Deckungsbeitrag-Komponenten zu float
            fahrzeuggrundpreis = float(fahrzeuggrundpreis) if fahrzeuggrundpreis else 0.0
            zubehoer = float(zubehoer) if zubehoer else 0.0
            fracht_brief_neben = float(fracht_brief_neben) if fracht_brief_neben else 0.0
            kosten_intern_rg = float(kosten_intern_rg) if kosten_intern_rg else 0.0
            einsatz_erhoehung_intern = float(einsatz_erhoehung_intern) if einsatz_erhoehung_intern else 0.0
            verkaufsunterstuetzung = float(verkaufsunterstuetzung) if verkaufsunterstuetzung else 0.0

            # DECKUNGSBEITRAG BERECHNEN
            if out_sale_price and out_sale_price > 0:
                # Netto-VK-Preis (MwSt rausrechnen)
                netto_vk_preis = out_sale_price / 1.19

                # Einsatzwert (FIX TAG83: + einsatz_erhoehung_intern)
                einsatzwert = fahrzeuggrundpreis + zubehoer + fracht_brief_neben + einsatz_erhoehung_intern

                # Deckungsbeitrag
                deckungsbeitrag = netto_vk_preis - einsatzwert - kosten_intern_rg + verkaufsunterstuetzung

                # DB%
                db_prozent = (deckungsbeitrag / netto_vk_preis * 100) if netto_vk_preis > 0 else 0.0

                # Netto-Preis (fuer alte Kompatibilitaet)
                netto_price = netto_vk_preis
            else:
                netto_vk_preis = None
                deckungsbeitrag = None
                db_prozent = None
                netto_price = None

            # Pruefen ob existiert
            target_cursor.execute("""
                SELECT id FROM sales
                WHERE dealer_vehicle_number = %s
                  AND dealer_vehicle_type = %s
            """, (dealer_vehicle_number, dealer_vehicle_type))

            existing = target_cursor.fetchone()

            if existing:
                # UPDATE
                target_cursor.execute("""
                    UPDATE sales SET
                        vin = %s,
                        internal_number = %s,
                        out_invoice_date = %s,
                        out_invoice_number = %s,
                        out_sale_price = %s,
                        out_sale_type = %s,
                        out_subsidiary = %s,
                        out_sales_contract_date = %s,
                        make_number = %s,
                        model_description = %s,
                        mileage_km = %s,
                        salesman_number = %s,
                        buyer_customer_no = %s,
                        netto_price = %s,
                        netto_vk_preis = %s,
                        deckungsbeitrag = %s,
                        db_prozent = %s,
                        fahrzeuggrundpreis = %s,
                        zubehoer = %s,
                        fracht_brief_neben = %s,
                        kosten_intern_rg = %s,
                        verkaufsunterstuetzung = %s,
                        synced_at = CURRENT_TIMESTAMP
                    WHERE dealer_vehicle_number = %s
                      AND dealer_vehicle_type = %s
                """, (
                    vin, internal_number, out_invoice_date, out_invoice_number,
                    out_sale_price, out_sale_type, out_subsidiary, out_sales_contract_date,
                    make_number, model_description, mileage_km, salesman_number, buyer_customer_no,
                    netto_price, netto_vk_preis, deckungsbeitrag, db_prozent,
                    fahrzeuggrundpreis, zubehoer, fracht_brief_neben,
                    kosten_intern_rg, verkaufsunterstuetzung,
                    dealer_vehicle_number, dealer_vehicle_type
                ))
                updated += 1
            else:
                # INSERT
                target_cursor.execute("""
                    INSERT INTO sales (
                        dealer_vehicle_number, dealer_vehicle_type, vin, internal_number,
                        out_invoice_date, out_invoice_number, out_sale_price, out_sale_type,
                        out_subsidiary, out_sales_contract_date, make_number, model_description,
                        mileage_km, salesman_number, buyer_customer_no,
                        netto_price, netto_vk_preis, deckungsbeitrag, db_prozent,
                        fahrzeuggrundpreis, zubehoer, fracht_brief_neben,
                        kosten_intern_rg, verkaufsunterstuetzung, synced_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    dealer_vehicle_number, dealer_vehicle_type, vin, internal_number,
                    out_invoice_date, out_invoice_number, out_sale_price, out_sale_type,
                    out_subsidiary, out_sales_contract_date, make_number, model_description,
                    mileage_km, salesman_number, buyer_customer_no,
                    netto_price, netto_vk_preis, deckungsbeitrag, db_prozent,
                    fahrzeuggrundpreis, zubehoer, fracht_brief_neben,
                    kosten_intern_rg, verkaufsunterstuetzung
                ))
                inserted += 1

            # Commit alle 100 Zeilen
            if (inserted + updated) % 100 == 0:
                target_conn.commit()
                log(f"Fortschritt: {inserted} neu, {updated} aktualisiert")

        except Exception as e:
            log(f"Fehler bei {dealer_vehicle_number}/{dealer_vehicle_type}: {e}", "ERROR")
            errors += 1
            target_conn.rollback()
            if errors > 50:
                log("Zu viele Fehler - Abbruch!", "ERROR")
                break

    # 6. Final commit
    target_conn.commit()

    # 7. Statistik
    log("=== SYNC ABGESCHLOSSEN ===")
    log(f"Neu eingefuegt:  {inserted}")
    log(f"Aktualisiert:    {updated}")
    log(f"Fehler:          {errors}")

    # 8. Validierung
    target_cursor.execute("SELECT COUNT(*) FROM sales")
    total = target_cursor.fetchone()[0]
    log(f"Gesamt in DB:    {total}")

    # 9. Deckungsbeitrag-Check
    target_cursor.execute("""
        SELECT COUNT(*) FROM sales
        WHERE deckungsbeitrag IS NOT NULL
    """)
    mit_db = target_cursor.fetchone()[0]
    log(f"Mit Deckungsbeitrag: {mit_db}")

    # 10. Test: Fahrzeug 111186 pruefen (sollte jetzt 2231.34 zeigen)
    # TAG 144: dealer_vehicle_number ist TEXT, daher String-Vergleich
    target_cursor.execute("""
        SELECT deckungsbeitrag, db_prozent FROM sales
        WHERE dealer_vehicle_number = '111186'
    """)
    test_row = target_cursor.fetchone()
    if test_row:
        log(f"Test Fzg 111186: DB={test_row[0]:.2f} EUR | DB%={test_row[1]:.2f}%")

    # 11. Aufraeumen
    loco_conn.close()
    target_conn.close()

    log("Sync V5 mit korrigiertem Deckungsbeitrag erfolgreich beendet!")
    return inserted, updated, errors

if __name__ == '__main__':
    try:
        sync_sales()
    except Exception as e:
        log(f"KRITISCHER FEHLER: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
