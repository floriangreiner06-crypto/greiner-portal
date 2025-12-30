#!/usr/bin/env python3
"""
Portal-Namen Umfrage versenden
Sendet eine E-Mail-Umfrage an ausgewählte Mitarbeiter zur Namenswahl für das Portal.

Verwendung:
    python3 scripts/send_portal_name_survey.py
"""

import sys
import os
from datetime import datetime, timedelta

# Pfad für Imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.graph_mail_connector import GraphMailConnector

# Absender
DRIVE_EMAIL = 'drive@auto-greiner.de'

# =============================================================================
# EMPFÄNGER-LISTE (ANPASSEN!)
# =============================================================================

# TODO: Hier die E-Mail-Adressen der ausgewählten Mitarbeiter eintragen
SURVEY_RECIPIENTS = [
    'florian.greiner@auto-greiner.de',  # Validierung
]

# Falls leer, wird eine Warnung ausgegeben
if not SURVEY_RECIPIENTS:
    print("⚠️  WARNUNG: SURVEY_RECIPIENTS ist leer!")
    print("Bitte in scripts/send_portal_name_survey.py die Empfänger eintragen.")
    print("\nBeispiel:")
    print("SURVEY_RECIPIENTS = [")
    print("    'florian.greiner@auto-greiner.de',")
    print("    'geschaeftsfuehrung@auto-greiner.de',")
    print("]")
    sys.exit(1)

# =============================================================================
# E-MAIL-VORLAGE
# =============================================================================

