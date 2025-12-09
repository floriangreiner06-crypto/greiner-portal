"""
GREINER DRIVE - Celery Task Queue
==================================
Ersetzt APScheduler mit robusterem Task-Management.

Komponenten:
- Redis: Message Broker (localhost:6379)
- Celery Worker: Führt Tasks aus
- Celery Beat: Scheduler (cron-artig)
- Flower: Web-UI für Monitoring (Port 5555)

Erstellt: 2025-12-09 (TAG 110)
"""

from celery import Celery
from celery.schedules import crontab
import os

# Basis-Pfad
BASE_DIR = '/opt/greiner-portal'

# Celery App erstellen
app = Celery(
    'greiner',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',  # Result Backend
    include=['celery_app.tasks']
)

# RedBeat für dynamische Schedules (optional)
try:
    from redbeat import RedBeatSchedulerEntry
    REDBEAT_AVAILABLE = True
except ImportError:
    REDBEAT_AVAILABLE = False

# Konfiguration
app.conf.update(
    # Zeitzone
    timezone='Europe/Berlin',
    enable_utc=False,
    
    # RedBeat für dynamische Schedules
    beat_scheduler='redbeat.RedBeatScheduler',
    redbeat_redis_url='redis://localhost:6379/2',
    redbeat_key_prefix='greiner:',
    
    # Task-Einstellungen
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    result_expires=86400,  # Results 24h behalten
    
    # Worker-Einstellungen
    worker_prefetch_multiplier=1,  # Ein Task nach dem anderen
    worker_max_tasks_per_child=50,  # Worker nach 50 Tasks neu starten (Memory-Leak-Schutz)
    
    # Task-Tracking
    task_track_started=True,
    task_send_sent_event=True,
    
    # Retry-Defaults
    task_default_retry_delay=60,  # 1 Minute warten vor Retry
    task_max_retries=3,
    
    # Beat Schedule (alle Jobs)
    beat_schedule={
        # =====================================================================
        # CONTROLLING & VERWALTUNG
        # =====================================================================
        
        # Bank & Finanzen - MT940 Import (3x täglich)
        'import-mt940-08': {
            'task': 'celery_app.tasks.import_mt940',
            'schedule': crontab(minute=0, hour=8, day_of_week='mon-fri'),
            'options': {'queue': 'controlling'}
        },
        'import-mt940-12': {
            'task': 'celery_app.tasks.import_mt940',
            'schedule': crontab(minute=0, hour=12, day_of_week='mon-fri'),
            'options': {'queue': 'controlling'}
        },
        'import-mt940-17': {
            'task': 'celery_app.tasks.import_mt940',
            'schedule': crontab(minute=0, hour=17, day_of_week='mon-fri'),
            'options': {'queue': 'controlling'}
        },
        
        # HypoVereinsbank PDF (einzige Bank ohne MT940)
        'import-hvb-pdf': {
            'task': 'celery_app.tasks.import_hvb_pdf',
            'schedule': crontab(minute=30, hour=8, day_of_week='mon-fri'),
            'options': {'queue': 'controlling'}
        },
        
        # Umsatz-Bereinigung
        'umsatz-bereinigung': {
            'task': 'celery_app.tasks.umsatz_bereinigung',
            'schedule': crontab(minute=30, hour=9, day_of_week='mon-fri'),
            'options': {'queue': 'controlling'}
        },
        
        # Santander Import
        'import-santander': {
            'task': 'celery_app.tasks.import_santander',
            'schedule': crontab(minute=15, hour=8, day_of_week='mon-fri'),
            'options': {'queue': 'controlling'}
        },
        
        # Hyundai Finance
        'scrape-hyundai': {
            'task': 'celery_app.tasks.scrape_hyundai',
            'schedule': crontab(minute=45, hour=8, day_of_week='mon-fri'),
            'options': {'queue': 'controlling'}
        },
        'import-hyundai': {
            'task': 'celery_app.tasks.import_hyundai',
            'schedule': crontab(minute=0, hour=9, day_of_week='mon-fri'),
            'options': {'queue': 'controlling'}
        },
        
        # Leasys Cache (alle 30 Min während Arbeitszeit)
        'leasys-cache-refresh': {
            'task': 'celery_app.tasks.leasys_cache_refresh',
            'schedule': crontab(minute='*/30', hour='7-18', day_of_week='mon-fri'),
            'options': {'queue': 'controlling'}
        },
        
        # HR & Mitarbeiter
        'sync-employees': {
            'task': 'celery_app.tasks.sync_employees',
            'schedule': crontab(minute=0, hour=6),
            'options': {'queue': 'controlling'}
        },
        'sync-locosoft-employees': {
            'task': 'celery_app.tasks.sync_locosoft_employees',
            'schedule': crontab(minute=15, hour=6),
            'options': {'queue': 'controlling'}
        },
        
        # E-Mail Reports
        'email-auftragseingang': {
            'task': 'celery_app.tasks.email_auftragseingang',
            'schedule': crontab(minute=15, hour=17, day_of_week='mon-fri'),
            'options': {'queue': 'controlling'}
        },
        'email-werkstatt-tagesbericht': {
            'task': 'celery_app.tasks.email_werkstatt_tagesbericht',
            'schedule': crontab(minute=30, hour=17, day_of_week='mon-fri'),
            'options': {'queue': 'aftersales'}
        },
        
        # Wartung
        'db-backup': {
            'task': 'celery_app.tasks.db_backup',
            'schedule': crontab(minute=0, hour=3),
            'options': {'queue': 'controlling'}
        },
        'cleanup-backups': {
            'task': 'celery_app.tasks.cleanup_backups',
            'schedule': crontab(minute=30, hour=3),
            'options': {'queue': 'controlling'}
        },
        
        # ML Training
        'ml-retrain': {
            'task': 'celery_app.tasks.ml_retrain',
            'schedule': crontab(minute=15, hour=3),
            'options': {'queue': 'aftersales'}
        },
        
        # Charge Types Sync (für SVS)
        'sync-charge-types': {
            'task': 'celery_app.tasks.sync_charge_types',
            'schedule': crontab(minute=5, hour=6),
            'options': {'queue': 'aftersales'}
        },
        
        # =====================================================================
        # AFTERSALES
        # =====================================================================
        
        # ServiceBox Scraper (3x täglich)
        'servicebox-scraper-09': {
            'task': 'celery_app.tasks.servicebox_scraper',
            'schedule': crontab(minute=30, hour=9, day_of_week='mon-fri'),
            'options': {'queue': 'aftersales'}
        },
        'servicebox-scraper-12': {
            'task': 'celery_app.tasks.servicebox_scraper',
            'schedule': crontab(minute=30, hour=12, day_of_week='mon-fri'),
            'options': {'queue': 'aftersales'}
        },
        'servicebox-scraper-16': {
            'task': 'celery_app.tasks.servicebox_scraper',
            'schedule': crontab(minute=30, hour=16, day_of_week='mon-fri'),
            'options': {'queue': 'aftersales'}
        },
        
        # ServiceBox Matcher (nach Scraper)
        'servicebox-matcher-10': {
            'task': 'celery_app.tasks.servicebox_matcher',
            'schedule': crontab(minute=0, hour=10, day_of_week='mon-fri'),
            'options': {'queue': 'aftersales'}
        },
        'servicebox-matcher-13': {
            'task': 'celery_app.tasks.servicebox_matcher',
            'schedule': crontab(minute=0, hour=13, day_of_week='mon-fri'),
            'options': {'queue': 'aftersales'}
        },
        'servicebox-matcher-17': {
            'task': 'celery_app.tasks.servicebox_matcher',
            'schedule': crontab(minute=0, hour=17, day_of_week='mon-fri'),
            'options': {'queue': 'aftersales'}
        },
        
        # ServiceBox Import (nach Matcher)
        'servicebox-import-10': {
            'task': 'celery_app.tasks.servicebox_import',
            'schedule': crontab(minute=5, hour=10, day_of_week='mon-fri'),
            'options': {'queue': 'aftersales'}
        },
        'servicebox-import-13': {
            'task': 'celery_app.tasks.servicebox_import',
            'schedule': crontab(minute=5, hour=13, day_of_week='mon-fri'),
            'options': {'queue': 'aftersales'}
        },
        'servicebox-import-17': {
            'task': 'celery_app.tasks.servicebox_import',
            'schedule': crontab(minute=5, hour=17, day_of_week='mon-fri'),
            'options': {'queue': 'aftersales'}
        },
        
        # ServiceBox Master (komplett neu laden)
        'servicebox-master': {
            'task': 'celery_app.tasks.servicebox_master',
            'schedule': crontab(minute=0, hour=20, day_of_week='mon-fri'),
            'options': {'queue': 'aftersales'}
        },
        
        # Teile
        'sync-teile': {
            'task': 'celery_app.tasks.sync_teile',
            'schedule': crontab(minute='*/30'),  # Alle 30 Min
            'options': {'queue': 'aftersales'}
        },
        'import-teile': {
            'task': 'celery_app.tasks.import_teile',
            'schedule': crontab(minute=0, hour='*/2'),  # Alle 2 Stunden
            'options': {'queue': 'aftersales'}
        },
        
        # =====================================================================
        # VERKAUF
        # =====================================================================
        
        # Verkauf Sync (stündlich während Arbeitszeit)
        'sync-sales': {
            'task': 'celery_app.tasks.sync_sales',
            'schedule': crontab(minute=0, hour='7-18', day_of_week='mon-fri'),
            'options': {'queue': 'verkauf'}
        },
        
        # Stellantis Import
        'import-stellantis': {
            'task': 'celery_app.tasks.import_stellantis',
            'schedule': crontab(minute=30, hour=7, day_of_week='mon-fri'),
            'options': {'queue': 'verkauf'}
        },
        
        # Stammdaten Sync
        'sync-stammdaten': {
            'task': 'celery_app.tasks.sync_stammdaten',
            'schedule': crontab(minute=30, hour=9),
            'options': {'queue': 'verkauf'}
        },
        
        # Locosoft Mirror (KRITISCH - inkl. VIEWs times, employees)
        'locosoft-mirror': {
            'task': 'celery_app.tasks.locosoft_mirror',
            'schedule': crontab(minute=0, hour=19),
            'options': {'queue': 'verkauf'}
        },
        
        # BWA Berechnung (nach Mirror)
        'bwa-berechnung': {
            'task': 'celery_app.tasks.bwa_berechnung',
            'schedule': crontab(minute=30, hour=19),
            'options': {'queue': 'controlling'}
        },
        
        # Werkstatt Leistung (nach Mirror)
        'werkstatt-leistung': {
            'task': 'celery_app.tasks.werkstatt_leistung',
            'schedule': crontab(minute=15, hour=19),
            'options': {'queue': 'aftersales'}
        },
    },
    
    # Task-Routen (welche Queue für welchen Task)
    task_routes={
        'celery_app.tasks.import_*': {'queue': 'controlling'},
        'celery_app.tasks.sync_*': {'queue': 'verkauf'},
        'celery_app.tasks.servicebox_*': {'queue': 'aftersales'},
        'celery_app.tasks.werkstatt_*': {'queue': 'aftersales'},
    },
)

# Autodiscover tasks
app.autodiscover_tasks(['celery_app'])
