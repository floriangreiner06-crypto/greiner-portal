"""
Stellantis ServiceBox API
Endpoints für Bestellungen aus dem ServiceBox-Scraper

TAG 136: PostgreSQL-Migration - nutzt db_session
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta

from api.db_utils import db_session, row_to_dict, rows_to_list
from api.db_connection import sql_placeholder, get_db_type

# Blueprint erstellen
parts_api = Blueprint('parts_api', __name__)


# =============================================================================
# LIEFERSCHEIN-STATUS HELPER
# =============================================================================

def get_lieferschein_status_for_bestellungen(cursor, bestellnummern):
    """
    Hole Lieferschein-Status für eine Liste von Bestellnummern
    Status: bestellt → geliefert → in_locosoft → zugebucht
    TAG 136: PostgreSQL-kompatibel
    """
    if not bestellnummern:
        return {}

    ph = sql_placeholder()
    placeholders = ','.join([ph] * len(bestellnummern))

    # TAG142: PostgreSQL Boolean-kompatibel (true/false statt 1/0)
    cursor.execute(f"""
        SELECT
            servicebox_bestellnr,
            COUNT(*) as pos_total,
            SUM(CASE WHEN locosoft_zugebucht = true THEN 1 ELSE 0 END) as zugebucht,
            SUM(CASE WHEN locosoft_gefunden = true AND locosoft_zugebucht = false THEN 1 ELSE 0 END) as in_locosoft,
            SUM(CASE WHEN locosoft_gefunden = false THEN 1 ELSE 0 END) as geliefert,
            MAX(lieferdatum) as letztes_lieferdatum
        FROM teile_lieferscheine
        WHERE servicebox_bestellnr IN ({placeholders})
          AND servicebox_bestellnr != ''
        GROUP BY servicebox_bestellnr
    """, bestellnummern)

    result = {}
    for row in cursor.fetchall():
        row_dict = row_to_dict(row)
        bestellnr = row_dict['servicebox_bestellnr']
        total = row_dict['pos_total'] or 0
        zugebucht = row_dict['zugebucht'] or 0
        in_loco = row_dict['in_locosoft'] or 0

        if total == 0:
            status = 'bestellt'
        elif zugebucht == total:
            status = 'zugebucht'
        elif zugebucht > 0 or in_loco > 0:
            status = 'in_locosoft'
        else:
            status = 'geliefert'

        result[bestellnr] = {
            'status': status,
            'lieferschein_positionen': total,
            'zugebucht': zugebucht,
            'in_locosoft': in_loco,
            'geliefert': row_dict['geliefert'] or 0,
            'letztes_lieferdatum': row_dict['letztes_lieferdatum']
        }

    return result


# =============================================================================
# ENDPOINTS
# =============================================================================

@parts_api.route('/api/parts/health', methods=['GET'])
def health_check():
    """Health Check"""
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM stellantis_bestellungen")
            bestellungen_count = row_to_dict(cursor.fetchone())['count']

            cursor.execute("SELECT COUNT(*) as count FROM stellantis_positionen")
            positionen_count = row_to_dict(cursor.fetchone())['count']

            cursor.execute("SELECT MAX(bestelldatum) as letzte_bestellung FROM stellantis_bestellungen")
            letzte_bestellung = row_to_dict(cursor.fetchone())['letzte_bestellung']

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

@parts_api.route('/api/parts/bestellungen', methods=['GET'])
def get_bestellungen():
    """
    Hole alle Bestellungen mit optionalen Filtern
    TAG 136: PostgreSQL-kompatibel
    TAG 171: Filter nach Serviceberater (ma_id) - zeigt nur Bestellungen für Aufträge des Serviceberaters
    """
    try:
        from flask_login import current_user
        from api.serviceberater_api import get_sb_config_from_ldap
        from api.db_utils import get_locosoft_connection as get_loco_conn
        from psycopg2.extras import RealDictCursor
        
        # Query-Parameter
        # TAG 173: Standard-Filter auf 90 Tage erhöht (statt 30)
        datum_von = request.args.get('datum_von', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
        datum_bis = request.args.get('datum_bis', datetime.now().strftime('%Y-%m-%d'))
        lokale_nr = request.args.get('lokale_nr')
        absender_code = request.args.get('absender_code')
        teilenummer = request.args.get('teilenummer')
        suche = request.args.get('suche')
        ma_id_param = request.args.get('ma_id', type=int)  # TAG 171: Optional ma_id Parameter
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # TAG 171: Prüfe ob User Serviceberater ist und hole ma_id
        serviceberater_auftrag_nrs = None
        if not ma_id_param and current_user.is_authenticated:
            display_name = getattr(current_user, 'display_name', '')
            if display_name:
                sb_config = get_sb_config_from_ldap(display_name)
                if sb_config:
                    ma_id_param = sb_config.get('ma_id')
        
        # TAG 171: Wenn ma_id vorhanden, hole alle Auftragsnummern dieses Serviceberaters
        if ma_id_param:
            try:
                conn_loco = get_loco_conn()
                cursor_loco = conn_loco.cursor(cursor_factory=RealDictCursor)
                cursor_loco.execute("""
                    SELECT DISTINCT o.number as auftrag_nr
                    FROM orders o
                    WHERE o.order_taking_employee_no = %s
                      AND o.order_date >= %s::date - INTERVAL '90 days'
                """, (ma_id_param, datum_bis))
                auftraege = cursor_loco.fetchall()
                serviceberater_auftrag_nrs = [str(a['auftrag_nr']) for a in auftraege]
                cursor_loco.close()
                conn_loco.close()
            except Exception as e:
                print(f"⚠️ Fehler beim Holen der Aufträge für Serviceberater {ma_id_param}: {e}")
                serviceberater_auftrag_nrs = None

        ph = sql_placeholder()

        # DATE() funktioniert in beiden DBs
        with db_session() as conn:
            cursor = conn.cursor()

            # Base Filter
            where_conditions = [f"DATE(b.bestelldatum) >= {ph}", f"DATE(b.bestelldatum) <= {ph}"]
            params = [datum_von, datum_bis]

            if lokale_nr:
                where_conditions.append(f"b.lokale_nr = {ph}")
                params.append(lokale_nr)

            if absender_code:
                where_conditions.append(f"b.absender_code = {ph}")
                params.append(absender_code)

            if teilenummer:
                where_conditions.append(f"EXISTS (SELECT 1 FROM stellantis_positionen p WHERE p.bestellung_id = b.id AND p.teilenummer LIKE {ph})")
                params.append(f"%{teilenummer}%")

            if suche:
                where_conditions.append(f"(b.bestellnummer LIKE {ph} OR b.lokale_nr LIKE {ph} OR b.parsed_kundennummer LIKE {ph} OR b.match_kunde_name LIKE {ph} OR EXISTS (SELECT 1 FROM stellantis_positionen p WHERE p.bestellung_id = b.id AND p.teilenummer LIKE {ph}))")
                params.extend([f"%{suche}%", f"%{suche}%", f"%{suche}%", f"%{suche}%", f"%{suche}%"])
            
            # TAG 171: Filter nach Serviceberater-Aufträgen (lokale_nr = Auftragsnummer)
            if serviceberater_auftrag_nrs and len(serviceberater_auftrag_nrs) > 0:
                # PostgreSQL: ANY() für Array-Vergleich
                if get_db_type() == 'postgresql':
                    placeholders = ','.join([ph] * len(serviceberater_auftrag_nrs))
                    where_conditions.append(f"b.lokale_nr = ANY(ARRAY[{placeholders}])")
                    params.extend(serviceberater_auftrag_nrs)
                else:
                    # SQLite: IN() für Liste
                    placeholders = ','.join([ph] * len(serviceberater_auftrag_nrs))
                    where_conditions.append(f"b.lokale_nr IN ({placeholders})")
                    params.extend(serviceberater_auftrag_nrs)

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
                    b.parsed_kundennummer,
                    b.parsed_vin,
                    b.match_typ,
                    b.match_kunde_name,
                    b.match_confidence,
                    b.kommentar_werkstatt,
                    (SELECT COUNT(*) FROM stellantis_positionen WHERE bestellung_id = b.id) as anzahl_positionen,
                    (SELECT COALESCE(ROUND(SUM(summe_inkl_mwst)::numeric, 2), 0) FROM stellantis_positionen WHERE bestellung_id = b.id) as gesamtwert,
                    b.import_timestamp
                FROM stellantis_bestellungen b
                WHERE {where_clause}
                ORDER BY b.bestelldatum DESC
                LIMIT {ph} OFFSET {ph}
            """

            # SQLite braucht andere ROUND-Syntax
            if get_db_type() != 'postgresql':
                query = query.replace('::numeric', '')

            cursor.execute(query, params + [limit, offset])
            bestellungen = rows_to_list(cursor.fetchall())

            # Lieferschein-Status für alle Bestellungen holen
            if bestellungen:
                bestellnummern = [b['bestellnummer'] for b in bestellungen if b.get('bestellnummer')]
                lieferschein_status = get_lieferschein_status_for_bestellungen(cursor, bestellnummern)

                for b in bestellungen:
                    ls_info = lieferschein_status.get(b['bestellnummer'], {})
                    b['lieferschein_status'] = ls_info.get('status', 'bestellt')
                    b['lieferschein_info'] = ls_info

            # 2. GESAMT-ANZAHL
            count_query = f"""
                SELECT COUNT(*) as total
                FROM stellantis_bestellungen b
                WHERE {where_clause}
            """
            cursor.execute(count_query, params)
            total = row_to_dict(cursor.fetchone())['total']

            # 3. STATISTIKEN
            if total > 0:
                ids_query = f"""
                    SELECT b.id
                    FROM stellantis_bestellungen b
                    WHERE {where_clause}
                """
                cursor.execute(ids_query, params)
                bestellung_ids = [row_to_dict(row)['id'] for row in cursor.fetchall()]

                if bestellung_ids:
                    id_placeholders = ','.join([ph] * len(bestellung_ids))
                    stats_query = f"""
                        SELECT
                            COUNT(*) as total_positionen,
                            COALESCE(SUM(summe_inkl_mwst), 0) as gesamtwert
                        FROM stellantis_positionen
                        WHERE bestellung_id IN ({id_placeholders})
                    """
                    cursor.execute(stats_query, bestellung_ids)
                    stats_row = row_to_dict(cursor.fetchone())

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

