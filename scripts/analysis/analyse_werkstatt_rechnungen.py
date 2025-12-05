#!/usr/bin/env python3
"""
LOCOSOFT WERKSTATT-ANALYSE
==========================
Analysiert Werkstattrechnungen für TEK-Kalkulation

Ausführen auf Server:
  cd /opt/greiner-portal
  source venv/bin/activate
  python3 scripts/analysis/analyse_werkstatt_rechnungen.py
"""

import psycopg2
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Locosoft Connection
LOCOSOFT_CONFIG = {
    "host": "10.80.80.8",
    "port": 5432,
    "database": "loco_auswertung_db",
    "user": "loco_auswertung_benutzer",
    "password": "loco"
}

def get_connection():
    return psycopg2.connect(**LOCOSOFT_CONFIG)

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def analyse_tabellen():
    """Schritt 1: Welche Tabellen gibt es für Werkstatt/Rechnungen?"""
    print_header("SCHRITT 1: VERFÜGBARE TABELLEN")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Suche nach relevanten Tabellen
    suchbegriffe = ['invoice', 'order', 'auftrag', 'rechnung', 'work', 'service', 'position']
    
    for begriff in suchbegriffe:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_name ILIKE %s
            ORDER BY table_name
        """, (f'%{begriff}%',))
        
        rows = cur.fetchall()
        if rows:
            print(f"\n🔍 Tabellen mit '{begriff}':")
            for row in rows:
                # Zähle Einträge
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {row[0]}")
                    count = cur.fetchone()[0]
                    print(f"   {row[0]}: {count:,} Einträge")
                except:
                    print(f"   {row[0]}: (Fehler beim Zählen)")
    
    cur.close()
    conn.close()

def analyse_invoices_schema():
    """Schritt 2: Schema der invoices-Tabelle"""
    print_header("SCHRITT 2: SCHEMA DER INVOICES-TABELLE")
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'invoices'
        ORDER BY ordinal_position
    """)
    
    print("\nSpalten in 'invoices':")
    print("-" * 50)
    for row in cur.fetchall():
        print(f"  {row[0]:<35} {row[1]:<15} {'NULL' if row[2]=='YES' else 'NOT NULL'}")
    
    cur.close()
    conn.close()

def analyse_invoices_beispiele():
    """Schritt 3: Beispieldaten aus invoices"""
    print_header("SCHRITT 3: BEISPIELDATEN AUS INVOICES")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Neueste Rechnungen
    cur.execute("""
        SELECT *
        FROM invoices
        ORDER BY id DESC
        LIMIT 5
    """)
    
    # Spaltennamen holen
    colnames = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    
    print("\nNeueste 5 Rechnungen:")
    print("-" * 100)
    
    for row in rows:
        print("\n--- Rechnung ---")
        for i, col in enumerate(colnames):
            val = row[i]
            if val is not None and str(val).strip():
                print(f"  {col}: {val}")
    
    cur.close()
    conn.close()

