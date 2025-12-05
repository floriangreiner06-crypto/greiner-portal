#!/usr/bin/env python3
"""
LOCOSOFT WERKSTATT-ANALYSE V2
=============================
Korrigiert: Keine 'id' Spalte in invoices

Ausführen:
  python3 /mnt/greiner-portal-sync/scripts/analysis/analyse_werkstatt_rechnungen_v2.py
"""

import psycopg2
from datetime import datetime

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

def analyse_invoices_beispiele():
    """Beispieldaten aus invoices (nach invoice_date sortiert)"""
    print_header("BEISPIELDATEN (neueste 5 Rechnungen)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            invoice_type,
            invoice_number,
            subsidiary,
            invoice_date,
            job_amount_net,
            job_amount_gross,
            part_amount_net,
            part_amount_gross,
            total_net,
            total_gross,
            creating_employee,
            order_number
        FROM invoices
        WHERE invoice_date IS NOT NULL
        ORDER BY invoice_date DESC, invoice_number DESC
        LIMIT 5
    """)
    
    print("\nNeueste 5 Rechnungen:")
    print("-" * 100)
    for row in cur.fetchall():
        print(f"""
Rechnung: {row[0]}-{row[1]} | Filiale: {row[2]} | Datum: {row[3]}
  Arbeit:  Netto {row[4]:>10} | Brutto {row[5]:>10}
  Teile:   Netto {row[6]:>10} | Brutto {row[7]:>10}
  GESAMT:  Netto {row[8]:>10} | Brutto {row[9]:>10}
  Mitarbeiter: {row[10]} | Auftrag: {row[11]}
""")
    
    cur.close()
    conn.close()

def analyse_invoice_types():
    """Welche Rechnungstypen gibt es?"""
    print_header("RECHNUNGSTYPEN (invoice_types)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM invoice_types")
    colnames = [desc[0] for desc in cur.description]
    
    print(f"Spalten: {colnames}")
    print("-" * 50)
    
    for row in cur.fetchall():
        print(row)
    
    # Verteilung nach Typ
    cur.execute("""
        SELECT 
            invoice_type,
            COUNT(*) as anzahl,
            SUM(total_gross) as summe_brutto
        FROM invoices
        GROUP BY invoice_type
        ORDER BY anzahl DESC
    """)
    
    print("\nVerteilung in invoices:")
    print("-" * 50)
    for row in cur.fetchall():
        summe = row[2] if row[2] else 0
        print(f"  Typ {row[0]}: {row[1]:>8,} Rechnungen | Summe: {summe:>15,.2f}")
    
    cur.close()
    conn.close()

def analyse_durchschnitt():
    """Durchschnittlicher Rechnungsbetrag"""
    print_header("DURCHSCHNITTLICHER RECHNUNGSBETRAG")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Gesamt
    cur.execute("""
        SELECT 
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            AVG(total_net) as avg_netto,
            MIN(total_gross) as min_brutto,
            MAX(total_gross) as max_brutto,
            SUM(total_gross) as summe_brutto,
            AVG(job_amount_gross) as avg_arbeit,
            AVG(part_amount_gross) as avg_teile
        FROM invoices
        WHERE total_gross > 0
          AND is_canceled = false
    """)
    
    row = cur.fetchone()
    print(f"""
ALLE RECHNUNGEN (nicht storniert, total_gross > 0):
───────────────────────────────────────────────────
  Anzahl:              {row[0]:>12,}
  
  Ø Brutto gesamt:     {row[1]:>12,.2f} €
  Ø Netto gesamt:      {row[2]:>12,.2f} €
  
  Minimum:             {row[3]:>12,.2f} €
  Maximum:             {row[4]:>12,.2f} €
  
  SUMME Brutto:        {row[5]:>15,.2f} €
  
  Ø Arbeit (brutto):   {row[6]:>12,.2f} €
  Ø Teile (brutto):    {row[7]:>12,.2f} €
""")
    
    cur.close()
    conn.close()

def analyse_nach_filiale():
    """Aufschlüsselung nach Filiale (subsidiary)"""
    print_header("NACH FILIALE (subsidiary)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            subsidiary,
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            SUM(total_gross) as summe_brutto
        FROM invoices
        WHERE total_gross > 0
          AND is_canceled = false
        GROUP BY subsidiary
        ORDER BY summe_brutto DESC
    """)
    
    print(f"{'Filiale':<10} {'Anzahl':>10} {'Ø Brutto':>15} {'Summe Brutto':>20}")
    print("-" * 60)
    for row in cur.fetchall():
        print(f"{row[0]:<10} {row[1]:>10,} {row[2]:>15,.2f} € {row[3]:>18,.2f} €")
    
    cur.close()
    conn.close()

