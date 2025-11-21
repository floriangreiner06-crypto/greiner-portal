"""
Stellantis ServiceBox API
Endpoints für Bestellungen aus dem ServiceBox-Scraper
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime, timedelta
import os

# Blueprint erstellen
stellantis_api = Blueprint('stellantis_api', __name__)

# Datenbank-Pfad (wird in app.py konfiguriert)
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

def get_db_connection():
    """Erstelle Datenbankverbindung"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def row_to_dict(row):
    """Konvertiere sqlite3.Row zu Dictionary"""
    return dict(zip(row.keys(), row)) if row else None

def rows_to_list(rows):
    """Konvertiere Liste von sqlite3.Row zu Liste von Dictionaries"""
    return [row_to_dict(row) for row in rows]


# =============================================================================
# ENDPOINTS
# =============================================================================

@stellantis_api.route('/api/stellantis/health', methods=['GET'])
def health_check():
    """Health Check"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Zähle Bestellungen
        cursor.execute("SELECT COUNT(*) as count FROM stellantis_bestellungen")
        bestellungen_count = cursor.fetchone()['count']
        
        # Zähle Positionen
        cursor.execute("SELECT COUNT(*) as count FROM stellantis_positionen")
        positionen_count = cursor.fetchone()['count']
        
        # Letzte Bestellung
        cursor.execute("SELECT MAX(bestelldatum) as letzte_bestellung FROM stellantis_bestellungen")
        letzte_bestellung = cursor.fetchone()['letzte_bestellung']
        
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'bestellungen': bestellungen_count,
            'positionen': positionen_count,
            'letzte_bestellung': letzte_bestellung,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@stellantis_api.route('/api/stellantis/bestellungen', methods=['GET'])
def get_bestellungen():
    """
    Hole alle Bestellungen mit optionalen Filtern
    
    Query Parameters:
    - datum_von: YYYY-MM-DD (Default: heute - 30 Tage)
    - datum_bis: YYYY-MM-DD (Default: heute)
    - lokale_nr: Filtern nach lokale_nr
    - absender_code: Filtern nach Absender-Code
    - limit: Max. Anzahl (Default: 100)
    - offset: Offset für Pagination (Default: 0)
    """
    try:
        # Query-Parameter
        datum_von = request.args.get('datum_von', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        datum_bis = request.args.get('datum_bis', datetime.now().strftime('%Y-%m-%d'))
        lokale_nr = request.args.get('lokale_nr')
        absender_code = request.args.get('absender_code')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Base Query
        query = """
            SELECT 
                b.id,
                b.bestellnummer,
                b.bestelldatum,
                b.absender_code,
                b.absender_name,
                b.empfaenger_code,
                b.lokale_nr,
                b.url,
                COUNT(p.id) as anzahl_positionen,
                ROUND(SUM(p.summe_inkl_mwst), 2) as gesamtwert,
                b.import_timestamp
            FROM stellantis_bestellungen b
            LEFT JOIN stellantis_positionen p ON b.id = p.bestellung_id
            WHERE DATE(b.bestelldatum) >= ? AND DATE(b.bestelldatum) <= ?
        """
        
        params = [datum_von, datum_bis]
        
        # Zusätzliche Filter
        if lokale_nr:
            query += " AND b.lokale_nr = ?"
            params.append(lokale_nr)
            
        if absender_code:
            query += " AND b.absender_code = ?"
            params.append(absender_code)
        
        query += " GROUP BY b.id ORDER BY b.bestelldatum DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        bestellungen = rows_to_list(cursor.fetchall())
        
        # Gesamtanzahl für Pagination
        count_query = """
            SELECT COUNT(*) as total
            FROM stellantis_bestellungen b
            WHERE DATE(b.bestelldatum) >= ? AND DATE(b.bestelldatum) <= ?
        """
        count_params = [datum_von, datum_bis]
        
        if lokale_nr:
            count_query += " AND b.lokale_nr = ?"
            count_params.append(lokale_nr)
            
        if absender_code:
            count_query += " AND b.absender_code = ?"
            count_params.append(absender_code)
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']
        
        conn.close()
        
        return jsonify({
            'bestellungen': bestellungen,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@stellantis_api.route('/api/stellantis/bestellungen/<bestellnummer>', methods=['GET'])
def get_bestellung_detail(bestellnummer):
    """
    Hole Details einer einzelnen Bestellung inkl. aller Positionen
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Bestellung
        cursor.execute("""
            SELECT * FROM stellantis_bestellungen
            WHERE bestellnummer = ?
        """, (bestellnummer,))
        
        bestellung = row_to_dict(cursor.fetchone())
        
        if not bestellung:
            conn.close()
            return jsonify({'error': 'Bestellung nicht gefunden'}), 404
        
        # Positionen
        cursor.execute("""
            SELECT 
                id,
                teilenummer,
                beschreibung,
                menge,
                menge_in_lieferung,
                menge_in_bestellung,
                preis_ohne_mwst_text,
                preis_mit_mwst_text,
                summe_inkl_mwst_text,
                preis_ohne_mwst,
                preis_mit_mwst,
                summe_inkl_mwst
            FROM stellantis_positionen
            WHERE bestellung_id = ?
            ORDER BY id
        """, (bestellung['id'],))
        
        positionen = rows_to_list(cursor.fetchall())
        
        # Statistik berechnen
        gesamtwert = sum(p['summe_inkl_mwst'] or 0 for p in positionen)
        
        bestellung['positionen'] = positionen
        bestellung['anzahl_positionen'] = len(positionen)
        bestellung['gesamtwert'] = round(gesamtwert, 2)
        
        conn.close()
        
        return jsonify(bestellung)
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@stellantis_api.route('/api/stellantis/positionen', methods=['GET'])
def get_positionen():
    """
    Hole alle Positionen mit optionalen Filtern
    
    Query Parameters:
    - teilenummer: Filtern nach Teilenummer
    - beschreibung: Suchen in Beschreibung (LIKE)
    - limit: Max. Anzahl (Default: 100)
    """
    try:
        teilenummer = request.args.get('teilenummer')
        beschreibung = request.args.get('beschreibung')
        limit = int(request.args.get('limit', 100))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                p.*,
                b.bestellnummer,
                b.bestelldatum,
                b.lokale_nr
            FROM stellantis_positionen p
            JOIN stellantis_bestellungen b ON p.bestellung_id = b.id
            WHERE 1=1
        """
        
        params = []
        
        if teilenummer:
            query += " AND p.teilenummer = ?"
            params.append(teilenummer)
            
        if beschreibung:
            query += " AND p.beschreibung LIKE ?"
            params.append(f'%{beschreibung}%')
        
        query += " ORDER BY b.bestelldatum DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        positionen = rows_to_list(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            'positionen': positionen,
            'count': len(positionen)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@stellantis_api.route('/api/stellantis/top-teile', methods=['GET'])
def get_top_teile():
    """
    Hole die häufigsten Teile
    
    Query Parameters:
    - limit: Anzahl Top-Teile (Default: 10)
    - datum_von: YYYY-MM-DD
    - datum_bis: YYYY-MM-DD
    """
    try:
        limit = int(request.args.get('limit', 10))
        datum_von = request.args.get('datum_von')
        datum_bis = request.args.get('datum_bis')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                p.teilenummer,
                p.beschreibung,
                COUNT(*) as anzahl_bestellungen,
                SUM(p.menge) as gesamt_menge,
                ROUND(AVG(p.preis_ohne_mwst), 2) as durchschnittspreis,
                ROUND(SUM(p.summe_inkl_mwst), 2) as gesamtwert,
                MAX(b.bestelldatum) as letzte_bestellung
            FROM stellantis_positionen p
            JOIN stellantis_bestellungen b ON p.bestellung_id = b.id
            WHERE 1=1
        """
        
        params = []
        
        if datum_von:
            query += " AND DATE(b.bestelldatum) >= ?"
            params.append(datum_von)
            
        if datum_bis:
            query += " AND DATE(b.bestelldatum) <= ?"
            params.append(datum_bis)
        
        query += """
            GROUP BY p.teilenummer, p.beschreibung
            ORDER BY anzahl_bestellungen DESC
            LIMIT ?
        """
        params.append(limit)
        
        cursor.execute(query, params)
        top_teile = rows_to_list(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            'top_teile': top_teile,
            'count': len(top_teile)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@stellantis_api.route('/api/stellantis/statistik', methods=['GET'])
def get_statistik():
    """
    Hole Gesamt-Statistik
    
    Query Parameters:
    - datum_von: YYYY-MM-DD (Default: heute - 30 Tage)
    - datum_bis: YYYY-MM-DD (Default: heute)
    """
    try:
        datum_von = request.args.get('datum_von', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        datum_bis = request.args.get('datum_bis', datetime.now().strftime('%Y-%m-%d'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Basis-Statistik
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT b.id) as anzahl_bestellungen,
                COUNT(p.id) as anzahl_positionen,
                ROUND(SUM(p.summe_inkl_mwst), 2) as gesamtwert,
                ROUND(AVG(p.summe_inkl_mwst), 2) as durchschnitt_position,
                COUNT(DISTINCT p.teilenummer) as anzahl_verschiedene_teile
            FROM stellantis_bestellungen b
            LEFT JOIN stellantis_positionen p ON b.id = p.bestellung_id
            WHERE DATE(b.bestelldatum) >= ? AND DATE(b.bestelldatum) <= ?
        """, (datum_von, datum_bis))
        
        statistik = row_to_dict(cursor.fetchone())
        
        # Bestellungen pro Tag
        cursor.execute("""
            SELECT 
                DATE(bestelldatum) as datum,
                COUNT(*) as anzahl
            FROM stellantis_bestellungen
            WHERE DATE(bestelldatum) >= ? AND DATE(bestelldatum) <= ?
            GROUP BY DATE(bestelldatum)
            ORDER BY datum
        """, (datum_von, datum_bis))
        
        bestellungen_pro_tag = rows_to_list(cursor.fetchall())
        
        # Top 5 Absender
        cursor.execute("""
            SELECT 
                absender_code,
                absender_name,
                COUNT(*) as anzahl
            FROM stellantis_bestellungen
            WHERE DATE(bestelldatum) >= ? AND DATE(bestelldatum) <= ?
            GROUP BY absender_code, absender_name
            ORDER BY anzahl DESC
            LIMIT 5
        """, (datum_von, datum_bis))
        
        top_absender = rows_to_list(cursor.fetchall())
        
        # Top 5 lokale_nr
        cursor.execute("""
            SELECT 
                lokale_nr,
                COUNT(*) as anzahl,
                ROUND(SUM(
                    (SELECT SUM(summe_inkl_mwst) FROM stellantis_positionen WHERE bestellung_id = b.id)
                ), 2) as gesamtwert
            FROM stellantis_bestellungen b
            WHERE DATE(bestelldatum) >= ? AND DATE(bestelldatum) <= ?
            AND lokale_nr IS NOT NULL
            GROUP BY lokale_nr
            ORDER BY anzahl DESC
            LIMIT 5
        """, (datum_von, datum_bis))
        
        top_lokale_nr = rows_to_list(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            'zeitraum': {
                'von': datum_von,
                'bis': datum_bis
            },
            'statistik': statistik,
            'bestellungen_pro_tag': bestellungen_pro_tag,
            'top_absender': top_absender,
            'top_lokale_nr': top_lokale_nr
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@stellantis_api.route('/api/stellantis/suche', methods=['GET'])
def suche():
    """
    Universelle Suche über Bestellungen und Positionen
    
    Query Parameters:
    - q: Suchbegriff
    - limit: Max. Ergebnisse (Default: 20)
    """
    try:
        suchbegriff = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not suchbegriff:
            return jsonify({
                'error': 'Suchbegriff fehlt'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Suche in Bestellungen
        cursor.execute("""
            SELECT 
                'bestellung' as typ,
                id,
                bestellnummer as nummer,
                bestelldatum as datum,
                lokale_nr,
                absender_name as details
            FROM stellantis_bestellungen
            WHERE bestellnummer LIKE ?
               OR lokale_nr LIKE ?
               OR absender_name LIKE ?
            LIMIT ?
        """, (f'%{suchbegriff}%', f'%{suchbegriff}%', f'%{suchbegriff}%', limit))
        
        bestellungen_treffer = rows_to_list(cursor.fetchall())
        
        # Suche in Positionen
        cursor.execute("""
            SELECT 
                'position' as typ,
                p.id,
                p.teilenummer as nummer,
                b.bestelldatum as datum,
                b.lokale_nr,
                p.beschreibung as details
            FROM stellantis_positionen p
            JOIN stellantis_bestellungen b ON p.bestellung_id = b.id
            WHERE p.teilenummer LIKE ?
               OR p.beschreibung LIKE ?
            LIMIT ?
        """, (f'%{suchbegriff}%', f'%{suchbegriff}%', limit))
        
        positionen_treffer = rows_to_list(cursor.fetchall())
        
        conn.close()
        
        # Kombiniere Ergebnisse
        ergebnisse = bestellungen_treffer + positionen_treffer
        ergebnisse.sort(key=lambda x: x['datum'], reverse=True)
        
        return jsonify({
            'suchbegriff': suchbegriff,
            'ergebnisse': ergebnisse[:limit],
            'anzahl_bestellungen': len(bestellungen_treffer),
            'anzahl_positionen': len(positionen_treffer),
            'gesamt': len(ergebnisse)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


# =============================================================================
# EXPORT ENDPOINTS
# =============================================================================

@stellantis_api.route('/api/stellantis/export/csv', methods=['GET'])
def export_csv():
    """
    Exportiere Bestellungen als CSV
    """
    try:
        from io import StringIO
        import csv
        
        datum_von = request.args.get('datum_von', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        datum_bis = request.args.get('datum_bis', datetime.now().strftime('%Y-%m-%d'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                b.bestellnummer,
                b.bestelldatum,
                b.absender_code,
                b.absender_name,
                b.empfaenger_code,
                b.lokale_nr,
                p.teilenummer,
                p.beschreibung,
                p.menge,
                p.preis_ohne_mwst,
                p.summe_inkl_mwst
            FROM stellantis_bestellungen b
            LEFT JOIN stellantis_positionen p ON b.id = p.bestellung_id
            WHERE DATE(b.bestelldatum) >= ? AND DATE(b.bestelldatum) <= ?
            ORDER BY b.bestelldatum DESC
        """, (datum_von, datum_bis))
        
        rows = cursor.fetchall()
        conn.close()
        
        # CSV erstellen
        si = StringIO()
        writer = csv.writer(si, delimiter=';')
        
        # Header
        writer.writerow([
            'Bestellnummer', 'Bestelldatum', 'Absender Code', 'Absender Name',
            'Empfänger Code', 'Lokale Nr', 'Teilenummer', 'Beschreibung',
            'Menge', 'Preis (netto)', 'Summe (brutto)'
        ])
        
        # Daten
        for row in rows:
            writer.writerow(row)
        
        output = si.getvalue()
        si.close()
        
        from flask import Response
        return Response(
            output,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=stellantis_bestellungen_{datum_von}_{datum_bis}.csv'
            }
        )
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("Stellantis API - Standalone-Test nicht möglich")
    print("Verwende: python app.py")
