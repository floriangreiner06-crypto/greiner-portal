#!/usr/bin/env python3
"""Prüft ob eAutoseller Task im Celery Schedule ist"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_app import app

print("=" * 60)
print("Celery Beat Schedule Check")
print("=" * 60)

schedule = app.conf.beat_schedule

# Suche nach eAutoseller Task
eautoseller_tasks = {k: v for k, v in schedule.items() if 'eautoseller' in k.lower()}

if eautoseller_tasks:
    print(f"\n✅ {len(eautoseller_tasks)} eAutoseller Task(s) gefunden:")
    for name, config in eautoseller_tasks.items():
        print(f"\n  Task: {name}")
        print(f"  Funktion: {config['task']}")
        print(f"  Schedule: {config['schedule']}")
        print(f"  Queue: {config.get('options', {}).get('queue', 'default')}")
else:
    print("\n❌ Keine eAutoseller Tasks gefunden!")

print(f"\n📊 Gesamt: {len(schedule)} Tasks im Schedule")

