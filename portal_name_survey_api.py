"""
Portal-Namen Umfrage API
Verwaltet die Umfrage-Ergebnisse und stellt Endpoints für die Abstimmung bereit.
"""

from flask import Blueprint, request, jsonify, render_template_string
from datetime import datetime
import os
import sys

# Pfad für Imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import db_session
from api.graph_mail_connector import GraphMailConnector

portal_name_survey_bp = Blueprint('portal_name_survey', __name__)

# Umfrage-Optionen
SURVEY_OPTIONS = {
    'DRIVE': 'DRIVE - Digitale Reporting- und Informations-Visualisierungs-Einheit',
    'PULSE': 'PULSE - Performance & Unified Logistics System Enterprise',
    'CORE': 'CORE - Central Operations & Reporting Engine',
    'NEXUS': 'NEXUS - Networked Excellence & Unified System'
}

# Absender für Ergebnis-E-Mail
RESULT_EMAIL = 'florian.greiner@auto-greiner.de'
DRIVE_EMAIL = 'drive@auto-greiner.de'


def init_survey_table():
    """Erstellt die Umfrage-Tabelle falls sie nicht existiert"""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Prüfe ob Tabelle existiert (PostgreSQL)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'portal_name_survey'
                );
            """)
            exists = cursor.fetchone()[0]
            
            if not exists:
                cursor.execute("""
                    CREATE TABLE portal_name_survey (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) NOT NULL,
                        choice VARCHAR(50) NOT NULL,
                        reason TEXT,
                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(email)
                    );
                """)
                conn.commit()
                print("✅ Umfrage-Tabelle erstellt")
            else:
                print("ℹ️  Umfrage-Tabelle existiert bereits")
                
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Tabelle: {e}")
        import traceback
        traceback.print_exc()


@portal_name_survey_bp.route('/api/survey/portal-name', methods=['POST', 'GET'])
def submit_survey_choice():
    """
    Endpoint für die Umfrage-Auswahl
    GET: Zeigt Bestätigungsseite
    POST: Speichert die Auswahl
    """
    if request.method == 'GET':
        # GET-Request: Zeige Bestätigungsseite mit Auswahl-Formular
        choice = request.args.get('choice', '')
        email = request.args.get('email', '')
        
        if choice not in SURVEY_OPTIONS:
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Portal-Namen Umfrage</title>
                    <style>
                        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                        .error { background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; }
                    </style>
                </head>
                <body>
                    <div class="error">
                        <h2>❌ Ungültige Auswahl</h2>
                        <p>Die gewählte Option ist nicht gültig. Bitte verwenden Sie die Links aus der E-Mail.</p>
                    </div>
                </body>
                </html>
            """), 400
        
        # Formular anzeigen
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Portal-Namen Umfrage - Bestätigung</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        max-width: 600px;
                        margin: 50px auto;
                        padding: 20px;
                        background: #f8f9fa;
                    }
                    .container {
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    h1 {
                        color: #1e3a5f;
                        margin-top: 0;
                    }
                    .choice {
                        background: #f0f9f4;
                        border-left: 4px solid #28a745;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 4px;
                    }
                    .choice strong {
                        color: #1e3a5f;
                        font-size: 18px;
                    }
                    form {
                        margin-top: 30px;
                    }
                    label {
                        display: block;
                        margin: 15px 0 5px 0;
                        color: #495057;
                        font-weight: bold;
                    }
                    input[type="email"] {
                        width: 100%;
                        padding: 10px;
                        border: 1px solid #dee2e6;
                        border-radius: 4px;
                        font-size: 14px;
                        box-sizing: border-box;
                    }
                    textarea {
                        width: 100%;
                        padding: 10px;
                        border: 1px solid #dee2e6;
                        border-radius: 4px;
                        font-size: 14px;
                        min-height: 100px;
                        box-sizing: border-box;
                        font-family: Arial, sans-serif;
                    }
                    button {
                        background: #1e3a5f;
                        color: white;
                        padding: 12px 30px;
                        border: none;
                        border-radius: 4px;
                        font-size: 16px;
                        cursor: pointer;
                        margin-top: 20px;
                    }
                    button:hover {
                        background: #2c5a8f;
                    }
                    .success {
                        background: #d4edda;
                        color: #155724;
                        padding: 15px;
                        border-radius: 4px;
                        margin-top: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🏁 Portal-Namen Umfrage</h1>
                    
                    <div class="choice">
                        <strong>Ihre Auswahl:</strong><br>
                        {{ choice_name }}
                    </div>
                    
                    <form method="POST" action="/api/survey/portal-name">
                        <input type="hidden" name="choice" value="{{ choice }}">
                        
                        <label for="email">Ihre E-Mail-Adresse:</label>
                        <input type="email" id="email" name="email" value="{{ email }}" required>
                        
                        <label for="reason">Optional: Begründung (warum diese Option?)</label>
                        <textarea id="reason" name="reason" placeholder="Ihre Begründung..."></textarea>
                        
                        <button type="submit">✅ Auswahl bestätigen</button>
                    </form>
                </div>
            </body>
            </html>
        """, choice=choice, choice_name=SURVEY_OPTIONS.get(choice, choice), email=email)
    
    else:
        # POST-Request: Speichere die Auswahl
        try:
            choice = request.form.get('choice') or request.json.get('choice')
            email = request.form.get('email') or request.json.get('email')
            reason = request.form.get('reason') or request.json.get('reason', '')
            
            if not choice or choice not in SURVEY_OPTIONS:
                return jsonify({'error': 'Ungültige Auswahl'}), 400
            
            if not email:
                return jsonify({'error': 'E-Mail-Adresse erforderlich'}), 400
            
            # Speichere in Datenbank
            with db_session() as conn:
                cursor = conn.cursor()
                
                # Prüfe ob bereits abgestimmt
                cursor.execute("SELECT id FROM portal_name_survey WHERE email = %s", (email,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update bestehender Eintrag
                    cursor.execute("""
                        UPDATE portal_name_survey 
                        SET choice = %s, reason = %s, submitted_at = CURRENT_TIMESTAMP
                        WHERE email = %s
                    """, (choice, reason, email))
                else:
                    # Neuer Eintrag
                    cursor.execute("""
                        INSERT INTO portal_name_survey (email, choice, reason)
                        VALUES (%s, %s, %s)
                    """, (email, choice, reason))
                
                conn.commit()
            
            # Erfolgsseite anzeigen
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Vielen Dank!</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            max-width: 600px;
                            margin: 50px auto;
                            padding: 20px;
                            background: #f8f9fa;
                        }
                        .container {
                            background: white;
                            padding: 30px;
                            border-radius: 8px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            text-align: center;
                        }
                        .success {
                            background: #d4edda;
                            color: #155724;
                            padding: 20px;
                            border-radius: 4px;
                            margin: 20px 0;
                        }
                        h1 { color: #28a745; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>✅ Vielen Dank!</h1>
                        <div class="success">
                            <p><strong>Ihre Auswahl wurde erfolgreich gespeichert.</strong></p>
                            <p>Sie haben sich für <strong>{{ choice_name }}</strong> entschieden.</p>
                        </div>
                        <p>Die Ergebnisse werden nach Ablauf der Umfrage-Frist ausgewertet.</p>
                    </div>
                </body>
                </html>
            """, choice_name=SURVEY_OPTIONS.get(choice, choice))
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500


@portal_name_survey_bp.route('/api/survey/portal-name/results', methods=['GET'])
def get_survey_results():
    """Gibt die Umfrage-Ergebnisse zurück (nur für interne Nutzung)"""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT choice, COUNT(*) as count, 
                       STRING_AGG(email, ', ') as emails
                FROM portal_name_survey
                GROUP BY choice
                ORDER BY count DESC
            """)
            
            results = []
            total = 0
            for row in cursor.fetchall():
                choice, count, emails = row
                results.append({
                    'choice': choice,
                    'count': count,
                    'emails': emails.split(', ') if emails else []
                })
                total += count
            
            return jsonify({
                'total': total,
                'results': results,
                'options': SURVEY_OPTIONS
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def send_results_email():
    """Sendet die Umfrage-Ergebnisse per E-Mail an den Initiator"""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT choice, COUNT(*) as count,
                       STRING_AGG(email, ', ') as emails
                FROM portal_name_survey
                GROUP BY choice
                ORDER BY count DESC
            """)
            
            results = []
            total = 0
            for row in cursor.fetchall():
                choice, count, emails = row
                results.append({
                    'choice': choice,
                    'name': SURVEY_OPTIONS.get(choice, choice),
                    'count': count,
                    'emails': emails.split(', ') if emails else []
                })
                total += count
            
            if total == 0:
                return False
            
            # HTML-E-Mail erstellen
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #1e3a5f; }}
                    .result {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #1e3a5f; }}
                    .winner {{ border-left-color: #28a745; background: #f0f9f4; }}
                    .count {{ font-size: 24px; font-weight: bold; color: #1e3a5f; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #dee2e6; }}
                    th {{ background: #1e3a5f; color: white; }}
                </style>
            </head>
            <body>
                <h1>📊 Portal-Namen Umfrage - Ergebnisse</h1>
                
                <p><strong>Gesamt: {total} Teilnehmer</strong></p>
                
                <table>
                    <tr>
                        <th>Option</th>
                        <th>Stimmen</th>
                        <th>Prozent</th>
                    </tr>
            """
            
            winner = results[0] if results else None
            for r in results:
                percent = (r['count'] / total * 100) if total > 0 else 0
                is_winner = r == winner
                row_class = 'winner' if is_winner else ''
                
                html += f"""
                    <tr class="{row_class}">
                        <td><strong>{r['name']}</strong></td>
                        <td class="count">{r['count']}</td>
                        <td>{percent:.1f}%</td>
                    </tr>
                """
            
            html += """
                </table>
                
                <h2>Detail-Übersicht:</h2>
            """
            
            for r in results:
                html += f"""
                <div class="result {'winner' if r == winner else ''}">
                    <h3>{r['name']} - {r['count']} Stimmen</h3>
                    <p><strong>Abgestimmt haben:</strong></p>
                    <ul>
                """
                for email in r['emails']:
                    html += f"<li>{email}</li>"
                
                html += """
                    </ul>
                </div>
                """
            
            html += """
                <hr>
                <p style="color: #6c757d; font-size: 12px;">
                    Automatisch generiert vom Greiner Portal System
                </p>
            </body>
            </html>
            """
            
            # E-Mail senden
            graph = GraphMailConnector()
            subject = f"📊 Portal-Namen Umfrage - Ergebnisse ({total} Teilnehmer)"
            
            return graph.send_mail(
                sender_email=DRIVE_EMAIL,
                to_emails=[RESULT_EMAIL],
                subject=subject,
                body_html=html
            )
            
    except Exception as e:
        print(f"❌ Fehler beim Senden der Ergebnisse: {e}")
        import traceback
        traceback.print_exc()
        return False

