#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill: calendar_event_id_drive und calendar_event_id_employee für bestehende
genehmigte Urlaubsbuchungen nachtragen.

Liest in drive@ und im Mitarbeiter-Kalender die Events am Buchungsdatum,
findet Einträge mit „via DRIVE“ im Body und passendem Betreff und speichert
die Graph-Event-IDs in vacation_bookings. Danach funktioniert Storno-Löschung
auch für ältere Buchungen.

Verwendung:
  cd /opt/greiner-portal
  python3 scripts/backfill_vacation_calendar_event_ids.py [--dry-run] [--ab=2026-01-01]

  --dry-run     Keine DB-Updates, nur ausgeben was gefunden würde
  --ab=YYYY-MM  Nur Buchungen ab diesem Datum (Default: alle mit fehlender ID)
"""

import os
import sys
import argparse
from datetime import datetime

# Projekt-Root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv('/opt/greiner-portal/config/.env')
except Exception:
    pass

from api.db_utils import db_session
from api.db_connection import convert_placeholders, sql_placeholder


def build_expected_subject(booking: dict) -> str:
    """Erzeugt den Betreff wie ihn vacation_calendar_service verwendet."""
    vacation_type = booking.get('vacation_type') or 'Urlaub'
    department = booking.get('department') or 'Allgemein'
    employee_name = booking.get('employee_name') or 'Unbekannt'
    day_part = booking.get('day_part') or 'full'
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
    return subject


def main():
    parser = argparse.ArgumentParser(description='Backfill Kalender-Event-IDs für Urlaubsbuchungen')
    parser.add_argument('--dry-run', action='store_true', help='Keine DB-Updates')
    parser.add_argument('--ab', default=None, metavar='YYYY-MM-DD', help='Nur Buchungen ab diesem Datum')
    args = parser.parse_args()

    try:
        from api.vacation_calendar_service import VacationCalendarService
    except Exception as e:
        print(f"Fehler: VacationCalendarService nicht ladbar: {e}")
        return 1

    svc = VacationCalendarService()
    calendar_mailbox = os.getenv('CALENDAR_MAILBOX', 'drive@auto-greiner.de')

    with db_session() as conn:
        cursor = conn.cursor()
        # Genehmigte Buchungen, bei denen mindestens eine Event-ID fehlt
        query = f"""
            SELECT
                vb.id,
                vb.booking_date,
                vb.day_part,
                COALESCE(vt.name, 'Urlaub') as vacation_type,
                e.first_name || ' ' || e.last_name as employee_name,
                COALESCE(e.department_name, '') as department,
                e.email as employee_email,
                vb.calendar_event_id_drive,
                vb.calendar_event_id_employee
            FROM vacation_bookings vb
            JOIN employees e ON vb.employee_id = e.id
            LEFT JOIN vacation_types vt ON vb.vacation_type_id = vt.id
            WHERE vb.status = 'approved'
              AND (vb.calendar_event_id_drive IS NULL OR vb.calendar_event_id_employee IS NULL)
        """
        params = []
        if args.ab:
            query += f" AND vb.booking_date >= {sql_placeholder()}"
            params.append(args.ab)
        query = convert_placeholders(query)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

    if not rows:
        print("Keine genehmigten Buchungen mit fehlender Event-ID gefunden.")
        return 0

    print(f"Gefunden: {len(rows)} Buchungen mit fehlender Event-ID.")

    to_update = []  # (booking_id, drive_id or None, employee_id or None, need_drive, need_employee)
    for row in rows:
        booking_id = row[0]
        date_str = row[1].strftime('%Y-%m-%d') if hasattr(row[1], 'strftime') else str(row[1])
        day_part = row[2] or 'full'
        vacation_type = row[3] or 'Urlaub'
        employee_name = row[4] or 'Unbekannt'
        department = row[5] or ''
        employee_email = (row[6] or '').strip()
        need_drive = row[7] is None
        need_employee = row[8] is None and bool(employee_email)

        booking = {
            'date': date_str,
            'day_part': day_part,
            'vacation_type': vacation_type,
            'employee_name': employee_name,
            'department': department,
        }
        expected_subject = build_expected_subject(booking)

        drive_id = None
        employee_id = None

        if need_drive and calendar_mailbox:
            events = svc.find_vacation_events_on_date(calendar_mailbox, date_str)
            for ev in events:
                if ev.get('subject') == expected_subject:
                    drive_id = ev.get('id')
                    break
            if not drive_id and events:
                for ev in events:
                    if employee_name in (ev.get('subject') or ''):
                        drive_id = ev.get('id')
                        break

        if need_employee and employee_email:
            events = svc.find_vacation_events_on_date(employee_email, date_str)
            for ev in events:
                if ev.get('subject') == expected_subject:
                    employee_id = ev.get('id')
                    break
            if not employee_id and events:
                for ev in events:
                    if employee_name in (ev.get('subject') or '') or 'via DRIVE' in (ev.get('body_content') or ''):
                        employee_id = ev.get('id')
                        break

        if drive_id or employee_id:
            to_update.append((booking_id, drive_id if need_drive else None, employee_id if need_employee else None, need_drive, need_employee))
            print(f"  Buchung {booking_id} {date_str} {employee_name}: drive={bool(drive_id)} mitarbeiter={bool(employee_id)}")
        else:
            print(f"  Buchung {booking_id} {date_str} {employee_name}: keine passenden Events gefunden")

    updated_drive = sum(1 for u in to_update if u[1])
    updated_employee = sum(1 for u in to_update if u[2])

    if to_update and not args.dry_run:
        with db_session() as conn:
            cur = conn.cursor()
            for booking_id, drive_id, employee_id, need_drive, need_employee in to_update:
                if drive_id and need_drive:
                    cur.execute(
                        "UPDATE vacation_bookings SET calendar_event_id_drive = %s WHERE id = %s",
                        (drive_id, booking_id)
                    )
                if employee_id and need_employee:
                    cur.execute(
                        "UPDATE vacation_bookings SET calendar_event_id_employee = %s WHERE id = %s",
                        (employee_id, booking_id)
                    )
            conn.commit()

    print(f"\nFertig. Aktualisiert: drive@ {updated_drive}, Mitarbeiter {updated_employee}.")
    if args.dry_run:
        print("(Dry-Run – keine Änderungen geschrieben)")
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
