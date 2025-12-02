"""
Controlling API - BWA und weitere Controlling-Funktionen
=========================================================
Erstellt: 2025-12-02
Version: 1.2 - 8932xx aus indirekten Kosten ausgeschlossen (Doppelzählung Fix)
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime

controlling_api = Blueprint('controlling_api', __name__)

DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

MONAT_NAMEN = {
    1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
    5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@controlling_api.route('/api/controlling/bwa', methods=['GET'])
def get_bwa():
    """
    BWA-Daten für einen Monat abrufen.
    
    Query-Parameter:
        monat: int (1-12)
        jahr: int (z.B. 2025)
    
    Returns:
        JSON mit allen BWA-Positionen
    """
    try:
        monat = request.args.get('monat', type=int)
        jahr = request.args.get('jahr', type=int)
        
        if not monat or not jahr:
            heute = datetime.now()
            monat = monat or heute.month
            jahr = jahr or heute.year
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Prüfen ob Daten existieren
        cursor.execute("""
            SELECT position, betrag 
            FROM bwa_monatswerte 
            WHERE jahr = ? AND monat = ?
        """, (jahr, monat))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            # Keine gespeicherten Daten - live berechnen
            return berechne_bwa_live(monat, jahr)
        
        # Daten aus DB
        data = {
            'monat': monat,
            'monat_name': MONAT_NAMEN.get(monat, str(monat)),
            'jahr': jahr
        }
        
        for row in rows:
            data[row['position']] = row['betrag']
        
        return jsonify({
            'status': 'ok',
            'data': data,
            'source': 'database'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def berechne_bwa_live(monat: int, jahr: int):
    """BWA live aus loco_journal_accountings berechnen."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        datum_von = f"{jahr}-{monat:02d}-01"
        if monat == 12:
            datum_bis = f"{jahr+1}-01-01"
        else:
            datum_bis = f"{jahr}-{monat+1:02d}-01"
        
        # Umsatz
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
        """, (datum_von, datum_bis))
        umsatz = cursor.fetchone()[0] or 0
        
        # Einsatz
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 700000 AND 799999
        """, (datum_von, datum_bis))
        einsatz = cursor.fetchone()[0] or 0
        
        # Variable Kosten
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR (nominal_account_number BETWEEN 455000 AND 456999 
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR (nominal_account_number BETWEEN 487000 AND 487099 
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR nominal_account_number BETWEEN 491000 AND 497899
              )
        """, (datum_von, datum_bis))
        variable = cursor.fetchone()[0] or 0
        
        # Direkte Kosten
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 400000 AND 489999
              AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
              AND NOT (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 424000 AND 424999
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR nominal_account_number BETWEEN 438000 AND 438999
                OR nominal_account_number BETWEEN 455000 AND 456999
                OR nominal_account_number BETWEEN 487000 AND 487099
                OR nominal_account_number BETWEEN 491000 AND 497999
              )
        """, (datum_von, datum_bis))
        direkte = cursor.fetchone()[0] or 0
        
        # Indirekte Kosten (OHNE 8932xx - das ist Umsatz!)
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND (
                (nominal_account_number BETWEEN 400000 AND 499999 
                 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                OR (nominal_account_number BETWEEN 424000 AND 424999 
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR (nominal_account_number BETWEEN 438000 AND 438999 
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR nominal_account_number BETWEEN 498000 AND 499999
                OR (nominal_account_number BETWEEN 891000 AND 896999
                    AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
              )
        """, (datum_von, datum_bis))
        indirekte = cursor.fetchone()[0] or 0
        
        # Neutrales Ergebnis (20-29xxxx inkl. kalk. Kosten/Rückstellungen)
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
            )/100.0, 0)
            FROM loco_journal_accountings
            WHERE accounting_date >= ? AND accounting_date < ?
              AND nominal_account_number BETWEEN 200000 AND 299999
        """, (datum_von, datum_bis))
        neutral = cursor.fetchone()[0] or 0
        
        conn.close()
        
        # Berechnungen
        db1 = umsatz - einsatz
        db2 = db1 - variable
        db3 = db2 - direkte
        be = db3 - indirekte
        ue = be + neutral
        
        data = {
            'monat': monat,
            'monat_name': MONAT_NAMEN.get(monat, str(monat)),
            'jahr': jahr,
            'umsatz': round(umsatz, 2),
            'einsatz': round(einsatz, 2),
            'db1': round(db1, 2),
            'variable': round(variable, 2),
            'db2': round(db2, 2),
            'direkte': round(direkte, 2),
            'db3': round(db3, 2),
            'indirekte': round(indirekte, 2),
            'betriebsergebnis': round(be, 2),
            'neutral': round(neutral, 2),
            'unternehmensergebnis': round(ue, 2)
        }
        
        return jsonify({
            'status': 'ok',
            'data': data,
            'source': 'live'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@controlling_api.route('/api/controlling/bwa/health', methods=['GET'])
def bwa_health():
    """Health-Check für BWA-API."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bwa_monatswerte")
        count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'module': 'bwa',
            'records': count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
