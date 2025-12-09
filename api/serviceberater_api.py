#!/usr/bin/env python3
"""
API: Serviceberater Controlling
================================
TEK-basiertes Controlling für Serviceberater

Endpoints:
- GET /api/serviceberater/uebersicht - Alle SB mit Umsatz/Ziel
- GET /api/serviceberater/<ma_id> - Detail eines SB
- GET /api/serviceberater/wettbewerb - Aktiver Verkaufswettbewerb
- GET /api/serviceberater/tek-config - TEK-Konfiguration

Datenquellen:
- Locosoft PostgreSQL: invoices (Rechnungen)
- SQLite: employees (MA-Namen), tek_config
"""

from flask import Blueprint, request, jsonify
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import sqlite3

serviceberater_api = Blueprint('serviceberater_api', __name__, url_prefix='/api/serviceberater')

# ============================================================
# KONFIGURATION
# ============================================================

# TEK-Vollkosten After Sales (aus Screenshot Dezember 2025)
TEK_CONFIG = {
    'vollkosten_monat': 47174,  # Direkte + Umlage für Teile/Service + Werkstattlohn
    'teile_service_direkt': 3000,
    'teile_service_umlage': 7219,
    'werkstattlohn_direkt': 6000,
    'werkstattlohn_umlage': 30955,
    'marge_arbeit': 1.00,  # 100% Marge auf Arbeit (kein Wareneinsatz)
    'marge_teile': 0.544,  # 54,4% Marge auf Teile (aus TEK)
    'marge_gewichtet': 0.75,  # Gewichtete Durchschnittsmarge
}

# Serviceberater MA-IDs (aus Locosoft-Analyse)
# Die mit hohem Arbeitsumsatz sind echte SB
SERVICEBERATER_IDS = [1025, 1006, 1016, 1002, 1036, 1023, 1034, 1010]

# Aktiver Wettbewerb
AKTIVER_WETTBEWERB = {
    'name': 'Contrasept Dezember 2025',
    'produkt': 'CONTRASEPT',
    'suchbegriffe': ['contrasept', 'desinfektion', 'innenraum'],
    'start': '2025-12-01',
    'ende': '2025-12-31',
    'ziel_team': 150,
    'praemie_1': 100,
    'praemie_2': 50,
    'praemie_3': 25,
}


def get_locosoft_connection():
    """Locosoft PostgreSQL Verbindung"""
    with open('/opt/greiner-portal/config/credentials.json') as f:
        creds = json.load(f)['databases']['locosoft']
    return psycopg2.connect(
        host=creds['host'], port=creds['port'],
        database=creds['database'], user=creds['user'],
        password=creds['password']
    )


def get_sqlite_connection():
    """SQLite Verbindung für MA-Namen"""
    return sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')


