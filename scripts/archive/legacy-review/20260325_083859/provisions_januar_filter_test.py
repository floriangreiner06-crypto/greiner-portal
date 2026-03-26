#!/usr/bin/env python3
"""
Test: Locosoft-/Portal-Daten für Januar analog zum L744PR-Export filtern.

Die CSV/Excel-Daten sind Original-Exporte aus Locosoft L744PR „Verkaufsnachweisliste“.
Im Report-Dialog wird nach Rechnungsdatum gefiltert (z. B. 01.01.26–31.01.26), nicht nach Leistungsdatum.
→ --datum rechnung (empfohlen für Abgleich mit L744PR): Filter auf out_invoice_date / invoice_date.
→ --datum leistung: Filter auf invoices.service_date (bei Fahrzeugrechnungen in Locosoft oft NULL).

Verwendung:
  python3 scripts/provisions_januar_filter_test.py --datum rechnung --quelle locosoft
  python3 scripts/provisions_januar_filter_test.py --csv /pfad/0126.csv
"""

import argparse
import csv
import os
import sys
from datetime import date

sys.path.insert(0, '/opt/greiner-portal')


def main():
    parser = argparse.ArgumentParser(description='Provisionsfilter Januar (analog Excel) testen')
    parser.add_argument('--monat', type=int, default=1, help='Monat (1-12)')
    parser.add_argument('--jahr', type=int, default=2026, help='Jahr')
    parser.add_argument('--csv', type=str, default=None,
                        help='Pfad zu CSV (z.B. 0126.csv) zum Abgleich')
    parser.add_argument('--quelle', choices=['portal', 'locosoft'], default='portal',
                        help='Datenquelle: portal (sales-Tabelle) oder locosoft (direkt)')
    parser.add_argument('--limit', type=int, default=0, help='Max Zeilen ausgeben (0=alle)')
    parser.add_argument('--datum', choices=['leistung', 'rechnung'], default='rechnung',
                        help='Filter nach Rechnungsdatum (wie L744PR-Dialog) oder Leistungsdatum (Spalte C)')
    parser.add_argument('--l744pr', action='store_true',
                        help='Zusatzfilter wie L744PR-Dialog: VKB 1003–9001, Fahrzeugart D–V')
    parser.add_argument('--betrieb', type=str, default=None,
                        help='Nur verkaufenden Betrieb (1, 2 oder 3); leer = alle. L744PR-Screenshot hatte 1.')
    args = parser.parse_args()

    von = date(args.jahr, args.monat, 1)
    if args.monat == 12:
        bis = date(args.jahr + 1, 1, 1)
    else:
        bis = date(args.jahr, args.monat + 1, 1)

    datum_label = "Leistungsdatum (Spalte C)" if args.datum == 'leistung' else "Rechnungsdatum"
    print(f"Filter: {datum_label} >= {von} AND < {bis}")
    if args.datum == 'leistung' and args.quelle == 'locosoft':
        print("(Locosoft: COALESCE(invoices.service_date, invoice_date) – service_date bei Fahrzeugrechnungen oft NULL)")
    if args.l744pr:
        print("L744PR-Zusatzfilter: Verkaufsberater 1003–9001, Verkaufsart B–U", end="")
        if args.betrieb:
            print(f", Betrieb {args.betrieb}")
        else:
            print(", alle Betriebe")
    else:
        print()
    print()

    rows_portal, rows_loco = [], []
    spalten = []

    if args.quelle == 'portal':
        if args.datum == 'leistung':
            print("Hinweis: Portal-Tabelle 'sales' hat kein Leistungsdatum; nur Rechnungsdatum vorhanden.")
            print("Für Filter nach Leistungsdatum (wie Excel) bitte --quelle locosoft verwenden.")
        rows_portal, spalten = _filter_portal(von, bis, args.datum, l744pr=args.l744pr, betrieb=args.betrieb)
        n = len(rows_portal)
        print(f"[Portal sales] Treffer: {n}")
        if n == 0:
            print("Hinweis: sync_sales ausführen, damit Portal sales aktuell ist.")
        else:
            _ausgabe(rows_portal, spalten, args.limit)
            _kurz_statistik(rows_portal, spalten)
    else:
        rows_loco, spalten = _filter_locosoft(von, bis, args.datum, l744pr=args.l744pr, betrieb=args.betrieb)
        n = len(rows_loco)
        print(f"[Locosoft] Treffer: {n}")
        if n > 0:
            _ausgabe(rows_loco, spalten, args.limit)
            _kurz_statistik(rows_loco, spalten)

    rows_aktuell = rows_portal if args.quelle == 'portal' else rows_loco

    if args.csv and os.path.isfile(args.csv):
        print()
        print("--- Abgleich mit CSV ---")
        n_csv, csv_rows = _lade_csv(args.csv)
        print(f"CSV Zeilen (ohne Kopf): {n_csv}")
        if n > 0 and n_csv > 0:
            print(f"{args.quelle}: {n} | CSV: {n_csv} | Differenz: {n - n_csv}")
            if abs(n - n_csv) > 0:
                print("Hinweis: Abweichung kann durch Exportquelle, Spalte C (Leistungsdatum) oder Belegarten entstehen.")
        elif n_csv > 0 and args.datum == 'leistung':
            print(f"Erwartung Excel (1 Überschrift + 93 Rechnungszeilen): {n_csv} Zeilen. DB-Treffer: {n}.")
        if csv_rows and rows_aktuell:
            _vergleiche_stichprobe(rows_aktuell, csv_rows, spalten)


