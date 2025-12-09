"""
Job Scheduler Manager
=====================
Zentrales Job-Management für DRIVE mit APScheduler.
Ersetzt Cron-Jobs mit Web-UI und Logging.

Erstellt: 2025-12-02
"""

import os
import sys
import logging
import subprocess
from datetime import datetime, timedelta
from functools import wraps
import sqlite3
import json
import traceback
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('job_scheduler')

# Pfade
BASE_DIR = '/opt/greiner-portal'
JOBS_DB = os.path.join(BASE_DIR, 'data', 'scheduler_jobs.db')
LOGS_DB = os.path.join(BASE_DIR, 'data', 'scheduler_logs.db')

# Timezone
LOCAL_TZ = ZoneInfo('Europe/Berlin')
UTC_TZ = ZoneInfo('UTC')


def utc_to_local(utc_str):
    """Konvertiert UTC-Zeitstring zu lokaler Zeit."""
    if not utc_str:
        return None
    try:
        # SQLite CURRENT_TIMESTAMP format: 'YYYY-MM-DD HH:MM:SS'
        utc_dt = datetime.strptime(utc_str, '%Y-%m-%d %H:%M:%S')
        utc_dt = utc_dt.replace(tzinfo=UTC_TZ)
        local_dt = utc_dt.astimezone(LOCAL_TZ)
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return utc_str  # Bei Fehler Original zurückgeben


