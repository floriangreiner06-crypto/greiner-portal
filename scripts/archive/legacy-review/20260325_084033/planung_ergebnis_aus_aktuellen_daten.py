#!/usr/bin/env python3
"""
Planung: Welches Ergebnis käme mit den aktuellen Daten raus?
================================================================
Nutzt:
- IST Vorjahr (VJ): zuerst aus Portal (loco_journal_accountings), Fallback Unternehmensplan-API
- IST YTD aktuelles Geschäftsjahr aus Unternehmensplan-Logik
- Hochrechnung: Umsatz/DB1 = YTD * 12 / Monate_abgelaufen
- Kosten-Budget: Mittelwert (VJ_Kosten + YTD_Kosten_hochgerechnet) / 2
- Ergebnis = Plan_DB1 - Kosten_Budget, Rendite = Ergebnis / Plan_Umsatz

Konzern (Standort 0). Geschäftsjahr Sep–Aug.
Kosten aus Locosoft-Konten (Portal-Spiegelung loco_journal_accountings).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.unternehmensplan_data import (
    get_ist_daten,
    get_current_geschaeftsjahr,
    get_letzter_abgeschlossener_monat,
    get_gj_months,
)
from api.db_connection import get_db
from api.db_utils import get_guv_filter

# Konzern-Filter wie in unternehmensplan_data (Standort 0): Umlage-Konten ausblenden
UMLAGE_ERLOESE = (817051, 827051, 837051, 847051)
UMLAGE_KOSTEN = (498001,)


def get_gj_datum(gj: str):
    """GJ '2024/25' -> (von_datum, bis_datum) für Portal-Queries."""
    start = int(gj.split('/')[0])
    return f"{start}-09-01", f"{start + 1}-09-01"


def lade_vj_aus_portal(gj: str) -> dict:
    """
    Lädt Vorjahres-Summen (Umsatz, Einsatz, DB1, Kosten) aus der Portal-DB
    (loco_journal_accountings = Locosoft-Konten gespiegelt). Konzern (Standort 0).
    BWA-konforme Logik: Umlage-Konten ausgeblendet, G&V-Filter.
    """
    von, bis = get_gj_datum(gj)
    umlage_erloese_str = ','.join(map(str, UMLAGE_ERLOESE))
    umlage_kosten_str = ','.join(map(str, UMLAGE_KOSTEN))
    guv = get_guv_filter()

    out = {
        'umsatz': 0.0, 'einsatz': 0.0, 'db1': 0.0,
        'variable_kosten': 0.0, 'direkte_kosten': 0.0, 'indirekte_kosten': 0.0, 'kosten': 0.0,
        'ergebnis': 0.0, 'rendite': 0.0
    }

    conn = get_db()
    try:
        cur = conn.cursor()

        # Umsatz (Konzern: Umlage-Erlöse ausblenden)
        cur.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              AND nominal_account_number NOT IN ({umlage_erloese_str})
              {guv}
        """, (von, bis))
        out['umsatz'] = float(cur.fetchone()[0] or 0)

        # Einsatz
        cur.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
              {guv}
        """, (von, bis))
        out['einsatz'] = float(cur.fetchone()[0] or 0)
        out['db1'] = out['umsatz'] - out['einsatz']

        # Variable Kosten
        cur.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR (nominal_account_number BETWEEN 455000 AND 456999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR (nominal_account_number BETWEEN 487000 AND 487099 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR nominal_account_number BETWEEN 491000 AND 497899
              )
              {guv}
        """, (von, bis))
        out['variable_kosten'] = float(cur.fetchone()[0] or 0)

        # Direkte Kosten
        cur.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 400000 AND 489999
              AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
              AND NOT (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 424000 AND 424999
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR nominal_account_number BETWEEN 438000 AND 438999
                OR nominal_account_number BETWEEN 455000 AND 456999
                OR nominal_account_number BETWEEN 487000 AND 487099
                OR nominal_account_number BETWEEN 491000 AND 497999
              )
              {guv}
        """, (von, bis))
        out['direkte_kosten'] = float(cur.fetchone()[0] or 0)

        # Indirekte Kosten (Konzern: 498001 ausblenden)
        cur.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND (
                (nominal_account_number BETWEEN 400000 AND 499999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                OR (nominal_account_number BETWEEN 424000 AND 424999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR (nominal_account_number BETWEEN 438000 AND 438999 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR (nominal_account_number BETWEEN 498000 AND 499999 AND nominal_account_number NOT IN ({umlage_kosten_str}))
                OR (nominal_account_number BETWEEN 891000 AND 896999 AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
              )
              {guv}
        """, (von, bis))
        out['indirekte_kosten'] = float(cur.fetchone()[0] or 0)

        out['kosten'] = out['variable_kosten'] + out['direkte_kosten'] + out['indirekte_kosten']
        out['ergebnis'] = out['db1'] - out['kosten']
        out['rendite'] = (out['ergebnis'] / out['umsatz'] * 100) if out['umsatz'] else 0
    finally:
        conn.close()

    return out