def _filter_portal(von, bis, datum_typ='rechnung', l744pr=False, betrieb=None):
    """Filtert Portal sales. Nur Rechnungsdatum verfügbar (out_invoice_date); Leistungsdatum fehlt in sales."""
    from api.db_utils import db_session, rows_to_list

    where_extra = []
    params = [von, bis]
    if l744pr:
        where_extra.append("AND s.salesman_number BETWEEN 1003 AND 9001")
        where_extra.append("AND s.out_sale_type >= 'B' AND s.out_sale_type <= 'U'")
    if betrieb:
        try:
            b = int(betrieb)
            where_extra.append("AND s.out_subsidiary = %s")
            params.append(b)
        except ValueError:
            pass
    where_sql = " ".join(where_extra) if where_extra else ""

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT
                s.out_invoice_date       AS rg_datum,
                s.out_invoice_number     AS rg_nr,
                s.out_subsidiary        AS verk_betrieb,
                s.salesman_number       AS verk_vkb,
                s.out_sale_type         AS fz_art,
                s.model_description     AS modell_bez,
                s.netto_vk_preis        AS rg_netto,
                s.deckungsbeitrag       AS deckungsbeitrag,
                s.db_prozent            AS db_prozent,
                s.vin                   AS fahrgestellnr,
                s.dealer_vehicle_type,
                s.dealer_vehicle_number
            FROM sales s
            WHERE s.out_invoice_date IS NOT NULL
              AND s.out_invoice_date >= %s
              AND s.out_invoice_date < %s
              {where_sql}
            ORDER BY s.out_invoice_date, s.out_invoice_number
        """, params)
        rows = rows_to_list(cur.fetchall())
    spalten = ['rg_datum', 'rg_nr', 'verk_betrieb', 'verk_vkb', 'fz_art', 'modell_bez',
               'rg_netto', 'deckungsbeitrag', 'db_prozent', 'fahrgestellnr']
    return rows, spalten


def _filter_locosoft(von, bis, datum_typ='leistung', l744pr=False, betrieb=None):
    """Filtert Locosoft dealer_vehicles + invoices. datum_typ='leistung' = Spalte C (service_date), sonst out_invoice_date."""
    from api.db_utils import locosoft_session, rows_to_list

    if datum_typ == 'leistung':
        # Excel Spalte C = Leistungsdatum. Locosoft: invoices.service_date, oft NULL → Fallback invoice_date
        where_date = "COALESCE(i.service_date, i.invoice_date) >= %s AND COALESCE(i.service_date, i.invoice_date) < %s"
        order_by = "COALESCE(i.service_date, i.invoice_date), dv.out_invoice_number"
    else:
        where_date = "dv.out_invoice_date >= %s AND dv.out_invoice_date < %s"
        order_by = "dv.out_invoice_date, dv.out_invoice_number"

    params = [von, bis]
    where_extra = []
    if l744pr:
        # Screenshot: Verkaufsberater 1003–9001, Verkaufsart B–U (nicht Fahrzeugart D–V; B–U liefert gleiche Stückzahl wie ohne)
        where_extra.append("AND (dv.out_salesman_number_1 BETWEEN 1003 AND 9001)")
        where_extra.append("AND dv.out_sale_type >= 'B' AND dv.out_sale_type <= 'U'")
    if betrieb:
        try:
            b = int(betrieb)
            where_extra.append("AND dv.out_subsidiary = %s")
            params.append(b)
        except ValueError:
            pass
    where_sql = " ".join(where_extra) if where_extra else ""

    with locosoft_session() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT
                dv.out_invoice_date     AS rg_datum,
                i.service_date          AS leistungsdatum,
                dv.out_invoice_number   AS rg_nr,
                dv.out_subsidiary       AS verk_betrieb,
                dv.out_salesman_number_1 AS verk_vkb,
                dv.out_sale_type        AS fz_art,
                m.description          AS modell_bez,
                i.total_net             AS rg_netto,
                dv.out_sale_price       AS out_sale_price,
                v.vin                   AS fahrgestellnr,
                dv.dealer_vehicle_type,
                dv.dealer_vehicle_number
            FROM dealer_vehicles dv
            LEFT JOIN vehicles v
                ON dv.dealer_vehicle_number = v.dealer_vehicle_number
                AND dv.dealer_vehicle_type = v.dealer_vehicle_type
            LEFT JOIN models m
                ON dv.out_model_code = m.model_code AND dv.out_make_number = m.make_number
            INNER JOIN invoices i
                ON dv.out_invoice_type = i.invoice_type
                AND dv.out_invoice_number::integer = i.invoice_number
                AND i.subsidiary = dv.out_subsidiary
            WHERE dv.out_invoice_date IS NOT NULL
              AND {where_date}
              {where_sql}
            ORDER BY {order_by}
        """, params)
        raw = cur.fetchall()
    # Portal hat deckungsbeitrag berechnet; Locosoft nur out_sale_price / total_net
    rows = []
    for r in raw:
        row = dict(r) if hasattr(r, 'keys') else {}
        if not row and r:
            names = [d[0] for d in cur.description]
            row = dict(zip(names, r))
        # Deckungsbeitrag in Locosoft müsste aus calc_* kommen – hier Platzhalter
        row['deckungsbeitrag'] = row.get('out_sale_price')
        row['db_prozent'] = None
        rows.append(row)
    spalten = ['rg_datum', 'rg_nr', 'verk_betrieb', 'verk_vkb', 'fz_art', 'modell_bez',
               'rg_netto', 'deckungsbeitrag', 'db_prozent', 'fahrgestellnr']
    return rows, spalten


