#!/usr/bin/env python3
"""Anfangsbestände 01.09. aus DATEV Afa_*.pdf extrahieren, optional mit Locosoft vergleichen."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF_DIR = PROJECT_ROOT / "docs" / "workstreams" / "controlling" / "AfA"


def run_pdftotext(pdf_path):
    try:
        r = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=60, cwd=str(PROJECT_ROOT))
        if r.returncode == 0:
            return r.stdout or ""
        return ""
    except Exception as e:
        print("pdftotext:", e, file=sys.stderr)
        return ""


def parse_pdf(text, quelle, betrieb, art):
    pos = []
    kz_re = re.compile(r"(DEG-[A-Z]+\s*[\dA-Z]+|LAN-[A-Z]+\s*[\dA-Z]+)")
    dat_re = re.compile(r"(\d{2}\.\d{2}\.\d{4})")
    eur_re = re.compile(r"([\d.]+\d{2}),(\d{2})")
    for i, line in enumerate(text.splitlines()):
        m = kz_re.search(line)
        if not m:
            continue
        kz = m.group(1).strip()
        if "," in kz:
            kz = kz.split(",")[0].strip()
        dates = dat_re.findall(line)
        eur = eur_re.findall(line)
        ahk = bw = None
        if eur:
            ahk = float(eur[0][0].replace(".", "") + "." + eur[0][1])
        if len(eur) >= 2:
            bw = float(eur[1][0].replace(".", "") + "." + eur[1][1])
        pos.append({"quelle": quelle, "betrieb": betrieb, "fahrzeugart": art,
            "kennzeichen": kz, "anschaffungsdatum": dates[0] if dates else None,
            "ahk": ahk, "buchwert_0109": bw})
    return pos


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pdf-dir", type=Path, default=DEFAULT_PDF_DIR)
    p.add_argument("--locosoft", action="store_true")
    p.add_argument("--csv", type=Path)
    args = p.parse_args()
    pdf_dir = args.pdf_dir if args.pdf_dir.exists() else Path("/mnt/greiner-portal-sync/docs/workstreams/controlling/AfA")
    if not pdf_dir.exists():
        print("PDF-Ordner fehlt", file=sys.stderr)
        return 1
    all_pos = []
    for pdf in sorted(pdf_dir.glob("Afa_*.pdf")):
        txt = run_pdftotext(pdf)
        if not txt:
            continue
        betrieb = "LAN" if "landau" in pdf.name.lower() else "DEG"
        art = "MIETWAGEN" if "mietwagen" in pdf.name.lower() else "VFW"
        parsed = parse_pdf(txt, pdf.name, betrieb, art)
        all_pos.extend(parsed)
        print(pdf.name, len(parsed), "Positionen", file=sys.stderr)
    if args.locosoft and all_pos:
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from api.db_utils import locosoft_session, rows_to_list
            with locosoft_session() as conn:
                cur = conn.cursor()
                cur.execute("SELECT v.vin, v.license_plate, dv.out_license_plate, dv.out_invoice_date FROM vehicles v JOIN dealer_vehicles dv ON dv.vehicle_number=v.internal_number AND dv.dealer_vehicle_type=v.dealer_vehicle_type AND dv.dealer_vehicle_number=v.dealer_vehicle_number")
                loco = rows_to_list(cur.fetchall(), cur)
            for p in all_pos:
                kz = (p.get("kennzeichen") or "").replace(" ", "").upper()
                p["locosoft_vin"] = p["locosoft_out_invoice_date"] = p["locosoft_match"] = None
                for r in loco:
                    lp = (r.get("license_plate") or "").strip().replace(" ", "").upper()
                    olp = (r.get("out_license_plate") or "").strip().replace(" ", "").upper()
                    if not kz or (not lp and not olp):
                        continue
                    if kz == lp or kz == olp:
                        p["locosoft_vin"], p["locosoft_out_invoice_date"], p["locosoft_match"] = r.get("vin"), r.get("out_invoice_date"), "kz"
                        break
            print("Locosoft:", sum(1 for x in all_pos if x.get("locosoft_match")), "/", len(all_pos), file=sys.stderr)
        except Exception as e:
            print("Locosoft:", e, file=sys.stderr)
    if args.csv:
        import csv
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["quelle","betrieb","fahrzeugart","kennzeichen","anschaffungsdatum","ahk","buchwert_0109","locosoft_vin","locosoft_out_invoice_date","locosoft_match"], extrasaction="ignore")
            w.writeheader()
            w.writerows(all_pos)
        print("CSV:", args.csv, file=sys.stderr)
    for x in all_pos[:20]:
        print(x)
    if len(all_pos) > 20:
        print("...", len(all_pos) - 20, "weitere")
    return 0


if __name__ == "__main__":
    sys.exit(main())
