#!/usr/bin/env python3
"""
============================================================================
SALES-SYNC V5: Mit korrigierter Deckungsbeitrag-Berechnung (Differenzmethode)
============================================================================
Erstellt: 11.11.2025
Aktualisiert: 28.11.2025 (TAG84)

FIX TAG84: Deckungsbeitrag-Berechnung korrigiert!
-------------------------------------------------
PROBLEM: Wir haben VK_brutto/1.19 gerechnet, aber Locosoft verwendet die
         Differenzmethode (§25a UStG für Gebrauchtwagen).

LOCOSOFT-FORMEL:
  Rohertrag_brutto = VK_brutto - Einsatzwert
  MwSt_auf_Rohertrag = Rohertrag_brutto / 1.19 * 0.19
  DB = Rohertrag_brutto - MwSt_auf_Rohertrag - var_kosten + VKU
  
  Vereinfacht: DB = (VK_brutto - Einsatzwert) / 1.19 - var_kosten + VKU

VORHER (FALSCH):
  DB = VK_brutto/1.19 - Einsatzwert - var_kosten + VKU  → NEGATIV
  
JETZT (KORREKT):
  DB = (VK_brutto - Einsatzwert) / 1.19 - var_kosten + VKU  → POSITIV ✓
============================================================================
"""

import sys
import psycopg2
import sqlite3
from datetime import datetime