def analyse_durchschnitt_rechnung():
    """Schritt 4: Durchschnittlicher Rechnungsbetrag"""
    print_header("SCHRITT 4: DURCHSCHNITTLICHER RECHNUNGSBETRAG")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Versuche verschiedene mögliche Spalten für Betrag
    betrag_spalten = ['total', 'amount', 'sum', 'value', 'betrag', 'netto', 'brutto', 
                      'total_amount', 'invoice_amount', 'net_amount', 'gross_amount']
    
    # Erst Schema prüfen
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns
        WHERE table_name = 'invoices'
    """)
    vorhandene_spalten = [row[0] for row in cur.fetchall()]
    
    print(f"\nVorhandene Spalten: {', '.join(vorhandene_spalten[:20])}...")
    
    # Suche Betrags-Spalte
    gefundene_betrag_spalten = []
    for spalte in betrag_spalten:
        for vorhanden in vorhandene_spalten:
            if spalte in vorhanden.lower():
                gefundene_betrag_spalten.append(vorhanden)
    
    if gefundene_betrag_spalten:
        print(f"\n💰 Mögliche Betrags-Spalten: {gefundene_betrag_spalten}")
        
        for spalte in gefundene_betrag_spalten[:3]:
            try:
                # Letzten 12 Monate
                cur.execute(f"""
                    SELECT 
                        COUNT(*) as anzahl,
                        AVG({spalte}) as durchschnitt,
                        MIN({spalte}) as min_betrag,
                        MAX({spalte}) as max_betrag,
                        SUM({spalte}) as summe
                    FROM invoices
                    WHERE {spalte} IS NOT NULL
                      AND {spalte} > 0
                """)
                
                row = cur.fetchone()
                if row and row[0] > 0:
                    print(f"\n📊 Analyse Spalte '{spalte}':")
                    print(f"   Anzahl Rechnungen:     {row[0]:>12,}")
                    print(f"   Durchschnitt:          {row[1]:>12,.2f}")
                    print(f"   Minimum:               {row[2]:>12,.2f}")
                    print(f"   Maximum:               {row[3]:>12,.2f}")
                    print(f"   Summe:                 {row[4]:>15,.2f}")
                    
                    # Ist es in Cent? (Werte > 10000 deuten auf Cent hin)
                    if row[1] > 10000:
                        print(f"\n   ⚠️  Vermutlich in CENT! Umgerechnet:")
                        print(f"   Durchschnitt:          {row[1]/100:>12,.2f} €")
                        print(f"   Minimum:               {row[2]/100:>12,.2f} €")
                        print(f"   Maximum:               {row[3]/100:>12,.2f} €")
            except Exception as e:
                print(f"   Fehler bei '{spalte}': {e}")
    
    cur.close()
    conn.close()

def analyse_werkstatt_vs_andere():
    """Schritt 5: Unterscheidung Werkstatt vs. andere Rechnungen"""
    print_header("SCHRITT 5: WERKSTATT VS. ANDERE RECHNUNGEN")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Schema prüfen für Typ-Unterscheidung
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns
        WHERE table_name = 'invoices'
          AND (column_name ILIKE '%type%' 
               OR column_name ILIKE '%art%'
               OR column_name ILIKE '%bereich%'
               OR column_name ILIKE '%category%'
               OR column_name ILIKE '%abteilung%'
               OR column_name ILIKE '%department%')
    """)
    
    typ_spalten = [row[0] for row in cur.fetchall()]
    print(f"\nMögliche Typ-Spalten: {typ_spalten if typ_spalten else 'KEINE GEFUNDEN'}")
    
    for spalte in typ_spalten[:3]:
        try:
            cur.execute(f"""
                SELECT {spalte}, COUNT(*) as anzahl
                FROM invoices
                WHERE {spalte} IS NOT NULL
                GROUP BY {spalte}
                ORDER BY anzahl DESC
                LIMIT 20
            """)
            
            print(f"\n📋 Werte in '{spalte}':")
            for row in cur.fetchall():
                print(f"   {str(row[0]):<30} {row[1]:>10,} Rechnungen")
        except Exception as e:
            print(f"   Fehler: {e}")
    
    cur.close()
    conn.close()

def analyse_monatlich():
    """Schritt 6: Monatliche Entwicklung"""
    print_header("SCHRITT 6: MONATLICHE ENTWICKLUNG (letzte 12 Monate)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Suche Datums-Spalte
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns
        WHERE table_name = 'invoices'
          AND (column_name ILIKE '%date%' 
               OR column_name ILIKE '%datum%'
               OR column_name ILIKE '%created%')
    """)
    
    datums_spalten = [row[0] for row in cur.fetchall()]
    print(f"\nDatums-Spalten: {datums_spalten}")
    
    # Suche Betrags-Spalte (nochmal)
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns
        WHERE table_name = 'invoices'
          AND data_type IN ('integer', 'bigint', 'numeric', 'real', 'double precision')
    """)
    
    numerische_spalten = [row[0] for row in cur.fetchall()]
    
    # Versuche monatliche Analyse
    if datums_spalten and numerische_spalten:
        datum_col = datums_spalten[0]
        
        # Finde beste Betrags-Spalte
        for betrag_col in numerische_spalten:
            if 'amount' in betrag_col.lower() or 'total' in betrag_col.lower() or 'sum' in betrag_col.lower():
                try:
                    cur.execute(f"""
                        SELECT 
                            DATE_TRUNC('month', {datum_col}::date) as monat,
                            COUNT(*) as anzahl,
                            AVG({betrag_col}) as durchschnitt,
                            SUM({betrag_col}) as summe
                        FROM invoices
                        WHERE {datum_col} >= CURRENT_DATE - INTERVAL '12 months'
                          AND {betrag_col} > 0
                        GROUP BY DATE_TRUNC('month', {datum_col}::date)
                        ORDER BY monat DESC
                    """)
                    
                    print(f"\n📅 Monatliche Analyse ({datum_col} / {betrag_col}):")
                    print("-" * 70)
                    print(f"{'Monat':<12} {'Anzahl':>10} {'Ø Betrag':>15} {'Summe':>20}")
                    print("-" * 70)
                    
                    for row in cur.fetchall():
                        monat_str = row[0].strftime('%Y-%m') if row[0] else 'N/A'
                        durchschnitt = row[2] / 100 if row[2] > 10000 else row[2]  # Cent-Korrektur
                        summe = row[3] / 100 if row[3] > 1000000 else row[3]
                        print(f"{monat_str:<12} {row[1]:>10,} {durchschnitt:>15,.2f} € {summe:>18,.2f} €")
                    
                    break
                except Exception as e:
                    continue
    
    cur.close()
    conn.close()

