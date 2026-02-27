#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
VACATION APPROVER SERVICE - AD-MANAGER BASIERT
========================================
Version: 3.0 - TAG 107
Datum: 09.12.2025
Updated: TAG 117 - Migration auf db_session

NEU: Team-Ermittlung über AD manager-Attribut!
- Team = alle Mitarbeiter wo AD manager = aktueller User
- Genehmigung weiterhin über GRP_Urlaub_Genehmiger_* Gruppen
- Admin (GRP_Urlaub_Admin) sieht alle
"""

import json
import logging
from typing import List, Dict, Optional

# Zentrale DB-Utilities (TAG117)
from api.db_utils import db_session

logger = logging.getLogger(__name__)

LDAP_CONFIG_PATH = '/opt/greiner-portal/config/ldap_credentials.env'

# LDAP-Modul
try:
    import ldap3
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False
    logger.warning("ldap3 nicht installiert - AD-Abfragen nicht möglich")


def load_ldap_config():
    """Lädt LDAP-Config"""
    config = {}
    try:
        with open(LDAP_CONFIG_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except:
        pass
    return config


def get_ad_users_with_manager() -> Dict[str, Dict]:
    """
    Holt alle AD-User mit manager-Attribut direkt aus LDAP.
    Cached in users-Tabelle wenn möglich.

    Returns:
        Dict[username] = {
            'name': str,
            'manager_username': str oder None,
            'manager_name': str oder None,
            'department': str,
            'company': str
        }
    """
    if not LDAP_AVAILABLE:
        logger.warning("LDAP nicht verfügbar - nutze DB-Cache")
        return {}

    ldap_config = load_ldap_config()
    if not ldap_config.get('LDAP_SERVER'):
        return {}

    try:
        server = ldap3.Server(
            ldap_config.get('LDAP_SERVER'),
            port=int(ldap_config.get('LDAP_PORT', '389')),
            use_ssl=ldap_config.get('LDAP_USE_SSL', 'False').lower() == 'true',
            get_info=ldap3.ALL
        )
        conn = ldap3.Connection(
            server,
            user=ldap_config.get('LDAP_BIND_DN'),
            password=ldap_config.get('LDAP_BIND_PASSWORD'),
            auto_bind=True
        )

        base_dn = ldap_config.get('LDAP_BASE_DN', 'DC=auto-greiner,DC=de')
        conn.search(
            search_base=f'OU=AUTO-GREINER,{base_dn}',
            search_filter='(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))',
            attributes=['sAMAccountName', 'displayName', 'manager', 'department', 'company']
        )

        # Erst alle User sammeln (für DN → username Lookup)
        dn_to_username = {}
        users = {}

        for entry in conn.entries:
            username = str(entry.sAMAccountName).lower()
            dn_to_username[str(entry.entry_dn).lower()] = username

            users[username] = {
                'name': str(entry.displayName) if entry.displayName else None,
                'manager_dn': str(entry.manager) if entry.manager and str(entry.manager) != '[]' else None,
                'manager_username': None,
                'manager_name': None,
                'department': str(entry.department) if entry.department and str(entry.department) != '[]' else None,
                'company': str(entry.company) if entry.company and str(entry.company) != '[]' else None,
            }

        # Manager-DN zu Username auflösen
        for username, user_data in users.items():
            if user_data['manager_dn']:
                manager_dn_lower = user_data['manager_dn'].lower()
                user_data['manager_username'] = dn_to_username.get(manager_dn_lower)

                # Manager-Name aus DN extrahieren
                if 'CN=' in user_data['manager_dn']:
                    user_data['manager_name'] = user_data['manager_dn'].split('CN=')[1].split(',')[0]

        conn.unbind()
        return users

    except Exception as e:
        logger.error(f"LDAP-Fehler: {e}")
        return {}


def get_team_by_manager(manager_username: str) -> List[Dict]:
    """
    Findet alle direkten Untergebenen eines Managers aus AD.

    Args:
        manager_username: LDAP-Username des Managers (ohne @domain)

    Returns:
        Liste der Team-Mitglieder
    """
    ad_users = get_ad_users_with_manager()

    if not ad_users:
        logger.warning("Keine AD-Daten verfügbar")
        return []

    manager_username_lower = manager_username.lower()

    # Finde alle User wo manager_username = dieser Manager
    team = []
    for username, user_data in ad_users.items():
        if user_data.get('manager_username') == manager_username_lower:
            team.append({
                'ldap_username': username,
                'name': user_data.get('name'),
                'department': user_data.get('department'),
                'company': user_data.get('company')
            })

    # Ergänze mit DB-Infos (employee_id, locosoft_id)
    if team:
        with db_session() as db_conn:
            cursor = db_conn.cursor()

            for member in team:
                cursor.execute("""
                    SELECT e.id as employee_id, lem.locosoft_id, le.subsidiary
                    FROM employees e
                    JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
                    LEFT JOIN loco_employees le ON lem.locosoft_id = le.employee_number AND le.is_latest_record IS NOT DISTINCT FROM true
                    WHERE lem.ldap_username = %s
                """, (member['ldap_username'],))

                row = cursor.fetchone()
                if row:
                    member['employee_id'] = row['employee_id']
                    member['locosoft_id'] = row['locosoft_id']
                    member['subsidiary'] = row['subsidiary']
                    member['standort'] = {1: 'Deggendorf', 3: 'Landau'}.get(row['subsidiary'], 'Unbekannt')
                else:
                    member['employee_id'] = None
                    member['locosoft_id'] = None
                    member['subsidiary'] = None
                    member['standort'] = 'Unbekannt'

    return sorted(team, key=lambda x: x.get('name') or '')


def get_employee_ad_groups(employee_id: int) -> List[str]:
    """Holt AD-Gruppen eines Mitarbeiters aus users-Tabelle"""
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT u.ad_groups
                FROM employees e
                JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
                JOIN users u ON lem.ldap_username = REPLACE(u.username, '@auto-greiner.de', '')
                WHERE e.id = %s
            """, (employee_id,))

            row = cursor.fetchone()
            if row and row['ad_groups']:
                return json.loads(row['ad_groups'])
            return []
    except Exception as e:
        logger.error(f"Fehler beim Laden der AD-Gruppen: {e}")
        return []


