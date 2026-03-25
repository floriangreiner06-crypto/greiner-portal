#!/usr/bin/env python3
"""
Abgleich: Buchhaltungs-Excel-Bestände (VFW/Mietwagen) vs. Locosoft-Bestand (DRIVE-Abfrage).

Liest alle .xlsx aus docs/workstreams/controlling/AfA (oder --dir).
Lädt Locosoft-Bestand (gleiche Logik wie „Bestand laden“: VFW Typ V, Mietwagen Jw-Kz M, out_invoice_date IS NULL).
Vergleicht anhand VIN, Kom.Nr. (dealer_vehicle_type + number), Kennzeichen.

Aufruf (im Projektroot auf dem Server):
  pip install openpyxl   # falls noch nicht vorhanden
  python scripts/afa_abgleich_excel_locosoft.py

  # Excel-Dateien liegen im Sync-Ordner (Windows F:\\...\\AfA entspricht auf dem Server):
  python scripts/afa_abgleich_excel_locosoft.py --dir /mnt/greiner-portal-sync/docs/workstreams/controlling/AfA

  # CSV-Report schreiben:
  python scripts/afa_abgleich_excel_locosoft.py --dir /mnt/greiner-portal-sync/docs/workstreams/controlling/AfA --csv /tmp/afa_abgleich.csv
"""
import argparse
import sys
from pathlib import Path

# Projektroot = Parent von scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import openpyxl
except ImportError:
    print("openpyxl fehlt: pip install openpyxl")
    sys.exit(1)

DEFAULT_AFA_DIR = PROJECT_ROOT / "docs" / "workstreams" / "controlling" / "AfA"


