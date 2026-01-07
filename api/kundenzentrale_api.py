#!/usr/bin/env python3
"""
API: Kundenzentrale Tagesziel
==============================
Tägliches Fakturierungsziel für Kundenzentrale (alle externen Rechnungen)

Endpoints:
- GET /api/kundenzentrale/tagesziel - Tägliche IST vs SOLL

Datenquellen:
- Locosoft PostgreSQL: invoices (alle externen Rechnungen)
- Unternehmensplan: 1%-Ziel für Gesamtumsatz

TAG 164: Initiale Implementierung
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from api.db_utils import row_to_dict
from api.unternehmensplan_data import get_gap_analyse, get_current_geschaeftsjahr
from api.serviceberater_api import get_werktage_monat
from api.standort_utils import get_standort_config
from api.serviceberater_data import KundenzentraleData

kundenzentrale_api = Blueprint('kundenzentrale_api', __name__, url_prefix='/api/kundenzentrale')


@kundenzentrale_api.route('/tagesziel', methods=['GET'])
def tagesziel():
    """
    Tägliches Fakturierungsziel für Kundenzentrale (TAG 164)
    
    Query-Parameter:
    - datum: YYYY-MM-DD (default: heute)
    - standort: 'alle', 'deggendorf', 'landau' (default: alle)
    """
    datum_param = request.args.get('datum', date.today().isoformat())
    standort = request.args.get('standort', 'alle')
    
    # Standort validieren (zentralisiert)
    standort_config = get_standort_config(standort)
    subsidiaries = standort_config['subsidiaries']
    
    try:
        datum = datetime.strptime(datum_param, '%Y-%m-%d').date()
    except:
        datum = date.today()
    
    monat = datum.month
    jahr = datum.year
    geschaeftsjahr = get_current_geschaeftsjahr()
    
    # Werktage-Berechnung
    werktage = get_werktage_monat(jahr, monat)
    
    # 1. Gesamtumsatz-Ziel - PRIORITÄT: Summe aller KST-Ziele > 1%-Ziel
    from api.db_utils import db_session
    
    gesamtumsatz_ziel_monat = None
    quelle = '1%-Ziel'
    
    # TAG 164: Prüfe KST-Ziele (Summe aller Bereiche)
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(umsatz_ziel) as gesamt_umsatz_ziel
                FROM kst_ziele
                WHERE geschaeftsjahr = %s
                  AND monat = %s
                  AND standort = 0
            """, (geschaeftsjahr, monat))
            row = cursor.fetchone()
            
            if row and row['gesamt_umsatz_ziel']:
                gesamtumsatz_ziel_monat = float(row['gesamt_umsatz_ziel'])
                quelle = 'KST-Ziele (Summe)'
    except Exception as e:
        print(f"Fehler beim Laden KST-Ziele: {e}")
    
    # Fallback: 1%-Ziel-Ableitung
    if gesamtumsatz_ziel_monat is None or gesamtumsatz_ziel_monat == 0:
        gap_analyse = get_gap_analyse(geschaeftsjahr, standort=0)
        gesamtumsatz_ziel_jahr = gap_analyse.get('prognose_jahresende', {}).get('umsatz', 0)
        
        # Fallback: Wenn keine Prognose, nutze IST × 1,01
        if gesamtumsatz_ziel_jahr == 0:
            from api.unternehmensplan_data import get_ist_daten
            ist_daten = get_ist_daten(geschaeftsjahr, standort=0, nur_abgeschlossene=False)
            gesamtumsatz_ist = ist_daten.get('gesamt', {}).get('umsatz', 0)
            gesamtumsatz_ziel_jahr = gesamtumsatz_ist * 1.01
        
        gesamtumsatz_ziel_monat = gesamtumsatz_ziel_jahr / 12
    
    tagesziel_umsatz = gesamtumsatz_ziel_monat / werktage['gesamt'] if werktage['gesamt'] > 0 else 0
    
    try:
        # IST heute (aus Datenmodul - SSOT)
        fakt_heute = KundenzentraleData.get_fakturierung_heute(datum, subsidiaries if len(subsidiaries) < 3 else None)
        umsatz_heute = fakt_heute['umsatz_gesamt']
        
        # IST Monat (aus Datenmodul - SSOT)
        fakt_monat = KundenzentraleData.get_fakturierung_monat(monat, jahr, subsidiaries if len(subsidiaries) < 3 else None)
        umsatz_monat = fakt_monat['umsatz_gesamt']
        
        # Erfüllung
        erfuellung_heute = (umsatz_heute / tagesziel_umsatz * 100) if tagesziel_umsatz > 0 else 0
        erfuellung_monat = (umsatz_monat / gesamtumsatz_ziel_monat * 100) if gesamtumsatz_ziel_monat > 0 else 0
        zeitfortschritt = werktage['fortschritt_prozent']
        
        # Status
        if erfuellung_heute >= 100:
            status_heute = 'ok'
            nachricht = f"Ihr habt heute {umsatz_heute:,.0f} EUR fakturiert - Ziel erreicht ✅"
        elif erfuellung_heute >= 80:
            status_heute = 'warnung'
            fehlt = tagesziel_umsatz - umsatz_heute
            nachricht = f"Ihr habt heute {umsatz_heute:,.0f} EUR fakturiert - Noch {fehlt:,.0f} EUR fehlen"
        else:
            status_heute = 'kritisch'
            fehlt = tagesziel_umsatz - umsatz_heute
            nachricht = f"Ihr habt heute {umsatz_heute:,.0f} EUR fakturiert - Noch {fehlt:,.0f} EUR fehlen"
        
        return jsonify({
            'success': True,
            'datum': datum.isoformat(),
            'standort': standort,
            'standort_name': standort_config['name'],
            'ziele': {
                'tagesziel_umsatz': round(tagesziel_umsatz, 2),
                'monatsziel_umsatz': round(gesamtumsatz_ziel_monat, 2),
                'werktage_gesamt': werktage['gesamt'],
                'werktage_vergangen': werktage['vergangen'],
                'werktage_verbleibend': werktage['verbleibend']
            },
            'ist': {
                'umsatz_heute': fakt_heute['umsatz_gesamt'],
                'anzahl_rechnungen_heute': fakt_heute['anzahl_rechnungen'],
                'umsatz_monat': fakt_monat['umsatz_gesamt'],
                'anzahl_rechnungen_monat': fakt_monat['anzahl_rechnungen']
            },
            'erfuellung': {
                'heute_prozent': round(erfuellung_heute, 1),
                'monat_prozent': round(erfuellung_monat, 1),
                'zeitfortschritt_prozent': round(zeitfortschritt, 1),
                'status': status_heute,
                'nachricht': nachricht
            },
            'aufschlüsselung': {
                'werkstatt': fakt_heute['umsatz_werkstatt'],
                'verkauf': fakt_heute['umsatz_verkauf'],
                'teile': fakt_heute['umsatz_teile'],
                'sonstiges': fakt_heute['umsatz_sonstiges']
            },
            'herkunft': {
                'quelle': quelle,
                'gesamtumsatz_ziel_monat': round(gesamtumsatz_ziel_monat, 2)
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@kundenzentrale_api.route('/health', methods=['GET'])
def health():
    """Health Check"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'version': '1.0.0',  # TAG 164
        'timestamp': datetime.now().isoformat(),
    })

