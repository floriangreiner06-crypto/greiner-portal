#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BANKENSPIEGEL 2.0 - FLASK ROUTES
================================
API-Endpunkte für das Bankenspiegel-Frontend

Author: Claude AI
Version: 2.0
Date: 2025-10-30
Updated: 2025-10-31 - Fahrzeugfinanzierungen Route gefixt
"""

from flask import Blueprint, render_template, jsonify, request
import sqlite3
from datetime import datetime, timedelta
import os

# Blueprint erstellen
bankenspiegel_bp = Blueprint('bankenspiegel', __name__)

# Datenbank-Pfad (AKTUALISIERT!)
DB_PATH = '/share/CACHEDEV1_DATA/Container/greiner_portal_neu/greiner_controlling.db'

# ============================================================================
# DATABASE HELPER
# ============================================================================

def get_db_connection():
    """Erstellt Datenbankverbindung"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    """Konvertiert sqlite3.Row zu Dict"""
    return dict(zip(row.keys(), row))

# ============================================================================
# HAUPTSEITE
# ============================================================================

@bankenspiegel_bp.route('/bankenspiegel')
def index():
    """Hauptseite des Bankenspiegels"""
    return render_template('bankenspiegel_erweitert.html')

# ============================================================================
# API: DASHBOARD-DATEN
# ============================================================================

@bankenspiegel_bp.route('/api/bankenspiegel/dashboard')
def api_dashboard():
    """Liefert Daten für das Dashboard"""

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Gesamtsaldo aller Konten (aus Transaktionen berechnet)
        cursor.execute("""
            SELECT
                COALESCE(SUM(saldo), 0) as gesamtsaldo
            FROM (
                SELECT 
                    t.konto_id,
                    SUM(t.betrag) as saldo
                FROM transaktionen t
                JOIN konten k ON t.konto_id = k.id
                WHERE k.aktiv = 1
                GROUP BY t.konto_id
            )
        """)
        gesamtsaldo = cursor.fetchone()[0] or 0.0

        # Anzahl aktiver Konten (nur mit Transaktionen)
        cursor.execute("""
            SELECT COUNT(DISTINCT t.konto_id)
            FROM transaktionen t
            JOIN konten k ON t.konto_id = k.id
            WHERE k.aktiv = 1
        """)
        anzahl_konten = cursor.fetchone()[0]

        # Anzahl aktiver Banken
        cursor.execute("SELECT COUNT(*) FROM banken WHERE aktiv = 1")
        anzahl_banken = cursor.fetchone()[0]

        # Transaktionen diesen Monat
        erster_des_monats = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) FROM transaktionen
            WHERE buchungsdatum >= ?
        """, (erster_des_monats,))
        transaktionen_monat = cursor.fetchone()[0]

        # Umsätze diesen Monat
        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 0) as einnahmen,
                COALESCE(SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END), 0) as ausgaben
            FROM transaktionen
            WHERE buchungsdatum >= ?
        """, (erster_des_monats,))
        umsaetze = cursor.fetchone()

        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'gesamtsaldo': round(gesamtsaldo, 2),
                'anzahl_konten': anzahl_konten,
                'anzahl_banken': anzahl_banken,
                'transaktionen_monat': transaktionen_monat,
                'einnahmen_monat': round(umsaetze[0], 2),
                'ausgaben_monat': round(umsaetze[1], 2)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# API: KONTENÜBERSICHT
# ============================================================================

@bankenspiegel_bp.route('/api/bankenspiegel/konten')
def api_konten():
    """Liefert alle Konten mit aktuellen Salden"""

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                k.id,
                b.bank_name,
                k.kontoname,
                k.iban,
                k.kontotyp,
                k.waehrung,
                COALESCE((SELECT SUM(betrag) FROM transaktionen WHERE konto_id = k.id), 0) as saldo,
                (SELECT MAX(buchungsdatum) FROM transaktionen WHERE konto_id = k.id) as stand_datum,
                k.aktiv
            FROM konten k
            JOIN banken b ON k.bank_id = b.id
            WHERE k.aktiv = 1 AND b.aktiv = 1
            ORDER BY b.bank_name, k.kontoname
        """)

        konten = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'data': konten
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# API: TRANSAKTIONEN
# ============================================================================

