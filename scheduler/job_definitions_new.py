"""
Job-Definitionen für DRIVE
==========================
Alle geplanten Jobs werden hier zentral definiert.

WICHTIG: Keine Lambdas verwenden - APScheduler kann sie nicht serialisieren!

Kostenstellen-Zuordnung:
- controlling: Controlling & Verwaltung (Bank, HR, Wartung)
- aftersales:  Aftersales (ServiceBox, Teile)
- verkauf:     Verkauf (Sync, Stellantis, Fahrzeuge)

Script-Struktur (TAG 90):
- scripts/imports/   → Daten importieren (Bank, Santander, Hyundai, etc.)
- scripts/sync/      → Mit Locosoft synchronisieren
- scripts/scrapers/  → Web-Scraper (ServiceBox, Hyundai)
- scripts/analysis/  → Analysen (Umsatz-Bereinigung)

Erstellt: 2025-12-02 (TAG 88)
Aktualisiert: 2025-12-04 (TAG 90) - Scripts umbenannt für Konsistenz
"""

from scheduler.job_manager import job_manager, run_script, run_shell


# ============================================================================
# JOB-FUNKTIONEN
# ============================================================================

# ---------------------------------------------------------------------------
# CONTROLLING & VERWALTUNG
# ---------------------------------------------------------------------------

# Bank & Finanzen
def job_import_mt940():
    """MT940 Import für alle Banken AUSSER HypoVereinsbank"""
    mt940_dir = '/mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/'
    return run_script('scripts/imports/import_mt940.py', 'import_mt940', 'MT940 Import', timeout=120, args=[mt940_dir])

def job_import_hvb_pdf():
    """PDF Import NUR für HypoVereinsbank (einzige Bank ohne MT940)"""
    return run_script('scripts/imports/import_hvb_pdf.py', 'import_hvb_pdf', 'HypoVereinsbank PDF Import', timeout=120, args=['--bank', 'hvb', '--days', '3'])

def job_umsatz_bereinigung():
    """Umsatz-Bereinigung für aktuellen Monat"""
    return run_script('scripts/analysis/umsatz_bereinigung.py', 'umsatz_bereinigung', 'Umsatz-Bereinigung', timeout=300)

def job_import_santander():
    """Santander Finanzierungsbestand importieren"""
    return run_script('scripts/imports/import_santander.py', 'import_santander', 'Santander Import')

def job_import_hyundai():
    """Hyundai Finance CSV importieren"""
    return run_script('scripts/imports/import_hyundai.py', 'import_hyundai', 'Hyundai Finance Import')

def job_scrape_hyundai():
    """Hyundai Finance Portal scrapen"""
    return run_script('scripts/scrapers/scrape_hyundai.py', 'scrape_hyundai', 'Hyundai Scraper', timeout=180)

def job_leasys_cache_refresh():
    """Leasys Fahrzeug-Cache aktualisieren"""
    return run_script('scripts/update_leasys_cache.py', 'leasys_cache_refresh', 'Leasys Cache Refresh', timeout=600)

# HR & Mitarbeiter
def job_sync_employees():
    """Mitarbeiter aus Locosoft synchronisieren"""
    return run_shell('venv/bin/python3 scripts/sync/sync_employees.py --real', 'sync_employees', 'Mitarbeiter Sync')

# E-Mail Reports
def job_email_auftragseingang():
    """Täglichen Auftragseingang-Report per E-Mail senden"""
    return run_script('scripts/send_daily_auftragseingang.py', 'email_auftragseingang', 'Auftragseingang E-Mail')

# Wartung
def job_db_backup():
    """Tägliches Backup der SQLite-Datenbank"""
    return run_shell('cp data/greiner_controlling.db data/greiner_controlling.db.backup_$(date +%Y%m%d_%H%M%S)', 'db_backup', 'DB Backup')

def job_cleanup_backups():
    """Alte Backups löschen (behalte letzte 7)"""
    return run_shell('cd data && ls -t greiner_controlling.db.backup_* 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null', 'cleanup_backups', 'Backup Cleanup')

