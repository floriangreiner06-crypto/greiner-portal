#!/usr/bin/env python3
"""
Debug-Script: Gudat API - Detaillierte Analyse
===============================================
Analysiert die Gudat-API-Responses um Probleme zu identifizieren:
1. Negative freie AW
2. Wochen-Übersicht 0%
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, '/opt/greiner-portal')

from tools.gudat_client import GudatClient

# Credentials aus Config laden
config_path = '/opt/greiner-portal/config/credentials.json'
with open(config_path, 'r') as f:
    config = json.load(f)
    gudat_config = config.get('external_systems', {}).get('gudat', {})
    username = gudat_config.get('username')
    password = gudat_config.get('password')

print("=" * 80)
print("GUDAT API - DETAILLIERTE ANALYSE")
print("=" * 80)
print(f"Zeitpunkt: {datetime.now()}")
print()

client = GudatClient(username, password)

if not client.login():
    print("❌ Login fehlgeschlagen!")
    sys.exit(1)

print("✅ Login erfolgreich")
print()

# =============================================================================
# 1. ROHE DATEN ANALYSIEREN
# =============================================================================

print("=" * 80)
print("1. ROHE DATEN (get_workload_raw)")
print("=" * 80)
print()

heute = datetime.now().strftime('%Y-%m-%d')
raw_data = client.get_workload_raw(heute, days=2)

if not raw_data:
    print("❌ Keine rohen Daten erhalten!")
    sys.exit(1)

print(f"✅ {len(raw_data)} Teams gefunden")
print()

# Finde Diagnosetechnik
diagnosetechnik = None
for team in raw_data:
    if 'diagnose' in team.get('name', '').lower():
        diagnosetechnik = team
        break

if diagnosetechnik:
    print("🔍 DIAGNOSETEchnik (rohe Daten):")
    print(f"   Name: {diagnosetechnik.get('name')}")
    print(f"   ID: {diagnosetechnik.get('id')}")
    print(f"   Kategorie: {diagnosetechnik.get('category_name')}")
    print()
    
    # Daten für heute
    data = diagnosetechnik.get('data', {})
    heute_data = data.get(heute, {})
    
    if heute_data:
        print(f"   📊 Daten für {heute}:")
        print(f"      base_workload: {heute_data.get('base_workload', 0)}")
        print(f"      planned_workload: {heute_data.get('planned_workload', 0)}")
        print(f"      free_workload: {heute_data.get('free_workload', 0)}")
        print(f"      absent_workload: {heute_data.get('absent_workload', 0)}")
        print()
        
        # Berechnung prüfen
        base = heute_data.get('base_workload', 0)
        planned = heute_data.get('planned_workload', 0)
        free = heute_data.get('free_workload', 0)
        absent = heute_data.get('absent_workload', 0)
        
        print(f"   🧮 Berechnung:")
        print(f"      base_workload: {base}")
        print(f"      planned_workload: {planned}")
        print(f"      absent_workload: {absent}")
        print(f"      Erwartet frei: {base - planned - absent}")
        print(f"      Tatsächlich frei: {free}")
        print(f"      Differenz: {free - (base - planned - absent)}")
    else:
        print(f"   ⚠️  Keine Daten für {heute} gefunden")
        print(f"   Verfügbare Daten: {list(data.keys())}")
    
    print()
    
    # Alle Daten-Strukturen
    print("   📋 Alle Daten-Strukturen:")
    for date, day_data in data.items():
        print(f"      {date}: {day_data}")
    print()

# =============================================================================
# 2. WORKLOAD SUMMARY ANALYSIEREN
# =============================================================================

print("=" * 80)
print("2. WORKLOAD SUMMARY (get_workload_summary)")
print("=" * 80)
print()

summary = client.get_workload_summary(heute)

if 'error' in summary:
    print(f"❌ Fehler: {summary['error']}")
else:
    print(f"✅ Summary erhalten")
    print(f"   Datum: {summary.get('date')}")
    print(f"   Gesamt Kapazität: {summary.get('total_capacity', 0)} AW")
    print(f"   Geplant: {summary.get('planned', 0)} AW")
    print(f"   Frei: {summary.get('free', 0)} AW")
    print(f"   Abwesend: {summary.get('absent', 0)} AW")
    print(f"   Auslastung: {summary.get('utilization_percent', 0)}%")
    print()
    
    # Finde Diagnosetechnik im Summary
    teams = summary.get('teams', [])
    diag_team = None
    for team in teams:
        if 'diagnose' in team.get('name', '').lower():
            diag_team = team
            break
    
    if diag_team:
        print("🔍 DIAGNOSETEchnik (Summary):")
        print(f"   Name: {diag_team.get('name')}")
        print(f"   ID: {diag_team.get('id')}")
        print(f"   Kapazität: {diag_team.get('capacity', 0)} AW")
        print(f"   Geplant: {diag_team.get('planned', 0)} AW")
        print(f"   Frei: {diag_team.get('free', 0)} AW")
        print(f"   Abwesend: {diag_team.get('absent', 0)} AW")
        print(f"   Auslastung: {diag_team.get('utilization', 0)}%")
        print()
        
        # Berechnung prüfen
        cap = diag_team.get('capacity', 0)
        planned = diag_team.get('planned', 0)
        free = diag_team.get('free', 0)
        absent = diag_team.get('absent', 0)
        
        print(f"   🧮 Berechnung:")
        print(f"      capacity: {cap}")
        print(f"      planned: {planned}")
        print(f"      absent: {absent}")
        print(f"      Erwartet frei: {cap - planned - absent}")
        print(f"      Tatsächlich frei: {free}")
        print(f"      Differenz: {free - (cap - planned - absent)}")
        print()

# =============================================================================
# 3. WOCHEN-ÜBERSICHT ANALYSIEREN
# =============================================================================

print("=" * 80)
print("3. WOCHEN-ÜBERSICHT (get_week_overview)")
print("=" * 80)
print()

week = client.get_week_overview(heute)

if 'error' in week:
    print(f"❌ Fehler: {week['error']}")
else:
    print(f"✅ Wochen-Übersicht erhalten")
    print(f"   Startdatum: {week.get('start_date')}")
    print(f"   Tage: {len(week.get('days', []))}")
    print()
    
    days = week.get('days', [])
    if days:
        print("   📅 Tages-Details:")
        for day in days:
            print(f"      {day.get('date')}: {day.get('capacity', 0)} AW Kapazität, "
                  f"{day.get('planned', 0)} AW geplant, "
                  f"{day.get('free', 0)} AW frei, "
                  f"{day.get('utilization', 0)}% Auslastung")
    else:
        print("   ⚠️  Keine Tage gefunden!")
        print()
        print("   🔍 Debug: Rohe Daten prüfen...")
        raw_week = client.get_workload_raw(heute, days=7)
        print(f"      Rohe Teams: {len(raw_week)}")
        
        # Sammle alle Daten
        all_dates = set()
        for team in raw_week:
            team_data = team.get('data', {})
            all_dates.update(team_data.keys())
            print(f"      Team '{team.get('name')}': {len(team_data)} Tage")
        
        print(f"      Gesamt verschiedene Daten: {len(all_dates)}")
        print(f"      Daten: {sorted(all_dates)}")
        
        # Prüfe warum keine Tage zurückgegeben werden
        print()
        print("   🔍 Prüfe warum keine Tage zurückgegeben werden:")
        for date in sorted(all_dates)[:7]:
            total_cap = 0
            total_planned = 0
            for team in raw_week:
                day_data = team.get('data', {}).get(date)
                if day_data:
                    total_cap += day_data.get('base_workload', 0)
                    total_planned += day_data.get('planned_workload', 0)
            print(f"      {date}: {total_cap} AW Kapazität, {total_planned} AW geplant")
            if total_cap == 0:
                print(f"         ⚠️  Keine Kapazität - Teams haben keine Daten für diesen Tag")

print()
print("=" * 80)
print("ANALYSE ABGESCHLOSSEN")
print("=" * 80)