def analyse_monatlich():
    """Monatliche Entwicklung (letzte 12 Monate)"""
    print_header("MONATLICHE ENTWICKLUNG (letzte 12 Monate)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            DATE_TRUNC('month', invoice_date) as monat,
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            SUM(total_gross) as summe_brutto,
            AVG(job_amount_gross) as avg_arbeit,
            AVG(part_amount_gross) as avg_teile
        FROM invoices
        WHERE invoice_date >= CURRENT_DATE - INTERVAL '12 months'
          AND total_gross > 0
          AND is_canceled = false
        GROUP BY DATE_TRUNC('month', invoice_date)
        ORDER BY monat DESC
    """)
    
    print(f"{'Monat':<12} {'Anzahl':>8} {'Ø Brutto':>12} {'Ø Arbeit':>12} {'Ø Teile':>12} {'Summe':>18}")
    print("-" * 80)
    
    for row in cur.fetchall():
        monat = row[0].strftime('%Y-%m') if row[0] else 'N/A'
        print(f"{monat:<12} {row[1]:>8,} {row[2]:>12,.2f} {row[4]:>12,.2f} {row[5]:>12,.2f} {row[3]:>16,.2f} €")
    
    cur.close()
    conn.close()

def analyse_mitarbeiter():
    """Rechnungen nach Mitarbeiter (creating_employee)"""
    print_header("NACH MITARBEITER (creating_employee)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Letzte 3 Monate
    cur.execute("""
        SELECT 
            creating_employee,
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            SUM(total_gross) as summe_brutto
        FROM invoices
        WHERE invoice_date >= CURRENT_DATE - INTERVAL '3 months'
          AND total_gross > 0
          AND is_canceled = false
          AND creating_employee IS NOT NULL
        GROUP BY creating_employee
        ORDER BY summe_brutto DESC
        LIMIT 20
    """)
    
    print("Top 20 Mitarbeiter (letzte 3 Monate):")
    print(f"{'MA-ID':<10} {'Anzahl':>10} {'Ø Brutto':>15} {'Summe Brutto':>20}")
    print("-" * 60)
    
    for row in cur.fetchall():
        print(f"{row[0]:<10} {row[1]:>10,} {row[2]:>15,.2f} € {row[3]:>18,.2f} €")
    
    cur.close()
    conn.close()

def analyse_werkstatt_spezifisch():
    """Nur Werkstatt-Rechnungen (job_amount > 0)"""
    print_header("NUR WERKSTATT-RECHNUNGEN (job_amount > 0)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            AVG(job_amount_gross) as avg_arbeit,
            AVG(part_amount_gross) as avg_teile,
            SUM(total_gross) as summe
        FROM invoices
        WHERE job_amount_gross > 0
          AND is_canceled = false
    """)
    
    row = cur.fetchone()
    print(f"""
WERKSTATT-RECHNUNGEN (mit Arbeitsleistung):
───────────────────────────────────────────
  Anzahl:              {row[0]:>12,}
  
  Ø Brutto gesamt:     {row[1]:>12,.2f} €
  Ø Arbeit (brutto):   {row[2]:>12,.2f} €
  Ø Teile (brutto):    {row[3]:>12,.2f} €
  
  SUMME:               {row[4]:>15,.2f} €
""")
    
    # Monatlich nur Werkstatt
    cur.execute("""
        SELECT 
            DATE_TRUNC('month', invoice_date) as monat,
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            SUM(total_gross) as summe
        FROM invoices
        WHERE invoice_date >= CURRENT_DATE - INTERVAL '12 months'
          AND job_amount_gross > 0
          AND is_canceled = false
        GROUP BY DATE_TRUNC('month', invoice_date)
        ORDER BY monat DESC
    """)
    
    print("\nMonatlich (nur Werkstatt, letzte 12 Monate):")
    print(f"{'Monat':<12} {'Anzahl':>10} {'Ø Brutto':>15} {'Summe':>20}")
    print("-" * 60)
    
    for row in cur.fetchall():
        monat = row[0].strftime('%Y-%m') if row[0] else 'N/A'
        print(f"{monat:<12} {row[1]:>10,} {row[2]:>15,.2f} € {row[3]:>18,.2f} €")
    
    cur.close()
    conn.close()

