#!/usr/bin/env python3
"""
API: Teile-Preisvergleich
- Locosoft OEM-Preise (UPE + EK)
- Schäferbarthold Scraper
- Dello/Automega Scraper (optional, langsam)
"""

from flask import Blueprint, request, jsonify
from psycopg2.extras import RealDictCursor
import re
import sys
sys.path.append('/opt/greiner-portal/tools/scrapers')

# Zentrale DB-Utilities (TAG117)
from api.db_utils import get_locosoft_connection

teile_api = Blueprint('teile_api', __name__, url_prefix='/api/teile')

PARTS_TYPE_NAMES = {
    0: 'Opel', 5: 'Hyundai', 6: 'Hyundai Zubehör',
    10: 'Fremdteil', 60: 'Opel (AT)', 65: 'Hyundai (AT)'
}

def normalize_teilenummer(tnr):
    if not tnr:
        return None
    return re.sub(r'[^a-zA-Z0-9]', '', tnr.upper())

def get_ek_rabatt(cursor, rebate_code, parts_type):
    if not rebate_code:
        return 0
    cursor.execute("""
        SELECT rebate_percent FROM parts_rebate_codes_buy 
        WHERE rebate_code = %s AND parts_type_boundary_from <= %s AND parts_type_boundary_until >= %s
        LIMIT 1
    """, (rebate_code, parts_type, parts_type))
    row = cursor.fetchone()
    return float(row['rebate_percent']) if row else 0


@teile_api.route('/vergleich/<teilenummer>', methods=['GET'])
def teile_vergleich(teilenummer):
    """Preisvergleich: Locosoft vs Schäferbarthold vs Dello (optional)
    
    Query-Parameter:
    - dello=true  -> Dello einbeziehen (langsam, ~15 Sek)
    - dello=false -> Nur Locosoft + Schäferbarthold (Standard)
    """
    include_dello = request.args.get('dello', 'false').lower() == 'true'
    
    result = {
        'success': True,
        'teilenummer': teilenummer,
        'quellen': {}
    }
    
    # 1. Locosoft OEM
    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        tnr_clean = normalize_teilenummer(teilenummer)
        
        cursor.execute("""
            SELECT part_number, description, rr_price, rebate_code, parts_type
            FROM parts_master 
            WHERE part_number = %s OR REPLACE(REPLACE(part_number, ' ', ''), '-', '') = %s
            LIMIT 1
        """, (teilenummer, tnr_clean))
        
        row = cursor.fetchone()
        if row:
            upe = float(row['rr_price']) if row['rr_price'] else None
            rabatt_prozent = get_ek_rabatt(cursor, row['rebate_code'], row['parts_type'])
            ek = round(upe * (1 - rabatt_prozent / 100), 2) if upe and rabatt_prozent else None
            
            result['quellen']['locosoft'] = {
                'name': 'Locosoft OEM',
                'teilenummer': row['part_number'],
                'beschreibung': row['description'],
                'upe': upe, 'ek': ek,
                'rabatt_code': row['rebate_code'],
                'rabatt_prozent': rabatt_prozent,
                'preis': ek if ek else upe,
                'marke': PARTS_TYPE_NAMES.get(row['parts_type'], 'Unbekannt')
            }
        cursor.close()
        conn.close()
    except Exception as e:
        result['quellen']['locosoft'] = {'error': str(e)}
    
    # 2. Schäferbarthold
    try:
        from schaeferbarthold_scraper_v3 import SchaeferbartholdScraper
        scraper = SchaeferbartholdScraper()
        sb_result = scraper.search(teilenummer)
        scraper.close()
        
        if sb_result['success'] and sb_result['ergebnisse']:
            sb = sb_result['ergebnisse'][0]
            result['quellen']['schaeferbarthold'] = {
                'name': 'Schäferbarthold',
                'teilenummer': sb['teilenummer'],
                'beschreibung': sb.get('kategorie'),
                'upe': sb.get('bruttopreis'),
                'ek': sb.get('einkaufspreis'),
                'rabatt_prozent': sb.get('rabatt_prozent'),
                'preis': sb.get('einkaufspreis'),
                'verfuegbar': sb.get('verfuegbar')
            }
    except Exception as e:
        result['quellen']['schaeferbarthold'] = {'error': str(e)}
    
    # 3. Dello (nur wenn explizit angefordert)
    if include_dello:
        try:
            from dello_scraper import DelloScraper
            dello = DelloScraper()
            dello_result = dello.get_price(teilenummer)
            dello.close()
            
            if dello_result['success'] and dello_result['ergebnisse']:
                ergebnisse = [e for e in dello_result['ergebnisse'] if e.get('ek')]
                if ergebnisse:
                    best = min(ergebnisse, key=lambda x: x['ek'])
                    result['quellen']['dello'] = {
                        'name': 'Dello/Automega',
                        'teilenummer': best['artikel_nr'],
                        'beschreibung': best.get('bezeichnung'),
                        'upe': best.get('upe'),
                        'ek': best.get('ek'),
                        'preis': best.get('ek'),
                        'alle_ergebnisse': len(dello_result['ergebnisse'])
                    }
        except Exception as e:
            result['quellen']['dello'] = {'error': str(e)}
    
    # 4. Empfehlung
    preise = []
    for quelle, daten in result['quellen'].items():
        if 'preis' in daten and daten['preis']:
            preise.append({'quelle': daten.get('name', quelle), 'preis': daten['preis']})
    
    if preise:
        preise_sorted = sorted(preise, key=lambda x: x['preis'])
        result['empfehlung'] = {'guenstigster': preise_sorted[0]['quelle'], 'preis': preise_sorted[0]['preis']}
        if len(preise) > 1:
            ersparnis = preise_sorted[-1]['preis'] - preise_sorted[0]['preis']
            result['empfehlung']['ersparnis'] = round(ersparnis, 2)
            result['empfehlung']['ersparnis_prozent'] = round((ersparnis / preise_sorted[-1]['preis']) * 100, 1)
    
    return jsonify(result)


@teile_api.route('/preis/<teilenummer>', methods=['GET'])
def teile_preis(teilenummer):
    """Nur Locosoft OEM-Preis (schnell)"""
    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        tnr_clean = normalize_teilenummer(teilenummer)
        
        cursor.execute("""
            SELECT part_number, description, rr_price, rebate_code, parts_type
            FROM parts_master 
            WHERE part_number = %s OR REPLACE(REPLACE(part_number, ' ', ''), '-', '') = %s
            LIMIT 1
        """, (teilenummer, tnr_clean))
        
        row = cursor.fetchone()
        if row:
            upe = float(row['rr_price']) if row['rr_price'] else None
            rabatt_prozent = get_ek_rabatt(cursor, row['rebate_code'], row['parts_type'])
            ek = round(upe * (1 - rabatt_prozent / 100), 2) if upe and rabatt_prozent else None
            cursor.close()
            conn.close()
            return jsonify({
                'success': True, 'teilenummer': row['part_number'],
                'beschreibung': row['description'], 'upe': upe, 'ek': ek,
                'rabatt_code': row['rebate_code'], 'rabatt_prozent': rabatt_prozent,
                'marke': PARTS_TYPE_NAMES.get(row['parts_type'], 'Unbekannt')
            })
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': 'Nicht gefunden'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@teile_api.route('/health', methods=['GET'])
def health():
    return jsonify({'success': True, 'status': 'healthy'})
