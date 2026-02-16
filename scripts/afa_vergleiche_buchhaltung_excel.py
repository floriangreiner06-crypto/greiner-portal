#!/usr/bin/env python3
"""
Vergleicht AfA-Buchhaltungs-Excel-Listen mit DRIVE-Filterlogik.
Liest docs/workstreams/controlling/AfA/*.xlsx und wertet aus:
- Spalten: Fz.-Art, Kom.Nr., Jw-Kz (Jahreswagenkennzeichen), Kennzeichen, Fahrgestellnr. (VIN), ggf. Nutzungsdauer
- Prüfung: Mietwagen-Listen nur mit Jw-Kz X? VFW-Listen Struktur
- Ausgabe: Zusammenfassung + ggf. Abweichungen für Filter-Anpassung
"""
import os
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("openpyxl fehlt: pip install openpyxl")
    sys.exit(1)

AFA_DIR = Path(__file__).resolve().parent.parent / "docs" / "workstreams" / "controlling" / "AfA"


def col_letter_to_idx(s):
    """A=0, B=1, ..., Z=25, AA=26, ..."""
    n = 0
    for c in (s or "").upper():
        n = n * 26 + (ord(c) - ord("A") + 1)
    return n - 1 if n else 0


def read_sheet(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    return rows


def find_header_row(rows, headers_wanted):
    """Erste Zeile finden, die alle gesuchten Header enthält (teilweise)."""
    for i, row in enumerate(rows):
        if not row:
            continue
        row_str = " ".join(str(c or "").strip() for c in row)
        if any(h in row_str for h in headers_wanted):
            return i, row
    return None, None


def normalize_header(c):
    s = (c or "").strip().lower()
    if "kom" in s and "nr" in s:
        return "Kom.Nr."
    if "jw" in s and "kz" in s:
        return "Jw-Kz"
    if "fz" in s and "art" in s:
        return "Fz.-Art"
    if "fahrgestell" in s or "fin" in s:
        return "Fahrgestellnr."
    if "modell" in s and "bez" in s:
        return "Modell-Bez."
    if "kennzeichen" in s or "kennz" in s:
        return "Kennzeichen"
    if "nutzung" in s and "dauer" in s:
        return "Nutzungsdauer"
    if "afa" in s or "abschreib" in s:
        return "AfA"
    return None


def extract_table(rows, header_row_idx, header_row):
    # Spaltenindex nach Header-Namen (exakt wie in Buchhaltung Excel: Zeile 2 = Fz.-Art, Kom.Nr., Jw-Kz, ...)
    col_map = {}
    for j, cell in enumerate(header_row):
        c = (cell or "").strip()
        if "Fz.-Art" in c or (len(c) >= 2 and "Fz" in c and "Art" in c):
            col_map["Fz.-Art"] = j
        elif "Kom" in c and "Nr" in c:
            col_map["Kom.Nr."] = j
        elif "Jw-Kz" in c or "Jahreswagen" in c.lower():
            col_map["Jw-Kz"] = j
        elif "Fahrgestell" in c or "Fahrgestellnr" in c:
            col_map["Fahrgestellnr."] = j
        elif "Modell-Bez" in c or ("Modell" in c and "Bez" in c):
            col_map["Modell-Bez."] = j
        elif "Kennzeichen" in c:
            col_map["Kennzeichen"] = j
        elif "Buchwert" in c:
            col_map["Buchwert"] = j
        elif "Einsatzwert" in c or (c and "Einsatz" in c):
            col_map["Einsatzwert"] = j
        elif "Nutzung" in (c or "") and "Dauer" in (c or ""):
            col_map["Nutzungsdauer"] = j
        elif "AfA" in (c or "") or "Abschreib" in (c or ""):
            col_map["AfA"] = j

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


def main():
    if not AFA_DIR.exists():
        print("Ordner nicht gefunden:", AFA_DIR)
        return

    xlsx_files = sorted(AFA_DIR.glob("*.xlsx"))
    if not xlsx_files:
        print("Keine .xlsx in", AFA_DIR)
        return

    print("=" * 60)
    print("AfA Buchhaltungs-Excel – Auswertung")
    print("=" * 60)

    all_mietwagen_jw = []
    all_vfw_jw = []
    nutzungsdauer_found = []
    file_summaries = []

    for path in xlsx_files:
        name = path.name
        rows = read_sheet(path)
        if not rows:
            print("\n", name, ": leer")
            continue

        # Header-Zeile: genau die Zeile, die eine Zelle "Fz.-Art" oder "Jw-Kz" hat (nicht in Langtext)
        header_row_idx, header_row = None, None
        for i in range(min(5, len(rows))):
            r = rows[i]
            if not r:
                continue
            for c in r:
                s = (c or "").strip()
                if s in ("Fz.-Art", "Jw-Kz", "Kom.Nr.") or s == "Fahrgestellnr.":
                    header_row_idx, header_row = i, r
                    break
            if header_row_idx is not None:
                break

        if header_row_idx is None:
            header_row_idx, header_row = 0, rows[0]

        data, col_map = extract_table(rows, header_row_idx, header_row)
        is_mietwagen = "mietwagen" in name.lower()
        is_vfw = "vfw" in name.lower()

        jw_values = []
        kennzeichen_values = []
        vin_values = []
        for rec in data:
            jw = rec.get("Jw-Kz")
            kz = rec.get("Kennzeichen")
            vin = rec.get("Fahrgestellnr.")
            if jw is not None and str(jw).strip():
                jw_values.append(str(jw).strip().upper())
            if kz is not None and str(kz).strip():
                kennzeichen_values.append(str(kz).strip())
            if vin is not None and str(vin).strip():
                vin_values.append(str(vin).strip())
            if "Nutzungsdauer" in rec and rec["Nutzungsdauer"] is not None:
                nutzungsdauer_found.append((name, rec.get("Nutzungsdauer")))

        jw_set = set(jw_values) if jw_values else set()
        has_x = "X" in jw_set or any("X" in (k or "") for k in kennzeichen_values)

        summary = {
            "name": name,
            "rows": len(data),
            "is_mietwagen": is_mietwagen,
            "is_vfw": is_vfw,
            "jw_values": list(jw_set),
            "has_x": has_x,
            "col_map": list(col_map.keys()),
        }
        file_summaries.append(summary)

        if is_mietwagen:
            all_mietwagen_jw.extend(jw_values)
        if is_vfw:
            all_vfw_jw.extend(jw_values)

        print(f"\n--- {name} ---")
        print(f"  Datenzeilen: {len(data)}")
        print(f"  Spalten: {list(col_map.keys())}")
        print(f"  Jw-Kz Werte (Beispiele): {list(jw_set)[:15]}")
        if kennzeichen_values:
            print(f"  Kennzeichen (Beispiele): {kennzeichen_values[:5]}")
        if is_mietwagen and jw_set and "X" not in jw_set and "M" not in jw_set and not has_x:
            print("  >>> Achtung: Mietwagen-Liste ohne Jw-Kz 'X' oder 'M' – Filter prüfen.")
        if is_mietwagen and ("X" in jw_set or "M" in jw_set or has_x):
            print("  >>> Mietwagen mit Jw-Kz X/M – DRIVE-Filter (X oder M) passt.")

    # Nutzungsdauer
    print("\n" + "=" * 60)
    print("Nutzungsdauer (AfA-Dauer)")
    if nutzungsdauer_found:
        for fname, val in nutzungsdauer_found[:20]:
            print(f"  {fname}: {val}")
    else:
        print("  In den Excel-Spalten keine Spalte 'Nutzungsdauer' / 'AfA-Dauer' gefunden.")
        print("  (Modul nutzt Default 72 Monate.)")

    # PDF prüfen (nur Hinweis)
    pdfs = list(AFA_DIR.glob("*.pdf"))
    if pdfs:
        print("\nDATEV-PDF:", pdfs[0].name)
        print("  (Nutzungsdauer/AfA-Dauer ggf. im PDF – manuell prüfen.)")

    # Empfehlung
    print("\n" + "=" * 60)
    print("Empfehlung Filter/Anpassung")
    mietwagen_jw_set = set(all_mietwagen_jw)
    if "mietwagen" in str(xlsx_files).lower():
        if "X" in mietwagen_jw_set or "M" in mietwagen_jw_set or not mietwagen_jw_set:
            print("  Mietwagen: DRIVE-Filter pre_owned_car_code IN ('X','M') + Kennzeichen X deckt Buchhaltungs-Listen ab.")
        else:
            print("  Mietwagen: In Listen Jw-Kz:", mietwagen_jw_set, "– ggf. Filter um weitere Codes erweitern.")
    print("  VFW: Filter dealer_vehicle_type 'V' unverändert.")
    return file_summaries


if __name__ == "__main__":
    main()
