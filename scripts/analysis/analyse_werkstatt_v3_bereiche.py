#!/usr/bin/env python3
"""
LOCOSOFT ANALYSE V3 - NACH GESCHÄFTSBEREICHEN
==============================================
Aufschlüsselung nach NW, GW, Service, Teile
Mit Bezug zu BWA-Kostenstellen

invoice_type Mapping:
  2 = Werkstatt
  3 = Reklamation  
  4 = Intern
  5 = Bar-/Teileverkauf
  6 = Garantie
  7 = Neufahrzeug
  8 = Gebrauchtfahrzeug

Ausführen:
  python3 /mnt/greiner-portal-sync/scripts/analysis/analyse_werkstatt_v3_bereiche.py
"""

import psycopg2
from datetime import datetime

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
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

# Mapping invoice_type zu Geschäftsbereich
INVOICE_TYPE_MAP = {
    2: ('SERVICE', 'Werkstatt'),
    3: ('SERVICE', 'Reklamation'),
    4: ('INTERN', 'Intern'),
    5: ('TEILE', 'Bar-/Teileverkauf'),
    6: ('SERVICE', 'Garantie'),
    7: ('NW', 'Neufahrzeug'),
    8: ('GW', 'Gebrauchtfahrzeug'),
}

# BWA Kostenstellen Mapping
BWA_KOSTENSTELLEN = {
    'NW': 'KST 81 - Neuwagen',
    'GW': 'KST 82 - Gebrauchtwagen', 
    'SERVICE': 'KST 83 - Werkstatt/Service',
    'TEILE': 'KST 84 - Teile & Zubehör',
    'INTERN': 'Intern (keine BWA)',
}

