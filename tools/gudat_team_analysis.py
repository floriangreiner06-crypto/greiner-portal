#!/usr/bin/env python3
"""
GUDAT - Detaillierte Team-Analyse
"""

import json
import sys
sys.path.insert(0, '/opt/greiner-portal/tools')

from gudat_client import GudatClient

USERNAME = "florian.greiner@auto-greiner.de"
PASSWORD = "Hyundai2025!"

print("=" * 70)
print("GUDAT TEAM-ANALYSE")
print("=" * 70)

client = GudatClient(USERNAME, PASSWORD)

if not client.login():
    print("Login fehlgeschlagen!")
    exit(1)

# Hole Rohdaten
raw_data = client.get_workload_raw('2025-12-09', days=1)

print(f"\n📋 {len(raw_data)} Teams gefunden:\n")

# Kategorisiere Teams
intern_teams = []
extern_teams = []

for team in raw_data:
    team_name = team.get('name', 'Unknown')
    category = team.get('category_name', 'Unknown')
    team_id = team.get('id')
    
    day_data = list(team.get('data', {}).values())[0] if team.get('data') else {}
    
    cap = day_data.get('base_workload', 0)
    planned = day_data.get('planned_workload', 0)
    members = day_data.get('members', [])
    
    info = {
        'id': team_id,
        'name': team_name,
        'category': category,
        'capacity': cap,
        'planned': planned,
        'members_count': len(members),
        'members': members
    }
    
    if 'extern' in team_name.lower():
        extern_teams.append(info)
    else:
        intern_teams.append(info)

print("=" * 70)
print("🔧 INTERNE TEAMS (verrechenbare Stunden)")
print("=" * 70)

for team in sorted(intern_teams, key=lambda x: -x['capacity']):
    print(f"\n📌 {team['name']} (ID: {team['id']})")
    print(f"   Kategorie: {team['category']}")
    print(f"   Kapazität: {team['capacity']} AW")
    print(f"   Geplant: {team['planned']} AW")
    print(f"   Mitarbeiter: {team['members_count']}")
    
    if team['members']:
        print("   Team-Mitglieder:")
        for m in team['members'][:5]:
            print(f"      - {m.get('name', 'Unknown')}: {m.get('base_workload', 0)} AW Kapazität")

print("\n" + "=" * 70)
print("🏭 EXTERNE DIENSTLEISTER")
print("=" * 70)

for team in extern_teams:
    print(f"\n📌 {team['name']} (ID: {team['id']})")
    print(f"   Kapazität: {team['capacity']} AW, Geplant: {team['planned']} AW")

# Fokus auf die wichtigen Teams
print("\n" + "=" * 70)
print("⭐ WICHTIGE TEAMS: Allgemeine Reparatur & Diagnosetechnik")
print("=" * 70)

for team in raw_data:
    team_name = team.get('name', '')
    if 'Allgemeine Reparatur' in team_name or 'Diagnosetechnik' in team_name:
        print(f"\n{'='*50}")
        print(f"📌 {team_name}")
        print(f"{'='*50}")
        
        day_data = list(team.get('data', {}).values())[0] if team.get('data') else {}
        
        print(f"   base_workload: {day_data.get('base_workload', 0)} AW")
        print(f"   planned_workload: {day_data.get('planned_workload', 0)} AW")
        print(f"   absence_workload: {day_data.get('absence_workload', 0)} AW")
        print(f"   plannable_workload: {day_data.get('plannable_workload', 0)} AW")
        print(f"   free_workload: {day_data.get('free_workload', 0)} AW")
        print(f"   team_productivity_factor: {day_data.get('team_productivity_factor', 0)}")
        
        members = day_data.get('members', [])
        print(f"\n   👥 Mitarbeiter ({len(members)}):")
        for m in members:
            name = m.get('name', 'Unknown')
            base = m.get('base_workload', 0)
            planned = m.get('planned_workload', 0)
            absent = m.get('absence_workload', 0)
            free = m.get('free_workload', 0)
            print(f"      {name}: Kap={base} AW, Geplant={planned}, Abwesend={absent}, Frei={free}")

# Speichere vollständige Daten für Analyse
with open('/tmp/gudat_teams_full.json', 'w') as f:
    json.dump(raw_data, f, indent=2, ensure_ascii=False)
print("\n\n📁 Vollständige Daten: /tmp/gudat_teams_full.json")
