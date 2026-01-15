"""
QA API - Feature-Prüfungen & Bug-Reports
==========================================
TAG 192: MVP für tägliche Feature-Prüfung und Fehlermeldung

Funktionen:
- Feature-Prüfungen speichern/abrufen
- Bug-Reports erstellen/abrufen
- Feature-Liste für User
- Statistiken
"""
from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from datetime import datetime, date, timedelta
import json
import os
import logging

from api.db_connection import get_db
from api.db_utils import db_session, row_to_dict, rows_to_list
from config.roles_config import get_allowed_features, get_feature_access_from_db

logger = logging.getLogger(__name__)

qa_api = Blueprint('qa_api', __name__)


# =============================================================================
# FEATURE-LISTE FÜR USER
# =============================================================================

@qa_api.route('/api/qa/features', methods=['GET'])
def get_user_features():
    """Gibt alle Features zurück, auf die der User Zugriff hat"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Nicht authentifiziert'}), 401
        
        # Rolle des Users ermitteln
        user_role = current_user.role if hasattr(current_user, 'role') else 'mitarbeiter'
        
        # Features aus Config/DB laden
        feature_access = get_feature_access_from_db()
        allowed_features = []
        
        for feature_name, roles in feature_access.items():
            if '*' in roles or user_role in roles:
                allowed_features.append({
                    'name': feature_name,
                    'display_name': feature_name.replace('_', ' ').title()
                })
        
        # Sortieren nach Name
        allowed_features.sort(key=lambda x: x['name'])
        
        return jsonify({'features': allowed_features})
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Features: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# FEATURE-PRÜFUNGEN
# =============================================================================

@qa_api.route('/api/qa/checks', methods=['GET'])
def get_qa_checks():
    """Gibt alle QA-Checks für den User zurück (optional: für bestimmtes Datum)"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Nicht authentifiziert'}), 401
        
        user_id = current_user.id
        check_date = request.args.get('date')
        
        if check_date:
            try:
                check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Ungültiges Datum-Format (YYYY-MM-DD)'}), 400
        else:
            check_date = date.today()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id,
                feature_name,
                check_date,
                status,
                notes,
                checked_at
            FROM feature_qa_checks
            WHERE user_id = %s AND check_date = %s
            ORDER BY feature_name
        ''', (user_id, check_date))
        
        checks = rows_to_list(cursor.fetchall())
        conn.close()
        
        return jsonify({
            'checks': checks,
            'date': check_date.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der QA-Checks: {e}")
        return jsonify({'error': str(e)}), 500


@qa_api.route('/api/qa/checks', methods=['POST'])
def save_qa_check():
    """Speichert einen QA-Check"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Nicht authentifiziert'}), 401
        
        data = request.get_json()
        feature_name = data.get('feature_name')
        status = data.get('status')
        notes = data.get('notes', '')
        check_date_str = data.get('date')
        
        if not feature_name or not status:
            return jsonify({'error': 'feature_name und status sind erforderlich'}), 400
        
        if status not in ['passed', 'failed', 'warning', 'not_checked']:
            return jsonify({'error': 'Ungültiger Status'}), 400
        
        if check_date_str:
            try:
                check_date = datetime.strptime(check_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Ungültiges Datum-Format (YYYY-MM-DD)'}), 400
        else:
            check_date = date.today()
        
        user_id = current_user.id
        
        conn = get_db()
        cursor = conn.cursor()
        
        # INSERT oder UPDATE (ON CONFLICT)
        cursor.execute('''
            INSERT INTO feature_qa_checks (user_id, feature_name, check_date, status, notes, checked_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, feature_name, check_date)
            DO UPDATE SET
                status = EXCLUDED.status,
                notes = EXCLUDED.notes,
                checked_at = CURRENT_TIMESTAMP
        ''', (user_id, feature_name, check_date, status, notes))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'QA-Check gespeichert'
        })
    
    except Exception as e:
        logger.error(f"Fehler beim Speichern des QA-Checks: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({'error': str(e)}), 500


@qa_api.route('/api/qa/checks/stats', methods=['GET'])
def get_qa_stats():
    """Gibt Statistiken für den User zurück (heute, letzte 7 Tage)"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Nicht authentifiziert'}), 401
        
        user_id = current_user.id
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Heute
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'passed') as passed,
                COUNT(*) FILTER (WHERE status = 'warning') as warning,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COUNT(*) FILTER (WHERE status = 'not_checked') as not_checked
            FROM feature_qa_checks
            WHERE user_id = %s AND check_date = %s
        ''', (user_id, today))
        
        today_stats = row_to_dict(cursor.fetchone())
        
        # Letzte 7 Tage
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'passed') as passed,
                COUNT(*) FILTER (WHERE status = 'warning') as warning,
                COUNT(*) FILTER (WHERE status = 'failed') as failed
            FROM feature_qa_checks
            WHERE user_id = %s AND check_date >= %s
        ''', (user_id, week_ago))
        
        week_stats = row_to_dict(cursor.fetchone())
        
        conn.close()
        
        return jsonify({
            'today': today_stats,
            'week': week_stats
        })
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der QA-Statistiken: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# BUG REPORTS
# =============================================================================

@qa_api.route('/api/qa/bugs', methods=['GET'])
def get_bugs():
    """Gibt alle Bugs zurück (mit Filtern)"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Nicht authentifiziert'}), 401
        
        # Filter-Parameter
        status = request.args.get('status')
        feature_name = request.args.get('feature')
        severity = request.args.get('severity')
        limit = request.args.get('limit', 50, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Query bauen
        query = '''
            SELECT 
                br.id,
                br.reporter_id,
                u.display_name as reporter_name,
                br.feature_name,
                br.title,
                br.description,
                br.severity,
                br.status,
                br.priority,
                br.created_at,
                br.updated_at,
                br.assigned_to
            FROM bug_reports br
            LEFT JOIN users u ON br.reporter_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if status:
            query += ' AND br.status = %s'
            params.append(status)
        
        if feature_name:
            query += ' AND br.feature_name = %s'
            params.append(feature_name)
        
        if severity:
            query += ' AND br.severity = %s'
            params.append(severity)
        
        query += ' ORDER BY br.created_at DESC LIMIT %s'
        params.append(limit)
        
        cursor.execute(query, params)
        bugs = rows_to_list(cursor.fetchall())
        
        conn.close()
        
        return jsonify({'bugs': bugs})
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Bugs: {e}")
        return jsonify({'error': str(e)}), 500


