"""
Admin API - System Status & Job Monitoring
VERSION 2.0 - TAG82 - Mit korrekten Script- und Log-Pfaden
"""
from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime
import subprocess
import os

admin_api = Blueprint('admin_api', __name__)
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'

# =============================================================================
# JOB SCRIPTS - Korrekte Pfade zu den ausführbaren Scripts
# =============================================================================
JOB_SCRIPTS = {
    'verkauf_sync': 'scripts/sync/sync_sales.py',
    'stellantis_fahrzeuge': 'scripts/imports/import_stellantis.py',
    'employee_sync': 'scripts/sync/sync_employees.py',
    'mt940_import': 'scripts/imports/import_mt940.py',
    'santander_import': 'scripts/imports/import_santander_bestand.py',
    'hvb_pdf_import': 'scripts/imports/import_hvb_pdf.py',
    'hyundai_finance': 'scripts/imports/import_hyundai_finance.py',
    'locosoft_stammdaten': 'scripts/sync/sync_fahrzeug_stammdaten.py',
    'umsatz_bereinigung': 'scripts/analysis/umsatz_bereinigung_production.py',
    'servicebox_scraper': 'tools/scrapers/servicebox_detail_scraper_pagination_final.py',
    'servicebox_import': 'scripts/imports/import_stellantis_bestellungen.py',
    'db_backup': 'scripts/maintenance/db_backup.sh',
    'backup_cleanup': 'scripts/maintenance/backup_cleanup.sh',
    'umsatz_vormonat': 'scripts/analysis/umsatz_vormonat_finalisieren.py',
}

# =============================================================================
# LOG FILES - Mapping von job_name zu tatsächlichem Log-Dateinamen
# =============================================================================
LOG_FILES = {
    'verkauf_sync': 'sync_sales.log',
    'stellantis_fahrzeuge': 'stellantis_import.log',
    'employee_sync': 'employee_sync.log',
    'mt940_import': 'mt940_import.log',
    'santander_import': 'santander_import.log',
    'hvb_pdf_import': 'hvb_import.log',
    'hyundai_finance': 'hyundai_import.log',
    'locosoft_stammdaten': 'locosoft_stammdaten.log',
    'umsatz_bereinigung': 'umsatz_bereinigung.log',
    'servicebox_scraper': 'servicebox_scraper.log',
    'servicebox_import': 'servicebox_import.log',
    'db_backup': 'db_backup.log',
    'backup_cleanup': 'backup_cleanup.log',
    'umsatz_vormonat': 'umsatz_vormonat.log',
}

