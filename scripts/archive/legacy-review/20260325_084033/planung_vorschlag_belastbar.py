#!/usr/bin/env python3
"""
Belastbarer Planungsvorschlag (Geschäftsjahr)
============================================
Erzeugt einen nachvollziehbaren Planungsvorschlag mit:
- Ziel (Break-even / 1 % Rendite)
- Ausgangslage (Prognose ohne Maßnahmen)
- Annahmen (Kosten, Zinskosten, Ziel-Margen, Standzeiten Bestand)
- Plan-Szenario: DB1 pro Bereich bei Ziel-Margen, Kosten-Budget, Ergebnis Plan
- Ausgabe: Konsolen-Zusammenfassung + Markdown-Datei (PLANUNGSVORSCHLAG.md)
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.unternehmensplan_data import (
    get_gap_analyse,
    get_ist_daten,
    get_current_geschaeftsjahr,
    get_letzter_abgeschlossener_monat,
)
from api.db_connection import get_db
from api.db_utils import get_guv_filter

# VJ aus Portal (wie planung_ergebnis_aus_aktuellen_daten)
from scripts.planung_ergebnis_aus_aktuellen_daten import (
    get_gj_datum,
    lade_vj_aus_portal,
)
from scripts.planung_gewinnzone_standzeit_vorschlag import (
    lade_bestand_und_durchschnittswert_locosoft,
    berechne_plan_zinskosten_annahme,
    lade_standzeiten_aus_locosoft,
    TAGE_UNTER_ZINS_ANNAHME,
    ZINSSATZ_ANNAHME,
)

OUTPUT_MD = "docs/workstreams/planung/PLANUNGSVORSCHLAG.md"


def anzahl_abgelaufene_gj_monate(gj: str) -> int:
    """Anzahl abgelaufener Monate im Geschäftsjahr (1–12)."""
    letzter_m, letzter_j = get_letzter_abgeschlossener_monat()
    start_jahr = int(gj.split("/")[0])
    if letzter_j == start_jahr and letzter_m >= 9:
        return letzter_m - 8
    if letzter_j == start_jahr + 1 and letzter_m <= 8:
        return letzter_m + 4
    return 1


def build_planungsvorschlag(gj: str, standort: int = 0, marge_override: dict | None = None) -> dict:
    """
    Baut den belastbaren Planungsvorschlag für das Geschäftsjahr.
    - Prognose/Umsatz aus Gap-Analyse (Hochrechnung YTD)
    - DB1-Plan pro Bereich: Umsatz-Anteil × Ziel-Marge (aus Gap-Analyse, ggf. marge_override)
    - Kosten-Budget: Mittelwert (VJ-Kosten + YTD-Kosten hochgerechnet)
    - Zinskosten-Plan: 90 Tage, 5 %, Lagerwert netto (Locosoft Bestand)
    - marge_override: z.B. {'NW': 9, 'GW': 6} für Test mit NW 9 %, GW 6 % Ziel-Marge
    """
    start = int(gj.split("/")[0])
    gj_vj = f"{start - 1}/{str(start)[-2:]}"

    gap = get_gap_analyse(gj, standort=standort)
    prognose = gap["prognose_jahresende"]
    ist_ytd = gap["ist_ytd"]
    bereiche = gap["bereiche"]
    ziel_rendite = gap.get("ziel_rendite", 1.0)
    ziel_ergebnis = prognose["umsatz"] * (ziel_rendite / 100)
    gap_zu_ziel = gap["gap_jahresende"]

    # VJ-Kosten (Portal oder Fallback)
    try:
        vj = lade_vj_aus_portal(gj_vj)
        if vj["umsatz"] == 0 and vj["kosten"] == 0:
            ist_vj = get_ist_daten(gj_vj, standort=standort, nur_abgeschlossene=True)
            vj = {k: float(ist_vj["gesamt"].get(k, 0)) for k in ["umsatz", "db1", "kosten", "ergebnis", "rendite"]}
            vj.setdefault("rendite", (vj["ergebnis"] / vj["umsatz"] * 100) if vj["umsatz"] else 0)
    except Exception:
        ist_vj = get_ist_daten(gj_vj, standort=standort, nur_abgeschlossene=True)
        vj = {k: float(ist_vj["gesamt"].get(k, 0)) for k in ["umsatz", "db1", "kosten", "ergebnis", "rendite"]}

    monate_ytd = max(1, anzahl_abgelaufene_gj_monate(gj))
    ytd_kosten_hoch = ist_ytd["kosten"] * 12 / monate_ytd
    kosten_budget = (float(vj["kosten"]) + ytd_kosten_hoch) / 2 if vj.get("kosten") else ytd_kosten_hoch

    # Bestand + Zinskosten-Plan (90 Tage, 5 %)
    bestand = lade_bestand_und_durchschnittswert_locosoft(standort=standort)
    plan_zins = berechne_plan_zinskosten_annahme(bestand)
    standzeiten = lade_standzeiten_aus_locosoft(gj_vj)

    # Plan pro Bereich: Umsatz-Anteil aus YTD, DB1 = Umsatz_Plan × Ziel-Marge
    plan_umsatz_gesamt = prognose["umsatz"]
    plan_bereiche = []
    plan_db1_gesamt = 0.0
    umsatz_ytd_gesamt = ist_ytd["umsatz"] or 1

    for b in bereiche:
        umsatz_ytd_b = b.get("umsatz", 0) or 0
        anteil = umsatz_ytd_b / umsatz_ytd_gesamt
        umsatz_plan_b = plan_umsatz_gesamt * anteil
        marge_ziel = (marge_override or {}).get(b["bereich"], b.get("marge_ziel", 10.0))
        db1_plan_b = umsatz_plan_b * (marge_ziel / 100)
        plan_db1_gesamt += db1_plan_b
        plan_bereiche.append({
            "bereich": b["bereich"],
            "umsatz_ytd": umsatz_ytd_b,
            "umsatz_plan": round(umsatz_plan_b, 0),
            "marge_ziel": marge_ziel,
            "db1_plan": round(db1_plan_b, 0),
            "marge_ist": b.get("marge_ist", 0),
            "potenzial_db1": b.get("potenzial_db1", 0),
        })

    plan_ergebnis = plan_db1_gesamt - kosten_budget
    plan_rendite = (plan_ergebnis / plan_umsatz_gesamt * 100) if plan_umsatz_gesamt else 0

    return {
        "gj": gj,
        "gj_vj": gj_vj,
        "standort": standort,
        "ziel_rendite": ziel_rendite,
        "ziel_ergebnis": round(ziel_ergebnis, 0),
        "prognose": prognose,
        "gap_zu_ziel": gap_zu_ziel,
        "vj": vj,
        "ist_ytd": ist_ytd,
        "monate_ytd": monate_ytd,
        "kosten_budget": round(kosten_budget, 0),
        "ytd_kosten_hoch": round(ytd_kosten_hoch, 0),
        "plan_umsatz_gesamt": round(plan_umsatz_gesamt, 0),
        "plan_bereiche": plan_bereiche,
        "plan_db1_gesamt": round(plan_db1_gesamt, 0),
        "plan_ergebnis": round(plan_ergebnis, 0),
        "plan_rendite": round(plan_rendite, 2),
        "plan_zinskosten": plan_zins["zinskosten_plan_jahr"],
        "bestand": bestand,
        "standzeiten": standzeiten,
        "annahmen": {
            "kosten": "Mittelwert (VJ-Kosten + YTD-Kosten hochgerechnet auf 12 Monate)",
            "zinskosten": f"{TAGE_UNTER_ZINS_ANNAHME} Tage unter Zins, {ZINSSATZ_ANNAHME*100:.0f} % Ø-Zins, Lagerwert netto (Locosoft Bestand)",
            "db1_pro_bereich": "Umsatz-Anteil (aus YTD) × Ziel-Marge (NW 8 %, GW 5 %, Teile 28 %, Werkstatt 55 %, Sonstige 50 %)",
        },
    }


def write_markdown(v: dict, path: str) -> None:
    """Schreibt PLANUNGSVORSCHLAG.md."""
    lines = [
        "# Belastbarer Planungsvorschlag",
        "",
        f"**Geschäftsjahr:** {v['gj']}  |  **Stand:** {date.today().isoformat()}  |  **Standort:** Konzern",
        "",
        "---",
        "",
        "## 1. Ziel",
        "",
        f"- **Ergebnisziel:** {v['ziel_rendite']} % Rendite (Gewinnzone) → **{v['ziel_ergebnis']:,.0f} €** bei Plan-Umsatz",
        "- **Alternativ:** Break-even (0 €)",
        "",
        "## 2. Ausgangslage (Prognose ohne Maßnahmen)",
        "",
        f"- **Prognose Jahresende** (Hochrechnung YTD): Umsatz {v['prognose']['umsatz']:,.0f} €, Ergebnis {v['prognose']['ergebnis']:,.0f} € ({v['prognose']['rendite']:.2f} % Rendite)",
        f"- **Gap zum {v['ziel_rendite']} %-Ziel:** {v['gap_zu_ziel']:,.0f} €",
        "",
        "## 3. Annahmen (belastbar aus Daten)",
        "",
        "| Annahme | Quelle / Formel |",
        "|--------|------------------|",
        "| **Kosten-Budget** | " + v["annahmen"]["kosten"] + " |",
        "| **Zinskosten-Plan** | " + v["annahmen"]["zinskosten"] + " |",
        "| **DB1 pro Bereich** | " + v["annahmen"]["db1_pro_bereich"] + " |",
        "| **Standzeiten Bestand** | Locosoft dealer_vehicles (Stichtag), NW/GW Ø Tage |",
        "",
        "## 4. Planungsvorschlag (Szenario: Ziel-Margen erreicht)",
        "",
        "### 4.1 Umsatz und DB1 nach Bereich",
        "",
        "| Bereich | Plan-Umsatz (Anteil YTD) | Ziel-Marge | Plan-DB1 |",
        "|---------|--------------------------|------------|----------|",
    ]
    for b in v["plan_bereiche"]:
        lines.append(f"| {b['bereich']} | {b['umsatz_plan']:,.0f} € | {b['marge_ziel']:.0f} % | {b['db1_plan']:,.0f} € |")
    lines.extend([
        f"| **Summe** | **{v['plan_umsatz_gesamt']:,.0f} €** | | **{v['plan_db1_gesamt']:,.0f} €** |",
        "",
        "### 4.2 Kosten und Ergebnis",
        "",
        f"- **Kosten-Budget (Mittelwert):** {v['kosten_budget']:,.0f} €",
        f"- **davon Zinskosten (Plan 90 Tage × 5 %):** {v['plan_zinskosten']:,.0f} €",
        f"- **Plan-Ergebnis:** DB1 − Kosten = **{v['plan_ergebnis']:,.0f} €**",
        f"- **Plan-Rendite:** **{v['plan_rendite']:.2f} %**",
        "",
    ])
    if v["plan_ergebnis"] < 0:
        lines.extend([
            "**Kernaussage:** Selbst bei Erreichen der Ziel-Margen in allen Bereichen reicht der Plan-DB1 nicht, um das Kosten-Budget zu decken. Für Break-even oder 1 % Rendite sind zusätzlich **Kostensenkung** und/oder **weitere DB1-Hebel** (z. B. Umsatzsteigerung bei gleicher Marge) nötig.",
            "",
        ])
    lines.extend([
        "### 4.3 Standzeiten Bestand (Locosoft)",
        "",
        f"- **NW:** {v['standzeiten']['stueck_bestand_nw']} Stück, Ø {v['standzeiten']['standzeit_bestand_nw']} Tage",
        f"- **GW:** {v['standzeiten']['stueck_bestand_gw']} Stück, Ø {v['standzeiten']['standzeit_bestand_gw']} Tage",
        "",
        "## 5. Nächste Schritte",
        "",
        "- Plan in Unternehmensplan (Portal) übernehmen bzw. mit Abteilungsleitern abstimmen.",
        "- Priorität: Bereiche mit größtem DB1-Potenzial (v. a. GW bei negativer Marge) angehen.",
        "- Kosten-Budget und Zinskosten-Plan regelmäßig mit IST abgleichen.",
        "",
        "---",
        "",
        "*Erzeugt mit `scripts/planung_vorschlag_belastbar.py`*",
    ])
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    gj = get_current_geschaeftsjahr()
    standort = 0

    print("=" * 70)
    print("Belastbarer Planungsvorschlag")
    print("=" * 70)
    print(f"Geschäftsjahr: {gj}  |  Standort: Konzern")
    print()

    try:
        v = build_planungsvorschlag(gj, standort=standort)
    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("--- Ausgangslage ---")
    print(f"  Prognose Jahresende: Umsatz {v['prognose']['umsatz']:,.0f} €, Ergebnis {v['prognose']['ergebnis']:,.0f} € ({v['prognose']['rendite']:.2f} % Rendite)")
    print(f"  Gap zum 1 %-Ziel:   {v['gap_zu_ziel']:,.0f} €")
    print()
    print("--- Annahmen ---")
    print(f"  Kosten-Budget:      Mittelwert (VJ + YTD hochgerechnet) = {v['kosten_budget']:,.0f} €")
    print(f"  Zinskosten-Plan:    90 Tage × 5 %, Lagerwert netto       = {v['plan_zinskosten']:,.0f} €")
    print(f"  DB1 pro Bereich:    Umsatz-Anteil × Ziel-Marge")
    print()
    print("--- Plan (Szenario: Ziel-Margen erreicht) ---")
    for b in v["plan_bereiche"]:
        print(f"  {b['bereich']:10}  Plan-Umsatz {b['umsatz_plan']:>12,.0f} €  |  Ziel-Marge {b['marge_ziel']:.0f} %  |  Plan-DB1 {b['db1_plan']:>12,.0f} €")
    print(f"  {'Summe':10}  Plan-Umsatz {v['plan_umsatz_gesamt']:>12,.0f} €  |  Plan-DB1   {v['plan_db1_gesamt']:>12,.0f} €")
    print()
    print(f"  Plan-Ergebnis:  {v['plan_db1_gesamt']:,.0f} − {v['kosten_budget']:,.0f} = {v['plan_ergebnis']:,.0f} €")
    print(f"  Plan-Rendite:   {v['plan_rendite']:.2f} %")
    print()
    print("--- Standzeiten Bestand (Locosoft) ---")
    print(f"  NW: {v['standzeiten']['stueck_bestand_nw']} Stück, Ø {v['standzeiten']['standzeit_bestand_nw']} Tage  |  GW: {v['standzeiten']['stueck_bestand_gw']} Stück, Ø {v['standzeiten']['standzeit_bestand_gw']} Tage")
    print()

    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    md_path = os.path.join(base, OUTPUT_MD)
    try:
        write_markdown(v, md_path)
        print(f"→ Markdown geschrieben: {OUTPUT_MD}")
    except Exception as e:
        print(f"Hinweis: Markdown konnte nicht geschrieben werden: {e}")

    # Testweise: NW 9 % (Trend), GW 6 % (Ziel aus GW-Planung)
    v_test = build_planungsvorschlag(gj, standort=standort, marge_override={"NW": 9, "GW": 6})
    print()
    print("=" * 70)
    print("TEST: Planung mit NW-Ziel 9 % (Trend), GW-Ziel 6 %")
    print("=" * 70)
    print("  NW: Ziel-Marge 8 % → 9 %  |  GW: Ziel-Marge 5 % → 6 %")
    print()
    print("--- Plan (Szenario) ---")
    for b in v_test["plan_bereiche"]:
        print(f"  {b['bereich']:10}  Plan-Umsatz {b['umsatz_plan']:>12,.0f} €  |  Ziel-Marge {b['marge_ziel']:.0f} %  |  Plan-DB1 {b['db1_plan']:>12,.0f} €")
    print(f"  {'Summe':10}  Plan-Umsatz {v_test['plan_umsatz_gesamt']:>12,.0f} €  |  Plan-DB1   {v_test['plan_db1_gesamt']:>12,.0f} €")
    print()
    print(f"  Plan-Ergebnis:  {v_test['plan_db1_gesamt']:,.0f} − {v_test['kosten_budget']:,.0f} = {v_test['plan_ergebnis']:,.0f} €")
    print(f"  Plan-Rendite:   {v_test['plan_rendite']:.2f} %")
    print()
    diff_db1 = v_test["plan_db1_gesamt"] - v["plan_db1_gesamt"]
    diff_erg = v_test["plan_ergebnis"] - v["plan_ergebnis"]
    print(f"  Differenz zum Basisszenario (8 %/5 %):  +{diff_db1:,.0f} € DB1  →  +{diff_erg:,.0f} € Ergebnis")
    print("=" * 70)


if __name__ == "__main__":
    main()
