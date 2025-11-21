"""
Bankenspiegel REST API - FIXED VERSION
========================================
Kompatibel mit ECHTEM DB-Schema (TAG 71 Fix)

Änderungen:
- Verwendet echte Spaltennamen (id statt konto_id, letztes_update statt stand_datum)
- Nutzt existierende View v_aktuelle_kontostaende
- Keine nicht-existierenden Views mehr
- Direkte Queries auf Tabellen

Fixed: 21.11.2025
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any

# Blueprint erstellen
bankenspiegel_api = Blueprint('bankenspiegel_api', __name__, url_prefix='/api/bankenspiegel')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_db():
    """Datenbank-Verbindung herstellen"""
    conn = sqlite3.connect('data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row: sqlite3.Row) -> Dict:
    """Konvertiert sqlite3.Row zu Dictionary"""
    return dict(row) if row else None

def rows_to_list(rows: List[sqlite3.Row]) -> List[Dict]:
    """Konvertiert Liste von sqlite3.Row zu Liste von Dicts"""
    return [dict(row) for row in rows]

# ============================================================================
# ENDPOINT 1: DASHBOARD
# ============================================================================

@bankenspiegel_api.route('/dashboard', methods=['GET'])
def get_dashboard():
    """
    GET /api/bankenspiegel/dashboard
    Dashboard-KPIs
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 1. Gesamtsaldo (aus v_aktuelle_kontostaende View)
        cursor.execute("""
            SELECT
                COUNT(*) as anzahl_konten,
                SUM(saldo) as gesamtsaldo,
                MIN(letztes_update) as aeltester_stand,
                MAX(letztes_update) as neuester_stand
            FROM v_aktuelle_kontostaende
        """)
        saldo_data = row_to_dict(cursor.fetchone())

        # 2. Transaktionen letzte 30 Tage (OHNE INTERNE TRANSFERS)
        cursor.execute("""
            SELECT
                COUNT(*) as anzahl,
                SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END) as einnahmen,
                SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END) as ausgaben
            FROM transaktionen
            WHERE buchungsdatum >= DATE('now', '-30 days')
              AND NOT (
                verwendungszweck LIKE '%Autohaus Greiner%Autohaus Greiner%'
                OR verwendungszweck LIKE '%Umbuchung%'
                OR verwendungszweck LIKE '%Einlage%'
                OR verwendungszweck LIKE '%Rückzahlung Einlage%'
              )
        """)
        trans_30d = row_to_dict(cursor.fetchone())

        # 2b. Interne Transfers (SEPARAT)
        cursor.execute("""
            SELECT
                COUNT(*) as anzahl,
                SUM(ABS(betrag)) as volumen
            FROM transaktionen
            WHERE buchungsdatum >= DATE('now', '-30 days')
              AND (
                verwendungszweck LIKE '%Autohaus Greiner%Autohaus Greiner%'
                OR verwendungszweck LIKE '%Umbuchung%'
                OR verwendungszweck LIKE '%Einlage%'
                OR verwendungszweck LIKE '%Rückzahlung Einlage%'
              )
        """)
        interne_30d = row_to_dict(cursor.fetchone())

        # 3. Aktueller Monat
        aktueller_monat = date.today().strftime('%Y-%m')
        cursor.execute("""
            SELECT
                SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END) as einnahmen,
                SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END) as ausgaben,
                SUM(betrag) as saldo,
                COUNT(*) as anzahl
            FROM transaktionen
            WHERE strftime('%Y-%m', buchungsdatum) = ?
        """, (aktueller_monat,))
        monat_data = row_to_dict(cursor.fetchone())

        # 4. Top 5 Ausgaben-Kategorien (aktueller Monat)
        cursor.execute("""
            SELECT
                kategorie,
                COUNT(*) as anzahl,
                SUM(ABS(betrag)) as summe
            FROM transaktionen
            WHERE buchungsdatum >= DATE('now', 'start of month')
            AND betrag < 0
            AND kategorie IS NOT NULL
            AND NOT (
                verwendungszweck LIKE '%Autohaus Greiner%Autohaus Greiner%'
                OR verwendungszweck LIKE '%Umbuchung%'
            )
            GROUP BY kategorie
            ORDER BY summe DESC
            LIMIT 5
        """)
        top_kategorien = rows_to_list(cursor.fetchall())

        # 5. Anzahl Banken
        cursor.execute("SELECT COUNT(*) as anzahl FROM banken WHERE aktiv = 1")
        anzahl_banken = cursor.fetchone()['anzahl']

        conn.close()

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'dashboard': {
                'gesamtsaldo': round(saldo_data['gesamtsaldo'] or 0, 2),
                'anzahl_konten': saldo_data['anzahl_konten'] or 0,
                'anzahl_banken': anzahl_banken,
                'neuester_stand': saldo_data['neuester_stand'],
                'letzte_30_tage': {
                    'anzahl_transaktionen': trans_30d['anzahl'] or 0,
                    'einnahmen': round(trans_30d['einnahmen'] or 0, 2),
                    'ausgaben': round(trans_30d['ausgaben'] or 0, 2),
                    'saldo': round((trans_30d['einnahmen'] or 0) - (trans_30d['ausgaben'] or 0), 2)
                },
                'interne_transfers_30_tage': {
                    'anzahl_transaktionen': interne_30d['anzahl'] or 0,
                    'volumen': round(interne_30d['volumen'] or 0, 2)
                },
                'aktueller_monat': {
                    'monat': aktueller_monat,
                    'einnahmen': round(monat_data['einnahmen'] or 0, 2),
                    'ausgaben': round(monat_data['ausgaben'] or 0, 2),
                    'saldo': round(monat_data['saldo'] or 0, 2),
                    'anzahl_transaktionen': monat_data['anzahl'] or 0
                },
                'top_kategorien': top_kategorien
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT 2: KONTEN
# ============================================================================

@bankenspiegel_api.route('/konten', methods=['GET'])
def get_konten():
    """
    GET /api/bankenspiegel/konten?bank_id=1
    Kontenliste mit Salden
    """
    try:
        bank_id = request.args.get('bank_id', type=int)

        conn = get_db()
        cursor = conn.cursor()

        # Query - verwendet v_aktuelle_kontostaende mit ECHTEN Spaltennamen
        query = """
            SELECT
                id,
                bank_name,
                kontoname,
                iban,
                kontotyp,
                'EUR' as waehrung,
                saldo,
                letztes_update as stand_datum,
                1 as aktiv
            FROM v_aktuelle_kontostaende
            WHERE 1=1
        """

        params = []

        # Filter nach Bank
        if bank_id:
            query += " AND bank_id = ?"
            params.append(bank_id)

        query += " ORDER BY CASE WHEN kontotyp = 'Girokonto' THEN 0 ELSE 1 END, bank_name, kontoname"

        cursor.execute(query, params)
        konten = rows_to_list(cursor.fetchall())

        # Statistik
        gesamtsaldo = sum(k['saldo'] or 0 for k in konten)

        conn.close()

        return jsonify({
            'success': True,
            'konten': konten,
            'count': len(konten),
            'gesamtsaldo': round(gesamtsaldo, 2)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT 3: TRANSAKTIONEN
# ============================================================================

@bankenspiegel_api.route('/transaktionen', methods=['GET'])
def get_transaktionen():
    """
    GET /api/bankenspiegel/transaktionen?konto_id=1&von=2025-01-01&bis=2025-12-31
    Transaktionsliste mit Filtern
    """
    try:
        # Parameter auslesen
        konto_id = request.args.get('konto_id', type=int)
        bank_id = request.args.get('bank_id', type=int)
        von = request.args.get('von')
        bis = request.args.get('bis')
        kategorie = request.args.get('kategorie')
        betrag_min = request.args.get('betrag_min', type=float)
        betrag_max = request.args.get('betrag_max', type=float)
        suche = request.args.get('suche')
        limit = min(request.args.get('limit', default=100, type=int), 1000)
        offset = request.args.get('offset', default=0, type=int)
        order = request.args.get('order', default='desc')

        conn = get_db()
        cursor = conn.cursor()

        # Query aufbauen - direkt auf Tabellen
        query = """
            SELECT
                t.id,
                b.bank_name,
                t.konto_id,
                k.kontoname,
                k.iban,
                t.buchungsdatum,
                t.valutadatum,
                t.buchungstext,
                t.verwendungszweck,
                t.betrag,
                t.waehrung,
                t.kategorie,
                t.steuerrelevant,
                t.import_datei as pdf_quelle,
                t.saldo_nach_buchung
            FROM transaktionen t
            JOIN konten k ON t.konto_id = k.id
            JOIN banken b ON k.bank_id = b.id
            WHERE 1=1
        """
        params = []

        # Filter anwenden
        if konto_id:
            query += " AND t.konto_id = ?"
            params.append(konto_id)

        if bank_id:
            query += " AND k.bank_id = ?"
            params.append(bank_id)

        if von:
            query += " AND t.buchungsdatum >= ?"
            params.append(von)

        if bis:
            query += " AND t.buchungsdatum <= ?"
            params.append(bis)

        if kategorie:
            query += " AND t.kategorie = ?"
            params.append(kategorie)

        if betrag_min is not None:
            query += " AND t.betrag >= ?"
            params.append(betrag_min)

        if betrag_max is not None:
            query += " AND t.betrag <= ?"
            params.append(betrag_max)

        if suche:
            query += " AND (t.buchungstext LIKE ? OR t.verwendungszweck LIKE ?)"
            search_term = f"%{suche}%"
            params.extend([search_term, search_term])

        # Sortierung
        order_dir = 'DESC' if order.lower() == 'desc' else 'ASC'
        query += f" ORDER BY t.buchungsdatum {order_dir}, t.id {order_dir}"

        # Limit & Offset
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        transaktionen = rows_to_list(cursor.fetchall())

        # Gesamt-Anzahl
        count_query = "SELECT COUNT(*) as total FROM transaktionen t JOIN konten k ON t.konto_id = k.id WHERE 1=1"
        count_params = []

        if konto_id:
            count_query += " AND t.konto_id = ?"
            count_params.append(konto_id)
        if bank_id:
            count_query += " AND k.bank_id = ?"
            count_params.append(bank_id)
        if von:
            count_query += " AND t.buchungsdatum >= ?"
            count_params.append(von)
        if bis:
            count_query += " AND t.buchungsdatum <= ?"
            count_params.append(bis)
        if kategorie:
            count_query += " AND t.kategorie = ?"
            count_params.append(kategorie)
        if betrag_min is not None:
            count_query += " AND t.betrag >= ?"
            count_params.append(betrag_min)
        if betrag_max is not None:
            count_query += " AND t.betrag <= ?"
            count_params.append(betrag_max)
        if suche:
            count_query += " AND (t.buchungstext LIKE ? OR t.verwendungszweck LIKE ?)"
            search_term = f"%{suche}%"
            count_params.extend([search_term, search_term])

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']

        # Statistik
        stats_query = """
            SELECT
                SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END) as summe_einnahmen,
                SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END) as summe_ausgaben,
                SUM(betrag) as saldo
            FROM transaktionen t
            JOIN konten k ON t.konto_id = k.id
            WHERE 1=1
        """
        stats_params = []

        if konto_id:
            stats_query += " AND t.konto_id = ?"
            stats_params.append(konto_id)
        if bank_id:
            stats_query += " AND k.bank_id = ?"
            stats_params.append(bank_id)
        if von:
            stats_query += " AND t.buchungsdatum >= ?"
            stats_params.append(von)
        if bis:
            stats_query += " AND t.buchungsdatum <= ?"
            stats_params.append(bis)
        if kategorie:
            stats_query += " AND t.kategorie = ?"
            stats_params.append(kategorie)
        if betrag_min is not None:
            stats_query += " AND t.betrag >= ?"
            stats_params.append(betrag_min)
        if betrag_max is not None:
            stats_query += " AND t.betrag <= ?"
            stats_params.append(betrag_max)
        if suche:
            stats_query += " AND (t.buchungstext LIKE ? OR t.verwendungszweck LIKE ?)"
            search_term = f"%{suche}%"
            stats_params.extend([search_term, search_term])

        cursor.execute(stats_query, stats_params)
        stats = cursor.fetchone()

        conn.close()

        return jsonify({
            'success': True,
            'transaktionen': transaktionen,
            'pagination': {
                'count': len(transaktionen),
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total
            },
            'statistik': {
                'einnahmen': round(stats['summe_einnahmen'] or 0, 2),
                'ausgaben': round(stats['summe_ausgaben'] or 0, 2),
                'saldo': round(stats['saldo'] or 0, 2)
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT 4: EINKAUFSFINANZIERUNG
# ============================================================================

@bankenspiegel_api.route('/einkaufsfinanzierung', methods=['GET'])
def get_einkaufsfinanzierung():
    """
    GET /api/bankenspiegel/einkaufsfinanzierung
    Einkaufsfinanzierung - Übersicht
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Gesamt-Übersicht
        cursor.execute("""
            SELECT
                COUNT(*) as anzahl_fahrzeuge,
                SUM(aktueller_saldo) as gesamt_finanzierung,
                SUM(original_betrag) as gesamt_original,
                SUM(original_betrag - aktueller_saldo) as gesamt_abbezahlt
            FROM fahrzeugfinanzierungen
        """)
        gesamt_row = cursor.fetchone()

        # Institute
        cursor.execute("""
            SELECT DISTINCT finanzinstitut
            FROM fahrzeugfinanzierungen
            ORDER BY finanzinstitut
        """)
        institute_liste = [row['finanzinstitut'] for row in cursor.fetchall()]

        institute = []
        for institut in institute_liste:
            cursor.execute("""
                SELECT
                    COUNT(*) as anzahl,
                    SUM(aktueller_saldo) as finanzierung,
                    SUM(original_betrag) as original,
                    AVG(aktueller_saldo) as durchschnitt,
                    MAX(alter_tage) as aeltestes_fahrzeug,
                    MIN(zinsfreiheit_tage) as min_zinsfreiheit,
                    SUM(original_betrag - aktueller_saldo) as abbezahlt
                FROM fahrzeugfinanzierungen
                WHERE finanzinstitut = ?
            """, (institut,))
            stats = cursor.fetchone()

            cursor.execute("""
                SELECT
                    rrdi,
                    COUNT(*) as anzahl,
                    SUM(aktueller_saldo) as finanzierung
                FROM fahrzeugfinanzierungen
                WHERE finanzinstitut = ?
                GROUP BY rrdi
                ORDER BY anzahl DESC
            """, (institut,))
            marken = rows_to_list(cursor.fetchall())

            institute.append({
                'name': institut,
                'anzahl': stats['anzahl'],
                'finanzierung': float(stats['finanzierung']) if stats['finanzierung'] else 0,
                'original': float(stats['original']) if stats['original'] else 0,
                'durchschnitt': float(stats['durchschnitt']) if stats['durchschnitt'] else 0,
                'marken': marken
            })

        conn.close()

        return jsonify({
            'success': True,
            'gesamt': {
                'anzahl_fahrzeuge': gesamt_row['anzahl_fahrzeuge'],
                'finanzierung': float(gesamt_row['gesamt_finanzierung']) if gesamt_row['gesamt_finanzierung'] else 0,
                'original': float(gesamt_row['gesamt_original']) if gesamt_row['gesamt_original'] else 0,
                'abbezahlt': float(gesamt_row['gesamt_abbezahlt']) if gesamt_row['gesamt_abbezahlt'] else 0
            },
            'institute': institute,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT 5: FAHRZEUGE MIT ZINSEN
# ============================================================================

@bankenspiegel_api.route('/fahrzeuge-mit-zinsen', methods=['GET'])
def get_fahrzeuge_mit_zinsen():
    """
    GET /api/bankenspiegel/fahrzeuge-mit-zinsen
    Fahrzeuge mit Zinsen
    """
    try:
        conn = get_db()
        c = conn.cursor()

        status = request.args.get('status', 'zinsen_laufen')
        institut = request.args.get('institut', 'alle')
        limit = int(request.args.get('limit', 100))

        query = "SELECT * FROM fahrzeuge_mit_zinsen WHERE 1=1"
        params = []

        if status == 'zinsen_laufen':
            query += " AND zinsstatus = 'Zinsen laufen'"
        elif status == 'warnung':
            query += " AND zinsstatus LIKE '%Warnung%'"

        if institut != 'alle':
            query += " AND finanzinstitut = ?"
            params.append(institut)

        query += " ORDER BY zinsen_gesamt DESC LIMIT ?"
        params.append(limit)

        c.execute(query, params)
        columns = [description[0] for description in c.description]
        rows = c.fetchall()

        fahrzeuge = [dict(zip(columns, row)) for row in rows]

        gesamt_saldo = sum(f.get('aktueller_saldo') or 0 for f in fahrzeuge)
        gesamt_zinsen = sum(f.get('zinsen_gesamt') or 0 for f in fahrzeuge)

        conn.close()

        return jsonify({
            'success': True,
            'fahrzeuge': fahrzeuge,
            'statistik': {
                'anzahl_fahrzeuge': len(fahrzeuge),
                'gesamt_saldo': round(gesamt_saldo, 2),
                'gesamt_zinsen': round(gesamt_zinsen, 2) if gesamt_zinsen > 0 else None
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT 6: KONTO SNAPSHOTS
# ============================================================================

@bankenspiegel_api.route('/konto/<int:konto_id>/snapshots')
def get_konto_snapshots(konto_id):
    """Historische Snapshots für ein Konto"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT k.kontoname, k.iban, k.kreditlinie, b.bank_name
            FROM konten k
            JOIN banken b ON k.bank_id = b.id
            WHERE k.id = ?
        ''', (konto_id,))

        konto_row = cursor.fetchone()
        if not konto_row:
            conn.close()
            return jsonify({'error': 'Konto nicht gefunden'}), 404

        konto_info = dict(konto_row)

        cursor.execute('''
            SELECT
                stichtag,
                kapitalsaldo,
                kreditlinie,
                zinssatz,
                ausnutzung_prozent,
                zinstyp
            FROM konto_snapshots
            WHERE konto_id = ?
            ORDER BY stichtag ASC
        ''', (konto_id,))

        snapshots = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return jsonify({
            'konto': {
                'id': konto_id,
                'name': konto_info['kontoname'],
                'iban': konto_info['iban'],
                'kreditlinie': konto_info['kreditlinie'],
                'bank': konto_info['bank_name']
            },
            'snapshots': snapshots,
            'count': len(snapshots)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@bankenspiegel_api.route('/health', methods=['GET'])
def health_check():
    """API Health Check"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM banken")
        banken_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM konten")
        konten_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM transaktionen")
        trans_count = cursor.fetchone()['count']

        conn.close()

        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': {
                'connected': True,
                'banken': banken_count,
                'konten': konten_count,
                'transaktionen': trans_count
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500
