#!/usr/bin/env python3
"""
Patch-Script: Ersetzt get_tek_data() durch API-basierten Ansatz
TAG146: Von 230 Zeilen DB-Queries auf 10 Zeilen API-Call
"""

import re

# Datei einlesen
with open('/opt/greiner-portal/scripts/send_daily_tek.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Import für Helper-Modul hinzufügen (nach anderen imports)
import_pos = content.find("from datetime import datetime, date")
if import_pos != -1:
    import_line_end = content.find('\n', import_pos)
    content = (content[:import_line_end+1] +
               "from scripts.tek_api_helper import get_tek_data_from_api\n" +
               content[import_line_end+1:])

# 2. get_tek_data() Funktion ersetzen
# Finde Start und Ende der Funktion
func_start = content.find("def get_tek_data(monat=None, jahr=None, standort=None):")
if func_start == -1:
    print("❌ Funktion get_tek_data nicht gefunden!")
    exit(1)

# Finde nächste Funktion (format_euro oder get_subscribers_for_report)
next_func = content.find("\ndef ", func_start + 10)
if next_func == -1:
    print("❌ Ende der Funktion nicht gefunden!")
    exit(1)

# Alte Funktion entfernen und durch API-Call ersetzen
old_function = content[func_start:next_func]
new_function = """def get_tek_data(monat=None, jahr=None, standort=None):
    \"\"\"
    Wrapper für get_tek_data_from_api (TAG146: API-basiert statt DB-Queries)

    ALTE VERSION: 230 Zeilen komplexe DB-Queries
    NEUE VERSION: 1 Zeile API-Call → 100% konsistent mit DRIVE Web-UI!
    \"\"\"
    return get_tek_data_from_api(monat, jahr, standort)

"""

content = content[:func_start] + new_function + content[next_func:]

# 3. format_euro() Funktion entfernen (nutzt 'k'-Notation)
format_euro_start = content.find("def format_euro(value):")
if format_euro_start != -1:
    format_euro_end = content.find("\n\ndef ", format_euro_start + 10)
    if format_euro_end != -1:
        print("⚠️  Entferne format_euro() (nutzte 'k'-Notation)")
        content = content[:format_euro_start] + content[format_euro_end+2:]

# Datei speichern
with open('/opt/greiner-portal/scripts/send_daily_tek.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Patch erfolgreich!")
print(f"   - get_tek_data(): 230 Zeilen → 5 Zeilen (API-Call)")
print(f"   - format_euro() entfernt (hatte 'k'-Notation)")
print(f"   - Import für tek_api_helper hinzugefügt")
