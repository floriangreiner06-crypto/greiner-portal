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

# Client-Cache: pro Center (deggendorf, landau) oder '' für Default
_clients = {}

def _invalidate_gudat_client(center: str = None):
    """Entfernt gecachten Client (z. B. nach Session-Fehler), nächster Aufruf macht frischen Login."""
    global _clients
    key = (center or '').strip().lower()
    if key in ('', 'deggendorf'):
        key = 'default'
    _clients.pop(key, None)
    logger.info("Gudat-Client-Cache invalidiert: center=%s", key or 'deggendorf')

def _load_gudat_full_config():
    """Lädt komplette Gudat-Config (group, centers mit username/password)."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config.get('external_systems', {}).get('gudat', {})

def get_gudat_client(center: str = None) -> GudatClient:
    """
    Holt oder erstellt den Gudat-Client (KIC).
    center: 'deggendorf' | 'landau' | None (None = Default Deggendorf, wie bisher)
    """
    global _clients
    key = (center or '').strip().lower()
    if key in ('', 'deggendorf'):
        key = 'default'
    if key not in _clients:
        try:
            gudat = _load_gudat_full_config()
            group = gudat.get('group') or 'greiner'
            centers = gudat.get('centers') or {}
            if key == 'default':
                # Deggendorf: aus centers.deggendorf, Fallback Top-Level
                c = centers.get('deggendorf', {})
                username = c.get('username') or gudat.get('username')
                password = c.get('password') or gudat.get('password')
                base_url = f"https://werkstattplanung.net/{group}/deggendorf/kic"
            else:
                if key not in centers:
                    raise ValueError(f"Center '{center}' nicht in gudat.centers konfiguriert")
                c = centers[key]
                username = c.get('username')
                password = c.get('password')
                base_url = f"https://werkstattplanung.net/{group}/{key}/kic"
            if not username or not password:
                raise ValueError("Gudat Credentials nicht in config/credentials.json gefunden")
            _clients[key] = GudatClient(username, password, base_url=base_url)
            if not _clients[key].login():
                raise Exception("Gudat Login fehlgeschlagen")
            logger.info("Gudat-Client initialisiert: center=%s", key)
        except Exception as e:
            logger.error("Gudat-Client Initialisierung fehlgeschlagen (center=%s): %s", key, e)
            raise
    return _clients[key]


# =============================================================================
# Endpoints
# =============================================================================

@gudat_bp.route('/health', methods=['GET'])
def health():
    """Health-Check für Gudat-Integration (optional: ?center=deggendorf|landau)"""
    try:
        center = request.args.get('center', type=str)
        client = get_gudat_client(center=center)
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
        center: deggendorf | landau (optional, default: deggendorf)
    
    Returns:
        JSON mit Kapazitäts-Summary
    """
    try:
        date = request.args.get('date')
        center = request.args.get('center', type=str)
        
        client = get_gudat_client(center=center)
        data = client.get_workload_summary(date)
        
        if 'error' in data:
            err = data.get('error', '')
            if 'Login' in err or '401' in err or 'Session' in err:
                _invalidate_gudat_client(center)
            return jsonify(data), 400
        
        return jsonify(data)
        
    except ValueError as e:
        logger.warning("Gudat Workload (center=%s): %s", center, e)
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        logger.error("Workload-Fehler (center=%s): %s", center, e)
        return jsonify({'error': str(e)}), 503


@gudat_bp.route('/workload/week', methods=['GET'])
def get_workload_week():
    """
    Holt Wochen-Kapazitäts-Übersicht
    
    Query-Parameter:
        start_date: Startdatum (YYYY-MM-DD), default: heute
        with_teams: Wenn true, werden Team-Daten pro Tag mitgeliefert (TAG 200)
        center: deggendorf | landau (optional)
    
    Returns:
        JSON mit täglichen Kapazitäts-Daten
        Wenn with_teams=true: Enthält auch 'teams_per_day' mit Team-Daten pro Tag
    """
    try:
        start_date = request.args.get('start_date')
        with_teams = request.args.get('with_teams', 'false').lower() == 'true'
        center = request.args.get('center', type=str)
        
        client = get_gudat_client(center=center)
        data = client.get_week_overview(start_date)
        
        if 'error' in data:
            err = data.get('error', '')
            if 'Login' in err or '401' in err or 'Session' in err:
                _invalidate_gudat_client(center)
            return jsonify(data), 400
        
        # TAG 200: Team-Daten pro Tag hinzufügen
        if with_teams:
            raw_data = client.get_workload_raw(start_date, days=7)
            if raw_data:
                # Gruppiere nach Datum
                teams_per_day = {}
                for team in raw_data:
                    team_name = team.get('name', '')
                    team_id = team.get('id')
                    category = team.get('category_name', '')
                    
                    for date, day_data in team.get('data', {}).items():
                        if date not in teams_per_day:
                            teams_per_day[date] = []
                        
                        teams_per_day[date].append({
                            'id': team_id,
                            'name': team_name,
                            'category': category,
                            'capacity': day_data.get('base_workload', 0),
                            'planned': day_data.get('planned_workload', 0),
                            'free': day_data.get('free_workload', 0),
                            'absent': day_data.get('absence_workload', 0),
                            'plannable': day_data.get('plannable_workload', 0),
                            'utilization': round(day_data.get('planned_workload', 0) / day_data.get('base_workload', 0) * 100, 1) if day_data.get('base_workload', 0) > 0 else 0,
                            'status': 'overloaded' if day_data.get('free_workload', 0) < 0 else ('warning' if day_data.get('free_workload', 0) < day_data.get('base_workload', 0) * 0.1 else 'ok')
                        })
                
                data['teams_per_day'] = teams_per_day
        
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
        center: deggendorf | landau (optional)
    
    Returns:
        JSON mit rohen Team-Daten
    """
    try:
        date = request.args.get('date')
        days = int(request.args.get('days', 7))
        center = request.args.get('center', type=str)
        
        if days < 1 or days > 14:
            return jsonify({'error': 'days muss zwischen 1 und 14 liegen'}), 400
        
        client = get_gudat_client(center=center)
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
        center: deggendorf | landau (optional)
    
    Returns:
        JSON mit Team-Liste und Status
    """
    try:
        date = request.args.get('date')
        center = request.args.get('center', type=str)
        
        client = get_gudat_client(center=center)
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
    """Holt aktuellen Benutzer (für Debugging). Optional: ?center=deggendorf|landau"""
    try:
        center = request.args.get('center', type=str)
        client = get_gudat_client(center=center)
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
