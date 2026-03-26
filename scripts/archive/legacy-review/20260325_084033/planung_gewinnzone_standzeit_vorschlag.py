#!/usr/bin/env python3
"""
Planung: Was brauchen wir für die Gewinnzone? Bereichspotenzial + Standzeit-Effekt
==================================================================================
- Gap zu Break-even (0 €) und zu 1 % Rendite (Gewinnzone)
- Größtes Potenzial pro Abteilung (NW, GW, Teile, Werkstatt, Sonstige)
- Zinskosten aus Locosoft (loco_journal_accountings: 895xxx, 4982x) – inkl. Zinsfreiheit
- Standzeit-Verbesserung: Ersparnis nur noch als Hinweis (gebuchte Zinsen sind Maßstab)
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.unternehmensplan_data import get_gap_analyse, get_current_geschaeftsjahr
from api.db_connection import get_db
from api.db_utils import locosoft_session, get_guv_filter

ZINSSATZ = 0.05
STANDZEIT_ALT = 300
STANDZEIT_NEU = 150

# Planungs-Annahme Zinskosten (nach Zinsfreiheit)
TAGE_UNTER_ZINS_ANNAHME = 90   # Gesamtbestand rechnerisch 90 Tage unter Zinsen
ZINSSATZ_ANNAHME = 0.05        # Durchschnittlicher Zins über alle Linien (Stellantis, Santander, Genobank)
# MwSt. wird nicht finanziert → Fahrzeugwert = netto (Locosoft: in_acntg_cost_unit_new_vehicle oder in_buy_list_price)


def get_gj_datum(gj: str):
    start = int(gj.split('/')[0])
    return f"{start}-09-01", f"{start + 1}-09-01"


def lade_zinskosten_aus_locosoft(von_datum: str, bis_datum: str) -> dict:
    """
    Zinskosten aus Locosoft (Portal: loco_journal_accountings).
    Konten: 895xxx, 4982x; plus in Locosoft tatsächlich genutzte 89x (Stellantis/Santander/Genobank):
    890501, 891001, 891711, 891712, 896711, 896712 (SOLL = Aufwand).
    """
    guv = get_guv_filter()
    out = {'zinskosten_895': 0.0, 'zinskosten_4982': 0.0, 'zinskosten_89x': 0.0, 'zinskosten_gesamt': 0.0, 'quelle': 'loco_journal_accountings'}

    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 895000 AND 895999
              {guv}
        """, (von_datum, bis_datum))
        out['zinskosten_895'] = float(cur.fetchone()[0] or 0)

        cur.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 498200 AND 498299
              {guv}
        """, (von_datum, bis_datum))
        out['zinskosten_4982'] = float(cur.fetchone()[0] or 0)

        # In Locosoft belegte Zinskosten-Konten (Stellantis/Santander/Genobank): SOLL = Aufwand
        cur.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE 0 END) / 100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number IN (890501, 891001, 891711, 891712, 896711, 896712)
              {guv}
        """, (von_datum, bis_datum))
        out['zinskosten_89x'] = float(cur.fetchone()[0] or 0)

        out['zinskosten_gesamt'] = out['zinskosten_895'] + out['zinskosten_4982'] + out['zinskosten_89x']

        # Falls 0: Alternative = Zinsen aus fahrzeugfinanzierungen (Portal, inkl. Zinsfreiheit)
        if out['zinskosten_gesamt'] == 0:
            try:
                cur.execute("""
                    SELECT COALESCE(SUM(zinsen_letzte_periode), 0) as monat,
                           COALESCE(SUM(zinsen_gesamt), 0) as kumuliert
                    FROM fahrzeugfinanzierungen
                    WHERE aktueller_saldo > 0
                """)
                row = cur.fetchone()
                if row and (row[0] or row[1]):
                    monat = float(row[0] or 0)
                    out['zinsen_fz_monat'] = monat
                    out['zinsen_fz_jahr_hochrechnung'] = round(monat * 12, 0)
                    out['zinskosten_gesamt'] = out['zinsen_fz_jahr_hochrechnung']
                    out['quelle'] = 'fahrzeugfinanzierungen (Hochrechnung Monat*12, inkl. Zinsfreiheit)'
            except Exception:
                pass
    finally:
        conn.close()

    return out