def _get_gl_approvers_impl(cursor) -> List[Dict]:
    """Hole GL/Admin als Fallback-Genehmiger (Implementierung mit gegebenem Cursor)"""
    cursor.execute("""
        SELECT u.id, u.username, u.display_name, u.email, u.ad_groups, e.id as employee_id
        FROM users u
        LEFT JOIN ldap_employee_mapping lem ON lem.ldap_username = REPLACE(u.username, '@auto-greiner.de', '')
        LEFT JOIN employees e ON lem.employee_id = e.id
        WHERE u.ad_groups LIKE '%GRP_Urlaub_Genehmiger_GL%'
           OR u.ad_groups LIKE '%GRP_Urlaub_Admin%'
    """)

    approvers = []
    for row in cursor.fetchall():
        ad_groups = json.loads(row['ad_groups']) if row['ad_groups'] else []
        if 'GRP_Urlaub_Genehmiger_GL' in ad_groups or 'GRP_Urlaub_Admin' in ad_groups:
            approvers.append({
                'approver_id': row['employee_id'],
                'approver_name': row['display_name'],
                'approver_ldap': row['username'].replace('@auto-greiner.de', ''),
                'approver_email': row['email'] or row['username'],
                'priority': 1,
                'ad_group': 'GRP_Urlaub_Genehmiger_GL',
                'is_admin': 'GRP_Urlaub_Admin' in ad_groups,
                'is_direct_manager': False
            })

    return approvers


