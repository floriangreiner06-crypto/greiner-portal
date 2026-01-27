"""
WhatsApp Business API Client (Twilio)
======================================
TAG 211: WhatsApp-Integration für Teile-Handelsgeschäft

Verwendet Twilio WhatsApp API für:
- Senden von Textnachrichten
- Senden von Bildern
- Empfangen von Nachrichten (via Webhook)
- Status-Tracking

Konfiguration:
- TWILIO_ACCOUNT_SID: Twilio Account SID
- TWILIO_AUTH_TOKEN: Twilio Auth Token
- TWILIO_WHATSAPP_NUMBER: Twilio WhatsApp-Nummer (Format: whatsapp:+1234567890)
- TWILIO_WEBHOOK_URL: Webhook-URL für eingehende Nachrichten
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Twilio Python SDK nicht installiert. Bitte 'pip install twilio' ausführen.")

if TWILIO_AVAILABLE:
    logger = logging.getLogger(__name__)

# =============================================================================
# KONFIGURATION
# =============================================================================

def get_whatsapp_config() -> Dict[str, str]:
    """Lädt Twilio-Konfiguration aus Environment-Variablen"""
    return {
        'account_sid': os.getenv('TWILIO_ACCOUNT_SID', ''),
        'auth_token': os.getenv('TWILIO_AUTH_TOKEN', ''),
        'whatsapp_number': os.getenv('TWILIO_WHATSAPP_NUMBER', ''),  # Format: whatsapp:+1234567890
        'webhook_url': os.getenv('TWILIO_WEBHOOK_URL', 'https://auto-greiner.de/whatsapp/webhook')
    }


# =============================================================================
# WHATSAPP CLIENT
# =============================================================================

class WhatsAppClient:
    """
    Client für Twilio WhatsApp API.
    
    Usage:
        client = WhatsAppClient()
        
        # Textnachricht senden
        result = client.send_text_message(
            to="491234567890",
            message="Hallo, wir haben das Teil auf Lager."
        )
        
        # Bild senden
        result = client.send_image_message(
            to="491234567890",
            image_url="https://example.com/image.jpg",
            caption="Hier ist das Teil"
        )
    """
    
    def __init__(self):
        if not TWILIO_AVAILABLE:
            raise ImportError("Twilio Python SDK nicht installiert. Bitte 'pip install twilio' ausführen.")
        
        self.config = get_whatsapp_config()
        self.account_sid = self.config['account_sid']
        self.auth_token = self.config['auth_token']
        self.whatsapp_number = self.config['whatsapp_number']
        
        if not self.account_sid or not self.auth_token or not self.whatsapp_number:
            logger.warning("Twilio-Konfiguration unvollständig. Bitte TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN und TWILIO_WHATSAPP_NUMBER in .env setzen.")
            self.client = None
        else:
            self.client = TwilioClient(self.account_sid, self.auth_token)
    
    def _format_phone_number(self, phone: str) -> str:
        """
        Formatiert Telefonnummer für Twilio (Format: whatsapp:+1234567890).
        
        Args:
            phone: Telefonnummer (z.B. "491234567890")
        
        Returns:
            Formatierte Nummer (z.B. "whatsapp:+491234567890")
        """
        # Stelle sicher, dass + vorhanden ist
        if not phone.startswith('+'):
            phone = '+' + phone
        
        # Füge whatsapp: Prefix hinzu
        return f"whatsapp:{phone}"
    
    def send_text_message(self, to: str, message: str) -> Optional[Dict[str, Any]]:
        """
        Sendet Textnachricht über Twilio WhatsApp API.
        
        Args:
            to: Telefonnummer im Format 491234567890 (mit Ländercode, ohne +)
            message: Nachrichtentext
        
        Returns:
            Response mit message_id oder None bei Fehler
        """
        if not self.client:
            logger.error("Twilio-Konfiguration unvollständig")
            return {
                'success': False,
                'error': 'Twilio-Konfiguration unvollständig'
            }
        
        try:
            from_number = self._format_phone_number(self.whatsapp_number)
            to_number = self._format_phone_number(to)
            
            logger.info(f"Sende WhatsApp-Nachricht an {to}")
            
            twilio_message = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            message_id = twilio_message.sid
            logger.info(f"WhatsApp-Nachricht gesendet: {message_id}")
            
            return {
                'success': True,
                'message_id': message_id,
                'status': twilio_message.status,
                'response': {
                    'sid': twilio_message.sid,
                    'status': twilio_message.status,
                    'to': twilio_message.to,
                    'from': twilio_message.from_
                }
            }
        
        except TwilioRestException as e:
            logger.error(f"Twilio API Fehler: {str(e)}")
            return {
                'success': False,
                'error': f'Twilio API Fehler: {str(e)}',
                'response': None
            }
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei Twilio API: {str(e)}")
            return {
                'success': False,
                'error': f'Unerwarteter Fehler: {str(e)}',
                'response': None
            }
    
    def send_image_message(self, to: str, image_url: str, caption: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Sendet Bildnachricht über Twilio WhatsApp API.
        
        Args:
            to: Telefonnummer im Format 491234567890
            image_url: URL zum Bild (muss öffentlich erreichbar sein)
            caption: Optionaler Bildtext
        
        Returns:
            Response mit message_id oder None bei Fehler
        """
        if not self.client:
            logger.error("Twilio-Konfiguration unvollständig")
            return {
                'success': False,
                'error': 'Twilio-Konfiguration unvollständig'
            }
        
        try:
            from_number = self._format_phone_number(self.whatsapp_number)
            to_number = self._format_phone_number(to)
            
            logger.info(f"Sende WhatsApp-Bild an {to}")
            
            # Twilio: Media-URL als Body, mit optionaler Caption
            body = caption if caption else ""
            
            twilio_message = self.client.messages.create(
                media_url=[image_url],
                body=body,
                from_=from_number,
                to=to_number
            )
            
            message_id = twilio_message.sid
            logger.info(f"WhatsApp-Bild gesendet: {message_id}")
            
            return {
                'success': True,
                'message_id': message_id,
                'status': twilio_message.status,
                'response': {
                    'sid': twilio_message.sid,
                    'status': twilio_message.status,
                    'to': twilio_message.to,
                    'from': twilio_message.from_,
                    'media_url': image_url
                }
            }
        
        except TwilioRestException as e:
            logger.error(f"Twilio API Fehler: {str(e)}")
            return {
                'success': False,
                'error': f'Twilio API Fehler: {str(e)}',
                'response': None
            }
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei Twilio API: {str(e)}")
            return {
                'success': False,
                'error': f'Unerwarteter Fehler: {str(e)}',
                'response': None
            }
    
    def send_document_message(self, to: str, document_url: str, filename: str, caption: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Sendet Dokument (PDF, etc.) über Twilio WhatsApp API.
        
        Args:
            to: Telefonnummer im Format 491234567890
            document_url: URL zum Dokument (muss öffentlich erreichbar sein)
            filename: Dateiname (wird von Twilio ignoriert, aber für Logging)
            caption: Optionaler Text
        
        Returns:
            Response mit message_id oder None bei Fehler
        """
        if not self.client:
            logger.error("Twilio-Konfiguration unvollständig")
            return {
                'success': False,
                'error': 'Twilio-Konfiguration unvollständig'
            }
        
        try:
            from_number = self._format_phone_number(self.whatsapp_number)
            to_number = self._format_phone_number(to)
            
            logger.info(f"Sende WhatsApp-Dokument an {to}: {filename}")
            
            # Twilio: Dokument als Media-URL senden
            body = caption if caption else f"Datei: {filename}"
            
            twilio_message = self.client.messages.create(
                media_url=[document_url],
                body=body,
                from_=from_number,
                to=to_number
            )
            
            message_id = twilio_message.sid
            logger.info(f"WhatsApp-Dokument gesendet: {message_id}")
            
            return {
                'success': True,
                'message_id': message_id,
                'status': twilio_message.status,
                'response': {
                    'sid': twilio_message.sid,
                    'status': twilio_message.status,
                    'to': twilio_message.to,
                    'from': twilio_message.from_,
                    'media_url': document_url
                }
            }
        
        except TwilioRestException as e:
            logger.error(f"Twilio API Fehler: {str(e)}")
            return {
                'success': False,
                'error': f'Twilio API Fehler: {str(e)}',
                'response': None
            }
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei Twilio API: {str(e)}")
            return {
                'success': False,
                'error': f'Unerwarteter Fehler: {str(e)}',
                'response': None
            }
    
    def mark_message_as_read(self, message_id: str) -> bool:
        """
        Markiert Nachricht als gelesen.
        
        Args:
            message_id: Twilio Message SID
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        # Twilio: Status-Updates über Webhook, nicht direkt über API
        # Diese Funktion wird über Webhook-Events verarbeitet
        logger.debug(f"Markiere Nachricht als gelesen: {message_id} (wird über Webhook verarbeitet)")
        return True


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def normalize_phone_number(phone: str) -> str:
    """
    Normalisiert Telefonnummer für WhatsApp.
    Entfernt Leerzeichen, Bindestriche, Klammern, etc.
    Entfernt führendes + falls vorhanden.
    
    Args:
        phone: Telefonnummer (z.B. "+49 123 4567890" oder "00491234567890")
    
    Returns:
        Normalisierte Nummer (z.B. "491234567890")
    """
    # Entferne alle nicht-numerischen Zeichen außer +
    normalized = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Entferne führendes +
    if normalized.startswith('+'):
        normalized = normalized[1:]
    
    # Ersetze 00 am Anfang durch nichts (internationales Format)
    if normalized.startswith('00'):
        normalized = normalized[2:]
    
    return normalized


class WhatsAppTeileClient(WhatsAppClient):
    """
    Client für Teile-Channel (separater Channel).
    Verwendet separate WhatsApp-Nummer für Teile-Bereich (falls vorhanden).
    """
    
    def __init__(self):
        # Lade Basis-Konfiguration
        self.config = get_whatsapp_config()
        self.account_sid = self.config['account_sid']
        self.auth_token = self.config['auth_token']
        
        # Überschreibe WhatsApp-Nummer mit Teile-Nummer (falls vorhanden)
        teile_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER_TEILE', '')
        if teile_whatsapp_number:
            self.whatsapp_number = teile_whatsapp_number
        else:
            self.whatsapp_number = self.config['whatsapp_number']
        
        if not self.account_sid or not self.auth_token or not self.whatsapp_number:
            logger.warning("Twilio Teile-Konfiguration unvollständig. Bitte TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN und TWILIO_WHATSAPP_NUMBER in .env setzen.")
            self.client = None
        else:
            self.client = TwilioClient(self.account_sid, self.auth_token)


def format_phone_number_for_display(phone: str) -> str:
    """
    Formatiert Telefonnummer für Anzeige.
    
    Args:
        phone: Normalisierte Telefonnummer (z.B. "491234567890")
    
    Returns:
        Formatierte Nummer (z.B. "+49 123 4567890")
    """
    if not phone:
        return ""
    
    # Deutsche Nummern
    if phone.startswith('49'):
        country = '+49'
        rest = phone[2:]
        if len(rest) == 10:
            return f"{country} {rest[:3]} {rest[3:]}"
        elif len(rest) == 11:
            return f"{country} {rest[:2]} {rest[2:5]} {rest[5:]}"
    
    # Fallback: Einfach + voranstellen
    return f"+{phone}"
