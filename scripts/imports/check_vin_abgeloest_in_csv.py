#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft, ob VINs in den CSV-Imports (Stellantis, Santander, Hyundai) mit Bezahlung/Abgelöst vorkommen.

Santander: CSV hat Spalte "Finanzierungsstatus" (Aktiv / Abgelöst) – hier können wir direkt prüfen.
Stellantis: Excel enthält nur aktuellen Vertragsbestand; abgelöste VINs erscheinen nicht mehr.
Hyundai: Bestandsliste enthält nur aktive Verträge; abgelöste VINs fehlen in der CSV (in DB: aktiv=false).

Verwendung:
  python scripts/imports/check_vin_abgeloest_in_csv.py
  python scripts/imports/check_vin_abgeloest_in_csv.py --vin W0VZRHPY3R6006849
  python scripts/imports/check_vin_abgeloest_in_csv.py --vins vins.txt
"""
import csv
import sys
import argparse
from pathlib import Path

# Projekt-Pfad
sys.path.insert(0, '/opt/greiner-portal')

# Pfade (wie in den Import-Scripts)
SANTANDER_CSV_DIR = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Santander')
HYUNDAI_CSV_DIR = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge/HyundaiFinance')


def parse_german_date(date_str):
    if not date_str or not str(date_str).strip():
        return None
    from datetime import datetime
    s = str(date_str).strip().strip('"')
    try:
        if '.' in s:
            dt = datetime.strptime(s[:10], '%d.%m.%Y')
        else:
            dt = datetime.strptime(s[:10], '%Y-%m-%d')
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return None


def get_latest_santander_csv():
    if not SANTANDER_CSV_DIR.exists():
        return None
    files = list(SANTANDER_CSV_DIR.glob('Bestandsliste_*.csv'))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def get_latest_hyundai_csv():
    if not HYUNDAI_CSV_DIR.exists():
        return None
    files = list(HYUNDAI_CSV_DIR.glob('stockList_*.csv'))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def check_santander(csv_path, vins_to_check=None):
    """Liest Santander-CSV und gibt VINs mit Finanzierungsstatus 'Abgelöst' zurück."""
    if not csv_path or not csv_path.exists():
        return [], "Santander-CSV nicht gefunden"
    results = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            vin = (row.get('VIN') or '').strip().strip('"')
            if not vin:
                continue
            status = (row.get('Finanzierungsstatus') or '').strip()
            vin_upper = vin.upper()
            if vins_to_check:
                if vin_upper not in vins_to_check and not any(v in vin_upper or vin_upper in v for v in vins_to_check):
                    continue
            # Nur Abgelöst ausgeben, oder bei VIN-Filter auch Aktiv (damit man sieht: „noch aktiv“)
            if status == 'Abgelöst' or (vins_to_check and status):
                endfaelligkeit = parse_german_date(row.get('Endfälligkeit', ''))
                rechnungsdatum = parse_german_date(row.get('Rechnungsdatum', ''))
                results.append({
                    'vin': vin,
                    'status': status or '(leer)',
                    'endfaelligkeit': endfaelligkeit,
                    'rechnungsdatum': rechnungsdatum,
                    'quelle': 'Santander CSV',
                })
    return results, None


def check_db_santander_abgeloest(vins_to_check=None):
    """DB: Santander-Einträge mit finanzierungsstatus = 'Abgelöst'."""
    try:
        from api.db_connection import get_db
        conn = get_db()
        cur = conn.cursor()
        if vins_to_check:
            placeholders = ','.join(['%s'] * len(vins_to_check))
            cur.execute(f"""
                SELECT vin, finanzierungsstatus, endfaelligkeit, import_datum, datei_quelle
                FROM fahrzeugfinanzierungen
                WHERE finanzinstitut = 'Santander' AND UPPER(vin) IN ({placeholders})
            """, list(vins_to_check))
        else:
            cur.execute("""
                SELECT vin, finanzierungsstatus, endfaelligkeit, import_datum, datei_quelle
                FROM fahrzeugfinanzierungen
                WHERE finanzinstitut = 'Santander' AND finanzierungsstatus = 'Abgelöst'
            """)
        rows = cur.fetchall()
        conn.close()
        # Index-Zugriff (vin, finanzierungsstatus, endfaelligkeit, import_datum, datei_quelle)
        result = []
        for r in rows:
            if hasattr(r, 'keys'):
                result.append(dict(r))
            else:
                result.append({
                    'vin': r[0], 'finanzierungsstatus': r[1], 'endfaelligkeit': r[2],
                    'import_datum': r[3], 'datei_quelle': r[4]
                })
        return result
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description='Prüft VINs in CSV-Imports auf Abgelöst/Bezahlung')
    parser.add_argument('--vin', type=str, help='Einzelne VIN')
    parser.add_argument('--vins', type=str, help='Datei mit einer VIN pro Zeile')
    parser.add_argument('--db', action='store_true', help='Zusätzlich DB nach Santander Abgelöst abfragen')
    args = parser.parse_args()

    vins_to_check = None
    if args.vin:
        vins_to_check = [args.vin.strip().upper()]
    elif args.vins:
        vins_file = Path(args.vins)
        if not vins_file.exists():
            print(f"Datei nicht gefunden: {vins_file}")
            sys.exit(1)
        vins_to_check = [line.strip().upper() for line in vins_file.read_text(encoding='utf-8').splitlines() if line.strip()]

    print("=" * 70)
    print("VIN-Check: Abgelöst/Bezahlung in Stellantis/Santander/Hyundai CSV-Imports")
    print("=" * 70)
    if vins_to_check:
        print(f"Gesuchte VIN(s): {vins_to_check}\n")
    else:
        print("Alle VINs mit Status 'Abgelöst' (Santander) werden ausgegeben.\n")

    # Santander CSV
    csv_path = get_latest_santander_csv()
    if csv_path:
        print(f"📄 Santander: {csv_path.name} ({csv_path.stat().st_mtime})")
        results, err = check_santander(csv_path, vins_to_check)
        if err:
            print(f"   ⚠️ {err}\n")
        else:
            if not results:
                print("   Keine Treffer (keine VIN mit Status 'Abgelöst'" + (" für die angegebenen VINs" if vins_to_check else "") + ").")
            else:
                for r in results:
                    print(f"   ✓ VIN {r['vin']}: Finanzierungsstatus = {r['status']} | Endfälligkeit {r.get('endfaelligkeit') or '-'} | Rechnungsdatum {r.get('rechnungsdatum') or '-'}")
            print()
    else:
        print("📄 Santander: Keine Bestandsliste_*.csv gefunden.\n")

    # DB Santander Abgelöst (optional)
    if args.db or vins_to_check:
        rows = check_db_santander_abgeloest(vins_to_check)
        if rows:
            print("🗄️ DB (fahrzeugfinanzierungen, Santander, Abgelöst bzw. Treffer):")
            for r in rows:
                print(f"   VIN {r.get('vin')}: {r.get('finanzierungsstatus')} | Endfälligkeit {r.get('endfaelligkeit')} | Import {r.get('import_datum')} | {r.get('datei_quelle') or ''}")
            print()
        elif vins_to_check:
            print("🗄️ DB: Keine Santander-Einträge für die angegebenen VINs gefunden.\n")

    print("Hinweise:")
    print("  • Stellantis: Excel enthält nur aktuellen Vertragsbestand; abgelöste VINs erscheinen nicht in der Datei.")
    print("  • Hyundai: Bestandsliste nur aktive Verträge; abgelöst = VIN nicht mehr in CSV (in DB: aktiv=false).")
    print("  • Santander: Einzige Quelle mit explizitem Status 'Abgelöst' in der CSV.")
    print("=" * 70)


if __name__ == '__main__':
    main()
