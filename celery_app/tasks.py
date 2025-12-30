"""
GREINER DRIVE - Celery Tasks
=============================
Alle Jobs als Celery Tasks mit Retry-Logik und Timeouts.

Erstellt: 2025-12-09 (TAG 110)
Aktualisiert: TAG 117 - Task-Locking gegen Race Conditions
"""

import os
import sys
import subprocess
import logging
import fcntl
from datetime import datetime
from contextlib import contextmanager

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

# Logging
logger = logging.getLogger('celery_tasks')

# Basis-Pfad
BASE_DIR = '/opt/greiner-portal'
VENV_PYTHON = os.path.join(BASE_DIR, 'venv', 'bin', 'python3')
LOCK_DIR = '/tmp/greiner_task_locks'

# Lock-Verzeichnis erstellen
os.makedirs(LOCK_DIR, exist_ok=True)


# =============================================================================
# TASK LOCKING - Verhindert parallele Ausführung desselben Tasks
# =============================================================================

@contextmanager
def task_lock(task_name: str, blocking: bool = False):
    """
    File-basiertes Locking für Tasks.

    Verhindert dass derselbe Task mehrfach parallel läuft.

    Args:
        task_name: Name des Tasks (wird zu Dateiname)
        blocking: True = warten auf Lock, False = sofort abbrechen wenn gesperrt

    Usage:
        with task_lock('import_mt940') as acquired:
            if not acquired:
                return {'status': 'skipped', 'reason': 'already running'}
            # Task ausführen...

    Yields:
        bool: True wenn Lock erhalten, False wenn bereits gesperrt (nur bei blocking=False)
    """
    lock_file = os.path.join(LOCK_DIR, f'{task_name}.lock')
    lock_fd = None
    acquired = False

    try:
        lock_fd = open(lock_file, 'w')

        # Lock-Modus: LOCK_NB = non-blocking (sofort Fehler wenn gesperrt)
        lock_mode = fcntl.LOCK_EX if blocking else (fcntl.LOCK_EX | fcntl.LOCK_NB)

        try:
            fcntl.flock(lock_fd, lock_mode)
            acquired = True
            # PID in Lock-File schreiben für Debugging
            lock_fd.write(f'{os.getpid()}\n{datetime.now().isoformat()}\n{task_name}')
            lock_fd.flush()
        except IOError:
            # Lock nicht erhalten (Task läuft bereits)
            acquired = False
            logger.warning(f"Task {task_name} läuft bereits - überspringe")

        yield acquired

    finally:
        if lock_fd:
            if acquired:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                except:
                    pass
            lock_fd.close()


def run_script(script_path: str, timeout: int = 300) -> dict:
    """
    Führt ein Python-Script aus und gibt Ergebnis zurück.
    
    Args:
        script_path: Relativer Pfad zum Script
        timeout: Timeout in Sekunden
    
    Returns:
        dict mit status, output, error, duration
    """
    full_path = os.path.join(BASE_DIR, script_path)
    start_time = datetime.now()
    
    logger.info(f"Starting: {script_path}")
    
    try:
        result = subprocess.run(
            [VENV_PYTHON, full_path],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, 'PYTHONPATH': BASE_DIR}
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            logger.info(f"Success: {script_path} ({duration:.1f}s)")
            return {
                'status': 'success',
                'output': result.stdout[-5000:] if result.stdout else '',  # Letzte 5000 Zeichen
                'duration': duration
            }
        else:
            logger.error(f"Failed: {script_path} - {result.stderr[:500]}")
            return {
                'status': 'error',
                'output': result.stdout[-2000:] if result.stdout else '',
                'error': result.stderr[-2000:] if result.stderr else '',
                'duration': duration
            }
            
    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Timeout: {script_path} after {timeout}s")
        return {
            'status': 'timeout',
            'error': f'Timeout nach {timeout}s',
            'duration': duration
        }
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Exception: {script_path} - {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'duration': duration
        }


