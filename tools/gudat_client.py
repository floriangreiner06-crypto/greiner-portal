#!/usr/bin/env python3
"""
=============================================================================
GREINER DRIVE - Gudat Werkstattplanung API Client
=============================================================================
Client für die werkstattplanung.net API (Gudat "Digitales Autohaus")

WICHTIG: Der Login-Flow benötigt einen Aufruf von /ack nach dem Login
um den laravel_token Cookie zu erhalten!

Flow:
1. GET /kic → Initiale Cookies
2. POST /login → Login
3. GET /ack → laravel_token Cookie (KRITISCH!)
4. GET /api/v1/* → API Calls

Autor: Claude AI für Greiner Portal  
Version: 2.1 (TAG 97 - Cookie-Parsing gefixt)
Datum: 2025-12-06
"""

import requests
import json
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from urllib.parse import unquote

logger = logging.getLogger(__name__)


class GudatClient:
    """
    Client für die Gudat Werkstattplanung API
    
    Usage:
        client = GudatClient(username, password)
        if client.login():
            data = client.get_workload_summary('2025-12-09')
            print(data)
    """
    
    BASE_URL = "https://werkstattplanung.net/greiner/deggendorf/kic"
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._logged_in = False
        
    def _get_xsrf(self) -> str:
        """Extrahiert und decoded den XSRF-Token aus den Session-Cookies"""
        xsrf = self.session.cookies.get('XSRF-TOKEN', '')
        return unquote(xsrf)
    
    def login(self) -> bool:
        """
        Führt den kompletten Login-Flow durch:
        1. Initiale Cookies holen
        2. Login POST
        3. /ack aufrufen für laravel_token
        
        Returns:
            True wenn erfolgreich
        """
        try:
            # 1. Initiale Cookies holen
            logger.info("Hole initiale Cookies...")
            response = self.session.get(f"{self.BASE_URL}", allow_redirects=False)
            
            logger.debug(f"Initiale Cookies: {list(self.session.cookies.keys())}")
            
            if 'XSRF-TOKEN' not in self.session.cookies:
                logger.error("Kein XSRF-TOKEN erhalten!")
                return False
            
            # 2. Login
            logger.info("Führe Login durch...")
            response = self.session.post(
                f"{self.BASE_URL}/login",
                json={
                    'username': self.username,
                    'password': self.password,
                    'remember': True
                },
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-XSRF-TOKEN': self._get_xsrf()
                }
            )
            
            if response.status_code != 201:
                logger.error(f"Login fehlgeschlagen: {response.status_code} - {response.text}")
                return False
            
            login_data = response.json()
            logger.info(f"Login erfolgreich: UserId={login_data.get('UserId')}")
            
            # 3. KRITISCH: /ack aufrufen für laravel_token!
            logger.info("Hole laravel_token via /ack...")
            response = self.session.get(
                f"{self.BASE_URL}/ack",
                headers={
                    'Accept': 'application/json',
                    'X-XSRF-TOKEN': self._get_xsrf()
                }
            )
            
            if 'laravel_token' not in self.session.cookies:
                logger.warning("laravel_token nicht erhalten - API-Calls könnten fehlschlagen!")
            else:
                logger.info("laravel_token erhalten!")
            
            self._logged_in = True
            logger.info(f"Login komplett. Cookies: {list(self.session.cookies.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"Login-Fehler: {e}")
            return False
    
    def _api_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Führt einen API-Request durch"""
        headers = kwargs.pop('headers', {})
        headers.setdefault('Accept', 'application/json')
        headers['X-XSRF-TOKEN'] = self._get_xsrf()
        
        url = f"{self.BASE_URL}{endpoint}"
        return self.session.request(method, url, headers=headers, **kwargs)
    
    def get_workload_raw(self, date: str = None, days: int = 7) -> List[Dict]:
        """
        Holt rohe Workload-Daten von der API
        
        Args:
            date: Startdatum (YYYY-MM-DD), default: heute
            days: Anzahl Tage (1-14)
            
        Returns:
            Liste der Team-Workload-Daten
        """
        if not self._logged_in:
            if not self.login():
                return []
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        response = self._api_request(
            'GET',
            '/api/v1/workload_week_summary',
            params={'date': date, 'days': days}
        )
        
        if response.status_code != 200:
            logger.error(f"API-Fehler: {response.status_code} - {response.text}")
            return []
        
        return response.json()
    
    def get_workload_summary(self, date: str = None) -> Dict[str, Any]:
        """
        Holt zusammengefasste Kapazitätsdaten für einen Tag
        
        Args:
            date: Datum (YYYY-MM-DD), default: heute
            
        Returns:
            Dict mit Kapazitäts-Zusammenfassung
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        raw_data = self.get_workload_raw(date, days=2)
        
        if not raw_data:
            return {'error': 'Keine Daten erhalten', 'date': date}
        
        # Aggregiere Daten
        total_capacity = 0
        total_planned = 0
        total_absent = 0
        total_free = 0
        teams = []
        
        for team in raw_data:
            team_name = team.get('name', 'Unknown')
            category = team.get('category_name', 'Unknown')
            team_id = team.get('id')
            
            # Finde Daten für das Datum
            day_data = team.get('data', {}).get(date)
            if not day_data:
                # Versuche nächsten Tag (falls Wochenende)
                next_day = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                day_data = team.get('data', {}).get(next_day)
            
            if not day_data:
                continue
            
            cap = day_data.get('base_workload', 0)
            planned = day_data.get('planned_workload', 0)
            absent = day_data.get('absence_workload', 0)
            free = day_data.get('free_workload', 0)
            plannable = day_data.get('plannable_workload', 0)
            
            total_capacity += cap
            total_planned += planned
            total_absent += absent
            total_free += free
            
            # Status pro Team
            if free < 0:
                status = 'overloaded'
            elif cap > 0 and free < cap * 0.1:
                status = 'warning'
            else:
                status = 'ok'
            
            teams.append({
                'id': team_id,
                'name': team_name,
                'category': category,
                'capacity': cap,
                'planned': planned,
                'absent': absent,
                'free': free,
                'plannable': plannable,
                'utilization': round(planned / cap * 100, 1) if cap > 0 else 0,
                'status': status,
            })
        
        # Gesamt-Status
        if total_free < 0:
            overall_status = 'overloaded'
        elif total_capacity > 0 and total_free < total_capacity * 0.1:
            overall_status = 'warning'
        else:
            overall_status = 'ok'
        
        utilization = round(total_planned / total_capacity * 100, 1) if total_capacity > 0 else 0
        
        return {
            'date': date,
            'total_capacity': total_capacity,
            'planned': total_planned,
            'absent': total_absent,
            'free': total_free,
            'utilization_percent': utilization,
            'status': overall_status,
            'teams': sorted(teams, key=lambda x: x['free']),  # Kritischste zuerst
            'teams_count': len(teams),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_week_overview(self, start_date: str = None) -> Dict[str, Any]:
        """
        Holt Wochen-Übersicht für 7 Tage
        
        Args:
            start_date: Startdatum (YYYY-MM-DD), default: heute
            
        Returns:
            Dict mit täglichen Summaries
        """
        if start_date is None:
            start_date = datetime.now().strftime('%Y-%m-%d')
        
        raw_data = self.get_workload_raw(start_date, days=7)
        
        if not raw_data:
            return {'error': 'Keine Daten erhalten'}
        
        # Sammle alle Daten
        all_dates = set()
        for team in raw_data:
            all_dates.update(team.get('data', {}).keys())
        
        days = []
        for date in sorted(all_dates):
            total_cap = 0
            total_planned = 0
            total_free = 0
            
            for team in raw_data:
                day_data = team.get('data', {}).get(date)
                if day_data:
                    total_cap += day_data.get('base_workload', 0)
                    total_planned += day_data.get('planned_workload', 0)
                    total_free += day_data.get('free_workload', 0)
            
            if total_cap > 0:
                status = 'overloaded' if total_free < 0 else ('warning' if total_free < total_cap * 0.1 else 'ok')
                days.append({
                    'date': date,
                    'weekday': datetime.strptime(date, '%Y-%m-%d').strftime('%A'),
                    'capacity': total_cap,
                    'planned': total_planned,
                    'free': total_free,
                    'utilization': round(total_planned / total_cap * 100, 1),
                    'status': status
                })
        
        return {
            'start_date': start_date,
            'days': days,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_current_user(self) -> Dict[str, Any]:
        """Holt aktuelle Benutzer-Informationen"""
        if not self._logged_in:
            if not self.login():
                return {'error': 'Nicht eingeloggt'}
        
        response = self._api_request('GET', '/api/v1/user')
        
        if response.status_code != 200:
            return {'error': f'API-Fehler: {response.status_code}'}
        
        return response.json()


# =============================================================================
# Singleton-Instanz für einfachen Zugriff
# =============================================================================
_client_instance: Optional[GudatClient] = None

def get_client(username: str = None, password: str = None) -> GudatClient:
    """
    Holt oder erstellt eine Gudat-Client-Instanz
    
    Bei erstem Aufruf müssen username/password angegeben werden.
    Danach wird die bestehende Instanz zurückgegeben.
    """
    global _client_instance
    
    if _client_instance is None:
        if username is None or password is None:
            raise ValueError("Username und Password müssen beim ersten Aufruf angegeben werden")
        _client_instance = GudatClient(username, password)
    
    return _client_instance


# =============================================================================
# CLI für Tests
# =============================================================================
if __name__ == '__main__':
    import sys
    
    # Logging einschalten
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    USERNAME = "florian.greiner@auto-greiner.de"
    PASSWORD = "Hyundai2025!"
    
    print("=" * 60)
    print("GUDAT CLIENT TEST v2.1")
    print("=" * 60)
    
    client = GudatClient(USERNAME, PASSWORD)
    
    if client.login():
        print("\n✅ Login erfolgreich!")
        print(f"   Cookies: {list(client.session.cookies.keys())}")
        
        # Tages-Summary
        print("\n" + "-" * 40)
        print("TAGES-ÜBERSICHT (Montag 09.12.)")
        print("-" * 40)
        
        summary = client.get_workload_summary('2025-12-09')
        
        if 'error' not in summary:
            print(f"\n📊 Kapazität: {summary['total_capacity']} AW")
            print(f"📋 Geplant: {summary['planned']} AW ({summary['utilization_percent']}%)")
            print(f"🏖️ Abwesend: {summary['absent']} AW")
            print(f"✨ Frei: {summary['free']} AW")
            
            status_icons = {'ok': '🟢', 'warning': '🟡', 'overloaded': '🔴'}
            print(f"\nStatus: {status_icons.get(summary['status'], '❓')} {summary['status'].upper()}")
            
            print(f"\n📋 Teams ({summary['teams_count']}):")
            for team in summary['teams'][:5]:
                icon = status_icons.get(team['status'], '❓')
                print(f"  {icon} {team['name']}: {team['free']} AW frei ({team['utilization']}%)")
        else:
            print(f"❌ Fehler: {summary['error']}")
        
        # Wochen-Übersicht
        print("\n" + "-" * 40)
        print("WOCHEN-ÜBERSICHT")
        print("-" * 40)
        
        week = client.get_week_overview('2025-12-09')
        
        if 'error' not in week:
            for day in week['days']:
                icon = status_icons.get(day['status'], '❓')
                weekday = day['weekday'][:3]
                print(f"  {icon} {day['date']} ({weekday}): {day['free']:>5} AW frei ({day['utilization']:>5.1f}%)")
    else:
        print("\n❌ Login fehlgeschlagen!")
        sys.exit(1)
