"""
Gudat → Locosoft Sync API (TAG 200)
====================================
Test-Integration: Termine von Gudat nach Locosoft Werkstattplaner übertragen
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
import sys
import os
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.locosoft_soap_client import LocosoftSOAPClient
from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor

bp = Blueprint('gudat_locosoft_sync', __name__, url_prefix='/api/gudat-locosoft')
logger = logging.getLogger(__name__)


@bp.route('/test-sync-termin', methods=['POST'])
@login_required  # TAG 200: Login aktiviert
def test_sync_termin():
    """
    TEST: Überträgt einen Termin von Gudat nach Locosoft Werkstattplaner
    
    Body (JSON):
        - auftrag_nr: Auftragsnummer in Locosoft (optional, wenn nicht vorhanden wird nur Termin erstellt)
        - gudat_task_id: Gudat Task-ID (optional, wenn nicht vorhanden wird erster offener Auftrag genommen)
        - date: Datum für Termin (YYYY-MM-DD), default: heute
        - time: Uhrzeit (HH:MM), default: 09:00
    
    Returns:
        JSON mit Erfolg/Fehler und Details
    """
    try:
        data = request.get_json() or {}
        auftrag_nr = data.get('auftrag_nr')
        gudat_task_id = data.get('gudat_task_id')
        date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        time_str = data.get('time', '09:00')
        
        # Datum/Zeit kombinieren
        bring_datetime = f"{date_str}T{time_str}:00"
        
        # 1. Hole Auftragsdaten aus Locosoft (falls Auftragsnummer vorhanden)
        kunde_nr = None
        fahrzeug_nr = None
        auftrag_daten = None
        
        if auftrag_nr:
            with locosoft_session() as conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("""
                    SELECT
                        o.order_customer as kunden_nr,
                        o.vehicle_number as fahrzeug_nr,
                        v.license_plate as kennzeichen,
                        COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name) as kunde,
                        o.order_taking_employee_no as serviceberater_nr,
                        m.description as hersteller,
                        o.estimated_outbound_time as geplant_fertig,
                        COALESCE(SUM(l.time_units), 0) as vorgabe_aw
                    FROM orders o
                    LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                    LEFT JOIN makes m ON v.make_number = m.make_number
                    LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
                    LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
                    WHERE o.number = %s
                    GROUP BY o.order_customer, o.vehicle_number, v.license_plate, cs.family_name, cs.first_name,
                             o.order_taking_employee_no, m.description, o.estimated_outbound_time
                """, (auftrag_nr,))
                
                row = cur.fetchone()
                if row:
                    kunde_nr = row['kunden_nr']
                    fahrzeug_nr = row['fahrzeug_nr']
                    serviceberater_nr = row['serviceberater_nr']
                    vorgabe_aw = float(row.get('vorgabe_aw', 0) or 0)
                    geplant_fertig = row.get('geplant_fertig')
                    auftrag_daten = {
                        'kunde': row['kunde'],
                        'kennzeichen': row['kennzeichen'],
                        'fahrzeug': row.get('hersteller') or None
                    }
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Auftrag {auftrag_nr} nicht gefunden'
                    }), 404
        
        # 2. Hole Gudat-Daten (optional, für Validierung)
        gudat_info = None
        if gudat_task_id:
            # TODO: Gudat Task-Details holen (später implementieren)
            gudat_info = {'task_id': gudat_task_id, 'note': 'Gudat-Details noch nicht implementiert'}
        
        # 3. Erstelle Termin in Locosoft Werkstattplaner per SOAP
        soap_client = LocosoftSOAPClient()
        
        # TAG 200: Berechne returnDateTime basierend auf Vorgabe-AW oder estimated_outbound_time
        # WICHTIG: returnDateTime muss NACH bringDateTime liegen!
        bring_dt = datetime.fromisoformat(bring_datetime.replace('T', ' ').replace('Z', ''))
        return_datetime = None
        
        if auftrag_nr and 'vorgabe_aw' in locals() and vorgabe_aw > 0:
            # Berechne Dauer aus Vorgabe-AW: 1 AW = 6 Minuten
            dauer_minuten = vorgabe_aw * 6
            # Mindestens 30 Minuten, maximal 8 Stunden
            dauer_minuten = max(30, min(dauer_minuten, 480))
            return_datetime = (bring_dt + timedelta(minutes=dauer_minuten)).isoformat().replace(' ', 'T')
        elif auftrag_nr and 'geplant_fertig' in locals() and geplant_fertig:
            # Nutze estimated_outbound_time falls vorhanden UND in der Zukunft
            geplant_dt = None
            if isinstance(geplant_fertig, str):
                geplant_dt = datetime.fromisoformat(geplant_fertig.replace('T', ' ').replace('Z', ''))
            else:
                geplant_dt = geplant_fertig
            
            # Nur verwenden, wenn geplant_fertig NACH bringDateTime liegt
            if geplant_dt and geplant_dt > bring_dt:
                return_datetime = geplant_dt.isoformat().replace(' ', 'T')
        
        # Fallback: Wenn kein returnDateTime gesetzt wurde, verwende Default (1 Stunde)
        if not return_datetime:
            return_datetime = (bring_dt + timedelta(hours=1)).isoformat().replace(' ', 'T')
        
        # TAG 200: Termin als 'fix' (fest) erstellen, damit er als Werkstatt-Termin erscheint
        # 'loose' = lose Anlieferung, 'fix' = fester Werkstatt-Termin
        appointment_data = {
            'number': 0,  # 0 = neuer Termin
            'bringDateTime': bring_datetime,
            'returnDateTime': return_datetime,  # TAG 200: WICHTIG für grafischen Planer!
            'text': f'Auftrag #{auftrag_nr}' if auftrag_nr else 'Neuer Termin',
            'type': 'fix',  # TAG 200: 'fix' = fester Werkstatt-Termin (statt 'loose')
            'comment': f'Gudat-Sync - Auftrag {auftrag_nr}' if auftrag_nr else 'Gudat-Sync',
            # TAG 200: Zusätzliche Parameter für Planer-Anzeige
            'urgency': 1,  # Standard-Dringlichkeit (1 = normal)
            'vehicleStatus': 0,  # Standard-Fahrzeugstatus
            'inProgress': 0  # Nicht in Bearbeitung (0 = geplant)
        }
        
        # TAG 200: SOAP erwartet customerNumber und vehicleNumber als direkte Integer
        if kunde_nr:
            appointment_data['customerNumber'] = kunde_nr
        
        if fahrzeug_nr:
            appointment_data['vehicleNumber'] = fahrzeug_nr
        
        if auftrag_nr:
            appointment_data['workOrderNumber'] = auftrag_nr
            # TAG 200: Workshop wird automatisch aus workOrderNumber ermittelt
        
        # TAG 200: Serviceberater setzen (falls vorhanden)
        if 'serviceberater_nr' in locals() and serviceberater_nr:
            appointment_data['bringServiceAdvisor'] = serviceberater_nr
            appointment_data['returnServiceAdvisor'] = serviceberater_nr  # TAG 200: Auch für Rückgabe
        
        # Debug: Log appointment_data
        logger.info(f"Erstelle Termin mit Daten: {appointment_data}")
        
        result = soap_client.write_appointment(appointment_data)
        
        # Debug: Log result
        logger.info(f"SOAP write_appointment Result: {result}")
        
        if result.get('success'):
            termin_nr = result.get('number')
            
            # Validierung: Prüfe ob Termin wirklich existiert
            if termin_nr:
                try:
                    # Versuche 1: Direkt lesen
                    check_termin = soap_client.read_appointment(termin_nr)
                    if check_termin:
                        logger.info(f"✅ Termin {termin_nr} erfolgreich validiert (read_appointment)")
                        logger.info(f"   Text: {check_termin.get('text', '')}")
                        logger.info(f"   Datum: {check_termin.get('bringDateTime')}")
                        logger.info(f"   Auftrag: {check_termin.get('workOrderNumber')}")
                        
                        # ZUSÄTZLICH: Prüfe ob in listAppointmentsByDate
                        try:
                            termine_liste = soap_client.list_appointments_by_date(date_str)
                            gefunden_in_liste = any(t.get('number') == termin_nr for t in termine_liste)
                            if gefunden_in_liste:
                                logger.info(f"   ✅ Termin {termin_nr} auch in listAppointmentsByDate gefunden!")
                            else:
                                logger.warning(f"   ⚠️  Termin {termin_nr} existiert, aber NICHT in listAppointmentsByDate für {date_str}")
                                logger.warning(f"   Mögliche Ursache: Termin in anderem Workshop/Bereich oder Datum-Problem")
                        except Exception as e2:
                            logger.warning(f"   ⚠️  Fehler bei listAppointmentsByDate-Prüfung: {e2}")
                    else:
                        logger.warning(f"⚠️  Termin {termin_nr}: read_appointment gibt None zurück")
                        
                        # Versuche 2: Über listAppointmentsByDate suchen
                        logger.info(f"🔍 Suche Termin {termin_nr} über listAppointmentsByDate für {date_str}...")
                        try:
                            termine_liste = soap_client.list_appointments_by_date(date_str)
                            logger.info(f"   📋 {len(termine_liste)} Termine gefunden für {date_str}")
                            gefunden = False
                            for t in termine_liste:
                                if t.get('number') == termin_nr:
                                    logger.info(f"   ✅ Termin {termin_nr} gefunden in listAppointmentsByDate!")
                                    logger.info(f"      Text: {t.get('text', '')}")
                                    logger.info(f"      Datum: {t.get('bringDateTime')}")
                                    logger.info(f"      Auftrag: {t.get('workOrderNumber')}")
                                    gefunden = True
                                    break
                            
                            if not gefunden:
                                logger.warning(f"   ⚠️  Termin {termin_nr} wurde NICHT in listAppointmentsByDate gefunden!")
                                logger.warning(f"   Gefundene Termin-Nummern: {[t.get('number') for t in termine_liste[:10]]}")
                                logger.warning(f"   Anzahl Termine: {len(termine_liste)}")
                                # Zeige Details der ersten Termine
                                if termine_liste:
                                    logger.warning(f"   Beispiel-Termine:")
                                    for t in termine_liste[:3]:
                                        logger.warning(f"      - Termin {t.get('number')}: {t.get('text', '')[:50]} - {t.get('bringDateTime')}")
                                else:
                                    logger.warning(f"   ⚠️  Keine Termine in listAppointmentsByDate für {date_str}")
                        except Exception as e:
                            logger.error(f"   ❌ Fehler bei listAppointmentsByDate: {e}")
                except Exception as e:
                    logger.error(f"❌ Validierung fehlgeschlagen: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            # 4. Optional: Setze estimated_inbound_time im Auftrag (falls vorhanden)
            # HINWEIS: estimated_inbound_time wird direkt in der DB gesetzt, nicht per SOAP
            # SOAP writeWorkOrderDetails unterstützt dieses Feld möglicherweise nicht
            if auftrag_nr:
                try:
                    # Direkt in DB setzen (schneller und zuverlässiger)
                    with locosoft_session() as conn:
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE orders 
                            SET estimated_inbound_time = %s
                            WHERE number = %s
                        """, (bring_datetime, auftrag_nr))
                        conn.commit()
                        logger.info(f"estimated_inbound_time für Auftrag {auftrag_nr} gesetzt")
                except Exception as e:
                    logger.warning(f"Termin {termin_nr} erstellt, aber estimated_inbound_time konnte nicht gesetzt werden: {e}")
            
            return jsonify({
                'success': True,
                'message': 'Termin erfolgreich erstellt',
                'termin_nr': termin_nr,
                'bring_datetime': bring_datetime,
                'auftrag_nr': auftrag_nr,
                'auftrag_daten': auftrag_daten,
                'gudat_info': gudat_info
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('message', 'Unbekannter Fehler beim Erstellen des Termins')
            }), 400
            
    except Exception as e:
        logger.exception("Fehler beim Test-Sync Termin")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/list-termine-heute', methods=['GET'])
@login_required
def list_termine_heute():
    """
    Listet alle Termine für heute aus Locosoft Werkstattplaner
    """
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        soap_client = LocosoftSOAPClient()
        termine = soap_client.list_appointments_by_date(today)
        
        return jsonify({
            'success': True,
            'date': today,
            'anzahl': len(termine),
            'termine': termine[:20]  # Max 20
        })
        
    except Exception as e:
        logger.exception("Fehler beim Abrufen der Termine")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
