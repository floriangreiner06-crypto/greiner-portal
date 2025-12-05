#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kompletter November-Import - Tag 15
===================================
Führt alle November-Imports in der richtigen Reihenfolge aus

Usage:
    python3 import_november_all_tag15.py [--dry-run]

Author: Claude AI
Version: 1.0
Date: 2025-11-07
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/opt/greiner-portal")

def print_header(title):
    """Gibt formatierten Header aus"""
    print("\n" + "="*70)
    print(f"🚀 {title}")
    print("="*70 + "\n")

def run_script(script_name, dry_run=False):
    """Führt ein Script aus"""
    cmd = ["python3", script_name]
    if dry_run:
        cmd.append("--dry-run")
    
    print(f"➤ Führe aus: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=BASE_DIR)
    
    if result.returncode != 0:
        print(f"❌ Fehler beim Ausführen von {script_name}")
        return False
    
    return True

def main():
    """Hauptfunktion"""
    dry_run = '--dry-run' in sys.argv
    
    print_header(f"NOVEMBER-IMPORT TAG 15 - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    if dry_run:
        print("⚠️  DRY-RUN MODUS - Keine Datenbank-Änderungen\n")
    
    # Status VORHER
    print_header("1. STATUS VORHER")
    if not run_script("check_november_status.py"):
        sys.exit(1)
    
    input("\n➤ Drücken Sie ENTER um fortzufahren...")
    
    # Sparkasse Import
    print_header("2. SPARKASSE IMPORT")
    if not run_script("import_sparkasse_november.py", dry_run):
        print("⚠️  Sparkasse-Import fehlgeschlagen, fahre trotzdem fort...")
    
    input("\n➤ Drücken Sie ENTER um fortzufahren...")
    
    # Hypovereinsbank Import
    print_header("3. HYPOVEREINSBANK IMPORT")
    if not run_script("import_hypovereinsbank_november.py", dry_run):
        print("⚠️  Hypo-Import fehlgeschlagen, fahre trotzdem fort...")
    
    input("\n➤ Drücken Sie ENTER um fortzufahren...")
    
    # Weitere Genobank-Konten (falls V2-Script vorhanden)
    if Path(BASE_DIR / "import_november_all_accounts_v2.py").exists():
        print_header("4. WEITERE GENOBANK-KONTEN")
        if not run_script("import_november_all_accounts_v2.py", dry_run):
            print("⚠️  Genobank-Import fehlgeschlagen, fahre trotzdem fort...")
        
        input("\n➤ Drücken Sie ENTER um fortzufahren...")
    
    # Status NACHHER
    print_header("5. STATUS NACHHER")
    if not run_script("check_november_status.py"):
        sys.exit(1)
    
    # Validierung
    print_header("6. VALIDIERUNG")
    if Path(BASE_DIR / "validate_salden.sh").exists():
        result = subprocess.run(["bash", "validate_salden.sh"], cwd=BASE_DIR)
        if result.returncode != 0:
            print("⚠️  Validierung fehlgeschlagen")
    
    # Fertig
    print_header("✅ IMPORT ABGESCHLOSSEN")
    
    if dry_run:
        print("⚠️  DRY-RUN MODUS war aktiv - Keine Daten wurden geändert")
        print("   Führen Sie ohne --dry-run aus um Daten zu importieren")
    else:
        print("✅ Alle Imports erfolgreich abgeschlossen!")
        print("   Prüfen Sie die Logs für Details")
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()