def gj_monat_abgelaufen(gj: str, kal_monat: int, kal_jahr: int) -> bool:
    """Liefert True wenn der Kalendermonat im GJ bereits abgelaufen ist."""
    start_jahr = int(gj.split('/')[0])
    # GJ: 1=Sep start_jahr, 2=Okt, ..., 4=Dez, 5=Jan start_jahr+1, ..., 12=Aug
    if kal_monat >= 9:
        gj_monat = kal_monat - 8
        gj_jahr = start_jahr
    else:
        gj_monat = kal_monat + 4
        gj_jahr = start_jahr + 1
    if gj_jahr < int(gj.split('/')[0]) + 1:
        return True
    from datetime import date
    heute = date.today()
    return (kal_jahr < heute.year) or (kal_jahr == heute.year and kal_monat < heute.month)


def anzahl_abgelaufene_gj_monate(gj: str) -> int:
    """Anzahl abgelaufener Monate im Geschäftsjahr (1–12)."""
    letzter_m, letzter_j = get_letzter_abgeschlossener_monat()
    start_jahr = int(gj.split('/')[0])
    if letzter_m >= 9:
        gj_monat = letzter_m - 8
    else:
        gj_monat = letzter_m + 4
    # letzter abgeschlossener Monat: z.B. Jan 2026 → GJ 2025/26 Monat 5
    if letzter_j == start_jahr and letzter_m >= 9:
        return gj_monat
    if letzter_j == start_jahr + 1 and letzter_m <= 8:
        return letzter_m + 4  # Jan=5, Feb=6, ..., Aug=12
    return min(12, gj_monat)


