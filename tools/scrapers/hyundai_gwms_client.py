#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai GWMS API Client v2
===========================
Korrigiertes SSV-Format basierend auf HAR-Analyse

Version: 2.0
Erstellt: 2025-12-04
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

# ============================================================================
# KONFIGURATION
# ============================================================================

CCC_URL = "https://ccc.hyundai.com"
GWMS_URL = "https://gwms.hyundaicdn.com"

USERNAME = "david.moser@auto-greiner.de"
PASSWORD = "LuisaSandra092025!!"

OUTPUT_DIR = Path("/opt/greiner-portal/data/hyundai_ccc")

# ============================================================================
# SSV FORMAT BUILDER
# ============================================================================

def build_ssv_login_body(username, password, lang='DE'):
    """
    Baut den korrekten SSV-Body für Login
    
    Format aus HAR:
    SSV:utf-8
    [cookies...]
    Dataset:ds_cond
    _RowType_[field definitions]
    U[field values]
    O[field values]
    """
    
    # Record Separator
    RS = '\x1e'
    # Unit Separator  
    US = '\x1f'
    
    parts = [
        "SSV:utf-8",
        # Dummy Session Cookie (wird vom Server ignoriert aber erwartet)
        "jsession123=testsatAAAAA_AAADAS",
        # Dataset Definition
        "Dataset:ds_cond",
        # Spalten-Definition
        f"_RowType_{US}id:STRING(256){US}bbn:STRING(256){US}langCd:STRING(256){US}usId:STRING(256){US}code:STRING(256)",
        # Update Row mit Credentials
        f"U{US}{username}{US}{password}{US}{lang}{US}\x03{US}\x03",
        # Original Row
        f"O{US}User:   {username}{US}{password}{US}{lang}{US}\x03{US}\x03",
        "",
        ""
    ]
    
    return RS.join(parts)


def build_ssv_otp_body(username, password, otp_code, lang='DE'):
    """Baut SSV-Body für 2FA Verifizierung"""
    
    RS = '\x1e'
    US = '\x1f'
    
    parts = [
        "SSV:utf-8",
        "jsession123=testsatAAAAA_AAADAS",
        "Dataset:ds_cond",
        f"_RowType_{US}id:STRING(256){US}bbn:STRING(256){US}langCd:STRING(256){US}usId:STRING(256){US}code:STRING(256){US}otpCd:STRING(256)",
        f"U{US}{username}{US}{password}{US}{lang}{US}\x03{US}\x03{US}{otp_code}",
        f"O{US}User:   {username}{US}{password}{US}{lang}{US}\x03{US}\x03{US}",
        "",
        ""
    ]
    
    return RS.join(parts)


# ============================================================================
# GWMS CLIENT
# ============================================================================