def lade_bestand_und_durchschnittswert_locosoft(standort: int = 0) -> dict:
    """
    Aktueller Fahrzeugbestand (noch nicht verkauft) aus Locosoft dealer_vehicles
    und durchschnittlicher Fahrzeugwert ohne MwSt. (MwSt. wird nicht finanziert).
    Wert = COALESCE(in_acntg_cost_unit_new_vehicle, in_buy_list_price) – in Locosoft i.d.R. netto.
    """
    from api.standort_utils import build_locosoft_filter_bestand
    standort_filter = build_locosoft_filter_bestand(standort, nur_stellantis=False)
    # Wert ohne MwSt.: Buchwert/ EK netto (Bank finanziert keine MwSt.)
    wert_sql = "COALESCE(dv.in_acntg_cost_unit_new_vehicle, dv.in_buy_list_price, 0)"
    out = {
        'anzahl_nw': 0, 'anzahl_gw': 0, 'anzahl_gesamt': 0,
        'avg_wert_netto_nw': 0.0, 'avg_wert_netto_gw': 0.0, 'avg_wert_netto_gesamt': 0.0,
        'summe_wert_netto_nw': 0.0, 'summe_wert_netto_gw': 0.0, 'summe_wert_netto_gesamt': 0.0,
    }
    try:
        with locosoft_session() as conn:
            cur = conn.cursor()
            # Bestand = noch nicht ausgeliefert
            base = f"""
                FROM dealer_vehicles dv
                WHERE dv.out_invoice_date IS NULL
                  AND COALESCE({wert_sql}, 0) > 0
                  {standort_filter}
            """
            # NW (N,T,V)
            cur.execute(f"""
                SELECT COUNT(*), COALESCE(AVG({wert_sql}), 0), COALESCE(SUM({wert_sql}), 0)
                {base}
                AND dv.dealer_vehicle_type IN ('N', 'T', 'V')
            """)
            row = cur.fetchone()
            if row and row[0]:
                out['anzahl_nw'] = int(row[0])
                out['avg_wert_netto_nw'] = float(row[1] or 0)
                out['summe_wert_netto_nw'] = float(row[2] or 0)
            # GW (D,G,L)
            cur.execute(f"""
                SELECT COUNT(*), COALESCE(AVG({wert_sql}), 0), COALESCE(SUM({wert_sql}), 0)
                {base}
                AND dv.dealer_vehicle_type IN ('D', 'G', 'L')
            """)
            row = cur.fetchone()
            if row and row[0]:
                out['anzahl_gw'] = int(row[0])
                out['avg_wert_netto_gw'] = float(row[1] or 0)
                out['summe_wert_netto_gw'] = float(row[2] or 0)
            # Gesamt
            cur.execute(f"""
                SELECT COUNT(*), COALESCE(AVG({wert_sql}), 0), COALESCE(SUM({wert_sql}), 0)
                {base}
            """)
            row = cur.fetchone()
            if row and row[0]:
                out['anzahl_gesamt'] = int(row[0])
                out['avg_wert_netto_gesamt'] = float(row[1] or 0)
                out['summe_wert_netto_gesamt'] = float(row[2] or 0)
    except Exception as e:
        out['_fehler'] = str(e)
    return out


def berechne_plan_zinskosten_annahme(bestand: dict) -> dict:
    """
    Plan-Zinskosten nach Annahme: Nach Zinsfreiheit 90 Tage unter Zinsen,
    durchschnittlich 5 % Zins, Fahrzeugwert ohne MwSt. aus Locosoft.
    Formel: Lagerwert_netto × (Tage/365) × Zinssatz  (mit Tage=90 für Gesamtbestand).
    """
    lagerwert = bestand.get('summe_wert_netto_gesamt') or 0
    tage = TAGE_UNTER_ZINS_ANNAHME
    zins = ZINSSATZ_ANNAHME
    zinskosten_plan = lagerwert * (tage / 365) * zins
    return {
        'zinskosten_plan_jahr': round(zinskosten_plan, 0),
        'lagerwert_netto_gesamt': lagerwert,
        'tage_unter_zins': tage,
        'zinssatz': zins,
        'annahme': f'{tage} Tage unter Zins, {zins*100:.0f} % Ø-Zins, Wert ohne MwSt. (Locosoft)',
    }


