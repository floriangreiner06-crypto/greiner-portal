#!/usr/bin/env python3
"""
Provisionsberechnung Januar 2026 für Rafael Kraus (VKB 2007) – Vergleich mit echter Abrechnung (PDF).

SSOT: Berechnung ausschließlich über api.provision_service (berechne_live_provision).
Option --sync: Schreibt Einzelberechnung als CSV + Report nach Windows-Sync.
"""
import argparse
import csv
import os
import sys
sys.path.insert(0, '/opt/greiner-portal')

SYNC_PROVISIONS = '/mnt/greiner-portal-sync/docs/workstreams/verkauf/provisionsabrechnung'


def main():
    from api.provision_service import berechne_live_provision

    parser = argparse.ArgumentParser(description='Provisionsberechnung Kraus Jan 2026 (SSOT: provision_service)')
    parser.add_argument('--sync', action='store_true', help='CSV + Report in Windows-Sync schreiben')
    args = parser.parse_args()

    vkb_kraus = 2007
    monat = '2026-01'
    result = berechne_live_provision(vkb_kraus, monat)

    sum_i = result['summe_kat_i']
    sum_ii = result['summe_kat_ii']
    sum_iii = result['summe_kat_iii']
    sum_iv = result['summe_kat_iv']
    total_berechnet = result['summe_gesamt']
    block_ii_prov = [(p['modell'], p.get('rg_netto', 0), p['provision']) for p in result['positionen_ii']]
    block_iii_prov = [(p['modell'], p.get('rg_netto', 0), p['provision']) for p in result['positionen_iii']]
    block_i_stueck = result['stueck_neuwagen']

    # Einzelzeilen für CSV (eine Zeile pro Fahrzeug + ggf. eine Summenzeile für I)
    einzel_rows = []
    if block_i_stueck > 0:
        db_sum = sum(p.get('deckungsbeitrag', 0) for p in result['positionen_i'])
        einzel_rows.append(('I Neuwagen', 'F', '', '', f'Summe DB {db_sum:.2f} €, {block_i_stueck} Stück', db_sum, sum_i))
    for p in result['positionen_ii']:
        einzel_rows.append(('II VFW', 'L', p.get('vin', ''), p.get('rg_nr', ''), p.get('modell', ''), p.get('rg_netto', 0), p['provision']))
    for p in result['positionen_iii']:
        einzel_rows.append(('III GW', 'B', p.get('vin', ''), p.get('rg_nr', ''), p.get('modell', ''), p.get('rg_netto', 0), p['provision']))
    for p in result['positionen_iv']:
        einzel_rows.append(('IV GW Bestand', 'G', p.get('vin', ''), p.get('rg_nr', ''), p.get('modell', ''), p.get('deckungsbeitrag', 0), p['provision']))

    pdf_vfw_sum = 253.61 + 166.96 + 208.47 + 166.96 + 224.16 + 151.28 + 197.86
    pdf_gw_sum = 300.00 + 103.00 + 204.12 + 176.47 + 139.59 + 263.03 + 138.66
    pdf_total = pdf_vfw_sum + pdf_gw_sum

    if args.sync:
        os.makedirs(SYNC_PROVISIONS, exist_ok=True)
        csv_path = os.path.join(SYNC_PROVISIONS, 'Einzelberechnung_Kraus_Jan2026.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(['Block', 'Typ_Locosoft', 'VIN', 'Rechnungsnummer', 'Fahrzeug', 'Netto_VK', 'Provision_EUR'])
            for row in einzel_rows:
                w.writerow(row)
        print(f"CSV geschrieben: {csv_path}")

    report_lines = []
    def out(s=''):
        report_lines.append(s)
        print(s)

    out("=== Provisionsberechnung Jan 2026 – Rafael Kraus (VKB 2007) ===\n")
    out("I. Neuwagen:     DB × 12 % + 50 €/Stück")
    out(f"   Stück (F): {block_i_stueck}, Summe DB: siehe Positionen → Provision: {sum_i:.2f} €\n")
    out("II. Testwagen/VFW (L): 1 %, min 103 €, max 300 €")
    for desc, netto, p in block_ii_prov:
        out(f"   {(desc or '')[:45]:45} Netto {netto:>10,.2f} → Prov. {p:>8.2f} €")
    out(f"   Summe Block II: {sum_ii:.2f} €\n")
    out("III. Gebrauchtwagen (B): 1 %, min 103 €, max 500 €")
    for desc, netto, p in block_iii_prov:
        out(f"   {(desc or '')[:45]:45} Netto {netto:>10,.2f} → Prov. {p:>8.2f} €")
    out(f"   Summe Block III: {sum_iii:.2f} €\n")
    out("IV. GW aus Bestand: 0 (keine Zuordnung)\n")
    out(f"   Total berechnet (I+II+III): {total_berechnet:.2f} €")
    out("")
    out("--- Vergleich mit echter Abrechnung (PDF) ---")
    out(f"   PDF Vorführwagen (7 Stück):  {pdf_vfw_sum:.2f} €")
    out(f"   PDF Gebrauchtwagen (7 Stück): {pdf_gw_sum:.2f} €")
    out(f"   PDF Total:                   {pdf_total:.2f} €")
    out(f"   Differenz (berechnet − PDF): {total_berechnet - pdf_total:.2f} €")

    if args.sync:
        report_path = os.path.join(SYNC_PROVISIONS, 'Einzelberechnung_Kraus_Jan2026_Report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        print(f"Report geschrieben: {report_path}")


if __name__ == '__main__':
    main()