def get_approvers_for_employee(employee_id: int) -> List[Dict]:
    """
    Findet Genehmiger für einen Mitarbeiter.

    NEU: Basiert auf AD manager-Attribut!
    1. Hole manager des Mitarbeiters aus AD
    2. Prüfe ob Manager eine GRP_Urlaub_Genehmiger_* Gruppe hat
    3. Wenn nicht → eskaliere zu nächsthöherem Manager oder GL
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            # 1. Hole LDAP-Username des Mitarbeiters
            cursor.execute("""
                SELECT lem.ldap_username
                FROM employees e
                JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
                WHERE e.id = %s
            """, (employee_id,))

            row = cursor.fetchone()
            if not row:
                logger.warning(f"Kein LDAP-Mapping für employee_id={employee_id}")
                return []

            employee_ldap = row['ldap_username']

            # 2. Hole AD-Daten inkl. Manager
            ad_users = get_ad_users_with_manager()
            employee_ad = ad_users.get(employee_ldap.lower())

            if not employee_ad:
                logger.warning(f"Keine AD-Daten für {employee_ldap}")
                return []

            manager_username = employee_ad.get('manager_username')

            if not manager_username:
                logger.warning(f"Kein Manager in AD für {employee_ldap} - eskaliere zu GL")
                return _get_gl_approvers_impl(cursor)

            # 3. Prüfe ob Manager Genehmiger-Rechte hat (SPLIT_PART = Teil vor @)
            manager_norm = _normalize_ldap_username(manager_username)
            cursor.execute("""
                SELECT u.id, u.username, u.display_name, u.email, u.ad_groups, e.id as employee_id
                FROM users u
                LEFT JOIN ldap_employee_mapping lem ON LOWER(TRIM(SPLIT_PART(COALESCE(lem.ldap_username,'') || '@', '@', 1))) = LOWER(TRIM(SPLIT_PART(COALESCE(u.username,'') || '@', '@', 1)))
                LEFT JOIN employees e ON lem.employee_id = e.id
                WHERE LOWER(TRIM(SPLIT_PART(COALESCE(u.username,'') || '@', '@', 1))) = %s
            """, (manager_norm or '',))

            manager_row = cursor.fetchone()

            if not manager_row:
                logger.warning(f"Manager {manager_username} nicht in users-Tabelle - eskaliere zu GL")
                return _get_gl_approvers_impl(cursor)

            ad_groups = json.loads(manager_row['ad_groups']) if manager_row['ad_groups'] else []

            # Prüfe ob Manager Genehmiger-Gruppe oder Admin hat (inkl. "Genehmiger für Urlaub Dispo")
            is_approver = any(_is_approver_group(g) for g in ad_groups)

            if not is_approver:
                logger.info(f"Manager {manager_username} hat keine Genehmiger-Gruppe - eskaliere zu GL")
                return _get_gl_approvers_impl(cursor)

            # Manager ist Genehmiger!
            approver_group = next((g for g in ad_groups if _is_approver_group(g)), 'GRP_Urlaub_Admin')

            return [{
                'approver_id': manager_row['employee_id'],
                'approver_name': manager_row['display_name'],
                'approver_ldap': manager_username,
                'approver_email': manager_row['email'] or f"{manager_username}@auto-greiner.de",
                'priority': 1,
                'ad_group': approver_group,
                'is_admin': 'GRP_Urlaub_Admin' in ad_groups,
                'is_direct_manager': True
            }]

    except Exception as e:
        logger.error(f"Fehler bei get_approvers_for_employee: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def get_team_for_approver(approver_ldap_username: str, include_self: bool = False) -> List[Dict]:
    """
    Findet alle Mitarbeiter für die ein User Genehmiger ist.

    NEU: Basiert auf AD manager-Attribut!
    - Normaler Genehmiger: Team = alle wo manager = dieser User
    - Admin: Team = ALLE aktiven Mitarbeiter
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            # 1. Hole AD-Gruppen des Users (SPLIT_PART = Teil vor @, unabhängig von Domain)
            norm = _normalize_ldap_username(approver_ldap_username)
            if not norm:
                return []
            cursor.execute("""
                SELECT ad_groups FROM users
                WHERE LOWER(TRIM(SPLIT_PART(COALESCE(username,'') || '@', '@', 1))) = %s
            """, (norm,))
            row = cursor.fetchone()
            if not row or not row.get('ad_groups'):
                return []

            raw_ag = row.get('ad_groups')
            ad_groups = json.loads(raw_ag) if isinstance(raw_ag, str) else (raw_ag if isinstance(raw_ag, list) else [])
            is_admin = 'GRP_Urlaub_Admin' in ad_groups
            is_approver_flag = any(_is_approver_group(g) for g in ad_groups)

            if not is_admin and not is_approver_flag:
                return []

            # 2. Admin sieht ALLE
            if is_admin:
                cursor.execute("""
                    SELECT DISTINCT
                        e.id as employee_id,
                        e.first_name || ' ' || e.last_name as name,
                        lem.ldap_username,
                        lem.locosoft_id,
                        le.subsidiary,
                        CASE le.subsidiary
                            WHEN 1 THEN 'Deggendorf'
                            WHEN 3 THEN 'Landau'
                            ELSE 'Unbekannt'
                        END as standort
                    FROM employees e
                    JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
                    LEFT JOIN loco_employees le ON lem.locosoft_id = le.employee_number AND le.is_latest_record IS NOT DISTINCT FROM true
                    WHERE e.aktiv = true
                    ORDER BY e.first_name || ' ' || e.last_name
                """)

                team = []
                for row in cursor.fetchall():
                    if not include_self and row['ldap_username'] == approver_ldap_username:
                        continue
                    team.append({
                        'employee_id': row['employee_id'],
                        'name': row['name'],
                        'ldap_username': row['ldap_username'],
                        'locosoft_id': row['locosoft_id'],
                        'subsidiary': row['subsidiary'],
                        'standort': row['standort'],
                        'approver_priority': 1
                    })
                return team

            # 3. Normaler Genehmiger: Team = direkte Reports (AD manager) + ggf. Abteilung aus Gruppen-Suffix
            team_raw = get_team_by_manager(approver_ldap_username)
            seen_ids = set()

            team = []
            for member in team_raw:
                if not include_self and member.get('ldap_username') == approver_ldap_username:
                    continue
                if member.get('employee_id'):  # Nur wenn in DB verknüpft
                    seen_ids.add(member['employee_id'])
                    team.append({
                        'employee_id': member['employee_id'],
                        'name': member['name'],
                        'ldap_username': member['ldap_username'],
                        'locosoft_id': member.get('locosoft_id'),
                        'subsidiary': member.get('subsidiary'),
                        'standort': member.get('standort', 'Unbekannt'),
                        'approver_priority': 1
                    })

            # 3b. Abteilung aus Genehmiger-Gruppen: technischer Name (GRP_Urlaub_Genehmiger_Disposition)
            #     ODER Anzeigename ("Genehmiger für Urlaub Disposition") → Margit kann für Susanne genehmigen
            def _department_suffixes_from_groups(groups):
                suffixes = []
                for g in (groups or []):
                    g = str(g).strip() if g else ""
                    if not g:
                        continue
                    if g.startswith('GRP_Urlaub_Genehmiger_'):
                        s = g.replace('GRP_Urlaub_Genehmiger_', '').strip()
                        if s and s not in suffixes:
                            suffixes.append(s)
                    elif _is_approver_group(g) and 'urlaub' in g.lower():
                        # Anzeigename z.B. "Genehmiger für Urlaub Disposition" → letztes Wort = Abteilung
                        parts = g.split()
                        if len(parts) >= 2:
                            s = parts[-1].strip()
                            if s and s not in suffixes:
                                suffixes.append(s)
                return suffixes

            try:
                dept_suffixes = _department_suffixes_from_groups(ad_groups)
                for suffix in dept_suffixes:
                    # Abgleich: exakt ODER department_name beginnt mit Suffix (z.B. Dispo → Disposition)
                    cursor.execute("""
                        SELECT e.id, e.first_name || ' ' || e.last_name as name, lem.ldap_username,
                               lem.locosoft_id, le.subsidiary
                        FROM employees e
                        JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
                        LEFT JOIN loco_employees le ON lem.locosoft_id = le.employee_number AND le.is_latest_record IS NOT DISTINCT FROM true
                        WHERE e.aktiv = true
                          AND (LOWER(TRIM(COALESCE(e.department_name, ''))) = LOWER(%s)
                             OR LOWER(TRIM(COALESCE(e.department_name, ''))) LIKE LOWER(%s) || '%%')
                        ORDER BY e.last_name, e.first_name
                    """, (suffix, suffix))
                    for dept_row in cursor.fetchall():
                        eid = dept_row[0]
                        if eid in seen_ids:
                            continue
                        seen_ids.add(eid)
                        if not include_self and (dept_row[2] or '').lower() == (approver_ldap_username or '').lower():
                            continue
                        team.append({
                            'employee_id': eid,
                            'name': dept_row[1] or 'Unbekannt',
                            'ldap_username': dept_row[2],
                            'locosoft_id': dept_row[3],
                            'subsidiary': dept_row[4],
                            'standort': {1: 'Deggendorf', 3: 'Landau'}.get(dept_row[4], 'Unbekannt') if dept_row[4] is not None else 'Unbekannt',
                            'approver_priority': 1
                        })
            except Exception as e:
                logger.warning(f"Team-Erweiterung nach Abteilung übersprungen: {e}")

            return team

    except Exception as e:
        logger.error(f"Fehler bei get_team_for_approver: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def _normalize_ldap_username(username: Optional[str]) -> str:
    """Username für Lookup normalisieren: lowercase, ohne @domain (Dispo/Test: Margit, Jennifer)."""
    if not username:
        return ""
    u = (username or "").strip().lower()
    return u.split("@")[0] if "@" in u else u


def _is_approver_group(group_name: str) -> bool:
    """
    Prüft ob eine AD-Gruppe Urlaub-Genehmiger-Rechte bedeutet.
    - Technische Namen: GRP_Urlaub_Genehmiger_*, GRP_Urlaub_Admin
    - Anzeigename aus AD (CN): z. B. "Genehmiger für Urlaub Dispo" (enthält Genehmiger + Urlaub)
    """
    if not group_name:
        return False
    g = (group_name if isinstance(group_name, str) else str(group_name)).strip()
    if g == 'GRP_Urlaub_Admin' or g.startswith('GRP_Urlaub_Genehmiger_'):
        return True
    g_lower = g.lower()
    if 'genehmiger' in g_lower and 'urlaub' in g_lower:
        return True
    return False


def is_approver(ldap_username: str) -> bool:
    """Prüft ob ein User Genehmiger-Rechte hat. Lookup case-insensitive und mit/ohne Domain."""
    try:
        norm = _normalize_ldap_username(ldap_username)
        if not norm:
            return False
        with db_session() as conn:
            cursor = conn.cursor()
            # Case-insensitiver Abgleich; Teil vor @ (SPLIT_PART) unabhängig von Domain-Schreibweise
            cursor.execute("""
                SELECT ad_groups FROM users
                WHERE LOWER(TRIM(SPLIT_PART(COALESCE(username,'') || '@', '@', 1))) = %s
            """, (norm,))
            row = cursor.fetchone()
            if not row:
                return False
            raw = row.get('ad_groups') if hasattr(row, 'get') else (row['ad_groups'] if 'ad_groups' in (row.keys() if hasattr(row, 'keys') else []) else None)
            if not raw:
                return False
            ad_groups = json.loads(raw) if isinstance(raw, str) else (raw if isinstance(raw, list) else [])
            for group in ad_groups:
                if _is_approver_group(group):
                    return True
            return False
    except Exception as e:
        logger.error(f"Fehler bei is_approver: {e}")
        return False


def is_admin(ldap_username: str) -> bool:
    """Prüft ob ein User Admin-Rechte hat (GRP_Urlaub_Admin). Lookup case-insensitive."""
    try:
        norm = _normalize_ldap_username(ldap_username)
        if not norm:
            return False
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ad_groups FROM users
                WHERE LOWER(TRIM(SPLIT_PART(COALESCE(username,'') || '@', '@', 1))) = %s
            """, (norm,))
            row = cursor.fetchone()
            if not row or not row['ad_groups']:
                return False
            raw = row['ad_groups']
            ad_groups = json.loads(raw) if isinstance(raw, str) else (raw if isinstance(raw, list) else [])
            return 'GRP_Urlaub_Admin' in ad_groups
    except Exception as e:
        logger.error(f"Fehler bei is_admin: {e}")
        return False


def get_approver_summary(ldap_username: str) -> Dict:
    """Gibt eine Zusammenfassung für einen Genehmiger zurück."""
    try:
        # Prüfe Admin zuerst (Admin ist auch immer Genehmiger)
        user_is_admin = is_admin(ldap_username)
        user_is_approver = is_approver(ldap_username)

        if not user_is_approver and not user_is_admin:
            return {
                'is_approver': False,
                'is_admin': False,
                'team_size': 0,
                'groups': [],
                'pending_requests': 0
            }

        team = get_team_for_approver(ldap_username)
        team_size = len(team)

        norm = _normalize_ldap_username(ldap_username)
        with db_session() as conn:
            cursor = conn.cursor()
            if norm:
                cursor.execute("""
                    SELECT ad_groups FROM users
                    WHERE LOWER(TRIM(SPLIT_PART(COALESCE(username,'') || '@', '@', 1))) = %s
                """, (norm,))
            else:
                cursor.execute("SELECT 1 WHERE 1=0")  # keine Zeile
            row = cursor.fetchone()
            raw = row.get('ad_groups') if row else None
            ad_groups = json.loads(raw) if isinstance(raw, str) else (raw if isinstance(raw, list) else [])
            approver_groups = [g for g in ad_groups if _is_approver_group(g) or (g and g.startswith('GRP_Urlaub_'))]

            # Offene Anträge
            team_ids = [m['employee_id'] for m in team if m.get('employee_id')]
            pending_count = 0

            if team_ids:
                placeholders = ','.join(['%s'] * len(team_ids))
                cursor.execute(f"""
                    SELECT COUNT(*) as cnt
                    FROM vacation_bookings
                    WHERE employee_id IN ({placeholders})
                      AND status = 'pending'
                """, team_ids)
                pending_count = cursor.fetchone()['cnt']

            return {
                'is_approver': user_is_approver or user_is_admin,
                'is_admin': user_is_admin,
                'team_size': team_size,
                'groups': approver_groups,
                'pending_requests': pending_count
            }

    except Exception as e:
        logger.error(f"Fehler bei get_approver_summary: {e}")
        return {
            'is_approver': False,
            'is_admin': False,
            'team_size': 0,
            'groups': [],
            'pending_requests': 0,
            'error': str(e)
        }


# ============================================================================
# TEST
# ============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("VACATION APPROVER SERVICE TEST (AD-MANAGER BASIERT)")
    print("=" * 60)
    print()

    # Test 0: AD-Daten laden
    print("0. Lade AD-User mit Manager...")
    ad_users = get_ad_users_with_manager()
    print(f"   {len(ad_users)} AD-User geladen")

    # Zeige ein paar Beispiele
    print("\n   Beispiele (User → Manager):")
    count = 0
    for username, data in ad_users.items():
        if data.get('manager_username') and count < 5:
            print(f"   - {username} → {data['manager_username']} ({data.get('manager_name')})")
            count += 1

    print()

    # Test 1: Team für Matthias König (Service-Leiter DEG)
    print("1. Team für matthias.koenig (via AD manager):")
    team = get_team_for_approver('matthias.koenig')
    print(f"   Team-Größe: {len(team)}")
    for m in team[:5]:
        print(f"   - {m['name']} ({m.get('standort', '?')})")
    if len(team) > 5:
        print(f"   ... und {len(team) - 5} weitere")

    print()

    # Test 2: Genehmiger für einen Mitarbeiter
    print("2. Genehmiger für employee_id=6 (Sandra Brendel):")
    approvers = get_approvers_for_employee(6)
    for a in approvers:
        mgr_flag = " [DIREKTER MANAGER]" if a.get('is_direct_manager') else ""
        print(f"   - {a['approver_name']} ({a['ad_group']}){mgr_flag}")

    print()

    # Test 3: Team für Admin (Sandra Brendel)
    print("3. Team für sandra.brendel (Admin):")
    team = get_team_for_approver('sandra.brendel')
    print(f"   Team-Größe: {len(team)} (Admin sieht alle)")

    print()

    # Test 4: Approver Summary
    print("4. Summary für florian.greiner:")
    summary = get_approver_summary('florian.greiner')
    print(f"   Ist Genehmiger: {summary['is_approver']}")
    print(f"   Team-Größe: {summary['team_size']}")
    print(f"   Gruppen: {', '.join(summary['groups'])}")
    print(f"   Offene Anträge: {summary['pending_requests']}")

    print()
    print("=" * 60)
    print("Test abgeschlossen")
