#!/usr/bin/env python3
import re

with open('/tmp/hyundai_screenshots/bestandsliste_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("🔍 Suche Download-Button mit Context...\n")

# Suche mat-icon mit download_file UND zeige 500 Zeichen davor und danach
pattern = r'.{0,500}<mat-icon[^>]*>download_file</mat-icon>.{0,500}'
matches = re.findall(pattern, html, re.DOTALL)

for i, match in enumerate(matches, 1):
    print(f"=== Match {i} ===")
    print(match)
    print("\n")

print("\n🔍 Suche nach allen Buttons in der Nähe...\n")

# Finde alle button-Tags
button_pattern = r'<button[^>]*>.*?</button>'
buttons = re.findall(button_pattern, html, re.DOTALL)

for i, btn in enumerate(buttons[:30], 1):
    if 'download' in btn.lower() or len(btn) < 300:
        print(f"Button {i}:")
        print(btn[:500])
        print("\n---\n")
