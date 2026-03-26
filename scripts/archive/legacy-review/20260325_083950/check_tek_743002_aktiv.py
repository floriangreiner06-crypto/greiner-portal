#!/usr/bin/env python3
"""
Prüft ob TEK 743002/G&V-Filter aktiv ist.
Aufruf: cd /opt/greiner-portal && venv/bin/python3 scripts/check_tek_743002_aktiv.py

- Zeigt Gesamt-Einsatz und DB1 aus get_tek_data()
- Zeigt 743002-Volumen im aktuellen Monat (wenn > 0, sollte Einsatz ohne 743002 niedriger sein)
"""
import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

from datetime import date
from dotenv import load_dotenv
load_dotenv('/opt/greiner-portal/config/.env', override=True)

from api.controlling_data import get_tek_data
from api.db_utils import db_session, row_to_dict, get_guv_filter

def main():
    heute = date.today()
    monat, jahr = heute.month, heute.year
    von = f"{jahr}-{monat:02d}-01"
    bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"

    print("=== TEK-Daten aus get_tek_data() (sollte 743002 + G&V ausschließen) ===")
    data = get_tek_data(monat=monat, jahr=jahr, firma='0', standort='0')
    gesamt = data.get('gesamt', {})
    print(f"Gesamt Einsatz: {gesamt.get('einsatz', 0):,.2f} €")
    print(f"Gesamt DB1:     {gesamt.get('db1', 0):,.2f} €")
    for b in data.get('bereiche', []):
        if b.get('id') == '4-Lohn':
            print(f"4-Lohn Einsatz: {b.get('einsatz', 0):,.2f} €")
            print(f"4-Lohn DB1:     {b.get('db1', 0):,.2f} €")
            break

    print("\n=== 743002-Volumen im aktuellen Monat (Portal DB: loco_journal_accountings) ===")
    guv_filter = get_guv_filter()
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as wert
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number = 743002
        """, (von, bis))
        row = cur.fetchone()
        wert_743002 = float(row[0] or 0) if row else 0
    print(f"743002 (EW Fremdleistungen) Saldo: {wert_743002:,.2f} €")
    if abs(wert_743002) > 1:
        print("  → Wenn dieser Betrag > 0: Einsatz in TEK sollte um diesen Betrag NIEDRIGER sein als ohne Filter.")
    else:
        print("  → Kein nennenswertes Volumen; 743002-Ausschluss ändert die Zahlen kaum.")

    print("\n=== Code-Check: Enthält controlling_data.py den 743002-Ausschluss? ===")
    p = '/opt/greiner-portal/api/controlling_data.py'
    with open(p, 'r') as f:
        content = f.read()
    if 'nominal_account_number != 743002' in content and 'get_guv_filter' in content:
        print("  JA – Datei enthält 743002-Ausschluss und G&V-Filter.")
    else:
        print("  NEIN – Datei scheint die Anpassung NICHT zu enthalten (bitte Sync/Deployment prüfen).")

if __name__ == '__main__':
    main()