@parts_api.route('/api/parts/bestellung/<bestellnummer>', methods=['GET'])
@parts_api.route('/api/parts/bestellungen/<bestellnummer>', methods=['GET'])
def get_bestellung_detail(bestellnummer):
    """
    Hole Details einer einzelnen Bestellung inkl. aller Positionen
    TAG 136: PostgreSQL-kompatibel
    """
    try:
        ph = sql_placeholder()

        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT * FROM stellantis_bestellungen
                WHERE bestellnummer = {ph}
            """, (bestellnummer,))

            bestellung = row_to_dict(cursor.fetchone())

            if not bestellung:
                return jsonify({'error': 'Bestellung nicht gefunden'}), 404

            cursor.execute(f"""
                SELECT * FROM stellantis_positionen
                WHERE bestellung_id = {ph}
                ORDER BY id
            """, (bestellung['id'],))

            positionen = rows_to_list(cursor.fetchall())
            
            # TAG173: Lieferschein-Status hinzufügen (wie in get_bestellungen)
            bestellnummern = [bestellung['bestellnummer']]
            lieferschein_status = get_lieferschein_status_for_bestellungen(cursor, bestellnummern)
            ls_info = lieferschein_status.get(bestellung['bestellnummer'], {})
            bestellung['lieferschein_status'] = ls_info.get('status', 'bestellt')
            bestellung['lieferschein_info'] = ls_info

        bestellung['anzahl_positionen'] = len(positionen)
        bestellung['gesamtwert'] = round(sum(p.get('summe_inkl_mwst', 0) or 0 for p in positionen), 2)
        bestellung['positionen'] = positionen

        return jsonify(bestellung)

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@parts_api.route('/api/parts/absender', methods=['GET'])
def get_absender():
    """Hole Liste aller eindeutigen Absender"""
    try:
        with db_session() as conn:
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

        return jsonify({
            'absender': absender,
            'anzahl': len(absender)
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@parts_api.route('/api/parts/sync-status', methods=['GET'])
def get_sync_status():
    """
    Liefert den aktuellen Sync-Status für ServiceBox
    TAG 136: PostgreSQL-kompatibel
    """
    try:
        # date('now') funktioniert in SQLite, für PostgreSQL: CURRENT_DATE
        if get_db_type() == 'postgresql':
            date_today = "CURRENT_DATE"
        else:
            date_today = "DATE('now')"

        with db_session() as conn:
            cursor = conn.cursor()

            # Sync-Status
            cursor.execute("""
                SELECT
                    last_run,
                    status,
                    records_processed,
                    records_matched,
                    error_message
                FROM sync_status
                WHERE sync_name = 'servicebox'
            """)
            sync_row = row_to_dict(cursor.fetchone())

            # Statistiken aus DB
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN match_typ IS NOT NULL THEN 1 ELSE 0 END) as matched,
                    MAX(bestelldatum) as letzte_bestellung,
                    MIN(bestelldatum) as erste_bestellung
                FROM stellantis_bestellungen
            """)
            stats_row = row_to_dict(cursor.fetchone())

            # Heute
            cursor.execute(f"""
                SELECT COUNT(*) as heute
                FROM stellantis_bestellungen
                WHERE DATE(bestelldatum) = {date_today}
            """)
            heute_row = row_to_dict(cursor.fetchone())

        # Response bauen
        if sync_row:
            last_run = sync_row['last_run']
            if last_run:
                try:
                    last_dt = datetime.strptime(str(last_run)[:19], '%Y-%m-%d %H:%M:%S')
                    diff = datetime.now() - last_dt
                    minutes = int(diff.total_seconds() / 60)
                    if minutes < 60:
                        ago_text = f"vor {minutes} Min."
                    elif minutes < 1440:
                        ago_text = f"vor {minutes // 60} Std."
                    else:
                        ago_text = f"vor {minutes // 1440} Tagen"
                except:
                    ago_text = None
            else:
                ago_text = None

            sync_status = {
                'last_run': last_run,
                'last_run_ago': ago_text,
                'status': sync_row['status'],
                'records_processed': sync_row['records_processed'],
                'records_matched': sync_row['records_matched'],
                'error_message': sync_row['error_message']
            }
        else:
            sync_status = {
                'last_run': None,
                'status': 'never_run'
            }

        return jsonify({
            'sync': sync_status,
            'stats': {
                'total': stats_row['total'] if stats_row else 0,
                'matched': stats_row['matched'] if stats_row else 0,
                'match_rate': round((stats_row['matched'] or 0) / max(stats_row['total'] or 1, 1) * 100, 1) if stats_row else 0,
                'heute': heute_row['heute'] if heute_row else 0,
                'letzte_bestellung': stats_row['letzte_bestellung'] if stats_row else None
            },
            'cron_schedule': '09:00, 12:00, 16:00, 19:00'
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@parts_api.route('/api/parts/servicebox-url', methods=['GET'])
def get_servicebox_url_with_auth():
    """
    Generiert ServiceBox-URL mit Credentials für automatischen Login
    """
    from flask import redirect, request
    import os
    import json
    from urllib.parse import unquote
    
    try:
        servicebox_url = request.args.get('url')
        if not servicebox_url:
            return jsonify({'error': 'URL-Parameter fehlt'}), 400
        
        # URL dekodieren
        servicebox_url = unquote(servicebox_url)
        
        # Credentials laden
        credentials_path = '/opt/greiner-portal/config/credentials.json'
        if not os.path.exists(credentials_path):
            return jsonify({'error': 'Credentials nicht gefunden'}), 404
        
        with open(credentials_path, 'r') as f:
            creds = json.load(f)
        
        servicebox_creds = creds.get('external_systems', {}).get('stellantis_servicebox', {})
        username = servicebox_creds.get('username')
        password = servicebox_creds.get('password')
        
        if not username or not password:
            return jsonify({'error': 'ServiceBox Credentials nicht gefunden'}), 404
        
        # URL mit Credentials bauen
        # Format: https://username:password@host/path
        if servicebox_url.startswith('http://') or servicebox_url.startswith('https://'):
            # URL bereits vollständig
            protocol, rest = servicebox_url.split('://', 1)
            auth_url = f"{protocol}://{username}:{password}@{rest}"
        else:
            # Nur Pfad, füge Base-URL hinzu
            base_url = servicebox_creds.get('portal_url', 'https://servicebox.mpsa.com')
            protocol, rest = base_url.split('://', 1)
            auth_url = f"{protocol}://{username}:{password}@{rest}/{servicebox_url.lstrip('/')}"
        
        # Redirect zur URL mit Credentials
        return redirect(auth_url)
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Stellantis API - Standalone-Test nicht möglich")
    print("Verwende: python app.py")
