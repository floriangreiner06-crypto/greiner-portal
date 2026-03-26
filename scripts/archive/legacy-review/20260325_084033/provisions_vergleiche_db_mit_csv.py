#!/usr/bin/env python3
"""
Simulation: Gleichen Monat aus DB (Locosoft) holen und mit der L744PR-CSV abgleichen.
Prüft: gleiche Fahrzeuge (VINs), gleiche Stückzahl, Abweichungen bei Rg-Nr., VKB, Fz.-Art, Rg.Netto.

Aufruf:
  python3 scripts/provisions_vergleiche_db_mit_csv.py
  python3 scripts/provisions_vergleiche_db_mit_csv.py --csv /pfad/0126.csv --monat 1 --jahr 2026
"""

import csv
import re
import sys
from collections import defaultdict
from datetime import date

sys.path.insert(0, '/opt/greiner-portal')


def _parse_netto(s):
    """Rg.Netto aus CSV: '17.500,00' -> float."""
    if not s:
        return None
    s = str(s).strip().replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def _norm_rg_nr_csv_to_db(csv_rg):
    """CSV Rg-Nr. 81101964 -> könnte 1101964 (ohne führende Ziffer) für Abgleich sein."""
    if not csv_rg:
        return None
    s = str(csv_rg).strip()
    if len(s) > 6 and s[:-6].isdigit() and s[-6:].isdigit():
        return s[-6:]  # letzte 6 Ziffern
    return s


def load_db_januar(jahr=2026, monat=1):
    """Lädt Januar aus Locosoft (Rechnungsdatum, ohne L744PR-Filter für Vollabgleich)."""
    import os
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    if _script_dir not in sys.path:
        sys.path.insert(0, _script_dir)
    from provisions_januar_filter_test import _filter_locosoft
    von = date(jahr, monat, 1)
    bis = date(jahr, monat + 1, 1) if monat < 12 else date(jahr + 1, 1, 1)
    rows, _ = _filter_locosoft(von, bis, datum_typ='rechnung', l744pr=False, betrieb=None)
    return rows


def load_csv_by_vin(path, vin_key='Fahrgestellnr.'):
    """Lädt CSV und gruppiert Zeilen pro VIN (alle Zeilen pro VIN)."""
    with open(path, 'r', encoding='latin-1', newline='') as f:
        r = csv.DictReader(f, delimiter='\t')
        rows = list(r)

    by_vin = defaultdict(list)
    for row in rows:
        vin = (row.get(vin_key) or '').strip()
        if not vin or vin == vin_key:
            continue
        by_vin[vin].append(row)
    return dict(by_vin)


def csv_representative_per_vin(csv_by_vin, db_rows=None):
    """
    Pro VIN eine CSV-Zeile wählen.
    Wenn db_rows gegeben: für jede VIN die Zeile, deren Rg.Netto am nächsten am DB-Wert liegt (gleiche Rechnung).
    Sonst: H vor Z, dann größtes Rg.Netto.
    """
    db_netto_by_vin = {}
    if db_rows:
        for r in db_rows:
            vin = str(r.get('fahrgestellnr') or '').strip()
            n = r.get('rg_netto')
            if vin and n is not None:
                try:
                    db_netto_by_vin[vin] = float(n)
                except (TypeError, ValueError):
                    pass

    repr_list = []
    for vin, occ in csv_by_vin.items():
        if db_netto_by_vin.get(vin) is not None:
            target = db_netto_by_vin[vin]
            chosen = min(occ, key=lambda r: abs((_parse_netto(r.get('Rg.Netto')) or 0) - target))
        else:
            def key(r):
                rg_typ = (r.get('Rg-Typ') or '').strip()
                netto = _parse_netto(r.get('Rg.Netto')) or 0
                return (0 if rg_typ == 'H' else 1, netto)
            chosen = max(occ, key=key)
        repr_list.append((vin, chosen))
    return repr_list


