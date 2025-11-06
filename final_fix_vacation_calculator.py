#!/usr/bin/env python3
"""Final Fix: datum -> date in WHERE und ORDER BY"""

file_path = 'vacation_v2/utils/vacation_calculator.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Ersetze in WHERE und ORDER BY
content = content.replace("strftime('%Y', datum)", "strftime('%Y', date)")
content = content.replace("ORDER BY datum", "ORDER BY date")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fix angewendet:")
print("   • WHERE strftime('%Y', datum) -> date")
print("   • ORDER BY datum -> date")
