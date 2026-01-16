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
        
        # ZUSÄTZLICH: Hole alle Aufträge, die überschritten sind (NUR abgeschlossene, keine aktiven Mechaniker)
        # TAG 192: KORRIGIERT - Nur abgeschlossene Aufträge, aktive werden aus stempeluhr_data geholt
        # Problem: Wenn Mechaniker erst vor kurzem angestempelt hat, sollte nur seine Laufzeit zählen,
        # nicht die Gesamtlaufzeit des Auftrags über alle Mechaniker hinweg
        ueberschritten_abgeschlossen = []
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                WITH gestempelt_gesamt AS (
                    -- TAG 192: GESAMTE Laufzeit berechnen (alle Tage, alle Mechaniker)
                    -- Nur für abgeschlossene Aufträge (keine aktiven Mechaniker)
                    -- TAG 192: KORRIGIERT - Nur Aufträge von HEUTE oder GESTERN
                    -- Problem: Alte Aufträge (z.B. vom 12.12.2025) wurden noch benachrichtigt
                    SELECT
                        order_number,
                        SUM(minuten) as laufzeit_min
                    FROM (
                        SELECT DISTINCT ON (order_number, employee_number, start_time, end_time)
                            order_number,
                            employee_number,
                            start_time,
                            end_time,
                            EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time)) / 60 as minuten
                        FROM times
                        WHERE order_number > 0
                          AND type = 2
                          AND end_time IS NOT NULL
                          -- TAG 192: Nur Stempelungen von HEUTE oder GESTERN
                          AND DATE(start_time) >= CURRENT_DATE - INTERVAL '1 day'
                        ORDER BY order_number, employee_number, start_time, end_time
                    ) t
                    GROUP BY order_number
                ),
                -- TAG 192: Nur Aufträge OHNE aktive Mechaniker (abgeschlossene Aufträge)
                auftraege_ohne_aktive_mechaniker AS (
                    SELECT DISTINCT order_number
                    FROM gestempelt_gesamt
                    WHERE order_number NOT IN (
                        -- Ausschließen: Aufträge mit aktiven Mechanikern (werden aus stempeluhr_data geholt)
                        SELECT DISTINCT order_number
                        FROM times
                        WHERE end_time IS NULL
                          AND type = 2
                          AND order_number > 31
                          AND DATE(start_time) = CURRENT_DATE
                    )
                ),
                laufzeit_gesamt AS (
                    SELECT 
                        gg.order_number,
                        gg.laufzeit_min
                    FROM gestempelt_gesamt gg
                    INNER JOIN auftraege_ohne_aktive_mechaniker aom ON gg.order_number = aom.order_number
                ),
                vorgabe_aw AS (
                    SELECT
                        l.order_number,
                        SUM(l.time_units) as vorgabe_aw
                    FROM labours l
                    WHERE l.time_units > 0
                    GROUP BY l.order_number
                ),
                -- Prüfe ob Auftrag noch offene (nicht fakturierte) Positionen hat
                offene_positionen AS (
                    SELECT
                        l.order_number,
                        COUNT(*) as anzahl_offen
                    FROM labours l
                    WHERE l.time_units > 0
                      AND l.is_invoiced = false
                    GROUP BY l.order_number
                )
                SELECT
                    lg.order_number,
                    lg.laufzeit_min as gestempelt_min,  -- Für Kompatibilität mit altem Code
                    lg.laufzeit_min,  -- Neue Feld: Gesamte Laufzeit
                    v.vorgabe_aw,
                    (lg.laufzeit_min / (v.vorgabe_aw * 6) * 100) as fortschritt_prozent,
                    o.order_taking_employee_no as serviceberater_nr
                FROM laufzeit_gesamt lg
                JOIN vorgabe_aw v ON lg.order_number = v.order_number
                JOIN orders o ON lg.order_number = o.number
                -- WICHTIG: Nur Aufträge mit offenen Positionen (noch nicht vollständig fakturiert)
                LEFT JOIN offene_positionen op ON lg.order_number = op.order_number
                WHERE v.vorgabe_aw > 0
                  AND (lg.laufzeit_min / (v.vorgabe_aw * 6) * 100) > 100
                  AND (op.anzahl_offen > 0 OR op.anzahl_offen IS NULL)
                  AND o.has_open_positions = true
            """)
            ueberschritten_abgeschlossen = cursor.fetchall()
        
        if not stempeluhr_data.get('success'):
            # Wenn Stempeluhr-Daten nicht verfügbar, nutze nur abgeschlossene
            ueberschritten = ueberschritten_abgeschlossen
        else:
            aktive_mechaniker = stempeluhr_data.get('aktive_mechaniker', [])
            # Filter: Nur Aufträge mit Überschreitung UND noch offenen Positionen
            # (abgeschlossene/fakturierte Aufträge werden ausgeschlossen)
            ueberschritten_aktiv = [
                m for m in aktive_mechaniker 
                if m.get('fortschritt_prozent', 0) > 100
                # Zusätzliche Prüfung: Hole Auftrag-Details um has_open_positions zu prüfen
                # (wird später in der Schleife gemacht, hier nur Überschreitung filtern)
            ]
            
            # Kombiniere aktive und abgeschlossene Überschreitungen
            auftrag_nrs_aktiv = {m.get('order_number') for m in ueberschritten_aktiv}
            ueberschritten = ueberschritten_aktiv + [
                u for u in ueberschritten_abgeschlossen
                if u['order_number'] not in auftrag_nrs_aktiv
            ]
        
        logger.info(f"{len(ueberschritten)} Überschreitungen gefunden")
        
        if not ueberschritten:
            return {'success': True, 'message': 'Keine Überschreitungen gefunden'}
        
        # TAG 185: Quality-Check: Matthias König (3007) erhält IMMER alle Überschreitungs-Emails
        QUALITY_CHECK_USER = 3007  # Matthias König
        
        # Fallback-User Mapping (TAG 182: Nur Matthias König für alle Betriebe)
        FALLBACK_USER_BY_BETRIEB = {
            1: [3007],  # Deggendorf: Matthias König
            2: [3007],  # Deggendorf Hyundai: Matthias König
            3: [3007]    # Landau: Matthias König
        }
        
        # E-Mail-Adressen aus DB holen
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Hole alle relevanten employee_numbers (Serviceberater + Quality-Check + Fallback)
            alle_employee_nrs = set()
            auftraege_mit_sb = {}  # auftrag_nr -> (serviceberater_nr, betrieb)
            
            for ueberschritt in ueberschritten:
                auftrag_nr = ueberschritt.get('order_number')
                if not auftrag_nr:
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
                        # TAG 185: Quality-Check - Matthias König IMMER hinzufügen
                        alle_employee_nrs.add(QUALITY_CHECK_USER)
                        # Fallback-User hinzufügen (falls kein Serviceberater)
                        if not serviceberater_nr and betrieb and betrieb in FALLBACK_USER_BY_BETRIEB:
                            for fallback_nr in FALLBACK_USER_BY_BETRIEB[betrieb]:
                                alle_employee_nrs.add(fallback_nr)
                except Exception as e:
                    logger.warning(f"Fehler beim Holen von Auftrag {auftrag_nr}: {e}")
                    continue
            
            if not alle_employee_nrs:
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
        
        # Erstelle Mapping: auftrag_nr -> ueberschritt
        # WICHTIG: Aktive Aufträge zuerst, damit sie nicht von abgeschlossenen überschrieben werden
        ueberschritten_map = {}
        # Zuerst aktive Aufträge (aus stempeluhr_data) - haben korrekte Laufzeit des aktiven Mechanikers
        # TAG 194: FIX - Alle aktiven Aufträge aufnehmen, nicht nur die mit fortschritt_prozent > 100
        # Die Prüfung ob überschritten erfolgt später in der E-Mail-Logik basierend auf heute_session_min
        if stempeluhr_data.get('success'):
            aktive_mechaniker = stempeluhr_data.get('aktive_mechaniker', [])
            for mechaniker in aktive_mechaniker:
                auftrag_nr = mechaniker.get('order_number')
                if auftrag_nr:
                    ueberschritten_map[auftrag_nr] = mechaniker
        # Dann abgeschlossene Aufträge (aus Query) - haben Gesamtlaufzeit
        for ueberschritt in ueberschritten_abgeschlossen:
            auftrag_nr = ueberschritt.get('order_number')
            if auftrag_nr and auftrag_nr not in ueberschritten_map:
                ueberschritten_map[auftrag_nr] = ueberschritt
        
        # Für jeden betroffenen User: E-Mail senden
        connector = GraphMailConnector()
        emails_gesendet = 0
        
        for auftrag_nr, (serviceberater_nr, betrieb) in auftraege_mit_sb.items():
            try:
                # Hole Überschreitungs-Daten
                ueberschritt = ueberschritten_map.get(auftrag_nr)
                if not ueberschritt:
                    logger.warning(f"Auftrag {auftrag_nr} nicht in ueberschritten_map gefunden - überspringe")
                    continue
                
                # TAG 194: FIX - Für aktive Aufträge: Nur heute_session_min verwenden (aktuelle Stempelung)
                # Für abgeschlossene Aufträge: Gesamtlaufzeit
                # Problem: fortschritt_prozent basiert auf laufzeit_min (aktuell + abgeschlossen heute)
                # Aber für E-Mails sollte nur die aktuelle Stempelung (heute_session_min) zählen
                # Beispiel: Mechaniker hat heute 50 Min abgeschlossen, stempelt neu an (20 Min aktuell)
                # - fortschritt_prozent = 70/60 = 117% (basierend auf laufzeit_min)
                # - Aber für E-Mail: 20/60 = 33% (basierend auf heute_session_min) → KEINE E-Mail
                if 'heute_session_min' in ueberschritt:
                    # Aktiver Auftrag: Nur aktuelle Stempelung heute verwenden
                    laufzeit_min = float(ueberschritt.get('heute_session_min', 0))
                    
                    # TAG 193: Mindestlaufzeit-Schwelle (30 Min) für aktive Aufträge
                    # Verhindert E-Mails bei sehr kurzen Stempelungen
                    if laufzeit_min < 30:
                        logger.debug(f"Auftrag {auftrag_nr}: Nur {laufzeit_min:.0f} Min aktuell gestempelt (< 30 Min Schwelle) - überspringe")
                        continue
                else:
                    # Abgeschlossener Auftrag: Gesamtlaufzeit verwenden
                    laufzeit_min = float(ueberschritt.get('laufzeit_min', ueberschritt.get('gestempelt_min', 0)))
                
                # Vorgabe: Entweder direkt als vorgabe_min oder als vorgabe_aw * 6
                if 'vorgabe_min' in ueberschritt:
                    vorgabe_min = float(ueberschritt.get('vorgabe_min', 0))
                    vorgabe_aw = vorgabe_min / 6
                else:
                    vorgabe_aw = float(ueberschritt.get('vorgabe_aw', 0))
                    vorgabe_min = vorgabe_aw * 6
                
                # Berechne Überschreitung
                # TAG 193: Für aktive Aufträge: Nur aktuelle Stempelung (heute_session_min)
                # Für abgeschlossene Aufträge: Gesamtlaufzeit
                diff_min = laufzeit_min - vorgabe_min
                diff_prozent = (laufzeit_min / vorgabe_min * 100) if vorgabe_min > 0 else 0
                
                # WICHTIG: Nur E-Mail senden, wenn tatsächlich überschritten (>100%)
                if diff_prozent <= 100:
                    logger.debug(f"Auftrag {auftrag_nr}: {diff_prozent:.1f}% ist KEINE Überschreitung - überspringe")
                    continue
                
                # Hole Auftrag-Details für Fahrzeug-Info
                auftrag_detail = WerkstattData.get_auftrag_detail(auftrag_nr)
                if not auftrag_detail.get('success'):
                    continue
                
                auftrag = auftrag_detail['auftrag']
                
                # WICHTIG: Prüfe ob Auftrag noch offene Positionen hat
                # (abgeschlossene/fakturierte Aufträge bekommen keine Warn-Email)
                status = auftrag.get('status', {})
                if not status.get('ist_offen', True):
                    logger.debug(f"Auftrag {auftrag_nr} hat keine offenen Positionen mehr - überspringe")
                    continue
                
                f = auftrag.get('fahrzeug', {})
                
                # TAG 193: Für aktive Aufträge: Nur aktuelle Stempelung (heute_session_min)
                # Für abgeschlossene Aufträge: Gesamtlaufzeit
                gestempelt_min = laufzeit_min
                
                # Empfänger bestimmen (TAG 182: Mit Deduplizierung)
                # TAG 185: Quality-Check - Matthias König erhält IMMER alle Emails
                empfaenger = []
                empfaenger_ids = set()  # Verhindert Duplikate
                
                # Fall 1: Serviceberater zugeordnet
                if serviceberater_nr and serviceberater_nr in employee_emails:
                    if serviceberater_nr not in empfaenger_ids:
                        empfaenger.append(employee_emails[serviceberater_nr])
                        empfaenger_ids.add(serviceberater_nr)
                
                # TAG 185: Quality-Check - Matthias König IMMER hinzufügen (zusätzlich zu Serviceberater)
                if QUALITY_CHECK_USER in employee_emails and QUALITY_CHECK_USER not in empfaenger_ids:
                    empfaenger.append(employee_emails[QUALITY_CHECK_USER])
                    empfaenger_ids.add(QUALITY_CHECK_USER)
                
                # Fall 2: Kein Serviceberater → Fallback-User (nur Matthias König)
                # (Wird durch Quality-Check bereits abgedeckt, aber für Sicherheit beibehalten)
                if not serviceberater_nr and betrieb and betrieb in FALLBACK_USER_BY_BETRIEB:
                    for fallback_nr in FALLBACK_USER_BY_BETRIEB[betrieb]:
                        if fallback_nr in employee_emails and fallback_nr not in empfaenger_ids:
                            empfaenger.append(employee_emails[fallback_nr])
                            empfaenger_ids.add(fallback_nr)
                
                if not empfaenger:
                    continue
                
                # TAG 182: Prüfe ob bereits E-Mail für diesen Auftrag heute gesendet wurde
                with db_session() as conn_tracking:
                    cursor_tracking = conn_tracking.cursor()
                    
                    # Prüfe für jeden Empfänger, ob bereits gesendet
                    empfaenger_zu_senden = []
                    for emp in empfaenger:
                        emp_locosoft_id = None
                        # Finde locosoft_id für diesen Empfänger
                        for loco_id, emp_data in employee_emails.items():
                            if emp_data['email'] == emp['email']:
                                emp_locosoft_id = loco_id
                                break
                        
                        if not emp_locosoft_id:
                            continue
                        
                        # Prüfe ob bereits gesendet
                        cursor_tracking.execute("""
                            SELECT 1 FROM email_notifications_sent
                            WHERE auftrag_nr = %s
                              AND employee_locosoft_id = %s
                              AND notification_type = 'ueberschreitung'
                              AND sent_date = CURRENT_DATE
                        """, (auftrag_nr, emp_locosoft_id))
                        
                        if cursor_tracking.fetchone():
                            logger.debug(f"E-Mail für Auftrag {auftrag_nr} an {emp['name']} bereits heute gesendet - überspringe")
                        else:
                            empfaenger_zu_senden.append((emp, emp_locosoft_id))
                    
                    if not empfaenger_zu_senden:
                        logger.debug(f"Alle E-Mails für Auftrag {auftrag_nr} bereits heute gesendet - überspringe")
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
                                <td style="padding: 10px; border: 1px solid #dee2e6; color: #dc3545; font-weight: bold;">+{int(abs(diff_min))} min ({diff_prozent:.0f}%)</td>
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
                    
                    # E-Mail senden (TAG 182: Nur an Empfänger, die noch keine E-Mail erhalten haben)
                    for emp, emp_locosoft_id in empfaenger_zu_senden:
                        try:
                            connector.send_mail(
                                sender_email='drive@auto-greiner.de',
                                to_emails=[emp['email']],
                                subject=subject,
                                body_html=body_html
                            )
                            
                            # TAG 182: Eintrag in Tracking-Tabelle nach erfolgreichem Versand
                            cursor_tracking.execute("""
                                INSERT INTO email_notifications_sent (auftrag_nr, employee_locosoft_id, notification_type, sent_date)
                                VALUES (%s, %s, 'ueberschreitung', CURRENT_DATE)
                                ON CONFLICT DO NOTHING
                            """, (auftrag_nr, emp_locosoft_id))
                            conn_tracking.commit()
                            
                            emails_gesendet += 1
                            logger.info(f"E-Mail gesendet an {emp['name']} ({emp['email']}) für Auftrag {auftrag_nr}")
                        except Exception as e:
                            logger.error(f"Fehler beim Senden an {emp['email']}: {e}")
                            conn_tracking.rollback()
            
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


# =============================================================================
# SERVICEBOX SCRAPER TASKS (TAG 171)
# =============================================================================

@shared_task(soft_time_limit=1800, name='celery_app.tasks.servicebox_scraper')
def servicebox_scraper():
    """
    ServiceBox API-Scraper - Holt Bestellungen aus ServiceBox via API
    TAG 173: Umgestellt auf API-Endpoint für bessere Performance
    Läuft 3x täglich (09:30, 12:30, 16:30)
    """
    import subprocess
    import os
    
    try:
        # TAG 173: Neuer API-Scraper
        script_path = '/opt/greiner-portal/tools/scrapers/servicebox_api_scraper.py'
        if not os.path.exists(script_path):
            # Fallback auf alten Scraper
            script_path = '/opt/greiner-portal/tools/scrapers/servicebox_detail_scraper_final.py'
            logger.warning(f"API-Scraper nicht gefunden, verwende alten Scraper: {script_path}")
        
        if not os.path.exists(script_path):
            logger.error(f"ServiceBox Scraper-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte ServiceBox API-Scraper...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        if result.returncode == 0:
            logger.info("ServiceBox API-Scraper erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}  # Letzte 500 Zeichen
        else:
            logger.error(f"ServiceBox API-Scraper fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("ServiceBox API-Scraper: Timeout nach 30 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei ServiceBox API-Scraper")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.servicebox_matcher')
def servicebox_matcher():
    """
    ServiceBox Matcher - Verknüpft Bestellungen mit Locosoft-Aufträgen
    Läuft nach Scraper (10:00, 13:00, 17:00)
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/scrapers/match_servicebox.py'
        if not os.path.exists(script_path):
            logger.error(f"ServiceBox Matcher-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte ServiceBox Matcher...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("ServiceBox Matcher erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"ServiceBox Matcher fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("ServiceBox Matcher: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei ServiceBox Matcher")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=120, name='celery_app.tasks.servicebox_import')
def servicebox_import():
    """
    ServiceBox Import - Importiert gematchte Bestellungen in DB
    Läuft nach Matcher (10:05, 13:05, 17:05)
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/imports/import_servicebox_to_db.py'
        if not os.path.exists(script_path):
            logger.error(f"ServiceBox Import-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte ServiceBox Import...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            logger.info("ServiceBox Import erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"ServiceBox Import fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("ServiceBox Import: Timeout nach 2 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei ServiceBox Import")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=3600, name='celery_app.tasks.servicebox_master')
def servicebox_master():
    """
    ServiceBox Master - Komplett neu laden (alle Bestellungen)
    Läuft täglich um 20:00
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/tools/scrapers/servicebox_scraper_complete.py'
        if not os.path.exists(script_path):
            logger.error(f"ServiceBox Master-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte ServiceBox Master (komplett neu laden)...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        if result.returncode == 0:
            logger.info("ServiceBox Master erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"ServiceBox Master fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("ServiceBox Master: Timeout nach 60 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei ServiceBox Master")
        return {'success': False, 'error': str(e)}


# =============================================================================
# CONTROLLING & VERWALTUNG - IMPORT TASKS (TAG 173)
# =============================================================================

@shared_task(soft_time_limit=180, name='celery_app.tasks.import_mt940', autoretry_for=(OSError,), retry_kwargs={'max_retries': 3, 'countdown': 30})
def import_mt940():
    """
    MT940 Import - Bank-Kontoauszüge importieren
    Läuft 3x täglich (08:00, 12:00, 17:00)
    Retry bei Mount-Problemen (OSError: Host is down)
    Verbesserte Mount-Prüfung mit Retry-Logik
    """
    import subprocess
    import os
    import time
    
    mt940_dir = '/mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/'
    script_path = '/opt/greiner-portal/scripts/imports/import_mt940.py'
    
    # Prüfe Script
    if not os.path.exists(script_path):
        logger.error(f"MT940 Import-Script nicht gefunden: {script_path}")
        return {'success': False, 'error': 'Script nicht gefunden'}
    
    # Verbesserte Mount-Prüfung mit Retry
    mount_ok = False
    for attempt in range(3):
        try:
            if os.path.exists(mt940_dir):
                # Zusätzliche Prüfung: Versuche Verzeichnis zu lesen
                try:
                    os.listdir(mt940_dir)
                    mount_ok = True
                    break
                except (OSError, PermissionError) as e:
                    if attempt < 2:
                        logger.warning(f"Mount-Prüfung fehlgeschlagen (Versuch {attempt + 1}/3): {e}, warte 2s...")
                        time.sleep(2)
                        continue
                    else:
                        logger.error(f"Mount nicht verfügbar nach 3 Versuchen: {e}")
            else:
                if attempt < 2:
                    logger.warning(f"Mount-Verzeichnis nicht gefunden (Versuch {attempt + 1}/3), warte 2s...")
                    time.sleep(2)
                    continue
        except Exception as e:
            if attempt < 2:
                logger.warning(f"Fehler bei Mount-Prüfung (Versuch {attempt + 1}/3): {e}, warte 2s...")
                time.sleep(2)
                continue
    
    if not mount_ok:
        error_msg = f"Mount-Verzeichnis nicht verfügbar: {mt940_dir}"
        logger.error(error_msg)
        # Wirf OSError für automatischen Retry
        raise OSError(112, error_msg)
    
    try:
        logger.info("Starte MT940 Import...")
        # Script hat jetzt eigene Retry-Logik (--retry 3)
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path, 
             '--retry', '3', '--retry-delay', '2', mt940_dir],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=180  # Erhöht auf 3 Minuten
        )
        
        if result.returncode == 0:
            logger.info("MT940 Import erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            error_msg = result.stderr[-500:] if result.stderr else result.stdout[-500:]
            logger.error(f"MT940 Import fehlgeschlagen: {error_msg}")
            
            # Bei Mount-Fehlern: Retry auslösen
            if 'Host is down' in error_msg or 'Errno 112' in error_msg:
                raise OSError(112, f"Mount-Problem: {error_msg}")
            
            return {'success': False, 'error': error_msg}
    
    except subprocess.TimeoutExpired:
        logger.error("MT940 Import: Timeout nach 3 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except OSError as e:
        # Mount-Problem - wird automatisch retried
        error_msg = f"Mount-Problem: {str(e)}"
        logger.warning(error_msg)
        raise  # Wird von autoretry_for behandelt
    except Exception as e:
        logger.exception("Fehler bei MT940 Import")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=120, name='celery_app.tasks.import_hvb_pdf')
def import_hvb_pdf():
    """
    HypoVereinsbank PDF Import - HVB PDF-Auszüge importieren
    Läuft täglich um 08:30
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/imports/import_all_bank_pdfs.py'
        if not os.path.exists(script_path):
            logger.error(f"HVB PDF Import-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte HypoVereinsbank PDF Import...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path,
             '--bank', 'hvb', '--days', '3'],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            logger.info("HVB PDF Import erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"HVB PDF Import fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("HVB PDF Import: Timeout nach 2 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei HVB PDF Import")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.import_santander')
def import_santander():
    """
    Santander Import - Santander Bestand importieren
    Läuft täglich um 08:15
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/imports/import_santander_bestand.py'
        if not os.path.exists(script_path):
            logger.error(f"Santander Import-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Santander Import...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Santander Import erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Santander Import fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Santander Import: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Santander Import")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.import_hyundai')
def import_hyundai():
    """
    Hyundai Finance Import - Hyundai Finance CSV importieren
    Läuft täglich um 09:00
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/imports/import_hyundai_finance.py'
        if not os.path.exists(script_path):
            logger.error(f"Hyundai Import-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Hyundai Finance Import...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Hyundai Import erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Hyundai Import fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Hyundai Import: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Hyundai Import")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=180, name='celery_app.tasks.scrape_hyundai')
def scrape_hyundai():
    """
    Hyundai Scraper - Hyundai Portal scrapen
    Läuft täglich um 08:45
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/tools/scrapers/hyundai_bestandsliste_scraper.py'
        if not os.path.exists(script_path):
            logger.error(f"Hyundai Scraper-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Hyundai Scraper...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            logger.info("Hyundai Scraper erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Hyundai Scraper fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Hyundai Scraper: Timeout nach 3 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Hyundai Scraper")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=60, name='celery_app.tasks.leasys_cache_refresh')
def leasys_cache_refresh():
    """
    Leasys Cache Refresh - Leasys Cache aktualisieren
    Läuft alle 30 Minuten während Arbeitszeit (7-18 Uhr)
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/update_leasys_cache.py'
        if not os.path.exists(script_path):
            logger.error(f"Leasys Cache-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Leasys Cache Refresh...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("Leasys Cache Refresh erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Leasys Cache Refresh fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Leasys Cache Refresh: Timeout nach 1 Minute")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Leasys Cache Refresh")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.umsatz_bereinigung')
def umsatz_bereinigung():
    """
    Umsatz-Bereinigung - Umsatzdaten bereinigen
    Läuft täglich um 09:30
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/analysis/umsatz_bereinigung_production.py'
        if not os.path.exists(script_path):
            logger.error(f"Umsatz-Bereinigung-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Umsatz-Bereinigung...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Umsatz-Bereinigung erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Umsatz-Bereinigung fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Umsatz-Bereinigung: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Umsatz-Bereinigung")
        return {'success': False, 'error': str(e)}


# =============================================================================
# SYNC TASKS (TAG 173)
# =============================================================================

@shared_task(soft_time_limit=300, name='celery_app.tasks.sync_employees')
def sync_employees():
    """
    Mitarbeiter Sync - Mitarbeiter synchronisieren
    Läuft täglich um 06:00
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/sync/sync_employees.py'
        if not os.path.exists(script_path):
            logger.error(f"Mitarbeiter Sync-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Mitarbeiter Sync...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Mitarbeiter Sync erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Mitarbeiter Sync fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Mitarbeiter Sync: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Mitarbeiter Sync")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.sync_locosoft_employees')
def sync_locosoft_employees():
    """
    Locosoft Employees Sync - Locosoft Employee Mapping
    Läuft täglich um 06:15
    """
    import subprocess
    import os
    
    try:
        # Prüfe verschiedene mögliche Pfade
        script_paths = [
            '/opt/greiner-portal/scripts/sync/sync_ldap_employees.py',
            '/opt/greiner-portal/scripts/sync/sync_employees.py'
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            logger.error(f"Locosoft Employees Sync-Script nicht gefunden")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Locosoft Employees Sync...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Locosoft Employees Sync erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Locosoft Employees Sync fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Locosoft Employees Sync: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Locosoft Employees Sync")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.sync_ad_departments')
def sync_ad_departments():
    """
    AD Abteilungen Sync - Abteilungen aus Active Directory
    Läuft täglich um 06:20
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/sync/sync_ad_departments.py'
        if not os.path.exists(script_path):
            logger.error(f"AD Abteilungen Sync-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte AD Abteilungen Sync...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("AD Abteilungen Sync erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"AD Abteilungen Sync fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("AD Abteilungen Sync: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei AD Abteilungen Sync")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=600, name='celery_app.tasks.sync_sales')
def sync_sales():
    """
    Verkauf Sync - Verkaufsdaten synchronisieren
    Läuft stündlich während Arbeitszeit (7-18 Uhr)
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/sync/sync_sales.py'
        if not os.path.exists(script_path):
            logger.error(f"Verkauf Sync-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Verkauf Sync...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            logger.info("Verkauf Sync erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Verkauf Sync fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Verkauf Sync: Timeout nach 10 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Verkauf Sync")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.sync_stammdaten')
def sync_stammdaten():
    """
    Stammdaten Sync - Fahrzeug-Stammdaten sync
    Läuft täglich um 09:30
    """
    import subprocess
    import os
    
    try:
        script_paths = [
            '/opt/greiner-portal/scripts/sync/sync_stammdaten.py',
            '/opt/greiner-portal/scripts/sync/sync_fahrzeug_stammdaten.py'
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            logger.error(f"Stammdaten Sync-Script nicht gefunden")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Stammdaten Sync...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Stammdaten Sync erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Stammdaten Sync fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Stammdaten Sync: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Stammdaten Sync")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=3600, name='celery_app.tasks.locosoft_mirror')
def locosoft_mirror():
    """
    Locosoft Mirror - Locosoft komplett spiegeln
    Läuft täglich um 19:00
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/sync/locosoft_mirror.py'
        if not os.path.exists(script_path):
            logger.error(f"Locosoft Mirror-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Locosoft Mirror...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        if result.returncode == 0:
            logger.info("Locosoft Mirror erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Locosoft Mirror fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Locosoft Mirror: Timeout nach 60 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Locosoft Mirror")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.sync_teile')
def sync_teile():
    """
    Teile Sync - Teile synchronisieren
    Läuft alle 30 Minuten
    """
    import subprocess
    import os
    
    try:
        script_paths = [
            '/opt/greiner-portal/scripts/sync/sync_teile.py',
            '/opt/greiner-portal/scripts/imports/sync_teile_locosoft.py'
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            logger.error(f"Teile Sync-Script nicht gefunden")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Teile Sync...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Teile Sync erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Teile Sync fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Teile Sync: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Teile Sync")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.sync_charge_types')
def sync_charge_types():
    """
    Charge Types Sync - AW-Preise synchronisieren
    Läuft täglich um 06:05
    WICHTIG: Script muss noch auf PostgreSQL migriert werden!
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/imports/sync_charge_types.py'
        if not os.path.exists(script_path):
            logger.error(f"Charge Types Sync-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Charge Types Sync...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Charge Types Sync erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Charge Types Sync fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Charge Types Sync: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Charge Types Sync")
        return {'success': False, 'error': str(e)}


# =============================================================================
# VERKAUF TASKS (TAG 173)
# =============================================================================

@shared_task(soft_time_limit=300, name='celery_app.tasks.import_stellantis')
def import_stellantis():
    """
    Stellantis Import - Stellantis Fahrzeuge importieren
    Läuft täglich um 07:30
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/imports/import_stellantis.py'
        if not os.path.exists(script_path):
            logger.error(f"Stellantis Import-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Stellantis Import...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Stellantis Import erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Stellantis Import fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Stellantis Import: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Stellantis Import")
        return {'success': False, 'error': str(e)}


# =============================================================================
# AFTERSALES TASKS (TAG 173)
# =============================================================================

@shared_task(soft_time_limit=300, name='celery_app.tasks.import_teile')
def import_teile():
    """
    Teile Import - Teile-Lieferscheine importieren
    Läuft alle 2 Stunden
    """
    import subprocess
    import os
    
    try:
        script_paths = [
            '/opt/greiner-portal/scripts/imports/import_teile.py',
            '/opt/greiner-portal/scripts/imports/import_teile_lieferscheine.py'
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            logger.error(f"Teile Import-Script nicht gefunden")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Teile Import...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Teile Import erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Teile Import fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Teile Import: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Teile Import")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.werkstatt_leistung')
def werkstatt_leistung():
    """
    Werkstatt Leistung - Leistungsgrade berechnen
    Läuft täglich um 19:15
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/sync/sync_werkstatt_zeiten.py'
        if not os.path.exists(script_path):
            logger.error(f"Werkstatt Leistung-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Werkstatt Leistung...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Werkstatt Leistung erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Werkstatt Leistung fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Werkstatt Leistung: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Werkstatt Leistung")
        return {'success': False, 'error': str(e)}


# =============================================================================
# E-MAIL TASKS (TAG 173)
# =============================================================================

@shared_task(soft_time_limit=300, name='celery_app.tasks.email_auftragseingang')
def email_auftragseingang():
    """
    E-Mail Auftragseingang - Täglichen Report senden
    Läuft täglich um 17:15
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/send_daily_auftragseingang.py'
        if not os.path.exists(script_path):
            logger.error(f"E-Mail Auftragseingang-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte E-Mail Auftragseingang...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("E-Mail Auftragseingang erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"E-Mail Auftragseingang fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("E-Mail Auftragseingang: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei E-Mail Auftragseingang")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.email_werkstatt_tagesbericht')
def email_werkstatt_tagesbericht():
    """
    Werkstatt E-Mail - Tagesbericht senden
    Läuft täglich um 17:30
    """
    import subprocess
    import os
    
    try:
        # TAG176: Fallback auf TEK-Script entfernt - war falsch!
        script_path = '/opt/greiner-portal/scripts/send_daily_werkstatt_tagesbericht.py'
        
        if not os.path.exists(script_path):
            logger.error(f"Werkstatt E-Mail-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': f'Script nicht gefunden: {script_path}'}
        
        logger.info("Starte Werkstatt E-Mail...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Werkstatt E-Mail erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Werkstatt E-Mail fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Werkstatt E-Mail: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Werkstatt E-Mail")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=600, name='celery_app.tasks.email_tek_daily')
def email_tek_daily():
    """
    TEK E-Mail - Tägliche Erfolgskontrolle per E-Mail
    Läuft täglich um 19:30 (nach Locosoft Mirror um 19:00)
    
    TAG 176: Aktiviert - nach Locosoft PostgreSQL-Befüllung (19:00 Uhr)
    TAG 181: Zeitprüfung hinzugefügt - verhindert Versand vor 19:00 Uhr
    """
    import subprocess
    import os
    from datetime import datetime
    
    try:
        # TAG 181: Zeitprüfung - TEK sollte erst nach 19:00 Uhr gesendet werden
        jetzt = datetime.now()
        if jetzt.hour < 19:
            error_msg = f"TEK E-Mail: Zu früh ({jetzt.strftime('%H:%M')} Uhr) - sollte erst nach 19:00 Uhr gesendet werden (nach Locosoft PostgreSQL Update)"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        # Prüfe verschiedene mögliche Pfade
        script_paths = [
            '/opt/greiner-portal/scripts/send_daily_tek.py',
            '/opt/greiner-portal/send_daily_tek.py'
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            logger.error(f"TEK E-Mail-Script nicht gefunden")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte TEK E-Mail-Versand...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            logger.info("TEK E-Mail erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            # TAG 186: Logge sowohl stdout als auch stderr für besseres Debugging
            error_msg = result.stderr[-500:] if result.stderr else result.stdout[-500:] if result.stdout else 'Unbekannter Fehler'
            logger.error(f"TEK E-Mail fehlgeschlagen (Exit Code: {result.returncode}): {error_msg}")
            if result.stdout:
                logger.info(f"TEK Script stdout: {result.stdout[-500:]}")
            return {'success': False, 'error': error_msg, 'exit_code': result.returncode}
    
    except subprocess.TimeoutExpired:
        logger.error("TEK E-Mail: Timeout nach 10 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei TEK E-Mail")
        return {'success': False, 'error': str(e)}


# =============================================================================
# CONTROLLING TASKS (TAG 173)
# =============================================================================

@shared_task(soft_time_limit=600, name='celery_app.tasks.refresh_finanzreporting_cube')
def refresh_finanzreporting_cube():
    """
    Finanzreporting Cube Refresh - Materialized Views aktualisieren
    Läuft täglich um 19:20 (nach Locosoft Mirror um 19:00)
    
    TAG 179: Automatischer Refresh nach Locosoft-Sync
    """
    try:
        from api.db_utils import db_session
        
        logger.info("Starte Finanzreporting Cube Refresh...")
        start_time = datetime.now()
        
        with db_session() as conn:
            cursor = conn.cursor()
            # Rufe PostgreSQL-Funktion auf, die alle Materialized Views aktualisiert
            cursor.execute("SELECT refresh_finanzreporting_cube()")
            conn.commit()
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Finanzreporting Cube Refresh erfolgreich abgeschlossen (Dauer: {duration:.1f}s)")
        
        return {
            'success': True,
            'message': 'Cube erfolgreich aktualisiert',
            'duration_seconds': duration
        }
    
    except Exception as e:
        logger.exception("Fehler bei Finanzreporting Cube Refresh")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=600, name='celery_app.tasks.bwa_berechnung')
def bwa_berechnung():
    """
    BWA Berechnung - BWA aus Locosoft berechnen
    Läuft täglich um 19:30
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/sync/bwa_berechnung.py'
        if not os.path.exists(script_path):
            logger.error(f"BWA Berechnung-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte BWA Berechnung...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            logger.info("BWA Berechnung erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"BWA Berechnung fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("BWA Berechnung: Timeout nach 10 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei BWA Berechnung")
        return {'success': False, 'error': str(e)}


# =============================================================================
# BACKUP & WARTUNG TASKS (TAG 173)
# =============================================================================

@shared_task(soft_time_limit=3600, name='celery_app.tasks.db_backup')
def db_backup():
    """
    DB Backup - Datenbank-Backup erstellen
    Läuft täglich um 03:00
    """
    import subprocess
    import os
    
    try:
        # Prüfe verschiedene mögliche Pfade
        script_paths = [
            '/opt/greiner-portal/scripts/backup/db_backup.py',
            '/opt/greiner-portal/scripts/db_backup.py'
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            logger.warning("DB Backup-Script nicht gefunden - verwende pg_dump direkt")
            # Fallback: pg_dump direkt aufrufen
            result = subprocess.run(
                ['pg_dump', '-h', '127.0.0.1', '-U', 'drive_user', '-d', 'drive_portal',
                 '-f', f'/opt/greiner-portal/data/backups/db_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql'],
                cwd='/opt/greiner-portal',
                capture_output=True,
                text=True,
                timeout=3600,
                env={**os.environ, 'PGPASSWORD': 'DrivePortal2024'}
            )
            
            if result.returncode == 0:
                logger.info("DB Backup erfolgreich abgeschlossen (pg_dump)")
                return {'success': True, 'stdout': result.stdout[-500:]}
            else:
                logger.error(f"DB Backup fehlgeschlagen: {result.stderr}")
                return {'success': False, 'error': result.stderr[-500:]}
        
        logger.info("Starte DB Backup...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        if result.returncode == 0:
            logger.info("DB Backup erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"DB Backup fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("DB Backup: Timeout nach 60 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei DB Backup")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.cleanup_backups')
def cleanup_backups():
    """
    Backup Cleanup - Alte Backups löschen
    Läuft täglich um 03:30
    """
    import subprocess
    import os
    from pathlib import Path
    
    try:
        # Prüfe verschiedene mögliche Pfade
        script_paths = [
            '/opt/greiner-portal/scripts/backup/cleanup_backups.py',
            '/opt/greiner-portal/scripts/cleanup_backups.py'
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            logger.warning("Backup Cleanup-Script nicht gefunden - verwende einfache Logik")
            # Fallback: Einfache Cleanup-Logik
            backup_dir = Path('/opt/greiner-portal/data/backups')
            if backup_dir.exists():
                import time
                now = time.time()
                deleted = 0
                for backup_file in backup_dir.glob('*.sql'):
                    # Lösche Backups älter als 30 Tage
                    if now - backup_file.stat().st_mtime > 30 * 24 * 3600:
                        backup_file.unlink()
                        deleted += 1
                
                logger.info(f"Backup Cleanup: {deleted} alte Backups gelöscht")
                return {'success': True, 'deleted': deleted}
            else:
                return {'success': True, 'message': 'Backup-Verzeichnis nicht gefunden'}
        
        logger.info("Starte Backup Cleanup...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Backup Cleanup erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Backup Cleanup fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Backup Cleanup: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Backup Cleanup")
        return {'success': False, 'error': str(e)}


# =============================================================================
# WEITERE TASKS (TAG 173)
# =============================================================================

@shared_task(soft_time_limit=3600, name='celery_app.tasks.ml_retrain')
def ml_retrain():
    """
    ML Training - Modell neu trainieren
    Läuft täglich um 03:15
    """
    import subprocess
    import os
    
    try:
        # Prüfe verschiedene mögliche Pfade
        script_paths = [
            '/opt/greiner-portal/scripts/ml/retrain.py',
            '/opt/greiner-portal/scripts/retrain_ml.py'
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            logger.warning("ML Training-Script nicht gefunden")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte ML Training...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        if result.returncode == 0:
            logger.info("ML Training erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"ML Training fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("ML Training: Timeout nach 60 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei ML Training")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.update_penner_marktpreise')
def update_penner_marktpreise():
    """
    Penner Marktpreise - Marktpreise aktualisieren
    Läuft täglich um 03:00
    """
    import subprocess
    import os
    
    try:
        # Prüfe verschiedene mögliche Pfade
        script_paths = [
            '/opt/greiner-portal/scripts/penner/update_marktpreise.py',
            '/opt/greiner-portal/scripts/update_penner_marktpreise.py'
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            logger.warning("Penner Marktpreise-Script nicht gefunden")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Penner Marktpreise Update...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Penner Marktpreise Update erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Penner Marktpreise Update fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Penner Marktpreise Update: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Penner Marktpreise Update")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.email_penner_weekly')
def email_penner_weekly():
    """
    Penner Wochenreport - Wochenreport senden
    Läuft Montag um 07:00
    """
    import subprocess
    import os
    
    try:
        script_path = '/opt/greiner-portal/scripts/send_weekly_penner_report.py'
        if not os.path.exists(script_path):
            logger.error(f"Penner Wochenreport-Script nicht gefunden: {script_path}")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte Penner Wochenreport...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("Penner Wochenreport erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"Penner Wochenreport fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("Penner Wochenreport: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei Penner Wochenreport")
        return {'success': False, 'error': str(e)}


@shared_task(soft_time_limit=300, name='celery_app.tasks.sync_eautoseller_data')
def sync_eautoseller_data():
    """
    eAutoseller Sync - eAutoseller Daten synchronisieren
    Läuft alle 15 Minuten während Arbeitszeit (7-18 Uhr)
    """
    import subprocess
    import os
    
    try:
        # Prüfe verschiedene mögliche Pfade
        script_paths = [
            '/opt/greiner-portal/scripts/sync/sync_eautoseller.py',
            '/opt/greiner-portal/scripts/sync_eautoseller_data.py'
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            logger.warning("eAutoseller Sync-Script nicht gefunden")
            return {'success': False, 'error': 'Script nicht gefunden'}
        
        logger.info("Starte eAutoseller Sync...")
        result = subprocess.run(
            ['/opt/greiner-portal/venv/bin/python3', script_path],
            cwd='/opt/greiner-portal',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("eAutoseller Sync erfolgreich abgeschlossen")
            return {'success': True, 'stdout': result.stdout[-500:]}
        else:
            logger.error(f"eAutoseller Sync fehlgeschlagen: {result.stderr}")
            return {'success': False, 'error': result.stderr[-500:]}
    
    except subprocess.TimeoutExpired:
        logger.error("eAutoseller Sync: Timeout nach 5 Minuten")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.exception("Fehler bei eAutoseller Sync")
        return {'success': False, 'error': str(e)}
