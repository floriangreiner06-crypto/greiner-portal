#!/usr/bin/env python3
"""
VERKAUFS-DUPLIKATE CHECKER
==========================
Analysiert die sales-Tabelle auf mögliche Duplikate

Autor: Claude
Datum: 11.11.2025
"""

import sqlite3
import sys
from datetime import datetime
from collections import defaultdict

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

def connect_db():
    """Verbindung zur Datenbank herstellen"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Fehler bei DB-Verbindung: {e}")
        sys.exit(1)

def print_header(title):
    """Schöner Header für Ausgaben"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def check_1_corsa_duplikate(conn):
    """Check 1: Spezifischer Corsa-Check für Anton Süß"""
    print_header("CHECK 1: Corsa-Duplikate (Anton Süß, November 2025)")
    
    query = """
    SELECT 
        s.id,
        s.salesman_number,
        s.dealer_vehicle_type,
        s.model_description,
        s.out_sales_contract_date,
        s.out_invoice_date,
        s.price,
        s.commission_num
    FROM sales s
    WHERE s.model_description LIKE '%Corsa%'
        AND s.model_description LIKE '%1.2%'
        AND s.model_description LIKE '%Direct Injection Turbo%'
        AND s.salesman_number = '2003'
        AND strftime('%Y', s.out_sales_contract_date) = '2025'
        AND strftime('%m', s.out_sales_contract_date) = '11'
    ORDER BY s.out_sales_contract_date, s.id
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("✅ Keine Corsa-Einträge gefunden für Anton Süß im November 2025")
        return
    
    print(f"📊 Gefunden: {len(rows)} Corsa-Einträge\n")
    
    for row in rows:
        type_label = {
            'N': '🆕 Neuwagen',
            'T': '🧪 Testfahrzeug',
            'V': '🚗 Vorführwagen',
            'G': '♻️  Gebraucht',
            'D': '🔄 Gebraucht (Demo)'
        }.get(row['dealer_vehicle_type'], f"❓ {row['dealer_vehicle_type']}")
        
        print(f"ID: {row['id']}")
        print(f"  Typ: {type_label}")
        print(f"  Modell: {row['model_description']}")
        print(f"  Vertragsdatum: {row['out_sales_contract_date']}")
        print(f"  Rechnungsdatum: {row['out_invoice_date']}")
        print(f"  Preis: {row['price']:,.2f} EUR")
        print(f"  Provision: {row['commission_num']}")
        print()
    
    if len(rows) > 1:
        print("⚠️  WARNUNG: Mehrere Einträge gefunden!")
        print("   → Möglicherweise Duplikat!\n")

def check_2_exact_duplicates(conn):
    """Check 2: Exakte Duplikate (gleiche Felder)"""
    print_header("CHECK 2: Exakte Duplikate")
    
    query = """
    SELECT 
        model_description,
        salesman_number,
        out_sales_contract_date,
        dealer_vehicle_type,
        price,
        COUNT(*) as anzahl,
        GROUP_CONCAT(id) as ids
    FROM sales
    WHERE out_sales_contract_date IS NOT NULL
    GROUP BY 
        model_description,
        salesman_number,
        out_sales_contract_date,
        dealer_vehicle_type,
        price
    HAVING COUNT(*) > 1
    ORDER BY anzahl DESC, out_sales_contract_date DESC
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("✅ Keine exakten Duplikate gefunden!\n")
        return
    
    print(f"⚠️  {len(rows)} Duplikate gefunden!\n")
    
    total_dupes = 0
    for row in rows:
        ids = row['ids'].split(',')
        dupe_count = len(ids) - 1
        total_dupes += dupe_count
        
        print(f"📍 {row['anzahl']}x identisch:")
        print(f"   IDs: {row['ids']}")
        print(f"   Modell: {row['model_description'][:60]}...")
        print(f"   Verkäufer: {row['salesman_number']}")
        print(f"   Datum: {row['out_sales_contract_date']}")
        print(f"   Typ: {row['dealer_vehicle_type']}")
        print(f"   Preis: {row['price']:,.2f} EUR")
        print()
    
    print(f"📊 ZUSAMMENFASSUNG:")
    print(f"   Duplikate-Gruppen: {len(rows)}")
    print(f"   Überschüssige Einträge: {total_dupes}")
    print()