def init_logs_db():
    """Erstellt die Log-Datenbank für Job-History."""
    conn = sqlite3.connect(LOGS_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            job_name TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            duration_seconds REAL,
            status TEXT DEFAULT 'running',
            result TEXT,
            error_message TEXT,
            triggered_by TEXT DEFAULT 'scheduler'
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_job_runs_job_id 
        ON job_runs(job_id, started_at DESC)
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_definitions (
            job_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'allgemein',
            script_path TEXT,
            cron_expression TEXT,
            interval_minutes INTEGER,
            is_active INTEGER DEFAULT 1,
            last_run TIMESTAMP,
            last_status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            run_on_startup INTEGER DEFAULT 0,
            timeout_seconds INTEGER DEFAULT 300,
            notify_on_error INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()


def log_job_start(job_id, job_name, triggered_by='scheduler'):
    """Loggt den Start eines Jobs."""
    conn = sqlite3.connect(LOGS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO job_runs (job_id, job_name, triggered_by, status)
        VALUES (?, ?, ?, 'running')
    ''', (job_id, job_name, triggered_by))
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def log_job_end(run_id, status, result=None, error_message=None):
    """Loggt das Ende eines Jobs."""
    conn = sqlite3.connect(LOGS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE job_runs 
        SET finished_at = CURRENT_TIMESTAMP,
            duration_seconds = (julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400,
            status = ?,
            result = ?,
            error_message = ?
        WHERE id = ?
    ''', (status, result, error_message, run_id))
    conn.commit()
    conn.close()


def update_job_status(job_id, status, last_run=None):
    """Aktualisiert den Status in job_definitions."""
    conn = sqlite3.connect(LOGS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE job_definitions 
        SET last_status = ?, last_run = COALESCE(?, CURRENT_TIMESTAMP)
        WHERE job_id = ?
    ''', (status, last_run, job_id))
    conn.commit()
    conn.close()


def run_script(script_path, job_id, job_name, timeout=300, args=None):
    """Führt ein Python-Script aus mit Logging.
    
    Args:
        script_path: Pfad zum Script (relativ zu BASE_DIR oder absolut)
        job_id: Eindeutige Job-ID
        job_name: Anzeigename des Jobs
        timeout: Timeout in Sekunden
        args: Liste von Argumenten für das Script
    """
    # Script-Pfad und Argumente trennen (falls im Pfad enthalten)
    parts = script_path.split()
    actual_script = parts[0]
    inline_args = parts[1:] if len(parts) > 1 else []
    
    full_path = os.path.join(BASE_DIR, actual_script) if not actual_script.startswith('/') else actual_script
    
    # Argumente zusammenführen
    all_args = inline_args + (args if args else [])
    
    logger.info(f"[{job_id}] Starting: {job_name}")
    run_id = log_job_start(job_id, job_name)
    
    try:
        # Python aus venv verwenden
        python_path = os.path.join(BASE_DIR, 'venv', 'bin', 'python3')
        
        # Command zusammenbauen
        cmd = [python_path, full_path] + all_args
        logger.debug(f"[{job_id}] Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            log_job_end(run_id, 'success', result.stdout[:5000])
            update_job_status(job_id, 'success')
            logger.info(f"[{job_id}] Completed successfully")
            return True
        else:
            error_msg = result.stderr[:2000] if result.stderr else f"Exit code: {result.returncode}"
            log_job_end(run_id, 'error', result.stdout[:2000], error_msg)
            update_job_status(job_id, 'error')
            logger.error(f"[{job_id}] Failed: {error_msg}")
            return False
            
    except subprocess.TimeoutExpired:
        log_job_end(run_id, 'timeout', None, f"Timeout nach {timeout}s")
        update_job_status(job_id, 'timeout')
        logger.error(f"[{job_id}] Timeout after {timeout}s")
        return False
        
    except Exception as e:
        log_job_end(run_id, 'error', None, str(e))
        update_job_status(job_id, 'error')
        logger.error(f"[{job_id}] Exception: {e}")
        return False


def run_shell(command, job_id, job_name, timeout=300):
    """Führt einen Shell-Befehl aus mit Logging."""
    logger.info(f"[{job_id}] Starting: {job_name}")
    run_id = log_job_start(job_id, job_name)
    
    # Vollständige PATH-Umgebung für Shell-Befehle
    env = os.environ.copy()
    env['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:' + env.get('PATH', '')
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        
        if result.returncode == 0:
            log_job_end(run_id, 'success', result.stdout[:5000])
            update_job_status(job_id, 'success')
            logger.info(f"[{job_id}] Completed successfully")
            return True
        else:
            error_msg = result.stderr[:2000] if result.stderr else f"Exit code: {result.returncode}"
            log_job_end(run_id, 'error', result.stdout[:2000], error_msg)
            update_job_status(job_id, 'error')
            logger.error(f"[{job_id}] Failed: {error_msg}")
            return False
            
    except subprocess.TimeoutExpired:
        log_job_end(run_id, 'timeout', None, f"Timeout nach {timeout}s")
        update_job_status(job_id, 'timeout')
        logger.error(f"[{job_id}] Timeout after {timeout}s")
        return False
        
    except Exception as e:
        log_job_end(run_id, 'error', None, str(e))
        update_job_status(job_id, 'error')
        logger.error(f"[{job_id}] Exception: {e}")
        return False


class JobSchedulerManager:
    """Zentraler Job-Scheduler für DRIVE."""
    
    _instance = None
    _scheduler = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._scheduler is not None:
            return
            
        init_logs_db()
        
        # Scheduler konfigurieren
        jobstores = {
            'default': SQLAlchemyJobStore(url=f'sqlite:///{JOBS_DB}')
        }
        executors = {
            'default': ThreadPoolExecutor(max_workers=5)
        }
        job_defaults = {
            'coalesce': True,  # Verpasste Jobs zusammenfassen
            'max_instances': 1,  # Nur eine Instanz gleichzeitig
            'misfire_grace_time': 300  # 5 Min Toleranz
        }
        
        self._scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Europe/Berlin'
        )
        
        # Event-Listener
        self._scheduler.add_listener(self._job_event_listener, 
                                      EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    
    def _job_event_listener(self, event):
        """Listener für Job-Events."""
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {event.exception}")
        elif hasattr(event, 'job_id'):
            logger.debug(f"Job {event.job_id} executed")
    
    def start(self):
        """Startet den Scheduler."""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Job Scheduler gestartet")
    
    def shutdown(self):
        """Stoppt den Scheduler."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Job Scheduler gestoppt")
    
    def add_cron_job(self, job_id, func, name, description='', category='allgemein',
                     hour='*', minute='0', day_of_week='*', **kwargs):
        """Fügt einen Cron-Job hinzu."""
        
        # In DB registrieren
        cron_expr = f"{minute} {hour} * * {day_of_week}"
        self._register_job(job_id, name, description, category, cron_expr, None, kwargs.get('script_path'))
        
        # Im Scheduler registrieren
        self._scheduler.add_job(
            func,
            'cron',
            id=job_id,
            name=name,
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
            replace_existing=True,
            **kwargs
        )
        logger.info(f"Cron-Job registriert: {job_id} ({cron_expr})")
    
    def add_interval_job(self, job_id, func, name, description='', category='allgemein',
                         minutes=60, **kwargs):
        """Fügt einen Interval-Job hinzu."""
        
        # In DB registrieren
        self._register_job(job_id, name, description, category, None, minutes, kwargs.get('script_path'))
        
        # Im Scheduler registrieren
        self._scheduler.add_job(
            func,
            'interval',
            id=job_id,
            name=name,
            minutes=minutes,
            replace_existing=True,
            **kwargs
        )
        logger.info(f"Interval-Job registriert: {job_id} (alle {minutes} Min)")
    
    def _register_job(self, job_id, name, description, category, cron_expr, interval_min, script_path):
        """Registriert Job in der Definitions-Tabelle."""
        conn = sqlite3.connect(LOGS_DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO job_definitions 
            (job_id, name, description, category, script_path, cron_expression, interval_minutes, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (job_id, name, description, category, script_path, cron_expr, interval_min))
        conn.commit()
        conn.close()
    
    def run_job_now(self, job_id, triggered_by='manual'):
        """Führt einen Job sofort aus."""
        job = self._scheduler.get_job(job_id)
        if job:
            logger.info(f"Manueller Start: {job_id} von {triggered_by}")
            # Job-Funktion direkt aufrufen
            try:
                job.func(*job.args, **job.kwargs)
                return True, "Job erfolgreich gestartet"
            except Exception as e:
                return False, str(e)
        return False, f"Job {job_id} nicht gefunden"
    
    def get_jobs(self):
        """Gibt alle registrierten Jobs zurück."""
        conn = sqlite3.connect(LOGS_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM job_definitions ORDER BY category, name
        ''')
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Zeiten konvertieren und nächste Ausführung hinzufügen
        for job in jobs:
            # UTC zu lokaler Zeit konvertieren
            if job.get('last_run'):
                job['last_run'] = utc_to_local(job['last_run'])
            
            try:
                scheduler_job = self._scheduler.get_job(job['job_id'])
                if scheduler_job:
                    # APScheduler 3.x: next_run_time, APScheduler 4.x: next_fire_time
                    next_run = getattr(scheduler_job, 'next_run_time', None) or \
                               getattr(scheduler_job, 'next_fire_time', None)
                    if next_run:
                        # APScheduler gibt bereits timezone-aware datetime zurück
                        job['next_run'] = next_run.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        job['next_run'] = None
                else:
                    job['next_run'] = None
            except Exception:
                job['next_run'] = None
        
        return jobs
    
    def get_job_history(self, job_id=None, limit=50):
        """Gibt die Job-History zurück."""
        conn = sqlite3.connect(LOGS_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if job_id:
            cursor.execute('''
                SELECT * FROM job_runs 
                WHERE job_id = ?
                ORDER BY started_at DESC LIMIT ?
            ''', (job_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM job_runs 
                ORDER BY started_at DESC LIMIT ?
            ''', (limit,))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # UTC zu lokaler Zeit konvertieren
        for entry in history:
            if entry.get('started_at'):
                entry['started_at'] = utc_to_local(entry['started_at'])
            if entry.get('finished_at'):
                entry['finished_at'] = utc_to_local(entry['finished_at'])
        
        return history
    
    def pause_job(self, job_id):
        """Pausiert einen Job."""
        self._scheduler.pause_job(job_id)
        conn = sqlite3.connect(LOGS_DB)
        cursor = conn.cursor()
        cursor.execute('UPDATE job_definitions SET is_active = 0 WHERE job_id = ?', (job_id,))
        conn.commit()
        conn.close()
        logger.info(f"Job pausiert: {job_id}")
    
    def resume_job(self, job_id):
        """Reaktiviert einen Job."""
        self._scheduler.resume_job(job_id)
        conn = sqlite3.connect(LOGS_DB)
        cursor = conn.cursor()
        cursor.execute('UPDATE job_definitions SET is_active = 1 WHERE job_id = ?', (job_id,))
        conn.commit()
        conn.close()
        logger.info(f"Job reaktiviert: {job_id}")
    
    def get_scheduler(self):
        """Gibt den APScheduler zurück."""
        return self._scheduler


# Singleton-Instanz
job_manager = JobSchedulerManager()
