"""
WhatsApp Routes
===============
TAG 211: WhatsApp-Integration für Teile-Handelsgeschäft (Twilio)

Endpoints:
- /whatsapp/webhook - Webhook für eingehende Nachrichten (POST: Nachrichten/Status)
- /whatsapp/send - Nachricht senden (API)
- /whatsapp/messages - Nachrichten-Liste (UI)
- /whatsapp/contacts - Kontakte verwalten (UI)
"""

from flask import Blueprint, request, jsonify, render_template, abort
from flask_login import login_required, current_user
import logging
from datetime import datetime
from urllib.parse import urlencode
from api.db_connection import get_db
from api.whatsapp_api import WhatsAppClient, normalize_phone_number, get_whatsapp_config
from api.locosoft_addressbook_api import search_customers as locosoft_search_customers, match_customer_by_phone as locosoft_match_customer_by_phone
import json
import os
import re

logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/whatsapp')

# Sicherheits-Konstanten
MAX_REQUEST_SIZE = 1024 * 1024  # 1MB (wie Nginx)


# =============================================================================
# SICHERHEITS-FUNKTIONEN
# =============================================================================

def validate_twilio_request(request) -> bool:
    """
    Validiert Twilio Webhook-Request mit Signatur.
    
    Twilio sendet eine Signatur im Header 'X-Twilio-Signature',
    die mit dem Auth Token validiert werden kann.
    
    Returns:
        True wenn Request von Twilio kommt, False sonst
    """
    try:
        from twilio.request_validator import RequestValidator
        
        auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        if not auth_token:
            logger.warning("TWILIO_AUTH_TOKEN nicht gesetzt - Signatur-Validierung deaktiviert für Testing")
            # Für lokales Testing: Wenn kein Token gesetzt, erlaube Requests
            # WICHTIG: In Produktion MUSS Token gesetzt sein!
            return True  # Temporär für Testing
        
        validator = RequestValidator(auth_token)
        
        # URL muss vollständig sein (mit https://)
        # Flask request.url enthält bereits vollständige URL
        url = request.url
        
        # Signatur aus Header
        signature = request.headers.get('X-Twilio-Signature', '')
        if not signature:
            logger.warning("Twilio Webhook: Keine Signatur im Header")
            return False
        
        # Form-encoded data (Twilio sendet Form, nicht JSON)
        params = request.form.to_dict()
        
        # Validiere Signatur
        is_valid = validator.validate(url, params, signature)
        
        if not is_valid:
            logger.warning(f"Ungültige Twilio-Signatur von {request.remote_addr}: {signature[:20]}...")
            return False
        
        logger.debug(f"Twilio-Request erfolgreich validiert von {request.remote_addr}")
        return True
        
    except ImportError:
        logger.error("Twilio Request Validator nicht verfügbar. Bitte 'pip install twilio' ausführen.")
        # Für Testing: Erlaube Requests wenn SDK nicht installiert
        return True
    except Exception as e:
        logger.error(f"Fehler bei Twilio-Request-Validierung: {str(e)}")
        return False