def check_3_same_model_same_day(conn):
    """Check 3: Gleiches Modell am gleichen Tag (unterschiedlicher Typ)"""
    print_header("CHECK 3: Gleiches Modell, gleicher Tag, unterschiedlicher Typ")
    
    query = """
    WITH model_counts AS (
        SELECT 
            model_description,
            salesman_number,
            out_sales_contract_date,
            COUNT(DISTINCT dealer_vehicle_type) as type_count,
            COUNT(*) as total_count,
            GROUP_CONCAT(DISTINCT dealer_vehicle_type) as types,
            GROUP_CONCAT(id) as ids,
            GROUP_CONCAT(price) as prices
        FROM sales
        WHERE out_sales_contract_date IS NOT NULL
        GROUP BY 
            model_description,
            salesman_number,
            out_sales_contract_date
        HAVING type_count > 1
    )
    SELECT * FROM model_counts
    ORDER BY out_sales_contract_date DESC
    LIMIT 20
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("✅ Keine verdächtigen Einträge (gleiches Modell, unterschiedlicher Typ)\n")
        return
    
    print(f"⚠️  {len(rows)} verdächtige Fälle gefunden!\n")
    
    for i, row in enumerate(rows, 1):
        print(f"🔍 Fall {i}:")
        print(f"   Modell: {row['model_description'][:60]}...")
        print(f"   Verkäufer: {row['salesman_number']}")
        print(f"   Datum: {row['out_sales_contract_date']}")
        print(f"   Typen: {row['types']} (unterschiedliche Kategorien!)")
        print(f"   IDs: {row['ids']}")
        print(f"   Preise: {row['prices']}")
        print()
    
    print(f"⚠️  Diese Fälle könnten DUPLIKATE sein!")
    print(f"   → Gleiches Fahrzeug wurde mit unterschiedlichen Typen erfasst\n")

def check_4_november_stats(conn):
    """Check 4: November 2025 Statistik"""
    print_header("CHECK 4: November 2025 - Verkaufsstatistik")
    
    # Gesamtstatistik
    query_total = """
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT salesman_number) as verkaufer_count,
        SUM(CASE WHEN dealer_vehicle_type = 'N' THEN 1 ELSE 0 END) as neuwagen,
        SUM(CASE WHEN dealer_vehicle_type IN ('T', 'V') THEN 1 ELSE 0 END) as test_vorfuehr,
        SUM(CASE WHEN dealer_vehicle_type IN ('G', 'D') THEN 1 ELSE 0 END) as gebraucht
    FROM sales
    WHERE strftime('%Y', out_sales_contract_date) = '2025'
        AND strftime('%m', out_sales_contract_date) = '11'
    """
    
    cursor = conn.cursor()
    cursor.execute(query_total)
    stats = cursor.fetchone()
    
    print(f"📊 GESAMT November 2025:")
    print(f"   Total Verkäufe: {stats['total']}")
    print(f"   Verkäufer: {stats['verkaufer_count']}")
    print(f"   └─ Neuwagen: {stats['neuwagen']}")
    print(f"   └─ Test/Vorführ: {stats['test_vorfuehr']}")
    print(f"   └─ Gebraucht: {stats['gebraucht']}")
    print()
    
    # Pro Verkäufer
    query_per_salesman = """
    SELECT 
        s.salesman_number,
        e.first_name || ' ' || e.last_name as name,
        COUNT(*) as verkaufe,
        SUM(CASE WHEN dealer_vehicle_type = 'N' THEN 1 ELSE 0 END) as neuwagen,
        SUM(CASE WHEN dealer_vehicle_type IN ('T', 'V') THEN 1 ELSE 0 END) as test_vorfuehr,
        SUM(CASE WHEN dealer_vehicle_type IN ('G', 'D') THEN 1 ELSE 0 END) as gebraucht,
        ROUND(SUM(s.price), 2) as umsatz
    FROM sales s
    LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
    WHERE strftime('%Y', s.out_sales_contract_date) = '2025'
        AND strftime('%m', s.out_sales_contract_date) = '11'
    GROUP BY s.salesman_number
    ORDER BY verkaufe DESC
    """
    
    cursor.execute(query_per_salesman)
    rows = cursor.fetchall()
    
    print(f"📊 PRO VERKÄUFER:")
    print(f"{'Nr':<6} {'Name':<20} {'Neu':>4} {'T/V':>4} {'Gebr':>4} {'Total':>5} {'Umsatz':>12}")
    print("-" * 70)
    
    for row in rows:
        name = row['name'] if row['name'] else f"VK-{row['salesman_number']}"
        print(f"{row['salesman_number']:<6} {name:<20} {row['neuwagen']:>4} "
              f"{row['test_vorfuehr']:>4} {row['gebraucht']:>4} {row['verkaufe']:>5} "
              f"{row['umsatz']:>12,.2f} €")
    print()

def check_5_detailed_corsa_search(conn):
    """Check 5: Alle Corsas im November (alle Verkäufer)"""
    print_header("CHECK 5: Alle Corsa-Verkäufe November 2025")
    
    query = """
    SELECT 
        s.id,
        s.salesman_number,
        e.first_name || ' ' || e.last_name as verkaufer,
        s.dealer_vehicle_type,
        s.model_description,
        s.out_sales_contract_date,
        s.price
    FROM sales s
    LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
    WHERE s.model_description LIKE '%Corsa%'
        AND strftime('%Y', s.out_sales_contract_date) = '2025'
        AND strftime('%m', s.out_sales_contract_date) = '11'
    ORDER BY s.model_description, s.out_sales_contract_date, s.id
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("ℹ️  Keine Corsa-Verkäufe im November 2025\n")
        return
    
    print(f"📊 Gefunden: {len(rows)} Corsa-Verkäufe\n")
    
    # Gruppiere nach Modellbeschreibung
    by_model = defaultdict(list)
    for row in rows:
        by_model[row['model_description']].append(row)
    
    for model, entries in by_model.items():
        print(f"🚗 {model}")
        print(f"   Anzahl: {len(entries)}")
        
        if len(entries) > 1:
            print("   ⚠️  MEHRFACH-VERKAUF!")
        
        for entry in entries:
            type_label = {
                'N': 'Neu', 'T': 'Test', 'V': 'Vorführ', 
                'G': 'Gebr', 'D': 'Demo'
            }.get(entry['dealer_vehicle_type'], entry['dealer_vehicle_type'])
            
            verkaufer = entry['verkaufer'] if entry['verkaufer'] else f"VK-{entry['salesman_number']}"
            
            print(f"   └─ ID {entry['id']}: {verkaufer} | {type_label} | "
                  f"{entry['out_sales_contract_date']} | {entry['price']:,.2f} €")
        print()

