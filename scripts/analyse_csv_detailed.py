"""Detaillierte Analyse der CSV - welche Aufträge sind enthalten?"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor

# CSV-Pfad (Server)
csv_path = '/tmp/offene.csv'

# Lese CSV und extrahiere Auftragsnummern
auftrag_nrs = []
with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
    import csv
    reader = csv.reader(f, delimiter='\t')
    header_found = False
    for row in reader:
        if len(row) == 0:
            continue
        if len(row) > 0 and 'Auftragsnummer' in str(row[0]):
            header_found = True
            continue
        if header_found and len(row) > 0:
            try:
                auftrag_nr = int(row[0])
                auftrag_nrs.append(auftrag_nr)
            except:
                continue

print(f"CSV enthält {len(auftrag_nrs)} Aufträge")
print(f"Erste 10 Auftragsnummern: {auftrag_nrs[:10]}")

# Prüfe diese Aufträge in Locosoft
with locosoft_session() as conn:
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Prüfe: Sind diese Aufträge wirklich unfakturiert?
    cur.execute(f"""
        SELECT 
            o.number as auftrag_nr,
            COUNT(*) as anzahl_labours,
            COUNT(CASE WHEN l.invoice_number IS NULL THEN 1 END) as unfakt_labours,
            COUNT(CASE WHEN l.invoice_number IS NOT NULL THEN 1 END) as fakt_labours,
            SUM(CASE WHEN l.invoice_number IS NULL THEN l.time_units * COALESCE(ct1.timeunit_rate, ct2.timeunit_rate, 0) ELSE 0 END) / 100.0 as unfakt_vk,
            SUM(CASE WHEN l.invoice_number IS NULL THEN l.net_price_in_order ELSE 0 END) / 100.0 as unfakt_net_price
        FROM orders o
        LEFT JOIN labours l ON o.number = l.order_number
        LEFT JOIN charge_types ct1 ON l.charge_type = ct1.type AND o.subsidiary = ct1.subsidiary
        LEFT JOIN charge_types ct2 ON l.charge_type = ct2.type AND ct2.subsidiary = 1
        WHERE o.number = ANY(%s)
        GROUP BY o.number
        ORDER BY o.number
        LIMIT 20
    """, (auftrag_nrs[:100],))
    
    rows = cur.fetchall()
    print(f"\nErste 20 Aufträge aus CSV in Locosoft:")
    for r in rows:
        print(f"  Auftrag {r['auftrag_nr']}: {r['anzahl_labours']} Labours ({r['unfakt_labours']} unfakt, {r['fakt_labours']} fakt), VK={r['unfakt_vk']:.2f}€, net_price={r['unfakt_net_price']:.2f}€")
    
    # Gesamtsumme für alle CSV-Aufträge
    cur.execute(f"""
        SELECT 
            COUNT(DISTINCT o.number) as anzahl_auftraege,
            SUM(CASE WHEN l.invoice_number IS NULL THEN l.time_units * COALESCE(ct1.timeunit_rate, ct2.timeunit_rate, 0) ELSE 0 END) / 100.0 as gesamt_vk,
            SUM(CASE WHEN l.invoice_number IS NULL THEN l.net_price_in_order ELSE 0 END) / 100.0 as gesamt_net_price
        FROM orders o
        LEFT JOIN labours l ON o.number = l.order_number
        LEFT JOIN charge_types ct1 ON l.charge_type = ct1.type AND o.subsidiary = ct1.subsidiary
        LEFT JOIN charge_types ct2 ON l.charge_type = ct2.type AND ct2.subsidiary = 1
        WHERE o.number = ANY(%s)
    """, (auftrag_nrs,))
    
    row = cur.fetchone()
    print(f"\nGesamtsumme für alle CSV-Aufträge:")
    print(f"  Anzahl Aufträge: {row['anzahl_auftraege']}")
    print(f"  VK-Wert (timeunit_rate): {row['gesamt_vk']:.2f} EUR")
    print(f"  net_price_in_order: {row['gesamt_net_price']:.2f} EUR")
    print(f"\n  CSV zeigt: 127.075,39 EUR")
    print(f"  Differenz: {127075.39 - float(row['gesamt_vk']):.2f} EUR")
    
    # Prüfe: Gibt es bereits fakturierte Rechnungen für diese Aufträge?
    cur.execute(f"""
        SELECT 
            COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen,
            SUM(i.job_amount_net) / 100.0 as job_amount_sum,
            SUM(i.job_amount_gross) / 100.0 as job_amount_gross_sum
        FROM invoices i
        WHERE i.order_number = ANY(%s)
          AND i.is_canceled = false
    """, (auftrag_nrs,))
    
    row2 = cur.fetchone()
    print(f"\nBereits fakturierte Rechnungen für CSV-Aufträge:")
    print(f"  Anzahl Rechnungen: {row2['anzahl_rechnungen']}")
    print(f"  job_amount_net (Summe): {row2['job_amount_sum']:.2f} EUR")
    print(f"  job_amount_gross (Summe): {row2['job_amount_gross_sum']:.2f} EUR")
    
    # Kombiniert: Unfakturiert + Fakturiert
    gesamt_kombiniert = float(row['gesamt_vk']) + float(row2['job_amount_sum'] or 0)
    print(f"\nKombiniert (unfakt VK + fakt job_amount_net): {gesamt_kombiniert:.2f} EUR")
    print(f"  CSV zeigt: 127.075,39 EUR")
    print(f"  Differenz: {127075.39 - gesamt_kombiniert:.2f} EUR")
    
    cur.close()

