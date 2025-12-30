#!/usr/bin/env python3
"""
TEK API Helper - Nutzt wiederverwendbares TEK-Datenmodul
TAG146: Saubere Lösung mit zentralem Datenmodul

Garantiert 100% Konsistenz zwischen Web-UI und E-Mail-Reports!
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from datetime import date
from api.controlling_data import get_tek_data  # Wiederverwendbares Datenmodul!

# Monatsnamen
MONATE = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']


def get_tek_data_from_api(monat=None, jahr=None, standort=None):
    """
    Holt TEK-Daten über das wiederverwendbare controlling_data Modul

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

    # Datenfunktion aufrufen (aus controlling_data.py)
    try:
        api_data = get_tek_data(
            monat=monat,
            jahr=jahr,
            firma=firma,
            standort=standort_param,
            modus='teil',   # Teilkosten/DB1
            umlage='mit'    # Mit Umlage
        )
    except Exception as e:
        print(f"❌ TEK Datenfehler: {e}")
        raise

    # Daten in PDF-Format umwandeln (minimal - die meiste Arbeit macht controlling_data!)
    bereiche = []
    for b in api_data.get('bereiche', []):
        bereiche.append({
            'bereich': b.get('id', ''),           # '1-NW', '2-GW', etc.
            'umsatz': float(b.get('umsatz', 0)),
            'einsatz': float(b.get('einsatz', 0)),
            'db1': float(b.get('db1', 0)),
            'marge': float(b.get('marge', 0))
        })

    gesamt = api_data.get('gesamt', {})
    vm = api_data.get('vm', {})      # Vormonat
    vj = api_data.get('vj', {})      # Vorjahr

    return {
        'datum': heute.strftime('%d.%m.%Y'),
        'monat': f"{MONATE[monat]} {jahr}",
        'standort': standort,
        'standort_name': standort_name,
        'gesamt': {
            'db1': float(gesamt.get('db1', 0)),
            'marge': float(gesamt.get('marge', 0)),
            'prognose': float(gesamt.get('prognose', 0)),
            'breakeven': float(gesamt.get('breakeven', 0)),
            'breakeven_abstand': float(gesamt.get('breakeven_diff', 0))
        },
        'bereiche': bereiche,
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