def standzeit_tage_expr(prefix: str = "dv") -> str:
    """SQL-Ausdruck: Standzeit in Tagen (Verkauf: Auslieferung - Ankunft; Bestand: heute - Ankunft)."""
    p = prefix
    return f"(COALESCE({p}.out_invoice_date, CURRENT_DATE) - COALESCE({p}.in_arrival_date, {p}.created_date))"


def lade_standzeiten_aus_locosoft(gj_vj: str, gj_vj2: str | None = None) -> dict:
    """
    Standzeiten aus Locosoft dealer_vehicles belegen (historisch + aktueller Bestand).
    - Historisch: verkaufte Fahrzeuge im GJ, Standzeit = out_invoice_date - COALESCE(in_arrival_date, created_date).
    - Bestand: out_invoice_date IS NULL, Standzeit = CURRENT_DATE - COALESCE(in_arrival_date, created_date).
    Liefert z. B. standzeit_nw/gw für VJ, standzeit_bestand_nw/gw, optional zweites VJ zum Vergleich.
    """
    von_vj, bis_vj = get_gj_datum(gj_vj)
    st_expr = standzeit_tage_expr("dv")
    out = {
        'gj_vj': gj_vj,
        'stueck_nw': 0, 'stueck_gw': 0,
        'standzeit_nw': 0, 'standzeit_gw': 0,
        'standzeit_bestand_nw': 0, 'standzeit_bestand_gw': 0,
        'stueck_bestand_nw': 0, 'stueck_bestand_gw': 0,
        'vj2': None,
        'standzeit_nw_vj2': 0, 'standzeit_gw_vj2': 0,
        'stueck_nw_vj2': 0, 'stueck_gw_vj2': 0,
    }
    try:
        with locosoft_session() as conn:
            cur = conn.cursor()
            # VJ: verkaufte Fahrzeuge (out_invoice_date im GJ), Standzeit = Auslieferung - Ankunft
            cur.execute(f"""
                SELECT COUNT(*), AVG({st_expr})
                FROM dealer_vehicles dv
                WHERE dv.out_invoice_date >= %s AND dv.out_invoice_date < %s
                  AND dv.out_invoice_date IS NOT NULL
                  AND (dv.in_arrival_date IS NOT NULL OR dv.created_date IS NOT NULL)
                  AND dv.dealer_vehicle_type IN ('N', 'T', 'V')
                  AND dv.out_subsidiary IN (1, 2, 3)
            """, (von_vj, bis_vj))
            row = cur.fetchone()
            out['stueck_nw'] = int(row[0] or 0)
            out['standzeit_nw'] = int(round(float(row[1] or 0), 0)) if row and row[1] is not None else 0

            cur.execute(f"""
                SELECT COUNT(*), AVG({st_expr})
                FROM dealer_vehicles dv
                WHERE dv.out_invoice_date >= %s AND dv.out_invoice_date < %s
                  AND dv.out_invoice_date IS NOT NULL
                  AND (dv.in_arrival_date IS NOT NULL OR dv.created_date IS NOT NULL)
                  AND dv.dealer_vehicle_type IN ('G', 'D', 'L')
                  AND dv.out_subsidiary IN (1, 2, 3)
            """, (von_vj, bis_vj))
            row = cur.fetchone()
            out['stueck_gw'] = int(row[0] or 0)
            out['standzeit_gw'] = int(round(float(row[1] or 0), 0)) if row and row[1] is not None else 0

            # Aktueller Bestand: noch nicht verkauft, Standzeit = heute - Ankunft/created
            cur.execute(f"""
                SELECT COUNT(*), AVG(CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date))
                FROM dealer_vehicles dv
                WHERE dv.out_invoice_date IS NULL
                  AND (dv.in_arrival_date IS NOT NULL OR dv.created_date IS NOT NULL)
                  AND dv.dealer_vehicle_type IN ('N', 'T', 'V')
                  AND dv.in_subsidiary IN (1, 2, 3)
            """)
            row = cur.fetchone()
            out['stueck_bestand_nw'] = int(row[0] or 0)
            out['standzeit_bestand_nw'] = int(round(float(row[1] or 0), 0)) if row and row[1] is not None else 0

            cur.execute(f"""
                SELECT COUNT(*), AVG(CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date))
                FROM dealer_vehicles dv
                WHERE dv.out_invoice_date IS NULL
                  AND (dv.in_arrival_date IS NOT NULL OR dv.created_date IS NOT NULL)
                  AND dv.dealer_vehicle_type IN ('G', 'D', 'L')
                  AND dv.in_subsidiary IN (1, 2, 3)
            """)
            row = cur.fetchone()
            out['stueck_bestand_gw'] = int(row[0] or 0)
            out['standzeit_bestand_gw'] = int(round(float(row[1] or 0), 0)) if row and row[1] is not None else 0

            # Optional: zweites Vorjahr (z. B. 2023/24) zum Vergleich
            if gj_vj2:
                von2, bis2 = get_gj_datum(gj_vj2)
                out['vj2'] = gj_vj2
                cur.execute(f"""
                    SELECT COUNT(*), AVG({st_expr})
                    FROM dealer_vehicles dv
                    WHERE dv.out_invoice_date >= %s AND dv.out_invoice_date < %s
                      AND dv.out_invoice_date IS NOT NULL
                      AND (dv.in_arrival_date IS NOT NULL OR dv.created_date IS NOT NULL)
                      AND dv.dealer_vehicle_type IN ('N', 'T', 'V')
                      AND dv.out_subsidiary IN (1, 2, 3)
                """, (von2, bis2))
                row = cur.fetchone()
                out['stueck_nw_vj2'] = int(row[0] or 0)
                out['standzeit_nw_vj2'] = int(round(float(row[1] or 0), 0)) if row and row[1] is not None else 0
                cur.execute(f"""
                    SELECT COUNT(*), AVG({st_expr})
                    FROM dealer_vehicles dv
                    WHERE dv.out_invoice_date >= %s AND dv.out_invoice_date < %s
                      AND dv.out_invoice_date IS NOT NULL
                      AND (dv.in_arrival_date IS NOT NULL OR dv.created_date IS NOT NULL)
                      AND dv.dealer_vehicle_type IN ('G', 'D', 'L')
                      AND dv.out_subsidiary IN (1, 2, 3)
                """, (von2, bis2))
                row = cur.fetchone()
                out['stueck_gw_vj2'] = int(row[0] or 0)
                out['standzeit_gw_vj2'] = int(round(float(row[1] or 0), 0)) if row and row[1] is not None else 0
    except Exception as e:
        out['_fehler'] = str(e)
    return out


