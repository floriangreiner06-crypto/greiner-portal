#!/usr/bin/env python3
"""
Vorführwagen (VFW) für Lohnsteuerprüfung – Pauschale Dienstwagenbesteuerung
============================================================================
Liefert aus Locosoft alle Vorführwagen im Prüfungszeitraum 01.2022–12.2025
mit mehr als 1.000 km – inkl. Antriebsart (1 % vs. 0,5 % / 0,25 %).

VFW-Erkennung (Locosoft):
- Kommissionsnummer (Kom.Nr.) nur V oder G (T ausgeschlossen)
- V = unverkauft, G = z. B. verkaufte Ex-VFW (Jahreswagenkennzeichen X)

Verwendung (auf Server, aus Projektroot):
    python scripts/vfw_lohnsteuer_2023_2024.py
    python scripts/vfw_lohnsteuer_2023_2024.py --csv vfw_lohnsteuer_2022_2025.csv

Ausgabe: Tabelle (und optional CSV) mit Kennzeichen, Modell, EZ, km, Antriebsart,
         Hinweis ob E/Hybrid (ermäßigte Versteuerung).
"""

import argparse
import csv
import sys
from pathlib import Path

# Projektroot für Imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor


# Kommissionsnummer nur V oder G (T ausgeschlossen)
VFW_KOMM_NR = ('V', 'G')

# Standort-Namen für Ausgabe
STANDORT_NAMEN = {1: 'Deggendorf Opel', 2: 'Deggendorf Hyundai', 3: 'Landau'}

# USt für Berechnung Netto → Brutto (1%-Regel bemisst sich am Bruttolistenpreis)
UST_FAKTOR = 1.19