# =============================================================================
# SCRIPT ARGUMENTE - Falls ein Script spezielle Argumente braucht
# =============================================================================
SCRIPT_ARGS = {
    'mt940_import': '/mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/',
    'servicebox_import': 'logs/servicebox_bestellungen_details_complete.json',
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


def get_log_path(job_name):
    """Ermittle den korrekten Log-Pfad für einen Job"""
    log_file = LOG_FILES.get(job_name, f"{job_name}.log")
    return f"/opt/greiner-portal/logs/{log_file}"


def script_exists(job_name):
    """Prüfe ob das Script existiert"""
    if job_name not in JOB_SCRIPTS or JOB_SCRIPTS[job_name] is None:
        return False
    script_path = f"/opt/greiner-portal/{JOB_SCRIPTS[job_name]}"
    return os.path.exists(script_path)


@admin_api.route('/api/admin/system-status', methods=['GET'])
def get_system_status():
    """Hole Status aller System-Jobs"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM system_jobs ORDER BY is_active DESC, job_name")
        jobs = [dict(row) for row in cursor.fetchall()]
        
        for job in jobs:
            job_name = job['job_name']
            
            # Prüfe ob Script existiert und ausführbar ist
            job['can_run'] = job_name in JOB_SCRIPTS and JOB_SCRIPTS[job_name] is not None
            job['script_path'] = JOB_SCRIPTS.get(job_name, None)
            job['log_file'] = LOG_FILES.get(job_name, f"{job_name}.log")
            
            # Prüfe ob Log existiert
            log_path = get_log_path(job_name)
            job['log_exists'] = os.path.exists(log_path)
            
            # Spezifische Live-Counts
            if job_name == 'servicebox_import':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM stellantis_bestellungen")
                job['live_last'] = safe_query(cursor, "SELECT MAX(import_timestamp) FROM stellantis_bestellungen", None)
            elif job_name == 'verkauf_sync':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM sales")
            elif job_name == 'locosoft_stammdaten':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM dealer_vehicles")
            elif job_name == 'stellantis_fahrzeuge':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM dealer_vehicles WHERE hersteller IN ('Opel','Peugeot','Citroen','Fiat','Jeep','Alfa Romeo')")
            elif job_name == 'mt940_import':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM transaktionen")
            elif job_name == 'employee_sync':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM employees")
            elif job_name == 'hyundai_finance':
                job['live_count'] = safe_query(cursor, "SELECT COUNT(*) FROM fahrzeugfinanzierungen WHERE bank LIKE '%yundai%'")
            elif job_name == 'santander_import':
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
    
    script = JOB_SCRIPTS[job_name]
    script_path = f"/opt/greiner-portal/{script}"
    
    # Prüfe ob Script existiert
    if not os.path.exists(script_path):
        return jsonify({'error': f'Script nicht gefunden: {script}'}), 404
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Status auf "running" setzen
        cursor.execute("""
            UPDATE system_jobs 
            SET last_status = 'running', last_run = ?, updated_at = ?
            WHERE job_name = ?
        """, (datetime.now().isoformat(), datetime.now().isoformat(), job_name))
        conn.commit()
        
        # History-Eintrag
        cursor.execute("""
            INSERT INTO system_job_history (job_name, run_start, status, message)
            VALUES (?, ?, 'running', 'Manuell gestartet')
        """, (job_name, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        # Script starten
        log_file = get_log_path(job_name)
        args = SCRIPT_ARGS.get(job_name, '')
        
        # Shell oder Python je nach Dateiendung
        if script.endswith('.sh'):
            cmd = f"cd /opt/greiner-portal && bash {script} >> {log_file} 2>&1 &"
        else:
            cmd = f"cd /opt/greiner-portal && venv/bin/python3 {script} {args} >> {log_file} 2>&1 &"
        
        subprocess.Popen(cmd, shell=True)
        
        return jsonify({
            'success': True,
            'message': f'Job {job_name} gestartet',
            'script': script,
            'log_file': log_file,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/job-log/<job_name>', methods=['GET'])
def get_job_log(job_name):
    """Hole letzte Log-Zeilen eines Jobs"""
    lines = int(request.args.get('lines', 100))
    log_path = get_log_path(job_name)
    
    try:
        if os.path.exists(log_path):
            result = subprocess.run(
                f"tail -n {lines} '{log_path}'", 
                shell=True, 
                capture_output=True, 
                text=True
            )
            
            # Auch Dateigröße und letztes Update holen
            stat = os.stat(log_path)
            
            return jsonify({
                'log': result.stdout,
                'file': log_path,
                'lines': lines,
                'size_kb': round(stat.st_size / 1024, 1),
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        else:
            # Versuche alternative Log-Namen
            alt_logs = [
                f"/opt/greiner-portal/logs/{job_name}.log",
                f"/opt/greiner-portal/logs/{job_name.replace('_', '-')}.log",
            ]
            for alt in alt_logs:
                if os.path.exists(alt):
                    result = subprocess.run(f"tail -n {lines} '{alt}'", shell=True, capture_output=True, text=True)
                    return jsonify({'log': result.stdout, 'file': alt, 'lines': lines})
            
            return jsonify({
                'error': 'Log-Datei nicht gefunden',
                'searched': [log_path] + alt_logs
            }), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/job-history/<job_name>', methods=['GET'])
def get_job_history(job_name):
    """Hole History eines Jobs"""
    limit = int(request.args.get('limit', 20))
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM system_job_history 
            WHERE job_name = ? 
            ORDER BY run_start DESC 
            LIMIT ?
        """, (job_name, limit))
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_api.route('/api/admin/logs', methods=['GET'])
def list_logs():
    """Liste alle verfügbaren Log-Dateien"""
    log_dir = '/opt/greiner-portal/logs'
    try:
        logs = []
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
    return jsonify({
        'status': 'ok', 
        'version': '2.0-tag82',
        'timestamp': datetime.now().isoformat()
    })