def get_survey_email_html(survey_url=None, email=None):
    """HTML-Vorlage für die Umfrage-E-Mail"""
    # Standard-URL falls nicht angegeben
    if not survey_url:
        survey_url = "http://drive.auto-greiner.de/api/survey/portal-name"
    if not email:
        email = ""
    
    # URL-Encoding für E-Mail
    email_param = email if email else ""
    
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #1e3a5f 0%, #28a745 100%);
            color: white;
            padding: 30px;
            border-radius: 8px 8px 0 0;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
        }
        .content {
            background: #ffffff;
            padding: 30px;
            border: 1px solid #dee2e6;
            border-top: none;
        }
        .intro {
            font-size: 16px;
            margin-bottom: 30px;
            color: #495057;
        }
        .option {
            background: #f8f9fa;
            border-left: 4px solid #1e3a5f;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .option h3 {
            margin-top: 0;
            color: #1e3a5f;
            font-size: 22px;
        }
        .option.current {
            border-left-color: #28a745;
            background: #f0f9f4;
        }
        .option.current h3::after {
            content: " (aktuell)";
            color: #28a745;
            font-size: 14px;
            font-weight: normal;
        }
        .acronym {
            font-weight: bold;
            color: #1e3a5f;
        }
        .description {
            color: #6c757d;
            margin-top: 10px;
            font-size: 14px;
        }
        .cta {
            background: #1e3a5f;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 4px;
            margin: 30px 0;
        }
        .cta a {
            color: white;
            text-decoration: none;
            font-weight: bold;
            font-size: 18px;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            font-size: 12px;
            color: #6c757d;
            text-align: center;
        }
        .deadline {
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
            text-align: center;
        }
        .deadline strong {
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏁 Portal-Namen Umfrage</h1>
    </div>
    
    <div class="content">
        <div class="intro">
            <p>Liebe Kolleginnen und Kollegen,</p>
            
            <p>unser integriertes ERP-System benötigt einen passenden Namen. Aktuell nutzen wir <strong>"DRIVE"</strong>, 
            haben aber auch drei weitere Optionen entwickelt, die besser zu unserem System passen könnten.</p>
            
            <p>Wir möchten <strong>Ihre Meinung</strong> einholen, bevor wir eine finale Entscheidung treffen.</p>
        </div>
        
        <div class="deadline">
            <strong>⏰ Bitte antworten Sie bis zum [DEADLINE]</strong>
        </div>
        
        <h2 style="color: #1e3a5f; margin-top: 30px;">Die Optionen:</h2>
        
        <!-- Option 1: DRIVE (aktuell) -->
        <div class="option current">
            <h3>DRIVE</h3>
            <p>
                <span class="acronym">Digitale Reporting- und Informations-Visualisierungs-Einheit</span><br>
                <span class="acronym">Digital Real-time Integrated Vehicle Enterprise</span>
            </p>
            <div class="description">
                ✓ Bereits etabliert und bekannt<br>
                ✓ Mehrere passende Bedeutungen<br>
                ⚠️ Weniger spezifisch für unser System
            </div>
        </div>
        
        <!-- Option 2: PULSE -->
        <div class="option">
            <h3>PULSE</h3>
            <p>
                <span class="acronym">Performance & Unified Logistics System Enterprise</span>
            </p>
            <div class="description">
                ✓ Dynamisch und lebendig - "der Puls des Unternehmens"<br>
                ✓ Passt perfekt zu Live-Daten und Werkstatt-Kapazität<br>
                ✓ Kurz, prägnant, einprägsam
            </div>
        </div>
        
        <!-- Option 3: CORE -->
        <div class="option">
            <h3>CORE</h3>
            <p>
                <span class="acronym">Central Operations & Reporting Engine</span>
            </p>
            <div class="description">
                ✓ Klar und zentral - das Kernsystem<br>
                ✓ Professionell und seriös<br>
                ✓ Einfach zu merken und auszusprechen
            </div>
        </div>
        
        <!-- Option 4: NEXUS -->
        <div class="option">
            <h3>NEXUS</h3>
            <p>
                <span class="acronym">Networked Excellence & Unified System</span>
            </p>
            <div class="description">
                ✓ Modern und technisch - der Verbindungspunkt<br>
                ✓ Betont die Integration verschiedener Bereiche<br>
                ✓ Klingt professionell und zukunftsorientiert
            </div>
        </div>
        
        <div style="margin: 30px 0; text-align: center;">
            <h3 style="color: #1e3a5f;">Ihre Auswahl:</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
                <a href="SURVEY_URL_PLACEHOLDER?choice=DRIVE&email=EMAIL_PLACEHOLDER"
                   style="display: block; background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 18px;">
                    ✅ DRIVE
                </a>
                <a href="SURVEY_URL_PLACEHOLDER?choice=PULSE&email=EMAIL_PLACEHOLDER"
                   style="display: block; background: #1e3a5f; color: white; padding: 20px; text-align: center; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 18px;">
                    ✅ PULSE
                </a>
                <a href="SURVEY_URL_PLACEHOLDER?choice=CORE&email=EMAIL_PLACEHOLDER"
                   style="display: block; background: #1e3a5f; color: white; padding: 20px; text-align: center; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 18px;">
                    ✅ CORE
                </a>
                <a href="SURVEY_URL_PLACEHOLDER?choice=NEXUS&email=EMAIL_PLACEHOLDER"
                   style="display: block; background: #1e3a5f; color: white; padding: 20px; text-align: center; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 18px;">
                    ✅ NEXUS
                </a>
            </div>
            <p style="font-size: 14px; color: #6c757d; margin-top: 20px;">
                Klicken Sie einfach auf den Button Ihrer Wahl. Sie werden zu einer Bestätigungsseite weitergeleitet.
            </p>
        </div>
        
        <div class="footer">
            <p>Diese E-Mail wurde automatisch vom Greiner Portal System gesendet.</p>
            <p>Bei Fragen wenden Sie sich bitte an die Geschäftsführung.</p>
        </div>
    </div>
</body>
</html>
    """
    
    # Variablen ersetzen
    html_template = html_template.replace('SURVEY_URL_PLACEHOLDER', survey_url)
    html_template = html_template.replace('EMAIL_PLACEHOLDER', email_param)
    
    return html_template


def send_survey():
    """Versendet die Umfrage-E-Mail an alle Empfänger"""
    
    if not SURVEY_RECIPIENTS:
        print("❌ Keine Empfänger definiert!")
        return False
    
    try:
        graph = GraphMailConnector()
        
        # Deadline berechnen (z.B. 7 Tage ab heute)
        deadline = (datetime.now() + timedelta(days=7)).strftime('%d.%m.%Y')
        
        # HTML-Vorlage laden und Deadline + URLs einfügen
        survey_url = "http://drive.auto-greiner.de/api/survey/portal-name"
        html_content = get_survey_email_html(survey_url=survey_url, email="")
        html_content = html_content.replace('[DEADLINE]', deadline)
        
        subject = "🏁 Umfrage: Portal-Namen - Ihre Meinung ist gefragt!"
        
        # E-Mail versenden
        result = graph.send_mail(
            sender_email=DRIVE_EMAIL,
            to_emails=SURVEY_RECIPIENTS,
            subject=subject,
            body_html=html_content
        )
        
        if result:
            print(f"✅ Umfrage erfolgreich versendet an {len(SURVEY_RECIPIENTS)} Empfänger:")
            for email in SURVEY_RECIPIENTS:
                print(f"   - {email}")
            print(f"\n📅 Deadline für Antworten: {deadline}")
            return True
        else:
            print("❌ Fehler beim Versenden der E-Mail")
            return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False


def preview_email():
    """Zeigt eine Vorschau der E-Mail (HTML in Datei speichern)"""
    survey_url = "http://drive.auto-greiner.de/api/survey/portal-name"
    html_content = get_survey_email_html(survey_url=survey_url, email="")
    html_content = html_content.replace('[DEADLINE]', 'DD.MM.YYYY')
    
    preview_file = 'docs/portal_name_survey_preview.html'
    os.makedirs(os.path.dirname(preview_file), exist_ok=True)
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Vorschau gespeichert: {preview_file}")
    print("   Öffnen Sie die Datei im Browser, um die E-Mail zu sehen.")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Portal-Namen Umfrage versenden')
    parser.add_argument('--preview', action='store_true', 
                       help='Nur Vorschau erstellen (keine E-Mail senden)')
    parser.add_argument('--send', action='store_true',
                       help='E-Mail tatsächlich versenden')
    parser.add_argument('--force', action='store_true',
                       help='Versand ohne Bestätigung')
    
    args = parser.parse_args()
    
    if args.preview:
        preview_email()
    elif args.send:
        print("=" * 60)
        print("Portal-Namen Umfrage - Versand")
        print("=" * 60)
        print(f"Empfänger: {len(SURVEY_RECIPIENTS)}")
        print()
        
        if args.force:
            send_survey()
        else:
            confirm = input("Möchten Sie die Umfrage wirklich versenden? (ja/nein): ")
            if confirm.lower() in ['ja', 'j', 'yes', 'y']:
                send_survey()
            else:
                print("Abgebrochen.")
    else:
        print("Portal-Namen Umfrage Tool")
        print()
        print("Verwendung:")
        print("  python3 scripts/send_portal_name_survey.py --preview  # Vorschau erstellen")
        print("  python3 scripts/send_portal_name_survey.py --send     # E-Mail versenden")
        print()
        print("⚠️  WICHTIG: Bitte zuerst SURVEY_RECIPIENTS in der Datei anpassen!")