def analyse_orders():
    """Orders-Tabelle (Werkstattaufträge)"""
    print_header("ORDERS-TABELLE (WERKSTATTAUFTRÄGE)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Schema
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'orders'
        ORDER BY ordinal_position
    """)
    
    print("Schema von 'orders':")
    print("-" * 50)
    for row in cur.fetchall():
        print(f"  {row[0]:<35} {row[1]}")
    
    cur.close()
    conn.close()

def analyse_order_classifications():
    """Auftrags-Klassifizierungen"""
    print_header("ORDER CLASSIFICATIONS (Auftragsarten)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM order_classifications_def")
    colnames = [desc[0] for desc in cur.description]
    
    print(f"Spalten: {colnames}")
    print("-" * 80)
    for row in cur.fetchall():
        print(row)
    
    cur.close()
    conn.close()

def zusammenfassung():
    """Zusammenfassung für TEK"""
    print_header("📊 ZUSAMMENFASSUNG FÜR TEK-KALKULATION")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Letzte 12 Monate Werkstatt
    cur.execute("""
        SELECT 
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            AVG(job_amount_gross) as avg_arbeit,
            AVG(part_amount_gross) as avg_teile,
            SUM(total_gross) as summe,
            SUM(job_amount_gross) as summe_arbeit,
            SUM(part_amount_gross) as summe_teile
        FROM invoices
        WHERE invoice_date >= CURRENT_DATE - INTERVAL '12 months'
          AND job_amount_gross > 0
          AND is_canceled = false
    """)
    
    row = cur.fetchone()
    
    # Anzahl Monate
    monate = 12
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  WERKSTATT-KENNZAHLEN (letzte 12 Monate)                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Anzahl Rechnungen:          {row[0]:>12,}                        ║
║  Rechnungen pro Monat:       {row[0]/monate:>12,.0f}                        ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  DURCHSCHNITTE PRO RECHNUNG:                                     ║
║  ─────────────────────────────────────────────────────────────   ║
║  Ø Gesamt (brutto):          {row[1]:>12,.2f} €                   ║
║  Ø Arbeit (brutto):          {row[2]:>12,.2f} €                   ║
║  Ø Teile (brutto):           {row[3]:>12,.2f} €                   ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  SUMMEN (12 Monate):                                             ║
║  ─────────────────────────────────────────────────────────────   ║
║  Gesamt (brutto):            {row[4]:>15,.2f} €                ║
║  davon Arbeit:               {row[5]:>15,.2f} €                ║
║  davon Teile:                {row[6]:>15,.2f} €                ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  PRO MONAT (Durchschnitt):                                       ║
║  ─────────────────────────────────────────────────────────────   ║
║  Umsatz gesamt:              {row[4]/monate:>15,.2f} €                ║
║  davon Arbeit:               {row[5]/monate:>15,.2f} €                ║
║  davon Teile:                {row[6]/monate:>15,.2f} €                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    cur.close()
    conn.close()

def main():
    print("\n" + "="*70)
    print("  LOCOSOFT WERKSTATT-RECHNUNGEN ANALYSE V2")
    print("  Für TEK-Kalkulation Serviceberater")
    print("="*70)
    print(f"  Ausgeführt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    try:
        conn = get_connection()
        conn.close()
        print("\n✅ Locosoft-Verbindung erfolgreich!")
    except Exception as e:
        print(f"\n❌ Verbindungsfehler: {e}")
        return
    
    # Analysen
    analyse_invoice_types()
    analyse_invoices_beispiele()
    analyse_durchschnitt()
    analyse_nach_filiale()
    analyse_monatlich()
    analyse_mitarbeiter()
    analyse_werkstatt_spezifisch()
    analyse_order_classifications()
    zusammenfassung()
    
    print("\n" + "="*70)
    print("  ANALYSE ABGESCHLOSSEN")
    print("="*70)

if __name__ == "__main__":
    main()