def run_shell(command: str, timeout: int = 300) -> dict:
    """
    Führt einen Shell-Befehl aus.
    """
    start_time = datetime.now()
    logger.info(f"Running shell: {command[:50]}...")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, 'PATH': f"{BASE_DIR}/venv/bin:{os.environ.get('PATH', '')}"}
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            'status': 'success' if result.returncode == 0 else 'error',
            'output': result.stdout[-2000:] if result.stdout else '',
            'error': result.stderr[-2000:] if result.stderr else '',
            'duration': duration
        }
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'error': f'Timeout nach {timeout}s'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


# =============================================================================
# CONTROLLING & VERWALTUNG
# =============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=120, soft_time_limit=300)
def import_mt940(self):
    """MT940 Import für alle Banken außer HypoVereinsbank"""
    with task_lock('import_mt940') as acquired:
        if not acquired:
            return {'status': 'skipped', 'reason': 'Task läuft bereits'}

        try:
            mt940_dir = '/mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/'
            result = subprocess.run(
                [VENV_PYTHON, 'scripts/imports/import_mt940.py', mt940_dir],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                raise Exception(result.stderr[:500])
            return {'status': 'success', 'output': result.stdout[-1000:]}
        except Exception as exc:
            if 'Host is down' in str(exc):
                # Netzwerk-Fehler → Retry
                raise self.retry(exc=exc)
            raise


@shared_task(bind=True, max_retries=2, soft_time_limit=180)
def import_hvb_pdf(self):
    """HypoVereinsbank PDF Import"""
    return run_script('scripts/imports/import_all_bank_pdfs.py', timeout=120)


@shared_task(soft_time_limit=600)
def umsatz_bereinigung():
    """Umsatz-Bereinigung"""
    return run_script('scripts/analysis/umsatz_bereinigung_production.py', timeout=300)


@shared_task(bind=True, max_retries=2, soft_time_limit=180)
def import_santander(self):
    """Santander Bestand Import"""
    return run_script('scripts/imports/import_santander_bestand.py', timeout=120)


@shared_task(soft_time_limit=300)
def scrape_hyundai():
    """Hyundai Finance Scraper"""
    # TAG 144: Pfad korrigiert von tools/scrapers nach scripts/scrapers
    return run_script('scripts/scrapers/scrape_hyundai.py', timeout=180)


@shared_task(bind=True, max_retries=2, soft_time_limit=180)
def import_hyundai(self):
    """Hyundai Finance CSV Import"""
    return run_script('scripts/imports/import_hyundai_finance.py', timeout=120)


@shared_task(bind=True, max_retries=2, soft_time_limit=900)
def leasys_cache_refresh(self):
    """Leasys Cache aktualisieren"""
    return run_script('scripts/update_leasys_cache.py', timeout=600)


@shared_task(soft_time_limit=300)
def sync_employees():
    """Mitarbeiter Sync aus Locosoft"""
    return run_shell('venv/bin/python3 scripts/sync/sync_employees.py --real', timeout=120)


@shared_task(soft_time_limit=300)
def sync_locosoft_employees():
    """Locosoft Employee Mapping für Urlaubsplaner"""
    return run_script('scripts/sync_locosoft_employees.py', timeout=120)


@shared_task(soft_time_limit=300)
def email_auftragseingang():
    """Täglicher Auftragseingang-Report per E-Mail"""
    return run_script('scripts/send_daily_auftragseingang.py', timeout=120)


@shared_task(soft_time_limit=300)
def email_werkstatt_tagesbericht():
    """Werkstatt Tagesbericht per E-Mail"""
    return run_script('scripts/reports/werkstatt_tagesbericht_email.py', timeout=120)


@shared_task(soft_time_limit=180)
def db_backup():
    """PostgreSQL Datenbank Backup (pg_dump)"""
    return run_shell(
        'PGPASSWORD=DrivePortal2024 pg_dump -h 127.0.0.1 -U drive_user -d drive_portal '
        '-Fc -f /data/greiner-backups/drive_portal_$(date +%Y%m%d_%H%M%S).dump',
        timeout=120
    )


@shared_task(soft_time_limit=60)
def cleanup_backups():
    """Alte Backups loeschen (behalte letzte 7)"""
    return run_shell(
        'cd /data/greiner-backups && ls -t drive_portal_*.dump 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null',
        timeout=30
    )


@shared_task(soft_time_limit=900)
def ml_retrain():
    """ML Modell neu trainieren"""
    return run_script('scripts/ml/train_auftragsdauer_model.py', timeout=600)


@shared_task(soft_time_limit=300)
def sync_charge_types():
    """Charge Types (AW-Preise) synchronisieren"""
    return run_script('scripts/imports/sync_charge_types.py', timeout=120)


# =============================================================================
# AFTERSALES
# =============================================================================

@shared_task(bind=True, max_retries=2, soft_time_limit=2100)
def servicebox_scraper(self):
    """ServiceBox Bestellungen scrapen"""
    with task_lock('servicebox_scraper') as acquired:
        if not acquired:
            return {'status': 'skipped', 'reason': 'Task läuft bereits'}
        # TAG 144: Pfad korrigiert
        return run_script('scripts/scrapers/scrape_servicebox.py', timeout=1800)


@shared_task(soft_time_limit=600)
def servicebox_matcher():
    """ServiceBox mit Locosoft matchen"""
    # TAG 144: Pfad korrigiert
    return run_script('scripts/scrapers/match_servicebox.py', timeout=300)


@shared_task(soft_time_limit=300)
def servicebox_import():
    """ServiceBox Daten in DB importieren"""
    return run_script('scripts/imports/import_servicebox_to_db.py', timeout=120)


@shared_task(soft_time_limit=4200)
def servicebox_master():
    """ServiceBox komplett neu laden"""
    # TAG 144: Pfad korrigiert
    return run_script('scripts/scrapers/scrape_servicebox_full.py', timeout=3600)


@shared_task(soft_time_limit=300)
def sync_teile():
    """Teile mit Locosoft synchronisieren"""
    return run_script('scripts/imports/sync_teile_locosoft.py', timeout=180)


@shared_task(soft_time_limit=300)
def import_teile():
    """Teile-Lieferscheine importieren"""
    return run_script('scripts/imports/import_teile_lieferscheine.py', timeout=180)


# =============================================================================
# VERKAUF
# =============================================================================

@shared_task(soft_time_limit=300)
def sync_sales():
    """Verkaufsdaten synchronisieren"""
    return run_script('scripts/sync/sync_sales.py', timeout=180)


@shared_task(bind=True, max_retries=2, soft_time_limit=600)
def import_stellantis(self):
    """Stellantis Fahrzeugdaten importieren"""
    return run_script('scripts/imports/import_stellantis.py', timeout=300)


@shared_task(soft_time_limit=300)
def sync_stammdaten():
    """Fahrzeug-Stammdaten synchronisieren"""
    return run_script('scripts/sync/sync_fahrzeug_stammdaten.py', timeout=180)


@shared_task(bind=True, max_retries=1, soft_time_limit=900)
def locosoft_mirror(self):
    """Locosoft Mirror (inkl. VIEWs times, employees)"""
    with task_lock('locosoft_mirror') as acquired:
        if not acquired:
            return {'status': 'skipped', 'reason': 'Task läuft bereits'}
        return run_shell('venv/bin/python3 scripts/sync/locosoft_mirror.py --min-rows 100', timeout=600)


@shared_task(soft_time_limit=300)
def bwa_berechnung():
    """BWA aus Locosoft-Daten berechnen"""
    return run_script('scripts/sync/bwa_berechnung.py', timeout=120)


@shared_task(soft_time_limit=600)
def werkstatt_leistung():
    """Werkstatt-Leistungsgrade berechnen"""
    return run_script('scripts/sync/sync_werkstatt_zeiten.py', timeout=300)


# =============================================================================
# HR / URLAUBSPLANER - TAG 113
# =============================================================================

@shared_task(soft_time_limit=300)
def sync_ad_departments():
    """AD Department Sync - Abteilungen aus Active Directory"""
    return run_script('scripts/sync/sync_ad_departments.py', timeout=180)


# =============================================================================
# LAGER / PENNER MARKTPREISE - TAG 142
# =============================================================================

@shared_task(bind=True, max_retries=1, soft_time_limit=1800)
def update_penner_marktpreise(self, min_lagerwert: int = 50, limit: int = 100):
    """
    Aktualisiert Marktpreise für Penner-Teile.

    Läuft nachts um 3:00 Uhr und scraped eBay/Daparto Preise
    für alle Penner mit Lagerwert > min_lagerwert.

    Args:
        min_lagerwert: Mindest-Lagerwert in EUR (default: 50)
        limit: Max. Anzahl Teile pro Lauf (default: 100)
    """
    with task_lock('update_penner_marktpreise') as acquired:
        if not acquired:
            return {'status': 'skipped', 'reason': 'Task läuft bereits'}

        from datetime import datetime
        start_time = datetime.now()

        try:
            # Service importieren und ausführen
            from api.preisvergleich_service import preisvergleich_service

            logger.info(f"Starte Penner-Marktpreis-Update (min_lagerwert={min_lagerwert}, limit={limit})")

            result = preisvergleich_service.update_all_penner(
                min_lagerwert=min_lagerwert,
                limit=limit
            )

            duration = (datetime.now() - start_time).total_seconds()

            logger.info(f"Penner-Marktpreis-Update abgeschlossen: {result.get('updated', 0)} Teile in {duration:.1f}s")

            return {
                'status': 'success',
                'updated': result.get('updated', 0),
                'failed': result.get('failed', 0),
                'skipped': result.get('skipped', 0),
                'duration': duration
            }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Penner-Marktpreis-Update fehlgeschlagen: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'duration': duration
            }