def fetch_vfw_pruefungszeitraum():
    """
    Holt aus Locosoft alle VFW im Prüfungszeitraum 01.2022–12.2025 mit > 1.000 km.

    - Kommissionsnummer nur V oder G (T ausgeschlossen).
    - Zeitraum: Ankunft bis 31.12.2025, Abmeldung frühestens 01.01.2022.
    - Kilometer: COALESCE(vehicles.mileage_km, dealer_vehicles.mileage_km) > 1000.
    """
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT
                dv.dealer_vehicle_number,
                dv.dealer_vehicle_type    AS kom_nr,
                dv.pre_owned_car_code     AS jahreswagenkz,
                dv.in_subsidiary          AS standort,
                dv.in_arrival_date        AS eingang,
                dv.deregistration_date    AS abmeldung,
                dv.out_invoice_date       AS verkauft_am,
                dv.mileage_km             AS km_dv,
                dv.in_buy_list_price      AS listenpreis_netto,
                dv.out_recommended_retail_price AS empf_vk_preis,
                dv.calc_basic_charge      AS calc_grundpreis,
                dv.calc_accessory         AS calc_zubehoer,
                mod.suggested_net_retail_price  AS modell_netto_preis,
                v.license_plate           AS kennzeichen,
                v.vin                     AS vin,
                v.free_form_make_text     AS marke_frei,
                v.free_form_model_text    AS modell_frei,
                v.first_registration_date AS ez,
                v.mileage_km              AS km_v,
                v.make_number,
                v.model_code,
                m.description            AS marke,
                mod.description          AS modell,
                mod.is_plugin_hybride     AS is_plugin_hybrid,
                (
                    SELECT string_agg(DISTINCT f.description, ', ' ORDER BY f.description)
                    FROM model_to_fuels mtf
                    JOIN fuels f ON mtf.code = f.code
                    WHERE mtf.make_number = v.make_number
                      AND mtf.model_code = v.model_code
                ) AS antriebsart
            FROM dealer_vehicles dv
            LEFT JOIN vehicles v
                ON dv.dealer_vehicle_number = v.dealer_vehicle_number
                AND dv.dealer_vehicle_type = v.dealer_vehicle_type
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN models mod
                ON v.make_number = mod.make_number AND v.model_code = mod.model_code
            WHERE dv.dealer_vehicle_type IN %s
              AND dv.in_arrival_date IS NOT NULL
              AND dv.in_arrival_date <= '2025-12-31'
              AND (dv.deregistration_date IS NULL OR dv.deregistration_date >= '2022-01-01')
              AND COALESCE(v.mileage_km, dv.mileage_km, 0) > 1000
            ORDER BY dv.in_subsidiary, dv.in_arrival_date, dv.dealer_vehicle_number
        """
        cursor.execute(query, (VFW_KOMM_NR,))
        rows = cursor.fetchall()
    return [dict(r) for r in rows]


def upe_brutto_and_1pct(row):
    """
    Ermittelt UPE brutto (für 1%-Regel) aus Locosoft-Werten.
    Priorität: empf.VK → Listenpreis Netto×1,19 → Modell Netto×1,19 → (calc_basic_charge + calc_accessory)×1,19.
    Returns (upe_brutto, 1_pct_monat, satz_verwendet, quelle).
    """
    empf_vk = row.get('empf_vk_preis')
    netto_dv = row.get('listenpreis_netto')
    netto_mod = row.get('modell_netto_preis')
    calc_grund = row.get('calc_grundpreis')
    calc_zubehoer = row.get('calc_zubehoer')
    is_e = is_elektro_or_hybrid(row)
    upe_brutto = None
    quelle = None
    if empf_vk is not None and float(empf_vk) > 0:
        upe_brutto = float(empf_vk)
        quelle = 'empf.VK'
    elif netto_dv is not None and float(netto_dv) > 0:
        upe_brutto = float(netto_dv) * UST_FAKTOR
        quelle = 'Listenpreis Netto×1,19'
    elif netto_mod is not None and float(netto_mod) > 0:
        upe_brutto = float(netto_mod) * UST_FAKTOR
        quelle = 'Modell Netto×1,19'
    elif calc_grund is not None and calc_zubehoer is not None:
        grund = float(calc_grund)
        zub = float(calc_zubehoer)
        if (grund + zub) > 0:
            # Bewertungs-VK-Bestandteile (oft Netto) → Brutto
            upe_brutto = round((grund + zub) * UST_FAKTOR, 2)
            quelle = 'Grund+Zubehör×1,19'
    if upe_brutto is None or upe_brutto <= 0:
        return None, None, None, (quelle or None)
    # 1%-Regel: 1 % von UPE brutto pro Monat; E/Hybrid: 0,5 % oder 0,25 % (vereinfacht 0,5 %)
    satz = 0.005 if is_e else 0.01
    pct_monat = round(upe_brutto * satz, 2)
    return round(upe_brutto, 2), pct_monat, satz, quelle


def is_elektro_or_hybrid(row):
    """Prüft anhand Antriebsart und Modell-Flag ob 0,5 % / 0,25 % gilt."""
    antrieb = (row.get('antriebsart') or '') + (row.get('modell') or '') + (row.get('modell_frei') or '')
    antrieb_lower = antrieb.lower()
    if row.get('is_plugin_hybrid'):
        return True
    if any(x in antrieb_lower for x in (
        'elektro', 'electric', 'ev', 'e-motion', 'battery', 'bev', 'strom',
        'hybrid', 'plug-in', 'plugin', 'phev',
        'corsa-e', 'mokka-e', 'astra-e', 'zafira life-e', 'combo-e', 'vivaro-e'
    )):
        return True
    return False


def run(csv_path=None):
    rows = fetch_vfw_pruefungszeitraum()

    # Anreicherung für Ausgabe (UPE brutto + 1%-Wert)
    for r in rows:
        r['km'] = r.get('km_v') or r.get('km_dv') or 0
        r['standort_name'] = STANDORT_NAMEN.get(r.get('standort'), str(r.get('standort') or ''))
        r['versteuerung_hinweis'] = '0,5 % / 0,25 % (E/Hybrid)' if is_elektro_or_hybrid(r) else '1 %'
        upe_b, pct_monat, satz, quelle = upe_brutto_and_1pct(r)
        r['upe_brutto'] = upe_b
        r['geldwert_vorteil_monat'] = pct_monat  # 1 % bzw. 0,5 % von UPE brutto
        r['upe_quelle'] = quelle
        # VFW-Status: Unverkauft (Kom.Nr. T/V) vs. Verkauft (Jahreswagenkz. X)
        jkz = (r.get('jahreswagenkz') or '').strip().upper()
        r['vfw_status'] = 'Verkauft (Jahreswg.Kz. X)' if jkz == 'X' else f"Kom.Nr. {r.get('kom_nr') or '-'}"

    # Konsolenausgabe
    if not rows:
        print('Keine Vorführwagen 2023/2024 mit > 1.000 km gefunden.')
        return

    # Kurz-Statistik UPE
    with_upe = [r for r in rows if r.get('upe_brutto')]
    avg_upe = round(sum(r['upe_brutto'] for r in with_upe) / len(with_upe), 0) if with_upe else None
    avg_1pct = round(sum(r['geldwert_vorteil_monat'] for r in with_upe) / len(with_upe), 2) if with_upe else None
    print(f"Vorführwagen Prüfungszeitraum 01.2022–12.2025, > 1.000 km: {len(rows)} Fahrzeuge (Kom.Nr. nur V oder G)")
    if with_upe:
        print(f"UPE brutto: {len(with_upe)} mit Wert; Durchschnitt UPE brutto: {avg_upe:,.0f} € → Ø geldwerter Vorteil/Monat: {avg_1pct:,.2f} €")
    print()
    print('Standort      | Kz       | Kom.Nr. | UPE brutto  | 1%%/Monat | Status              | Marke/Modell     | EZ       | km     | Versteuerung')
    print('-' * 145)
    for r in rows:
        kennz = (r.get('kennzeichen') or '').strip()[:9]
        kom_nr = r.get('kom_nr') or '-'
        upe_s = f"{r.get('upe_brutto'):,.0f} €" if r.get('upe_brutto') else "-"
        pct_s = f"{r.get('geldwert_vorteil_monat'):,.2f} €" if r.get('geldwert_vorteil_monat') else "-"
        status = (r.get('vfw_status') or '-')[:21]
        marke_modell = f"{r.get('marke') or r.get('marke_frei') or '-'} / {r.get('modell') or r.get('modell_frei') or '-'}"[:18]
        ez = (r.get('ez') or '') if r.get('ez') else '-'
        if hasattr(ez, 'strftime'):
            ez = ez.strftime('%Y-%m-%d')
        hinweis = r.get('versteuerung_hinweis', '')
        print(f"{r.get('standort_name', ''):14} | {kennz:9} | {kom_nr:7} | {upe_s:11} | {pct_s:8} | {status:21} | {marke_modell:18} | {ez:10} | {r.get('km', 0):>6} | {hinweis}")

    # Optional CSV (Hinweis: in_buy_list_price = Netto – für 1 %-Regel Bruttolistenpreis ggf. manuell ergänzen)
    if csv_path:
        out_rows = []
        for r in rows:
            ez = r.get('ez')
            if hasattr(ez, 'strftime'):
                ez = ez.strftime('%Y-%m-%d') if ez else ''
            out_rows.append({
                'standort_name': r.get('standort_name'),
                'standort': r.get('standort'),
                'dealer_vehicle_number': r.get('dealer_vehicle_number'),
                'kom_nr': r.get('kom_nr'),
                'jahreswagenkz': r.get('jahreswagenkz'),
                'vfw_status': r.get('vfw_status'),
                'kennzeichen': r.get('kennzeichen'),
                'vin': r.get('vin'),
                'marke': r.get('marke') or r.get('marke_frei'),
                'modell': r.get('modell') or r.get('modell_frei'),
                'ez': ez,
                'km': r.get('km'),
                'antriebsart': r.get('antriebsart'),
                'versteuerung_hinweis': r.get('versteuerung_hinweis'),
                'listenpreis_netto': r.get('listenpreis_netto'),
                'empf_vk_preis': r.get('empf_vk_preis'),
                'modell_netto_preis': r.get('modell_netto_preis'),
                'upe_brutto': r.get('upe_brutto'),
                'upe_quelle': r.get('upe_quelle'),
                'geldwert_vorteil_monat': r.get('geldwert_vorteil_monat'),
                'eingang': r.get('eingang').strftime('%Y-%m-%d') if r.get('eingang') and hasattr(r.get('eingang'), 'strftime') else '',
                'abmeldung': r.get('abmeldung').strftime('%Y-%m-%d') if r.get('abmeldung') and hasattr(r.get('abmeldung'), 'strftime') else '',
                'verkauft_am': r.get('verkauft_am').strftime('%Y-%m-%d') if r.get('verkauft_am') and hasattr(r.get('verkauft_am'), 'strftime') else '',
            })
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=out_rows[0].keys())
            writer.writeheader()
            writer.writerows(out_rows)
        print(f'\nCSV gespeichert: {csv_path}')


def main():
    p = argparse.ArgumentParser(description='VFW 2023/2024 >1000 km + Antriebsart für Lohnsteuerprüfung')
    p.add_argument('--csv', type=str, help='CSV-Datei zum Speichern der Liste')
    args = p.parse_args()
    run(csv_path=args.csv)


if __name__ == '__main__':
    main()