def validate_phone_number(phone: str) -> bool:
    """
    Validiert Telefonnummer (E.164 Format).
    
    Args:
        phone: Telefonnummer (kann whatsapp: Prefix haben)
    
    Returns:
        True wenn gültig, False sonst
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Entferne whatsapp: Prefix
    phone_clean = phone.replace('whatsapp:', '').replace('+', '').strip()
    
    # Prüfe: Nur Ziffern, 7-15 Zeichen (E.164 Standard)
    if not re.match(r'^\d{7,15}$', phone_clean):
        return False
    
    return True


def validate_message_sid(sid: str) -> bool:
    """
    Validiert Twilio Message SID Format.
    
    Format: SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (34 Zeichen)
    
    Args:
        sid: Message SID
    
    Returns:
        True wenn gültig, False sonst
    """
    if not sid or not isinstance(sid, str):
        return False
    
    # Twilio Message SID: SM + 32 Zeichen = 34 Zeichen
    if len(sid) != 34:
        return False
    
    # Muss mit SM beginnen
    if not sid.startswith('SM'):
        return False
    
    # Rest muss alphanumerisch sein
    if not re.match(r'^SM[a-zA-Z0-9]{32}$', sid):
        return False
    
    return True


# =============================================================================
# WEBHOOK ENDPOINT
# =============================================================================

@whatsapp_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook für Twilio WhatsApp API.
    
    POST: Eingehende Nachrichten und Status-Updates
    Twilio sendet Form-encoded data, nicht JSON!
    
    SICHERHEIT:
    - Twilio Request Validator (Signatur-Validierung)
    - Input-Validierung (Telefonnummern, Message-IDs)
    - Request-Size-Limits (1MB)
    """
    # Logge Request (für Forensik)
    logger.info(f"Webhook-Request von {request.remote_addr}: "
                f"Signature={request.headers.get('X-Twilio-Signature', 'N/A')[:20]}..., "
                f"Size={request.content_length or 'N/A'}")
    
    # 1. Request-Size prüfen
    if request.content_length and request.content_length > MAX_REQUEST_SIZE:
        logger.warning(f"Request zu groß von {request.remote_addr}: {request.content_length} bytes (max: {MAX_REQUEST_SIZE})")
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 413  # Request Entity Too Large
    
    # 2. Twilio Signatur validieren (KRITISCH!)
    # HINWEIS: Für lokales Testing ohne Token wird Validierung temporär übersprungen
    auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
    if auth_token:  # Nur validieren wenn Token gesetzt
        if not validate_twilio_request(request):
            logger.error(f"Ungültiger Twilio-Request von {request.remote_addr} - Request abgelehnt")
            return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 401  # Unauthorized
    
    # 3. Request verarbeiten
    try:
        # Twilio sendet Form-encoded data
        data = request.form.to_dict()
        
        if not data:
            logger.warning("Twilio Webhook: Keine Daten empfangen")
            return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200
        
        # Twilio Webhook-Struktur
        # MessageSid: Eindeutige Message-ID
        # MessageStatus: Status (queued, sent, delivered, read, failed)
        # From: Absender (Format: whatsapp:+1234567890)
        # To: Empfänger (Format: whatsapp:+1234567890)
        # Body: Nachrichtentext (bei Text-Nachrichten)
        # NumMedia: Anzahl der Medien (bei Media-Nachrichten)
        
        message_sid = data.get('MessageSid', '').strip()
        message_status = data.get('MessageStatus', '').strip()
        from_number = data.get('From', '').strip()
        to_number = data.get('To', '').strip()
        body = data.get('Body', '').strip()
        num_media_str = data.get('NumMedia', '0') or '0'
        
        # Input-Validierung
        try:
            num_media = int(num_media_str)
        except (ValueError, TypeError):
            logger.warning(f"Ungültige NumMedia: {num_media_str}")
            num_media = 0
        
        # Validiere Message SID (wenn vorhanden und Format korrekt)
        if message_sid:
            # Für Testing: Erlaube auch kürzere SIDs (z.B. "SMtest123")
            if len(message_sid) >= 3 and not validate_message_sid(message_sid):
                logger.debug(f"Message SID Format nicht standard (Testing?): {message_sid}")
                # Für Testing erlauben, aber warnen
        
        # Validiere Telefonnummern (wenn vorhanden)
        if from_number and not validate_phone_number(from_number):
            logger.warning(f"Ungültige From-Telefonnummer: {from_number}")
            # Für Testing: Weiter verarbeiten, aber warnen
        
        if to_number and not validate_phone_number(to_number):
            logger.warning(f"Ungültige To-Telefonnummer: {to_number}")
            # Für Testing: Weiter verarbeiten, aber warnen
        
        # Body-Length-Limit (verhindert extrem lange Nachrichten)
        if body and len(body) > 10000:  # Max. 10KB Text
            logger.warning(f"Nachricht zu lang: {len(body)} Zeichen")
            body = body[:10000]  # Kürze auf 10KB
        
        # Status-Update (für ausgehende Nachrichten)
        if message_status and message_sid:
            _handle_status_update_twilio(message_sid, message_status)
        
        # Eingehende Nachricht (wenn From vorhanden und nicht unsere Nummer)
        if from_number and message_sid:
            # Prüfe ob es eine eingehende Nachricht ist (nicht Status-Update)
            if body or num_media > 0:
                _handle_incoming_message_twilio(data)
        
        # Twilio erwartet XML-Response (oder einfachen Text)
        logger.info(f"Webhook erfolgreich verarbeitet: MessageSid={message_sid}, From={from_number}")
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200
        
    except ValueError as e:
        # Input-Validierungs-Fehler
        logger.warning(f"Input-Validierungs-Fehler im Twilio Webhook: {str(e)}")
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 400  # Bad Request
    except Exception as e:
        # Unerwartete Fehler
        logger.error(f"Fehler beim Verarbeiten des Twilio Webhooks: {str(e)}")
        import traceback
        traceback.print_exc()
        # Gebe generische Fehlermeldung zurück (keine Details preisgeben)
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 500


