#!/usr/bin/env python3
"""
Debug v29 - Alles in EINEM curl-Aufruf mit --next
Oder: Verwende Python requests mit Session
"""

import requests
from urllib.parse import unquote
import json

BASE_URL = "https://werkstattplanung.net/greiner/deggendorf/kic"
USERNAME = "florian.greiner@auto-greiner.de"  
PASSWORD = "Hyundai2025!"

print("=" * 60)
print("GUDAT DEBUG v29 - Python requests mit persistenter Session")
print("=" * 60)

# Erstelle Session die Cookies automatisch verwaltet
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'Accept-Language': 'de-DE,de;q=0.9',
})

# 1. Hole initiale Cookies (OHNE Redirect folgen!)
print("\n[1] GET /kic (allow_redirects=False)...")
resp = session.get(f"{BASE_URL}", allow_redirects=False)
print(f"    Status: {resp.status_code}")
print(f"    Cookies in Session: {list(session.cookies.keys())}")

# Falls keine Cookies, versuche mit Redirect
if not session.cookies:
    print("    Keine Cookies, versuche mit Redirects...")
    resp = session.get(f"{BASE_URL}/", allow_redirects=True)
    print(f"    Status: {resp.status_code}")
    print(f"    Cookies: {list(session.cookies.keys())}")

xsrf = unquote(session.cookies.get('XSRF-TOKEN', ''))
print(f"    XSRF: {xsrf[:50]}...")

# 2. Login
print("\n[2] Login...")
resp = session.post(
    f"{BASE_URL}/login",
    json={'username': USERNAME, 'password': PASSWORD, 'remember': True},
    headers={
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-XSRF-TOKEN': xsrf,
    }
)
print(f"    Status: {resp.status_code}")
print(f"    Response: {resp.text[:80]}")
print(f"    Cookies nach Login: {list(session.cookies.keys())}")

# Neues XSRF Token
xsrf_new = unquote(session.cookies.get('XSRF-TOKEN', ''))
print(f"    Neues XSRF: {xsrf_new[:50]}...")

# 3. API Test - SOFORT in gleicher Session
print("\n[3] API Test (gleiche Session)...")
resp = session.get(
    f"{BASE_URL}/api/v1/workload_week_summary",
    params={'date': '2025-12-09', 'days': 1},
    headers={
        'Accept': 'application/json',
        'X-XSRF-TOKEN': xsrf_new,
        'x-client-version': '6.37.52',
    }
)
print(f"    Status: {resp.status_code}")
print(f"    Response: {resp.text[:150]}")

# 4. Debug: Was sendet requests eigentlich?
print("\n[4] Debug: Gesendete Cookies...")
# Bereite einen Request vor um zu sehen was gesendet wird
req = requests.Request('GET', f"{BASE_URL}/api/v1/workload_week_summary",
                       params={'date': '2025-12-09', 'days': 1},
                       headers={'Accept': 'application/json', 'X-XSRF-TOKEN': xsrf_new})
prepared = session.prepare_request(req)
print(f"    Cookie Header: {prepared.headers.get('Cookie', 'NONE')[:100]}...")

# 5. Vergleiche: Session-Cookie VOR und NACH Login
print("\n[5] Session-Cookie Analyse...")
for cookie in session.cookies:
    print(f"    {cookie.name}:")
    print(f"      Domain: {cookie.domain}")
    print(f"      Path: {cookie.path}")
    print(f"      Secure: {cookie.secure}")
    print(f"      Value: {cookie.value[:30]}...")

# 6. Test: Manueller Cookie-Header statt Session
print("\n[6] Test: Manueller Cookie-Header...")
cookie_str = '; '.join([f"{c.name}={c.value}" for c in session.cookies])
resp = requests.get(
    f"{BASE_URL}/api/v1/workload_week_summary",
    params={'date': '2025-12-09', 'days': 1},
    headers={
        'Accept': 'application/json',
        'X-XSRF-TOKEN': xsrf_new,
        'Cookie': cookie_str,
        'User-Agent': 'Mozilla/5.0',
    }
)
print(f"    Status: {resp.status_code}")
print(f"    Response: {resp.text[:100]}")

if resp.status_code == 200 and 'base_workload' in resp.text:
    data = resp.json()
    print(f"\n    ✅✅✅ ERFOLG! {len(data)} Teams ✅✅✅")