@shared_task(soft_time_limit=300)
def email_penner_weekly():
    """
    Wöchentlicher Penner-Verkaufschancen Report per E-Mail.
    Läuft jeden Montag um 7:00 Uhr.
    """
    return run_script('scripts/send_weekly_penner_report.py --force', timeout=180)


@shared_task(bind=True, max_retries=2, soft_time_limit=300)
def sync_eautoseller_data(self):
    """
    Synchronisiert eAutoseller-Daten (KPIs und Fahrzeugliste).
    Läuft alle 15 Minuten während Arbeitszeit.
    
    Aktualisiert:
    - Dashboard-KPIs (startdata.asp)
    - Fahrzeugliste (kfzuebersicht.asp)
    """
    with task_lock('sync_eautoseller_data') as acquired:
        if not acquired:
            return {'status': 'skipped', 'reason': 'already running'}
        
        start_time = datetime.now()
        logger.info("eAutoseller-Daten-Sync gestartet")
        
        try:
            # Import hier, damit Fehler erst beim Ausführen auftreten
            from lib.eautoseller_client import EAutosellerClient
            import os
            
            # Credentials aus Environment oder Config
            username = os.getenv('EAUTOSELLER_USERNAME', 'fGreiner')
            password = os.getenv('EAUTOSELLER_PASSWORD', 'fGreiner12')
            loginbereich = os.getenv('EAUTOSELLER_LOGINBEREICH', 'kfz')
            
            client = EAutosellerClient(username, password, loginbereich)
            client.login()
            
            # KPIs abrufen
            kpis = client.get_dashboard_kpis()
            logger.info(f"KPIs abgerufen: {len(kpis)} Widgets")
            
            # Fahrzeugliste abrufen (wird später verfeinert)
            vehicles = client.get_vehicle_list(active_only=True)
            logger.info(f"Fahrzeugliste abgerufen: {len(vehicles)} Fahrzeuge")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                'status': 'success',
                'kpis_count': len(kpis),
                'vehicles_count': len(vehicles),
                'duration': duration
            }
            
        except Exception as exc:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"eAutoseller-Sync fehlgeschlagen: {str(exc)}")
            
            # Retry bei Netzwerk-Fehlern
            if 'timeout' in str(exc).lower() or 'connection' in str(exc).lower():
                raise self.retry(exc=exc, countdown=60)
            
            return {
                'status': 'error',
                'error': str(exc),
                'duration': duration
            }