def read_sheet(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    return rows


def extract_table(rows, header_row_idx, header_row):
    col_map = {}
    for j, cell in enumerate(header_row):
        c = (cell or "").strip()
        if "Fz.-Art" in c or (len(c) >= 2 and "Fz" in c and "Art" in c):
            col_map["Fz.-Art"] = j
        elif "Kom" in c and "Nr" in c:
            col_map["Kom.Nr."] = j
        elif "Jw-Kz" in c or "Jahreswagen" in c.lower():
            col_map["Jw-Kz"] = j
        elif "Fahrgestell" in c or "Fahrgestellnr" in c or (c and "FIN" in c.upper()):
            col_map["Fahrgestellnr."] = j
        elif "Modell-Bez" in c or ("Modell" in c and "Bez" in c):
            col_map["Modell-Bez."] = j
        elif "Kennzeichen" in c:
            col_map["Kennzeichen"] = j
        elif "Buchwert" in c:
            col_map["Buchwert"] = j
        elif "Einsatzwert" in c or (c and "Einsatz" in c):
            col_map["Einsatzwert"] = j
    data = []
    for row in rows[header_row_idx + 1 :]:
        if not any(x is not None and str(x).strip() for x in row):
            continue
        rec = {}
        for name, j in col_map.items():
            if j < len(row):
                val = row[j]
                if val is not None:
                    val = str(val).strip() if not isinstance(val, (int, float)) else val
                rec[name] = val
        if rec:
            data.append(rec)
    return data, col_map


def find_header_row(rows):
    for i in range(min(6, len(rows))):
        r = rows[i] or []
        for c in r:
            s = (c or "").strip()
            if s in ("Fz.-Art", "Jw-Kz", "Kom.Nr.") or "Fahrgestell" in s:
                return i, r
    return 0, rows[0] if rows else []


def load_excel_files(afa_dir):
    """Lädt alle .xlsx aus afa_dir, gibt Liste (dateiname, daten_rows, col_map) zurück."""
    xlsx = sorted(afa_dir.glob("*.xlsx"))
    result = []
    for path in xlsx:
        rows = read_sheet(path)
        if not rows:
            result.append((path.name, [], {}))
            continue
        hi, hr = find_header_row(rows)
        data, col_map = extract_table(rows, hi, hr)
        result.append((path.name, data, col_map))
    return result


def load_locosoft_bestand():
    """Lädt Locosoft-Bestand (VFW + Mietwagen Jw-Kz M, nicht verkauft). Gleiche Logik wie API Bestand laden."""
    from api.db_utils import locosoft_session, rows_to_list

    # Gleiche Bedingung wie in afa_api: Jw-Kz M
    cond = "UPPER(TRIM(COALESCE(dv.pre_owned_car_code, ''))) = 'M'"
    sql = """
    SELECT
        dv.dealer_vehicle_type,
        dv.dealer_vehicle_number,
        dv.vehicle_number AS internal_number,
        v.vin,
        v.license_plate,
        dv.out_license_plate,
        m.description AS model_description
    FROM dealer_vehicles dv
    LEFT JOIN vehicles v
        ON v.internal_number = dv.vehicle_number
        AND v.dealer_vehicle_type = dv.dealer_vehicle_type
        AND v.dealer_vehicle_number = dv.dealer_vehicle_number
    LEFT JOIN models m
        ON v.model_code = m.model_code AND v.make_number = m.make_number
    WHERE (
        (dv.dealer_vehicle_type = 'V' AND (dv.is_rental_or_school_vehicle IS NULL OR dv.is_rental_or_school_vehicle = false))
        OR (dv.is_rental_or_school_vehicle = true AND (""" + cond + """))
        OR (dv.dealer_vehicle_type = 'G' AND (""" + cond + """))
    )
    AND (dv.deactivated_date IS NULL AND dv.deactivated_by_employee_no IS NULL)
    AND (dv.out_invoice_date IS NULL)
    AND dv.vehicle_number IS NOT NULL
    ORDER BY dv.dealer_vehicle_type, dv.dealer_vehicle_number
    """
    with locosoft_session() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows_to_list(rows, cur)


def normalize_vin(v):
    if v is None:
        return ""
    return str(v).strip().upper()


def normalize_kom_nr(kom, fz_art):
    """Kom.Nr. kann 'G 12345' oder 12345 sein. Liefert (typ, nr) z.B. ('G', 12345)."""
    if kom is None or (isinstance(kom, str) and not kom.strip()):
        return None, None
    s = str(kom).strip().upper()
    if not s:
        return None, None
    # Typ aus Fz.-Art: V -> V, G -> G
    typ = (fz_art or "").strip().upper() or None
    if typ not in ("V", "G"):
        typ = "V" if "VFW" in (fz_art or "") else "G"
    # Zahl extrahieren
    parts = s.replace(",", " ").split()
    num = None
    for p in parts:
        if p in ("V", "G", "N", "D", "T"):
            typ = p
            continue
        try:
            num = int(float(p))
            break
        except (ValueError, TypeError):
            continue
    if num is None and s.isdigit():
        num = int(s)
    return typ or None, num


def main():
    parser = argparse.ArgumentParser(description="Abgleich Buchhaltungs-Excel vs. Locosoft-Bestand (AfA)")
    parser.add_argument("--dir", default=None, help="Ordner mit .xlsx (Standard: docs/workstreams/controlling/AfA)")
    parser.add_argument("--csv", default=None, help="Optional: Ergebnis als CSV schreiben")
    args = parser.parse_args()

    afa_dir = Path(args.dir) if args.dir else DEFAULT_AFA_DIR
    if not afa_dir.exists():
        # Fallback: Sync-Pfad
        sync_dir = Path("/mnt/greiner-portal-sync/docs/workstreams/controlling/AfA")
        if sync_dir.exists():
            afa_dir = sync_dir
            print("Hinweis: Nutze Sync-Pfad", afa_dir)
        else:
            print("Ordner nicht gefunden:", afa_dir)
            print("Nutzen Sie --dir für den Pfad zu den Excel-Dateien (z.B. F:\\...\\AfA unter Windows).")
            sys.exit(1)

    excel_files = load_excel_files(afa_dir)
    xlsx_count = sum(1 for _ in afa_dir.glob("*.xlsx"))
    if not xlsx_count:
        print("Keine .xlsx Dateien in", afa_dir)
        sys.exit(1)

    print("Locosoft-Bestand laden …")
    try:
        loco_list = load_locosoft_bestand()
    except Exception as e:
        print("Fehler beim Laden aus Locosoft:", e)
        sys.exit(1)

    # Locosoft-Listen für Abgleich
    loco_by_vin = {}
    loco_by_kom = {}
    loco_by_kennzeichen = {}
    for r in loco_list:
        vin = normalize_vin(r.get("vin"))
        if vin:
            loco_by_vin[vin] = r
        dt = (r.get("dealer_vehicle_type") or "").strip().upper()
        dn = r.get("dealer_vehicle_number")
        if dt and dn is not None:
            key = (dt, int(dn))
            loco_by_kom[key] = r
        for kz in (r.get("license_plate"), r.get("out_license_plate")):
            if kz and str(kz).strip():
                loco_by_kennzeichen[str(kz).strip().upper()] = r

    print("Locosoft-Bestand: {} Fahrzeuge (VFW + Mietwagen Jw-Kz M, nicht verkauft)\n".format(len(loco_list)))
    print("=" * 70)
    print("Abgleich: Excel (Buchhaltung) vs. Locosoft (DRIVE-Abfrage)")
    print("=" * 70)

    csv_rows = []
    for name, data, col_map in excel_files:
        if not data:
            print("\n--- {} --- (keine Datenzeilen)".format(name))
            continue
        in_loco_vin = []
        in_loco_kom = []
        in_loco_kz = []
        only_excel = []
        for rec in data:
            vin = normalize_vin(rec.get("Fahrgestellnr."))
            kom = rec.get("Kom.Nr.")
            fz_art = rec.get("Fz.-Art")
            kz = (rec.get("Kennzeichen") or "").strip()
            typ, num = normalize_kom_nr(kom, fz_art)
            matched = False
            if vin and vin in loco_by_vin:
                in_loco_vin.append(rec)
                matched = True
            if not matched and typ and num is not None and (typ, num) in loco_by_kom:
                in_loco_kom.append(rec)
                matched = True
            if not matched and kz and kz.upper() in loco_by_kennzeichen:
                in_loco_kz.append(rec)
                matched = True
            if not matched:
                only_excel.append(rec)

        n_match = len(in_loco_vin) + len(in_loco_kom) + len(in_loco_kz)
        n_only = len(only_excel)
        print("\n--- {} ---".format(name))
        print("  Excel-Zeilen:     {}".format(len(data)))
        print("  In Locosoft:      {} (davon VIN: {}, Kom.Nr.: {}, Kennzeichen: {})".format(
            n_match, len(in_loco_vin), len(in_loco_kom), len(in_loco_kz)))
        print("  Nur in Excel:     {} (nicht in Locosoft-Bestand)".format(n_only))
        if only_excel and len(only_excel) <= 15:
            for r in only_excel[:15]:
                vin = r.get("Fahrgestellnr.") or "-"
                kom = r.get("Kom.Nr.") or "-"
                kz = r.get("Kennzeichen") or "-"
                print("      VIN: {} | Kom.Nr.: {} | Kennz.: {}".format(vin, kom, kz))
        elif only_excel:
            for r in only_excel[:5]:
                vin = r.get("Fahrgestellnr.") or "-"
                kom = r.get("Kom.Nr.") or "-"
                kz = r.get("Kennzeichen") or "-"
                print("      VIN: {} | Kom.Nr.: {} | Kennz.: {}".format(vin, kom, kz))
            print("      … und {} weitere".format(len(only_excel) - 5))

        csv_rows.append([name, len(data), n_match, n_only])

    # Locosoft ohne Excel-Treffer (pro Kategorie grob)
    loco_vins = set(loco_by_vin.keys())
    excel_vins = set()
    for _, data, _ in excel_files:
        for rec in data:
            v = normalize_vin(rec.get("Fahrgestellnr."))
            if v:
                excel_vins.add(v)
    only_loco_count = len(loco_vins - excel_vins)
    print("\n" + "=" * 70)
    print("Locosoft-Bestand ohne Treffer in keiner Excel-Liste (VIN): {} Fahrzeuge".format(only_loco_count))
    print("  (kann normal sein: Excel je Liste getrennt; VIN-Abgleich ist über alle Listen)")

    if args.csv:
        out = Path(args.csv)
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            import csv
            w = csv.writer(f, delimiter=";")
            w.writerow(["Datei", "Excel_Zeilen", "In_Locosoft", "Nur_in_Excel"])
            w.writerows(csv_rows)
        print("\nCSV geschrieben:", out)


if __name__ == "__main__":
    main()