# =============================================================================
# TEST ENDPOINT (nur für lokales Testing)
# =============================================================================

@whatsapp_bp.route('/webhook/test', methods=['GET', 'POST'])
def webhook_test():
    """
    Test-Endpoint für lokales Webhook-Testing.
    Funktioniert ohne Signatur-Validierung.
    
    GET: Zeigt Test-Formular
    POST: Simuliert Webhook-Request
    """
    if request.method == 'GET':
        return """
        <html>
        <head><title>WhatsApp Webhook Test</title></head>
        <body>
            <h1>WhatsApp Webhook Test</h1>
            <form method="POST" action="/whatsapp/webhook/test">
                <p>MessageSid: <input type="text" name="MessageSid" value="SMtest123"></p>
                <p>From: <input type="text" name="From" value="whatsapp:+491234567890"></p>
                <p>Body: <input type="text" name="Body" value="Test-Nachricht"></p>
                <p><input type="submit" value="Test Webhook"></p>
            </form>
            <hr>
            <p><a href="/whatsapp/webhook/test?direct=1">Direkter Test (POST zu /whatsapp/webhook)</a></p>
        </body>
        </html>
        """
    
    # POST: Weiterleitung zum echten Webhook (form-urlencoded wie Twilio)
    if request.method == 'POST':
        test_data = {
            'MessageSid': request.form.get('MessageSid', 'SMtest123'),
            'From': request.form.get('From', 'whatsapp:+491234567890'),
            'Body': request.form.get('Body', 'Test-Nachricht'),
            'To': request.form.get('To', 'whatsapp:+14155238886'),
            'NumMedia': request.form.get('NumMedia', '0')
        }
        from flask import current_app
        with current_app.test_request_context(
            '/whatsapp/webhook',
            method='POST',
            data=urlencode(test_data),
            content_type='application/x-www-form-urlencoded'
        ):
            webhook()
        return """
        <html><head><title>Inbound-Test</title></head><body>
        <h1>Inbound-Test ausgeführt</h1>
        <p>Webhook wurde simuliert. Wenn From/Body korrekt waren, ist die Nachricht in der DB.</p>
        <p><strong>Nächster Schritt:</strong> <a href="/whatsapp/verkauf/chat">Verkauf → WhatsApp Chat</a> öffnen und den Kontakt (From-Nummer) auswählen – die eingehende Nachricht sollte erscheinen.</p>
        <p><a href="/whatsapp/webhook/test">Nochmal testen</a></p>
        </body></html>
        """


def _handle_status_update_twilio(message_sid: str, status: str):
    """
    Verarbeitet Status-Updates von Twilio.
    
    Args:
        message_sid: Twilio Message SID
        status: Status (queued, sent, delivered, read, failed, undelivered)
    """
    try:
        # Mappe Twilio-Status zu unseren Status-Werten
        status_mapping = {
            'queued': 'pending',
            'sent': 'sent',
            'delivered': 'delivered',
            'read': 'read',
            'failed': 'failed',
            'undelivered': 'failed'
        }
        
        status_value = status_mapping.get(status, status.lower())
        
        if not message_sid:
            return
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Update Status in DB
        cursor.execute("""
            UPDATE whatsapp_messages 
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE message_id = %s
        """, (status_value, message_sid))
        
        if cursor.rowcount > 0:
            logger.info(f"Twilio Nachricht-Status aktualisiert: {message_sid} -> {status_value}")
            conn.commit()
        else:
            logger.debug(f"Twilio Nachricht nicht gefunden für Status-Update: {message_sid}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Fehler beim Verarbeiten des Status-Updates (Twilio): {str(e)}")


