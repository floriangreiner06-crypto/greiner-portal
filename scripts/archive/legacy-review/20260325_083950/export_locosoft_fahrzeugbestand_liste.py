#!/usr/bin/env python3
"""
Locosoft Fahrzeugbestandsliste – Einsatz, momentaner Verkauf, DB1
==================================================================
Exportiert den aktuellen Fahrzeugbestand aus Locosoft (dealer_vehicles)
mit Einsatz (EK netto), momentanem Verkaufspreis (VK brutto/netto) und kalkuliertem DB1.

Verwendung:
  python scripts/export_locosoft_fahrzeugbestand_liste.py [--standort 0|1|2|3] [--csv datei.csv]
  --standort 0 = alle, 1 = DEG, 2 = Hyundai, 3 = Landau
  Ohne --csv: Ausgabe nur auf Konsole (Tabelle + Summen).

Datenquelle: Locosoft PostgreSQL (dealer_vehicles, vehicles, models).
EK/VK/DB1: api.kalkulation_helpers (SSOT).
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import date

# Projekt-Root für Imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.db_utils import locosoft_session
from api.standort_utils import STANDORT_NAMEN, build_locosoft_filter_bestand
from api.kalkulation_helpers import (
    sql_ek_netto,
    sql_variable_kosten,
    sql_besteuerung_art,
    sql_vk_netto,
    sql_vku_subquery,
    sql_db1,
    sql_standzeit_tage,
)

FAHRZEUGTYP_LABEL = {
    "N": "NW",
    "G": "GW",
    "D": "VFW",
    "V": "Vermiet",
    "T": "Tausch",
}


def get_bestandsliste(standort: int = 0):
    """
    Liest Fahrzeugbestand aus Locosoft: Einsatz, Verkauf (momentan), DB1.
    Nur Fahrzeuge mit out_invoice_date IS NULL (noch nicht verkauft).
    """
    standort_filter = build_locosoft_filter_bestand(standort, nur_stellantis=False)
    # Für SQL: "AND in_subsidiary = 1" -> "AND dv.in_subsidiary = 1"
    where_standort = ""
    if standort_filter:
        where_standort = " " + standort_filter.replace("in_subsidiary", "dv.in_subsidiary")

    query = f"""
        SELECT
            dv.dealer_vehicle_type AS typ,
            dv.dealer_vehicle_number AS nr,
            dv.in_subsidiary AS standort_id,
            v.license_plate AS kennzeichen,
            v.vin AS fin,
            COALESCE(v.free_form_model_text, m.description) AS modell,
            v.first_registration_date AS ez,
            dv.in_arrival_date AS eingang,
            {sql_standzeit_tage("dv")} AS standzeit_tage,
            dv.mileage_km AS km,
            {sql_ek_netto("dv")} AS einsatz,
            COALESCE(dv.out_sale_price, 0) AS vk_brutto,
            ({sql_vk_netto("dv")}) AS vk_netto,
            {sql_variable_kosten("dv")} AS variable_kosten,
            ({sql_db1("dv", vku_nur_bei_verkauf=True)}) AS db1
        FROM dealer_vehicles dv
        LEFT JOIN vehicles v
            ON v.dealer_vehicle_number = dv.dealer_vehicle_number
            AND v.dealer_vehicle_type = dv.dealer_vehicle_type
        LEFT JOIN models m
            ON m.model_code = dv.out_model_code AND m.make_number = dv.out_make_number
        WHERE dv.out_invoice_date IS NULL
        {where_standort}
        ORDER BY dv.dealer_vehicle_type, dv.in_subsidiary, standzeit_tage DESC NULLS LAST
    """

    with locosoft_session() as conn:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description] if cur.description else []

    result = []
    for row in rows:
        r = dict(zip(cols, row))
        r["typ_label"] = FAHRZEUGTYP_LABEL.get(r.get("typ") or "", r.get("typ") or "")
        r["standort_name"] = STANDORT_NAMEN.get(r.get("standort_id"), "Unbekannt")
        result.append(r)
    return result


def main():
    parser = argparse.ArgumentParser(description="Locosoft Fahrzeugbestandsliste (Einsatz, Verkauf, DB1)")
    parser.add_argument("--standort", type=int, default=0, help="0=alle, 1=DEG, 2=Hyundai, 3=Landau")
    parser.add_argument("--csv", type=str, default="", help="CSV-Datei zum Schreiben (optional)")
    args = parser.parse_args()

    rows = get_bestandsliste(standort=args.standort)

    def num(x):
        return float(x) if x is not None else 0.0

    # Summen
    sum_einsatz = sum(num(r.get("einsatz")) for r in rows)
    sum_vk_brutto = sum(num(r.get("vk_brutto")) for r in rows)
    sum_vk_netto = sum(num(r.get("vk_netto")) for r in rows)
    sum_db1 = sum(num(r.get("db1")) for r in rows)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow([
                "Typ", "Nr", "Standort", "Kennzeichen", "FIN", "Modell", "EZ", "Eingang", "Standzeit_Tage", "km",
                "Einsatz_netto", "VK_brutto", "VK_netto", "DB1"
            ])
            for r in rows:
                w.writerow([
                    r.get("typ_label"),
                    r.get("nr"),
                    r.get("standort_name"),
                    r.get("kennzeichen") or "",
                    r.get("fin") or "",
                    r.get("modell") or "",
                    r.get("ez"),
                    r.get("eingang"),
                    r.get("standzeit_tage"),
                    r.get("km") or "",
                    round(num(r.get("einsatz")), 2),
                    round(num(r.get("vk_brutto")), 2),
                    round(num(r.get("vk_netto")), 2),
                    round(num(r.get("db1")), 2),
                ])
        print(f"CSV geschrieben: {args.csv} ({len(rows)} Zeilen)")

    # Konsole: Kurztabelle
    print(f"\nLocosoft Fahrzeugbestand (Stichtag {date.today()}, Standort={args.standort}) – {len(rows)} Fahrzeuge\n")
    print(f"{'Typ':<6} {'Standort':<10} {'Kennzeichen':<12} {'Modell':<28} {'Einsatz':>12} {'VK_brutto':>12} {'VK_netto':>12} {'DB1':>12}")
    print("-" * 110)
    for r in rows[:50]:  # erste 50
        modell = (r.get("modell") or "")[:27]
        print(
            f"{r.get('typ_label', ''):<6} {r.get('standort_name', ''):<10} {(r.get('kennzeichen') or ''):<12} {modell:<28} "
            f"{num(r.get('einsatz')):>11,.0f} {num(r.get('vk_brutto')):>11,.0f} {num(r.get('vk_netto')):>11,.0f} {num(r.get('db1')):>11,.0f}"
        )
    if len(rows) > 50:
        print(f"... und {len(rows) - 50} weitere (siehe CSV)")
    print("-" * 110)
    print(f"{'SUMME':<6} {'':<10} {'':<12} {'':<28} {sum_einsatz:>11,.0f} {sum_vk_brutto:>11,.0f} {sum_vk_netto:>11,.0f} {sum_db1:>11,.0f}")
    print()


if __name__ == "__main__":
    main()
