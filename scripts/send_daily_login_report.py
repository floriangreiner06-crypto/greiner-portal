#!/usr/bin/env python3
"""
Täglicher Login-Report - Liste der Benutzer die sich heute in DRIVE eingeloggt haben
Versendet täglich um 17:30 Uhr per E-Mail

Schedule (Celery Beat):
30 17 * * 1-5 (Mo-Fr um 17:30 Uhr)
Task: celery_app.tasks.email_daily_logins

Version: 1.0 (TAG 209)
"""

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

from datetime import datetime, date
from api.db_connection import get_db, convert_placeholders

# ============================================================================
# KONFIGURATION
# ============================================================================

ABSENDER = "drive@auto-greiner.de"
EMPFAENGER = "florian.greiner@auto-greiner.de"  # Florian Greiner

# Monatsnamen
MONATE = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']


def get_todays_logins():
    """
    Holt alle Benutzer die sich heute eingeloggt haben.
    
    Returns:
        List[Dict]: Liste der eingeloggten Benutzer mit Details
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Hole alle Benutzer die sich heute eingeloggt haben
        # last_login ist ein TIMESTAMP, wir prüfen ob es heute ist
        cursor.execute(convert_placeholders("""
            SELECT 
                id,
                username,
                display_name,
                email,
                ou,
                title,
                last_login
            FROM users
            WHERE DATE(last_login) = CURRENT_DATE
            ORDER BY last_login DESC
        """))
        
        rows = cursor.fetchall()
        
        # Konvertiere zu Dict-Format
        logins = []
        for row in rows:
            logins.append({
                'id': row[0],
                'username': row[1],
                'display_name': row[2] or row[1],
                'email': row[3] or '',
                'ou': row[4] or 'Unbekannt',
                'title': row[5] or '',
                'last_login': row[6]
            })
        
        return logins
    
    finally:
        conn.close()


def format_login_time(login_timestamp):
    """Formatiert Login-Zeit für Anzeige"""
    if not login_timestamp:
        return 'Unbekannt'
    
    if isinstance(login_timestamp, str):
        # Parse ISO-Format String
        try:
            dt = datetime.fromisoformat(login_timestamp.replace('Z', '+00:00'))
        except:
            return login_timestamp
    else:
        dt = login_timestamp
    
    return dt.strftime('%H:%M:%S')


def build_email_html(logins, datum):
    """
    Erstellt HTML-E-Mail mit Liste der eingeloggten Benutzer.
    
    Args:
        logins: List[Dict] - Liste der eingeloggten Benutzer
        datum: date - Datum des Reports
    
    Returns:
        str: HTML-Content
    """
    datum_str = datum.strftime('%d.%m.%Y')
    wochentag = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'][datum.weekday()]
    
    # HTML-Tabelle für Benutzer
    if logins:
        user_rows = ''
        for i, login in enumerate(logins, 1):
            login_time = format_login_time(login['last_login'])
            user_rows += f"""
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 8px; text-align: center;">{i}</td>
                    <td style="padding: 8px;">{login['display_name']}</td>
                    <td style="padding: 8px; color: #666;">{login['username']}</td>
                    <td style="padding: 8px; color: #666;">{login['ou']}</td>
                    <td style="padding: 8px; color: #666;">{login['title'] or '-'}</td>
                    <td style="padding: 8px; text-align: center; color: #28a745; font-weight: bold;">{login_time}</td>
                </tr>
            """
        
        table_content = f"""
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <thead>
                    <tr style="background-color: #0066cc; color: white;">
                        <th style="padding: 12px; text-align: center; width: 50px;">#</th>
                        <th style="padding: 12px; text-align: left;">Name</th>
                        <th style="padding: 12px; text-align: left;">Benutzername</th>
                        <th style="padding: 12px; text-align: left;">Abteilung</th>
                        <th style="padding: 12px; text-align: left;">Titel</th>
                        <th style="padding: 12px; text-align: center;">Login-Zeit</th>
                    </tr>
                </thead>
                <tbody>
                    {user_rows}
                </tbody>
            </table>
        """
    else:
        table_content = """
            <div style="padding: 20px; text-align: center; color: #999; font-style: italic;">
                Keine Benutzer haben sich heute eingeloggt.
            </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        </style>
    </head>
    <body style="margin: 0; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 900px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            
            <h1 style="color: #0066cc; margin-top: 0; border-bottom: 3px solid #0066cc; padding-bottom: 10px;">
                🔐 DRIVE Login-Report
            </h1>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0; font-size: 16px;">
                    <strong>Datum:</strong> {wochentag}, {datum_str}
                </p>
                <p style="margin: 5px 0; font-size: 16px;">
                    <strong>Anzahl eingeloggter Benutzer:</strong> 
                    <span style="color: #28a745; font-weight: bold; font-size: 18px;">{len(logins)}</span>
                </p>
            </div>
            
            {table_content}
            
            <p style="color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
                Automatisch generiert von DRIVE<br>
                <a href="http://drive.auto-greiner.de/admin/users" style="color: #0066cc;">Benutzer-Verwaltung in DRIVE öffnen</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    return html


def main():
    """Hauptfunktion"""
    print(f"\n{'='*60}")
    print("DRIVE Login-Report Generator")
    print(f"{'='*60}\n")
    
    try:
        # Datum
        heute = date.today()
        print(f"Datum: {heute.strftime('%d.%m.%Y')}")
        
        # Hole eingeloggte Benutzer
        print("\n[1] Lade eingeloggte Benutzer...")
        logins = get_todays_logins()
        print(f"    {len(logins)} Benutzer haben sich heute eingeloggt")
        
        if logins:
            for login in logins:
                login_time = format_login_time(login['last_login'])
                print(f"    - {login['display_name']} ({login['ou']}) - {login_time}")
        
        # HTML erstellen
        print("\n[2] Erstelle E-Mail...")
        html_body = build_email_html(logins, heute)
        
        # Betreff
        betreff = f"DRIVE Login-Report - {heute.strftime('%d.%m.%Y')} ({len(logins)} Benutzer)"
        
        # E-Mail senden
        print("\n[3] Sende E-Mail...")
        print(f"    Absender: {ABSENDER}")
        print(f"    Empfänger: {EMPFAENGER}")
        print(f"    Betreff: {betreff}")
        
        from api.graph_mail_connector import GraphMailConnector
        connector = GraphMailConnector()
        
        connector.send_mail(
            sender_email=ABSENDER,
            to_emails=[EMPFAENGER],
            subject=betreff,
            body_html=html_body
        )
        
        print(f"\n✅ ERFOLG! E-Mail gesendet.")
        print(f"{'='*60}\n")
        return 0
    
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n{'='*60}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
