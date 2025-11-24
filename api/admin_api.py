"""
Admin API - System Status & Job Monitoring
"""
from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime
import subprocess
import os

admin_api = Blueprint('admin_api', __name__)
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

JOB_SCRIPTS = {
    'verkauf_sync': 'scripts/sync/sync_sales.py',
    'stellantis_fahrzeuge': 'scripts/sync/import_stellantis.py',
    'employee_sync': 'scripts/sync/sync_employees.py --real',
    'mt940_import': 'scripts/imports/import_mt940.py /mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/',
    'santander_import': 'scripts/imports/import_santander_bestand.py',
    'hvb_pdf_import': None,
    'hyundai_finance': 'scripts/imports/import_hyundai_finance.py',
    'locosoft_stammdaten': 'scripts/sync/sync_fahrzeug_stammdaten.py',
    'umsatz_bereinigung': 'scripts/analysis/umsatz_bereinigung_production.py',
    'servicebox_scraper': 'tools/scrapers/servicebox_detail_scraper_pagination_final.py',
    'servicebox_import': 'scripts/imports/import_stellantis_bestellungen.py logs/servicebox_bestellungen_details_complete.json',
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def safe_query(cursor, query, default=0):
    """Führe Query aus, bei Fehler return default"""
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        return row[0] if row else default
    except:
        return default

@admin_api.route('/api/admin/system-status', methods=['GET'])
def get_system_status():
    """Hole Status aller System-Jobs"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM system_jobs ORDER BY is_active DESC, job_name")
        jobs = [dict(row) for row in cursor.fetchall()]
        
        for job in jobs:
            job['can_run'] = job['job_name'] in JOB_SCRIPTS and JOB_SCRIPTS[job['job_name']] is not None
            
            # Spezifische Live-Counts (sicher)
            if job['job_name'] == 'servicebox_import':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM stellantis_bestellungen")
                job['live_last'] = safe_query(cursor, "SELECT MAX(import_timestamp) FROM stellantis_bestellungen", None)
            elif job['job_name'] == 'verkauf_sync':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM sales")
            elif job['job_name'] == 'locosoft_stammdaten':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM dealer_vehicles")
            elif job['job_name'] == 'stellantis_fahrzeuge':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM dealer_vehicles WHERE hersteller LIKE '%tellantis%' OR hersteller IN ('Opel','Peugeot','Citroen','Fiat','Jeep')")
            elif job['job_name'] == 'mt940_import':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM transaktionen")
            elif job['job_name'] == 'employee_sync':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM employees")
            elif job['job_name'] == 'hyundai_finance':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM fahrzeugfinanzierungen WHERE bank LIKE '%yundai%'")
            elif job['job_name'] == 'santander_import':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM fahrzeugfinanzierungen WHERE bank LIKE '%antander%'")
        
        conn.close()
        return jsonify({'jobs': jobs, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/api/admin/job-run/<job_name>', methods=['POST'])
def run_job(job_name):
    """Job manuell starten"""
    if job_name not in JOB_SCRIPTS or JOB_SCRIPTS[job_name] is None:
        return jsonify({'error': f'Job {job_name} kann nicht manuell gestartet werden'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE system_jobs 
            SET last_status = 'running', last_run = ?, updated_at = ?
            WHERE job_name = ?
        """, (datetime.now().isoformat(), datetime.now().isoformat(), job_name))
        conn.commit()
        
        cursor.execute("""
            INSERT INTO system_job_history (job_name, run_start, status, message)
            VALUES (?, ?, 'running', 'Manuell gestartet')
        """, (job_name, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        script = JOB_SCRIPTS[job_name]
        log_file = f"logs/{job_name}.log"
        cmd = f"cd /opt/greiner-portal && venv/bin/python3 {script} >> {log_file} 2>&1 &"
        subprocess.Popen(cmd, shell=True)
        
        return jsonify({
            'success': True,
            'message': f'Job {job_name} gestartet',
            'log_file': log_file,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/api/admin/job-log/<job_name>', methods=['GET'])
def get_job_log(job_name):
    """Hole letzte Log-Zeilen eines Jobs"""
    lines = int(request.args.get('lines', 50))
    log_file = f"/opt/greiner-portal/logs/{job_name}.log"
    
    try:
        if os.path.exists(log_file):
            result = subprocess.run(f"tail -n {lines} {log_file}", shell=True, capture_output=True, text=True)
            return jsonify({'log': result.stdout, 'file': log_file, 'lines': lines})
        else:
            return jsonify({'log': 'Log-Datei nicht gefunden', 'file': log_file})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/api/admin/job-history/<job_name>', methods=['GET'])
def get_job_history(job_name):
    """Hole History eines Jobs"""
    limit = int(request.args.get('limit', 20))
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_job_history WHERE job_name = ? ORDER BY run_start DESC LIMIT ?", (job_name, limit))
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/api/admin/health', methods=['GET'])
def admin_health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})
