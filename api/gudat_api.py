#!/usr/bin/env python3
"""
=============================================================================
GREINER DRIVE - Gudat Werkstattplanung API Blueprint
=============================================================================
Flask-Blueprint für die Integration der Gudat-Kapazitätsdaten ins Greiner Portal

Endpoints:
    GET /api/gudat/health          - Health-Check
    GET /api/gudat/workload        - Tages-Kapazität
    GET /api/gudat/workload/week   - Wochen-Übersicht
    GET /api/gudat/teams           - Team-Details

Autor: Claude AI für Greiner Portal
Version: 1.0 (TAG 97)
Datum: 2025-12-06
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

# Füge tools-Verzeichnis zum Path hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from gudat_client import GudatClient

logger = logging.getLogger(__name__)

# Blueprint erstellen
gudat_bp = Blueprint('gudat', __name__, url_prefix='/api/gudat')

# Client-Instanz (wird bei erstem Request initialisiert)
_client = None

def get_gudat_client() -> GudatClient:
    """Holt oder erstellt den Gudat-Client"""
    global _client
    
    if _client is None:
        # Lade Credentials aus Config
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json')
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            gudat_config = config.get('external_systems', {}).get('gudat', {})
            username = gudat_config.get('username')
            password = gudat_config.get('password')
            
            logger.info(f"Gudat-Config geladen: URL={gudat_config.get('portal_url')}, User={username}")
            
            if not username or not password:
                raise ValueError("Gudat Credentials nicht in config/credentials.json gefunden")
            
            _client = GudatClient(username, password)
            
            # Login durchführen
            if not _client.login():
                raise Exception("Gudat Login fehlgeschlagen")
            
            logger.info("Gudat-Client erfolgreich initialisiert")
            
        except Exception as e:
            logger.error(f"Gudat-Client Initialisierung fehlgeschlagen: {e}")
            raise
    
    return _client


# =============================================================================
# Endpoints
# =============================================================================

@gudat_bp.route('/health', methods=['GET'])
def health():
    """Health-Check für Gudat-Integration"""
    try:
        client = get_gudat_client()
        return jsonify({
            'status': 'healthy',
            'service': 'gudat',
            'logged_in': client._logged_in,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'gudat',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


@gudat_bp.route('/workload', methods=['GET'])
def get_workload():
    """
    Holt Kapazitäts-Übersicht für einen Tag
    
    Query-Parameter:
        date: Datum (YYYY-MM-DD), default: heute
    
    Returns:
        JSON mit Kapazitäts-Summary
    """
    try:
        date = request.args.get('date')
        
        client = get_gudat_client()
        data = client.get_workload_summary(date)
        
        if 'error' in data:
            return jsonify(data), 400
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Workload-Fehler: {e}")
        return jsonify({'error': str(e)}), 500


@gudat_bp.route('/workload/week', methods=['GET'])
def get_workload_week():
    """
    Holt Wochen-Kapazitäts-Übersicht
    
    Query-Parameter:
        start_date: Startdatum (YYYY-MM-DD), default: heute
    
    Returns:
        JSON mit täglichen Kapazitäts-Daten
    """
    try:
        start_date = request.args.get('start_date')
        
        client = get_gudat_client()
        data = client.get_week_overview(start_date)
        
        if 'error' in data:
            return jsonify(data), 400
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Wochen-Workload-Fehler: {e}")
        return jsonify({'error': str(e)}), 500


@gudat_bp.route('/workload/raw', methods=['GET'])
def get_workload_raw():
    """
    Holt rohe Workload-Daten (für Debugging/ML)
    
    Query-Parameter:
        date: Startdatum (YYYY-MM-DD), default: heute
        days: Anzahl Tage (1-14), default: 7
    
    Returns:
        JSON mit rohen Team-Daten
    """
    try:
        date = request.args.get('date')
        days = int(request.args.get('days', 7))
        
        if days < 1 or days > 14:
            return jsonify({'error': 'days muss zwischen 1 und 14 liegen'}), 400
        
        client = get_gudat_client()
        data = client.get_workload_raw(date, days)
        
        if not data:
            return jsonify({'error': 'Keine Daten erhalten'}), 400
        
        return jsonify({
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'days': days,
            'teams': data,
            'teams_count': len(data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Raw-Workload-Fehler: {e}")
        return jsonify({'error': str(e)}), 500


@gudat_bp.route('/teams', methods=['GET'])
def get_teams():
    """
    Holt Team-Details für einen Tag
    
    Query-Parameter:
        date: Datum (YYYY-MM-DD), default: heute
    
    Returns:
        JSON mit Team-Liste und Status
    """
    try:
        date = request.args.get('date')
        
        client = get_gudat_client()
        summary = client.get_workload_summary(date)
        
        if 'error' in summary:
            return jsonify(summary), 400
        
        return jsonify({
            'date': summary['date'],
            'teams': summary['teams'],
            'teams_count': summary['teams_count'],
            'timestamp': summary['timestamp']
        })
        
    except Exception as e:
        logger.error(f"Teams-Fehler: {e}")
        return jsonify({'error': str(e)}), 500


@gudat_bp.route('/user', methods=['GET'])
def get_user():
    """Holt aktuellen Benutzer (für Debugging)"""
    try:
        client = get_gudat_client()
        data = client.get_current_user()
        
        if 'error' in data:
            return jsonify(data), 400
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"User-Fehler: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Blueprint registrieren (in app.py aufrufen)
# =============================================================================
def register_gudat_api(app):
    """Registriert den Gudat-Blueprint in der Flask-App"""
    app.register_blueprint(gudat_bp)
    logger.info("Gudat-API Blueprint registriert unter /api/gudat/")