def main():
    standort = 0  # Konzern
    gj_aktuell = get_current_geschaeftsjahr()
    start = int(gj_aktuell.split('/')[0])
    gj_vj = f"{start - 1}/{str(start)[-2:]}"

    print("=" * 64)
    print("Planung: Ergebnis mit aktuellen Daten (Hochrechnung + Kosten-Mittelwert)")
    print("=" * 64)
    print(f"Aktuelles GJ: {gj_aktuell}  |  Vorjahr: {gj_vj}  |  Standort: Konzern (0)")
    print()

    # VJ: zuerst aus Portal (loco_journal_accountings = Locosoft-Konten), dann Fallback API
    try:
        g_vj = lade_vj_aus_portal(gj_vj)
        if g_vj['umsatz'] == 0 and g_vj['kosten'] == 0:
            ist_vj = get_ist_daten(gj_vj, standort=standort, nur_abgeschlossene=True)
            g_vj = ist_vj['gesamt']
            print("Hinweis: VJ aus Portal leer; Fallback auf Unternehmensplan-API (Locosoft live).")
    except Exception as e:
        print(f"VJ aus Portal fehlgeschlagen ({e}); Fallback auf API.")
        ist_vj = get_ist_daten(gj_vj, standort=standort, nur_abgeschlossene=True)
        g_vj = ist_vj['gesamt']

    try:
        ist_ytd = get_ist_daten(gj_aktuell, standort=standort, nur_abgeschlossene=True)
        g_ytd = ist_ytd['gesamt']
    except Exception as e:
        print(f"Fehler beim Laden der YTD-Daten: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    monate_ytd = anzahl_abgelaufene_gj_monate(gj_aktuell)
    if monate_ytd <= 0:
        monate_ytd = 1

    # Hochrechnung aktuelles Jahr (linear auf 12 Monate)
    umsatz_hoch = g_ytd['umsatz'] * 12 / monate_ytd
    db1_hoch = g_ytd['db1'] * 12 / monate_ytd

    # Kosten-Budget = Mittelwert (VJ + hochgerechnetes IST); falls VJ fehlt nur Hochrechnung
    kosten_hoch = g_ytd['kosten'] * 12 / monate_ytd
    if g_vj['kosten'] > 0:
        kosten_budget = (g_vj['kosten'] + kosten_hoch) / 2
    else:
        kosten_budget = kosten_hoch
        print("Hinweis: Vorjahr-Kosten = 0; Kosten-Budget = YTD-Hochrechnung.")
        print()

    # Ergebnis = Plan DB1 - Kosten Budget (Plan = Hochrechnung)
    ergebnis_plan = db1_hoch - kosten_budget
    rendite_plan = (ergebnis_plan / umsatz_hoch * 100) if umsatz_hoch else 0

    # Zum Vergleich: wenn Plan = Vorjahr (DB1 und Umsatz VJ, nur Kosten Mittelwert)
    ergebnis_vj_plan = g_vj['db1'] - kosten_budget
    rendite_vj_plan = (ergebnis_vj_plan / g_vj['umsatz'] * 100) if g_vj['umsatz'] else 0

    print("--- IST ---")
    print(f"Vorjahr {gj_vj} (12 Monate, Quelle: Portal loco_journal_accountings / Locosoft-Konten):")
    print(f"  Umsatz: {g_vj['umsatz']:,.0f} €  |  DB1: {g_vj['db1']:,.0f} €  |  Kosten: {g_vj['kosten']:,.0f} €  |  Ergebnis: {g_vj['ergebnis']:,.0f} €  |  Rendite: {g_vj['rendite']:.2f} %")
    print(f"Aktuell {gj_aktuell} YTD ({monate_ytd} Monate):")
    print(f"  Umsatz: {g_ytd['umsatz']:,.0f} €  |  DB1: {g_ytd['db1']:,.0f} €  |  Kosten: {g_ytd['kosten']:,.0f} €  |  Ergebnis: {g_ytd['ergebnis']:,.0f} €  |  Rendite: {(g_ytd['ergebnis']/g_ytd['umsatz']*100) if g_ytd['umsatz'] else 0:.2f} %")
    print()
    print("--- Plan-Annahme ---")
    print("  Umsatz/DB1: Hochrechnung YTD auf 12 Monate")
    print("  Kosten: Mittelwert (VJ + hochgerechnetes YTD)")
    print()
    print("--- Ergebnis bei dieser Planung ---")
    print(f"  Plan Umsatz (Hochrechnung):  {umsatz_hoch:,.0f} €")
    print(f"  Plan DB1 (Hochrechnung):     {db1_hoch:,.0f} €")
    print(f"  Kosten-Budget (Mittelwert):  {kosten_budget:,.0f} €")
    print(f"  → Ergebnis (Plan):           {ergebnis_plan:,.0f} €")
    print(f"  → Rendite (Plan):            {rendite_plan:.2f} %")
    print()
    print("--- Zum Vergleich (Plan = Vorjahr-Umsatz/DB1, Kosten = Mittelwert) ---")
    if g_vj['umsatz'] > 0:
        print(f"  → Ergebnis: {ergebnis_vj_plan:,.0f} €  |  Rendite: {rendite_vj_plan:.2f} %")
    else:
        print("  → (Vorjahr-Umsatz = 0, Vergleich entfällt)")
    print()
    print("(Ziel Unternehmensplan: 1 % Rendite)")
    print("=" * 64)


if __name__ == "__main__":
    main()
