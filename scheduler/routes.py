"""
Job Scheduler API & Routes
==========================
Web-UI und API-Endpoints für Job-Management.

WICHTIG: Der eigentliche Scheduler läuft als separater Service (greiner-scheduler).
Diese Routes dienen nur der Web-UI und dem manuellen Job-Start.

Erstellt: 2025-12-02
Aktualisiert: 2025-12-04 - Separater Scheduler-Service
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from datetime import datetime
import sqlite3
import subprocess
import threading
import os

scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/admin/jobs')

BASE_DIR = '/opt/greiner-portal'
LOGS_DB = os.path.join(BASE_DIR, 'data', 'scheduler_logs.db')

# Job-Manager wird für DB-Zugriff verwendet (nicht für Scheduler!)
job_manager = None

def init_scheduler_routes(jm):
    """Initialisiert die Routes mit dem Job-Manager."""
    global job_manager
    job_manager = jm


def get_db():
    """Verbindung zur Logs-DB."""
    conn = sqlite3.connect(LOGS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_jobs_from_db():
    """Holt alle Job-Definitionen aus der DB."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM job_definitions ORDER BY category, name')
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jobs
    except:
        return []


def get_history_from_db(job_id=None, limit=50):
    """Holt Job-History aus der DB."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        if job_id:
            cursor.execute('''
                SELECT * FROM job_runs WHERE job_id = ? 
                ORDER BY started_at DESC LIMIT ?
            ''', (job_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM job_runs ORDER BY started_at DESC LIMIT ?
            ''', (limit,))
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history
    except:
        return []


# =============================================================================
# JOB-FUNKTIONEN FÜR MANUELLEN START
# =============================================================================
# Diese Funktionen werden bei manuellem Start über die Web-UI ausgeführt

from scheduler.job_manager import run_script, run_shell

JOB_FUNCTIONS = {
    # Bank & Finanzen
    'import_mt940_08': lambda: run_script('scripts/imports/import_mt940.py', 'import_mt940', 'MT940 Import', 120, 
                                          args=['/mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/']),
    'import_mt940_12': lambda: run_script('scripts/imports/import_mt940.py', 'import_mt940', 'MT940 Import', 120,
                                          args=['/mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/']),
    'import_mt940_17': lambda: run_script('scripts/imports/import_mt940.py', 'import_mt940', 'MT940 Import', 120,
                                          args=['/mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/']),
    'import_hvb_pdf': lambda: run_script('scripts/imports/import_all_bank_pdfs.py', 'import_hvb_pdf', 
                                         'HypoVereinsbank PDF Import', 120, args=['--bank', 'hvb', '--days', '3']),
    'umsatz_bereinigung': lambda: run_script('scripts/analysis/umsatz_bereinigung_production.py', 
                                             'umsatz_bereinigung', 'Umsatz-Bereinigung', 300),
    'import_santander': lambda: run_script('scripts/imports/import_santander_bestand.py', 
                                           'import_santander', 'Santander Import'),
    'import_hyundai': lambda: run_script('scripts/imports/import_hyundai_finance.py', 
                                         'import_hyundai', 'Hyundai Finance Import'),
    'scrape_hyundai': lambda: run_script('tools/scrapers/hyundai_bestandsliste_scraper.py', 
                                         'scrape_hyundai', 'Hyundai Scraper', 180),
    'leasys_cache_refresh': lambda: run_script('scripts/update_leasys_cache.py', 
                                               'leasys_cache_refresh', 'Leasys Cache Refresh', 600),
    
    # HR & Wartung
    'sync_employees': lambda: run_shell('venv/bin/python3 scripts/sync/sync_employees.py --real', 
                                        'sync_employees', 'Mitarbeiter Sync'),
    'email_auftragseingang': lambda: run_script('scripts/send_daily_auftragseingang.py', 
                                                'email_auftragseingang', 'Auftragseingang E-Mail'),
    'db_backup': lambda: run_shell('cp data/greiner_controlling.db data/greiner_controlling.db.backup_$(date +%Y%m%d_%H%M%S)', 
                                   'db_backup', 'DB Backup'),
    'cleanup_backups': lambda: run_shell('cd data && ls -t greiner_controlling.db.backup_* 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null', 
                                         'cleanup_backups', 'Backup Cleanup'),
    
    # ServiceBox
    'servicebox_scraper_09': lambda: run_script('tools/scrapers/servicebox_detail_scraper_v3_kommentar.py', 
                                                'servicebox_scraper', 'ServiceBox Scraper', 1800),
    'servicebox_scraper_12': lambda: run_script('tools/scrapers/servicebox_detail_scraper_v3_kommentar.py', 
                                                'servicebox_scraper', 'ServiceBox Scraper', 1800),
    'servicebox_scraper_16': lambda: run_script('tools/scrapers/servicebox_detail_scraper_v3_kommentar.py', 
                                                'servicebox_scraper', 'ServiceBox Scraper', 1800),
    'servicebox_matcher_10': lambda: run_script('tools/scrapers/servicebox_locosoft_matcher.py', 
                                                'servicebox_matcher', 'ServiceBox Matcher', 300),
    'servicebox_matcher_13': lambda: run_script('tools/scrapers/servicebox_locosoft_matcher.py', 
                                                'servicebox_matcher', 'ServiceBox Matcher', 300),
    'servicebox_matcher_17': lambda: run_script('tools/scrapers/servicebox_locosoft_matcher.py', 
                                                'servicebox_matcher', 'ServiceBox Matcher', 300),
    'servicebox_import_10': lambda: run_script('scripts/imports/import_servicebox_to_db.py', 
                                               'servicebox_import', 'ServiceBox Import', 120),
    'servicebox_import_13': lambda: run_script('scripts/imports/import_servicebox_to_db.py', 
                                               'servicebox_import', 'ServiceBox Import', 120),
    'servicebox_import_17': lambda: run_script('scripts/imports/import_servicebox_to_db.py', 
                                               'servicebox_import', 'ServiceBox Import', 120),
    'servicebox_master': lambda: run_script('tools/scrapers/servicebox_detail_scraper_v3_master.py', 
                                            'servicebox_master', 'ServiceBox Master', 3600),
    
    # Teile
    'sync_teile_locosoft': lambda: run_script('scripts/imports/sync_teile_locosoft.py', 
                                              'sync_teile_locosoft', 'Teile-Locosoft Sync'),
    'import_teile_lieferscheine': lambda: run_script('scripts/imports/import_teile_lieferscheine.py', 
                                                     'import_teile_lieferscheine', 'Teile-Lieferscheine Import'),
    
    # Verkauf
    'sync_sales': lambda: run_script('scripts/sync/sync_sales.py', 'sync_sales', 'Verkauf Sync'),
    'import_stellantis': lambda: run_script('scripts/sync/import_stellantis.py', 'import_stellantis', 'Stellantis Import'),
    'sync_stammdaten': lambda: run_script('scripts/sync/sync_fahrzeug_stammdaten.py', 'sync_stammdaten', 'Stammdaten Sync'),
    'locosoft_mirror': lambda: run_shell('venv/bin/python3 scripts/sync/locosoft_mirror.py --min-rows 100', 
                                         'locosoft_mirror', 'Locosoft Mirror', 600),
    'bwa_berechnung': lambda: run_script('scripts/sync/bwa_berechnung.py', 'bwa_berechnung', 'BWA Berechnung', 120),
}


def run_job_in_background(job_id, user='web'):
    """Führt einen Job im Hintergrund aus."""
    if job_id not in JOB_FUNCTIONS:
        return False, f"Job {job_id} nicht gefunden"
    
    def execute():
        try:
            JOB_FUNCTIONS[job_id]()
        except Exception as e:
            print(f"Job {job_id} Fehler: {e}")
    
    thread = threading.Thread(target=execute, daemon=True)
    thread.start()
    return True, f"Job {job_id} gestartet"


# =============================================================================
# ROUTES
# =============================================================================

@scheduler_bp.route('/')
def job_overview():
    """Übersicht aller Jobs."""
    jobs = get_jobs_from_db()
    history = get_history_from_db(limit=20)
    
    # Jobs nach Kategorie gruppieren
    categories = {}
    for job in jobs:
        cat = job.get('category', 'allgemein')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(job)
    
    # Statistiken
    today = datetime.now().strftime('%Y-%m-%d')
    stats = {
        'total': len(jobs),
        'active': len([j for j in jobs if j.get('is_active')]),
        'success_today': len([h for h in history if h.get('status') == 'success' 
                              and h.get('started_at', '').startswith(today)]),
        'errors_today': len([h for h in history if h.get('status') == 'error'
                             and h.get('started_at', '').startswith(today)])
    }
    
    return render_template('admin/jobs.html', 
                          categories=categories, 
                          history=history,
                          stats=stats)


@scheduler_bp.route('/run/<job_id>', methods=['POST'])
def run_job(job_id):
    """Führt einen Job manuell aus."""
    user = request.args.get('user', 'web')
    success, message = run_job_in_background(job_id, user)
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'success': success, 'message': message})
    
    flash(f'Job "{job_id}" gestartet' if success else f'Fehler: {message}', 
          'success' if success else 'danger')
    return redirect(url_for('scheduler.job_overview'))


@scheduler_bp.route('/pause/<job_id>', methods=['POST'])
def pause_job(job_id):
    """Pausiert einen Job (setzt is_active=0 in DB)."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE job_definitions SET is_active = 0 WHERE job_id = ?', (job_id,))
        conn.commit()
        conn.close()
        message = f'Job {job_id} pausiert'
        success = True
    except Exception as e:
        message = str(e)
        success = False
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'success': success, 'message': message})
    
    flash(message, 'warning' if success else 'danger')
    return redirect(url_for('scheduler.job_overview'))