def schaetze_zinskosten_ersparnis_standzeit(gj_vj: str, zinskosten_vj_gebucht: float, standzeiten: dict | None = None) -> dict:
    """
    Ergänzt Standzeit-Infos (Stück, Standzeit VJ) und optionale Ersparnis-Schätzung.
    zinskosten_vj_gebucht = aus Locosoft (loco_journal_accountings), inkl. Zinsfreiheit.
    standzeiten = optional von lade_standzeiten_aus_locosoft(gj_vj), sonst wird intern geladen.
    Ersparnis = grobe Schätzung falls Standzeit von 300 auf 150 reduziert wurde (25 % der gebuchten Zinsen).
    """
    if standzeiten is None:
        standzeiten = lade_standzeiten_aus_locosoft(gj_vj)
    out = {
        'stueck_nw': standzeiten['stueck_nw'], 'stueck_gw': standzeiten['stueck_gw'],
        'standzeit_nw': standzeiten['standzeit_nw'], 'standzeit_gw': standzeiten['standzeit_gw'],
        'zinskosten_vj_gebucht': zinskosten_vj_gebucht,
        'ersparnis_schaetzung': round(zinskosten_vj_gebucht * 0.25, 0) if zinskosten_vj_gebucht > 0 else 0,
    }
    if standzeiten.get('_fehler'):
        out['_fallback'] = standzeiten['_fehler']
    return out


