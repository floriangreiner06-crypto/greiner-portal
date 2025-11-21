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
        
        cursor.execute("SELECT COUNT(*) as count FROM stellantis_bestellungen")
        bestellungen_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM stellantis_positionen")
        positionen_count = cursor.fetchone()['count']
        
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
    - teilenummer: Filtern nach Teilenummer
    - suche: Volltextsuche (Bestellnummer, Lokale Nr, Teilenummer)
    - limit: Max. Anzahl (Default: 100)
    - offset: Offset für Pagination (Default: 0)
    """
    try:
        # Query-Parameter
        datum_von = request.args.get('datum_von', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        datum_bis = request.args.get('datum_bis', datetime.now().strftime('%Y-%m-%d'))
        lokale_nr = request.args.get('lokale_nr')
        absender_code = request.args.get('absender_code')
        teilenummer = request.args.get('teilenummer')
        suche = request.args.get('suche')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Base Filter
        where_conditions = ["DATE(b.bestelldatum) >= ?", "DATE(b.bestelldatum) <= ?"]
        params = [datum_von, datum_bis]
        
        if lokale_nr:
            where_conditions.append("b.lokale_nr = ?")
            params.append(lokale_nr)
            
        if absender_code:
            where_conditions.append("b.absender_code = ?")
            params.append(absender_code)
            
        if teilenummer:
            where_conditions.append("EXISTS (SELECT 1 FROM stellantis_positionen p WHERE p.bestellung_id = b.id AND p.teilenummer LIKE ?)")
            params.append(f"%{teilenummer}%")
            
        if suche:
            where_conditions.append("(b.bestellnummer LIKE ? OR b.lokale_nr LIKE ? OR EXISTS (SELECT 1 FROM stellantis_positionen p WHERE p.bestellung_id = b.id AND p.teilenummer LIKE ?))")
            params.extend([f"%{suche}%", f"%{suche}%", f"%{suche}%"])
        
        where_clause = " AND ".join(where_conditions)
        
        # 1. BESTELLUNGEN mit Pagination
        query = f"""
            SELECT
                b.id,
                b.bestellnummer,
                b.bestelldatum,
                b.absender_code,
                b.absender_name,
                b.empfaenger_code,
                b.lokale_nr,
                b.url,
                (SELECT COUNT(*) FROM stellantis_positionen WHERE bestellung_id = b.id) as anzahl_positionen,
                (SELECT COALESCE(ROUND(SUM(summe_inkl_mwst), 2), 0) FROM stellantis_positionen WHERE bestellung_id = b.id) as gesamtwert,
                b.import_timestamp
            FROM stellantis_bestellungen b
            WHERE {where_clause}
            ORDER BY b.bestelldatum DESC 
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, params + [limit, offset])
        bestellungen = rows_to_list(cursor.fetchall())
        
        # 2. GESAMT-ANZAHL
        count_query = f"""
            SELECT COUNT(*) as total
            FROM stellantis_bestellungen b
            WHERE {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # 3. STATISTIKEN
        if total > 0:
            # Hole alle IDs die dem Filter entsprechen
            ids_query = f"""
                SELECT b.id
                FROM stellantis_bestellungen b
                WHERE {where_clause}
            """
            cursor.execute(ids_query, params)
            bestellung_ids = [row['id'] for row in cursor.fetchall()]
            
            # Stats über diese IDs
            if bestellung_ids:
                placeholders = ','.join('?' * len(bestellung_ids))
                stats_query = f"""
                    SELECT
                        COUNT(*) as total_positionen,
                        COALESCE(SUM(summe_inkl_mwst), 0) as gesamtwert
                    FROM stellantis_positionen
                    WHERE bestellung_id IN ({placeholders})
                """
                cursor.execute(stats_query, bestellung_ids)
                stats_row = cursor.fetchone()
                
                stats = {
                    'total_bestellungen': total,
                    'total_positionen': int(stats_row['total_positionen'] or 0),
                    'durchschnitt_positionen': round((stats_row['total_positionen'] or 0) / total, 1),
                    'gesamtwert': round(float(stats_row['gesamtwert'] or 0), 2)
                }
            else:
                stats = {
                    'total_bestellungen': total,
                    'total_positionen': 0,
                    'durchschnitt_positionen': 0,
                    'gesamtwert': 0
                }
        else:
            stats = {
                'total_bestellungen': 0,
                'total_positionen': 0,
                'durchschnitt_positionen': 0,
                'gesamtwert': 0
            }
        
        conn.close()
        
        return jsonify({
            'bestellungen': bestellungen,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@stellantis_api.route('/api/stellantis/bestellung/<bestellnummer>', methods=['GET'])
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
            SELECT * FROM stellantis_positionen
            WHERE bestellung_id = ?
            ORDER BY id
        """, (bestellung['id'],))
        
        positionen = rows_to_list(cursor.fetchall())
        
        # Berechne Gesamtwerte
        bestellung['anzahl_positionen'] = len(positionen)
        bestellung['gesamtwert'] = round(sum(p.get('summe_inkl_mwst', 0) or 0 for p in positionen), 2)
        bestellung['positionen'] = positionen
        
        conn.close()
        
        return jsonify(bestellung)
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@stellantis_api.route('/api/stellantis/absender', methods=['GET'])
def get_absender():
    """Hole Liste aller eindeutigen Absender"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT
                absender_code as code,
                absender_name as name,
                COUNT(*) as anzahl_bestellungen
            FROM stellantis_bestellungen
            WHERE absender_code IS NOT NULL
            GROUP BY absender_code, absender_name
            ORDER BY anzahl_bestellungen DESC
        """)
        
        absender = rows_to_list(cursor.fetchall())
        conn.close()
        
        return jsonify({
            'absender': absender,
            'anzahl': len(absender)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Stellantis API - Standalone-Test nicht möglich")
    print("Verwende: python app.py")