def log(message, level="INFO"):
    """Simple logging"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level:5}] {message}")

def load_env():
    """Liest .env Datei"""
    env = {}
    with open('config/.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
    return env

def sync_sales():
    """Synchronisiert Sales von Locosoft nach SQLite mit DB-Berechnung"""

    log("=== SALES SYNC V5 MIT KORRIGIERTEM DECKUNGSBEITRAG (DIFFERENZMETHODE) ===")
    log("FIX TAG84: DB = (VK_brutto - Einsatz) / 1.19 - var_kosten + VKU")

    # 1. Credentials laden
    log("Lade Credentials...")
    env = load_env()

    pg_creds = {
        'host': env['LOCOSOFT_HOST'],
        'port': int(env['LOCOSOFT_PORT']),
        'database': env['LOCOSOFT_DATABASE'],
        'user': env['LOCOSOFT_USER'],
        'password': env['LOCOSOFT_PASSWORD']
    }

    sqlite_path = 'data/greiner_controlling.db'

    # 2. Verbindungen öffnen
    log(f"Verbinde zu Locosoft ({pg_creds['host']})...")
    pg_conn = psycopg2.connect(**pg_creds)
    pg_cursor = pg_conn.cursor()

    log(f"Verbinde zu SQLite ({sqlite_path})...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()

    # 3. Sales aus Locosoft laden MIT DECKUNGSBEITRAG-KOMPONENTEN
    log("Lade Sales aus Locosoft (mit Deckungsbeitrag)...")
    pg_cursor.execute("""
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
            
            -- Deckungsbeitrag-Komponenten (alle NETTO!)
            COALESCE(dv.calc_basic_charge, 0) as fahrzeuggrundpreis,
            COALESCE(dv.calc_accessory, 0) as zubehoer,
            COALESCE(dv.calc_extra_expenses, 0) as fracht_brief_neben,
            COALESCE(dv.calc_cost_internal_invoices, 0) as kosten_intern_rg,
            COALESCE(dv.calc_usage_value_encr_internal, 0) as einsatz_erhoehung_intern,
            
            -- Variable Verkaufskosten
            COALESCE(dv.calc_var_selling_costs, 0) as variable_verkaufskosten,
            
            -- Verkaufsunterstützung (claimed = gefordert)
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

    sales = pg_cursor.fetchall()
    log(f"Gefunden: {len(sales)} Verkäufe in Locosoft")

    # 4. Zähler
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
             kosten_intern_rg, einsatz_erhoehung_intern, 
             variable_verkaufskosten, verkaufsunterstuetzung) = row

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
            variable_verkaufskosten = float(variable_verkaufskosten) if variable_verkaufskosten else 0.0
            verkaufsunterstuetzung = float(verkaufsunterstuetzung) if verkaufsunterstuetzung else 0.0

            # ================================================================
            # DECKUNGSBEITRAG BERECHNEN - DIFFERENZMETHODE (wie Locosoft)
            # ================================================================
            if out_sale_price and out_sale_price > 0:
                # Einsatzwert (NETTO - ohne Steuer, wie im Locosoft-Screenshot)
                einsatzwert = (fahrzeuggrundpreis + zubehoer + fracht_brief_neben + 
                               einsatz_erhoehung_intern)
                
                # Rohertrag BRUTTO = VK_brutto - Einsatzwert_netto
                rohertrag_brutto = out_sale_price - einsatzwert
                
                # MwSt nur auf den Rohertrag (Differenzmethode §25a UStG)
                # rohertrag_brutto enthält 19% MwSt → Netto = brutto / 1.19
                rohertrag_netto = rohertrag_brutto / 1.19
                
                # Variable Kosten (Kosten interne RG + variable VK-Kosten)
                variable_kosten = kosten_intern_rg + variable_verkaufskosten
                
                # DECKUNGSBEITRAG I (wie in Locosoft)
                # = Rohertrag_netto - variable_kosten + Verkaufsunterstützung
                deckungsbeitrag = rohertrag_netto - variable_kosten + verkaufsunterstuetzung
                
                # DB% bezogen auf Netto-VK-Preis
                # Locosoft zeigt DB% = DB / (VK_brutto - MwSt_auf_Rohertrag)
                # Vereinfacht: DB% = DB / (Einsatz + Rohertrag_netto)
                netto_vk_preis = einsatzwert + rohertrag_netto
                db_prozent = (deckungsbeitrag / netto_vk_preis * 100) if netto_vk_preis > 0 else 0.0
                
                # Netto-Preis (für Kompatibilität)
                netto_price = out_sale_price / 1.19  # klassische Berechnung
            else:
                einsatzwert = None
                rohertrag_brutto = None
                rohertrag_netto = None
                deckungsbeitrag = None
                db_prozent = None
                netto_price = None
                netto_vk_preis = None

            # Prüfen ob existiert
            sqlite_cursor.execute("""
                SELECT id FROM sales
                WHERE dealer_vehicle_number = ?
                  AND dealer_vehicle_type = ?
            """, (dealer_vehicle_number, dealer_vehicle_type))

            existing = sqlite_cursor.fetchone()

            if existing:
                # UPDATE
                sqlite_cursor.execute("""
                    UPDATE sales SET
                        vin = ?,
                        internal_number = ?,
                        out_invoice_date = ?,
                        out_invoice_number = ?,
                        out_sale_price = ?,
                        out_sale_type = ?,
                        out_subsidiary = ?,
                        out_sales_contract_date = ?,
                        make_number = ?,
                        model_description = ?,
                        mileage_km = ?,
                        salesman_number = ?,
                        buyer_customer_no = ?,
                        netto_price = ?,
                        netto_vk_preis = ?,
                        deckungsbeitrag = ?,
                        db_prozent = ?,
                        fahrzeuggrundpreis = ?,
                        zubehoer = ?,
                        fracht_brief_neben = ?,
                        kosten_intern_rg = ?,
                        verkaufsunterstuetzung = ?,
                        synced_at = CURRENT_TIMESTAMP
                    WHERE dealer_vehicle_number = ?
                      AND dealer_vehicle_type = ?
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
                sqlite_cursor.execute("""
                    INSERT INTO sales (
                        dealer_vehicle_number, dealer_vehicle_type, vin, internal_number,
                        out_invoice_date, out_invoice_number, out_sale_price, out_sale_type,
                        out_subsidiary, out_sales_contract_date, make_number, model_description,
                        mileage_km, salesman_number, buyer_customer_no, 
                        netto_price, netto_vk_preis, deckungsbeitrag, db_prozent,
                        fahrzeuggrundpreis, zubehoer, fracht_brief_neben,
                        kosten_intern_rg, verkaufsunterstuetzung, synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
                sqlite_conn.commit()
                log(f"Fortschritt: {inserted} neu, {updated} aktualisiert")

        except Exception as e:
            log(f"Fehler bei {dealer_vehicle_number}/{dealer_vehicle_type}: {e}", "ERROR")
            errors += 1
            if errors > 50:
                log("Zu viele Fehler - Abbruch!", "ERROR")
                break

    # 6. Final commit
    sqlite_conn.commit()

    # 7. Statistik
    log("=== SYNC ABGESCHLOSSEN ===")
    log(f"Neu eingefügt:  {inserted}")
    log(f"Aktualisiert:    {updated}")
    log(f"Fehler:          {errors}")

    # 8. Validierung
    sqlite_cursor.execute("SELECT COUNT(*) FROM sales")
    total = sqlite_cursor.fetchone()[0]
    log(f"Gesamt in DB:    {total}")

    # 9. Deckungsbeitrag-Check
    sqlite_cursor.execute("""
        SELECT COUNT(*) FROM sales
        WHERE deckungsbeitrag IS NOT NULL
    """)
    mit_db = sqlite_cursor.fetchone()[0]
    log(f"Mit Deckungsbeitrag: {mit_db}")
    
    # 10. Test: Q5 Fahrzeug 215638 prüfen (sollte jetzt ~504.20 zeigen)
    sqlite_cursor.execute("""
        SELECT vin, out_sale_price, deckungsbeitrag, db_prozent 
        FROM sales
        WHERE dealer_vehicle_number = 215638
    """)
    test_row = sqlite_cursor.fetchone()
    if test_row:
        log(f"")
        log(f"=== VALIDIERUNG Q5 (215638) ===")
        log(f"VIN: {test_row[0]}")
        log(f"VK brutto: {test_row[1]:.2f}€")
        log(f"DB berechnet: {test_row[2]:.2f}€ | DB%: {test_row[3]:.2f}%")
        log(f"Erwartet (Locosoft): 504.20€ | 7.7%")
        
        # Check ob es passt
        if test_row[2] and abs(test_row[2] - 504.20) < 1:
            log(f"✅ VALIDIERUNG ERFOLGREICH!")
        else:
            log(f"⚠️ ABWEICHUNG - bitte prüfen!", "WARN")

    # 11. Aufräumen
    pg_conn.close()
    sqlite_conn.close()

    log("")
    log("✅ Sync V5 mit korrigiertem Deckungsbeitrag (Differenzmethode) beendet!")
    return inserted, updated, errors

if __name__ == '__main__':
    try:
        sync_sales()
    except Exception as e:
        log(f"KRITISCHER FEHLER: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
