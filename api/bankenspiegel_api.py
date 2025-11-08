"""
Bankenspiegel REST API
Hybrid-Ansatz - Inspiriert von Urlaubsplaner V2

Blueprint für alle Bankenspiegel-Endpoints
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
    conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row  # Dict-ähnlicher Zugriff
    return conn


def row_to_dict(row: sqlite3.Row) -> Dict:
    """Konvertiert sqlite3.Row zu Dictionary"""
    return dict(row) if row else None


def rows_to_list(rows: List[sqlite3.Row]) -> List[Dict]:
    """Konvertiert Liste von sqlite3.Row zu Liste von Dicts"""
    return [dict(row) for row in rows]


# ============================================================================
# ENDPOINT 1: DASHBOARD (KPIs & Übersicht)
# ============================================================================

@bankenspiegel_api.route('/dashboard', methods=['GET'])
def get_dashboard():
    """
    GET /api/bankenspiegel/dashboard
    
    Gibt Dashboard-KPIs zurück:
    - Gesamtsaldo aller Konten
    - Anzahl aktiver Konten
    - Anzahl Transaktionen (letzte 30 Tage)
    - Monatliche Umsätze (aktueller Monat)
    - Top 5 Ausgaben-Kategorien
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # 1. Gesamtsaldo (aus v_aktuelle_kontostaende View)
        cursor.execute("""
            SELECT 
                COUNT(*) as anzahl_konten,
                SUM(saldo) as gesamtsaldo,
                MIN(stand_datum) as aeltester_stand,
                MAX(stand_datum) as neuester_stand
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
                OR (verwendungszweck LIKE '%PN:801%' AND verwendungszweck LIKE '%Autohaus Greiner%')
              )
        """)
        trans_30d = row_to_dict(cursor.fetchone())
        
        # 2b. Interne Transfers der letzten 30 Tage (SEPARAT)
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
                OR (verwendungszweck LIKE '%PN:801%' AND verwendungszweck LIKE '%Autohaus Greiner%')
              )
        """)
        interne_30d = row_to_dict(cursor.fetchone())
        
        # 3. Aktueller Monat (aus v_monatliche_umsaetze View)
        aktueller_monat = date.today().strftime('%Y-%m')
        cursor.execute("""
            SELECT 
                SUM(einnahmen) as einnahmen,
                SUM(ausgaben) as ausgaben,
                SUM(saldo) as saldo,
                SUM(anzahl_transaktionen) as anzahl
            FROM v_monatliche_umsaetze
            WHERE monat = ?
        """, (aktueller_monat,))
        monat_data = row_to_dict(cursor.fetchone())
        
        # 4. Top 5 Ausgaben-Kategorien (aktueller Monat, OHNE INTERNE TRANSFERS)
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
                OR verwendungszweck LIKE '%Einlage%'
                OR verwendungszweck LIKE '%Rückzahlung Einlage%'
                OR (verwendungszweck LIKE '%PN:801%' AND verwendungszweck LIKE '%Autohaus Greiner%')
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
                    'volumen': round(interne_30d['volumen'] or 0, 2),
                    'hinweis': 'Interne Umbuchungen zwischen eigenen Konten (nicht in Umsätzen gezählt)'
                },
                'aktueller_monat': {
                    'monat': aktueller_monat,
                    'einnahmen': round(monat_data['einnahmen'] or 0, 2) if monat_data['einnahmen'] else 0,
                    'ausgaben': round(monat_data['ausgaben'] or 0, 2) if monat_data['ausgaben'] else 0,
                    'saldo': round(monat_data['saldo'] or 0, 2) if monat_data['saldo'] else 0,
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
# ENDPOINT 2: KONTEN (Kontenliste mit Salden)
# ============================================================================

@bankenspiegel_api.route('/konten', methods=['GET'])
def get_konten():
    """
    GET /api/bankenspiegel/konten?bank_id=1&aktiv=1
    
    Gibt Liste aller Konten mit aktuellem Saldo zurück
    
    Query-Parameter:
    - bank_id: Filter nach Bank-ID (optional)
    - aktiv: Filter nach aktiv (1) oder inaktiv (0) (optional, default: 1)
    """
    try:
        bank_id = request.args.get('bank_id', type=int)
        aktiv = request.args.get('aktiv', default=1, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Query mit optionalen Filtern
        query = """
            SELECT 
                konto_id,
                bank_name,
                kontoname,
                iban,
                kontotyp,
                waehrung,
                saldo,
                stand_datum,
                aktiv
            FROM v_aktuelle_kontostaende
            WHERE 1=1
        """
        params = []
        
        if aktiv is not None:
            query += " AND aktiv = ?"
            params.append(aktiv)
        
        if bank_id:
            # Filter nach Bank über Subquery
            query = """
                SELECT 
                    konto_id,
                    bank_name,
                    kontoname,
                    iban,
                    kontotyp,
                    waehrung,
                    saldo,
                    stand_datum,
                    aktiv
                FROM v_aktuelle_kontostaende
                WHERE konto_id IN (SELECT id FROM konten WHERE bank_id = ?)
            """
            params = [bank_id]
            
            if aktiv is not None:
                query += " AND aktiv = ?"
                params.append(aktiv)
        
        query += " ORDER BY bank_name, kontoname"
        
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
# ENDPOINT 3: TRANSAKTIONEN (Filterbare Liste)
# ============================================================================

@bankenspiegel_api.route('/transaktionen', methods=['GET'])
def get_transaktionen():
    """
    GET /api/bankenspiegel/transaktionen?konto_id=1&von=2025-01-01&bis=2025-12-31&limit=100
    
    Gibt Transaktionsliste zurück mit Filtern
    
    Query-Parameter:
    - konto_id: Filter nach Konto-ID (optional)
    - bank_id: Filter nach Bank-ID (optional)
    - von: Start-Datum (optional, format: YYYY-MM-DD)
    - bis: End-Datum (optional, format: YYYY-MM-DD)
    - kategorie: Filter nach Kategorie (optional)
    - betrag_min: Mindestbetrag (optional)
    - betrag_max: Maximalbetrag (optional)
    - suche: Volltext-Suche in buchungstext/verwendungszweck (optional)
    - limit: Max. Anzahl Ergebnisse (default: 100, max: 1000)
    - offset: Offset für Pagination (default: 0)
    - order: Sortierung 'asc' oder 'desc' (default: desc)
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
        
        # Query aufbauen (nutzt v_transaktionen_uebersicht View)
        query = """
            SELECT 
                id,
                bank_name,
                konto_id,
                kontoname,
                iban,
                buchungsdatum,
                valutadatum,
                buchungstext,
                verwendungszweck,
                betrag,
                waehrung,
                kategorie,
                steuerrelevant,
                pdf_quelle,
                saldo_nach_buchung
            FROM v_transaktionen_uebersicht
            WHERE 1=1
        """
        params = []
        
        # Filter anwenden
        if konto_id:
            query += " AND konto_id = ?"
            params.append(konto_id)
        
        if bank_id:
            query += " AND bank_name IN (SELECT bank_name FROM banken WHERE id = ?)"
            params.append(bank_id)
        
        if von:
            query += " AND buchungsdatum >= ?"
            params.append(von)
        
        if bis:
            query += " AND buchungsdatum <= ?"
            params.append(bis)
        
        if kategorie:
            query += " AND kategorie = ?"
            params.append(kategorie)
        
        if betrag_min is not None:
            query += " AND betrag >= ?"
            params.append(betrag_min)
        
        if betrag_max is not None:
            query += " AND betrag <= ?"
            params.append(betrag_max)
        
        if suche:
            query += " AND (buchungstext LIKE ? OR verwendungszweck LIKE ?)"
            search_term = f"%{suche}%"
            params.extend([search_term, search_term])
        
        # Sortierung
        order_dir = 'DESC' if order.lower() == 'desc' else 'ASC'
        query += f" ORDER BY buchungsdatum {order_dir}, id {order_dir}"
        
        # Limit & Offset
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        transaktionen = rows_to_list(cursor.fetchall())
        
        # Gesamt-Anzahl ermitteln (für Pagination)
        count_query = """
            SELECT COUNT(*) as total
            FROM v_transaktionen_uebersicht
            WHERE 1=1
        """
        count_params = []
        
        # Gleiche Filter wie oben
        if konto_id:
            count_query += " AND konto_id = ?"
            count_params.append(konto_id)
        if bank_id:
            count_query += " AND bank_name IN (SELECT bank_name FROM banken WHERE id = ?)"
            count_params.append(bank_id)
        if von:
            count_query += " AND buchungsdatum >= ?"
            count_params.append(von)
        if bis:
            count_query += " AND buchungsdatum <= ?"
            count_params.append(bis)
        if kategorie:
            count_query += " AND kategorie = ?"
            count_params.append(kategorie)
        if betrag_min is not None:
            count_query += " AND betrag >= ?"
            count_params.append(betrag_min)
        if betrag_max is not None:
            count_query += " AND betrag <= ?"
            count_params.append(betrag_max)
        if suche:
            count_query += " AND (buchungstext LIKE ? OR verwendungszweck LIKE ?)"
            search_term = f"%{suche}%"
            count_params.extend([search_term, search_term])
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']
        
        # Statistik über gefilterte Transaktionen
        if transaktionen:
            summe_einnahmen = sum(t['betrag'] for t in transaktionen if t['betrag'] > 0)
            summe_ausgaben = sum(abs(t['betrag']) for t in transaktionen if t['betrag'] < 0)
            saldo = summe_einnahmen - summe_ausgaben
        else:
            summe_einnahmen = 0
            summe_ausgaben = 0
            saldo = 0
        
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
                'einnahmen': round(summe_einnahmen, 2),
                'ausgaben': round(summe_ausgaben, 2),
                'saldo': round(saldo, 2)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@bankenspiegel_api.route('/health', methods=['GET'])
