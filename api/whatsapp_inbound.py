"""
WhatsApp eingehende Nachrichten — gemeinsame Verarbeitung
==========================================================
Wird genutzt von: Webhook (routes) und Polling (Celery-Task).
Eingehende Twilio-Nachricht in DB speichern, Kontakt ggf. anlegen/matchen.
"""

import logging
from datetime import datetime

from api.db_connection import get_db
from api.whatsapp_api import normalize_phone_number

logger = logging.getLogger(__name__)


def process_inbound_message(data: dict) -> None:
    """
    Verarbeitet eine eingehende Nachricht (Twilio-Format).
    Nutzbar für Webhook (form dict) und Polling (API-Response als dict gemappt).

    Args:
        data: Dict mit MessageSid, From, To, Body, NumMedia (0), optional MediaUrl0, MediaContentType0
    """
    try:
        message_sid = data.get('MessageSid')
        from_number = (data.get('From') or '').strip()
        body = (data.get('Body') or '').strip()
        num_media = int(data.get('NumMedia', '0') or '0')

        if not message_sid or not from_number:
            logger.warning("Unvollständige Nachricht (MessageSid/From fehlt): %s", data)
            return

        if from_number.startswith('whatsapp:'):
            from_number = from_number.replace('whatsapp:', '')
        phone_number = normalize_phone_number(from_number)

        message_type = 'text'
        if num_media > 0:
            media_content_type = (data.get('MediaContentType0') or '').lower()
            if 'image' in media_content_type:
                message_type = 'image'
            elif 'video' in media_content_type:
                message_type = 'video'
            elif 'audio' in media_content_type:
                message_type = 'audio'
            elif 'application' in media_content_type or 'document' in media_content_type:
                message_type = 'document'
            else:
                message_type = 'document'

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM whatsapp_contacts WHERE phone_number = %s",
            (phone_number,),
        )
        contact_row = cursor.fetchone()
        if contact_row:
            contact_id = contact_row[0] if isinstance(contact_row, dict) else contact_row['id']
        else:
            cursor.execute(
                """
                INSERT INTO whatsapp_contacts (workshop_name, phone_number, contact_name)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (f"Kontakt {phone_number}", phone_number, None),
            )
            contact_id = cursor.fetchone()[0] if cursor.rowcount > 0 else None
            conn.commit()
            logger.info("Neuer WhatsApp-Kontakt erstellt: %s", phone_number)

        try:
            from api.locosoft_addressbook_api import match_customer_by_phone as locosoft_match_customer_by_phone
            match = locosoft_match_customer_by_phone(phone_number)
            if match:
                display_name = (match.get('display_name') or '').strip() or f"Kunde {match.get('customer_number', '')}"
                first_name = (match.get('first_name') or '').strip() or None
                cursor.execute(
                    """
                    UPDATE whatsapp_contacts
                    SET workshop_name = %s, contact_name = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (display_name, first_name or display_name, contact_id),
                )
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info("WhatsApp-Kontakt gematcht: %s -> %s", phone_number, display_name)
        except Exception as match_err:
            logger.debug("Kunden-Match für %s: %s", phone_number, match_err)

        content = None
        media_url = None
        caption = None
        if message_type == 'text':
            content = body
        elif num_media > 0:
            media_url = data.get('MediaUrl0', '')
            caption = body if body else None

        cursor.execute(
            """
            INSERT INTO whatsapp_messages (
                contact_id, message_id, direction, message_type,
                content, media_url, caption, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (message_id) DO NOTHING
            """,
            (
                contact_id,
                message_sid,
                'inbound',
                message_type,
                content,
                media_url,
                caption,
                'delivered',
                datetime.now(),
            ),
        )
        if cursor.rowcount > 0:
            conn.commit()
            logger.info("Eingehende Twilio-Nachricht gespeichert: %s von %s", message_sid, phone_number)
        conn.close()
    except Exception as e:
        logger.exception("Fehler beim Verarbeiten der eingehenden Nachricht: %s", e)
