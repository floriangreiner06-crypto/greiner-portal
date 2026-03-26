#!/usr/bin/env python3
"""
Planungsszenario: Ergebnis bei 1000 GW + 100 NW mehr
=====================================================
Rechnet das Planungsergebnis aus, wenn:
- GW mit Ziel-Marge bei 1000 Stück (statt Hochrechnung)
- NW zusätzlich 100 Stück mehr (Ziel-Marge 8 %)

- GW-Umsatz (neu) = 1000 × Ø-VK_GW, GW-DB1 = GW-Umsatz × 5 %
- NW-Zusatz: +100 × Ø-VK_NW Umsatz, +100 × Ø-VK_NW × 8 % DB1
- Übrige Bereiche unverändert. Plan-Ergebnis = Plan-DB1 gesamt − Kosten-Budget
"""

import sys
import os
from datetime import date
from calendar import monthrange

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.db_utils import locosoft_session
from api.unternehmensplan_data import get_current_geschaeftsjahr
from scripts.planung_vorschlag_belastbar import build_planungsvorschlag
from scripts.planung_ergebnis_aus_aktuellen_daten import get_gj_datum


def get_gw_stueck_ytd(gj: str, standort: int = 0) -> int:
    """GW-Stückzahl YTD aus Locosoft dealer_vehicles (Auslieferungen im GJ bis heute)."""
    von, _ = get_gj_datum(gj)
    start_jahr = int(gj.split("/")[0])
    heute = date.today()
    if heute.month >= 9:
        aktueller_monat_gj = heute.month - 8
    else:
        aktueller_monat_gj = heute.month + 4
    if aktueller_monat_gj <= 4:
        end_year, end_month = start_jahr, 8 + aktueller_monat_gj
    else:
        end_year, end_month = start_jahr + 1, aktueller_monat_gj - 4
    last_day = monthrange(end_year, end_month)[1]
    bis_ytd = date(end_year, end_month, last_day).isoformat()

    standort_filter = ""
    if standort == 1:
        standort_filter = "AND (dv.in_subsidiary = 1 OR dv.in_subsidiary = 2)"
    elif standort == 2:
        standort_filter = "AND dv.in_subsidiary = 2"
    elif standort == 3:
        standort_filter = "AND dv.in_subsidiary = 3"

    with locosoft_session() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT COUNT(*) AS stueck
            FROM dealer_vehicles dv
            WHERE dv.dealer_vehicle_type IN ('G', 'D', 'L')
              AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date) IS NOT NULL
              AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date)::date >= %s
              AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date)::date <= %s
              AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date)::date <= CURRENT_DATE
              {standort_filter}
        """, (von, bis_ytd))
        row = cur.fetchone()
    return int(row[0] or 0)


def get_nw_stueck_ytd(gj: str, standort: int = 0) -> int:
    """NW-Stückzahl YTD aus Locosoft dealer_vehicles (N, T, V)."""
    von, _ = get_gj_datum(gj)
    start_jahr = int(gj.split("/")[0])
    heute = date.today()
    if heute.month >= 9:
        aktueller_monat_gj = heute.month - 8
    else:
        aktueller_monat_gj = heute.month + 4
    if aktueller_monat_gj <= 4:
        end_year, end_month = start_jahr, 8 + aktueller_monat_gj
    else:
        end_year, end_month = start_jahr + 1, aktueller_monat_gj - 4
    last_day = monthrange(end_year, end_month)[1]
    bis_ytd = date(end_year, end_month, last_day).isoformat()

    standort_filter = ""
    if standort == 1:
        standort_filter = "AND (dv.in_subsidiary = 1 OR dv.in_subsidiary = 2)"
    elif standort == 2:
        standort_filter = "AND dv.in_subsidiary = 2"
    elif standort == 3:
        standort_filter = "AND dv.in_subsidiary = 3"

    with locosoft_session() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT COUNT(*) AS stueck
            FROM dealer_vehicles dv
            WHERE dv.dealer_vehicle_type IN ('N', 'T', 'V')
              AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date) IS NOT NULL
              AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date)::date >= %s
              AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date)::date <= %s
              AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date)::date <= CURRENT_DATE
              {standort_filter}
        """, (von, bis_ytd))
        row = cur.fetchone()
    return int(row[0] or 0)


