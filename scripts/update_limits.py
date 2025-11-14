#!/usr/bin/env python3
import sqlite3
import shutil
from datetime import datetime

# Backup erstellen
backup_file = f"/opt/greiner-portal/data/greiner_controlling.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2('/opt/greiner-portal/data/greiner_controlling.db', backup_file)
print(f"✅ Backup erstellt: {backup_file}")

# Verbindung zur DB
conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
cursor = conn.cursor()

# Updates
updates = [
    (1, 'Sparkasse KK', 100000),
    (8, '1700057908 Festgeld', 250000),
    (17, '4700057908 Darlehen', 1000000),
    (23, '3700057908 Festgeld', 824000),
]

print("\n" + "=" * 80)
print("🔧 FÜHRE LIMIT-UPDATES DURCH")
print("=" * 80)

for konto_id, kontoname, neues_limit in updates:
    cursor.execute("UPDATE konten SET kreditlinie = ? WHERE id = ?", (neues_limit, konto_id))
    print(f"✅ ID {konto_id:2d} | {kontoname:30s} → {neues_limit:>10,.0f} EUR")

conn.commit()

# Verifizierung
print("\n" + "=" * 80)
print("✅ VERIFIZIERUNG")
print("=" * 80)

for konto_id, kontoname, soll_limit in updates:
    cursor.execute("SELECT kreditlinie FROM konten WHERE id = ?", (konto_id,))
    ist_limit = cursor.fetchone()[0]
    status = "✅" if ist_limit == soll_limit else "❌"
    print(f"{status} ID {konto_id:2d} | {kontoname:30s} | Limit: {ist_limit:>10,.0f} EUR")

conn.close()

print("\n✅ LIMITS ERFOLGREICH AKTUALISIERT!")
print(f"📦 Backup: {backup_file}")