@qa_api.route('/api/qa/bugs', methods=['POST'])
def create_bug():
    """Erstellt einen neuen Bug-Report"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Nicht authentifiziert'}), 401
        
        data = request.get_json()
        
        # Pflichtfelder
        feature_name = data.get('feature_name')
        title = data.get('title')
        description = data.get('description')
        
        if not feature_name or not title or not description:
            return jsonify({'error': 'feature_name, title und description sind erforderlich'}), 400
        
        # Optionale Felder
        steps_to_reproduce = data.get('steps_to_reproduce', '')
        expected_behavior = data.get('expected_behavior', '')
        actual_behavior = data.get('actual_behavior', '')
        severity = data.get('severity', 'medium')
        browser_info = data.get('browser_info', '')
        url = data.get('url', '')
        screenshot_urls = data.get('screenshot_urls', [])
        
        if severity not in ['low', 'medium', 'high', 'critical']:
            severity = 'medium'
        
        # Browser-Info als JSON speichern
        if isinstance(browser_info, dict):
            browser_info = json.dumps(browser_info)
        
        user_id = current_user.id
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bug_reports (
                reporter_id, feature_name, title, description,
                steps_to_reproduce, expected_behavior, actual_behavior,
                severity, browser_info, url, screenshot_urls
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            user_id, feature_name, title, description,
            steps_to_reproduce, expected_behavior, actual_behavior,
            severity, browser_info, url, screenshot_urls
        ))
        
        bug_id = cursor.fetchone()['id']
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'bug_id': bug_id,
            'message': 'Bug-Report erstellt'
        })
    
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Bug-Reports: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({'error': str(e)}), 500


@qa_api.route('/api/qa/bugs/<int:bug_id>', methods=['GET'])
def get_bug_detail(bug_id):
    """Gibt Details eines Bugs zurück"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Nicht authentifiziert'}), 401
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                br.*,
                u.display_name as reporter_name,
                u2.display_name as assigned_to_name
            FROM bug_reports br
            LEFT JOIN users u ON br.reporter_id = u.id
            LEFT JOIN users u2 ON br.assigned_to = u2.id
            WHERE br.id = %s
        ''', (bug_id,))
        
        bug = row_to_dict(cursor.fetchone())
        
        if not bug:
            conn.close()
            return jsonify({'error': 'Bug nicht gefunden'}), 404
        
        # Browser-Info parsen falls JSON
        if bug.get('browser_info'):
            try:
                bug['browser_info'] = json.loads(bug['browser_info'])
            except:
                pass
        
        conn.close()
        
        return jsonify({'bug': bug})
    
    except Exception as e:
        logger.error(f"Fehler beim Laden des Bug-Details: {e}")
        return jsonify({'error': str(e)}), 500


@qa_api.route('/api/qa/bugs/<int:bug_id>', methods=['PUT'])
def update_bug(bug_id):
    """Aktualisiert einen Bug (Status, Priorität, etc.)"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Nicht authentifiziert'}), 401
        
        # Nur Admin kann Bugs aktualisieren (später erweitern)
        if not hasattr(current_user, 'role') or current_user.role != 'admin':
            return jsonify({'error': 'Keine Berechtigung'}), 403
        
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Prüfen ob Bug existiert
        cursor.execute('SELECT id FROM bug_reports WHERE id = %s', (bug_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Bug nicht gefunden'}), 404
        
        # Update-Felder
        update_fields = []
        params = []
        
        if 'status' in data:
            update_fields.append('status = %s')
            params.append(data['status'])
        
        if 'priority' in data:
            update_fields.append('priority = %s')
            params.append(data['priority'])
        
        if 'assigned_to' in data:
            update_fields.append('assigned_to = %s')
            params.append(data['assigned_to'])
        
        if 'resolution_notes' in data:
            update_fields.append('resolution_notes = %s')
            params.append(data['resolution_notes'])
            if data.get('status') == 'fixed':
                update_fields.append('resolved_at = CURRENT_TIMESTAMP')
        
        if not update_fields:
            conn.close()
            return jsonify({'error': 'Keine Felder zum Aktualisieren'}), 400
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        params.append(bug_id)
        
        query = f'UPDATE bug_reports SET {", ".join(update_fields)} WHERE id = %s'
        cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Bug aktualisiert'
        })
    
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren des Bugs: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({'error': str(e)}), 500
