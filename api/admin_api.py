"""
Admin API - Health & Logs
==========================
Bereinigt: TAG 120 - Obsolete Job-Endpoints entfernt (jetzt via Celery)

Celery Task Management: /admin/celery/
Flower Dashboard: :5555
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import os

admin_api = Blueprint('admin_api', __name__)


@admin_api.route('/api/admin/logs', methods=['GET'])
def list_logs():
    """Liste alle verfügbaren Log-Dateien"""
    log_dir = '/opt/greiner-portal/logs'
    try:
        logs = []
        if os.path.exists(log_dir):
            for f in os.listdir(log_dir):
                if f.endswith('.log'):
                    path = os.path.join(log_dir, f)
                    stat = os.stat(path)
                    logs.append({
                        'name': f,
                        'size_kb': round(stat.st_size / 1024, 1),
                        'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            logs.sort(key=lambda x: x['last_modified'], reverse=True)
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/health', methods=['GET'])
def admin_health():
    """Health-Check Endpoint"""
    return jsonify({
        'status': 'ok',
        'scheduler': 'celery',
        'version': '3.0-tag120',
        'timestamp': datetime.now().isoformat()
    })