def generate_cleanup_sql(conn):
    """Generiere SQL-Script zur Bereinigung"""
    print_header("SQL-BEREINIGUNG (OPTIONAL)")
    
    # Finde exakte Duplikate
    query = """
    SELECT 
        model_description,
        salesman_number,
        out_sales_contract_date,
        dealer_vehicle_type,
        price,
        GROUP_CONCAT(id) as ids
    FROM sales
    WHERE out_sales_contract_date IS NOT NULL
    GROUP BY 
        model_description,
        salesman_number,
        out_sales_contract_date,
        dealer_vehicle_type,
        price
    HAVING COUNT(*) > 1
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("✅ Keine Bereinigung notwendig (keine exakten Duplikate)\n")
        return
    
    print("-- SQL-Script zum Löschen von Duplikaten")
    print("-- ACHTUNG: Vorher Backup erstellen!")
    print("-- Ausführung: sqlite3 greiner_controlling.db < cleanup.sql\n")
    print("BEGIN TRANSACTION;\n")
    
    total_to_delete = 0
    for row in rows:
        ids = row['ids'].split(',')
        # Behalte den ersten, lösche den Rest
        ids_to_delete = ids[1:]
        total_to_delete += len(ids_to_delete)
        
        for id_to_delete in ids_to_delete:
            print(f"-- Duplikat: {row['model_description'][:50]}... | {row['out_sales_contract_date']}")
            print(f"DELETE FROM sales WHERE id = {id_to_delete};")
            print()
    
    print("COMMIT;")
    print(f"\n-- Würde {total_to_delete} Duplikate löschen\n")

def main():
    """Hauptprogramm"""
    print("\n" + "="*80)
    print("  🔍 VERKAUFS-DUPLIKATE ANALYSE")
    print("  Greiner Portal - Datenbank Check")
    print("  " + datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    print("="*80)
    
    conn = connect_db()
    
    try:
        # Alle Checks durchführen
        check_1_corsa_duplikate(conn)
        check_2_exact_duplicates(conn)
        check_3_same_model_same_day(conn)
        check_4_november_stats(conn)
        check_5_detailed_corsa_search(conn)
        generate_cleanup_sql(conn)
        
        print_header("✅ ANALYSE ABGESCHLOSSEN")
        print("Nächste Schritte:")
        print("1. Ergebnisse prüfen")
        print("2. Bei Duplikaten: Backup erstellen")
        print("3. SQL-Script ausführen (falls generiert)")
        print("4. Erneut prüfen mit diesem Script\n")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