class GWMSClient:
    """Client für GWMS API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'application/xml, text/xml, */*',
            'Accept-Language': 'de,de-DE;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache, no-store',
            'Pragma': 'no-cache',
            'Origin': CCC_URL,
            'Referer': f'{CCC_URL}/nxui/ccc/index.html',
            'X-Requested-With': 'XMLHttpRequest',
        })
        self.authenticated = False
    
    def login(self, otp_code=None):
        """Login mit korrektem SSV-Format"""
        
        print("="*60)
        print("🔐 CCC/GWMS LOGIN")
        print("="*60)
        
        if not otp_code:
            # Step 1: Initial Login
            print("\n1️⃣ Sende Login-Request...")
            
            body = build_ssv_login_body(USERNAME, PASSWORD)
            
            # Debug: Body anzeigen
            print(f"\n   Body (erste 200 Zeichen): {repr(body[:200])}")
            
            response = self.session.post(
                f"{CCC_URL}/login/selectUserLogin.do",
                data=body.encode('utf-8'),
                headers={'Content-Type': 'text/xml'}
            )
            
            print(f"\n   Status: {response.status_code}")
            print(f"   Response: {repr(response.text[:200])}")
            
            if '2FA_OTP_USER' in response.text:
                print("\n   📱 2FA erforderlich!")
                
                # OTP Timeout abfragen
                otp_resp = self.session.post(
                    f"{CCC_URL}/login/select2FAOtpLimitTime.do",
                    data=body.encode('utf-8'),
                    headers={'Content-Type': 'text/xml'}
                )
                print(f"   OTP Timeout: {otp_resp.text}")
                
                return {'status': '2fa_required'}
            
            elif 'ErrorCode:int=0' in response.text:
                print("\n   ✅ Login erfolgreich (kein 2FA)")
                self.authenticated = True
                return {'status': 'success'}
            
            else:
                print(f"\n   ❌ Unerwartete Response")
                return {'status': 'error', 'response': response.text}
        
        else:
            # Step 2: Mit OTP einloggen
            print(f"\n2️⃣ Sende 2FA-Code: {otp_code}")
            
            body = build_ssv_otp_body(USERNAME, PASSWORD, otp_code)
            
            response = self.session.post(
                f"{CCC_URL}/login/checkGoogleCode.do",
                data=body.encode('utf-8'),
                headers={'Content-Type': 'text/xml'}
            )
            
            print(f"\n   Status: {response.status_code}")
            print(f"   Response (erste 300): {response.text[:300]}")
            
            if 'ErrorCode:int=0' in response.text:
                print("\n   ✅ 2FA erfolgreich!")
                self.authenticated = True
                
                # Step 3: SSO für GWMS
                print("\n3️⃣ Hole SSO Token für GWMS...")
                
                # Erst die globalen Datasets laden
                self.session.post(
                    f"{CCC_URL}/login/selectLoginGlobalDataset.do",
                    data=body.encode('utf-8'),
                    headers={'Content-Type': 'text/xml'}
                )
                
                # SSO aufrufen
                sso_resp = self.session.get(
                    f"{CCC_URL}/common/login/sso.do",
                    allow_redirects=True
                )
                print(f"   SSO Final URL: {sso_resp.url[:60]}...")
                
                # Cookies anzeigen
                print(f"\n   🍪 Cookies: {dict(self.session.cookies)}")
                
                return {'status': 'success'}
            else:
                return {'status': 'error', 'message': 'OTP ungültig oder abgelaufen'}
    
    def search_vin(self, vin):
        """VIN im GWMS suchen"""
        
        if len(vin) != 17:
            return {'error': 'VIN muss 17 Zeichen haben'}
        
        print(f"\n🔍 Suche VIN: {vin}")
        
        # Zuerst GWMS Startseite aufrufen (für Session)
        self.session.get(
            f"{GWMS_URL}/jsp_html5/w400_basic_data/w400_0980/W400_0980.jsp",
            params={
                'dep1Val': '400',
                'dep2Val': '400', 
                'dep1Index': '1',
                'dep2Index': '1',
                'dep3Index': '0',
                'screenID': 'W400_0980'
            }
        )
        
        # VIN aufteilen
        vin_prefix = vin[:11]
        vin_suffix = vin[11:]
        
        # Servlet aufrufen
        data = {
            'gubun': 'search',
            'KEY_VHL001_DIST_CD': 'ALL',
            'KEY_VHL001_PLNT_CD': 'ALL',
            'KEY_VHL001_VIN_NO': vin_prefix,
            'KEY_VHL001_VIN_SRL': vin_suffix,
            'currPage': '1',
            'pageRow': '10',
            'screenID': 'W400_0980'
        }
        
        response = self.session.post(
            f"{GWMS_URL}/servlet/hkmc.gwms.w400_basic_data.w400_0980.W400_0980_Servlet",
            data=urlencode(data),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8;',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Origin': GWMS_URL,
                'Referer': f"{GWMS_URL}/jsp_html5/w400_basic_data/w400_0980/W400_0980.jsp",
                'X-Requested-With': 'XMLHttpRequest',
            }
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                return self._parse_vin_response(result)
            except:
                return {'error': 'Keine gültige JSON-Response', 'raw': response.text[:500]}
        else:
            return {'error': f'HTTP {response.status_code}'}
    
    def _parse_vin_response(self, data):
        """Parst VIN-Response"""
        
        if not data or not data[0].get('Table0'):
            return {'error': 'Keine Daten'}
        
        v = data[0]['Table0'][0]
        
        def fmt_date(d):
            if d and len(d) == 8:
                return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
            return d
        
        return {
            'vin': v.get('VHL001_VIN_NO'),
            'model': v.get('VHL001_LTS_MDL_NM'),
            'model_code': v.get('VHL001_LTS_MDL_CD'),
            'license_plate': v.get('VHL001_REGST_NO'),
            'warranty_start': fmt_date(v.get('VHL001_WARR_START_DT')),
            'sale_date': fmt_date(v.get('VHL001_RETL_SALE_DT')),
            'ship_date': fmt_date(v.get('VHL001_SHIP_DT')),
            'distributor': v.get('VHL001_DIST_CD2_NM'),
            'warnings': [
                {'code': w.get('VAL2'), 'text': w.get('VAL3')} 
                for w in v.get('VT_SPECIALVIN', [])
            ],
            'open_campaigns': v.get('VT_OPENCAMPAIGN', []),
            'vin_blocks': v.get('VT_BLOCKVIN', []),
            'free_services': v.get('VT_FREESERVICE', []),
        }
    
    def print_result(self, data):
        """Gibt Ergebnis formatiert aus"""
        
        if 'error' in data:
            print(f"\n❌ {data['error']}")
            if 'raw' in data:
                print(f"   Raw: {data['raw']}")
            return
        
        print(f"""
{'='*60}
🚗 FAHRZEUG: {data.get('vin')}
{'='*60}
   Modell:          {data.get('model')}
   Kennzeichen:     {data.get('license_plate')}
   Garantie-Start:  {data.get('warranty_start')}
   Verkauf:         {data.get('sale_date')}
   Importeur:       {data.get('distributor')}
        """)
        
        if data.get('warnings'):
            print("⚠️  WARNUNGEN:")
            for w in data['warnings']:
                print(f"   • [{w['code']}] {w['text']}")
        
        if data.get('open_campaigns'):
            print("\n📢 OFFENE CAMPAIGNS:")
            for c in data['open_campaigns']:
                print(f"   • {c}")
        else:
            print("\n✅ Keine offenen Campaigns")
        
        if data.get('vin_blocks'):
            print("\n🚫 VIN-SPERREN:")
            for b in data['vin_blocks']:
                print(f"   • {b}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*60)
    print("  🚗 HYUNDAI GWMS CLIENT v2")
    print("="*60)
    print(f"  User: {USERNAME}")
    print("="*60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    client = GWMSClient()
    
    # Login Step 1
    result = client.login()
    
    if result['status'] == '2fa_required':
        print("\n" + "="*60)
        otp = input("  📱 2FA-Code eingeben: ").strip()
        result = client.login(otp_code=otp)
    
    if result['status'] != 'success':
        print(f"\n❌ Login fehlgeschlagen: {result}")
        return 1
    
    print("\n✅ Login erfolgreich!")
    
    # VIN-Suche Loop
    while True:
        print("\n" + "-"*60)
        vin = input("VIN eingeben (q=Ende): ").strip().upper()
        
        if vin.lower() == 'q':
            break
        
        if len(vin) != 17:
            print("❌ VIN muss 17 Zeichen haben!")
            continue
        
        data = client.search_vin(vin)
        client.print_result(data)
        
        # Speichern
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fp = OUTPUT_DIR / f"vin_{vin}_{ts}.json"
        with open(fp, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 {fp}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
