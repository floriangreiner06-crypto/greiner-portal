"""
GREINER DRIVE - Celery Tasks
=============================
Serviceberater-Benachrichtigungen bei Zeitüberschreitungen

TAG 171: Serviceberater-Modal per E-Mail
"""

import logging
from datetime import datetime, date
from celery import shared_task

# Logging
logger = logging.getLogger('celery_tasks')

# Neue Task für Serviceberater-Benachrichtigungen (TAG 171)
@shared_task(soft_time_limit=300)
def benachrichtige_serviceberater_ueberschreitungen():
    """
    Prüft periodisch Überschreitungen und sendet E-Mails an Serviceberater.
    Läuft alle 15 Minuten während Arbeitszeit (Mo-Fr, 7-18 Uhr).
    
    TAG 171: Serviceberater-Modal per E-Mail
    """
    try:
        from api.werkstatt_data import WerkstattData
        from api.graph_mail_connector import GraphMailConnector
        from api.db_utils import db_session, locosoft_session
        from psycopg2.extras import RealDictCursor
        
        # Prüfe ob Arbeitszeit (Mo-Fr, 7-18 Uhr)
        jetzt = datetime.now()
        if jetzt.weekday() >= 5:  # Samstag/Sonntag
            return {'success': True, 'message': 'Wochenende - keine Benachrichtigungen'}
        if jetzt.hour < 7 or jetzt.hour >= 18:
            return {'success': True, 'message': 'Außerhalb Arbeitszeit - keine Benachrichtigungen'}
        
        logger.info("Prüfe Überschreitungen für Serviceberater-Benachrichtigungen...")
        
        # Stempeluhr-Daten holen (nur heute, alle Betriebe)
        stempeluhr_data = WerkstattData.get_stempeluhr(
            datum=date.today(),
            subsidiaries=None  # Alle Betriebe
        )
        
        # TEST-MODUS: Wenn Stempeluhr-Daten nicht verfügbar, trotzdem Test-Mail senden
        if not stempeluhr_data.get('success'):
            logger.warning("Stempeluhr-Daten nicht verfügbar - Test-Mail wird trotzdem gesendet")
            # Erstelle Dummy-Daten für Test-Mail
            aktive_mechaniker = []
            ueberschritten = [{
                'order_number': 'TEST-12345',
                'fortschritt_prozent': 120,
                'name': 'Test-Mechaniker'
            }]
            TEST_MODE = True
        else:
            aktive_mechaniker = stempeluhr_data.get('aktive_mechaniker', [])
            ueberschritten = [m for m in aktive_mechaniker if m.get('fortschritt_prozent', 0) > 100]
            
            # TEST-MODUS: Wenn keine Überschreitungen, trotzdem Test-Mail an Florian senden
            TEST_MODE = len(ueberschritten) == 0
        
        if not ueberschritten:
            logger.info("Keine Überschreitungen gefunden - Test-Mail wird trotzdem gesendet")
            # Erstelle Dummy-Überschreitung für Test-Mail
            if aktive_mechaniker:
                # Nimm ersten aktiven Mechaniker als Beispiel
                dummy_mech = aktive_mechaniker[0]
                ueberschritten = [{
                    'order_number': dummy_mech.get('order_number', 'TEST-12345'),
                    'fortschritt_prozent': 120,  # Dummy-Wert
                    'name': dummy_mech.get('name', 'Test-Mechaniker')
                }]
            else:
                # Fallback: Erstelle komplett Dummy-Daten
                ueberschritten = [{
                    'order_number': 'TEST-12345',
                    'fortschritt_prozent': 120,
                    'name': 'Test-Mechaniker'
                }]
        
        logger.info(f"{len(ueberschritten)} Überschreitungen gefunden (TEST_MODE={TEST_MODE})")
        
        # Fallback-User Mapping
        FALLBACK_USER_BY_BETRIEB = {
            1: [3007],  # Deggendorf: Matthias König
            2: [3007],  # Deggendorf Hyundai: Matthias König
            3: [1003, 4002]  # Landau: Rolf Sterr + Leonhard Keidl
        }
        
        # E-Mail-Adressen aus DB holen
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Hole alle relevanten employee_numbers (Serviceberater + Fallback)
            alle_employee_nrs = set()
            auftraege_mit_sb = {}  # auftrag_nr -> (serviceberater_nr, betrieb)
            
            for ueberschritt in ueberschritten:
                auftrag_nr = ueberschritt.get('order_number')
                if not auftrag_nr:
                    continue
                
                # Im TEST_MODE mit Dummy-Daten: Verwende Fallback-Betrieb
                if TEST_MODE and auftrag_nr.startswith('TEST-'):
                    # Verwende Betrieb 1 (Deggendorf) als Fallback für Test
                    auftraege_mit_sb[auftrag_nr] = (None, 1)
                    # Füge Fallback-User hinzu
                    if 1 in FALLBACK_USER_BY_BETRIEB:
                        for fallback_nr in FALLBACK_USER_BY_BETRIEB[1]:
                            alle_employee_nrs.add(fallback_nr)
                    continue
                
                # Auftrag-Details holen für Serviceberater-Nr
                try:
                    auftrag_detail = WerkstattData.get_auftrag_detail(auftrag_nr)
                    if auftrag_detail.get('success'):
                        auftrag = auftrag_detail['auftrag']
                        serviceberater_nr = auftrag.get('serviceberater_nr')
                        betrieb = auftrag.get('betrieb')
                        
                        auftraege_mit_sb[auftrag_nr] = (serviceberater_nr, betrieb)
                        
                        # Serviceberater hinzufügen
                        if serviceberater_nr:
                            alle_employee_nrs.add(serviceberater_nr)
                        # Fallback-User hinzufügen
                        if betrieb and betrieb in FALLBACK_USER_BY_BETRIEB:
                            for fallback_nr in FALLBACK_USER_BY_BETRIEB[betrieb]:
                                alle_employee_nrs.add(fallback_nr)
                except Exception as e:
                    logger.warning(f"Fehler beim Holen von Auftrag {auftrag_nr}: {e}")
                    continue
            
            # Im TEST_MODE: Auch ohne Employee-Nummern weiter machen (Test-Mail wird trotzdem gesendet)
            if not alle_employee_nrs and not TEST_MODE:
                return {'success': True, 'message': 'Keine relevanten Employee-Nummern gefunden'}
            
            # E-Mail-Adressen aus employees-Tabelle holen
            cursor.execute("""
                SELECT 
                    e.id,
                    e.first_name,
                    e.last_name,
                    e.email,
                    lem.locosoft_id
                FROM employees e
                LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
                WHERE lem.locosoft_id = ANY(%s)
                  AND e.aktiv = true
                  AND e.email IS NOT NULL
            """, (list(alle_employee_nrs),))
            
            employee_emails = {}
            for row in cursor.fetchall():
                locosoft_id = row[4]
                if locosoft_id:
                    employee_emails[locosoft_id] = {
                        'email': row[3],
                        'name': f"{row[1]} {row[2]}".strip()
                    }
        
        # Für jeden betroffenen User: E-Mail senden
        connector = GraphMailConnector()
        emails_gesendet = 0
        
        for auftrag_nr, (serviceberater_nr, betrieb) in auftraege_mit_sb.items():
            try:
                # Im TEST_MODE mit Dummy-Daten: Verwende Dummy-Werte
                if TEST_MODE and auftrag_nr.startswith('TEST-'):
                    auftrag = {
                        'auftrag_nr': auftrag_nr,
                        'summen': {'gestempelt_min': 120, 'total_aw': 10},
                        'fahrzeug': {'kennzeichen': 'TEST-XX', 'marke': 'Test', 'modell': 'Fahrzeug'},
                        'serviceberater_nr': None,
                        'betrieb': betrieb or 1
                    }
                    s = auftrag.get('summen', {})
                    f = auftrag.get('fahrzeug', {})
                else:
                    auftrag_detail = WerkstattData.get_auftrag_detail(auftrag_nr)
                    if not auftrag_detail.get('success'):
                        continue
                    
                    auftrag = auftrag_detail['auftrag']
                    s = auftrag.get('summen', {})
                    f = auftrag.get('fahrzeug', {})
                
                # Berechne Überschreitung
                gestempelt_min = s.get('gestempelt_min', 0)
                vorgabe_min = (s.get('total_aw', 0) * 6)
                diff_min = gestempelt_min - vorgabe_min
                diff_prozent = (gestempelt_min / vorgabe_min * 100) if vorgabe_min > 0 else 0
                
                # Empfänger bestimmen
                empfaenger = []
                
                # Fall 1: Serviceberater zugeordnet
                if serviceberater_nr and serviceberater_nr in employee_emails:
                    empfaenger.append(employee_emails[serviceberater_nr])
                
                # Fall 2: Kein Serviceberater → Fallback-User
                if not serviceberater_nr and betrieb and betrieb in FALLBACK_USER_BY_BETRIEB:
                    for fallback_nr in FALLBACK_USER_BY_BETRIEB[betrieb]:
                        if fallback_nr in employee_emails:
                            empfaenger.append(employee_emails[fallback_nr])
                
                # Im TEST_MODE: Auch ohne Empfänger weiter machen (Test-Mail wird trotzdem gesendet)
                if not empfaenger and not TEST_MODE:
                    continue
                
                # E-Mail-Inhalt
                betrieb_name = {1: 'Deggendorf', 2: 'Deggendorf Hyundai', 3: 'Landau'}.get(betrieb, 'Unbekannt')
                hat_sb = serviceberater_nr and serviceberater_nr > 0
                
                subject = f"⚠️ Auftrag {auftrag_nr} überschreitet Vorgabe ({betrieb_name})"
                
                if hat_sb:
                    body_intro = f"<p>Ihr Auftrag <strong>{auftrag_nr}</strong> liegt deutlich über der Vorgabe.</p>"
                else:
                    body_intro = f"<p>Auftrag <strong>{auftrag_nr}</strong> ({betrieb_name}) hat keinen zugeordneten Serviceberater und überschreitet die Vorgabe.</p>"
                
                body_html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px;">
                    <h2 style="color: #dc3545;">⚠️ Auftrag überschreitet Vorgabe</h2>
                    {body_intro}
                    
                    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Auftrag</td>
                            <td style="padding: 10px; border: 1px solid #dee2e6;">{auftrag_nr}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Fahrzeug</td>
                            <td style="padding: 10px; border: 1px solid #dee2e6;">{f.get('kennzeichen', '-')} - {f.get('marke', '')} {f.get('modell', '')}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Betrieb</td>
                            <td style="padding: 10px; border: 1px solid #dee2e6;">{betrieb_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Gestempelt</td>
                            <td style="padding: 10px; border: 1px solid #dee2e6;">{int(gestempelt_min)} min ({gestempelt_min/60:.1f} Std)</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Vorgabe</td>
                            <td style="padding: 10px; border: 1px solid #dee2e6;">{int(vorgabe_min)} min ({vorgabe_min/60:.1f} Std)</td>
                        </tr>
                        <tr style="background: #fff5f5;">
                            <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold; color: #dc3545;">Überschreitung</td>
                            <td style="padding: 10px; border: 1px solid #dee2e6; color: #dc3545; font-weight: bold;">+{int(diff_min)} min ({diff_prozent:.0f}%)</td>
                        </tr>
                    </table>
                    
                    <div style="background: #cce5ff; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; margin: 20px 0;">
                        <strong>💡 Mögliche Ursachen:</strong>
                        <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                            <li>Teile fehlen oder verzögert?</li>
                            <li>Unterstützung durch Kollegen nötig?</li>
                            <li>Vorgabe zu niedrig angesetzt?</li>
                            <li>Unvorhergesehene Probleme aufgetreten?</li>
                        </ul>
                    </div>
                    
                    <p style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin: 20px 0;">
                        <strong>📋 Aktion erforderlich:</strong><br>
                        Bitte im <a href="http://drive.auto-greiner.de/werkstatt/cockpit">Greiner DRIVE Portal</a> prüfen und Maßnahmen einleiten.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
                    <p style="color: #6c757d; font-size: 12px;">Diese E-Mail wurde automatisch vom Greiner DRIVE Portal gesendet.</p>
                </div>
                """
                
                # E-Mail senden
                for emp in empfaenger:
                    try:
                        connector.send_mail(
                            sender_email='drive@auto-greiner.de',
                            to_emails=[emp['email']],
                            subject=subject,
                            body_html=body_html
                        )
                        emails_gesendet += 1
                        logger.info(f"E-Mail gesendet an {emp['name']} ({emp['email']}) für Auftrag {auftrag_nr}")
                    except Exception as e:
                        logger.error(f"Fehler beim Senden an {emp['email']}: {e}")
                
                # TEST: Zusätzlich Test-Mail an Florian Greiner senden
                test_subject = f"[TEST] {subject}" if TEST_MODE else f"[KOPIE] {subject}"
                test_body = f"<div style='background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin-bottom: 20px;'><strong>⚠️ {'TEST-MAIL' if TEST_MODE else 'KOPIE'}:</strong> Diese E-Mail wurde {'als Test gesendet (keine echten Überschreitungen gefunden)' if TEST_MODE else 'als Kopie an Florian gesendet'}.</div>{body_html}"
                try:
                    connector.send_mail(
                        sender_email='drive@auto-greiner.de',
                        to_emails=['florian.greiner@auto-greiner.de'],
                        subject=test_subject,
                        body_html=test_body
                    )
                    logger.info(f"Test-E-Mail gesendet an florian.greiner@auto-greiner.de für Auftrag {auftrag_nr} (TEST_MODE={TEST_MODE})")
                except Exception as e:
                    logger.error(f"Fehler beim Senden der Test-Mail an Florian: {e}")
            
            except Exception as e:
                logger.error(f"Fehler bei Auftrag {auftrag_nr}: {e}")
                continue
        
        return {
            'success': True,
            'ueberschritten_anzahl': len(ueberschritten),
            'emails_gesendet': emails_gesendet
        }
    
    except Exception as e:
        logger.exception("Fehler bei Serviceberater-Benachrichtigungen")
        return {'success': False, 'error': str(e)}
