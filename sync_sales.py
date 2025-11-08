#!/usr/bin/env python3
"""
============================================================================
SALES-SYNC: Locosoft PostgreSQL → SQLite
============================================================================
Erstellt: 08.11.2025
Zweck: Synchronisiert Verkaufsdaten aus Locosoft dealer_vehicles
Filter: Nur valide Daten (Datum zwischen 2020 und 2030)
============================================================================
"""

import sys
import psycopg2
import sqlite3
from datetime import datetime, date

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
    """Synchronisiert Sales von Locosoft nach SQLite"""
    
    log("=== SALES SYNC GESTARTET ===")
    
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
    
    # 3. Sales aus Locosoft laden
    log("Lade Sales aus Locosoft...")
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
            dv.buyer_customer_no::TEXT
        FROM dealer_vehicles dv
        LEFT JOIN vehicles v ON dv.dealer_vehicle_number = v.dealer_vehicle_number 
                             AND dv.dealer_vehicle_type = v.dealer_vehicle_type
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
    skipped = 0
    errors = 0
    
    # 5. Sales synchronisieren
    log("Synchronisiere Sales...")
    for row in sales:
        try:
            (dealer_vehicle_number, dealer_vehicle_type, vin, internal_number,
             out_invoice_date, out_invoice_number, out_sale_price, out_sale_type,
             out_subsidiary, out_sales_contract_date, make_number, mileage_km,
             salesman_number, buyer_customer_no) = row
            
            # ALLE Decimal-Werte zu float/int konvertieren (SQLite mag keine Decimals!)
            out_sale_price = float(out_sale_price) if out_sale_price else None
            make_number = int(make_number) if make_number else None
            mileage_km = int(mileage_km) if mileage_km else None
            salesman_number = int(salesman_number) if salesman_number else None
            out_subsidiary = int(out_subsidiary) if out_subsidiary else None
            internal_number = int(internal_number) if internal_number else None
            
            # Netto-Preis berechnen (Brutto / 1.19)
            netto_price = out_sale_price / 1.19 if out_sale_price else None
            
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
                        mileage_km = ?,
                        salesman_number = ?,
                        buyer_customer_no = ?,
                        netto_price = ?,
                        synced_at = CURRENT_TIMESTAMP
                    WHERE dealer_vehicle_number = ?
                      AND dealer_vehicle_type = ?
                """, (
                    vin, internal_number, out_invoice_date, out_invoice_number,
                    out_sale_price, out_sale_type, out_subsidiary, out_sales_contract_date,
                    make_number, mileage_km, salesman_number, buyer_customer_no,
                    netto_price, dealer_vehicle_number, dealer_vehicle_type
                ))
                updated += 1
            else:
                # INSERT
                sqlite_cursor.execute("""
                    INSERT INTO sales (
                        dealer_vehicle_number, dealer_vehicle_type, vin, internal_number,
                        out_invoice_date, out_invoice_number, out_sale_price, out_sale_type,
                        out_subsidiary, out_sales_contract_date, make_number, mileage_km,
                        salesman_number, buyer_customer_no, netto_price, synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    dealer_vehicle_number, dealer_vehicle_type, vin, internal_number,
                    out_invoice_date, out_invoice_number, out_sale_price, out_sale_type,
                    out_subsidiary, out_sales_contract_date, make_number, mileage_km,
                    salesman_number, buyer_customer_no, netto_price
                ))
                inserted += 1
            
            # Commit alle 100 Zeilen
            if (inserted + updated) % 100 == 0:
                sqlite_conn.commit()
                log(f"Fortschritt: {inserted} neu, {updated} aktualisiert")
        
        except Exception as e:
            log(f"Fehler bei {dealer_vehicle_number}/{dealer_vehicle_type}: {e}", "ERROR")
            errors += 1
            if errors > 50:  # Erhöht auf 50 Fehler
                log("Zu viele Fehler - Abbruch!", "ERROR")
                break
    
    # 6. Final commit
    sqlite_conn.commit()
    
    # 7. Statistik
    log("=== SYNC ABGESCHLOSSEN ===")
    log(f"Neu eingefügt:  {inserted}")
    log(f"Aktualisiert:    {updated}")
    log(f"Übersprungen:    {skipped}")
    log(f"Fehler:          {errors}")
    
    # 8. Validierung
    sqlite_cursor.execute("SELECT COUNT(*) FROM sales")
    total = sqlite_cursor.fetchone()[0]
    log(f"Gesamt in DB:    {total}")
    
    sqlite_cursor.execute("""
        SELECT COUNT(*) FROM sales 
        WHERE out_sales_contract_date >= '2025-11-01'
    """)
    nov = sqlite_cursor.fetchone()[0]
    log(f"November 2025:   {nov}")
    
    # 9. Aufräumen
    pg_conn.close()
    sqlite_conn.close()
    
    log("✅ Sync erfolgreich beendet!")
    return inserted, updated, errors

if __name__ == '__main__':
    try:
        sync_sales()
    except Exception as e:
        log(f"KRITISCHER FEHLER: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
