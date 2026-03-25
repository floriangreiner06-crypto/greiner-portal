#!/usr/bin/env python3
"""
Rückruf: VIN-Liste aus Excel gegen Locosoft abgleichen („bereits Kunde“ vs. „noch kein Kunde“).

Liest .xlsx aus docs/workstreams/werkstatt/Rückruf/ (oder --dir).
Ermittelt VIN-Spalte per Kopfzeile (VIN/FIN/Fahrgestellnummer) oder per Muster (17 Zeichen).
Abgleich gegen Locosoft vehicles.vin. Gibt Trefferanzahl und Kurzstatistik aus.

Aufruf (im Projektroot):
  python scripts/rueckruf_vin_abgleich_locosoft.py
  python scripts/rueckruf_vin_abgleich_locosoft.py --dir /mnt/greiner-portal-sync/docs/workstreams/werkstatt/Rückruf
  python scripts/rueckruf_vin_abgleich_locosoft.py --file docs/workstreams/werkstatt/Rückruf/KBM_PLZ_94_1.xlsx
"""
import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import openpyxl
except ImportError:
    print("openpyxl fehlt: pip install openpyxl")
    sys.exit(1)

DEFAULT_RUECKRUF_DIR = PROJECT_ROOT / "docs" / "workstreams" / "werkstatt" / "Rückruf"

# VIN: 17 Zeichen, Zeichensatz ISO 3779 (keine I, O, Q)
VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


def normalize_vin(val):
    if val is None:
        return ""
    s = str(val).strip().upper().replace(" ", "").replace("-", "")
    return s[:17] if len(s) >= 17 else s


def looks_like_vin(val):
    if val is None or not isinstance(val, (str, int, float)):
        return False
    s = normalize_vin(val)
    return len(s) == 17 and VIN_PATTERN.match(s) is not None