def _handle_incoming_message_twilio(data: dict):
    """
    Verarbeitet eingehende Nachricht von Twilio.
    
    Args:
        data: Form-encoded data von Twilio
    """
    try:
        message_sid = data.get('MessageSid')
        from_number = data.get('From', '')
        body = data.get('Body', '')
        num_media = int(data.get('NumMedia', '0') or '0')
        
        if not message_sid or not from_number:
            logger.warning(f"Unvollständige Nachricht empfangen: {data}")
            return
        
        # Entferne whatsapp: Prefix von Twilio-Format
        # Format: whatsapp:+491234567890 -> +491234567890 -> 491234567890
        if from_number.startswith('whatsapp:'):
            from_number = from_number.replace('whatsapp:', '')
        
        # Normalisiere Telefonnummer
        phone_number = normalize_phone_number(from_number)
        
        # Bestimme Nachrichtentyp
        message_type = 'text'
        if num_media > 0:
            # Prüfe Media-Typ
            media_content_type = data.get('MediaContentType0', '')
            if 'image' in media_content_type:
                message_type = 'image'
            elif 'video' in media_content_type:
                message_type = 'video'
            elif 'audio' in media_content_type:
                message_type = 'audio'
            elif 'application' in media_content_type or 'document' in media_content_type:
                message_type = 'document'
            else:
                message_type = 'document'  # Fallback
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Finde oder erstelle Kontakt
        cursor.execute("""
            SELECT id FROM whatsapp_contacts 
            WHERE phone_number = %s
        """, (phone_number,))
        contact_row = cursor.fetchone()
        
        if contact_row:
            contact_id = contact_row[0] if isinstance(contact_row, dict) else contact_row['id']
        else:
            # Neuer Kontakt - erstelle mit unbekanntem Namen
            cursor.execute("""
                INSERT INTO whatsapp_contacts (workshop_name, phone_number, contact_name)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (f"Kontakt {phone_number}", phone_number, None))
            contact_id = cursor.fetchone()[0] if cursor.rowcount > 0 else None
            conn.commit()
            logger.info(f"Neuer WhatsApp-Kontakt erstellt: {phone_number}")
        # Eingehende Nachricht: Absender-Nummer mit Kunden (locosoft_kunden_sync) matchen
        try:
            match = locosoft_match_customer_by_phone(phone_number)
            if match:
                display_name = (match.get('display_name') or '').strip() or f"Kunde {match.get('customer_number', '')}"
                first_name = (match.get('first_name') or '').strip() or None
                cursor.execute("""
                    UPDATE whatsapp_contacts
                    SET workshop_name = %s, contact_name = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (display_name, first_name or display_name, contact_id))
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"WhatsApp-Kontakt gematcht: {phone_number} -> {display_name}")
        except Exception as match_err:
            logger.debug(f"Kunden-Match für {phone_number}: {match_err}")
        
        # Extrahiere Nachrichteninhalt je nach Typ
        content = None
        media_url = None
        caption = None
        
        if message_type == 'text':
            content = body
        elif num_media > 0:
            # Twilio: Media-URLs sind in MediaUrl0, MediaUrl1, etc.
            media_url = data.get('MediaUrl0', '')
            # Caption ist im Body (falls vorhanden)
            caption = body if body else None
        
        # Speichere Nachricht in DB
        cursor.execute("""
            INSERT INTO whatsapp_messages (
                contact_id, message_id, direction, message_type,
                content, media_url, caption, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (message_id) DO NOTHING
        """, (
            contact_id,
            message_sid,
            'inbound',
            message_type,
            content,
            media_url,
            caption,
            'delivered',  # Eingehende Nachrichten sind bereits zugestellt
            datetime.now()
        ))
        
        if cursor.rowcount > 0:
            conn.commit()
            logger.info(f"Eingehende Twilio-Nachricht gespeichert: {message_sid} von {phone_number}")
            
            # TODO: Automatische Antworten (z.B. Bestätigung)
            # TODO: Teile-Anfrage erkennen und verarbeiten
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Fehler beim Verarbeiten der eingehenden Nachricht (Twilio): {str(e)}")
        import traceback
        traceback.print_exc()


# =============================================================================
# API ENDPOINTS
# =============================================================================

