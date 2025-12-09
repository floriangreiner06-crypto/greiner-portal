"""
Microsoft Graph API Mail Connector
Für E-Mail-Versand über Office 365

Benötigt in config/.env:
- GRAPH_TENANT_ID
- GRAPH_CLIENT_ID  
- GRAPH_CLIENT_SECRET
"""

import requests
from msal import ConfidentialClientApplication
from datetime import datetime, timedelta
import base64
import os


class GraphMailConnector:
    """
    Office 365 E-Mail-Versand über Microsoft Graph API
    """
    
    def __init__(self):
        self.tenant_id = None
        self.client_id = None
        self.client_secret = None
        self.token = None
        self.token_expires = None
        
        self._load_credentials()
    
    def _load_credentials(self):
        """Credentials aus .env laden"""
        env_path = '/opt/greiner-portal/config/.env'
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key == 'GRAPH_TENANT_ID':
                            self.tenant_id = value
                        elif key == 'GRAPH_CLIENT_ID':
                            self.client_id = value
                        elif key == 'GRAPH_CLIENT_SECRET':
                            self.client_secret = value
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise Exception("Graph API Credentials nicht vollständig konfiguriert. Benötigt: GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET in config/.env")
    
    def _get_token(self):
        """OAuth Token holen (mit Caching)"""
        if self.token and self.token_expires and self.token_expires > datetime.now():
            return self.token
        
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        
        if "access_token" in result:
            self.token = result['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=result['expires_in'] - 300)
            return self.token
        else:
            raise Exception(f"Token-Fehler: {result.get('error_description', result.get('error', 'Unbekannt'))}")
    
    def send_mail(self, sender_email: str, to_emails: list, subject: str, 
                  body_html: str, attachments: list = None, cc_emails: list = None):
        """
        E-Mail senden über Graph API
        
        Args:
            sender_email: Absender (muss in O365 existieren oder Shared Mailbox sein)
            to_emails: Liste der Empfänger
            subject: Betreff
            body_html: HTML-Body
            attachments: Liste von Dicts: [{"name": "file.pdf", "content": bytes}, ...]
            cc_emails: Liste der CC-Empfänger (optional)
        
        Returns:
            bool: True wenn erfolgreich
        """
        token = self._get_token()
        
        # Empfänger formatieren
        recipients = [{"emailAddress": {"address": email}} for email in to_emails]
        
        # Mail-Objekt
        mail_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body_html
                },
                "toRecipients": recipients
            },
            "saveToSentItems": "true"
        }
        
        # CC hinzufügen
        if cc_emails:
            mail_data["message"]["ccRecipients"] = [
                {"emailAddress": {"address": email}} for email in cc_emails
            ]
        
        # Anhänge hinzufügen
        if attachments:
            mail_data["message"]["attachments"] = []
            for att in attachments:
                mail_data["message"]["attachments"].append({
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": att["name"],
                    "contentType": att.get("content_type", "application/pdf"),
                    "contentBytes": base64.b64encode(att["content"]).decode('utf-8')
                })
        
        # Senden
        response = requests.post(
            f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=mail_data,
            timeout=30
        )
        
        if response.status_code == 202:
            return True
        else:
            raise Exception(f"Mail-Fehler {response.status_code}: {response.text}")
    
    def test_connection(self):
        """Verbindung testen"""
        try:
            token = self._get_token()
            return True, "Graph API Verbindung erfolgreich"
        except Exception as e:
            return False, str(e)
