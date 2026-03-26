#!/usr/bin/env python3
"""
Planung GJ 2025/26 – pragmatischer Ansatz (kalibriert mit Vorjahr)
==================================================================
Vorjahr-Referenz (IST):
- NW: 452 Stück, DB1 1.578.056 € (Ø 3.491 €) – evtl. nicht saubere Trennung NW
- GW: 771 Stück, DB1 613.012 € (Ø 795 €)

Plan 2025/26:
- NW: 130 Leapmotor + 300 Opel + 200 Hyundai = 630 Stück; Ø DB konservativ 1.800 € (VJ-Ø war höher)
- GW: 900 Stück, Ziel Gesamt-DB 800.000 €; VJ-Niveau bei 900 Stück = 715.500 € (Ø 795 €)
- Teile, Werkstatt, Sonstige + Kosten: aus aktuellem Plan übernommen
"""

import sys
import os
from datetime import date
from calendar import monthrange

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.unternehmensplan_data import get_current_geschaeftsjahr, get_gap_analyse
from scripts.planung_vorschlag_belastbar import build_planungsvorschlag
from scripts.planung_szenario_gw_1000 import get_gw_stueck_ytd, get_nw_stueck_ytd
from scripts.planung_ergebnis_aus_aktuellen_daten import get_gj_datum

# Vorjahr-Referenz (IST, zur Kalibrierung)
VJ_NW_STUECK = 452
VJ_NW_DB1 = 1_578_056   # € (evtl. nicht saubere Trennung NW)
VJ_GW_STUECK = 771
VJ_GW_DB1 = 613_012     # €

# Annahmen GJ 2025/26
NW_LEAPMOTOR = 130
NW_OPEL = 300
NW_HYUNDAI = 200
NW_DB_PRO_STUECK = 1_800   # € (nur wenn nicht NW_GW_Ø verwendet)

GW_PLAN_STUECK = 900
GW_ZIEL_DB_GESAMT = 800_000  # € (nur wenn nicht NW_GW_Ø verwendet)

# Gemeinsamer Ø DB für NW+GW (wenn gesetzt, überschreibt getrennte NW/GW-Planung)
NW_GW_DB_PRO_STUECK = 1_880  # € Ø pro Stück (NW + GW zusammen)


