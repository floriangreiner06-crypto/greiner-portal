#!/usr/bin/env python3
"""
Planungsszenario: Schließung Filiale Landau
===========================================
Rechnet die Auswirkung einer Schließung der Filiale Landau (Standort 3):
- Konzern heute: YTD und Prognose Jahresende (Umsatz, DB1, Kosten, Ergebnis)
- Anteil Landau: YTD und Prognose (aus get_ist_daten standort=3)
- Konzern ohne Landau: Differenz (was bliebe bei Schließung)
- Effekt: Verbesserung/Verschlechterung des Ergebnisses

Datenquelle: Portal loco_journal_accountings (BWA-Logik, Standort-Filter).
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.unternehmensplan_data import get_ist_daten, get_current_geschaeftsjahr, get_gap_analyse

STANDORT_LANDAU = 3


def ytd_und_prognose(ist: dict, aktueller_monat_gj: int):
    """YTD-Summe und Prognose Jahresende (wie get_gap_analyse)."""
    monate = ist.get("monate") or []
    ytd = {
        "umsatz": sum(m["umsatz"] for m in monate[:aktueller_monat_gj]),
        "db1": sum(m["db1"] for m in monate[:aktueller_monat_gj]),
        "kosten": sum(m["kosten"] for m in monate[:aktueller_monat_gj]),
    }
    ytd["ergebnis"] = ytd["db1"] - ytd["kosten"]
    ytd["rendite"] = (ytd["ergebnis"] / ytd["umsatz"] * 100) if ytd["umsatz"] else 0

    monate_verbleibend = 12 - aktueller_monat_gj
    if aktueller_monat_gj > 0:
        d = {
            "umsatz": ytd["umsatz"] / aktueller_monat_gj,
            "db1": ytd["db1"] / aktueller_monat_gj,
            "kosten": ytd["kosten"] / aktueller_monat_gj,
        }
        prognose = {
            "umsatz": ytd["umsatz"] + d["umsatz"] * monate_verbleibend,
            "db1": ytd["db1"] + d["db1"] * monate_verbleibend,
            "kosten": ytd["kosten"] + d["kosten"] * monate_verbleibend,
        }
    else:
        prognose = {"umsatz": 0, "db1": 0, "kosten": 0}
    prognose["ergebnis"] = prognose["db1"] - prognose["kosten"]
    prognose["rendite"] = (prognose["ergebnis"] / prognose["umsatz"] * 100) if prognose["umsatz"] else 0
    return ytd, prognose


def main():
    gj = get_current_geschaeftsjahr()

    # Konzern (Standort 0)
    gap = get_gap_analyse(gj, standort=0)
    aktueller_monat_gj = gap["aktueller_monat"]
    konzern_ytd = gap["ist_ytd"]
    konzern_prognose = gap["prognose_jahresende"]
    # Gap liefert für prognose nur umsatz, ergebnis, rendite – DB1/Kosten für Konzern aus ist_ytd hochrechnen
    konzern_prognose_db1 = konzern_ytd["db1"] * 12 / max(1, aktueller_monat_gj)
    konzern_prognose_kosten = konzern_ytd["kosten"] * 12 / max(1, aktueller_monat_gj)
    konzern_prognose_ergebnis = konzern_prognose_db1 - konzern_prognose_kosten

    # Landau (Standort 3)
    landau_ist = get_ist_daten(gj, standort=STANDORT_LANDAU, nur_abgeschlossene=False)
    landau_ytd, landau_prognose = ytd_und_prognose(landau_ist, aktueller_monat_gj)

    # Konzern ohne Landau
    ohne_ytd = {
        "umsatz": konzern_ytd["umsatz"] - landau_ytd["umsatz"],
        "db1": konzern_ytd["db1"] - landau_ytd["db1"],
        "kosten": konzern_ytd["kosten"] - landau_ytd["kosten"],
    }
    ohne_ytd["ergebnis"] = ohne_ytd["db1"] - ohne_ytd["kosten"]
    ohne_ytd["rendite"] = (ohne_ytd["ergebnis"] / ohne_ytd["umsatz"] * 100) if ohne_ytd["umsatz"] else 0

    ohne_prognose_umsatz = konzern_prognose["umsatz"] - landau_prognose["umsatz"]
    ohne_prognose_db1 = konzern_prognose_db1 - landau_prognose["db1"]
    ohne_prognose_kosten = konzern_prognose_kosten - landau_prognose["kosten"]
    ohne_prognose_ergebnis = ohne_prognose_db1 - ohne_prognose_kosten
    ohne_prognose_rendite = (ohne_prognose_ergebnis / ohne_prognose_umsatz * 100) if ohne_prognose_umsatz else 0

    # Effekt Schließung = Ergebnis ohne Landau − Ergebnis Konzern (positiv = Verbesserung)
    effekt_ytd = ohne_ytd["ergebnis"] - konzern_ytd["ergebnis"]
    effekt_prognose = ohne_prognose_ergebnis - konzern_prognose_ergebnis

    print("=" * 70)
    print("Planungsszenario: Schließung Filiale Landau")
    print("=" * 70)
    print(f"Geschäftsjahr: {gj}  |  Stichtag: {date.today().isoformat()}")
    print()
    print("--- Konzern (alle Standorte) ---")
    print(f"  YTD ({aktueller_monat_gj} Monate):  Umsatz {konzern_ytd['umsatz']:>14,.0f} €  |  DB1 {konzern_ytd['db1']:>12,.0f} €  |  Kosten {konzern_ytd['kosten']:>12,.0f} €  |  Ergebnis {konzern_ytd['ergebnis']:>12,.0f} €  |  Rendite {konzern_ytd['rendite']:>6.2f} %")
    print(f"  Prognose Jahresende:         Umsatz {konzern_prognose['umsatz']:>14,.0f} €  |  DB1 {konzern_prognose_db1:>12,.0f} €  |  Kosten {konzern_prognose_kosten:>12,.0f} €  |  Ergebnis {konzern_prognose_ergebnis:>12,.0f} €  |  Rendite {(konzern_prognose_ergebnis/konzern_prognose['umsatz']*100) if konzern_prognose['umsatz'] else 0:>6.2f} %")
    print()
    print("--- Filiale Landau (Standort 3) – Anteil heute ---")
    print(f"  YTD:   Umsatz {landau_ytd['umsatz']:>14,.0f} €  |  DB1 {landau_ytd['db1']:>12,.0f} €  |  Kosten {landau_ytd['kosten']:>12,.0f} €  |  Ergebnis {landau_ytd['ergebnis']:>12,.0f} €  |  Rendite {landau_ytd['rendite']:>6.2f} %")
    print(f"  Prognose: Umsatz {landau_prognose['umsatz']:>14,.0f} €  |  DB1 {landau_prognose['db1']:>12,.0f} €  |  Kosten {landau_prognose['kosten']:>12,.0f} €  |  Ergebnis {landau_prognose['ergebnis']:>12,.0f} €")
    print()
    print("--- Konzern OHNE Landau (bei Schließung) ---")
    print(f"  YTD:   Umsatz {ohne_ytd['umsatz']:>14,.0f} €  |  DB1 {ohne_ytd['db1']:>12,.0f} €  |  Kosten {ohne_ytd['kosten']:>12,.0f} €  |  Ergebnis {ohne_ytd['ergebnis']:>12,.0f} €  |  Rendite {ohne_ytd['rendite']:>6.2f} %")
    print(f"  Prognose: Umsatz {ohne_prognose_umsatz:>14,.0f} €  |  DB1 {ohne_prognose_db1:>12,.0f} €  |  Kosten {ohne_prognose_kosten:>12,.0f} €  |  Ergebnis {ohne_prognose_ergebnis:>12,.0f} €  |  Rendite {ohne_prognose_rendite:>6.2f} %")
    print()
    print("--- Effekt Schließung Landau ---")
    print(f"  YTD:     Ergebnis {effekt_ytd:+,.0f} €  ({'Verbesserung' if effekt_ytd > 0 else 'Verschlechterung'})")
    print(f"  Prognose: Ergebnis {effekt_prognose:+,.0f} €  ({'Verbesserung' if effekt_prognose > 0 else 'Verschlechterung'})")
    if effekt_prognose > 0:
        print("  → Eine Schließung der Filiale Landau würde die Prognose um {0:,.0f} € verbessern (Landau trägt derzeit negativ bei).".format(effekt_prognose))
    else:
        print("  → Eine Schließung würde die Prognose um {0:,.0f} € verschlechtern (Landau trägt positiv bei).".format(-effekt_prognose))
    print("=" * 70)


if __name__ == "__main__":
    main()
