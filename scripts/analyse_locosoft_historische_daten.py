#!/usr/bin/env python3
"""
Locosoft PostgreSQL - Historische Daten Analyse
===============================================
TAG 181: Prüft ob mehr historische Daten verfügbar sind als wir aktuell nutzen

Ziel:
- Prüfe alle Tabellen in Locosoft-DB
- Analysiere Datums-Spannen für journal_accountings
- Prüfe ob es ältere Daten gibt (vor 2023-09)
- Identifiziere mögliche Import-Probleme
"""

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')

from datetime import datetime, date
from api.db_utils import locosoft_session, row_to_dict
from api.db_connection import convert_placeholders
import psycopg2.extras

def analyse_tabellen():
    """Analysiert alle Tabellen in der Locosoft-DB"""
    print("="*80)
    print("LOCOSOFT POSTGRESQL - HISTORISCHE DATEN ANALYSE")
    print("="*80)
    print()
    
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. Alle Tabellen auflisten
        print("📋 VERFÜGBARE TABELLEN:")
        print("-"*80)
        cursor.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name) as spalten_anzahl
            FROM information_schema.tables t
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tabellen = cursor.fetchall()
        print(f"Anzahl Tabellen: {len(tabellen)}\n")
        
        for t in tabellen:
            print(f"  - {t['table_name']:40s} ({t['spalten_anzahl']} Spalten)")
        
        print()
        
        # 2. journal_accountings - Detaillierte Analyse
        print("="*80)
        print("📊 JOURNAL_ACCOUNTINGS - DETAILLIERTE ANALYSE")
        print("="*80)
        print()
        
        # Gesamt-Statistik
        cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl_buchungen,
                MIN(accounting_date) as erste_buchung,
                MAX(accounting_date) as letzte_buchung,
                COUNT(DISTINCT DATE_TRUNC('month', accounting_date)) as anzahl_monate,
                COUNT(DISTINCT nominal_account_number) as anzahl_konten
            FROM journal_accountings
            WHERE accounting_date IS NOT NULL
        """))
        stat = row_to_dict(cursor.fetchone())
        
        print("Gesamt-Statistik:")
        print(f"  Anzahl Buchungen: {stat['anzahl_buchungen']:,}")
        print(f"  Erste Buchung: {stat['erste_buchung']}")
        print(f"  Letzte Buchung: {stat['letzte_buchung']}")
        print(f"  Anzahl Monate: {stat['anzahl_monate']}")
        print(f"  Anzahl Konten: {stat['anzahl_konten']}")
        print()
        
        # Monatliche Verteilung
        print("Monatliche Verteilung (erste 10 Monate):")
        cursor.execute(convert_placeholders("""
            SELECT 
                DATE_TRUNC('month', accounting_date) as monat,
                COUNT(*) as anzahl_buchungen,
                COUNT(DISTINCT nominal_account_number) as anzahl_konten,
                MIN(accounting_date) as min_datum,
                MAX(accounting_date) as max_datum
            FROM journal_accountings
            WHERE accounting_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', accounting_date)
            ORDER BY monat
            LIMIT 10
        """))
        monate = cursor.fetchall()
        for m in monate:
            print(f"  {m['monat']}: {m['anzahl_buchungen']:,} Buchungen, {m['anzahl_konten']} Konten")
        print()
        
        print("Monatliche Verteilung (letzte 10 Monate):")
        cursor.execute(convert_placeholders("""
            SELECT 
                DATE_TRUNC('month', accounting_date) as monat,
                COUNT(*) as anzahl_buchungen,
                COUNT(DISTINCT nominal_account_number) as anzahl_konten,
                MIN(accounting_date) as min_datum,
                MAX(accounting_date) as max_datum
            FROM journal_accountings
            WHERE accounting_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', accounting_date)
            ORDER BY monat DESC
            LIMIT 10
        """))
        monate = cursor.fetchall()
        for m in monate:
            print(f"  {m['monat']}: {m['anzahl_buchungen']:,} Buchungen, {m['anzahl_konten']} Konten")
        print()
        
        # Prüfe ob es Daten VOR 2023-09 gibt
        print("="*80)
        print("🔍 PRÜFUNG: Daten VOR September 2023")
        print("="*80)
        print()
        
        cursor.execute(convert_placeholders("""
            SELECT 
                COUNT(*) as anzahl_buchungen,
                MIN(accounting_date) as erste_buchung,
                MAX(accounting_date) as letzte_buchung,
                COUNT(DISTINCT DATE_TRUNC('month', accounting_date)) as anzahl_monate
            FROM journal_accountings
            WHERE accounting_date IS NOT NULL
              AND accounting_date < '2023-09-01'
        """))
        vor_2023 = row_to_dict(cursor.fetchone())
        
        if vor_2023['anzahl_buchungen'] > 0:
            print(f"✅ GEFUNDEN: {vor_2023['anzahl_buchungen']:,} Buchungen VOR 2023-09!")
            print(f"   Erste Buchung: {vor_2023['erste_buchung']}")
            print(f"   Letzte Buchung: {vor_2023['letzte_buchung']}")
            print(f"   Anzahl Monate: {vor_2023['anzahl_monate']}")
            print()
            
            # Detaillierte Monats-Verteilung VOR 2023-09
            print("Monatliche Verteilung VOR 2023-09:")
            cursor.execute(convert_placeholders("""
                SELECT 
                    DATE_TRUNC('month', accounting_date) as monat,
                    COUNT(*) as anzahl_buchungen
                FROM journal_accountings
                WHERE accounting_date IS NOT NULL
                  AND accounting_date < '2023-09-01'
                GROUP BY DATE_TRUNC('month', accounting_date)
                ORDER BY monat
            """))
            monate_vor = cursor.fetchall()
            for m in monate_vor:
                print(f"  {m['monat']}: {m['anzahl_buchungen']:,} Buchungen")
        else:
            print("❌ KEINE Daten VOR 2023-09 gefunden")
            print("   → Alle Daten beginnen ab September 2023")
        print()
        
        # 3. Prüfe andere relevante Tabellen
        print("="*80)
        print("📋 ANDERE RELEVANTE TABELLEN")
        print("="*80)
        print()
        
        relevante_tabellen = [
            'orders',
            'dealer_vehicles',
            'labours',
            'parts',
            'nominal_accounts'
        ]
        
        for tabelle in relevante_tabellen:
            try:
                # Prüfe ob Tabelle existiert
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (tabelle,))
                exists = cursor.fetchone()[0]
                
                if not exists:
                    print(f"  {tabelle}: ❌ Tabelle existiert nicht")
                    continue
                
                # Prüfe ob es Datums-Spalten gibt
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = %s
                      AND (data_type LIKE '%date%' OR data_type LIKE '%timestamp%')
                    ORDER BY column_name
                """, (tabelle,))
                date_spalten = cursor.fetchall()
                
                if date_spalten:
                    print(f"  {tabelle}:")
                    for spalte in date_spalten:
                        # Prüfe Min/Max für diese Spalte
                        try:
                            # Versuche mit CAST zu date falls timestamp
                            cursor.execute(convert_placeholders(f"""
                                SELECT 
                                    MIN({spalte['column_name']}::date) as min_datum,
                                    MAX({spalte['column_name']}::date) as max_datum,
                                    COUNT(*) as anzahl_zeilen
                                FROM {tabelle}
                                WHERE {spalte['column_name']} IS NOT NULL
                            """))
                            stat = row_to_dict(cursor.fetchone())
                            if stat['min_datum']:
                                print(f"    - {spalte['column_name']}: {stat['min_datum']} bis {stat['max_datum']} ({stat['anzahl_zeilen']:,} Zeilen)")
                        except Exception as e:
                            # Fallback ohne CAST
                            try:
                                cursor.execute(convert_placeholders(f"""
                                    SELECT 
                                        MIN({spalte['column_name']}) as min_datum,
                                        MAX({spalte['column_name']}) as max_datum,
                                        COUNT(*) as anzahl_zeilen
                                    FROM {tabelle}
                                    WHERE {spalte['column_name']} IS NOT NULL
                                """))
                                stat = row_to_dict(cursor.fetchone())
                                if stat['min_datum']:
                                    print(f"    - {spalte['column_name']}: {stat['min_datum']} bis {stat['max_datum']} ({stat['anzahl_zeilen']:,} Zeilen)")
                            except Exception as e2:
                                print(f"    - {spalte['column_name']}: Fehler beim Abfragen ({str(e2)[:50]})")
                else:
                    print(f"  {tabelle}: Keine Datums-Spalten gefunden")
            except Exception as e:
                print(f"  {tabelle}: Fehler - {str(e)[:50]}")
        
        print()
        
        # 4. Prüfe ob es Unterschiede zwischen Tabellen gibt
        print("="*80)
        print("🔍 VERGLEICH: Verschiedene Tabellen")
        print("="*80)
        print()
        
        # Vergleiche journal_accountings mit orders
        try:
            cursor.execute(convert_placeholders("""
                SELECT 
                    MIN(order_date::date) as erste_order,
                    MAX(order_date::date) as letzte_order,
                    COUNT(*) as anzahl_orders
                FROM orders
                WHERE order_date IS NOT NULL
            """))
            orders_stat = row_to_dict(cursor.fetchone())
            
            if orders_stat['erste_order']:
                print(f"ORDERS Tabelle:")
                print(f"  Erste Order: {orders_stat['erste_order']}")
                print(f"  Letzte Order: {orders_stat['letzte_order']}")
                print(f"  Anzahl Orders: {orders_stat['anzahl_orders']:,}")
                
                # Vergleich
                if orders_stat['erste_order'] and orders_stat['erste_order'] < date(2023, 9, 1):
                    print(f"  ⚠️  Orders haben ältere Daten als journal_accountings!")
                    print(f"     → Möglicherweise fehlen historische Buchungen in journal_accountings")
                    print()
                    
                    # Prüfe ob wir aus orders historische Umsätze ableiten können
                    print("  💡 MÖGLICHKEIT: Historische Umsätze aus orders ableiten?")
                    cursor.execute(convert_placeholders("""
                        SELECT 
                            DATE_TRUNC('month', order_date) as monat,
                            COUNT(*) as anzahl_orders,
                            COUNT(DISTINCT DATE_TRUNC('month', order_date)) as monate_mit_orders
                        FROM orders
                        WHERE order_date IS NOT NULL
                          AND order_date < '2023-09-01'
                        GROUP BY DATE_TRUNC('month', order_date)
                        ORDER BY monat DESC
                        LIMIT 10
                    """))
                    monate_orders = cursor.fetchall()
                    if monate_orders:
                        print(f"     → {len(monate_orders)} Monate mit Orders VOR 2023-09")
                        print(f"     → Beispiel (letzte 5 Monate):")
                        for m in monate_orders[:5]:
                            print(f"       {m['monat']}: {m['anzahl_orders']} Orders")
        except Exception as e:
            print(f"  Fehler beim Abfragen von orders: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
        
        # 5. Zusammenfassung
        print("="*80)
        print("📊 ZUSAMMENFASSUNG")
        print("="*80)
        print()
        
        print(f"journal_accountings:")
        print(f"  - Erste Buchung: {stat['erste_buchung']}")
        print(f"  - Letzte Buchung: {stat['letzte_buchung']}")
        print(f"  - Anzahl Monate: {stat['anzahl_monate']}")
        print(f"  - Anzahl Buchungen: {stat['anzahl_buchungen']:,}")
        print()
        
        if vor_2023['anzahl_buchungen'] == 0:
            print("❌ PROBLEM: Keine historischen Daten VOR 2023-09 in journal_accountings")
            print("   → Mögliche Ursachen:")
            print("     1. Daten wurden erst 2023-09 in Locosoft-DB importiert")
            print("     2. Historische Daten wurden gelöscht/archiviert")
            print("     3. Import-Script hat nur Daten ab 2023-09 importiert")
            print()
            print("💡 LÖSUNG:")
            print("   - Prüfe ob es ein Backup/Archiv mit älteren Daten gibt")
            print("   - Prüfe ob Locosoft selbst ältere Daten hat (andere Datenquelle)")
            print("   - Prüfe Import-Scripts ob sie ein Datums-Limit haben")
        else:
            print(f"✅ GEFUNDEN: {vor_2023['anzahl_monate']} Monate historische Daten VOR 2023-09!")
            print("   → Diese Daten können für ML-Training genutzt werden!")

if __name__ == '__main__':
    try:
        analyse_tabellen()
    except Exception as e:
        print(f"\n❌ FEHLER: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