def get_ma_namen():
    """Hole MA-Namen aus employees Tabelle"""
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT locosoft_id, display_name, title 
            FROM employees 
            WHERE locosoft_id IS NOT NULL
        """)
        namen = {row[0]: {'name': row[1], 'title': row[2]} for row in cursor.fetchall()}
        conn.close()
        return namen
    except:
        return {}


# ============================================================
# API ENDPOINTS
# ============================================================

@serviceberater_api.route('/uebersicht', methods=['GET'])
def uebersicht():
    """
    Übersicht aller Serviceberater mit Umsatz und Zielerreichung
    
    Query-Parameter:
    - monat: YYYY-MM (default: aktueller Monat)
    - filiale: 1, 2, 3 oder 'alle' (default: alle)
    """
    monat_param = request.args.get('monat', datetime.now().strftime('%Y-%m'))
    filiale = request.args.get('filiale', 'alle')
    
    try:
        jahr, monat = monat_param.split('-')
        start_datum = f"{jahr}-{monat}-01"
        # Letzter Tag des Monats
        if int(monat) == 12:
            ende_datum = f"{int(jahr)+1}-01-01"
        else:
            ende_datum = f"{jahr}-{int(monat)+1:02d}-01"
    except:
        return jsonify({'success': False, 'error': 'Ungültiges Datumsformat'}), 400
    
    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Filiale-Filter
        filiale_filter = ""
        if filiale != 'alle':
            filiale_filter = f"AND subsidiary = {int(filiale)}"
        
        # Serviceberater-Umsätze (nur Service-Rechnungen: Typ 2, 3, 6)
        cursor.execute(f"""
            SELECT 
                creating_employee as ma_id,
                COUNT(*) as anzahl_rechnungen,
                SUM(total_gross) as umsatz_gesamt,
                SUM(job_amount_gross) as umsatz_arbeit,
                SUM(part_amount_gross) as umsatz_teile,
                AVG(total_gross) as avg_rechnung
            FROM invoices
            WHERE invoice_date >= %s
              AND invoice_date < %s
              AND is_canceled = false
              AND total_gross > 0
              AND invoice_type IN (2, 3, 6)
              AND creating_employee IS NOT NULL
              {filiale_filter}
            GROUP BY creating_employee
            ORDER BY umsatz_gesamt DESC
        """, (start_datum, ende_datum))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # MA-Namen hinzufügen
        ma_namen = get_ma_namen()
        
        # Anzahl SB für Break-Even Berechnung
        anzahl_sb = len([r for r in rows if r['ma_id'] in SERVICEBERATER_IDS]) or len(SERVICEBERATER_IDS)
        vollkosten_pro_sb = TEK_CONFIG['vollkosten_monat'] / anzahl_sb
        break_even = vollkosten_pro_sb / TEK_CONFIG['marge_gewichtet']
        
        # Ergebnis aufbereiten
        serviceberater = []
        for row in rows:
            ma_id = row['ma_id']
            umsatz = float(row['umsatz_gesamt'] or 0)
            arbeit = float(row['umsatz_arbeit'] or 0)
            teile = float(row['umsatz_teile'] or 0)
            
            # Deckungsbeitrag berechnen
            db1 = (arbeit * TEK_CONFIG['marge_arbeit']) + (teile * TEK_CONFIG['marge_teile'])
            
            # Zielerreichung
            erreichung = (umsatz / break_even * 100) if break_even > 0 else 0
            
            # Status
            if erreichung >= 100:
                status = 'success'
            elif erreichung >= 80:
                status = 'warning'
            else:
                status = 'danger'
            
            ma_info = ma_namen.get(ma_id, {})
            
            serviceberater.append({
                'ma_id': ma_id,
                'name': ma_info.get('name', f'MA {ma_id}'),
                'title': ma_info.get('title', 'Serviceberater'),
                'ist_serviceberater': ma_id in SERVICEBERATER_IDS,
                'anzahl_rechnungen': row['anzahl_rechnungen'],
                'umsatz_gesamt': round(umsatz, 2),
                'umsatz_arbeit': round(arbeit, 2),
                'umsatz_teile': round(teile, 2),
                'avg_rechnung': round(float(row['avg_rechnung'] or 0), 2),
                'db1': round(db1, 2),
                'ziel': round(break_even, 2),
                'erreichung': round(erreichung, 1),
                'status': status,
            })
        
        # Tage im Monat für Hochrechnung
        heute = datetime.now()
        if monat_param == heute.strftime('%Y-%m'):
            tag_aktuell = heute.day
            tage_gesamt = 30 if int(monat) in [4, 6, 9, 11] else 31 if int(monat) != 2 else 28
            arbeitstage_aktuell = tag_aktuell * 5 / 7  # Grobe Schätzung
            arbeitstage_gesamt = tage_gesamt * 5 / 7
        else:
            arbeitstage_aktuell = arbeitstage_gesamt = 1  # Abgeschlossener Monat
        
        return jsonify({
            'success': True,
            'monat': monat_param,
            'filiale': filiale,
            'serviceberater': serviceberater,
            'config': {
                'vollkosten_monat': TEK_CONFIG['vollkosten_monat'],
                'vollkosten_pro_sb': round(vollkosten_pro_sb, 2),
                'break_even': round(break_even, 2),
                'anzahl_sb': anzahl_sb,
                'marge_arbeit': TEK_CONFIG['marge_arbeit'],
                'marge_teile': TEK_CONFIG['marge_teile'],
            },
            'zeitraum': {
                'start': start_datum,
                'ende': ende_datum,
                'arbeitstage_aktuell': round(arbeitstage_aktuell, 1),
                'arbeitstage_gesamt': round(arbeitstage_gesamt, 1),
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@serviceberater_api.route('/detail/<int:ma_id>', methods=['GET'])
def detail(ma_id):
    """
    Detail-Ansicht für einen Serviceberater
    
    Query-Parameter:
    - monat: YYYY-MM (default: aktueller Monat)
    """
    monat_param = request.args.get('monat', datetime.now().strftime('%Y-%m'))
    
    try:
        jahr, monat = monat_param.split('-')
        start_datum = f"{jahr}-{monat}-01"
        if int(monat) == 12:
            ende_datum = f"{int(jahr)+1}-01-01"
        else:
            ende_datum = f"{jahr}-{int(monat)+1:02d}-01"
    except:
        return jsonify({'success': False, 'error': 'Ungültiges Datumsformat'}), 400
    
    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Tägliche Umsätze
        cursor.execute("""
            SELECT 
                invoice_date as datum,
                COUNT(*) as anzahl,
                SUM(total_gross) as umsatz,
                SUM(job_amount_gross) as arbeit,
                SUM(part_amount_gross) as teile
            FROM invoices
            WHERE creating_employee = %s
              AND invoice_date >= %s
              AND invoice_date < %s
              AND is_canceled = false
              AND total_gross > 0
              AND invoice_type IN (2, 3, 6)
            GROUP BY invoice_date
            ORDER BY invoice_date
        """, (ma_id, start_datum, ende_datum))
        
        tage = []
        for row in cursor.fetchall():
            tage.append({
                'datum': row['datum'].strftime('%Y-%m-%d'),
                'anzahl': row['anzahl'],
                'umsatz': round(float(row['umsatz'] or 0), 2),
                'arbeit': round(float(row['arbeit'] or 0), 2),
                'teile': round(float(row['teile'] or 0), 2),
            })
        
        # Letzte 10 Rechnungen
        cursor.execute("""
            SELECT 
                invoice_type,
                invoice_number,
                invoice_date,
                total_gross,
                job_amount_gross,
                part_amount_gross,
                order_number
            FROM invoices
            WHERE creating_employee = %s
              AND invoice_date >= %s
              AND invoice_date < %s
              AND is_canceled = false
              AND invoice_type IN (2, 3, 6)
            ORDER BY invoice_date DESC, invoice_number DESC
            LIMIT 10
        """, (ma_id, start_datum, ende_datum))
        
        rechnungen = []
        typ_namen = {2: 'Werkstatt', 3: 'Reklamation', 6: 'Garantie'}
        for row in cursor.fetchall():
            rechnungen.append({
                'typ': typ_namen.get(row['invoice_type'], f'Typ {row["invoice_type"]}'),
                'nummer': f"{row['invoice_type']}-{row['invoice_number']}",
                'datum': row['invoice_date'].strftime('%d.%m.%Y'),
                'gesamt': round(float(row['total_gross'] or 0), 2),
                'arbeit': round(float(row['job_amount_gross'] or 0), 2),
                'teile': round(float(row['part_amount_gross'] or 0), 2),
                'auftrag': row['order_number'],
            })
        
        cursor.close()
        conn.close()
        
        # MA-Name
        ma_namen = get_ma_namen()
        ma_info = ma_namen.get(ma_id, {'name': f'MA {ma_id}', 'title': 'Serviceberater'})
        
        # Summen
        umsatz_gesamt = sum(t['umsatz'] for t in tage)
        arbeit_gesamt = sum(t['arbeit'] for t in tage)
        teile_gesamt = sum(t['teile'] for t in tage)
        anzahl_gesamt = sum(t['anzahl'] for t in tage)
        
        # Break-Even
        anzahl_sb = len(SERVICEBERATER_IDS)
        vollkosten_pro_sb = TEK_CONFIG['vollkosten_monat'] / anzahl_sb
        break_even = vollkosten_pro_sb / TEK_CONFIG['marge_gewichtet']
        erreichung = (umsatz_gesamt / break_even * 100) if break_even > 0 else 0
        
        return jsonify({
            'success': True,
            'ma_id': ma_id,
            'name': ma_info['name'],
            'title': ma_info['title'],
            'monat': monat_param,
            'zusammenfassung': {
                'anzahl_rechnungen': anzahl_gesamt,
                'umsatz_gesamt': round(umsatz_gesamt, 2),
                'umsatz_arbeit': round(arbeit_gesamt, 2),
                'umsatz_teile': round(teile_gesamt, 2),
                'avg_rechnung': round(umsatz_gesamt / anzahl_gesamt, 2) if anzahl_gesamt > 0 else 0,
                'ziel': round(break_even, 2),
                'erreichung': round(erreichung, 1),
            },
            'tage': tage,
            'rechnungen': rechnungen,
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@serviceberater_api.route('/wettbewerb', methods=['GET'])
def wettbewerb():
    """
    Aktueller Verkaufswettbewerb (z.B. Contrasept)
    
    Query-Parameter:
    - monat: YYYY-MM (default: aus Wettbewerb-Config)
    """
    monat_param = request.args.get('monat')
    
    # Wettbewerb-Zeitraum
    start_datum = AKTIVER_WETTBEWERB['start']
    ende_datum = AKTIVER_WETTBEWERB['ende']
    
    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # TODO: Hier müssten wir die Positionen der Rechnungen abfragen
        # um nach "Contrasept" zu filtern. Das erfordert Zugriff auf
        # eine positions-Tabelle in Locosoft (invoice_positions o.ä.)
        
        # Vorerst: Dummy-Daten als Platzhalter
        # In der echten Implementierung: Query auf positions-Tabelle
        
        cursor.close()
        conn.close()
        
        # Platzhalter-Ranking (wird später durch echte Daten ersetzt)
        ranking = [
            {'rang': 1, 'ma_id': 1025, 'name': 'Serviceberater 1', 'anzahl': 47, 'umsatz': 1410},
            {'rang': 2, 'ma_id': 1006, 'name': 'Serviceberater 2', 'anzahl': 42, 'umsatz': 1260},
            {'rang': 3, 'ma_id': 1016, 'name': 'Serviceberater 3', 'anzahl': 31, 'umsatz': 930},
        ]
        
        team_gesamt = sum(r['anzahl'] for r in ranking)
        
        return jsonify({
            'success': True,
            'wettbewerb': {
                'name': AKTIVER_WETTBEWERB['name'],
                'produkt': AKTIVER_WETTBEWERB['produkt'],
                'start': start_datum,
                'ende': ende_datum,
                'ziel_team': AKTIVER_WETTBEWERB['ziel_team'],
                'praemien': {
                    'platz_1': AKTIVER_WETTBEWERB['praemie_1'],
                    'platz_2': AKTIVER_WETTBEWERB['praemie_2'],
                    'platz_3': AKTIVER_WETTBEWERB['praemie_3'],
                }
            },
            'ranking': ranking,
            'team': {
                'gesamt': team_gesamt,
                'ziel': AKTIVER_WETTBEWERB['ziel_team'],
                'erreichung': round(team_gesamt / AKTIVER_WETTBEWERB['ziel_team'] * 100, 1),
            },
            'hinweis': 'Wettbewerb-Daten sind Platzhalter. Echte Daten erfordern Zugriff auf Rechnungspositionen.',
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@serviceberater_api.route('/tek-config', methods=['GET'])
def tek_config():
    """TEK-Konfiguration für After Sales"""
    
    anzahl_sb = len(SERVICEBERATER_IDS)
    vollkosten_pro_sb = TEK_CONFIG['vollkosten_monat'] / anzahl_sb
    
    return jsonify({
        'success': True,
        'tek': {
            'vollkosten_after_sales': TEK_CONFIG['vollkosten_monat'],
            'teile_service': {
                'direkt': TEK_CONFIG['teile_service_direkt'],
                'umlage': TEK_CONFIG['teile_service_umlage'],
            },
            'werkstattlohn': {
                'direkt': TEK_CONFIG['werkstattlohn_direkt'],
                'umlage': TEK_CONFIG['werkstattlohn_umlage'],
            },
            'margen': {
                'arbeit': TEK_CONFIG['marge_arbeit'],
                'teile': TEK_CONFIG['marge_teile'],
                'gewichtet': TEK_CONFIG['marge_gewichtet'],
            },
        },
        'serviceberater': {
            'anzahl': anzahl_sb,
            'ids': SERVICEBERATER_IDS,
            'vollkosten_pro_sb': round(vollkosten_pro_sb, 2),
            'break_even': round(vollkosten_pro_sb / TEK_CONFIG['marge_gewichtet'], 2),
        },
        'quelle': 'TEK Dezember 2025 - Vollkosten (BE)',
    })


@serviceberater_api.route('/health', methods=['GET'])
def health():
    """Health Check"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
    })
