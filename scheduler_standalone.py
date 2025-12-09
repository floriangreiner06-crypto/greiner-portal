#!/usr/bin/env python3
"""
Greiner Portal - Standalone Job Scheduler
=========================================
Läuft als separater Prozess, unabhängig von Gunicorn.

Starten mit:
    python3 scheduler_standalone.py

Oder als Systemd-Service:
    sudo systemctl start greiner-scheduler
"""

import sys
import os
import signal
import time

# Projekt-Pfad setzen
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

from scheduler.job_manager import job_manager
from scheduler.job_definitions import register_all_jobs

def signal_handler(signum, frame):
    """Graceful shutdown bei SIGTERM/SIGINT"""
    print("\n🛑 Shutdown-Signal empfangen...")
    if job_manager and job_manager.get_scheduler().running:
        job_manager.shutdown()
    print("✅ Scheduler beendet")
    sys.exit(0)

def main():
    print("=" * 60)
    print("🚀 GREINER PORTAL - JOB SCHEDULER")
    print("=" * 60)
    
    # Signal-Handler registrieren
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Jobs registrieren
    print("\n📋 Registriere Jobs...")
    register_all_jobs()
    
    # Scheduler starten
    print("\n▶️  Starte Scheduler...")
    job_manager.start()
    
    print("\n✅ Scheduler läuft!")
    print("   Drücke Ctrl+C zum Beenden\n")
    
    # Endlos-Loop (Scheduler läuft im Hintergrund)
    try:
        while True:
            time.sleep(60)
            # Optionales Health-Log
            scheduler = job_manager.get_scheduler()
            if scheduler and scheduler.running:
                jobs = job_manager.get_jobs()
                print(f"💓 Scheduler aktiv - {len(jobs)} Jobs registriert")
            else:
                print("⚠️  Scheduler nicht mehr aktiv!")
                break
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == '__main__':
    main()