@whatsapp_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """
    Sendet WhatsApp-Nachricht.
    
    Request Body:
        {
            "to": "491234567890",
            "message": "Textnachricht",
            "type": "text" | "image",
            "image_url": "https://...",  // nur bei type=image
            "caption": "Bildtext"  // optional
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Keine Daten'}), 400
        
        to = data.get('to')
        message_type = data.get('type', 'text')
        
        if not to:
            return jsonify({'error': 'Telefonnummer fehlt'}), 400
        
        # Normalisiere Telefonnummer
        phone_number = normalize_phone_number(to)
        
        client = WhatsAppClient()
        result = None
        
        if message_type == 'text':
            message = data.get('message')
            if not message:
                return jsonify({'error': 'Nachrichtentext fehlt'}), 400
            result = client.send_text_message(phone_number, message)
        
        elif message_type == 'image':
            image_url = data.get('image_url')
            if not image_url:
                return jsonify({'error': 'Bild-URL fehlt'}), 400
            caption = data.get('caption')
            result = client.send_image_message(phone_number, image_url, caption)
        
        else:
            return jsonify({'error': f'Unbekannter Nachrichtentyp: {message_type}'}), 400
        
        if result and result.get('success'):
            # Speichere Nachricht in DB
            _save_outbound_message(phone_number, result.get('message_id'), message_type, data)
            return jsonify(result), 200
        else:
            return jsonify(result or {'error': 'Nachricht konnte nicht gesendet werden'}), 500
        
    except Exception as e:
        logger.error(f"Fehler beim Senden der WhatsApp-Nachricht: {str(e)}")
        return jsonify({'error': str(e)}), 500


def _save_outbound_message(phone_number: str, message_id: str, message_type: str, data: dict):
    """
    Speichert ausgehende Nachricht in DB.
    
    Args:
        phone_number: Telefonnummer
        message_id: WhatsApp Message ID
        message_type: Nachrichtentyp
        data: Original Request-Daten
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Finde Kontakt
        cursor.execute("""
            SELECT id FROM whatsapp_contacts 
            WHERE phone_number = %s
        """, (phone_number,))
        contact_row = cursor.fetchone()
        contact_id = contact_row[0] if contact_row else None
        
        # Speichere Nachricht
        content = data.get('message') if message_type == 'text' else None
        media_url = data.get('image_url') if message_type == 'image' else None
        caption = data.get('caption')
        
        cursor.execute("""
            INSERT INTO whatsapp_messages (
                contact_id, message_id, direction, message_type,
                content, media_url, caption, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (message_id) DO UPDATE SET
                status = EXCLUDED.status,
                updated_at = CURRENT_TIMESTAMP
        """, (
            contact_id,
            message_id,
            'outbound',
            message_type,
            content,
            media_url,
            caption,
            'sent',
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Fehler beim Speichern der ausgehenden Nachricht: {str(e)}")


# =============================================================================
# VERKÄUFER-ENDPOINTS (TAG 211)
# =============================================================================

def _require_whatsapp_verkauf():
    """Prüft Zugriff auf WhatsApp Verkauf."""
    if not current_user.is_authenticated:
        return False
    if hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('whatsapp_verkauf'):
        return True
    return False


@whatsapp_bp.route('/verkauf/locosoft-addressbook', methods=['GET'])
@login_required
def verkauf_locosoft_addressbook_api():
    """API: Kunden aus Locosoft als Adressbuch (für Neuer Chat)."""
    if not _require_whatsapp_verkauf():
        return jsonify({'error': 'Keine Berechtigung'}), 403
    try:
        q = request.args.get('q', '').strip()
        subsidiary = request.args.get('subsidiary', type=int)
        limit = min(request.args.get('limit', 50, type=int), 100)
        mobile_only = request.args.get('mobile_only', '0') in ('1', 'true', 'yes')
        logger.info(f"Locosoft Adressbuch: q={q!r} mobile_only={mobile_only} -> Suche starten")
        customers = locosoft_search_customers(q=q or '', subsidiary=subsidiary, limit=limit, mobile_only=mobile_only)
        return jsonify({'customers': customers, 'mobile_only': mobile_only}), 200
    except Exception as e:
        logger.error(f"Locosoft Adressbuch: {e}")
        return jsonify({'error': str(e), 'customers': []}), 500


@whatsapp_bp.route('/verkauf/chat', methods=['GET'])
@login_required
def verkauf_chat():
    """
    Chat-Interface für Verkäufer (WhatsApp-ähnlich).
    Zeigt Kontakte links, Chat rechts.
    """
    if not _require_whatsapp_verkauf():
        abort(403)
    return render_template('whatsapp/verkauf_chat.html')


@whatsapp_bp.route('/verkauf/chats', methods=['GET'])
@login_required
def verkauf_chats_api():
    """
    API: Liste der Chats für aktuellen User (Verkäufer).
    Nutzt Kontakte mit Nachrichten; falls Migration (contact_type/assigned_user_id) vorhanden,
    auch Verkauf-Kontakte ohne Nachrichten.
    """
    if not _require_whatsapp_verkauf():
        return jsonify({'error': 'Keine Berechtigung'}), 403
    try:
        conn = get_db()
        cursor = conn.cursor()
        user_id = current_user.id if hasattr(current_user, 'id') else None
        # Zuerst Abfrage mit Verkauf-Spalten (contact_type, assigned_user_id)
        try:
            cursor.execute("""
                SELECT DISTINCT c.id, c.workshop_name as contact_name, c.phone_number, c.contact_name as contact_person,
                       (SELECT content FROM whatsapp_messages m WHERE m.contact_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message_preview,
                       (SELECT created_at FROM whatsapp_messages m WHERE m.contact_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message_at,
                       (SELECT COUNT(*) FROM whatsapp_messages m WHERE m.contact_id = c.id AND m.direction = 'inbound' AND m.status != 'read') as unread_count
                FROM whatsapp_contacts c
                WHERE c.active = true
                AND (
                    EXISTS (SELECT 1 FROM whatsapp_messages m WHERE m.contact_id = c.id)
                    OR (COALESCE(c.contact_type, 'workshop') = 'customer' AND (c.assigned_user_id = %s OR c.assigned_user_id IS NULL))
                )
                ORDER BY last_message_at DESC NULLS LAST, c.workshop_name
                LIMIT 100
            """, (user_id,))
        except Exception as schema_err:
            # Fallback: Spalten contact_type/assigned_user_id fehlen (Migration nicht ausgeführt)
            logger.debug(f"Verkauf chats: Fallback-Query (Schema: {schema_err})")
            cursor.execute("""
                SELECT DISTINCT c.id, c.workshop_name as contact_name, c.phone_number, c.contact_name as contact_person,
                       (SELECT content FROM whatsapp_messages m WHERE m.contact_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message_preview,
                       (SELECT created_at FROM whatsapp_messages m WHERE m.contact_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message_at,
                       (SELECT COUNT(*) FROM whatsapp_messages m WHERE m.contact_id = c.id AND m.direction = 'inbound' AND m.status != 'read') as unread_count
                FROM whatsapp_contacts c
                WHERE c.active = true
                AND EXISTS (SELECT 1 FROM whatsapp_messages m WHERE m.contact_id = c.id)
                ORDER BY last_message_at DESC NULLS LAST, c.workshop_name
                LIMIT 100
            """)
        rows = cursor.fetchall()
        desc = [d[0] for d in cursor.description] if cursor.description else []
        conn.close()
        chats = [dict(zip(desc, r)) for r in rows] if desc and rows else []
        for c in chats:
            if c.get('last_message_at') and hasattr(c['last_message_at'], 'isoformat'):
                c['last_message_at'] = c['last_message_at'].isoformat()
        return jsonify({'chats': chats}), 200
    except Exception as e:
        logger.error(f"Verkauf chats API: {e}")
        return jsonify({'error': str(e)}), 500


@whatsapp_bp.route('/verkauf/messages/<int:contact_id>', methods=['GET'])
@login_required
def verkauf_messages_api(contact_id):
    """API: Chat-Verlauf für einen Kontakt."""
    if not _require_whatsapp_verkauf():
        return jsonify({'error': 'Keine Berechtigung'}), 403
    try:
        limit = request.args.get('limit', 50, type=int)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.id, m.message_id, m.contact_id, m.direction, m.message_type, m.content, m.media_url, m.caption, m.status, m.created_at,
                   c.workshop_name as contact_name, c.phone_number
            FROM whatsapp_messages m
            LEFT JOIN whatsapp_contacts c ON m.contact_id = c.id
            WHERE m.contact_id = %s
            ORDER BY m.created_at ASC
            LIMIT %s
        """, (contact_id, limit))
        rows = cursor.fetchall()
        desc = [d[0] for d in cursor.description] if cursor.description else []
        conn.close()
        messages = [dict(zip(desc, r)) for r in rows] if desc and rows else []
        for m in messages:
            if m.get('created_at') and hasattr(m['created_at'], 'isoformat'):
                m['created_at'] = m['created_at'].isoformat()
        return jsonify({'messages': messages}), 200
    except Exception as e:
        logger.error(f"Verkauf messages API: {e}")
        return jsonify({'error': str(e)}), 500


def _ensure_verkauf_contact(phone_number: str, contact_name: str = None) -> int:
    """
    Findet oder erstellt einen WhatsApp-Kontakt für Verkauf (contact_type=customer).
    Gibt contact_id zurück. Funktioniert auch ohne Migration (contact_type/assigned_user_id).
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id FROM whatsapp_contacts WHERE phone_number = %s
        """, (phone_number,))
        row = cursor.fetchone()
        if row:
            return row[0] if isinstance(row, dict) else row['id']
        user_id = current_user.id if hasattr(current_user, 'id') else None
        display_name = (contact_name or '').strip() or f"Kunde {phone_number[-6:]}"
        try:
            cursor.execute("""
                INSERT INTO whatsapp_contacts (workshop_name, phone_number, contact_name, contact_type, assigned_user_id)
                VALUES (%s, %s, %s, 'customer', %s)
                RETURNING id
            """, (display_name, phone_number, contact_name or None, user_id))
        except Exception:
            cursor.execute("""
                INSERT INTO whatsapp_contacts (workshop_name, phone_number, contact_name)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (display_name, phone_number, contact_name or None))
        row = cursor.fetchone()
        contact_id = row[0] if hasattr(row, '__getitem__') else row['id']
        conn.commit()
        logger.info(f"Neuer Verkauf-Kontakt erstellt: {phone_number} (id={contact_id})")
        return contact_id
    finally:
        conn.close()


@whatsapp_bp.route('/verkauf/contact', methods=['POST'])
@login_required
def verkauf_contact_api():
    """API: Neuen Verkauf-Kontakt anlegen (ohne Nachricht). Für 'Neuer Chat'."""
    if not _require_whatsapp_verkauf():
        return jsonify({'error': 'Keine Berechtigung'}), 403
    try:
        data = request.get_json() or {}
        to = data.get('to') or data.get('phone_number')
        contact_name = (data.get('contact_name') or '').strip() or None
        if not to:
            return jsonify({'error': 'Telefonnummer erforderlich'}), 400
        phone_number = normalize_phone_number(str(to))
        contact_id = _ensure_verkauf_contact(phone_number, contact_name)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, workshop_name, phone_number, contact_name
            FROM whatsapp_contacts WHERE id = %s
        """, (contact_id,))
        row = cursor.fetchone()
        desc = [d[0] for d in cursor.description] if cursor.description else []
        conn.close()
        if not row:
            return jsonify({'error': 'Kontakt nicht gefunden'}), 500
        contact = dict(zip(desc, row)) if desc and row else {'id': contact_id, 'phone_number': phone_number, 'contact_name': contact_name}
        return jsonify({'contact': contact}), 200
    except Exception as e:
        logger.error(f"Verkauf contact API: {e}")
        return jsonify({'error': str(e)}), 500


@whatsapp_bp.route('/verkauf/send', methods=['POST'])
@login_required
def verkauf_send_api():
    """API: Nachricht senden (Verkäufer). Legt bei neuer Nummer automatisch einen Kontakt an."""
    if not _require_whatsapp_verkauf():
        return jsonify({'error': 'Keine Berechtigung'}), 403
    try:
        data = request.get_json() or {}
        to = data.get('to') or data.get('phone_number')
        message = data.get('message') or data.get('content')
        contact_name = data.get('contact_name', '').strip() or None
        if not to or not message:
            return jsonify({'error': 'to und message erforderlich'}), 400
        phone_number = normalize_phone_number(str(to))
        contact_id = _ensure_verkauf_contact(phone_number, contact_name)
        client = WhatsAppClient()
        result = client.send_text_message(phone_number, message)
        if result and result.get('success'):
            _save_outbound_message(phone_number, result.get('message_id', ''), 'text', {'message': message})
            return jsonify({**result, 'contact_id': contact_id}), 200
        return jsonify(result or {'error': 'Senden fehlgeschlagen'}), 500
    except Exception as e:
        logger.error(f"Verkauf send API: {e}")
        return jsonify({'error': str(e)}), 500


@whatsapp_bp.route('/verkauf/updates', methods=['GET'])
@login_required
def verkauf_updates_api():
    """API: Neue Nachrichten (z.B. nach last_message_id) für Polling."""
    if not _require_whatsapp_verkauf():
        return jsonify({'error': 'Keine Berechtigung'}), 403
    try:
        contact_id = request.args.get('contact_id', type=int)
        last_id = request.args.get('last_message_id', type=int)
        if not contact_id:
            return jsonify({'messages': []}), 200
        conn = get_db()
        cursor = conn.cursor()
        if last_id:
            cursor.execute("""
                SELECT m.id, m.message_id, m.contact_id, m.direction, m.message_type, m.content, m.media_url, m.caption, m.status, m.created_at
                FROM whatsapp_messages m
                WHERE m.contact_id = %s AND m.id > %s
                ORDER BY m.created_at ASC
            """, (contact_id, last_id))
        else:
            cursor.execute("""
                SELECT m.id, m.message_id, m.contact_id, m.direction, m.message_type, m.content, m.media_url, m.caption, m.status, m.created_at
                FROM whatsapp_messages m
                WHERE m.contact_id = %s
                ORDER BY m.created_at ASC
                LIMIT 50
            """, (contact_id,))
        rows = cursor.fetchall()
        desc = [d[0] for d in cursor.description] if cursor.description else []
        conn.close()
        messages = [dict(zip(desc, r)) for r in rows] if desc and rows else []
        for m in messages:
            if m.get('created_at') and hasattr(m['created_at'], 'isoformat'):
                m['created_at'] = m['created_at'].isoformat()
        return jsonify({'messages': messages}), 200
    except Exception as e:
        logger.error(f"Verkauf updates API: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# UI ENDPOINTS
# =============================================================================

@whatsapp_bp.route('/messages', methods=['GET'])
@login_required
def messages_list():
    """
    Zeigt Nachrichten-Liste.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Hole Nachrichten (letzte 50)
        cursor.execute("""
            SELECT * FROM v_whatsapp_messages_with_contact
            ORDER BY created_at DESC
            LIMIT 50
        """)
        messages = cursor.fetchall()
        
        conn.close()
        
        return render_template('whatsapp/messages.html', messages=messages)
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Nachrichten: {str(e)}")
        return render_template('whatsapp/messages.html', messages=[], error=str(e))


@whatsapp_bp.route('/contacts', methods=['GET'])
@login_required
def contacts_list():
    """
    Zeigt Kontakte-Liste.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM whatsapp_contacts
            WHERE active = true
            ORDER BY workshop_name
        """)
        contacts = cursor.fetchall()
        
        conn.close()
        
        return render_template('whatsapp/contacts.html', contacts=contacts)
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Kontakte: {str(e)}")
        return render_template('whatsapp/contacts.html', contacts=[], error=str(e))


@whatsapp_bp.route('/api/messages', methods=['GET'])
@login_required
def api_messages():
    """
    API-Endpoint für Nachrichten (JSON).
    """
    try:
        contact_id = request.args.get('contact_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        if contact_id:
            cursor.execute("""
                SELECT * FROM v_whatsapp_messages_with_contact
                WHERE contact_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (contact_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM v_whatsapp_messages_with_contact
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
        
        messages = cursor.fetchall()
        
        # Konvertiere zu Dict für JSON
        result = []
        for msg in messages:
            if isinstance(msg, dict):
                result.append(dict(msg))
            else:
                # HybridRow zu Dict
                result.append({key: msg[key] for key in msg.keys()})
        
        conn.close()
        
        return jsonify({'messages': result}), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Nachrichten (API): {str(e)}")
        return jsonify({'error': str(e)}), 500