# ---------------------------------------------------------------------------
# AFTERSALES
# ---------------------------------------------------------------------------

# ServiceBox
def job_servicebox_scraper():
    """ServiceBox Bestellungen scrapen (inkrementell)"""
    return run_script('scripts/scrapers/scrape_servicebox.py', 'servicebox_scraper', 'ServiceBox Scraper', timeout=1800)

def job_servicebox_matcher():
    """ServiceBox mit Locosoft matchen"""
    return run_script('scripts/scrapers/match_servicebox.py', 'servicebox_matcher', 'ServiceBox Matcher', timeout=300)

def job_servicebox_import():
    """ServiceBox Daten in DB importieren"""
    return run_script('scripts/imports/import_servicebox.py', 'servicebox_import', 'ServiceBox Import', timeout=120)

def job_servicebox_master():
    """ServiceBox komplett neu laden (Master-Update)"""
    return run_script('scripts/scrapers/scrape_servicebox_full.py', 'servicebox_master', 'ServiceBox Master', timeout=3600)

# Teile
def job_sync_teile():
    """Teile mit Locosoft synchronisieren"""
    return run_script('scripts/sync/sync_teile.py', 'sync_teile', 'Teile Sync')

def job_import_teile():
    """Teile-Lieferscheine importieren"""
    return run_script('scripts/imports/import_teile.py', 'import_teile', 'Teile Import')

# ---------------------------------------------------------------------------
# VERKAUF
# ---------------------------------------------------------------------------

def job_sync_sales():
    """Verkaufsdaten aus Locosoft synchronisieren"""
    return run_script('scripts/sync/sync_sales.py', 'sync_sales', 'Verkauf Sync')

def job_import_stellantis():
    """Stellantis-Fahrzeugdaten importieren (Peugeot, Opel, Fiat)"""
    return run_script('scripts/imports/import_stellantis.py', 'import_stellantis', 'Stellantis Import')

def job_sync_stammdaten():
    """Fahrzeug-Stammdaten aus Locosoft synchronisieren"""
    return run_script('scripts/sync/sync_stammdaten.py', 'sync_stammdaten', 'Stammdaten Sync')

def job_locosoft_mirror():
    """Locosoft-Daten für lokale Abfragen spiegeln"""
    return run_shell('venv/bin/python3 scripts/sync/locosoft_mirror.py --min-rows 100', 'locosoft_mirror', 'Locosoft Mirror', timeout=600)

def job_bwa_berechnung():
    """BWA aus gespiegelten Locosoft-Daten berechnen"""
    return run_script('scripts/sync/bwa_berechnung.py', 'bwa_berechnung', 'BWA Berechnung', timeout=120)


# ============================================================================
# REGISTRIERUNG
# ============================================================================