def analyse_serviceberater():
    """Schritt 7: Gibt es Serviceberater-Zuordnung?"""
    print_header("SCHRITT 7: SERVICEBERATER IN RECHNUNGEN?")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Suche nach Mitarbeiter/Berater-Spalten
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns
        WHERE table_name = 'invoices'
          AND (column_name ILIKE '%employee%' 
               OR column_name ILIKE '%mitarbeiter%'
               OR column_name ILIKE '%berater%'
               OR column_name ILIKE '%user%'
               OR column_name ILIKE '%seller%'
               OR column_name ILIKE '%salesman%'
               OR column_name ILIKE '%advisor%'
               OR column_name ILIKE '%created_by%')
    """)
    
    ma_spalten = [row[0] for row in cur.fetchall()]
    print(f"\nMitarbeiter-Spalten: {ma_spalten if ma_spalten else 'KEINE GEFUNDEN'}")
    
    for spalte in ma_spalten[:3]:
        try:
            cur.execute(f"""
                SELECT {spalte}, COUNT(*) as anzahl
                FROM invoices
                WHERE {spalte} IS NOT NULL
                GROUP BY {spalte}
                ORDER BY anzahl DESC
                LIMIT 15
            """)
            
            print(f"\n👤 Werte in '{spalte}':")
            for row in cur.fetchall():
                print(f"   {str(row[0]):<40} {row[1]:>8,} Rechnungen")
        except Exception as e:
            print(f"   Fehler: {e}")
    
    cur.close()
    conn.close()

def analyse_orders_tabelle():
    """Schritt 8: Orders-Tabelle (Werkstattaufträge?)"""
    print_header("SCHRITT 8: ORDERS-TABELLE (WERKSTATTAUFTRÄGE)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Schema von orders
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'orders'
        ORDER BY ordinal_position
    """)
    
    print("\nSpalten in 'orders':")
    print("-" * 50)
    for row in cur.fetchall():
        print(f"  {row[0]:<35} {row[1]}")
    
    # Beispieldaten
    cur.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 3")
    colnames = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    
    print("\n\nNeueste 3 Orders:")
    for row in rows:
        print("\n--- Order ---")
        for i, col in enumerate(colnames):
            val = row[i]
            if val is not None and str(val).strip():
                print(f"  {col}: {val}")
    
    cur.close()
    conn.close()

def main():
    print("\n" + "="*70)
    print("  LOCOSOFT WERKSTATT-RECHNUNGEN ANALYSE")
    print("  Für TEK-Kalkulation Serviceberater")
    print("="*70)
    print(f"  Ausgeführt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    try:
        # Test-Verbindung
        conn = get_connection()
        conn.close()
        print("\n✅ Locosoft-Verbindung erfolgreich!")
    except Exception as e:
        print(f"\n❌ Verbindungsfehler: {e}")
        return
    
    # Alle Analysen durchführen
    analyse_tabellen()
    analyse_invoices_schema()
    analyse_invoices_beispiele()
    analyse_durchschnitt_rechnung()
    analyse_werkstatt_vs_andere()
    analyse_monatlich()
    analyse_serviceberater()
    analyse_orders_tabelle()
    
    print("\n" + "="*70)
    print("  ANALYSE ABGESCHLOSSEN")
    print("="*70)
    print("\n📋 Nächster Schritt:")
    print("   Ergebnisse an Claude schicken für TEK-Berechnung!")
    print()

if __name__ == "__main__":
    main()
