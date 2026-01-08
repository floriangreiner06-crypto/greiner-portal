"""
Berechnung: Gesamtfahrzeug-Stückzahl - Summe der Standorte
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.gewinnplanung_v2_gw_data import lade_vorjahr_gw

print("=" * 100)
print("BERECHNUNG: Gesamtfahrzeug-Stückzahl")
print("=" * 100)

# Zeitraum: Geschäftsjahr 2024/25
geschaeftsjahr = '2025/26'

print("\n1. Einzelne Standorte:")
print("-" * 100)

# Opel DEG (Standort 1, nur Stellantis)
vj_opel = lade_vorjahr_gw(1, geschaeftsjahr, None, nur_stellantis=True)
print(f"Opel DEG (Standort 1, nur Stellantis): {vj_opel['stueck']} Stk.")

# Hyundai (Standort 2)
vj_hyundai = lade_vorjahr_gw(2, geschaeftsjahr, None, nur_stellantis=False)
print(f"Hyundai Deg (Standort 2): {vj_hyundai['stueck']} Stk.")

# Landau (Standort 3)
vj_landau = lade_vorjahr_gw(3, geschaeftsjahr, None, nur_stellantis=False)
print(f"Landau (Standort 3): {vj_landau['stueck']} Stk.")

# Summe
summe_einzel = vj_opel['stueck'] + vj_hyundai['stueck'] + vj_landau['stueck']
print(f"\nSumme (Opel DEG + Hyundai + Landau): {summe_einzel} Stk.")

print("\n\n2. Gesamtbetrieb (Standort 0):")
print("-" * 100)

# Gesamtbetrieb direkt
from api.gewinnplanung_v2_gw_api import get_vorjahr
from flask import Flask
from unittest.mock import patch

# Mock Flask request context
app = Flask(__name__)
with app.test_request_context('/api/gewinnplanung/v2/gw/vorjahr/0?geschaeftsjahr=2025/26'):
    # Direkt die Logik ausführen
    from api.db_utils import locosoft_session, db_session, row_to_dict
    from api.controlling_api import build_firma_standort_filter, BEREICHE_CONFIG, _berechne_bereich_werte
    from api.db_connection import convert_placeholders
    
    vj_von = "2024-09-01"
    vj_bis = "2025-09-01"
    
    # Gesamtbetrieb BWA-Werte
    with db_session() as conn:
        cursor = conn.cursor()
        firma_filter_umsatz, firma_filter_einsatz, _, _ = build_firma_standort_filter('0', '0')
        guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
        
        gw_config = BEREICHE_CONFIG['GW']
        gw_werte = _berechne_bereich_werte(cursor, 'GW', gw_config, vj_von, vj_bis,
                                                   firma_filter_umsatz, guv_filter, firma_filter_einsatz)
        
        # Stückzahl aus Locosoft (alle Standorte)
        with locosoft_session() as conn_loco:
            cursor_loco = conn_loco.cursor()
            cursor_loco.execute(f"""
                SELECT COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('G', 'D', 'L')
            """, (vj_von, vj_bis))
            row = cursor_loco.fetchone()
            gesamt_stueck = int(row[0] or 0) if row else 0
    
    print(f"Gesamtbetrieb (Standort 0): {gesamt_stueck} Stk.")
    print(f"Umsatz: {gw_werte['erlos']:,.2f} €")
    print(f"DB1: {gw_werte['bruttoertrag']:,.2f} €")

print("\n\n" + "=" * 100)
print("VERGLEICH:")
print(f"  Summe Einzelstandorte: {summe_einzel} Stk.")
print(f"  Gesamtbetrieb (Standort 0): {gesamt_stueck} Stk.")
print(f"  Differenz: {abs(summe_einzel - gesamt_stueck)} Stk.")
print(f"\n  Global Cube (erwartet): 625 Stk.")
print(f"  Aktuell (DRIVE): {gesamt_stueck} Stk.")
print(f"  Differenz zu Global Cube: {abs(gesamt_stueck - 625)} Stk. ({abs(gesamt_stueck - 625)/625*100:.1f}%)")
print("=" * 100)

if summe_einzel == gesamt_stueck:
    print("\n✅ Summe der Einzelstandorte = Gesamtbetrieb (konsistent)")
else:
    print(f"\n⚠️  Summe der Einzelstandorte ≠ Gesamtbetrieb (Differenz: {abs(summe_einzel - gesamt_stueck)} Stk.)")

