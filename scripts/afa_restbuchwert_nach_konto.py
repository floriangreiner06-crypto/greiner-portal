#!/usr/bin/env python3
"""
DRIVE Restbuchwerte (Summe) pro AfA-Sachkonto zum Abgleich mit der Buchhaltung.
Stichtag: heute. Nur aktive Fahrzeuge (status='aktiv'), Tageszulassungen zählen mit.
Ausführung: python scripts/afa_restbuchwert_nach_konto.py
"""
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.db_utils import db_session, row_to_dict
from api.afa_api import (
    berechne_restbuchwert,
    AFA_KONTO_HABEN_MIETWAGEN,
    AFA_KONTO_HABEN_VFW,
    BETRIEBSNR_TO_STANDORT,
)


def main():
    stichtag = date.today()
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, vin, kennzeichen, fahrzeug_bezeichnung, betriebsnr, fahrzeugart,
                   anschaffungskosten_netto, afa_monatlich, nutzungsdauer_monate, anschaffungsdatum, tageszulassung
            FROM afa_anlagevermoegen
            WHERE status = 'aktiv'
            ORDER BY betriebsnr, fahrzeugart, fahrzeug_bezeichnung
        """)
        rows = cur.fetchall()
    colnames = [c[0] for c in (cur.description or [])]
    fahrzeuge = []
    for r in rows:
        row = row_to_dict(r, cur) if hasattr(r, 'keys') else dict(zip(colnames, r))
        if not row:
            continue
        rest = berechne_restbuchwert(row, stichtag)
        row['restbuchwert'] = rest
        fahrzeuge.append(row)

    # Summe pro (betriebsnr, fahrzeugart) → Konto 090301, 090302, 090401, 090402
    summen = {}  # (konto_5stellig, standort) -> summe
    for f in fahrzeuge:
        bn = int(f.get('betriebsnr') or 1)
        art = (f.get('fahrzeugart') or '').strip().upper() or 'VFW'
        standort = BETRIEBSNR_TO_STANDORT.get(bn, f'BN{bn}')
        if art == 'MIETWAGEN':
            konto = AFA_KONTO_HABEN_MIETWAGEN.get(bn, 90301)
        else:
            konto = AFA_KONTO_HABEN_VFW.get(bn, 90401)
        konto_str = f'0{konto}' if konto < 100000 else str(konto)
        key = (konto_str, standort)
        summen[key] = summen.get(key, 0) + (f.get('restbuchwert') or 0)

    # Ausgabe wie Buchhaltung (Sortierung: 090301 DEG, 090301 HYU, 090302 LAN, 090401 DEG, 090401 HYU, 090402 LAN)
    reihenfolge = [
        ('090301', 'DEG'), ('090301', 'HYU'), ('090302', 'LAN'),
        ('090401', 'DEG'), ('090401', 'HYU'), ('090402', 'LAN'),
    ]
    print(f"DRIVE Restbuchwerte (Stichtag {stichtag}) – nur aktive Fahrzeuge")
    print("=" * 60)
    total_drive = 0
    for (konto, standort) in reihenfolge:
        key = (konto, standort)
        wert = round(summen.get(key, 0), 2)
        total_drive += wert
        label = {"090301": "RENT", "090302": "RENT", "090401": "VFW", "090402": "VFW"}.get(konto, "")
        if konto == "090301":
            bezeichnung = f"RENT {standort}"
        elif konto == "090302":
            bezeichnung = f"RENT {standort}"
        else:
            bezeichnung = f"VFW {standort}"
        print(f"{konto} {bezeichnung:20} EUR {wert:>12,.2f} H".replace(",", "X").replace(".", ",").replace("X", "."))
    print("-" * 60)
    print(f"DRIVE Summe aller Konten:     EUR {total_drive:>12,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print()
    print("Zum Abgleich: Buchhaltung Guthaben (H) mit den Werten oben vergleichen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