def register_all_jobs():
    """Registriert alle Jobs im Scheduler."""
    
    # =========================================================================
    # KOSTENSTELLE: CONTROLLING & VERWALTUNG
    # =========================================================================
    
    # --- Bank & Finanzen ---
    
    # MT940 Import - 08:00, 12:00, 17:00
    job_manager.add_cron_job(
        job_id='import_mt940_08',
        func=job_import_mt940,
        name='MT940 Import (08:00)',
        description='Importiert MT940 Kontoauszüge (Genobank, Sparkasse, VR Bank Landau)',
        category='controlling',
        hour='8', minute='0', day_of_week='mon-fri'
    )
    
    job_manager.add_cron_job(
        job_id='import_mt940_12',
        func=job_import_mt940,
        name='MT940 Import (12:00)',
        description='Importiert MT940 Kontoauszüge (Genobank, Sparkasse, VR Bank Landau)',
        category='controlling',
        hour='12', minute='0', day_of_week='mon-fri'
    )
    
    job_manager.add_cron_job(
        job_id='import_mt940_17',
        func=job_import_mt940,
        name='MT940 Import (17:00)',
        description='Importiert MT940 Kontoauszüge (Genobank, Sparkasse, VR Bank Landau)',
        category='controlling',
        hour='17', minute='0', day_of_week='mon-fri'
    )
    
    # HypoVereinsbank PDF Import - 08:30
    job_manager.add_cron_job(
        job_id='import_hvb_pdf',
        func=job_import_hvb_pdf,
        name='HypoVereinsbank PDF Import',
        description='Importiert HypoVereinsbank PDF (einzige Bank ohne MT940)',
        category='controlling',
        hour='8', minute='30', day_of_week='mon-fri'
    )
    
    # Umsatz-Bereinigung - 09:30
    job_manager.add_cron_job(
        job_id='umsatz_bereinigung',
        func=job_umsatz_bereinigung,
        name='Umsatz-Bereinigung',
        description='Bereinigt Umsatzdaten für aktuellen Monat',
        category='controlling',
        hour='9', minute='30', day_of_week='mon-fri'
    )
    
    # Santander Import - 08:15
    job_manager.add_cron_job(
        job_id='import_santander',
        func=job_import_santander,
        name='Santander Bestand Import',
        description='Importiert Santander Finanzierungsbestand',
        category='controlling',
        hour='8', minute='15', day_of_week='mon-fri'
    )
    
    # Hyundai Finance - 08:45 Scrape, 09:00 Import
    job_manager.add_cron_job(
        job_id='scrape_hyundai',
        func=job_scrape_hyundai,
        name='Hyundai Scraper',
        description='Scrapt Hyundai Finance Portal',
        category='controlling',
        hour='8', minute='45', day_of_week='mon-fri'
    )
    
    job_manager.add_cron_job(
        job_id='import_hyundai',
        func=job_import_hyundai,
        name='Hyundai Finance Import',
        description='Importiert Hyundai Finance CSV',
        category='controlling',
        hour='9', minute='0', day_of_week='mon-fri'
    )
    
    # Leasys Cache - alle 30 Min (07:00-18:00)
    job_manager.add_cron_job(
        job_id='leasys_cache_refresh',
        func=job_leasys_cache_refresh,
        name='Leasys Cache Refresh',
        description='Aktualisiert Leasys Fahrzeug-Cache für Kalkulator',
        category='controlling',
        hour='7-18', minute='*/30', day_of_week='mon-fri'
    )
    
    # --- HR & Mitarbeiter ---
    
    job_manager.add_cron_job(
        job_id='sync_employees',
        func=job_sync_employees,
        name='Mitarbeiter Sync',
        description='Synchronisiert Mitarbeiter aus Locosoft',
        category='controlling',
        hour='6', minute='0'
    )
    
    # --- E-Mail Reports ---
    
    job_manager.add_cron_job(
        job_id='email_auftragseingang',
        func=job_email_auftragseingang,
        name='Auftragseingang Daily Report',
        description='Sendet täglichen Auftragseingang-Report per E-Mail',
        category='controlling',
        hour='17', minute='15', day_of_week='mon-fri'
    )
    
    # --- Wartung ---
    
    job_manager.add_cron_job(
        job_id='db_backup',
        func=job_db_backup,
        name='Datenbank Backup',
        description='Erstellt tägliches Backup der SQLite-Datenbank',
        category='controlling',
        hour='3', minute='0'
    )
    
    job_manager.add_cron_job(
        job_id='cleanup_backups',
        func=job_cleanup_backups,
        name='Backup Cleanup',
        description='Löscht alte Backups (behalte letzte 7)',
        category='controlling',
        hour='3', minute='30'
    )
    
    # =========================================================================
    # KOSTENSTELLE: AFTERSALES
    # =========================================================================
    
    # --- ServiceBox ---
    
    # Scraper: 09:30, 12:30, 16:30
    for time_id, hour in [('09', '9'), ('12', '12'), ('16', '16')]:
        job_manager.add_cron_job(
            job_id=f'servicebox_scraper_{time_id}',
            func=job_servicebox_scraper,
            name=f'ServiceBox Scraper ({hour}:30)',
            description='Scrapt ServiceBox Bestellungen',
            category='aftersales',
            hour=hour, minute='30', day_of_week='mon-fri'
        )
    
    # Matcher: 10:00, 13:00, 17:00
    for time_id, hour in [('10', '10'), ('13', '13'), ('17', '17')]:
        job_manager.add_cron_job(
            job_id=f'servicebox_matcher_{time_id}',
            func=job_servicebox_matcher,
            name=f'ServiceBox Matcher ({hour}:00)',
            description='Matched ServiceBox mit Locosoft',
            category='aftersales',
            hour=hour, minute='0', day_of_week='mon-fri'
        )
    
    # Import: 10:05, 13:05, 17:05
    for time_id, hour in [('10', '10'), ('13', '13'), ('17', '17')]:
        job_manager.add_cron_job(
            job_id=f'servicebox_import_{time_id}',
            func=job_servicebox_import,
            name=f'ServiceBox Import ({hour}:05)',
            description='Importiert ServiceBox Daten in DB',
            category='aftersales',
            hour=hour, minute='5', day_of_week='mon-fri'
        )
    
    # Master-Update: 20:00
    job_manager.add_cron_job(
        job_id='servicebox_master',
        func=job_servicebox_master,
        name='ServiceBox Master (20:00)',
        description='Lädt alle ServiceBox Bestellungen komplett neu',
        category='aftersales',
        hour='20', minute='0', day_of_week='mon-fri'
    )
    
    # --- Teile ---
    
    job_manager.add_interval_job(
        job_id='sync_teile',
        func=job_sync_teile,
        name='Teile Sync',
        description='Synchronisiert Teile mit Locosoft',
        category='aftersales',
        minutes=30
    )
    
    job_manager.add_cron_job(
        job_id='import_teile',
        func=job_import_teile,
        name='Teile Import',
        description='Importiert Teile-Lieferscheine',
        category='aftersales',
        hour='*/2', minute='0'
    )
    
    # =========================================================================
    # KOSTENSTELLE: VERKAUF
    # =========================================================================
    
    job_manager.add_cron_job(
        job_id='sync_sales',
        func=job_sync_sales,
        name='Verkauf Sync',
        description='Synchronisiert Verkaufsdaten aus Locosoft',
        category='verkauf',
        hour='7-18', minute='0', day_of_week='mon-fri'
    )
    
    job_manager.add_cron_job(
        job_id='import_stellantis',
        func=job_import_stellantis,
        name='Stellantis Import',
        description='Importiert Stellantis-Fahrzeugdaten (Peugeot, Opel, Fiat)',
        category='verkauf',
        hour='7', minute='30', day_of_week='mon-fri'
    )
    
    job_manager.add_cron_job(
        job_id='sync_stammdaten',
        func=job_sync_stammdaten,
        name='Stammdaten Sync',
        description='Synchronisiert Fahrzeug-Stammdaten aus Locosoft',
        category='verkauf',
        hour='9', minute='30'
    )
    
    job_manager.add_cron_job(
        job_id='locosoft_mirror',
        func=job_locosoft_mirror,
        name='Locosoft Mirror',
        description='Spiegelt Locosoft-Daten für lokale Abfragen',
        category='verkauf',
        hour='19', minute='0'
    )
    
    job_manager.add_cron_job(
        job_id='bwa_berechnung',
        func=job_bwa_berechnung,
        name='BWA Berechnung',
        description='Berechnet BWA aus gespiegelten Locosoft-Daten',
        category='controlling',
        hour='19', minute='30'
    )
    
    # =========================================================================
    # ÜBERSICHT
    # =========================================================================
    
    try:
        job_count = len(job_manager.get_jobs())
        print(f"📋 {job_count} Jobs registriert")
    except Exception as e:
        print(f"📋 Jobs registriert (Zählung: {e})")
