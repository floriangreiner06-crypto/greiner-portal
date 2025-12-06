#!/usr/bin/env python3
"""
GUDAT - Zeige ALLE Types und Felder
"""

import json

print("=" * 70)
print("GUDAT - ALLE GRAPHQL TYPES")
print("=" * 70)

with open('/tmp/gudat_graphql_schema.json', 'r') as f:
    data = json.load(f)

types = data.get('data', {}).get('__schema', {}).get('types', [])

# Filtere System-Types raus (beginnen mit __)
user_types = [t for t in types if not t.get('name', '').startswith('__')]

print(f"\n📋 {len(user_types)} Types gefunden\n")

# Sortiere nach Name
for t in sorted(user_types, key=lambda x: x.get('name', '')):
    name = t.get('name', '')
    kind = t.get('kind', '')
    fields = t.get('fields')
    
    # Nur OBJECT types mit Feldern zeigen
    if kind == 'OBJECT' and fields:
        print(f"\n{'='*60}")
        print(f"📌 {name} ({len(fields)} Felder)")
        print(f"{'='*60}")
        
        for f in fields:
            field_name = f.get('name', '')
            field_type = f.get('type', {})
            
            # Type kann nested sein
            type_name = field_type.get('name')
            if not type_name:
                # Könnte LIST oder NON_NULL sein
                of_type = field_type.get('ofType', {})
                type_name = of_type.get('name') or field_type.get('kind', '?')
            
            print(f"   - {field_name}: {type_name}")

# Zeige auch die Query root
print("\n" + "=" * 70)
print("🔍 QUERY ROOT (verfügbare Queries)")
print("=" * 70)

for t in types:
    if t.get('name') == 'Query':
        for f in t.get('fields', []):
            print(f"   - {f.get('name')}")
