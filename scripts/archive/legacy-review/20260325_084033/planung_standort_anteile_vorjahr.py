#!/usr/bin/env python3
"""
Planung: Standort-Aufteilung nach Vorjahres-Anteilen
====================================================
Ermittelt aus Locosoft die Vorjahres-Stückzahlen NW/GW pro Standort,
berechnet Anteile und schlägt eine Verteilung der Planzahlen vor.

Verwendung:
  cd /opt/greiner-portal && python scripts/planung_standort_anteile_vorjahr.py [Geschäftsjahr]
  z.B.: python scripts/planung_standort_anteile_vorjahr.py 2025/26

Planzahlen (konfigurierbar im Script oder per Argument):
  - 580 NW gesamt (280 Opel + 200 Hyundai + 100 Leapmotor)
  - 850 GW gesamt

Standorte: 1 = Deggendorf Opel, 2 = Deggendorf Hyundai, 3 = Landau Opel
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.db_utils import locosoft_session
from api.standort_utils import STANDORT_NAMEN


def get_gj_datum(gj: str):
    """GJ '2024/25' -> (2024-09-01, 2025-09-01)."""
    start = int(gj.split('/')[0])
    return f"{start}-09-01", f"{start + 1}-09-01"


def hole_stueck_pro_standort(von: str, bis: str, typ: str) -> dict:
    """
    Liefert Stückzahlen pro out_subsidiary (1,2,3) aus Locosoft dealer_vehicles.
    typ: 'NW' -> N,T,V  /  'GW' -> G,D,L
    """
    if typ == 'NW':
        type_filter = "dealer_vehicle_type IN ('N', 'T', 'V')"
    else:
        type_filter = "dealer_vehicle_type IN ('G', 'D', 'L')"

    with locosoft_session() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT out_subsidiary AS standort, COUNT(*) AS stueck
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND {type_filter}
              AND out_subsidiary IN (1, 2, 3)
            GROUP BY out_subsidiary
            ORDER BY out_subsidiary
        """, (von, bis))
        rows = cur.fetchall()

    return {int(r[0]): int(r[1]) for r in rows}


def anteile_verteilen(ziel_gesamt: int, stueck_pro_standort: dict) -> dict:
    """Verteilt ziel_gesamt nach Anteilen aus stueck_pro_standort. Summe = ziel_gesamt."""
    total = sum(stueck_pro_standort.get(s, 0) for s in (1, 2, 3))
    if total == 0:
        # Fallback: gleichmäßig
        pro_st = ziel_gesamt // 3
        return {1: pro_st, 2: pro_st, 3: ziel_gesamt - 2 * pro_st}

    anteile = {}
    rest = ziel_gesamt
    for standort in (1, 2, 3):
        st = stueck_pro_standort.get(standort, 0)
        if standort == 3:
            anteile[3] = rest
        else:
            wert = round(ziel_gesamt * st / total)
            anteile[standort] = wert
            rest -= wert
    return anteile


def main():
    gj = (sys.argv[1] if len(sys.argv) > 1 else "2024/25").strip()
    von, bis = get_gj_datum(gj)

    # Planzahlen (können hier angepasst werden)
    nw_gesamt = 580   # 280 Opel + 200 Hyundai + 100 Leapmotor
    gw_gesamt = 850

    print("=" * 60)
    print("Planung: Standort-Aufteilung nach Vorjahres-Anteilen")
    print("=" * 60)
    print(f"Vorjahr (Referenz): Geschäftsjahr {gj}")
    print(f"Zeitraum: {von} bis {bis}")
    print(f"Planzahlen: NW gesamt = {nw_gesamt}, GW gesamt = {gw_gesamt}")
    print()

    try:
        nw_vj = hole_stueck_pro_standort(von, bis, 'NW')
        gw_vj = hole_stueck_pro_standort(von, bis, 'GW')
    except Exception as e:
        print(f"Fehler beim Abfragen von Locosoft: {e}")
        sys.exit(1)

    nw_sum = sum(nw_vj.get(s, 0) for s in (1, 2, 3))
    gw_sum = sum(gw_vj.get(s, 0) for s in (1, 2, 3))

    print("--- Vorjahr IST (Locosoft dealer_vehicles) ---")
    print("NW (N,T,V):")
    for s in (1, 2, 3):
        st = nw_vj.get(s, 0)
        pct = (100 * st / nw_sum) if nw_sum else 0
        print(f"  {STANDORT_NAMEN.get(s, s)}: {st} Stück ({pct:.1f} %)")
    print(f"  Summe NW: {nw_sum}")
    print("GW (G,D,L):")
    for s in (1, 2, 3):
        st = gw_vj.get(s, 0)
        pct = (100 * st / gw_sum) if gw_sum else 0
        print(f"  {STANDORT_NAMEN.get(s, s)}: {st} Stück ({pct:.1f} %)")
    print(f"  Summe GW: {gw_sum}")
    print()

    nw_plan = anteile_verteilen(nw_gesamt, nw_vj)
    gw_plan = anteile_verteilen(gw_gesamt, gw_vj)

    print("--- Vorschlag Plan (Verteilung nach VJ-Anteilen) ---")
    print(f"NW Plan gesamt {nw_gesamt} Stück:")
    for s in (1, 2, 3):
        print(f"  {STANDORT_NAMEN.get(s, s)}: {nw_plan[s]} Stück")
    print(f"GW Plan gesamt {gw_gesamt} Stück:")
    for s in (1, 2, 3):
        print(f"  {STANDORT_NAMEN.get(s, s)}: {gw_plan[s]} Stück")

    # Marken-Vorschlag: 280 Opel (1+3), 200 Hyundai (2), 100 Leapmotor (z.B. 1)
    nw1, nw3 = nw_vj.get(1, 0), nw_vj.get(3, 0)
    opel_sum_vj = nw1 + nw3
    if opel_sum_vj > 0:
        opel_1 = round(280 * nw1 / opel_sum_vj)
        opel_3 = 280 - opel_1
        leapmotor_1 = 100  # Leapmotor z.B. Standort 1
        print()
        print("--- Vorschlag nach Marken (280 Opel / 200 Hyundai / 100 Leapmotor) ---")
        print("  Opel 280 auf Standort 1+3 nach VJ-Anteil:")
        print(f"    {STANDORT_NAMEN.get(1)}: {opel_1} Opel")
        print(f"    {STANDORT_NAMEN.get(3)}: {opel_3} Opel")
        print(f"  Hyundai 200: {STANDORT_NAMEN.get(2)}: 200")
        print(f"  Leapmotor 100: {STANDORT_NAMEN.get(1)}: {leapmotor_1} (Beispiel)")
        print("  → NW Stück pro Standort für Abteilungsleiter-Planung:")
        print(f"    Standort 1 (DEG Opel): {opel_1 + leapmotor_1} NW  (Opel + Leapmotor)")
        print(f"    Standort 2 (HYU):       200 NW  (Hyundai)")
        print(f"    Standort 3 (LAN):       {opel_3} NW  (Opel)")
    print()
    print("GW wie oben (850 nach VJ-Anteilen verteilt).")
    print("=" * 60)


if __name__ == "__main__":
    main()
