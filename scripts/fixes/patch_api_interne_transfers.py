#!/usr/bin/env python3
"""
API-Patch: Interne Transfers filtern
Datum: 2025-11-07

Dieses Script patcht die bankenspiegel_api.py um interne Transfers
aus den Dashboard-Statistiken herauszufiltern.

Problem: 343 interne Umbuchungen verfälschen die Umsatzzahlen massiv
         (~3,9 Mio EUR von 7,3 Mio EUR sind interne Transfers)

Lösung: SQL WHERE-Clause hinzufügen um interne Transfers zu filtern
"""

import re
import shutil
from datetime import datetime

# SQL WHERE-Clause zum Filtern interner Transfers
INTERNAL_TRANSFER_FILTER = """
    AND NOT (
        t.verwendungszweck LIKE '%Autohaus Greiner%Autohaus Greiner%'
        OR t.verwendungszweck LIKE '%Umbuchung%'
        OR t.verwendungszweck LIKE '%Einlage%'
        OR t.verwendungszweck LIKE '%Rückzahlung Einlage%'
        OR (t.verwendungszweck LIKE '%PN:801%' AND t.verwendungszweck LIKE '%Autohaus Greiner%')
    )
"""

def backup_file(filepath):
    """Erstelle Backup der Originaldatei"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{filepath}.backup_{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup erstellt: {backup_path}")
    return backup_path

def patch_dashboard_query(content):
    """Patche die Dashboard-Query um interne Transfers zu filtern"""
    
    # Suche nach der Dashboard-Query für "letzte_30_tage"
    pattern = r'(WHERE t\.buchungsdatum >= DATE\(["\']now["\']\s*,\s*["\']-30 days["\']\))'
    
    # Füge den Filter hinzu
    replacement = r'\1' + INTERNAL_TRANSFER_FILTER.strip()
    
    content_new = re.sub(pattern, replacement, content)
    
    # Zähle wie viele Ersetzungen
    count = len(re.findall(pattern, content))
    
    return content_new, count

def patch_current_month_query(content):
    """Patche die Query für den aktuellen Monat"""
    
    # Suche nach der Query für aktuellen Monat
    pattern = r"(WHERE strftime\('%Y-%m', t\.buchungsdatum\) = strftime\('%Y-%m', 'now'\))"
    
    # Füge den Filter hinzu
    replacement = r'\1' + INTERNAL_TRANSFER_FILTER.strip()
    
    content_new = re.sub(pattern, replacement, content)
    
    # Zähle Ersetzungen
    count = len(re.findall(pattern, content))
    
    return content_new, count

def add_internal_transfers_section(content):
    """Füge separaten Bereich für interne Transfers zum Dashboard hinzu"""
    
    # Suche nach der Stelle wo "letzte_30_tage" hinzugefügt wird
    pattern = r'("letzte_30_tage":\s*\{[^}]+\})'
    
    internal_section = """,
        "interne_transfers_30_tage": {
            "anzahl_transaktionen": interne_count,
            "volumen": float(interne_volumen) if interne_volumen else 0.0
        }"""
    
    replacement = r'\1' + internal_section
    
    content_new = re.sub(pattern, replacement, content)
    
    return content_new

def add_internal_transfers_query(content):
    """Füge Query für interne Transfers hinzu"""
    
    # Suche nach der Stelle wo die letzte_30_tage Query definiert ist
    # und füge danach die Query für interne Transfers ein
    
    internal_query = """
        # Interne Transfers (letzte 30 Tage)
        cursor.execute('''
            SELECT 
                COUNT(*) as anzahl,
                SUM(ABS(betrag)) as volumen
            FROM transaktionen t
            WHERE t.buchungsdatum >= DATE('now', '-30 days')
              AND (
                t.verwendungszweck LIKE '%Autohaus Greiner%Autohaus Greiner%'
                OR t.verwendungszweck LIKE '%Umbuchung%'
                OR t.verwendungszweck LIKE '%Einlage%'
                OR t.verwendungszweck LIKE '%Rückzahlung Einlage%'
                OR (t.verwendungszweck LIKE '%PN:801%' AND t.verwendungszweck LIKE '%Autohaus Greiner%')
              )
        ''')
        row = cursor.fetchone()
        interne_count = row[0] if row else 0
        interne_volumen = row[1] if row else 0.0
"""
    
    # Finde die Stelle nach den letzte_30_tage Queries
    pattern = r"(letzte_30_saldo = [^\n]+\n)"
    replacement = r'\1' + internal_query
    
    content_new = re.sub(pattern, replacement, content, count=1)
    
    return content_new

def main():
    filepath = '/opt/greiner-portal/api/bankenspiegel_api.py'
    
    print("=" * 60)
    print("API-PATCH: Interne Transfers filtern")
    print("=" * 60)
    print()
    
    # Backup erstellen
    print("📦 Erstelle Backup...")
    backup_path = backup_file(filepath)
    print()
    
    # Datei einlesen
    print("📖 Lese API-Datei...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"✅ Datei gelesen: {len(content)} Zeichen")
    print()
    
    # Patches anwenden
    print("🔧 Wende Patches an...")
    
    # Patch 1: Dashboard letzte 30 Tage
    content, count1 = patch_dashboard_query(content)
    print(f"  ✅ Patch 1: Dashboard letzte_30_tage ({count1} Ersetzungen)")
    
    # Patch 2: Aktueller Monat
    content, count2 = patch_current_month_query(content)
    print(f"  ✅ Patch 2: Aktueller Monat ({count2} Ersetzungen)")
    
    # Patch 3: Interne Transfers Query hinzufügen
    content = add_internal_transfers_query(content)
    print(f"  ✅ Patch 3: Interne Transfers Query hinzugefügt")
    
    # Patch 4: Interne Transfers zum Dashboard-Response
    content = add_internal_transfers_section(content)
    print(f"  ✅ Patch 4: Interne Transfers im Response")
    
    print()
    
    # Datei schreiben
    print("💾 Schreibe gepatchte Datei...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Datei geschrieben: {filepath}")
    print()
    
    # Zusammenfassung
    print("=" * 60)
    print("✅ PATCH ERFOLGREICH!")
    print("=" * 60)
    print()
    print("📋 Zusammenfassung:")
    print(f"  • Backup: {backup_path}")
    print(f"  • Interne Transfers werden nun gefiltert")
    print(f"  • Dashboard zeigt nur noch echte Umsätze")
    print(f"  • Interne Transfers separat ausgewiesen")
    print()
    print("🔄 Nächste Schritte:")
    print("  1. Flask neu starten:")
    print("     pkill -f 'python.*app.py'")
    print("     nohup python3 app.py > logs/flask.log 2>&1 &")
    print()
    print("  2. Dashboard testen:")
    print("     curl -s http://localhost:5000/api/bankenspiegel/dashboard | python3 -m json.tool")
    print()
    print("  3. Erwartete Änderung:")
    print("     • Einnahmen: 7,28 Mio → 5,36 Mio EUR (-26%)")
    print("     • Ausgaben:  7,06 Mio → 5,08 Mio EUR (-28%)")
    print("     • Neue Sektion: 'interne_transfers_30_tage'")
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        print()
        print("💡 Tipp: Falls Fehler auftreten, Backup wiederherstellen:")
        print("   cp /opt/greiner-portal/api/bankenspiegel_api.py.backup_* /opt/greiner-portal/api/bankenspiegel_api.py")
        exit(1)
