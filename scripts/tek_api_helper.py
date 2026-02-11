#!/usr/bin/env python3
"""
TEK API Helper - Nutzt die /api/tek API direkt
TAG 215: 100% Konsistenz mit DRIVE Online-Version!

Garantiert identische Daten zwischen Web-UI und E-Mail-Reports!
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from datetime import date, timedelta
import requests

# Monatsnamen
MONATE = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']


def get_tek_data_from_api(monat=None, jahr=None, standort=None):
    """
    Holt TEK-Daten direkt über die /api/tek API (wie DRIVE Online-Version)
    
    TAG 215: Nutzt die gleiche API wie die Web-UI → 100% identische Daten!

    Args:
        monat: Monat (1-12), default: aktueller Monat
        jahr: Jahr (YYYY), default: aktuelles Jahr
        standort: None/'ALL'=Alle, 'DEG'=Deggendorf, 'LAN'=Landau

    Returns:
        dict mit Keys: datum, monat, standort, standort_name, gesamt, bereiche, vormonat, vorjahr
    """
    heute = date.today()
    if not monat:
        monat = heute.month
    if not jahr:
        jahr = heute.year

    # Parameter (wie in DRIVE TEK-Seite)
    firma = '0'      # Alle (Standard)
    standort_param = '0'  # Alle (Standard)

    # Standort-Mapping für Filiale-Reports
    standort_name = "Gesamt"
    if standort == 'DEG':
        firma = '1'            # Stellantis
        standort_param = '1'   # Deggendorf
        standort_name = "Deggendorf"
    elif standort == 'LAN':
        firma = '1'            # Stellantis
        standort_param = '2'   # Landau
        standort_name = "Landau"

    # TAG 215: Nutze die gleiche Logik wie /api/tek direkt (ohne HTTP/Auth)
    # Extrahiere die Kernlogik aus api_tek() für interne Nutzung
    try:
        # Importiere die benötigten Funktionen
        from routes.controlling_routes import get_stueckzahlen_locosoft, get_werkstatt_produktivitaet
        from api.controlling_data import get_tek_data as get_tek_data_core
        from api.db_utils import locosoft_session
        import psycopg2.extras
        from datetime import timedelta
        
        # Hole die Daten über controlling_data (wie api_tek es macht)
        api_data = get_tek_data_core(
            monat=monat,
            jahr=jahr,
            firma=firma,
            standort=standort_param,
            modus='teil',
            umlage='mit'
        )
        
        # Stückzahlen holen (wie api_tek Zeile 1038-1061)
        von = f"{jahr}-{monat:02d}-01"
        bis = f"{jahr}-{monat+1:02d}-01" if monat < 12 else f"{jahr+1}-01-01"
        
        stueck_nw = get_stueckzahlen_locosoft(von, bis, '1-NW', firma, standort_param)
        stueck_gw = get_stueckzahlen_locosoft(von, bis, '2-GW', firma, standort_param)
        
        # Stückzahlen zu Bereichen hinzufügen (wie api_tek Zeile 1049-1068)
        bereiche_dict = {}
        for b in api_data.get('bereiche', []):
            bkey = b.get('id', '')
            bereiche_dict[bkey] = {
                'umsatz': float(b.get('umsatz', 0)),
                'einsatz': float(b.get('einsatz', 0)),
                'db1': float(b.get('db1', 0)),
                'marge': float(b.get('marge', 0)),
                'stueck': 0,
                'heute_umsatz': 0,
                'heute_db1': 0,
                'heute_einsatz': 0,
                'hinweis': b.get('hinweis'),  # TAG 219: 4-Lohn kalk. Einsatz-Hinweis
                'produktivitaet': b.get('produktivitaet'),
                'leistungsgrad': b.get('leistungsgrad'),
                'einsatz_kalk': b.get('einsatz_kalk'),
                'db1_kalk': b.get('db1_kalk'),
                'marge_kalk': b.get('marge_kalk'),
            }
            
            # Stückzahlen zuordnen
            if bkey == '1-NW':
                bereiche_dict[bkey]['stueck'] = stueck_nw.get('gesamt_stueck', 0)
                if bereiche_dict[bkey]['stueck'] > 0:
                    bereiche_dict[bkey]['db1_pro_stueck'] = round(bereiche_dict[bkey]['db1'] / bereiche_dict[bkey]['stueck'], 2)
            elif bkey == '2-GW':
                bereiche_dict[bkey]['stueck'] = stueck_gw.get('gesamt_stueck', 0)
                if bereiche_dict[bkey]['stueck'] > 0:
                    bereiche_dict[bkey]['db1_pro_stueck'] = round(bereiche_dict[bkey]['db1'] / bereiche_dict[bkey]['stueck'], 2)
        
        # Werkstatt-KPIs aus DRIVE (werkstatt_leistung_daily) – controlling_data setzt sie nicht, nur die Route
        if '4-Lohn' in bereiche_dict:
            betrieb = firma if firma in ('1', '2') else '0'
            try:
                ws_kpi = get_werkstatt_produktivitaet(von, bis, betrieb)
                bereiche_dict['4-Lohn']['produktivitaet'] = ws_kpi.get('produktivitaet')
                bereiche_dict['4-Lohn']['leistungsgrad'] = ws_kpi.get('leistungsgrad')
            except Exception:
                pass
        
        # Heute-Daten holen (wie api_tek Zeile 1406-1597)
        heute = date.today()
        heute_bereiche = {}
        if heute.year == jahr and heute.month == monat:
            heute_str = heute.isoformat()
            morgen_str = (heute + timedelta(days=1)).isoformat()
            
            # Firma-Filter
            firma_filter_umsatz = ""
            firma_filter_einsatz = ""
            if firma == '1':
                firma_filter_umsatz = "AND subsidiary_to_company_ref = 1"
                firma_filter_einsatz = "AND subsidiary_to_company_ref = 1"
                if standort_param == '1':
                    firma_filter_umsatz += " AND branch_number = 1"
                    firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
                elif standort_param == '2':
                    firma_filter_umsatz += " AND branch_number = 3"
                    firma_filter_einsatz += " AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
            elif firma == '2':
                firma_filter_umsatz = "AND subsidiary_to_company_ref = 2"
                firma_filter_einsatz = "AND subsidiary_to_company_ref = 2"
            
            with locosoft_session() as loco_conn:
                loco_cur = loco_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Tagesumsatz PRO BEREICH (Heute)
                loco_cur.execute(f"""
                    SELECT
                        CASE
                            WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN '1-NW'
                            WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN '2-GW'
                            WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN '3-Teile'
                            WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN '4-Lohn'
                            WHEN nominal_account_number BETWEEN 860000 AND 869999 THEN '5-Sonst'
                            ELSE '9-Andere'
                        END as bereich,
                        COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0, 0) as umsatz
                    FROM journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 800000 AND 899999
                      {firma_filter_umsatz if firma_filter_umsatz else ''}
                    GROUP BY bereich
                """, (heute_str, morgen_str))
                heute_umsatz_bereich = {r['bereich']: float(r['umsatz'] or 0) for r in loco_cur.fetchall()}
                
                # Tageseinsatz PRO BEREICH (Heute)
                loco_cur.execute(f"""
                    SELECT
                        CASE
                            WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN '1-NW'
                            WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN '2-GW'
                            WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN '3-Teile'
                            WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN '4-Lohn'
                            WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN '5-Sonst'
                            ELSE '9-Andere'
                        END as bereich,
                        COALESCE(SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0, 0) as einsatz
                    FROM journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND nominal_account_number BETWEEN 700000 AND 799999
                      {firma_filter_einsatz if firma_filter_einsatz else ''}
                    GROUP BY bereich
                """, (heute_str, morgen_str))
                heute_einsatz_bereich = {r['bereich']: float(r['einsatz'] or 0) for r in loco_cur.fetchall()}
                
                # Pro Bereich zusammenführen (Heute)
                for bkey in ['1-NW', '2-GW', '3-Teile', '4-Lohn', '5-Sonst']:
                    h_umsatz = heute_umsatz_bereich.get(bkey, 0)
                    h_einsatz = heute_einsatz_bereich.get(bkey, 0)
                    heute_bereiche[bkey] = {
                        'umsatz': round(h_umsatz, 2),
                        'einsatz': round(h_einsatz, 2),
                        'db1': round(h_umsatz - h_einsatz, 2)
                    }
                
                # Heute-Stückzahlen
                heute_stueck_nw = get_stueckzahlen_locosoft(heute_str, morgen_str, '1-NW', firma, standort_param)
                heute_stueck_gw = get_stueckzahlen_locosoft(heute_str, morgen_str, '2-GW', firma, standort_param)
                
                # Heute-Daten zu Bereichen hinzufügen
                for bkey in bereiche_dict:
                    if bkey in heute_bereiche:
                        bereiche_dict[bkey]['heute_umsatz'] = heute_bereiche[bkey]['umsatz']
                        bereiche_dict[bkey]['heute_einsatz'] = heute_bereiche[bkey]['einsatz']
                        bereiche_dict[bkey]['heute_db1'] = heute_bereiche[bkey]['db1']
                    if bkey == '1-NW':
                        bereiche_dict[bkey]['heute_stueck'] = heute_stueck_nw.get('gesamt_stueck', 0)
                    elif bkey == '2-GW':
                        bereiche_dict[bkey]['heute_stueck'] = heute_stueck_gw.get('gesamt_stueck', 0)
            
    except Exception as e:
        print(f"❌ TEK Datenfehler: {e}")
        import traceback
        traceback.print_exc()
        raise

    # Daten aus bereiche_dict extrahieren (identisch mit Online-Version!)
    bereiche_liste = []
    for bkey, b in bereiche_dict.items():
        bereiche_liste.append({
            'bereich': bkey,
            'umsatz': float(b.get('umsatz', 0)),
            'einsatz': float(b.get('einsatz', 0)),
            'db1': float(b.get('db1', 0)),
            'marge': float(b.get('marge', 0)),
            'stueck': int(b.get('stueck', 0)),  # TAG 215: Aus get_stueckzahlen_locosoft (wie Online-Version!)
            'heute_umsatz': float(b.get('heute_umsatz', 0)),  # TAG 215: Heute-Daten
            'heute_db1': float(b.get('heute_db1', 0)),
            'heute_einsatz': float(b.get('heute_einsatz', 0)),
            'heute_stueck': int(b.get('heute_stueck', 0)),  # TAG 215: Heute-Stückzahlen
            'db1_pro_stueck': float(b.get('db1_pro_stueck', 0)),
            'hinweis': b.get('hinweis'),  # TAG 219: 4-Lohn kalk. Einsatz
            'produktivitaet': b.get('produktivitaet'),
            'leistungsgrad': b.get('leistungsgrad'),
            'einsatz_kalk': b.get('einsatz_kalk'),
            'db1_kalk': b.get('db1_kalk'),
            'marge_kalk': b.get('marge_kalk'),
        })

    gesamt = api_data.get('gesamt', {})
    vm = api_data.get('vm', {})  # TAG 215: controlling_data.py nutzt 'vm' nicht 'vormonat'
    vj = api_data.get('vj', {})  # TAG 215: controlling_data.py nutzt 'vj' nicht 'vorjahr'
    heute_daten = api_data.get('heute', {})

    # Datum aus heute_daten oder aktuelles Datum
    datum_str = heute_daten.get('datum_formatiert', heute.strftime('%d.%m.%Y')) if heute_daten else heute.strftime('%d.%m.%Y')
    if '.' not in datum_str:
        # Format: "YYYY-MM-DD" -> "DD.MM.YYYY"
        try:
            from datetime import datetime
            datum_obj = datetime.strptime(datum_str, '%Y-%m-%d')
            datum_str = datum_obj.strftime('%d.%m.%Y')
        except:
            datum_str = heute.strftime('%d.%m.%Y')

    return {
        'datum': datum_str,
        'monat': f"{MONATE[monat]} {jahr}",
        'standort': standort,
        'standort_name': standort_name,
        'firma': firma,  # TAG 215: Für Drill-Down APIs
        'standort_api': standort_param,  # TAG 215: Für Drill-Down APIs
        'monat_num': monat,  # TAG 215: Für Drill-Down APIs
        'jahr_num': jahr,  # TAG 215: Für Drill-Down APIs
        'gesamt': {
            'umsatz': float(gesamt.get('umsatz', 0)),
            'einsatz': float(gesamt.get('einsatz', 0)),
            'db1': float(gesamt.get('db1', 0)),
            'marge': float(gesamt.get('marge', 0)),
            'prognose': float(gesamt.get('prognose', 0)),
            'breakeven': float(gesamt.get('breakeven', 0)),
            'breakeven_abstand': float(gesamt.get('breakeven_diff', 0))
        },
        'bereiche': bereiche_liste,  # TAG 215: Jetzt mit stueck, heute_umsatz, heute_db1, heute_einsatz
        'vormonat': {
            'db1': float(vm.get('db1', 0)),
            'marge': float(vm.get('marge', 0))
        },
        'vorjahr': {
            'db1': float(vj.get('db1', 0)),
            'marge': float(vj.get('marge', 0))
        }
    }


if __name__ == '__main__':
    # Test
    print("Testing TEK API Helper...")
    data = get_tek_data_from_api()
    print(f"Gesamt DB1: {data['gesamt']['db1']:,.2f} €")
    print(f"Vormonat DB1: {data['vormonat']['db1']:,.2f} €")
    print(f"Vorjahr DB1: {data['vorjahr']['db1']:,.2f} €")
    print(f"Bereiche: {len(data['bereiche'])}")
    print("✅ OK!")