@scheduler_bp.route('/resume/<job_id>', methods=['POST'])
def resume_job(job_id):
    """Reaktiviert einen Job (setzt is_active=1 in DB)."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE job_definitions SET is_active = 1 WHERE job_id = ?', (job_id,))
        conn.commit()
        conn.close()
        message = f'Job {job_id} reaktiviert'
        success = True
    except Exception as e:
        message = str(e)
        success = False
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'success': success, 'message': message})
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('scheduler.job_overview'))


@scheduler_bp.route('/history')
def job_history():
    """Zeigt die komplette Job-History."""
    job_id = request.args.get('job_id')
    limit = request.args.get('limit', 100, type=int)
    
    history = get_history_from_db(job_id=job_id, limit=limit)
    jobs = get_jobs_from_db()
    
    return render_template('admin/job_history.html', 
                          history=history,
                          jobs=jobs,
                          selected_job=job_id)


@scheduler_bp.route('/api/jobs')
def api_jobs():
    """API: Alle Jobs."""
    jobs = get_jobs_from_db()
    return jsonify(jobs)


@scheduler_bp.route('/api/history')
def api_history():
    """API: Job-History."""
    job_id = request.args.get('job_id')
    limit = request.args.get('limit', 50, type=int)
    history = get_history_from_db(job_id=job_id, limit=limit)
    return jsonify(history)


@scheduler_bp.route('/api/status')
def api_status():
    """API: Scheduler-Status (prüft ob Service läuft)."""
    import subprocess
    try:
        result = subprocess.run(['systemctl', 'is-active', 'greiner-scheduler'], 
                               capture_output=True, text=True, timeout=5)
        running = result.stdout.strip() == 'active'
    except:
        running = False
    
    jobs = get_jobs_from_db()
    return jsonify({
        'running': running,
        'service': 'greiner-scheduler',
        'job_count': len(jobs),
        'timestamp': datetime.now().isoformat()
    })
