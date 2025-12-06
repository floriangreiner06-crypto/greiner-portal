#!/usr/bin/env python3
"""
GUDAT - laravel_token finden!
"""

import time
import json
import subprocess
import re
from urllib.parse import unquote

BASE_URL = "https://werkstattplanung.net/greiner/deggendorf/kic"
USERNAME = "florian.greiner@auto-greiner.de"
PASSWORD = "Hyundai2025!"

print("=" * 60)
print("GUDAT - laravel_token FINDEN")
print("=" * 60)

# Test 1: Kommt laravel_token vom Login?
print("\n[1] Teste Login-Response auf laravel_token...")

# Hole initiale Cookies
result = subprocess.run([
    'curl', '-s', '-i',
    '-H', 'User-Agent: Mozilla/5.0',
    f'{BASE_URL}'
], capture_output=True, text=True)

cookies = {}
for line in result.stdout.split('\n'):
    if line.lower().startswith('set-cookie:'):
        match = re.match(r'set-cookie:\s*([^=]+)=([^;]+)', line, re.I)
        if match:
            cookies[match.group(1)] = match.group(2)

print(f"    Initiale Cookies: {list(cookies.keys())}")

# Login
xsrf = unquote(cookies.get('XSRF-TOKEN', ''))
cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])

result = subprocess.run([
    'curl', '-s', '-i',
    '-X', 'POST',
    '-H', 'Content-Type: application/json',
    '-H', 'Accept: application/json',
    '-H', f'X-XSRF-TOKEN: {xsrf}',
    '-H', f'Cookie: {cookie_str}',
    '-H', 'User-Agent: Mozilla/5.0',
    '-d', json.dumps({'username': USERNAME, 'password': PASSWORD, 'remember': True}),
    f'{BASE_URL}/login'
], capture_output=True, text=True)

print("\n    Set-Cookie vom Login:")
for line in result.stdout.split('\n'):
    if line.lower().startswith('set-cookie:'):
        name = line.split('=')[0].replace('set-cookie:', '').replace('Set-Cookie:', '').strip()
        print(f"      - {name}")
        
        # Update cookies
        match = re.match(r'set-cookie:\s*([^=]+)=([^;]+)', line, re.I)
        if match:
            cookies[match.group(1)] = match.group(2)

print(f"\n    Alle Cookies nach Login: {list(cookies.keys())}")

if 'laravel_token' in cookies:
    print("\n    ✅ laravel_token kommt vom LOGIN!")
else:
    print("\n    ❌ laravel_token NICHT vom Login!")
    
    # Test 2: Kommt es von einem anderen Endpunkt?
    print("\n[2] Teste andere Endpunkte...")
    
    endpoints = [
        '/da/',
        '/da/#/',
        '/api/v1/user',
        '/api/v1/config',
        '/ack',
    ]
    
    xsrf_new = unquote(cookies.get('XSRF-TOKEN', ''))
    cookie_str_new = '; '.join([f"{k}={v}" for k, v in cookies.items()])
    
    for endpoint in endpoints:
        result = subprocess.run([
            'curl', '-s', '-i',
            '-H', 'Accept: application/json',
            '-H', f'X-XSRF-TOKEN: {xsrf_new}',
            '-H', f'Cookie: {cookie_str_new}',
            '-H', 'User-Agent: Mozilla/5.0',
            f'{BASE_URL}{endpoint}'
        ], capture_output=True, text=True)
        
        new_cookies = []
        for line in result.stdout.split('\n'):
            if line.lower().startswith('set-cookie:'):
                name = line.split('=')[0].replace('set-cookie:', '').replace('Set-Cookie:', '').strip()
                new_cookies.append(name)
                
                # Update
                match = re.match(r'set-cookie:\s*([^=]+)=([^;]+)', line, re.I)
                if match:
                    cookies[match.group(1)] = match.group(2)
        
        if new_cookies:
            print(f"      {endpoint}: {new_cookies}")
            if 'laravel_token' in new_cookies:
                print(f"\n    ✅ laravel_token kommt von {endpoint}!")
                break
        else:
            print(f"      {endpoint}: (keine neuen Cookies)")

# Finale: Teste API mit allen Cookies
print("\n[3] Teste API mit allen gesammelten Cookies...")
xsrf_final = unquote(cookies.get('XSRF-TOKEN', ''))
cookie_str_final = '; '.join([f"{k}={v}" for k, v in cookies.items()])

print(f"    Cookies: {list(cookies.keys())}")

result = subprocess.run([
    'curl', '-s',
    '-H', 'Accept: application/json',
    '-H', f'X-XSRF-TOKEN: {xsrf_final}',
    '-H', f'Cookie: {cookie_str_final}',
    '-H', 'User-Agent: Mozilla/5.0',
    f'{BASE_URL}/api/v1/workload_week_summary?date=2025-12-09&days=1'
], capture_output=True, text=True)

if 'base_workload' in result.stdout:
    print(f"\n    ✅✅✅ API FUNKTIONIERT! ✅✅✅")
    data = json.loads(result.stdout)
    print(f"    {len(data)} Teams geladen!")
    
    # Zusammenfassung
    total_cap = 0
    total_planned = 0
    for team in data:
        for date_str, info in team.get('data', {}).items():
            total_cap += info.get('base_workload', 0)
            total_planned += info.get('planned_workload', 0)
    
    print(f"\n    📊 Montag 09.12.2025:")
    print(f"       Kapazität: {total_cap} AW")
    print(f"       Geplant: {total_planned} AW")
else:
    print(f"\n    Response: {result.stdout[:150]}")