def _ausgabe(rows, spalten, limit):
    if not rows:
        return
    print("Spalten:", ", ".join(spalten))
    print("-" * 80)
    for i, r in enumerate(rows):
        if limit and i >= limit:
            print(f"... und {len(rows) - limit} weitere")
            break
        line = []
        for k in spalten:
            v = r.get(k)
            if v is None:
                line.append("")
            elif isinstance(v, (int, float)) and k in ('rg_netto', 'deckungsbeitrag', 'db_prozent'):
                line.append(f"{v:,.2f}".replace(",", " "))
            else:
                line.append(str(v))
        print("\t".join(line))


def _kurz_statistik(rows, spalten):
    if not rows:
        return
    vkbs = set()
    fz_art = {}
    for r in rows:
        v = r.get('verk_vkb')
        if v is not None:
            vkbs.add(v)
        a = r.get('fz_art') or "?"
        fz_art[a] = fz_art.get(a, 0) + 1
    print()
    print("Kurz: Verkäufer (VKB) Anzahl:", len(vkbs), "| Fz.-Art:", dict(sorted(fz_art.items())))


def _lade_csv(path):
    """Lädt CSV (Tabulator), gibt Anzahl Datenzeilen und Liste der Zeilen (Dict) zurück."""
    with open(path, 'r', encoding='latin-1', newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
    return len(rows), rows


def _vergleiche_stichprobe(rows_db, csv_rows, spalten):
    """Vergleicht erste Zeilen DB vs CSV (Rg-Nr, VKB, Fz.-Art, Rg.Netto)."""
    print()
    print("Stichprobe (erste 3): DB vs CSV")
    csv_rg = None
    csv_vkb = None
    csv_fz = None
    csv_netto = None
    for i, row in enumerate(csv_rows[:3]):
        # CSV-Spaltennamen aus 0126: Rg-Nr., verk. VKB, Fz.-Art, Rg.Netto
        csv_rg = row.get('Rg-Nr.') or row.get('Rg-Nr')
        csv_vkb = row.get('verk. VKB')
        csv_fz = row.get('Fz.-Art')
        csv_netto = row.get('Rg.Netto')
        db = rows_db[i] if i < len(rows_db) else {}
        db_rg = str(db.get('rg_nr') or '')
        db_vkb = str(db.get('verk_vkb') or '')
        db_fz = str(db.get('fz_art') or '')
        db_netto = db.get('rg_netto')
        netto_str = f"{db_netto:,.2f}" if db_netto is not None else ""
        print(f"  {i+1}: Rg-Nr DB={db_rg} CSV={csv_rg} | VKB DB={db_vkb} CSV={csv_vkb} | Fz DB={db_fz} CSV={csv_fz} | Netto DB={netto_str} CSV={csv_netto}")


if __name__ == '__main__':
    main()