def compare(db_rows, csv_repr):
    """Vergleicht DB-Zeilen mit CSV-Repräsentanten. Gibt Match-Statistik und Differenzen zurück."""
    db_by_vin = {str(r.get('fahrgestellnr') or '').strip(): r for r in db_rows if r.get('fahrgestellnr')}
    csv_by_vin = {vin: row for vin, row in csv_repr}

    vins_db = set(db_by_vin.keys())
    vins_csv = set(csv_by_vin.keys())
    common = vins_db & vins_csv
    only_db = vins_db - vins_csv
    only_csv = vins_csv - vins_db

    diffs = []
    for vin in sorted(common):
        db = db_by_vin[vin]
        csv_row = csv_by_vin[vin]
        db_rg = str(db.get('rg_nr') or '')
        csv_rg = str(csv_row.get('Rg-Nr.') or csv_row.get('Rg-Nr') or '')
        db_netto = db.get('rg_netto')
        if db_netto is not None and hasattr(db_netto, '__float__'):
            db_netto = float(db_netto)
        csv_netto = _parse_netto(csv_row.get('Rg.Netto'))
        db_vkb = db.get('verk_vkb')
        csv_vkb = csv_row.get('verk. VKB')
        if csv_vkb is not None:
            csv_vkb = str(csv_vkb).strip()
        db_fz = str(db.get('fz_art') or '')
        csv_fz = str(csv_row.get('Fz.-Art') or '').strip()

        # Rg-Nr.: DB z.B. 1101964, CSV 81101964 (führende Ziffer = Betrieb/Typ); vergleiche letzte 6–7 Ziffern
        db_rg_clean = re.sub(r'\D', '', db_rg)[-7:] if db_rg else ''
        csv_rg_clean = re.sub(r'\D', '', csv_rg)[-7:] if csv_rg else ''
        rg_ok = (len(db_rg_clean) >= 5 and len(csv_rg_clean) >= 5 and
                 (db_rg_clean == csv_rg_clean or db_rg_clean.endswith(csv_rg_clean[-6:]) or csv_rg_clean.endswith(db_rg_clean[-6:])))

        netto_ok = (db_netto is None and csv_netto is None) or (
            db_netto is not None and csv_netto is not None and abs(float(db_netto) - float(csv_netto)) < 5.0
        )
        vkb_ok = str(db_vkb) == str(csv_vkb)
        # Fz.-Art: DB = B/L/F (Locosoft), CSV = D/G/N/V/T (Export) – unterschiedliche Codierung
        fz_ok = db_fz == csv_fz

        # Nur Rg-Nr., Netto und VKB als harte Abweichung; Fz.-Art hat in Export andere Codierung (B/L/F vs D/G/N/V/T)
        if not (rg_ok and netto_ok and vkb_ok):
            diffs.append({
                'vin': vin,
                'rg_ok': rg_ok, 'db_rg': db_rg, 'csv_rg': csv_rg,
                'netto_ok': netto_ok, 'db_netto': db_netto, 'csv_netto': csv_netto,
                'vkb_ok': vkb_ok, 'db_vkb': db_vkb, 'csv_vkb': csv_vkb,
                'fz_ok': fz_ok, 'db_fz': db_fz, 'csv_fz': csv_fz,
            })

    return {
        'only_db': sorted(only_db),
        'only_csv': sorted(only_csv),
        'common': len(common),
        'diffs': diffs,
        'n_db': len(db_by_vin),
        'n_csv': len(csv_by_vin),
    }


def main():
    import argparse
    p = argparse.ArgumentParser(description='DB vs. CSV für einen Monat vergleichen')
    p.add_argument('--csv', default='/mnt/greiner-portal-sync/docs/workstreams/verkauf/provisionsabrechnung/0126.csv', help='Pfad zur Monats-CSV')
    p.add_argument('--monat', type=int, default=1)
    p.add_argument('--jahr', type=int, default=2026)
    args = p.parse_args()

    print("=== Simulation: DB (Locosoft) vs. CSV (L744PR-Export) ===\n")
    print(f"Monat: {args.monat}/{args.jahr}")
    print(f"CSV:   {args.csv}\n")

    db_rows = load_db_januar(jahr=args.jahr, monat=args.monat)
    print(f"DB (Locosoft, Rechnungsdatum im Monat): {len(db_rows)} Zeilen (Fahrzeuge)")

    csv_by_vin = load_csv_by_vin(args.csv)
    csv_repr = csv_representative_per_vin(csv_by_vin, db_rows=db_rows)
    print(f"CSV (eine Zeile pro VIN, an DB-Netto angepasst): {len(csv_repr)} VINs\n")

    res = compare(db_rows, csv_repr)

    print("--- Abgleich VINs ---")
    print(f"  Nur in DB:  {len(res['only_db'])} VINs")
    if res['only_db'][:5]:
        print("    ", res['only_db'][:5], "..." if len(res['only_db']) > 5 else "")
    print(f"  Nur in CSV: {len(res['only_csv'])} VINs")
    if res['only_csv'][:5]:
        print("    ", res['only_csv'][:5], "..." if len(res['only_csv']) > 5 else "")
    print(f"  In beiden:  {res['common']} VINs\n")

    print("--- Abweichungen (Rg-Nr. / Netto / VKB; Fz.-Art-Codierung DB vs. Export unterschiedlich) ---")
    if not res['diffs']:
        print("  Keine – gleiche Fahrzeuge und gleiche Kernfelder (Rg-Nr., Netto, VKB).")
    else:
        print(f"  {len(res['diffs'])} VIN(s) mit Abweichung bei Rg-Nr./Netto/VKB:")
        for d in res['diffs'][:15]:
            parts = []
            if not d['rg_ok']:
                parts.append(f"Rg-Nr. DB={d['db_rg']} CSV={d['csv_rg']}")
            if not d['netto_ok']:
                parts.append(f"Netto DB={d['db_netto']} CSV={d['csv_netto']}")
            if not d['vkb_ok']:
                parts.append(f"VKB DB={d['db_vkb']} CSV={d['csv_vkb']}")
            if not d['fz_ok']:
                parts.append(f"Fz DB={d['db_fz']} CSV={d['csv_fz']}")
            print(f"    {d['vin']}: {', '.join(parts)}")
        if len(res['diffs']) > 15:
            print(f"    ... und {len(res['diffs']) - 15} weitere")

    print("\n--- Fazit ---")
    if res['common'] == res['n_db'] == res['n_csv'] and not res['diffs']:
        print("  Ja – gleiche Stückzahl und gleiche Daten/Fahrzeuge (VINs, Rg-Nr., Netto, VKB).")
    else:
        print(f"  Stückzahl: DB={res['n_db']}, CSV (eine Zeile pro VIN)={res['n_csv']}; gemeinsame VINs={res['common']}.")
        if not res['diffs']:
            print("  Keine Abweichungen bei Rg-Nr./Netto/VKB – Daten aus DB entsprechen der CSV.")
        else:
            print(f"  Abweichungen bei Rg-Nr./Netto/VKB: {len(res['diffs'])} VIN(s).")
            print("  (Mögliche Ursachen: Brutto vs. Netto in einer Quelle, Rundung, oder andere Rechnungszeile bei mehreren pro VIN.)")


if __name__ == '__main__':
    main()
