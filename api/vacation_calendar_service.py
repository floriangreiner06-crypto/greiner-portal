#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VACATION CALENDAR SERVICE - TAG 104
Alle Urlaube im DRIVE-Hauptkalender mit Format: [Abteilung] Name
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List

try:
    from dotenv import load_dotenv
    load_dotenv('/opt/greiner-portal/config/.env')
except:
    pass


class VacationCalendarService:
    def __init__(self):
        self.tenant_id = os.getenv('GRAPH_TENANT_ID')
        self.client_id = os.getenv('GRAPH_CLIENT_ID')
        self.client_secret = os.getenv('GRAPH_CLIENT_SECRET')
        self.calendar_mailbox = os.getenv('CALENDAR_MAILBOX', 'drive@auto-greiner.de')
        self._access_token = None
        self._token_expires = None
        self._main_calendar_id = None
    
    def _get_token(self):
        if self._access_token and self._token_expires and datetime.now() < self._token_expires:
            return self._access_token
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        token_data = response.json()
        self._access_token = token_data['access_token']
        self._token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'] - 300)
        return self._access_token
    
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self._get_token()}',
            'Content-Type': 'application/json'
        }
    
    def _get_main_calendar_id(self):
        if self._main_calendar_id:
            return self._main_calendar_id
        url = f"https://graph.microsoft.com/v1.0/users/{self.calendar_mailbox}/calendars"
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            for cal in response.json().get('value', []):
                if cal['name'] == 'Calendar':
                    self._main_calendar_id = cal['id']
                    return self._main_calendar_id
        except Exception as e:
            print(f"Fehler: {e}")
        return None
    
    def add_vacation_event(self, booking_details):
        calendar_id = self._get_main_calendar_id()
        if not calendar_id:
            return False
        
        date_str = booking_details.get('date', '')
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return False
        
        employee_name = booking_details.get('employee_name', 'Unbekannt')
        vacation_type = booking_details.get('vacation_type', 'Urlaub')
        department = booking_details.get('department', 'Allgemein')
        day_part = booking_details.get('day_part', 'full')
        
        type_icons = {
            'Urlaub': '🏖️', 'Zeitausgleich': '⏰', 'Krankheit': '🤒',
            'Schulung': '📚', 'Sonderurlaub': '👶', 'Arzttermin': '🏥'
        }
        icon = type_icons.get(vacation_type, '📅')
        
        subject = f"{icon} [{department}] {employee_name}"
        if vacation_type not in ['Urlaub', None, '']:
            subject = f"{icon} [{department}] {employee_name} ({vacation_type})"
        if day_part == 'half':
            subject += " (1/2 Tag)"
        
        if day_part == 'full':
            event = {
                'subject': subject,
                'isAllDay': True,
                'start': {'dateTime': date_obj.strftime('%Y-%m-%dT00:00:00'), 'timeZone': 'Europe/Berlin'},
                'end': {'dateTime': (date_obj + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00'), 'timeZone': 'Europe/Berlin'},
                'showAs': 'oof',
                'categories': [department, vacation_type],
                'body': {'contentType': 'text', 'content': f'{vacation_type} - {employee_name} ({department}) - via DRIVE'}
            }
        else:
            event = {
                'subject': subject,
                'isAllDay': False,
                'start': {'dateTime': date_obj.strftime('%Y-%m-%dT08:00:00'), 'timeZone': 'Europe/Berlin'},
                'end': {'dateTime': date_obj.strftime('%Y-%m-%dT12:00:00'), 'timeZone': 'Europe/Berlin'},
                'showAs': 'oof',
                'categories': [department, vacation_type],
                'body': {'contentType': 'text', 'content': f'{vacation_type} (1/2 Tag) - {employee_name} ({department}) - via DRIVE'}
            }
        
        url = f"https://graph.microsoft.com/v1.0/users/{self.calendar_mailbox}/calendars/{calendar_id}/events"
        try:
            response = requests.post(url, headers=self._get_headers(), json=event)
            response.raise_for_status()
            print(f"Kalendereintrag erstellt: {subject} am {date_str}")
            return True
        except Exception as e:
            print(f"Fehler: {e}")
            return False
    
    def list_calendars(self):
        url = f"https://graph.microsoft.com/v1.0/users/{self.calendar_mailbox}/calendars"
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return [{'id': c['id'], 'name': c['name']} for c in response.json().get('value', [])]
        except:
            return []


if __name__ == '__main__':
    import sys
    svc = VacationCalendarService()
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("Test: Kalendereintrag erstellen...")
        svc.add_vacation_event({
            'date': '2025-12-23',
            'day_part': 'full',
            'vacation_type': 'Urlaub',
            'employee_name': 'Max Mustermann',
            'department': 'Verkauf'
        })
