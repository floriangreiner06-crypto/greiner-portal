"""
Analyse: Gesamtstückzahl GW - Vergleich BWA vs. Locosoft
=========================================================
Prüft, woher die 771 Stück kommen und warum es nicht 625 sind.
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session, db_session, row_to_dict
from api.db_connection import convert_placeholders
from api.controlling_api import build_firma_standort_filter, BEREICHE_CONFIG, _berechne_bereich_werte

print("=" * 100)
print("ANALYSE: Gesamtstückzahl GW - Vergleich BWA vs. Locosoft")
print("=" * 100)

# Zeitraum: Geschäftsjahr 2024/25 (Sep 2024 - Aug 2025)
vj_von = "2024-09-01"
vj_bis = "2025-09-01"

print(f"\nZeitraum: {vj_von} bis {vj_bis}")
print("\n" + "=" * 100)

# 1. Locosoft: Gesamtstückzahl (alle Standorte)
print("\n1. LOCOSOFT - Gesamtstückzahl (alle Standorte, alle subsidiaries):")
print("-" * 100)

with locosoft_session() as conn_loco:
    cursor_loco = conn_loco.cursor()
    
    # Alle GW-Verkäufe
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
    """, (vj_von, vj_bis))
    
    row = cursor_loco.fetchone()
    gesamt_stueck = int(row[0] or 0) if row else 0
    print(f"Gesamtstückzahl: {gesamt_stueck} Stk.")
    
    # Nach subsidiary aufgeschlüsselt
    cursor_loco.execute("""
        SELECT 
            out_subsidiary,
            COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
        GROUP BY out_subsidiary
        ORDER BY out_subsidiary
    """, (vj_von, vj_bis))
    
    rows = cursor_loco.fetchall()
    print(f"\nNach subsidiary aufgeschlüsselt:")
    print(f"{'Subsidiary':<15} {'Stück':<10}")
    print("-" * 100)
    summe = 0
    for row in rows:
        print(f"{row[0]:<15} {row[1]:<10}")
        summe += row[1]
    print(f"{'Summe':<15} {summe:<10}")
    
    # Nach Standort (wie in der API verwendet)
    print(f"\n\n1b. LOCOSOFT - Nach Standort (wie in API verwendet):")
    print("-" * 100)
    
    # Opel DEG (subsidiary=1)
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
          AND out_subsidiary = 1
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    opel_deg = int(row[0] or 0) if row else 0
    print(f"Opel DEG (subsidiary=1): {opel_deg} Stk.")
    
    # Hyundai (subsidiary=2)
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
          AND out_subsidiary = 2
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    hyundai = int(row[0] or 0) if row else 0
    print(f"Hyundai (subsidiary=2): {hyundai} Stk.")
    
    # Landau (subsidiary=3)
    cursor_loco.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('G', 'D', 'L')
          AND out_subsidiary = 3
    """, (vj_von, vj_bis))
    row = cursor_loco.fetchone()
    landau = int(row[0] or 0) if row else 0
    print(f"Landau (subsidiary=3): {landau} Stk.")
    
    summe_standorte = opel_deg + hyundai + landau
    print(f"\nSumme (Opel DEG + Hyundai + Landau): {summe_standorte} Stk.")
    print(f"Gesamt (alle subsidiaries): {gesamt_stueck} Stk.")
    print(f"Differenz: {gesamt_stueck - summe_standorte} Stk.")

# 2. BWA: Gesamtbetrieb GW-Werte
print("\n\n2. BWA - Gesamtbetrieb GW-Werte:")
print("-" * 100)

with db_session() as conn:
    cursor = conn.cursor()
    
    firma_filter_umsatz, firma_filter_einsatz, _, _ = build_firma_standort_filter('0', '0')
    guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
    
    gw_config = BEREICHE_CONFIG['GW']
    gw_werte = _berechne_bereich_werte(cursor, 'GW', gw_config, vj_von, vj_bis,
                                       firma_filter_umsatz, guv_filter, firma_filter_einsatz)
    
    print(f"Umsatz: {gw_werte['erlos']:,.2f} €")
    print(f"Einsatz: {gw_werte['einsatz']:,.2f} €")
    print(f"DB1: {gw_werte['bruttoertrag']:,.2f} €")

# 3. API: Was gibt die API zurück?
print("\n\n3. API - Was gibt get_vorjahr(standort=0) zurück?")
print("-" * 100)

from api.gewinnplanung_v2_gw_api import get_vorjahr
from flask import Flask
from unittest.mock import Mock

app = Flask(__name__)
with app.test_request_context('/api/gewinnplanung/v2/gw/vorjahr/0?geschaeftsjahr=2025/26'):
    from flask import request
    result = get_vorjahr(0)
    
    if result[0].status_code == 200:
        import json
        data = json.loads(result[0].data)
        if data.get('success') and data.get('vorjahr'):
            vj = data['vorjahr']
            print(f"Stück: {vj.get('stueck', 0)} Stk.")
            print(f"Umsatz: {vj.get('umsatz', 0):,.2f} €")
            print(f"DB1: {vj.get('db1', 0):,.2f} €")

print("\n\n" + "=" * 100)
print("ERWARTET: 625 Stk. (aus Global Cube?)")
print("AKTUELL: 771 Stk. (aus API)")
print("DIFFERENZ: 146 Stk.")
print("=" * 100)

