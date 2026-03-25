#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VACATION CALENDAR SERVICE - TAG 104 / Erweiterung 2026-02
- drive@: Alle Urlaube im DRIVE-Hauptkalender (für Führungskräfte sichtbar).
- Mitarbeiter-Kalender: Eintrag im persönlichen M365-Kalender (erscheint in Team-Ansicht des Vorgesetzten).
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

try:
    from dotenv import load_dotenv
    load_dotenv('/opt/greiner-portal/config/.env')
except Exception:
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
    
    def _build_event_payload(self, booking_details: dict) -> tuple:
        """Baut Subject und Event-Body für einen Urlaubstermin. Returns (subject, event_dict)."""
        date_str = booking_details.get('date', '')
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except Exception:
            return None, None
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
                'categories': [department or 'Allgemein', vacation_type or 'Urlaub'],
                'body': {'contentType': 'text', 'content': f'{vacation_type} - {employee_name} ({department}) - via DRIVE'}
            }
        else:
            event = {
                'subject': subject,
                'isAllDay': False,
                'start': {'dateTime': date_obj.strftime('%Y-%m-%dT08:00:00'), 'timeZone': 'Europe/Berlin'},
                'end': {'dateTime': date_obj.strftime('%Y-%m-%dT12:00:00'), 'timeZone': 'Europe/Berlin'},
                'showAs': 'oof',
                'categories': [department or 'Allgemein', vacation_type or 'Urlaub'],
                'body': {'contentType': 'text', 'content': f'{vacation_type} (1/2 Tag) - {employee_name} ({department}) - via DRIVE'}
            }
        return subject, event

    def add_vacation_event(self, booking_details: dict) -> Dict[str, Any]:
        """
        Erstellt Urlaubstermin in drive@ und im Mitarbeiter-Kalender (M365).
        Returns: {'drive_ok': bool, 'drive_event_id': str|None, 'employee_event_id': str|None}
        """
        result = {'drive_ok': False, 'drive_event_id': None, 'employee_event_id': None}
        subject, event = self._build_event_payload(booking_details)
        if not event:
            return result
        date_str = booking_details.get('date', '')

        # 1) drive@ (Übersicht für Führungskräfte)
        calendar_id = self._get_main_calendar_id()
        if calendar_id:
            url = f"https://graph.microsoft.com/v1.0/users/{self.calendar_mailbox}/calendars/{calendar_id}/events"
            try:
                response = requests.post(url, headers=self._get_headers(), json=event)
                response.raise_for_status()
                data = response.json()
                result['drive_ok'] = True
                result['drive_event_id'] = data.get('id')
                print(f"Kalender drive@: {subject} am {date_str}")
            except Exception as e:
                print(f"Fehler drive@ Kalender: {e}")

        # 2) Mitarbeiter-Kalender (für Team-Ansicht des Vorgesetzten)
        employee_email = (booking_details.get('employee_email') or '').strip()
        if employee_email:
            try:
                user_url = f"https://graph.microsoft.com/v1.0/users/{employee_email}/calendar/events"
                resp = requests.post(user_url, headers=self._get_headers(), json=event)
                resp.raise_for_status()
                data = resp.json()
                result['employee_event_id'] = data.get('id')
                print(f"Kalender Mitarbeiter {employee_email}: {subject} am {date_str}")
            except Exception as e:
                print(f"Fehler Mitarbeiter-Kalender {employee_email}: {e}")

        return result

    def delete_vacation_event(
        self,
        booking_details: dict,
        calendar_event_id_employee: Optional[str] = None,
        calendar_event_id_drive: Optional[str] = None
    ) -> bool:
        """
        Löscht Urlaubstermin aus drive@ und/oder Mitarbeiter-Kalender.
        Mindestens eine der Event-IDs sollte gesetzt sein (bei alten Buchungen ggf. nur drive@ per Suche).
        """
        deleted_any = False
        employee_email = (booking_details.get('employee_email') or '').strip()

        if calendar_event_id_employee and employee_email:
            try:
                url = f"https://graph.microsoft.com/v1.0/users/{employee_email}/events/{calendar_event_id_employee}"
                requests.delete(url, headers=self._get_headers())
                deleted_any = True
                print(f"Kalender Mitarbeiter: Event {calendar_event_id_employee} gelöscht")
            except Exception as e:
                print(f"Fehler Löschung Mitarbeiter-Kalender: {e}")

        if calendar_event_id_drive:
            try:
                url = f"https://graph.microsoft.com/v1.0/users/{self.calendar_mailbox}/events/{calendar_event_id_drive}"
                requests.delete(url, headers=self._get_headers())
                deleted_any = True
                print(f"Kalender drive@: Event {calendar_event_id_drive} gelöscht")
            except Exception as e:
                print(f"Fehler Löschung drive@: {e}")

        if not deleted_any and self.calendar_mailbox:
            deleted_any = self._delete_drive_event_by_date_subject(booking_details)
        return deleted_any

    def _delete_drive_event_by_date_subject(self, booking_details: dict) -> bool:
        """Fallback: Suche in drive@ nach Event an Datum mit passendem Betreff und lösche es."""
        date_str = booking_details.get('date', '')
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except Exception:
            return False
        start = date_obj.strftime('%Y-%m-%dT00:00:00')
        end = (date_obj + timedelta(days=2)).strftime('%Y-%m-%dT00:00:00')
        url = f"https://graph.microsoft.com/v1.0/users/{self.calendar_mailbox}/calendarView?startDateTime={start}&endDateTime={end}"
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            for ev in response.json().get('value', []):
                subj = (ev.get('subject') or '')
                if 'via DRIVE' in (ev.get('body', {}).get('content') or '') or '[' in subj:
                    event_id = ev.get('id')
                    if event_id:
                        del_url = f"https://graph.microsoft.com/v1.0/users/{self.calendar_mailbox}/events/{event_id}"
                        requests.delete(del_url, headers=self._get_headers())
                        print(f"Kalender drive@: Event per Suche gelöscht: {event_id}")
                        return True
        except Exception as e:
            print(f"Fehler drive@ Suche/Löschung: {e}")
        return False

    def list_calendars(self):
        url = f"https://graph.microsoft.com/v1.0/users/{self.calendar_mailbox}/calendars"
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return [{'id': c['id'], 'name': c['name']} for c in response.json().get('value', [])]
        except Exception:
            return []

    def find_vacation_events_on_date(self, user_email: str, date_str: str) -> List[Dict[str, Any]]:
        """
        Sucht an einem Datum im Kalender von user_email (oder drive@) nach Events,
        die im Body „via DRIVE“ enthalten (Urlaubseinträge von DRIVE).
        Returns: Liste von {'id': str, 'subject': str, 'body_content': str}
        """
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except Exception:
            return []
        start = date_obj.strftime('%Y-%m-%dT00:00:00')
        end = (date_obj + timedelta(days=2)).strftime('%Y-%m-%dT00:00:00')
        url = f"https://graph.microsoft.com/v1.0/users/{user_email}/calendarView?startDateTime={start}&endDateTime={end}"
        out = []
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            for ev in response.json().get('value', []):
                body = ev.get('body', {}) or {}
                body_content = (body.get('content') or '')
                if 'via DRIVE' not in body_content:
                    continue
                out.append({
                    'id': ev.get('id'),
                    'subject': ev.get('subject') or '',
                    'body_content': body_content
                })
        except Exception as e:
            print(f"Fehler Suche Kalender {user_email} am {date_str}: {e}")
        return out


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