def main():
    gj = get_current_geschaeftsjahr()
    standort = 0

    v = build_planungsvorschlag(gj, standort=standort)
    gap = get_gap_analyse(gj, standort=standort)
    gw_stueck_ytd = get_gw_stueck_ytd(gj, standort=standort)

    # GW YTD DB1 aus BWA (gap bereiche)
    gw_basis = next((b for b in gap["bereiche"] if b["bereich"] == "GW"), None)
    gw_db1_ytd = float(gw_basis["db1"]) if gw_basis else 0.0

    # NW Plan
    nw_plan_stueck = NW_LEAPMOTOR + NW_OPEL + NW_HYUNDAI
    nw_stueck_ytd = get_nw_stueck_ytd(gj, standort=standort)
    nw_basis = next((b for b in gap["bereiche"] if b["bereich"] == "NW"), None)
    nw_db1_ytd = float(nw_basis["db1"]) if nw_basis else 0.0
    gw_verbleibend = max(0, GW_PLAN_STUECK - gw_stueck_ytd)

    # Gemeinsamer Ø NW+GW = 1.880 €/Stück
    use_combined = NW_GW_DB_PRO_STUECK is not None and NW_GW_DB_PRO_STUECK > 0
    if use_combined:
        fahrzeug_plan_stueck = nw_plan_stueck + GW_PLAN_STUECK
        plan_db1_nw_gw = fahrzeug_plan_stueck * NW_GW_DB_PRO_STUECK
        fz_verbleibend = max(0, nw_plan_stueck - nw_stueck_ytd) + gw_verbleibend
        db1_ytd_fz = nw_db1_ytd + gw_db1_ytd
        db1_noch_noetig = plan_db1_nw_gw - db1_ytd_fz
        db_pro_stueck_ab_jetzt = (db1_noch_noetig / fz_verbleibend) if fz_verbleibend > 0 else NW_GW_DB_PRO_STUECK
    else:
        plan_db1_nw_gw = nw_plan_stueck * NW_DB_PRO_STUECK + GW_ZIEL_DB_GESAMT
        gw_db1_noch_noetig = GW_ZIEL_DB_GESAMT - gw_db1_ytd
        db_pro_stueck_ab_jetzt = (gw_db1_noch_noetig / gw_verbleibend) if gw_verbleibend > 0 else 0
        db1_noch_noetig = gw_db1_noch_noetig
        fz_verbleibend = gw_verbleibend

    # Teile, Werkstatt, Sonstige: aus aktuellem Plan
    plan_bereiche_alt = v["plan_bereiche"]
    db1_teile = next((b["db1_plan"] for b in plan_bereiche_alt if b["bereich"] == "Teile"), 0)
    db1_werkstatt = next((b["db1_plan"] for b in plan_bereiche_alt if b["bereich"] == "Werkstatt"), 0)
    db1_sonstige = next((b["db1_plan"] for b in plan_bereiche_alt if b["bereich"] == "Sonstige"), 0)

    plan_db1_rest = db1_teile + db1_werkstatt + db1_sonstige
    plan_db1_gesamt = plan_db1_nw_gw + plan_db1_rest
    kosten_budget = v["kosten_budget"]
    plan_ergebnis = plan_db1_gesamt - kosten_budget
    plan_umsatz_roh = v["plan_umsatz_gesamt"]  # für Rendite grob
    plan_rendite = (plan_ergebnis / plan_umsatz_roh * 100) if plan_umsatz_roh else 0

    # Bei 0,5 % Rendite-Ziel: welcher Ø DB (NW+GW) wäre nötig? Inkl. Aufholbedarf (neg. GW YTD).
    # Rendite = Ergebnis / Umsatz  =>  DB1_gesamt = Kosten + 0,005 * Umsatz
    ziel_rendite_pct = 0.5
    plan_db1_gesamt_05pct = kosten_budget + (ziel_rendite_pct / 100) * plan_umsatz_roh
    plan_db1_nw_gw_05pct = plan_db1_gesamt_05pct - plan_db1_rest
    fz_plan_stueck = nw_plan_stueck + GW_PLAN_STUECK
    db_pro_stueck_05pct = (plan_db1_nw_gw_05pct / fz_plan_stueck) if fz_plan_stueck else 0
    plan_ergebnis_05pct = plan_db1_gesamt_05pct - kosten_budget
    # Aufholbedarf: YTD haben wir schon (nw_db1_ytd + gw_db1_ytd), davon GW negativ → ab jetzt nötig
    db1_ytd_nw_gw = nw_db1_ytd + gw_db1_ytd
    db1_noch_noetig_05pct = plan_db1_nw_gw_05pct - db1_ytd_nw_gw
    db_pro_stueck_ab_jetzt_05pct = (db1_noch_noetig_05pct / fz_verbleibend) if fz_verbleibend > 0 else db_pro_stueck_05pct

    # Vorjahr-Ø für Referenz
    vj_nw_db_pro_stueck = VJ_NW_DB1 / VJ_NW_STUECK if VJ_NW_STUECK else 0
    vj_gw_db_pro_stueck = VJ_GW_DB1 / VJ_GW_STUECK if VJ_GW_STUECK else 0
    gw_plan_vj_niveau = int(GW_PLAN_STUECK * vj_gw_db_pro_stueck)  # 900 × VJ-Ø

    print("=" * 72)
    print("Planung GJ 2025/26 – pragmatischer Ansatz (kalibriert mit Vorjahr)")
    print("=" * 72)
    print(f"Geschäftsjahr: {gj}  |  Standort: Konzern  |  Stichtag: {date.today().isoformat()}")
    print()
    print("--- Vorjahr-Referenz (IST) ---")
    print(f"  NW: {VJ_NW_STUECK} Stück, DB1 {VJ_NW_DB1:,.0f} €  →  Ø {vj_nw_db_pro_stueck:,.0f} €/Stück  (evtl. nicht saubere Trennung NW)")
    print(f"  GW: {VJ_GW_STUECK} Stück, DB1 {VJ_GW_DB1:,.0f} €  →  Ø {vj_gw_db_pro_stueck:,.0f} €/Stück")
    print()
    if use_combined:
        print("--- Annahme NW+GW: gemeinsamer Ø 1.880 €/Stück ---")
        print(f"  NW: {nw_plan_stueck} Stück (130 Leap + 300 Opel + 200 Hyundai)  |  GW: {GW_PLAN_STUECK} Stück  →  gesamt {nw_plan_stueck + GW_PLAN_STUECK} Stück")
        print(f"  Plan-DB1 NW+GW = {nw_plan_stueck + GW_PLAN_STUECK} × {NW_GW_DB_PRO_STUECK:,.0f} € = {plan_db1_nw_gw:,.0f} €")
        print(f"  YTD: NW {nw_stueck_ytd} Stück ({nw_db1_ytd:,.0f} € DB1), GW {gw_stueck_ytd} Stück ({gw_db1_ytd:,.0f} € DB1)  →  zusammen {nw_db1_ytd + gw_db1_ytd:,.0f} €")
        print(f"  Verbleibend: {fz_verbleibend} Stück  |  Noch nötig: {db1_noch_noetig:,.0f} € DB1")
        print(f"  → Ab jetzt nötig: {db_pro_stueck_ab_jetzt:,.0f} € DB pro Stück (Ø) für alle verbleibenden NW+GW")
    else:
        print("--- Annahmen NW (Plan) ---")
        print(f"  Leapmotor {NW_LEAPMOTOR} + Opel {NW_OPEL} + Hyundai {NW_HYUNDAI} = {nw_plan_stueck} Stück, Ø DB {NW_DB_PRO_STUECK:,.0f} €")
        print("--- Annahmen GW (Plan) ---")
        print(f"  Plan: {GW_PLAN_STUECK} Stück, Ziel Gesamt-DB1 GW = {GW_ZIEL_DB_GESAMT:,.0f} €")
        print(f"  YTD: {gw_stueck_ytd} Stück, DB1 YTD = {gw_db1_ytd:,.0f} €  |  Ab jetzt nötig: {db_pro_stueck_ab_jetzt:,.0f} € DB/Stück")
    print()
    print("--- Plan DB1 (pragmatisch) ---")
    if use_combined:
        print(f"  NW+GW:    {plan_db1_nw_gw:>12,.0f} €  (Ø {NW_GW_DB_PRO_STUECK:,.0f} €/Stück)")
    else:
        print(f"  NW:       {nw_plan_stueck * NW_DB_PRO_STUECK:>12,.0f} €")
        print(f"  GW:       {GW_ZIEL_DB_GESAMT:>12,.0f} €")
    print(f"  Teile:     {db1_teile:>12,.0f} €")
    print(f"  Werkstatt: {db1_werkstatt:>12,.0f} €")
    print(f"  Sonstige:  {db1_sonstige:>12,.0f} €")
    print(f"  Summe DB1: {plan_db1_gesamt:>12,.0f} €")
    print()
    print("--- Ergebnis ---")
    print(f"  Kosten (Budget): {kosten_budget:>12,.0f} €")
    print(f"  Plan-Ergebnis:   {plan_db1_gesamt:,.0f} − {kosten_budget:,.0f} = {plan_ergebnis:,.0f} €")
    print(f"  Plan-Rendite:    {plan_rendite:.2f} %")
    print()
    print("--- Bei 0,5 % Rendite-Ziel (inkl. Aufholbedarf GW) ---")
    print(f"  Nötiger Plan-DB1 gesamt:  {plan_db1_gesamt_05pct:,.0f} €  (Kosten + 0,5 % × Umsatz)")
    print(f"  Nötiger Plan-DB1 NW+GW:   {plan_db1_nw_gw_05pct:,.0f} €  →  Ø {db_pro_stueck_05pct:,.0f} €/Stück übers Jahr ({fz_plan_stueck} Stück)")
    print(f"  YTD NW+GW bereits:       {db1_ytd_nw_gw:,.0f} €  (davon GW negativ → Aufholbedarf)")
    print(f"  Noch nötig (Rest-Jahr):   {db1_noch_noetig_05pct:,.0f} €  bei {fz_verbleibend} verbleibenden Stück")
    print(f"  → Ab jetzt nötig:         {db_pro_stueck_ab_jetzt_05pct:,.0f} € DB/Stück (Ø) um 0,5 % zu erreichen")
    print(f"  Plan-Ergebnis:            {plan_ergebnis_05pct:,.0f} €  |  Rendite: {ziel_rendite_pct} %")
    print("=" * 72)


if __name__ == "__main__":
    main()
