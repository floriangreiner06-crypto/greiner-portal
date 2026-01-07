"""
ABTEILUNGSLEITER-PLANUNG API - REST-Endpoints für Bottom-Up Planung
====================================================================
TAG 165: API für Abteilungsleiter-Planung (10 Fragen pro KST)

Architektur:
- Nutzt abteilungsleiter_planung_data.py (SSOT)
- Nur HTTP-Handling, keine Business-Logik
- RESTful Endpoints

Endpoints:
- GET  /api/planung/abteilungsleiter - Liste aller Planungen
- GET  /api/planung/abteilungsleiter/<id> - Planung laden
- POST /api/planung/abteilungsleiter - Planung erstellen/aktualisieren
- POST /api/planung/abteilungsleiter/<id>/berechnen - Planung berechnen
- POST /api/planung/abteilungsleiter/<id>/freigeben - Planung freigeben
- GET  /api/planung/abteilungsleiter/<id>/impact - Impact-Analyse
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import date, datetime
from typing import Dict, Any, Optional

from api.db_connection import get_db
from api.db_utils import db_session, row_to_dict
from api.abteilungsleiter_planung_data import AbteilungsleiterPlanungData
from api.unternehmensplan_data import get_current_geschaeftsjahr
from psycopg2.extras import RealDictCursor

planung_bp = Blueprint('abteilungsleiter_planung_api', __name__, url_prefix='/api/planung/abteilungsleiter')


def get_gj_from_date(d=None):
    """Ermittelt Geschaeftsjahr aus Datum (Sep-Aug)"""
    if d is None:
        d = date.today()
    if d.month >= 9:
        return f"{d.year}/{str(d.year + 1)[2:]}"
    else:
        return f"{d.year - 1}/{str(d.year)[2:]}"


def get_kalendar_monat():
    """Gibt aktuellen Kalendermonat zurück (1-12)"""
    return date.today().month


@planung_bp.route('/health')
def health():
    """Health-Check"""
    return jsonify({
        'status': 'ok',
        'service': 'abteilungsleiter-planung',
        'timestamp': datetime.now().isoformat(),
        'geschaeftsjahr': get_gj_from_date()
    })


@planung_bp.route('', methods=['GET'])
@login_required
def liste():
    """
    Liste aller Planungen.
    
    Query-Params:
        - geschaeftsjahr: z.B. '2025/26'
        - monat: 1-12
        - bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        - standort: 1, 2, oder 3
        - status: 'entwurf', 'freigegeben', 'abgelehnt'
    """
    try:
        geschaeftsjahr = request.args.get('geschaeftsjahr', get_gj_from_date())
        monat = request.args.get('monat', type=int)
        bereich = request.args.get('bereich')
        standort = request.args.get('standort', type=int)
        status = request.args.get('status')
        
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT id, geschaeftsjahr, monat, bereich, standort, status,
                       erstellt_von, erstellt_am, freigegeben_von, freigegeben_am,
                       umsatz_basis, db1_basis, db2_basis,
                       umsatz_ziel, db1_ziel, db2_ziel
                FROM abteilungsleiter_planung
                WHERE 1=1
            """
            params = []
            
            if geschaeftsjahr:
                query += " AND geschaeftsjahr = %s"
                params.append(geschaeftsjahr)
            
            if monat:
                query += " AND monat = %s"
                params.append(monat)
            
            if bereich:
                query += " AND bereich = %s"
                params.append(bereich)
            
            if standort:
                query += " AND standort = %s"
                params.append(standort)
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            query += " ORDER BY geschaeftsjahr DESC, monat DESC, bereich, standort"
            
            cursor.execute(query, params)
            planungen = [row_to_dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                'success': True,
                'planungen': planungen,
                'anzahl': len(planungen)
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@planung_bp.route('/<int:planung_id>', methods=['GET'])
@login_required
def get_planung(planung_id: int):
    """Lädt eine Planung."""
    try:
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM abteilungsleiter_planung
                WHERE id = %s
            """, (planung_id,))
            
            planung = cursor.fetchone()
            if not planung:
                return jsonify({'success': False, 'error': 'Planung nicht gefunden'}), 404
            
            return jsonify({
                'success': True,
                'planung': row_to_dict(planung)
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@planung_bp.route('', methods=['POST'])
@login_required
def erstellen_oder_aktualisieren():
    """
    Erstellt oder aktualisiert eine Planung.
    
    Body:
        - geschaeftsjahr: z.B. '2025/26'
        - monat: 1-12
        - bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        - standort: 1, 2, oder 3
        - planung_data: Dict mit 10 Fragen (bereichs-spezifisch)
    """
    try:
        data = request.get_json()
        
        geschaeftsjahr = data.get('geschaeftsjahr', get_gj_from_date())
        monat = data.get('monat', get_kalendar_monat())
        bereich = data['bereich']
        standort = data['standort']
        planung_data = data.get('planung_data', {})
        
        # Validierung
        if bereich not in ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']:
            return jsonify({'success': False, 'error': 'Ungültiger Bereich'}), 400
        
        if standort not in [1, 2, 3]:
            return jsonify({'success': False, 'error': 'Ungültiger Standort'}), 400
        
        # Planung berechnen (SSOT)
        if bereich in ['NW', 'GW']:
            berechnung = AbteilungsleiterPlanungData.berechne_nw_gw_planung(
                geschaeftsjahr=geschaeftsjahr,
                monat=monat,
                bereich=bereich,
                standort=standort,
                planung_data=planung_data
            )
        elif bereich == 'Werkstatt':
            berechnung = AbteilungsleiterPlanungData.berechne_werkstatt_planung(
                geschaeftsjahr=geschaeftsjahr,
                monat=monat,
                standort=standort,
                planung_data=planung_data
            )
        elif bereich == 'Teile':
            berechnung = AbteilungsleiterPlanungData.berechne_teile_planung(
                geschaeftsjahr=geschaeftsjahr,
                monat=monat,
                standort=standort,
                planung_data=planung_data
            )
        else:
            return jsonify({'success': False, 'error': 'Bereich noch nicht implementiert'}), 400
        
        # Hybrid-Berechnung (Basis + Aufhol)
        hybrid = AbteilungsleiterPlanungData.berechne_hybrid_ziele(
            berechnung['umsatz_basis'],
            berechnung['db1_basis'],
            geschaeftsjahr,
            bereich,
            standort
        )
        
        # In Datenbank speichern (UPSERT)
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Alle Planungsdaten zusammenführen
            insert_data = {
                'geschaeftsjahr': geschaeftsjahr,
                'monat': monat,
                'bereich': bereich,
                'standort': standort,
                'status': 'entwurf',
                'erstellt_von': current_user.username,
                **planung_data,
                'umsatz_basis': berechnung['umsatz_basis'],
                'db1_basis': berechnung['db1_basis'],
                'db2_basis': berechnung.get('db2_basis', 0),
                'aufhol_umsatz': hybrid['aufhol_umsatz'],
                'aufhol_db1': hybrid['aufhol_db1'],
                'umsatz_ziel': hybrid['umsatz_ziel'],
                'db1_ziel': hybrid['db1_ziel'],
                'db2_ziel': berechnung.get('db2_basis', 0)  # DB2 hat kein Aufhol
            }
            
            # SQL-Query bauen (dynamisch, da viele Spalten)
            columns = list(insert_data.keys())
            values = [insert_data[col] for col in columns]
            placeholders = ', '.join(['%s'] * len(values))
            
            query = f"""
                INSERT INTO abteilungsleiter_planung ({', '.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT (geschaeftsjahr, monat, bereich, standort)
                DO UPDATE SET
                    {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['geschaeftsjahr', 'monat', 'bereich', 'standort']])},
                    geaendert_von = EXCLUDED.erstellt_von,
                    geaendert_am = CURRENT_TIMESTAMP
                RETURNING id
            """
            
            cursor.execute(query, values)
            planung_id = cursor.fetchone()['id']
            conn.commit()
            
            return jsonify({
                'success': True,
                'planung_id': planung_id,
                'berechnung': berechnung,
                'hybrid': hybrid,
                'message': 'Planung gespeichert'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@planung_bp.route('/<int:planung_id>/berechnen', methods=['POST'])
@login_required
def berechnen(planung_id: int):
    """
    Berechnet eine Planung neu (z.B. nach Änderung der Parameter).
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Planung laden
            cursor.execute("""
                SELECT * FROM abteilungsleiter_planung
                WHERE id = %s
            """, (planung_id,))
            
            planung = cursor.fetchone()
            if not planung:
                return jsonify({'success': False, 'error': 'Planung nicht gefunden'}), 404
            
            planung_dict = row_to_dict(planung)
            
            # Planung berechnen (SSOT)
            bereich = planung_dict['bereich']
            if bereich in ['NW', 'GW']:
                berechnung = AbteilungsleiterPlanungData.berechne_nw_gw_planung(
                    planung_id=planung_id,
                    geschaeftsjahr=planung_dict['geschaeftsjahr'],
                    monat=planung_dict['monat'],
                    bereich=bereich,
                    standort=planung_dict['standort'],
                    planung_data=planung_dict
                )
            elif bereich == 'Werkstatt':
                berechnung = AbteilungsleiterPlanungData.berechne_werkstatt_planung(
                    planung_id=planung_id,
                    geschaeftsjahr=planung_dict['geschaeftsjahr'],
                    monat=planung_dict['monat'],
                    standort=planung_dict['standort'],
                    planung_data=planung_dict
                )
            elif bereich == 'Teile':
                berechnung = AbteilungsleiterPlanungData.berechne_teile_planung(
                    planung_id=planung_id,
                    geschaeftsjahr=planung_dict['geschaeftsjahr'],
                    monat=planung_dict['monat'],
                    standort=planung_dict['standort'],
                    planung_data=planung_dict
                )
            else:
                return jsonify({'success': False, 'error': 'Bereich noch nicht implementiert'}), 400
            
            # Hybrid-Berechnung
            hybrid = AbteilungsleiterPlanungData.berechne_hybrid_ziele(
                berechnung['umsatz_basis'],
                berechnung['db1_basis'],
                planung_dict['geschaeftsjahr'],
                bereich,
                planung_dict['standort']
            )
            
            # Berechnete Werte aktualisieren
            cursor.execute("""
                UPDATE abteilungsleiter_planung
                SET umsatz_basis = %s,
                    db1_basis = %s,
                    db2_basis = %s,
                    aufhol_umsatz = %s,
                    aufhol_db1 = %s,
                    umsatz_ziel = %s,
                    db1_ziel = %s,
                    db2_ziel = %s,
                    geaendert_am = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                berechnung['umsatz_basis'],
                berechnung['db1_basis'],
                berechnung.get('db2_basis', 0),
                hybrid['aufhol_umsatz'],
                hybrid['aufhol_db1'],
                hybrid['umsatz_ziel'],
                hybrid['db1_ziel'],
                berechnung.get('db2_basis', 0),
                planung_id
            ))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'berechnung': berechnung,
                'hybrid': hybrid,
                'message': 'Planung neu berechnet'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@planung_bp.route('/<int:planung_id>/freigeben', methods=['POST'])
@login_required
def freigeben(planung_id: int):
    """
    Gibt eine Planung frei und schreibt Ziele in kst_ziele.
    
    Body:
        - kommentar: Optional Kommentar
    """
    try:
        data = request.get_json() or {}
        kommentar = data.get('kommentar')
        
        # Freigabe (SSOT)
        result = AbteilungsleiterPlanungData.freigeben_planung(
            planung_id,
            current_user.username,
            kommentar
        )
        
        if not result['success']:
            return jsonify(result), 400
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@planung_bp.route('/<int:planung_id>/impact', methods=['GET'])
@login_required
def get_impact(planung_id: int):
    """
    Gibt Impact-Analyse für eine Planung zurück.
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM abteilungsleiter_planung
                WHERE id = %s
            """, (planung_id,))
            
            planung = cursor.fetchone()
            if not planung:
                return jsonify({'success': False, 'error': 'Planung nicht gefunden'}), 404
            
            planung_dict = row_to_dict(planung)
            
            # Impact-Analyse (bereits in Berechnung enthalten)
            bereich = planung_dict['bereich']
            if bereich in ['NW', 'GW']:
                berechnung = AbteilungsleiterPlanungData.berechne_nw_gw_planung(
                    planung_id=planung_id,
                    geschaeftsjahr=planung_dict['geschaeftsjahr'],
                    monat=planung_dict['monat'],
                    bereich=bereich,
                    standort=planung_dict['standort'],
                    planung_data=planung_dict
                )
            elif bereich == 'Werkstatt':
                berechnung = AbteilungsleiterPlanungData.berechne_werkstatt_planung(
                    planung_id=planung_id,
                    geschaeftsjahr=planung_dict['geschaeftsjahr'],
                    monat=planung_dict['monat'],
                    standort=planung_dict['standort'],
                    planung_data=planung_dict
                )
            elif bereich == 'Teile':
                berechnung = AbteilungsleiterPlanungData.berechne_teile_planung(
                    planung_id=planung_id,
                    geschaeftsjahr=planung_dict['geschaeftsjahr'],
                    monat=planung_dict['monat'],
                    standort=planung_dict['standort'],
                    planung_data=planung_dict
                )
            else:
                return jsonify({'success': False, 'error': 'Bereich noch nicht implementiert'}), 400
            
            return jsonify({
                'success': True,
                'impact': berechnung.get('impact', {}),
                'vorjahr': berechnung.get('vorjahr', {})
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@planung_bp.route('/jahresplanung', methods=['GET'])
@login_required
def jahresplanung_laden():
    """
    Lädt Jahresplanung für einen Bereich und Standort.
    
    Query-Params:
        - geschaeftsjahr: z.B. '2025/26'
        - bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        - standort: 1, 2, oder 3
    """
    geschaeftsjahr = request.args.get('geschaeftsjahr', get_gj_from_date())
    bereich = request.args.get('bereich')
    standort = request.args.get('standort', type=int)
    
    if not bereich or not standort:
        return jsonify({'success': False, 'error': 'bereich und standort erforderlich'}), 400
    
    try:
        jahresplanung = AbteilungsleiterPlanungData.lade_jahresplanung(
            geschaeftsjahr, bereich, standort
        )
        return jsonify({'success': True, 'data': jahresplanung})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@planung_bp.route('/kopiere-vorjahr', methods=['POST'])
@login_required
def kopiere_vorjahr():
    """
    Kopiert Vorjahres-Planung als Basis für neues Geschäftsjahr.
    
    Body:
        - geschaeftsjahr: z.B. '2025/26'
        - bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        - standort: 1, 2, oder 3
    """
    data = request.get_json()
    geschaeftsjahr = data.get('geschaeftsjahr', get_gj_from_date())
    bereich = data.get('bereich')
    standort = data.get('standort')
    
    if not bereich or not standort:
        return jsonify({'success': False, 'error': 'bereich und standort erforderlich'}), 400
    
    try:
        result = AbteilungsleiterPlanungData.kopiere_vorjahr(
            geschaeftsjahr, bereich, standort, current_user.username
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

