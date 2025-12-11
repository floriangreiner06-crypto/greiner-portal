#!/usr/bin/env python3
"""
Kontoauszug Watcher
===================
Prüft alle 5 Minuten (7-9 Uhr) auf neue Kontoauszüge
und importiert sie automatisch.

Erstellt: 2025-12-02
"""

import os
import sys
import glob
import time
from datetime import datetime, timedelta

# Pfade
BASE_DIR = '/opt/greiner-portal'
MT940_DIR = '/mnt/buchhaltung/Buchhaltung/Kontoauszüge/mt940/'
PDF_DIR = '/mnt/buchhaltung/Buchhaltung/Kontoauszüge/'
LOCK_FILE = '/tmp/kontoauszug_import.lock'

# Prüfe ob Import bereits läuft
if os.path.exists(LOCK_FILE):
    # Lock älter als 10 Minuten = stale
    if os.path.getmtime(LOCK_FILE) > time.time() - 600:
        print(f"[{datetime.now()}] Import läuft bereits (Lock-File existiert)")
        sys.exit(0)
    else:
        os.remove(LOCK_FILE)

def find_new_files(directory, extensions, max_age_minutes=10):
    """Findet Dateien die in den letzten X Minuten geändert wurden."""
    new_files = []
    cutoff = time.time() - (max_age_minutes * 60)
    
    for ext in extensions:
        pattern = os.path.join(directory, f'**/*.{ext}')
        for filepath in glob.glob(pattern, recursive=True):
            if os.path.getmtime(filepath) > cutoff:
                new_files.append(filepath)
    
    return new_files

def main():
    print(f"[{datetime.now()}] Kontoauszug-Watcher gestartet")
    
    # MT940 prüfen
    new_mt940 = find_new_files(MT940_DIR, ['sta', 'STA', 'mt940', 'MT940'])
    
    # PDFs prüfen (alle Bank-Unterordner)
    new_pdfs = find_new_files(PDF_DIR, ['pdf', 'PDF'])
    
    if not new_mt940 and not new_pdfs:
        print(f"[{datetime.now()}] Keine neuen Dateien gefunden")
        return
    
    # Lock setzen
    with open(LOCK_FILE, 'w') as f:
        f.write(str(datetime.now()))
    
    try:
        # MT940 importieren
        if new_mt940:
            print(f"[{datetime.now()}] {len(new_mt940)} neue MT940 Dateien gefunden")
            import subprocess
            result = subprocess.run(
                [os.path.join(BASE_DIR, 'venv/bin/python3'), 
                 os.path.join(BASE_DIR, 'scripts/imports/import_mt940.py'),
                 MT940_DIR],
                capture_output=True,
                text=True,
                cwd=BASE_DIR
            )
            print(result.stdout)
            if result.stderr:
                print(f"STDERR: {result.stderr}")
        
        # PDFs importieren
        if new_pdfs:
            print(f"[{datetime.now()}] {len(new_pdfs)} neue PDF Dateien gefunden")
            import subprocess
            result = subprocess.run(
                [os.path.join(BASE_DIR, 'venv/bin/python3'),
                 os.path.join(BASE_DIR, 'scripts/imports/import_all_bank_pdfs.py'),
                 '--today'],
                capture_output=True,
                text=True,
                cwd=BASE_DIR
            )
            print(result.stdout)
            if result.stderr:
                print(f"STDERR: {result.stderr}")
                
    finally:
        # Lock entfernen
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    
    print(f"[{datetime.now()}] Kontoauszug-Watcher beendet")

if __name__ == '__main__':
    main()