def health_check():
    """
    GET /api/bankenspiegel/health
    
    Prüft API-Status und Datenbank-Verbindung
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Prüfe DB-Zugriff
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

# ============================================================================
# EINKAUFSFINANZIERUNG ENDPOINT
# ============================================================================
@bankenspiegel_api.route('/einkaufsfinanzierung', methods=['GET'])
def get_einkaufsfinanzierung():
    """
    GET /api/bankenspiegel/einkaufsfinanzierung
    Einkaufsfinanzierung - Übersicht Stellantis & Santander
    
    Returns:
        JSON mit:
        - gesamt: Gesamt-Statistik
        - institute: Liste mit Daten pro Institut
        - top_fahrzeuge: Teuerste Fahrzeuge
        - warnungen: Zinsfreiheit-Warnungen
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # 1. GESAMT-ÜBERSICHT
        cursor.execute("""
            SELECT
                COUNT(*) as anzahl_fahrzeuge,
                SUM(aktueller_saldo) as gesamt_finanzierung,
                SUM(original_betrag) as gesamt_original,
                SUM(original_betrag - aktueller_saldo) as gesamt_abbezahlt
            FROM fahrzeugfinanzierungen
        """)
        gesamt_row = cursor.fetchone()
        
        # 2. DATEN PRO INSTITUT
        cursor.execute("""
            SELECT DISTINCT finanzinstitut 
            FROM fahrzeugfinanzierungen 
            ORDER BY finanzinstitut
        """)
        institute_liste = [row['finanzinstitut'] for row in cursor.fetchall()]
        
        institute = []
        for institut in institute_liste:
            # Statistik pro Institut
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
            
            # Marken-Verteilung
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
            marken = []
            for row in cursor.fetchall():
                marke_name = row['rrdi'] if row['rrdi'] else "Unbekannt"
                # Vereinfachung für Stellantis
                if institut == 'Stellantis':
                    if "0154X" in str(marke_name):
                        marke_name = "Leapmotor"
                    else:
                        marke_name = "Opel/Hyundai"
                
                marken.append({
                    'name': marke_name,
                    'anzahl': row['anzahl'],
                    'finanzierung': float(row['finanzierung']) if row['finanzierung'] else 0
                })
            
            institute.append({
                'name': institut,
                'anzahl': stats['anzahl'],
                'finanzierung': float(stats['finanzierung']) if stats['finanzierung'] else 0,
                'original': float(stats['original']) if stats['original'] else 0,
                'durchschnitt': float(stats['durchschnitt']) if stats['durchschnitt'] else 0,
                'aeltestes': stats['aeltestes_fahrzeug'],
                'min_zinsfreiheit': stats['min_zinsfreiheit'],
                'abbezahlt': float(stats['abbezahlt']) if stats['abbezahlt'] else 0,
                'marken': marken
            })
        
        # 3. TOP 10 TEUERSTE FAHRZEUGE
        cursor.execute("""
            SELECT
                finanzinstitut,
                vin,
                modell,
                rrdi,
                aktueller_saldo,
                original_betrag,
                alter_tage,
                zinsfreiheit_tage
            FROM fahrzeugfinanzierungen
            ORDER BY aktueller_saldo DESC
            LIMIT 10
        """)
        
        top_fahrzeuge = []
        for row in cursor.fetchall():
            top_fahrzeuge.append({
                'institut': row['finanzinstitut'],
                'vin': row['vin'][-8:] if row['vin'] else '???',
                'modell': row['modell'],
                'marke': row['rrdi'],
                'saldo': float(row['aktueller_saldo']) if row['aktueller_saldo'] else 0,
                'original': float(row['original_betrag']) if row['original_betrag'] else 0,
                'alter': row['alter_tage'],
                'zinsfreiheit': row['zinsfreiheit_tage']
            })
        
        # 4. ZINSFREIHEIT-WARNUNGEN (< 30 Tage)
        cursor.execute("""
            SELECT
                finanzinstitut,
                vin,
                modell,
                rrdi,
                zinsfreiheit_tage,
                aktueller_saldo,
                alter_tage
            FROM fahrzeugfinanzierungen
            WHERE zinsfreiheit_tage IS NOT NULL
            AND zinsfreiheit_tage < 30
            ORDER BY zinsfreiheit_tage ASC
        """)
        
        warnungen = []
        for row in cursor.fetchall():
            warnungen.append({
                'institut': row['finanzinstitut'],
                'vin': row['vin'][-8:] if row['vin'] else '???',
                'modell': row['modell'],
                'marke': row['rrdi'],
                'tage_uebrig': row['zinsfreiheit_tage'],
                'saldo': float(row['aktueller_saldo']) if row['aktueller_saldo'] else 0,
                'alter': row['alter_tage'],
                'kritisch': row['zinsfreiheit_tage'] < 15 if row['zinsfreiheit_tage'] else False
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'gesamt': {
                'anzahl_fahrzeuge': gesamt_row['anzahl_fahrzeuge'],
                'finanzierung': float(gesamt_row['gesamt_finanzierung']) if gesamt_row['gesamt_finanzierung'] else 0,
                'original': float(gesamt_row['gesamt_original']) if gesamt_row['gesamt_original'] else 0,
                'abbezahlt': float(gesamt_row['gesamt_abbezahlt']) if gesamt_row['gesamt_abbezahlt'] else 0,
                'abbezahlt_prozent': round(gesamt_row['gesamt_abbezahlt'] / gesamt_row['gesamt_original'] * 100, 1) if gesamt_row['gesamt_original'] else 0
            },
            'institute': institute,
            'top_fahrzeuge': top_fahrzeuge,
            'warnungen': warnungen,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# FAHRZEUGE MIT ZINSEN
# ============================================================================

@bankenspiegel_api.route('/fahrzeuge-mit-zinsen', methods=['GET'])
def get_fahrzeuge_mit_zinsen():
    """
    GET /api/bankenspiegel/fahrzeuge-mit-zinsen
    
    Gibt Fahrzeuge zurück, bei denen aktuell Zinsen laufen
    
    Query-Parameter:
    - status: 'zinsen_laufen', 'warnung', 'alle' (default: 'zinsen_laufen')
    - institut: 'Stellantis', 'Santander', 'alle' (default: 'alle')
    - limit: Anzahl (default: 100)
    
    Response:
    {
        "fahrzeuge": [...],
        "statistik": {
            "anzahl_fahrzeuge": 41,
            "gesamt_saldo": 823793.61,
            "gesamt_zinsen": 14018.31,
            "santander": {...},
            "stellantis": {...}
        }
    }
    """
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Query-Parameter
        status = request.args.get('status', 'zinsen_laufen')
        institut = request.args.get('institut', 'alle')
        limit = int(request.args.get('limit', 100))
        
        # Query zusammenbauen
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
        
        # Statistik berechnen
        gesamt_saldo = sum(f.get('aktueller_saldo') or 0 for f in fahrzeuge)
        gesamt_zinsen = sum(f.get('zinsen_gesamt') or 0 for f in fahrzeuge)
        
        # Nach Institut aufschlüsseln
        santander_fz = [f for f in fahrzeuge if f.get('finanzinstitut') == 'Santander']
        stellantis_fz = [f for f in fahrzeuge if f.get('finanzinstitut') == 'Stellantis']
        
        santander_zinsen = sum(f.get('zinsen_gesamt') or 0 for f in santander_fz)
        santander_zinsen_monatlich = sum(f.get('zinsen_monatlich_geschaetzt') or 0 for f in santander_fz)
        
        avg_tage = sum(f.get('tage_seit_zinsstart') or 0 for f in fahrzeuge) / len(fahrzeuge) if fahrzeuge else 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'fahrzeuge': fahrzeuge,
            'statistik': {
                'anzahl_fahrzeuge': len(fahrzeuge),
                'gesamt_saldo': round(gesamt_saldo, 2),
                'gesamt_zinsen': round(gesamt_zinsen, 2) if gesamt_zinsen > 0 else None,
                'durchschnitt_tage_seit_zinsstart': round(avg_tage, 1),
                'santander': {
                    'anzahl': len(santander_fz),
                    'zinsen_gesamt': round(santander_zinsen, 2) if santander_zinsen > 0 else None,
                    'zinsen_monatlich': round(santander_zinsen_monatlich, 2) if santander_zinsen_monatlich > 0 else None
                },
                'stellantis': {
                    'anzahl': len(stellantis_fz),
                    'zinsen_gesamt': None  # Stellantis hat keine Zinsdaten
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



# ============================================================================
# ERROR HANDLERS
# ============================================================================

@bankenspiegel_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint nicht gefunden'
    }), 404


@bankenspiegel_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Interner Server-Fehler'
    }), 500