@bankenspiegel_bp.route('/api/bankenspiegel/transaktionen')
def api_transaktionen():
    """Liefert Transaktionen mit Filteroptionen"""

    try:
        # Query-Parameter
        konto_id = request.args.get('konto_id', type=int)
        von_datum = request.args.get('von')
        bis_datum = request.args.get('bis')
        limit = request.args.get('limit', 100, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        # SQL aufbauen
        sql = """
            SELECT
                t.id,
                t.buchungsdatum,
                t.valutadatum,
                t.buchungstext,
                t.verwendungszweck,
                t.betrag,
                t.waehrung,
                t.kategorie,
                t.steuerrelevant,
                k.kontoname,
                b.bank_name
            FROM transaktionen t
            JOIN konten k ON t.konto_id = k.id
            JOIN banken b ON k.bank_id = b.id
            WHERE 1=1
        """
        params = []

        if konto_id:
            sql += " AND t.konto_id = ?"
            params.append(konto_id)

        if von_datum:
            sql += " AND t.buchungsdatum >= ?"
            params.append(von_datum)

        if bis_datum:
            sql += " AND t.buchungsdatum <= ?"
            params.append(bis_datum)

        sql += " ORDER BY t.buchungsdatum DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        transaktionen = [dict_from_row(row) for row in cursor.fetchall()]

        conn.close()

        return jsonify({
            'success': True,
            'data': transaktionen
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# API: MONATLICHE UMSÄTZE
# ============================================================================

@bankenspiegel_bp.route('/api/bankenspiegel/umsaetze_monatlich')
def api_umsaetze_monatlich():
    """Liefert monatliche Umsätze für Charts"""

    try:
        # Letzten 12 Monate
        monate = request.args.get('monate', 12, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                strftime('%Y-%m', buchungsdatum) as monat,
                SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END) as einnahmen,
                SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END) as ausgaben,
                SUM(betrag) as saldo
            FROM transaktionen
            WHERE buchungsdatum >= date('now', '-' || ? || ' months')
            GROUP BY strftime('%Y-%m', buchungsdatum)
            ORDER BY monat
        """, (monate,))

        umsaetze = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'data': umsaetze
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# API: KATEGORIEAUSWERTUNG
# ============================================================================

@bankenspiegel_bp.route('/api/bankenspiegel/kategorien')
def api_kategorien():
    """Liefert Ausgaben nach Kategorien"""

    try:
        # Zeitraum
        von_datum = request.args.get('von')
        bis_datum = request.args.get('bis')

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                COALESCE(kategorie, 'Nicht kategorisiert') as kategorie,
                COUNT(*) as anzahl,
                SUM(ABS(betrag)) as summe
            FROM transaktionen
            WHERE betrag < 0
        """
        params = []

        if von_datum:
            sql += " AND buchungsdatum >= ?"
            params.append(von_datum)

        if bis_datum:
            sql += " AND buchungsdatum <= ?"
            params.append(bis_datum)

        sql += " GROUP BY kategorie ORDER BY summe DESC"

        cursor.execute(sql, params)
        kategorien = [dict_from_row(row) for row in cursor.fetchall()]

        conn.close()

        return jsonify({
            'success': True,
            'data': kategorien
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# API: SALDO-ENTWICKLUNG
# ============================================================================

@bankenspiegel_bp.route('/api/bankenspiegel/saldo_entwicklung')
def api_saldo_entwicklung():
    """Liefert Saldo-Entwicklung über Zeit"""

    try:
        konto_id = request.args.get('konto_id', type=int)
        tage = request.args.get('tage', 90, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        if konto_id:
            cursor.execute("""
                SELECT
                    datum,
                    saldo
                FROM kontostand_historie
                WHERE konto_id = ?
                  AND datum >= date('now', '-' || ? || ' days')
                ORDER BY datum
            """, (konto_id, tage))
        else:
            # Gesamtsaldo aller Konten
            cursor.execute("""
                SELECT
                    kh.datum,
                    SUM(kh.saldo) as saldo
                FROM kontostand_historie kh
                JOIN konten k ON kh.konto_id = k.id
                WHERE kh.datum >= date('now', '-' || ? || ' days')
                  AND k.aktiv = 1
                GROUP BY kh.datum
                ORDER BY kh.datum
            """, (tage,))

        entwicklung = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'data': entwicklung
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# API: BANKEN
# ============================================================================

@bankenspiegel_bp.route('/api/bankenspiegel/banken')
def api_banken():
    """Liefert alle Banken"""

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                bank_name,
                bank_typ,
                iban_prefix,
                aktiv,
                (SELECT COUNT(*) FROM konten WHERE bank_id = banken.id AND aktiv = 1) as anzahl_konten
            FROM banken
            ORDER BY bank_name
        """)

        banken = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'data': banken
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# API: SUCHE
# ============================================================================

@bankenspiegel_bp.route('/api/bankenspiegel/suche')
def api_suche():
    """Volltextsuche in Transaktionen"""

    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 50, type=int)

        if not query or len(query) < 3:
            return jsonify({
                'success': False,
                'error': 'Suchbegriff muss mindestens 3 Zeichen lang sein'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        search_term = f'%{query}%'

        cursor.execute("""
            SELECT
                t.id,
                t.buchungsdatum,
                t.buchungstext,
                t.verwendungszweck,
                t.betrag,
                k.kontoname,
                b.bank_name
            FROM transaktionen t
            JOIN konten k ON t.konto_id = k.id
            JOIN banken b ON k.bank_id = b.id
            WHERE t.buchungstext LIKE ?
               OR t.verwendungszweck LIKE ?
            ORDER BY t.buchungsdatum DESC
            LIMIT ?
        """, (search_term, search_term, limit))

        ergebnisse = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'data': ergebnisse
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# FAHRZEUGFINANZIERUNGEN - NUR EINE VERSION!
# ============================================================================

@bankenspiegel_bp.route('/bankenspiegel/fahrzeugfinanzierungen')
def fahrzeugfinanzierungen():
    """Fahrzeugfinanzierungen Übersicht - Stellantis Bank"""

    conn = get_db_connection()

    # Gesamt-Statistik
    stats = conn.execute("""
        SELECT
            COUNT(*) as anzahl_fahrzeuge,
            SUM(aktueller_saldo) as gesamt_saldo,
            SUM(original_betrag) as gesamt_original,
            SUM(abbezahlt) as gesamt_abbezahlt
        FROM fahrzeugfinanzierungen
    """).fetchone()

    # Nach RRDI
    rrdi_stats = conn.execute("""
        SELECT
            rrdi,
            COUNT(*) as anzahl,
            SUM(aktueller_saldo) as saldo,
            SUM(original_betrag) as original,
            SUM(abbezahlt) as abbezahlt,
            AVG(alter_tage) as durchschnitt_alter
        FROM fahrzeugfinanzierungen
        GROUP BY rrdi
    """).fetchall()

    # Nach Produktfamilie
    produkt_stats = conn.execute("""
        SELECT
            produktfamilie,
            COUNT(*) as anzahl,
            SUM(aktueller_saldo) as saldo
        FROM fahrzeugfinanzierungen
        GROUP BY produktfamilie
        ORDER BY saldo DESC
    """).fetchall()

    # Alle Fahrzeuge
    fahrzeuge = conn.execute("""
        SELECT
            rrdi, produktfamilie, vin, modell, vertragsbeginn,
            alter_tage, zinsfreiheit_tage, aktueller_saldo,
            original_betrag, abbezahlt
        FROM fahrzeugfinanzierungen
        ORDER BY aktueller_saldo DESC
    """).fetchall()

    # Alerts: Zinsfreiheit läuft bald ab
    alerts = conn.execute("""
        SELECT
            rrdi, vin, modell,
            (zinsfreiheit_tage - alter_tage) as tage_bis_zinsen,
            aktueller_saldo
        FROM fahrzeugfinanzierungen
        WHERE (zinsfreiheit_tage - alter_tage) < 30
          AND (zinsfreiheit_tage - alter_tage) > 0
        ORDER BY tage_bis_zinsen ASC
    """).fetchall()

    conn.close()

    return render_template('fahrzeugfinanzierungen.html',
                         stats=stats,
                         rrdi_stats=rrdi_stats,
                         produkt_stats=produkt_stats,
                         fahrzeuge=fahrzeuge,
                         alerts=alerts)


# ============================================================================
# API: LOCOSOFT STELLANTIS-BESTAND
# ============================================================================

@bankenspiegel_bp.route('/api/bankenspiegel/stellantis_bestand')
def api_stellantis_bestand():
    """Liefert LocoSoft-Bestand mit Stellantis-Finanzierung"""
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=os.environ.get('LOCOSOFT_DB_HOST', '10.80.80.8'),
            port=int(os.environ.get('LOCOSOFT_DB_PORT', 5432)),
            database=os.environ.get('LOCOSOFT_DB_NAME', 'loco_auswertung_db'),
            user=os.environ.get('LOCOSOFT_DB_USER', 'loco_auswertung_benutzer'),
            password=os.environ.get('LOCOSOFT_DB_PASSWORD', 'loco')
        )
        cursor = conn.cursor()
        
        # Statistik
        cursor.execute("""
            SELECT 
                COUNT(*) as anzahl,
                COUNT(CASE WHEN dv.dealer_vehicle_type = 'N' THEN 1 END) as neu,
                COUNT(CASE WHEN dv.dealer_vehicle_type = 'T' THEN 1 END) as transit,
                COUNT(CASE WHEN dv.dealer_vehicle_type NOT IN ('N', 'T') THEN 1 END) as sonstige
            FROM vehicles v
            LEFT JOIN dealer_vehicles dv ON v.internal_number = dv.vehicle_number
            WHERE EXISTS (
                SELECT 1 FROM codes_vehicle_list cvl
                WHERE cvl.vehicle_number = v.internal_number
                  AND cvl.code = 'F/LBA'
                  AND cvl.value_text ILIKE '%stellantis%'
            )
        """)
        
        stats_row = cursor.fetchone()
        stats = {
            'anzahl': stats_row[0],
            'neu': stats_row[1],
            'transit': stats_row[2],
            'sonstige': stats_row[3]
        }
        
        # Neueste Fahrzeuge (letzte 5)
        cursor.execute("""
            SELECT 
                v.vin,
                v.license_plate,
                v.model_code,
                v.first_registration_date,
                dv.dealer_vehicle_type
            FROM vehicles v
            LEFT JOIN dealer_vehicles dv ON v.internal_number = dv.vehicle_number
            WHERE EXISTS (
                SELECT 1 FROM codes_vehicle_list cvl
                WHERE cvl.vehicle_number = v.internal_number
                  AND cvl.code = 'F/LBA'
                  AND cvl.value_text ILIKE '%stellantis%'
            )
            AND v.first_registration_date IS NOT NULL
            ORDER BY v.first_registration_date DESC
            LIMIT 5
        """)
        
        neueste = []
        for row in cursor.fetchall():
            neueste.append({
                'vin': row[0],
                'kennzeichen': row[1],
                'modell': row[2],
                'erstzulassung': str(row[3]) if row[3] else None,
                'typ': row[4]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'statistik': stats,
                'neueste': neueste
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



# ============================================================================
# BLUEPRINT REGISTRIERUNG
# ============================================================================

# ============================================================================
# API: FAHRZEUGFINANZIERUNGEN (für Dashboard)
# ============================================================================

@bankenspiegel_bp.route('/api/bankenspiegel/fahrzeugfinanzierungen')
def api_fahrzeugfinanzierungen():
    """Liefert Stellantis Fahrzeugfinanzierungen für Dashboard"""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Gesamt-Statistik
        cursor.execute("""
            SELECT
                COUNT(*) as anzahl_fahrzeuge,
                SUM(aktueller_saldo) as gesamt_saldo,
                SUM(original_betrag) as gesamt_original,
                SUM(abbezahlt) as gesamt_abbezahlt
            FROM fahrzeugfinanzierungen
        """)
        gesamt_row = cursor.fetchone()
        gesamt = dict_from_row(gesamt_row) if gesamt_row else {}
        
        # Nach RRDI
        cursor.execute("""
            SELECT
                rrdi,
                COUNT(*) as anzahl,
                SUM(aktueller_saldo) as saldo,
                SUM(original_betrag) as original,
                SUM(abbezahlt) as abbezahlt,
                MAX(import_datum) as letzter_import
            FROM fahrzeugfinanzierungen
            GROUP BY rrdi
            ORDER BY saldo DESC
        """)
        nach_rrdi = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Top 10 Fahrzeuge (höchste Salden)
        cursor.execute("""
            SELECT
                rrdi, vin, modell, aktueller_saldo, 
                vertragsbeginn, alter_tage
            FROM fahrzeugfinanzierungen
            ORDER BY aktueller_saldo DESC
            LIMIT 10
        """)
        top_fahrzeuge = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Alerts: Zinsfreiheit läuft bald ab
        cursor.execute("""
            SELECT
                rrdi, vin, modell,
                (zinsfreiheit_tage - alter_tage) as tage_bis_zinsen,
                aktueller_saldo
            FROM fahrzeugfinanzierungen
            WHERE (zinsfreiheit_tage - alter_tage) < 30
              AND (zinsfreiheit_tage - alter_tage) > 0
            ORDER BY tage_bis_zinsen ASC
            LIMIT 5
        """)
        alerts = [dict_from_row(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'gesamt': gesamt,
                'nach_rrdi': nach_rrdi,
                'top_fahrzeuge': top_fahrzeuge,
                'alerts': alerts
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500




# ============================================================================
# STELLANTIS BESTANDSLISTE (VIEW)
# ============================================================================

@bankenspiegel_bp.route('/bankenspiegel/stellantis_bestand')
def stellantis_bestand():
    """Zeigt LocoSoft-Bestand mit Stellantis-Finanzierung"""
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=os.environ.get('LOCOSOFT_DB_HOST', '10.80.80.8'),
            port=int(os.environ.get('LOCOSOFT_DB_PORT', 5432)),
            database=os.environ.get('LOCOSOFT_DB_NAME', 'loco_auswertung_db'),
            user=os.environ.get('LOCOSOFT_DB_USER', 'loco_auswertung_benutzer'),
            password=os.environ.get('LOCOSOFT_DB_PASSWORD', 'loco')
        )
        cursor = conn.cursor()
        
        # Alle Fahrzeuge
        cursor.execute("""
            SELECT 
                v.vin,
                v.license_plate,
                v.model_code,
                v.free_form_model_text,
                v.first_registration_date,
                v.production_year,
                dv.dealer_vehicle_type,
                dv.location,
                (SELECT value_text FROM codes_vehicle_list 
                 WHERE vehicle_number = v.internal_number AND code = 'F/LVN') as vertragsnummer,
                (SELECT value_text FROM codes_vehicle_list 
                 WHERE vehicle_number = v.internal_number AND code = 'BRIEF') as brief_ort
            FROM vehicles v
            LEFT JOIN dealer_vehicles dv ON v.internal_number = dv.vehicle_number
            WHERE EXISTS (
                SELECT 1 FROM codes_vehicle_list cvl
                WHERE cvl.vehicle_number = v.internal_number
                  AND cvl.code = 'F/LBA'
                  AND cvl.value_text ILIKE '%stellantis%'
            )
            ORDER BY dv.dealer_vehicle_type, v.license_plate
        """)
        
        vehicles = []
        for row in cursor.fetchall():
            vehicles.append({
                'vin': row[0],
                'kennzeichen': row[1],
                'modell_code': row[2],
                'modell_text': row[3],
                'erstzulassung': row[4],
                'baujahr': row[5],
                'typ': row[6],
                'standort': row[7],
                'vertragsnummer': row[8],
                'brief_ort': row[9]
            })
        
        # Statistik
        stats = {
            'gesamt': len(vehicles),
            'neu': sum(1 for v in vehicles if v['typ'] == 'N'),
            'transit': sum(1 for v in vehicles if v['typ'] == 'T'),
            'sonstige': sum(1 for v in vehicles if v['typ'] not in ['N', 'T'])
        }
        
        conn.close()
        
        return render_template('stellantis_bestand.html',
                             vehicles=vehicles,
                             stats=stats)
        
    except Exception as e:
        return f"Fehler: {str(e)}", 500


def register_routes(app):
    """Registriert alle Bankenspiegel-Routes in der Flask-App"""
    app.register_blueprint(bankenspiegel_bp)