def read_sheet(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    return rows


def find_vin_column_index(rows):
    """
    Findet den Spaltenindex der VIN-Spalte.
    1) Kopfzeile suchen (erste Zeilen): VIN, FIN, Fahrgestellnummer, Fahrgestellnr.
    2) Kein Header: Spalte mit durchgängig 17-Zeichen-VINs (erste passende Spalte).
    """
    if not rows:
        return None
    # Prüfe erste 5 Zeilen auf Header
    for row_idx in range(min(5, len(rows))):
        row = rows[row_idx] or []
        for col_idx, cell in enumerate(row):
            c = str(cell or "").strip()
            if not c:
                continue
            c_upper = c.upper()
            if any(
                x in c_upper
                for x in ("VIN", "FIN", "FAHRGESTELLNUMMER", "FAHRGESTELLNR", "Fahrgestell")
            ):
                return col_idx
    # Kein Header: erste Spalte, in der (ab Zeile 0) überwiegend VIN-Muster vorkommt
    num_cols = max(len(r or []) for r in rows) if rows else 0
    for col_idx in range(num_cols):
        count_vin = 0
        count_total = 0
        for row in rows:
            if col_idx >= len(row or []):
                continue
            val = (row or [])[col_idx]
            if val is None or (isinstance(val, str) and not val.strip()):
                continue
            count_total += 1
            if looks_like_vin(val):
                count_vin += 1
        if count_total >= 1 and count_vin >= max(1, count_total * 0.5):
            return col_idx
    # Fallback: Spalte 0
    return 0


def extract_vins_from_rows(rows, vin_col_idx):
    vins = []
    for row in rows or []:
        if vin_col_idx >= len(row or []):
            continue
        val = (row or [])[vin_col_idx]
        v = normalize_vin(val)
        if len(v) == 17 and VIN_PATTERN.match(v):
            vins.append(v)
    return vins


def load_vins_from_excel(path):
    rows = read_sheet(path)
    if not rows:
        return [], None
    vin_col_idx = find_vin_column_index(rows)
    if vin_col_idx is None:
        return [], None
    vins = extract_vins_from_rows(rows, vin_col_idx)
    return vins, vin_col_idx


def load_vins_from_dir(directory):
    """Lädt alle VINs aus allen .xlsx im Ordner. Gibt (liste_vins, dateinamen_info) zurück."""
    xlsx_files = sorted(directory.glob("*.xlsx"))
    all_vins = []
    file_info = []
    for path in xlsx_files:
        vins, col_idx = load_vins_from_excel(path)
        all_vins.extend(vins)
        file_info.append((path.name, len(vins), col_idx))
    return all_vins, file_info


def query_locosoft_vins_present(vins_unique, batch_size=500):
    """
    Prüft welche VINs in Locosoft vehicles vorhanden sind.
    Gibt set der VINs zurück, die in Locosoft gefunden wurden.
    """
    from api.db_utils import locosoft_session, rows_to_list

    found = set()
    vins_list = list(vins_unique)
    for i in range(0, len(vins_list), batch_size):
        batch = vins_list[i : i + batch_size]
        placeholders = ",".join(["%s"] * len(batch))
        sql = f"""
            SELECT TRIM(UPPER(vin)) AS vin
            FROM vehicles
            WHERE vin IS NOT NULL AND TRIM(vin) != ''
              AND UPPER(TRIM(vin)) IN ({placeholders})
        """
        with locosoft_session() as conn:
            cur = conn.cursor()
            cur.execute(sql, batch)
            rows = cur.fetchall()
            for row in rows:
                v = (row[0] if isinstance(row, (tuple, list)) else row.get("vin")) if row else None
                if v:
                    found.add(str(v).strip().upper())
    return found


def main():
    parser = argparse.ArgumentParser(
        description="Rückruf: VIN-Liste aus Excel vs. Locosoft (Treffer = bereits Kunde)"
    )
    parser.add_argument(
        "--dir",
        default=None,
        help="Ordner mit .xlsx (Standard: docs/workstreams/werkstatt/Rückruf)",
    )
    parser.add_argument("--file", default=None, help="Einzelne Excel-Datei")
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists():
            print("Datei nicht gefunden:", path)
            sys.exit(1)
        vins, col_idx = load_vins_from_excel(path)
        file_info = [(path.name, len(vins), col_idx)]
    else:
        rueckruf_dir = Path(args.dir) if args.dir else DEFAULT_RUECKRUF_DIR
        if not rueckruf_dir.exists():
            sync_dir = Path("/mnt/greiner-portal-sync/docs/workstreams/werkstatt/Rückruf")
            if sync_dir.exists():
                rueckruf_dir = sync_dir
                print("Hinweis: Nutze Sync-Pfad", rueckruf_dir)
            else:
                print("Ordner nicht gefunden:", rueckruf_dir)
                print("Nutzen Sie --dir oder --file.")
                sys.exit(1)
        vins, file_info = load_vins_from_dir(rueckruf_dir)

    if not vins:
        print("Keine VINs in der Excel-Liste gefunden.")
        if file_info:
            for name, n, col in file_info:
                print(f"  {name}: {n} VINs (Spalte {col})")
        sys.exit(0)

    unique_vins = list(dict.fromkeys(vins))
    print("--- Rückruf VIN-Abgleich Locosoft ---")
    print(f"Excel: {len(vins)} VIN-Einträge, {len(unique_vins)} eindeutige VINs")
    for name, n, col in file_info:
        print(f"  {name}: {n} VINs (VIN-Spalte Index {col})")

    try:
        found = query_locosoft_vins_present(unique_vins)
    except Exception as e:
        print("Fehler bei Locosoft-Abfrage:", e)
        sys.exit(1)

    n_hit = len(found)
    n_miss = len(unique_vins) - n_hit
    print()
    print("Ergebnis:")
    print(f"  Treffer (VIN ist Kunde in Locosoft):  {n_hit}")
    print(f"  Nicht in Locosoft (noch kein Kunde):  {n_miss}")
    if unique_vins:
        pct = round(100.0 * n_hit / len(unique_vins), 1)
        print(f"  Anteil Treffer: {pct} %")
    print()
    print("Damit könnt ihr entscheiden, ob ein volles Feature (z. B. Portal-UI) lohnt.")


if __name__ == "__main__":
    main()
