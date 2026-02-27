#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
AD DEPARTMENT SYNC - TAG 113 (PostgreSQL)
========================================
Synchronisiert Abteilungen aus Active Directory in employees-Tabelle.

Nutzt das AD 'department' Attribut DIREKT (1:1, kein Mapping).
DB: PostgreSQL (drive_portal) über api.db_utils.db_session.
Kein SQLite – siehe docs/NO_SQLITE.md.

Features:
- Liest department-Attribut aus AD für jeden Mitarbeiter
- Aktualisiert employees.department_name
- Loggt alle Änderungen

Ausführung:
- Manuell: python3 scripts/sync/sync_ad_departments.py
- Celery: sync_ad_departments Task

Author: Claude AI
Created: 2025-12-11 (TAG 113)
Updated: 2026-02-25 (PostgreSQL-only, kein SQLite)
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Logging Setup
LOG_DIR = Path('/opt/greiner-portal/logs')
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'ad_department_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

sys.path.insert(0, '/opt/greiner-portal')


def main():
    """Hauptfunktion für AD Department Sync (PostgreSQL)."""
    print("=" * 70)
    print("🔐 AD DEPARTMENT SYNC (PostgreSQL)")
    print(f"   Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    try:
        from auth.ldap_connector import LDAPConnector
        from api.db_utils import db_session

        # LDAP Verbindung
        print("\n🔌 Verbinde zu Active Directory...")
        ldap = LDAPConnector()
        conn_ldap = ldap._get_service_connection()
        print("  ✅ LDAP-Verbindung hergestellt")

        # PostgreSQL über db_session (kein SQLite)
        print("\n📊 Verbinde zu PostgreSQL (drive_portal)...")
        with db_session() as conn:
            cursor = conn.cursor()
            # Aktiv = true (PostgreSQL); locosoft_id für Mapping-Anlage
            cursor.execute("""
                SELECT e.id, e.email, e.first_name, e.last_name, e.department_name,
                       COALESCE(e.locosoft_id, 0), lem.ldap_username
                FROM employees e
                LEFT JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
                WHERE e.aktiv = true AND e.email IS NOT NULL
            """)
            employees = cursor.fetchall()

            print(f"\n👥 Prüfe {len(employees)} Mitarbeiter gegen AD...")
            print("-" * 70)

            updated = 0
            unchanged = 0
            not_found = 0
            mapping_created = 0  # neu: Mapping angelegt, wenn per E-Mail-Prefix gefunden
            errors = []
            changes = []

            for emp_id, email, first_name, last_name, current_dept, locosoft_id, ldap_username in employees:
                username = ldap_username if ldap_username else (email.split('@')[0] if email else None)
                if not username:
                    continue

                try:
                    conn_ldap.search(
                        search_base=ldap.config['LDAP_BASE_DN'],
                        search_filter=f'(sAMAccountName={username})',
                        attributes=['department']
                    )

                    if conn_ldap.entries:
                        entry = conn_ldap.entries[0]
                        ad_dept = str(entry.department) if hasattr(entry, 'department') and entry.department else None

                        # Wenn wir den MA per E-Mail-Prefix gefunden haben (ohne Mapping): Mapping anlegen,
                        # damit "kein AD" im Urlaubsplaner verschwindet (konsistent mit sync_ldap_employees_pg).
                        if not ldap_username:
                            cursor.execute(
                                "SELECT id FROM ldap_employee_mapping WHERE employee_id = %s",
                                (emp_id,)
                            )
                            existing = cursor.fetchone()
                            if existing:
                                cursor.execute(
                                    "UPDATE ldap_employee_mapping SET ldap_username = %s, ldap_email = %s, locosoft_id = %s WHERE employee_id = %s",
                                    (username, email, locosoft_id, emp_id)
                                )
                            else:
                                cursor.execute(
                                    "INSERT INTO ldap_employee_mapping (ldap_username, ldap_email, employee_id, locosoft_id, verified) VALUES (%s, %s, %s, %s, 1)",
                                    (username, email, emp_id, locosoft_id)
                                )
                            mapping_created += 1
                            logger.info(f"Mapping angelegt/aktualisiert: {first_name} {last_name} → {username}")

                        if ad_dept and ad_dept != current_dept:
                            cursor.execute(
                                "UPDATE employees SET department_name = %s WHERE id = %s",
                                (ad_dept, emp_id)
                            )
                            changes.append({
                                'name': f"{first_name} {last_name}",
                                'old': current_dept,
                                'new': ad_dept
                            })
                            updated += 1
                            logger.info(f"UPDATE: {first_name} {last_name}: {current_dept} → {ad_dept}")
                        else:
                            unchanged += 1
                    else:
                        not_found += 1
                        errors.append(f"{first_name} {last_name} ({username})")

                except Exception as e:
                    errors.append(f"{first_name} {last_name}: {str(e)[:50]}")
                    logger.error(f"Fehler bei {first_name} {last_name}: {e}")

            conn.commit()

        conn_ldap.unbind()

        # Zusammenfassung
        print("\n" + "=" * 70)
        print("📊 SYNC ABGESCHLOSSEN")
        print("=" * 70)
        print(f"\n✅ Aktualisiert:    {updated}")
        if mapping_created:
            print(f"🔗 AD-Mapping:      {mapping_created} (per E-Mail-Prefix zugeordnet)")
        print(f"⏸️  Unverändert:     {unchanged}")
        print(f"⚠️  Nicht in AD:     {not_found}")
        if changes:
            print(f"\n🔄 Änderungen ({len(changes)}):")
            for c in changes[:20]:
                print(f"   {c['name']}: {c['old']} → {c['new']}")
            if len(changes) > 20:
                print(f"   ... und {len(changes) - 20} weitere")
        if errors and not_found > 0:
            print(f"\n⚠️  Nicht gefunden ({not_found}):")
            for e in errors[:10]:
                print(f"   • {e}")
            if len(errors) > 10:
                print(f"   ... und {len(errors) - 10} weitere")
        print("\n✅ AD Department Sync erfolgreich!")
        print("=" * 70)

        return {
            'status': 'success',
            'updated': updated,
            'mapping_created': mapping_created,
            'unchanged': unchanged,
            'not_found': not_found,
            'changes': changes[:10]
        }

    except Exception as e:
        logger.error(f"Sync fehlgeschlagen: {e}")
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'error': str(e)}


if __name__ == '__main__':
    result = main()
    sys.exit(0 if result.get('status') == 'success' else 1)