def analyse_nach_geschaeftsbereich():
    """Hauptanalyse nach Geschäftsbereichen"""
    print_header("ANALYSE NACH GESCHÄFTSBEREICHEN (letzte 12 Monate)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Pro Rechnungstyp
    cur.execute("""
        SELECT 
            invoice_type,
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            SUM(total_gross) as summe_brutto,
            AVG(job_amount_gross) as avg_arbeit,
            AVG(part_amount_gross) as avg_teile,
            SUM(job_amount_gross) as summe_arbeit,
            SUM(part_amount_gross) as summe_teile
        FROM invoices
        WHERE invoice_date >= CURRENT_DATE - INTERVAL '12 months'
          AND is_canceled = false
          AND total_gross > 0
        GROUP BY invoice_type
        ORDER BY summe_brutto DESC
    """)
    
    results = cur.fetchall()
    
    # Aggregation nach Geschäftsbereich
    bereiche = {}
    for row in results:
        inv_type = row[0]
        if inv_type in INVOICE_TYPE_MAP:
            bereich, beschreibung = INVOICE_TYPE_MAP[inv_type]
            if bereich not in bereiche:
                bereiche[bereich] = {
                    'anzahl': 0,
                    'summe_brutto': 0,
                    'summe_arbeit': 0,
                    'summe_teile': 0,
                    'details': []
                }
            bereiche[bereich]['anzahl'] += row[1]
            bereiche[bereich]['summe_brutto'] += row[3] if row[3] else 0
            bereiche[bereich]['summe_arbeit'] += row[6] if row[6] else 0
            bereiche[bereich]['summe_teile'] += row[7] if row[7] else 0
            bereiche[bereich]['details'].append({
                'typ': beschreibung,
                'anzahl': row[1],
                'avg_brutto': row[2],
                'summe': row[3]
            })
    
    # Ausgabe
    print(f"\n{'BEREICH':<15} {'BWA-KST':<25} {'ANZAHL':>10} {'Ø BRUTTO':>12} {'SUMME 12M':>18}")
    print("-" * 85)
    
    gesamt_summe = 0
    for bereich in ['NW', 'GW', 'SERVICE', 'TEILE', 'INTERN']:
        if bereich in bereiche:
            data = bereiche[bereich]
            avg = data['summe_brutto'] / data['anzahl'] if data['anzahl'] > 0 else 0
            kst = BWA_KOSTENSTELLEN.get(bereich, '')
            print(f"{bereich:<15} {kst:<25} {data['anzahl']:>10,} {avg:>12,.2f} € {data['summe_brutto']:>15,.2f} €")
            gesamt_summe += data['summe_brutto']
            
            # Details
            for detail in data['details']:
                print(f"  └─ {detail['typ']:<20} {detail['anzahl']:>8,} {detail['avg_brutto']:>12,.2f} € {detail['summe']:>15,.2f} €")
    
    print("-" * 85)
    print(f"{'GESAMT':<42} {sum(b['anzahl'] for b in bereiche.values()):>10,} {'':>12} {gesamt_summe:>15,.2f} €")
    
    cur.close()
    conn.close()
    
    return bereiche

def analyse_service_detail():
    """Detailanalyse nur Service/Werkstatt (KST 83)"""
    print_header("DETAIL: SERVICE/WERKSTATT (KST 83)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Nur invoice_type 2, 3, 6 (Werkstatt, Reklamation, Garantie)
    cur.execute("""
        SELECT 
            invoice_type,
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            SUM(total_gross) as summe_brutto,
            AVG(job_amount_gross) as avg_arbeit,
            AVG(part_amount_gross) as avg_teile
        FROM invoices
        WHERE invoice_date >= CURRENT_DATE - INTERVAL '12 months'
          AND is_canceled = false
          AND total_gross > 0
          AND invoice_type IN (2, 3, 6)
        GROUP BY invoice_type
        ORDER BY anzahl DESC
    """)
    
    print(f"\n{'TYP':<20} {'ANZAHL':>10} {'Ø GESAMT':>12} {'Ø ARBEIT':>12} {'Ø TEILE':>12}")
    print("-" * 70)
    
    typ_namen = {2: 'Werkstatt', 3: 'Reklamation', 6: 'Garantie'}
    for row in cur.fetchall():
        typ = typ_namen.get(row[0], f'Typ {row[0]}')
        print(f"{typ:<20} {row[1]:>10,} {row[2]:>12,.2f} € {row[4]:>12,.2f} € {row[5]:>12,.2f} €")
    
    # Monatliche Entwicklung Service
    print("\n\nMonatliche Entwicklung SERVICE (Typ 2, 3, 6):")
    print("-" * 90)
    
    cur.execute("""
        SELECT 
            DATE_TRUNC('month', invoice_date) as monat,
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            SUM(total_gross) as summe_brutto,
            SUM(job_amount_gross) as summe_arbeit,
            SUM(part_amount_gross) as summe_teile
        FROM invoices
        WHERE invoice_date >= CURRENT_DATE - INTERVAL '12 months'
          AND is_canceled = false
          AND total_gross > 0
          AND invoice_type IN (2, 3, 6)
        GROUP BY DATE_TRUNC('month', invoice_date)
        ORDER BY monat DESC
    """)
    
    print(f"{'MONAT':<12} {'ANZAHL':>8} {'Ø BRUTTO':>12} {'SUMME':>15} {'ARBEIT':>15} {'TEILE':>15}")
    print("-" * 90)
    
    for row in cur.fetchall():
        monat = row[0].strftime('%Y-%m') if row[0] else 'N/A'
        print(f"{monat:<12} {row[1]:>8,} {row[2]:>12,.2f} € {row[3]:>13,.2f} € {row[4]:>13,.2f} € {row[5]:>13,.2f} €")
    
    cur.close()
    conn.close()

def analyse_teile_detail():
    """Detailanalyse Teile (KST 84)"""
    print_header("DETAIL: TEILE & ZUBEHÖR (KST 84)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Nur invoice_type 5 (Bar-/Teileverkauf)
    cur.execute("""
        SELECT 
            DATE_TRUNC('month', invoice_date) as monat,
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            SUM(total_gross) as summe_brutto,
            SUM(part_amount_gross) as summe_teile
        FROM invoices
        WHERE invoice_date >= CURRENT_DATE - INTERVAL '12 months'
          AND is_canceled = false
          AND total_gross > 0
          AND invoice_type = 5
        GROUP BY DATE_TRUNC('month', invoice_date)
        ORDER BY monat DESC
    """)
    
    print(f"\n{'MONAT':<12} {'ANZAHL':>10} {'Ø BRUTTO':>12} {'SUMME':>18}")
    print("-" * 55)
    
    for row in cur.fetchall():
        monat = row[0].strftime('%Y-%m') if row[0] else 'N/A'
        print(f"{monat:<12} {row[1]:>10,} {row[2]:>12,.2f} € {row[3]:>16,.2f} €")
    
    cur.close()
    conn.close()

def analyse_serviceberater_service():
    """Serviceberater nur für Service-Bereich"""
    print_header("SERVICEBERATER - NUR SERVICE/WERKSTATT (letzte 3 Monate)")
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            creating_employee,
            COUNT(*) as anzahl,
            AVG(total_gross) as avg_brutto,
            SUM(total_gross) as summe_brutto,
            SUM(job_amount_gross) as summe_arbeit,
            SUM(part_amount_gross) as summe_teile
        FROM invoices
        WHERE invoice_date >= CURRENT_DATE - INTERVAL '3 months'
          AND is_canceled = false
          AND total_gross > 0
          AND invoice_type IN (2, 3, 6)  -- Nur Service!
          AND creating_employee IS NOT NULL
        GROUP BY creating_employee
        ORDER BY summe_brutto DESC
        LIMIT 15
    """)
    
    print(f"\n{'MA-ID':<10} {'ANZAHL':>8} {'Ø BRUTTO':>12} {'SUMME':>15} {'ARBEIT':>15} {'TEILE':>12}")
    print("-" * 85)
    
    for row in cur.fetchall():
        print(f"{row[0]:<10} {row[1]:>8,} {row[2]:>12,.2f} € {row[3]:>13,.2f} € {row[4]:>13,.2f} € {row[5]:>10,.2f} €")
    
    cur.close()
    conn.close()

def bwa_vergleich():
    """Vergleich mit BWA-Struktur"""
    print_header("📊 BWA-VERGLEICH: LOCOSOFT vs. TEK-STRUKTUR")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Letzte 12 Monate pro Bereich
    bereiche_sql = {
        'NW (KST 81)': "invoice_type = 7",
        'GW (KST 82)': "invoice_type = 8", 
        'SERVICE (KST 83)': "invoice_type IN (2, 3, 6)",
        'TEILE (KST 84)': "invoice_type = 5",
    }
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  BWA-KOSTENSTELLEN - UMSÄTZE AUS LOCOSOFT (letzte 12 Monate)                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
""")
    
    gesamt = 0
    ergebnisse = {}
    
    for name, where in bereiche_sql.items():
        cur.execute(f"""
            SELECT 
                COUNT(*) as anzahl,
                SUM(total_gross) as summe_brutto,
                AVG(total_gross) as avg_brutto
            FROM invoices
            WHERE invoice_date >= CURRENT_DATE - INTERVAL '12 months'
              AND is_canceled = false
              AND total_gross > 0
              AND {where}
        """)
        row = cur.fetchone()
        anzahl = row[0] if row[0] else 0
        summe = row[1] if row[1] else 0
        avg = row[2] if row[2] else 0
        
        ergebnisse[name] = {'anzahl': anzahl, 'summe': summe, 'avg': avg}
        gesamt += summe
        
        print(f"║  {name:<20} {anzahl:>8,} Rechnungen   Ø {avg:>10,.2f} €   = {summe:>15,.2f} €  ║")
    
    print(f"""╠══════════════════════════════════════════════════════════════════════════════╣
║  GESAMT (12 Monate):                                      {gesamt:>15,.2f} €  ║
║  GESAMT pro Monat:                                        {gesamt/12:>15,.2f} €  ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Vergleich mit BWA Sep+Okt 2025
    print("""
┌──────────────────────────────────────────────────────────────────────────────┐
│  VERGLEICH MIT BWA (aus vorherigen Sessions)                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  BWA Sep+Okt 2025:                                                           │
│  ─────────────────────────────────────────────────────────────               │
│  Umsatz Werkstatt (83):    730.000 €/Monat                                   │
│  Umsatz Teile (84):        410.000 €/Monat                                   │
│  ───────────────────────────────────────────                                 │
│  After Sales GESAMT:     1.140.000 €/Monat                                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
""")
    
    # Service + Teile aus Locosoft
    service_summe = ergebnisse.get('SERVICE (KST 83)', {}).get('summe', 0)
    teile_summe = ergebnisse.get('TEILE (KST 84)', {}).get('summe', 0)
    
    print(f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│  LOCOSOFT AFTER SALES (letzte 12 Monate):                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Service/Werkstatt:    {service_summe/12:>12,.2f} €/Monat                                   │
│  Teile & Zubehör:      {teile_summe/12:>12,.2f} €/Monat                                   │
│  ───────────────────────────────────────────                                 │
│  After Sales GESAMT:   {(service_summe+teile_summe)/12:>12,.2f} €/Monat                                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
""")
    
    cur.close()
    conn.close()

def tek_serviceberater():
    """TEK-Berechnung für Serviceberater"""
    print_header("💰 TEK-KALKULATION SERVICEBERATER")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Service-Umsatz pro Monat (Durchschnitt)
    cur.execute("""
        SELECT 
            AVG(monatssumme) as avg_monat
        FROM (
            SELECT 
                DATE_TRUNC('month', invoice_date) as monat,
                SUM(total_gross) as monatssumme
            FROM invoices
            WHERE invoice_date >= CURRENT_DATE - INTERVAL '12 months'
              AND is_canceled = false
              AND total_gross > 0
              AND invoice_type IN (2, 3, 6)
            GROUP BY DATE_TRUNC('month', invoice_date)
        ) sub
    """)
    
    service_monat = cur.fetchone()[0] or 0
    
    # Anzahl aktive Serviceberater (die Rechnungen erstellen)
    cur.execute("""
        SELECT COUNT(DISTINCT creating_employee)
        FROM invoices
        WHERE invoice_date >= CURRENT_DATE - INTERVAL '3 months'
          AND is_canceled = false
          AND invoice_type IN (2, 3, 6)
          AND creating_employee IS NOT NULL
    """)
    
    anzahl_sb = cur.fetchone()[0] or 1
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  TEK-GRUNDLAGEN FÜR SERVICEBERATER                                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📊 UMSATZ-DATEN (aus Locosoft):                                             ║
║  ─────────────────────────────────────────────────────────────               ║
║  Service-Umsatz pro Monat (Ø):     {service_monat:>12,.2f} €                    ║
║  Aktive Serviceberater:            {anzahl_sb:>12}                              ║
║  Umsatz pro SB pro Monat (Ø):      {service_monat/anzahl_sb:>12,.2f} €                    ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  💰 VOLLKOSTEN PRO SERVICEBERATER (Schätzung):                               ║
║  ─────────────────────────────────────────────────────────────               ║
║  Personalkosten (direkt):                    5.500 €/Monat                   ║
║  Anteilige Gemeinkosten:                     2.500 €/Monat                   ║
║  Kalkulatorische Kosten:                       500 €/Monat                   ║
║  ────────────────────────────────────────────────────────                    ║
║  VOLLKOSTEN GESAMT:                          8.500 €/Monat                   ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🎯 BREAK-EVEN BERECHNUNG:                                                   ║
║  ─────────────────────────────────────────────────────────────               ║
║                                                                              ║
║  Bei 15% Bruttomarge:                                                        ║
║  Break-Even Umsatz = 8.500 € ÷ 0,15 = 56.667 €/Monat                        ║
║                                                                              ║
║  Bei 20% Bruttomarge:                                                        ║
║  Break-Even Umsatz = 8.500 € ÷ 0,20 = 42.500 €/Monat                        ║
║                                                                              ║
║  Bei 25% Bruttomarge:                                                        ║
║  Break-Even Umsatz = 8.500 € ÷ 0,25 = 34.000 €/Monat                        ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  📈 IST vs. SOLL:                                                            ║
║  ─────────────────────────────────────────────────────────────               ║
║                                                                              ║
║  Ø IST-Umsatz pro SB:              {service_monat/anzahl_sb:>12,.2f} €                    ║
║  Break-Even (15% Marge):                   56.667 €                          ║
║                                                                              ║
║  Status: {"✅ ÜBER Break-Even" if service_monat/anzahl_sb > 56667 else "⚠️  UNTER Break-Even"}                                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    cur.close()
    conn.close()

def main():
    print("\n" + "="*80)
    print("  LOCOSOFT ANALYSE V3 - GESCHÄFTSBEREICHE & TEK")
    print("  NW | GW | Service | Teile - Mit BWA-Bezug")
    print("="*80)
    print(f"  Ausgeführt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        conn = get_connection()
        conn.close()
        print("\n✅ Locosoft-Verbindung erfolgreich!")
    except Exception as e:
        print(f"\n❌ Verbindungsfehler: {e}")
        return
    
    # Analysen
    analyse_nach_geschaeftsbereich()
    analyse_service_detail()
    analyse_teile_detail()
    analyse_serviceberater_service()
    bwa_vergleich()
    tek_serviceberater()
    
    print("\n" + "="*80)
    print("  ANALYSE ABGESCHLOSSEN - Bereit für TEK-Kalkulation!")
    print("="*80)

if __name__ == "__main__":
    main()