def main():
    gj = get_current_geschaeftsjahr()
    standort = 0
    ziel_gw_stueck = 1000
    ziel_nw_mehr = 100

    print("=" * 70)
    print("Planungsszenario: 1000 GW + 100 NW mehr")
    print("=" * 70)
    print(f"Geschäftsjahr: {gj}  |  Standort: Konzern")
    print()

    v = build_planungsvorschlag(gj, standort=standort)
    gw_stueck_ytd = get_gw_stueck_ytd(gj, standort=standort)
    nw_stueck_ytd = get_nw_stueck_ytd(gj, standort=standort)

    gw_basis = next((b for b in v["plan_bereiche"] if b["bereich"] == "GW"), None)
    nw_basis = next((b for b in v["plan_bereiche"] if b["bereich"] == "NW"), None)
    if not gw_basis:
        print("Kein GW-Bereich in Planung gefunden.")
        sys.exit(1)

    gw_umsatz_ytd = gw_basis.get("umsatz_ytd") or 0
    gw_plan_umsatz_alt = gw_basis["umsatz_plan"]
    gw_plan_db1_alt = gw_basis["db1_plan"]
    marge_gw = gw_basis["marge_ziel"]

    if gw_stueck_ytd > 0:
        oe_vk_gw = gw_umsatz_ytd / gw_stueck_ytd
    else:
        oe_vk_gw = 20_000.0
        print(f"Hinweis: GW YTD Stück = 0, verwende Ø-VK {oe_vk_gw:,.0f} €.")

    gw_umsatz_1000 = ziel_gw_stueck * oe_vk_gw
    gw_db1_1000 = gw_umsatz_1000 * (marge_gw / 100)

    # NW: +100 Stück (Ziel-Marge 8 %)
    if nw_basis and nw_stueck_ytd > 0:
        nw_umsatz_ytd = nw_basis.get("umsatz_ytd") or 0
        oe_vk_nw = nw_umsatz_ytd / nw_stueck_ytd
    else:
        oe_vk_nw = 30_000.0
        if not nw_basis or nw_stueck_ytd == 0:
            print(f"Hinweis: NW YTD Stück = {nw_stueck_ytd}, verwende Ø-VK NW {oe_vk_nw:,.0f} €.")
    nw_umsatz_100_mehr = ziel_nw_mehr * oe_vk_nw
    marge_nw = nw_basis["marge_ziel"] if nw_basis else 8.0
    nw_db1_100_mehr = nw_umsatz_100_mehr * (marge_nw / 100)

    plan_umsatz_gesamt_alt = v["plan_umsatz_gesamt"]
    plan_db1_gesamt_alt = v["plan_db1_gesamt"]
    plan_umsatz_neu = plan_umsatz_gesamt_alt - gw_plan_umsatz_alt + gw_umsatz_1000 + nw_umsatz_100_mehr
    plan_db1_neu = plan_db1_gesamt_alt - gw_plan_db1_alt + gw_db1_1000 + nw_db1_100_mehr
    plan_ergebnis_neu = plan_db1_neu - v["kosten_budget"]
    plan_rendite_neu = (plan_ergebnis_neu / plan_umsatz_neu * 100) if plan_umsatz_neu else 0

    print("--- Basisszenario (Hochrechnung YTD, Ziel-Margen) ---")
    print(f"  GW YTD:             {gw_stueck_ytd} Stück, Umsatz YTD {gw_umsatz_ytd:,.0f} €  →  Ø-VK {oe_vk_gw:,.0f} €")
    if nw_basis:
        print(f"  NW YTD:             {nw_stueck_ytd} Stück, Umsatz YTD {nw_basis.get('umsatz_ytd', 0):,.0f} €  →  Ø-VK {oe_vk_nw:,.0f} €")
    print(f"  Plan gesamt:        Umsatz {plan_umsatz_gesamt_alt:,.0f} €  |  DB1 {plan_db1_gesamt_alt:,.0f} €  |  Ergebnis {v['plan_ergebnis']:,.0f} €  |  Rendite {v['plan_rendite']:.2f} %")
    print()
    print("--- Szenario: GW = 1000 Stück (5 %) + 100 NW mehr (8 %) ---")
    print(f"  GW Plan (neu):      1000 × {oe_vk_gw:,.0f} € = {gw_umsatz_1000:,.0f} € Umsatz  |  DB1 {gw_db1_1000:,.0f} €")
    print(f"  NW +100:           +100 × {oe_vk_nw:,.0f} € = +{nw_umsatz_100_mehr:,.0f} € Umsatz  |  DB1 +{nw_db1_100_mehr:,.0f} €")
    print(f"  Plan gesamt (neu): Umsatz {plan_umsatz_neu:,.0f} €  |  DB1 {plan_db1_neu:,.0f} €  |  Ergebnis {plan_ergebnis_neu:,.0f} €  |  Rendite {plan_rendite_neu:.2f} %")
    print()
    print("--- Differenz zum Basisszenario ---")
    print(f"  +Umsatz:   {plan_umsatz_neu - plan_umsatz_gesamt_alt:+,.0f} €")
    print(f"  +DB1:      {plan_db1_neu - plan_db1_gesamt_alt:+,.0f} €")
    print(f"  +Ergebnis: {plan_ergebnis_neu - v['plan_ergebnis']:+,.0f} €")
    print(f"  Rendite:   {v['plan_rendite']:.2f} % → {plan_rendite_neu:.2f} %")
    print("=" * 70)


if __name__ == "__main__":
    main()
