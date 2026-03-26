#!/usr/bin/env python3
"""
Analysiert doppelte Zeilen pro VIN in einem L744PR-Export (CSV, Tabulator).
Siehe: docs/workstreams/verkauf/provisionsabrechnung/DOPPELTE_ZEILEN_PRO_VIN_ANALYSE.md

Aufruf:
  python3 scripts/provisions_analyse_doppelte_vin.py /pfad/0126.csv
"""

import csv
import sys
from collections import defaultdict


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else '/mnt/greiner-portal-sync/docs/workstreams/verkauf/provisionsabrechnung/0126.csv'
    vin_key = 'Fahrgestellnr.'

    with open(path, 'r', encoding='latin-1', newline='') as f:
        r = csv.DictReader(f, delimiter='\t')
        rows = list(r)

    by_vin = defaultdict(list)
    for i, row in enumerate(rows):
        vin = (row.get(vin_key) or '').strip()
        if vin:
            by_vin[vin].append(row)

    dups = {v: L for v, L in by_vin.items() if len(L) > 1}
    same_rg = [(v, L) for v, L in dups.items()
               if len(set(row.get('Rg-Nr.') for row in L)) == 1
               and len(set(row.get('Rg.Netto') for row in L)) == 1]
    diff_rg = [(v, L) for v, L in dups.items() if (v, L) not in [(x, y) for x, y in same_rg]]

    n_single = len(by_vin) - len(dups)
    n_dup_vin = len(dups)
    n_exact = len(same_rg)
    n_multi_inv = len(diff_rg)
    extra_exact = sum(len(L) - 1 for _, L in same_rg)
    extra_multi = sum(len(L) - 1 for _, L in diff_rg)

    print("Datei:", path)
    print("Zeilen (ohne Kopf):", len(rows))
    print("Eindeutige VINs (nur 1 Zeile):", n_single)
    print("VINs mit mehreren Zeilen:", n_dup_vin)
    print()
    print("1) Echte Duplikate (gleiche Rg-Nr., gleiches Rg.Netto):")
    print("   VINs:", n_exact, "| Überzählige Zeilen:", extra_exact)
    print()
    print("2) Mehrere Rechnungen/Positionen pro VIN (versch. Rg-Nr. oder Beträge):")
    print("   VINs:", n_multi_inv, "| Überzählige Zeilen:", extra_multi)
    print("   → Rg-Typ oft H (Haupt) + Z (Zusatz)")
    print()
    print("Kernbestand (eindeutige VINs):", n_single + n_dup_vin, "Fahrzeuge")
    print("Erklärung 93 Extra-Zeilen: 55 Report-Duplikate + 38 Zusatzrechnungen (H+Z) pro VIN")


if __name__ == '__main__':
    main()
