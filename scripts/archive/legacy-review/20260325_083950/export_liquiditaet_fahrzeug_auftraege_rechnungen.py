#!/usr/bin/env python3
"""
Export: Fahrzeug-Aufträge (noch nicht in Rechnung) und Rechnungen (Rechnungsdatum im Zeitraum)
mit Werten für Dispo-Prüfung. Enthält Ablöse (Einkaufsfinanzierung) aus Portal.

- Doppel-VIN: Dieselbe VIN kann in Locosoft in beiden Listen vorkommen (z. B. N-Zeile noch offen,
  T/V-Zeile bereits in Rechnung). Für Liquidität zählt jede VIN nur einmal: wenn sie in
  "Rechnungen" vorkommt, wird sie in "Aufträge" weggelassen (Ablöse/Fälligkeit zählt beim Rechnungsdatum).
- Ablöse: Pro VIN aus Portal fahrzeugfinanzierungen (aktiv) → ablöse_eur; Netto = VK − Ablöse.

Aufruf: cd /opt/greiner-portal && python3 scripts/export_liquiditaet_fahrzeug_auftraege_rechnungen.py [--tage 60]
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import date, timedelta

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

STANDORT = {1: "DEG", 2: "HYU", 3: "LAN"}


def _vin_norm(vin):
    if not vin:
        return ""
    return (vin or "").strip().upper()


def main():
    parser = argparse.ArgumentParser(description="Fahrzeug-Aufträge und Rechnungen für Dispo exportieren")
    parser.add_argument("--tage", type=int, default=60, help="Zeitraum für Rechnungsdatum (Tage ab heute)")
    args = parser.parse_args()
    heute = date.today()
    ende = heute + timedelta(days=args.tage)

    from api.db_utils import locosoft_session, db_session, rows_to_list, row_to_dict
    from psycopg2.extras import RealDictCursor

    out_dir = os.path.join(PROJECT_ROOT, "docs", "workstreams", "controlling", "Liquiditaet", "export")
    os.makedirs(out_dir, exist_ok=True)

    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # ---- 1. Rechnungen ZUERST (Rechnungsdatum im Zeitraum) ----
        cur.execute("""
            SELECT
                dv.dealer_vehicle_type AS typ,
                dv.dealer_vehicle_number AS haendler_nr,
                dv.out_invoice_date AS rechnungsdatum,
                dv.out_invoice_number AS rechnungsnummer,
                dv.out_sale_price AS vk_preis_eur,
                dv.out_subsidiary AS subsidiary,
                v.vin AS vin
            FROM dealer_vehicles dv
            LEFT JOIN vehicles v ON v.internal_number = dv.vehicle_number
                AND v.dealer_vehicle_type = dv.dealer_vehicle_type
                AND v.dealer_vehicle_number = dv.dealer_vehicle_number
            WHERE dv.out_invoice_date IS NOT NULL
              AND dv.out_invoice_date >= %s AND dv.out_invoice_date <= %s
            ORDER BY dv.out_invoice_date, dv.dealer_vehicle_number
        """, (heute, ende))
        rechnungen = rows_to_list(cur.fetchall(), cur)

        # VINs, die bereits in Rechnungen vorkommen → in Aufträgen weglassen (keine Doppelzählung)
        vins_in_rechnungen = {_vin_norm(r.get("vin")) for r in rechnungen if _vin_norm(r.get("vin"))}

        # ---- 2. Aufträge (noch nicht in Rechnung), OHNE VINs die schon in Rechnungen sind ----
        cur.execute("""
            SELECT
                dv.dealer_vehicle_type AS typ,
                dv.dealer_vehicle_number AS haendler_nr,
                dv.out_sales_contract_date AS vertragsdatum,
                dv.out_sales_contract_number AS vertragsnummer,
                dv.out_sale_price AS vk_preis_eur,
                dv.out_estimated_invoice_value AS geschaetzter_rechnungswert,
                dv.out_subsidiary AS subsidiary,
                v.vin AS vin
            FROM dealer_vehicles dv
            LEFT JOIN vehicles v ON v.internal_number = dv.vehicle_number
                AND v.dealer_vehicle_type = dv.dealer_vehicle_type
                AND v.dealer_vehicle_number = dv.dealer_vehicle_number
            WHERE dv.out_sales_contract_date IS NOT NULL
              AND dv.out_invoice_date IS NULL
            ORDER BY dv.out_sales_contract_date DESC, dv.dealer_vehicle_number
        """)
        auftraege_raw = rows_to_list(cur.fetchall(), cur)
        # Deduplizierung: VIN nur in einer Liste (Priorität Rechnungen)
        auftraege = [r for r in auftraege_raw if _vin_norm(r.get("vin")) not in vins_in_rechnungen]
    n_entfernt = len(auftraege_raw) - len(auftraege)

    # ---- 3. Ablöse aus Portal (fahrzeugfinanzierungen) für alle VINs ----
    all_vins = []
    for r in auftraege + rechnungen:
        v = _vin_norm(r.get("vin"))
        if v:
            all_vins.append(v)
    ablöse_map = {}  # vin_norm -> summe aktueller_saldo
    if all_vins:
        with db_session() as drive_conn:
            drive_cur = drive_conn.cursor()
            placeholders = ",".join(["%s"] * len(all_vins))
            drive_cur.execute(f"""
                SELECT TRIM(UPPER(vin)) AS vin, COALESCE(SUM(aktueller_saldo), 0) AS ablöse
                FROM fahrzeugfinanzierungen
                WHERE aktiv = true AND TRIM(UPPER(vin)) IN ({placeholders})
                GROUP BY TRIM(UPPER(vin))
            """, all_vins)
            for row in drive_cur.fetchall():
                d = row_to_dict(row, drive_cur)
                ablöse_map[d.get("vin") or ""] = float(d.get("ablöse") or 0)

    for r in auftraege + rechnungen:
        r["standort"] = STANDORT.get(r.get("subsidiary") or 0) or str(r.get("subsidiary") or "")
        vin_n = _vin_norm(r.get("vin"))
        r["ablöse_eur"] = ablöse_map.get(vin_n, 0.0)
        vk = float(r.get("vk_preis_eur") or 0)
        r["netto_liquiditaet_eur"] = round(vk - r["ablöse_eur"], 2)

    # CSV: Aufträge (inkl. Ablöse + Netto Liquidität)
    csv_auftraege = os.path.join(out_dir, "liquiditaet_auftraege_noch_nicht_in_rechnung.csv")
    cols_auftrag = ["typ", "haendler_nr", "vertragsdatum", "vertragsnummer", "vk_preis_eur", "geschaetzter_rechnungswert", "standort", "vin", "ablöse_eur", "netto_liquiditaet_eur"]
    with open(csv_auftraege, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols_auftrag, extrasaction="ignore", delimiter=";")
        w.writeheader()
        for r in auftraege:
            w.writerow({k: r.get(k) for k in cols_auftrag})

    # CSV: Rechnungen (inkl. Ablöse + Netto Liquidität)
    csv_rechnungen = os.path.join(out_dir, "liquiditaet_rechnungen_im_zeitraum.csv")
    cols_rechnung = ["typ", "haendler_nr", "rechnungsdatum", "rechnungsnummer", "vk_preis_eur", "standort", "vin", "ablöse_eur", "netto_liquiditaet_eur"]
    with open(csv_rechnungen, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols_rechnung, extrasaction="ignore", delimiter=";")
        w.writeheader()
        for r in rechnungen:
            w.writerow({k: r.get(k) for k in cols_rechnung})

    # Konsolen-Ausgabe: Tabellen
    def fmt_eur(v):
        if v is None:
            return ""
        try:
            return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            return str(v)

    if n_entfernt:
        print(f"Hinweis: {n_entfernt} Auftragszeilen mit VIN, die bereits in 'Rechnungen' vorkommen, wurden weggelassen (keine Doppelzählung).")
    print("=" * 120)
    print("Fahrzeug-Aufträge (noch nicht in Rechnung) – zur Dispo-Prüfung")
    print(f"Anzahl: {len(auftraege)} | Summe VK: {fmt_eur(sum(float(x.get('vk_preis_eur') or 0) for x in auftraege))} € | Summe Ablöse: {fmt_eur(sum(x.get('ablöse_eur') or 0 for x in auftraege))} € | Summe Netto: {fmt_eur(sum(x.get('netto_liquiditaet_eur') or 0 for x in auftraege))} €")
    print("=" * 120)
    print(f"{'Typ':<4} {'Händler-Nr':>10} {'Vertragsdatum':<12} {'Vertragsnr':<18} {'VK (€)':>12} {'Ablöse (€)':>12} {'Netto (€)':>12} {'Standort':<6} {'VIN'}")
    print("-" * 120)
    for r in auftraege[:200]:
        print(f"{str(r.get('typ') or ''):<4} {r.get('haendler_nr') or '':>10} {str(r.get('vertragsdatum') or ''):<12} {str(r.get('vertragsnummer') or ''):<18} {fmt_eur(r.get('vk_preis_eur')):>12} {fmt_eur(r.get('ablöse_eur')):>12} {fmt_eur(r.get('netto_liquiditaet_eur')):>12} {str(r.get('standort') or ''):<6} {str(r.get('vin') or '')}")
    if len(auftraege) > 200:
        print(f"... und {len(auftraege) - 200} weitere Zeilen (siehe CSV).")

    print()
    print("=" * 120)
    print("Fahrzeug-Rechnungen (Rechnungsdatum im Zeitraum) – zur Dispo-Prüfung")
    print(f"Zeitraum: {heute} bis {ende} | Anzahl: {len(rechnungen)} | Summe VK: {fmt_eur(sum(float(x.get('vk_preis_eur') or 0) for x in rechnungen))} € | Summe Ablöse: {fmt_eur(sum(x.get('ablöse_eur') or 0 for x in rechnungen))} € | Summe Netto: {fmt_eur(sum(x.get('netto_liquiditaet_eur') or 0 for x in rechnungen))} €")
    print("=" * 120)
    print(f"{'Typ':<4} {'Händler-Nr':>10} {'Rechnungsdatum':<14} {'Rechnungsnr':>12} {'VK (€)':>12} {'Ablöse (€)':>12} {'Netto (€)':>12} {'Standort':<6} {'VIN'}")
    print("-" * 120)
    for r in rechnungen:
        print(f"{str(r.get('typ') or ''):<4} {r.get('haendler_nr') or '':>10} {str(r.get('rechnungsdatum') or ''):<14} {r.get('rechnungsnummer') or '':>12} {fmt_eur(r.get('vk_preis_eur')):>12} {fmt_eur(r.get('ablöse_eur')):>12} {fmt_eur(r.get('netto_liquiditaet_eur')):>12} {str(r.get('standort') or ''):<6} {str(r.get('vin') or '')}")

    print()
    print("CSV-Export (inkl. Spalten ablöse_eur, netto_liquiditaet_eur):")
    print(f"  Aufträge:   {csv_auftraege}")
    print(f"  Rechnungen: {csv_rechnungen}")
    print("(Trennzeichen ;, UTF-8 mit BOM. Ablöse = Einkaufsfinanzierung Portal; Netto = VK − Ablöse für Liquidität.)")


if __name__ == "__main__":
    main()