def main():
    gj = get_current_geschaeftsjahr()
    start = int(gj.split('/')[0])
    gj_vj = f"{start - 1}/{str(start)[-2:]}"

    print("=" * 70)
    print("Planung: Gewinnzone – Was müssen wir planen? Bereichspotenzial + Standzeit")
    print("=" * 70)
    print(f"Geschäftsjahr: {gj}  |  Vorjahr (für Standzeit): {gj_vj}")
    print()

    # 1) Gap-Analyse (zum 1%-Ziel; Break-even = 0)
    try:
        gap = get_gap_analyse(gj, standort=0)
    except Exception as e:
        print(f"Fehler Gap-Analyse: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    prognose = gap['prognose_jahresende']
    ziel_1pct = gap['ziel_jahresende']['ergebnis']
    gap_1pct = gap['gap_jahresende']
    gap_null = 0 - prognose['ergebnis']  # Wie viel fehlt zu Break-even

    print("--- Aktuelle Prognose Jahresende (ohne Standzeit-Effekt) ---")
    print(f"  Umsatz (Hochrechnung):  {prognose['umsatz']:,.0f} €")
    print(f"  Ergebnis (Prognose):   {prognose['ergebnis']:,.0f} €  ({prognose['rendite']:.2f} % Rendite)")
    print(f"  Ziel 1 % (Gewinnzone): {ziel_1pct:,.0f} €")
    print(f"  → Gap zu Break-even (0 €):     {gap_null:,.0f} € (müssen wir zulegen)")
    print(f"  → Gap zum 1 %-Ziel:            {gap_1pct:,.0f} €")
    print()

    # 2) Bereichspotenzial (größtes Potenzial zuerst)
    print("--- Potenzial nach Abteilung (DB1-Verbesserung bei Erreichen Ziel-Marge) ---")
    bereiche = gap.get('bereiche', [])
    if not bereiche:
        print("  (Keine Bereichsdaten verfügbar – evtl. nur YTD-Struktur)")
    else:
        for b in bereiche:
            status = '🔴' if b['status'] == 'kritisch' else ('🟡' if b['status'] == 'warnung' else '🟢')
            print(f"  {status} {b['bereich']:12} Marge IST {b['marge_ist']:.1f} % → Ziel {b['marge_ziel']:.0f} %  |  Potenzial DB1: {b['potenzial_db1']:,.0f} €")
        groesstes = max(bereiche, key=lambda x: x['potenzial_db1']) if bereiche else None
        if groesstes and groesstes['potenzial_db1'] > 0:
            print(f"  → Größtes Potenzial: {groesstes['bereich']} (+{groesstes['potenzial_db1']:,.0f} € DB1 bei Ziel-Marge)")
    print()

    # 3) Standzeiten aus Locosoft (historisch + Bestand) belegen
    gj_vj2 = f"{start - 2}/{str(start - 1)[-2:]}"  # z. B. 2023/24
    standzeiten = lade_standzeiten_aus_locosoft(gj_vj, gj_vj2=gj_vj2)

    # 4) Zinskosten aus Locosoft (inkl. Zinsfreiheit) + Ersparnis
    von_vj, bis_vj = get_gj_datum(gj_vj)
    zins_vj = lade_zinskosten_aus_locosoft(von_vj, bis_vj)
    zinskosten_vj = zins_vj['zinskosten_gesamt']

    st = schaetze_zinskosten_ersparnis_standzeit(gj_vj, zinskosten_vj, standzeiten=standzeiten)

    print("--- Zinskosten aus Locosoft / Portal (inkl. Zinsfreiheit) ---")
    print(f"  Quelle: {zins_vj.get('quelle', 'loco_journal_accountings')}")
    z89x = zins_vj.get('zinskosten_89x', 0)
    print(f"  Vorjahr {gj_vj}:  {zinskosten_vj:,.0f} €  (895xxx: {zins_vj['zinskosten_895']:,.0f} €, 4982x: {zins_vj['zinskosten_4982']:,.0f} €, 89x: {z89x:,.0f} €)")
    if zinskosten_vj == 0 and zins_vj.get('zinsen_fz_jahr_hochrechnung'):
        print(f"  → Fallback: Fahrzeugfinanzierungen (Portal) Hochrechnung: {zins_vj['zinsen_fz_jahr_hochrechnung']:,.0f} €/Jahr (Monat × 12, inkl. Zinsfreiheit)")
    elif zinskosten_vj == 0:
        print("  Hinweis: Keine Buchungen auf 895/4982/89x im Portal. Zinskosten ggf. unter anderen Konten.")
    # Plan-Zinskosten (Annahme: 90 Tage unter Zins, 5 %, Ø-Wert ohne MwSt. aus Locosoft)
    bestand = lade_bestand_und_durchschnittswert_locosoft(standort=0)
    plan_zins = berechne_plan_zinskosten_annahme(bestand)
    print()
    print("--- Plan-Zinskosten (Annahme: nach Zinsfreiheit 90 Tage unter Zinsen, 5 % Ø-Zins, Wert ohne MwSt.) ---")
    print(f"  Bestand (Locosoft, Stichtag): NW {bestand['anzahl_nw']}, GW {bestand['anzahl_gw']} → gesamt {bestand['anzahl_gesamt']} Fahrzeuge")
    print(f"  Ø Wert netto (ohne MwSt.): NW {bestand['avg_wert_netto_nw']:,.0f} €, GW {bestand['avg_wert_netto_gw']:,.0f} €, gesamt {bestand['avg_wert_netto_gesamt']:,.0f} €")
    if bestand['anzahl_nw'] and bestand['avg_wert_netto_nw'] < 1000:
        print("  (Hinweis: NW-Ø-Wert wirkt niedrig – in Locosoft evtl. in_acntg_cost_unit_new_vehicle/in_buy_list_price für NW nicht befüllt)")
    print(f"  Lagerwert netto gesamt: {bestand['summe_wert_netto_gesamt']:,.0f} €")
    print(f"  → Zinskosten Plan (90 Tage × 5 %): {plan_zins['zinskosten_plan_jahr']:,.0f} €/Jahr")
    print()
    print("--- Standzeiten aus Locosoft (dealer_vehicles) ---")
    print("  Standzeiten des Bestands (Stichtag, noch nicht verkaufte Fz) – relevant für Planung/Zinsen:")
    print(f"    NW: {standzeiten['stueck_bestand_nw']} Stück, Ø Standzeit {standzeiten['standzeit_bestand_nw']} Tage  |  GW: {standzeiten['stueck_bestand_gw']} Stück, Ø Standzeit {standzeiten['standzeit_bestand_gw']} Tage")
    print("  Zum Vergleich – Standzeiten der verkauften Fahrzeuge (wie lange lagen sie vor Verkauf):")
    print(f"    VJ {gj_vj}: NW {st['stueck_nw']} Stück, Ø {st['standzeit_nw']} Tage  |  GW {st['stueck_gw']} Stück, Ø {st['standzeit_gw']} Tage")
    if standzeiten.get('vj2'):
        print(f"    VJ {standzeiten['vj2']}: NW {standzeiten['stueck_nw_vj2']} Stück, Ø {standzeiten['standzeit_nw_vj2']} Tage  |  GW {standzeiten['stueck_gw_vj2']} Stück, Ø {standzeiten['standzeit_gw_vj2']} Tage")
    if standzeiten.get('_fehler'):
        print(f"  (Hinweis: {standzeiten['_fehler']})")
    print(f"  Geschätzte Ersparnis durch Standzeit-Reduktion (300→150 Tage, grob): {st['ersparnis_schaetzung']:,.0f} €/Jahr")
    print()

    # 4) Was müssen wir planen?
    ersparnis = st['ersparnis_schaetzung']
    gap_nach_standzeit = gap_null - ersparnis
    gap_1pct_nach_standzeit = gap_1pct - ersparnis

    print("--- Was müssen wir planen, um in die Gewinnzone zu kommen? ---")
    print(f"  Mit Standzeit-Ersparnis ({ersparnis:,.0f} €) reduziert sich der Fehlbetrag:")
    print(f"  → Gap zu Break-even nach Standzeit-Effekt: {gap_nach_standzeit:,.0f} €")
    print(f"  → Gap zum 1 %-Ziel nach Standzeit-Effekt:   {gap_1pct_nach_standzeit:,.0f} €")
    print()
    if groesstes and groesstes['potenzial_db1'] >= gap_nach_standzeit and gap_nach_standzeit > 0:
        print(f"  Vorschlag: Fokus auf {groesstes['bereich']} – Potenzial ({groesstes['potenzial_db1']:,.0f} €) reicht theoretisch für Break-even.")
    elif bereiche and gap_nach_standzeit > 0:
        summe_potenzial = sum(b['potenzial_db1'] for b in bereiche)
        print(f"  Vorschlag: Kombination aus mehreren Bereichen (Gesamtpotenzial DB1: {summe_potenzial:,.0f} €) + Standzeit-Ersparnis.")
        print(f"  Priorität: {', '.join(b['bereich'] for b in bereiche[:3])} (nach Potenzial).")
    print()
    print("(Zinskosten = gebuchte Werte aus Locosoft, inkl. Zinsfreiheitsperioden.)")
    print("=" * 70)


if __name__ == "__main__":
    main()
