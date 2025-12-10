"""
Werkstatt API - Leistungsübersicht
==================================
REST API für Werkstatt-Mechaniker-Leistungsdaten

Endpoints:
- GET /api/werkstatt/leistung - Mechaniker-Leistungsdaten
- GET /api/werkstatt/mechaniker/<nr> - Detail für einen Mechaniker
- GET /api/werkstatt/trend - Leistungsgrad-Trend über Zeit

Erstellt: 2025-12-04 (TAG 90)
Updated: 2025-12-04 - Betriebsfilter hinzugefügt
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime, timedelta

werkstatt_api = Blueprint('werkstatt_api', __name__, url_prefix='/api/werkstatt')

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'


def get_db():
    """Gibt eine DB-Verbindung zurück"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_date_range(zeitraum, von=None, bis=None):
    """Berechnet Datumsbereich basierend auf Zeitraum-Parameter"""
    heute = datetime.now().date()
    
    if zeitraum == 'heute':
        return heute.isoformat(), heute.isoformat()
    elif zeitraum == 'woche':
        # Montag dieser Woche (weekday() = 0 für Montag)
        montag = heute - timedelta(days=heute.weekday())
        return montag.isoformat(), heute.isoformat()
    elif zeitraum == 'monat':
        start = heute.replace(day=1)
        return start.isoformat(), heute.isoformat()
    elif zeitraum == 'vormonat':
        erster_aktuell = heute.replace(day=1)
        letzter_vormonat = erster_aktuell - timedelta(days=1)
        erster_vormonat = letzter_vormonat.replace(day=1)
        return erster_vormonat.isoformat(), letzter_vormonat.isoformat()
    elif zeitraum == 'quartal':
        quartal_start_monat = ((heute.month - 1) // 3) * 3 + 1
        start = heute.replace(month=quartal_start_monat, day=1)
        return start.isoformat(), heute.isoformat()
    elif zeitraum == 'jahr':
        start = heute.replace(month=1, day=1)
        return start.isoformat(), heute.isoformat()
    elif zeitraum == 'custom' and von and bis:
        return von, bis
    else:
        # Default: aktueller Monat
        start = heute.replace(day=1)
        return start.isoformat(), heute.isoformat()


@werkstatt_api.route('/leistung', methods=['GET'])
def get_leistung():
    """
    GET /api/werkstatt/leistung
    
    Parameter:
    - zeitraum: heute|woche|monat|vormonat|quartal|jahr|custom
    - von: Startdatum (bei custom)
    - bis: Enddatum (bei custom)
    - betrieb: alle|1|3
    - sort: leistungsgrad|stempelzeit|aw|auftraege
    
    Returns: Mechaniker-Liste mit Leistungsdaten
    """
    try:
        zeitraum = request.args.get('zeitraum', 'monat')
        von = request.args.get('von')
        bis = request.args.get('bis')
        betrieb = request.args.get('betrieb', 'alle')
        sort = request.args.get('sort', 'leistungsgrad')
        inkl_ehemalige = request.args.get('inkl_ehemalige', '0') == '1'
        
        datum_von, datum_bis = get_date_range(zeitraum, von, bis)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Mechaniker-Aggregation aus werkstatt_leistung_daily
        # NUR Mitarbeiter mit Stempelzeit > 0 (echte Mechaniker)
        query = """
            SELECT 
                mechaniker_nr,
                mechaniker_name as name,
                MAX(ist_aktiv) as ist_aktiv,
                COUNT(DISTINCT datum) as tage,
                SUM(anzahl_auftraege) as auftraege,
                SUM(stempelzeit_min) as stempelzeit,
                SUM(anwesenheit_min) as anwesenheit,
                SUM(vorgabezeit_aw) as aw,
                SUM(umsatz) as umsatz,
                CASE 
                    WHEN SUM(stempelzeit_min) > 0 AND SUM(vorgabezeit_aw) > 0
                    THEN ROUND(SUM(vorgabezeit_aw) * 6.0 / SUM(stempelzeit_min) * 100, 1)
                    ELSE NULL
                END as leistungsgrad,
                CASE 
                    WHEN SUM(anwesenheit_min) > 0 AND SUM(stempelzeit_min) > 0
                    THEN ROUND(SUM(stempelzeit_min) / SUM(anwesenheit_min) * 100, 1)
                    ELSE NULL
                END as produktivitaet
            FROM werkstatt_leistung_daily
            WHERE datum >= ? AND datum <= ?
            AND mechaniker_nr IS NOT NULL
            AND mechaniker_name IS NOT NULL
            AND stempelzeit_min > 0
        """
        params = [datum_von, datum_bis]
        
        # Betrieb-Filter
        # Locosoft: 1=Deggendorf (Stellantis), 3=Landau
        # Hinweis: Betrieb 2 (Hyundai) hat keine eigenen Werkstatt-Mitarbeiter!
        # NULL/0 Betriebe gehören meist zu Deggendorf
        if betrieb and betrieb != 'alle':
            betrieb_nr = int(betrieb)
            if betrieb_nr == 1:
                # Deggendorf: betrieb_nr = 1 ODER NULL/0 (nicht zugeordnet)
                query += " AND (betrieb_nr = 1 OR betrieb_nr IS NULL OR betrieb_nr = 0)"
            else:
                query += " AND betrieb_nr = ?"
                params.append(betrieb_nr)
        
        # Nur aktive Mitarbeiter (außer inkl_ehemalige ist gesetzt)
        if not inkl_ehemalige:
            query += " AND ist_aktiv = 1"
        
        query += " GROUP BY mechaniker_nr, mechaniker_name"
        
        # Sortierung
        if sort == 'leistungsgrad':
            query += " ORDER BY leistungsgrad DESC NULLS LAST"
        elif sort == 'stempelzeit':
            query += " ORDER BY stempelzeit DESC"
        elif sort == 'aw':
            query += " ORDER BY aw DESC"
        elif sort == 'auftraege':
            query += " ORDER BY auftraege DESC"
        else:
            query += " ORDER BY leistungsgrad DESC NULLS LAST"
        
        cursor.execute(query, params)
        mechaniker = [dict(row) for row in cursor.fetchall()]
        
        # Gesamt-KPIs berechnen
        gesamt_auftraege = sum(m['auftraege'] or 0 for m in mechaniker)
        gesamt_stempelzeit = sum(m['stempelzeit'] or 0 for m in mechaniker)
        gesamt_anwesenheit = sum(m['anwesenheit'] or 0 for m in mechaniker)
        gesamt_aw = sum(m['aw'] or 0 for m in mechaniker)
        gesamt_umsatz = sum(m['umsatz'] or 0 for m in mechaniker)
        gesamt_vorgabe = gesamt_aw * 6
        gesamt_leistungsgrad = round(gesamt_vorgabe / gesamt_stempelzeit * 100, 1) if gesamt_stempelzeit > 0 else 0
        gesamt_produktivitaet = round(gesamt_stempelzeit / gesamt_anwesenheit * 100, 1) if gesamt_anwesenheit > 0 else 0
        
        # Anzahl Tage (unique) - auch mit Betrieb-Filter
        tage_query = """
            SELECT COUNT(DISTINCT datum) 
            FROM werkstatt_leistung_daily
            WHERE datum >= ? AND datum <= ?
        """
        tage_params = [datum_von, datum_bis]
        if betrieb and betrieb != 'alle':
            betrieb_nr = int(betrieb)
            if betrieb_nr == 1:
                tage_query += " AND (betrieb_nr = 1 OR betrieb_nr IS NULL OR betrieb_nr = 0)"
            else:
                tage_query += " AND betrieb_nr = ?"
                tage_params.append(betrieb_nr)
        
        cursor.execute(tage_query, tage_params)
        anzahl_tage = cursor.fetchone()[0] or 0
        
        # Trend-Daten (letzte 14 Tage) - auch mit Betrieb-Filter
        trend_query = """
            SELECT 
                datum,
                ROUND(SUM(vorgabezeit_aw) * 6.0 / NULLIF(SUM(stempelzeit_min), 0) * 100, 1) as leistungsgrad
            FROM werkstatt_leistung_daily
            WHERE datum >= date('now', '-14 days')
        """
        trend_params = []
        if betrieb and betrieb != 'alle':
            betrieb_nr = int(betrieb)
            if betrieb_nr == 1:
                trend_query += " AND (betrieb_nr = 1 OR betrieb_nr IS NULL OR betrieb_nr = 0)"
            else:
                trend_query += " AND betrieb_nr = ?"
                trend_params.append(betrieb_nr)
        trend_query += " GROUP BY datum ORDER BY datum"
        
        cursor.execute(trend_query, trend_params)
        trend = [dict(row) for row in cursor.fetchall()]
        
        # SVS aus charge_types_sync holen (TAG 110)
        svs = 119.0  # Default
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='charge_types_sync'")
            if cursor.fetchone():
                betrieb_nr = 1 if betrieb == 'alle' or betrieb == '1,2' else int(betrieb)
                cursor.execute("SELECT stundensatz FROM charge_types_sync WHERE type = 10 AND subsidiary = ?", [betrieb_nr])
                row = cursor.fetchone()
                if row and row[0]:
                    svs = float(row[0])
        except:
            pass
        
        # Neue KPIs berechnen (TAG 110)
        gesamt_effizienz = round(gesamt_leistungsgrad * gesamt_produktivitaet / 100, 1) if gesamt_leistungsgrad and gesamt_produktivitaet else 0
        gesamt_stempelzeit_std = gesamt_stempelzeit / 60 if gesamt_stempelzeit else 0
        verlorene_std = gesamt_stempelzeit_std * (1 - gesamt_leistungsgrad / 100) if gesamt_leistungsgrad else 0
        entgangener_umsatz = verlorene_std * svs
        realisierter_svs = round(gesamt_umsatz / gesamt_stempelzeit_std, 2) if gesamt_stempelzeit_std > 0 and gesamt_umsatz else svs
        std_pro_durchgang = round(gesamt_stempelzeit_std / gesamt_auftraege, 2) if gesamt_auftraege > 0 else 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'zeitraum': {
                'von': datum_von,
                'bis': datum_bis,
                'label': zeitraum
            },
            'betrieb': betrieb,
            'mechaniker': mechaniker,
            'anzahl_mechaniker': len(mechaniker),
            'anzahl_tage': anzahl_tage,
            # Alte Felder (Kompatibilität)
            'gesamt_auftraege': gesamt_auftraege,
            'gesamt_stempelzeit': gesamt_stempelzeit,
            'gesamt_anwesenheit': gesamt_anwesenheit,
            'gesamt_aw': gesamt_aw,
            'gesamt_umsatz': gesamt_umsatz,
            'gesamt_leistungsgrad': gesamt_leistungsgrad,
            'gesamt_produktivitaet': gesamt_produktivitaet,
            'avg_std_pro_tag': round(gesamt_stempelzeit / anzahl_tage / 60, 1) if anzahl_tage > 0 else 0,
            'avg_auftraege_pro_tag': round(gesamt_auftraege / anzahl_tage, 1) if anzahl_tage > 0 else 0,
            # Neue KPIs (TAG 110)
            'gesamt': {
                'leistungsgrad': gesamt_leistungsgrad,
                'produktivitaet': gesamt_produktivitaet,
                'effizienz': gesamt_effizienz,
                'stempelzeit': gesamt_stempelzeit,
                'anwesenheit': gesamt_anwesenheit,
                'auftraege': gesamt_auftraege,
                'aw': gesamt_aw,
                'umsatz': round(gesamt_umsatz, 2),
                'svs': svs,
                'realisierter_svs': realisierter_svs,
                'verlorene_std': round(verlorene_std, 1),
                'entgangener_umsatz': round(entgangener_umsatz, 2),
                'std_pro_durchgang': std_pro_durchgang,
                'tage': anzahl_tage
            },
            'trend': trend
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_api.route('/mechaniker/<int:mechaniker_nr>', methods=['GET'])
def get_mechaniker_detail(mechaniker_nr):
    """
    GET /api/werkstatt/mechaniker/<nr>
    
    Returns: Detail-Daten für einen Mechaniker
    """
    try:
        zeitraum = request.args.get('zeitraum', 'monat')
        von = request.args.get('von')
        bis = request.args.get('bis')
        
        datum_von, datum_bis = get_date_range(zeitraum, von, bis)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Tages-Daten
        cursor.execute("""
            SELECT 
                datum,
                anzahl_auftraege as auftraege,
                stempelzeit_min as stempelzeit,
                vorgabezeit_aw as aw,
                leistungsgrad,
                umsatz
            FROM werkstatt_leistung_daily
            WHERE mechaniker_nr = ?
            AND datum >= ? AND datum <= ?
            ORDER BY datum DESC
        """, [mechaniker_nr, datum_von, datum_bis])
        tage = [dict(row) for row in cursor.fetchall()]
        
        # Aufträge
        cursor.execute("""
            SELECT 
                rechnungs_datum,
                rechnungs_nr,
                auftrags_nr,
                kennzeichen,
                summe_aw,
                summe_stempelzeit_min,
                leistungsgrad,
                lohn_netto
            FROM werkstatt_auftraege_abgerechnet
            WHERE rechnungs_datum >= ? AND rechnungs_datum <= ?
            ORDER BY rechnungs_datum DESC
            LIMIT 50
        """, [datum_von, datum_bis])
        auftraege = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'mechaniker_nr': mechaniker_nr,
            'tage': tage,
            'auftraege': auftraege
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_api.route('/schlechteste-auftraege', methods=['GET'])
def get_schlechteste_auftraege():
    """
    GET /api/werkstatt/schlechteste-auftraege
    
    Parameter:
    - zeitraum: heute|woche|monat|vormonat|quartal|jahr|custom
    - von/bis: bei custom
    - betrieb: alle|1|3
    - limit: Anzahl pro Mechaniker (default: 3)
    - min_stempelzeit: Mindest-Stempelzeit in Minuten (default: 30)
    
    Returns: Die schlechtesten Aufträge pro Mechaniker
    """
    try:
        zeitraum = request.args.get('zeitraum', 'monat')
        von = request.args.get('von')
        bis = request.args.get('bis')
        betrieb = request.args.get('betrieb', 'alle')
        limit = request.args.get('limit', 3, type=int)
        min_stempelzeit = request.args.get('min_stempelzeit', 30, type=int)
        
        datum_von, datum_bis = get_date_range(zeitraum, von, bis)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Alle Aufträge mit Mechaniker-Info aus labours
        # DISTINCT auf Auftrags-Nr um Duplikate zu vermeiden
        query = """
            WITH auftraege_mit_mechaniker AS (
                SELECT DISTINCT
                    a.rechnungs_datum,
                    a.rechnungs_nr,
                    a.auftrags_nr,
                    a.kennzeichen,
                    a.betrieb,
                    a.summe_aw,
                    a.summe_stempelzeit_min,
                    a.leistungsgrad,
                    a.lohn_netto,
                    l.mechanic_no as mechaniker_nr,
                    e.name as mechaniker_name
                FROM werkstatt_auftraege_abgerechnet a
                JOIN loco_labours l ON a.rechnungs_nr = l.invoice_number 
                    AND a.rechnungs_typ = l.invoice_type
                LEFT JOIN loco_employees e ON l.mechanic_no = e.employee_number 
                    AND e.is_latest_record = 1
                WHERE a.rechnungs_datum >= ? AND a.rechnungs_datum <= ?
                AND a.leistungsgrad IS NOT NULL
                AND a.leistungsgrad > 0
                AND a.leistungsgrad < 500
                AND a.summe_stempelzeit_min >= ?
                AND l.mechanic_no IS NOT NULL
                AND l.mechanic_no > 0
        """
        params = [datum_von, datum_bis, min_stempelzeit]
        
        if betrieb and betrieb != 'alle':
            query += " AND a.betrieb = ?"
            params.append(int(betrieb))
        
        query += """
            ),
            ranked AS (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY mechaniker_nr 
                        ORDER BY leistungsgrad ASC
                    ) as rang
                FROM auftraege_mit_mechaniker
            )
            SELECT 
                mechaniker_nr,
                mechaniker_name,
                rechnungs_datum,
                rechnungs_nr,
                auftrags_nr,
                kennzeichen,
                summe_aw,
                summe_stempelzeit_min,
                leistungsgrad,
                lohn_netto,
                rang
            FROM ranked
            WHERE rang <= ?
            ORDER BY mechaniker_name, rang
        """
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Gruppieren nach Mechaniker
        mechaniker_auftraege = {}
        for row in rows:
            mech_nr = row['mechaniker_nr']
            if mech_nr not in mechaniker_auftraege:
                mechaniker_auftraege[mech_nr] = {
                    'mechaniker_nr': mech_nr,
                    'mechaniker_name': row['mechaniker_name'],
                    'auftraege': []
                }
            mechaniker_auftraege[mech_nr]['auftraege'].append({
                'rang': row['rang'],
                'datum': row['rechnungs_datum'],
                'rechnungs_nr': row['rechnungs_nr'],
                'auftrags_nr': row['auftrags_nr'],
                'kennzeichen': row['kennzeichen'],
                'aw': row['summe_aw'],
                'stempelzeit': row['summe_stempelzeit_min'],
                'leistungsgrad': row['leistungsgrad'],
                'lohn': row['lohn_netto']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'zeitraum': {'von': datum_von, 'bis': datum_bis},
            'min_stempelzeit': min_stempelzeit,
            'limit_pro_mechaniker': limit,
            'mechaniker': list(mechaniker_auftraege.values())
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@werkstatt_api.route('/trend', methods=['GET'])
def get_trend():
    """
    GET /api/werkstatt/trend
    
    Parameter:
    - tage: Anzahl Tage zurück (default: 30)
    - betrieb: alle|1|3
    
    Returns: Täglicher Leistungsgrad-Trend
    """
    try:
        tage = request.args.get('tage', 30, type=int)
        betrieb = request.args.get('betrieb', 'alle')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                datum,
                COUNT(DISTINCT mechaniker_nr) as mechaniker,
                SUM(anzahl_auftraege) as auftraege,
                SUM(stempelzeit_min) as stempelzeit,
                SUM(vorgabezeit_aw) as aw,
                ROUND(SUM(vorgabezeit_aw) * 6.0 / NULLIF(SUM(stempelzeit_min), 0) * 100, 1) as leistungsgrad
            FROM werkstatt_leistung_daily
            WHERE datum >= date('now', ?)
        """
        params = [f'-{tage} days']
        
        if betrieb and betrieb != 'alle':
            betrieb_nr = int(betrieb)
            if betrieb_nr == 1:
                query += " AND (betrieb_nr = 1 OR betrieb_nr IS NULL OR betrieb_nr = 0)"
            else:
                query += " AND betrieb_nr = ?"
                params.append(betrieb_nr)
        
        query += " GROUP BY datum ORDER BY datum"
        
        cursor.execute(query, params)
        trend = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'trend': trend
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_api.route('/health', methods=['GET'])
def health_check():
    """Health Check Endpoint"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM werkstatt_leistung_daily")
        count_daily = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM werkstatt_auftraege_abgerechnet")
        count_auftraege = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(datum) FROM werkstatt_leistung_daily")
        last_date = cursor.fetchone()[0]
        
        # Prüfe ob betrieb_nr Spalte existiert
        cursor.execute("PRAGMA table_info(werkstatt_leistung_daily)")
        columns = [r[1] for r in cursor.fetchall()]
        has_betrieb = 'betrieb_nr' in columns
        
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'werkstatt_leistung_daily': count_daily,
            'werkstatt_auftraege_abgerechnet': count_auftraege,
            'last_sync': last_date,
            'betrieb_filter_available': has_betrieb
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
