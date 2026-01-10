"""
Report Registry - Dynamisches Report-System
============================================
Zentrale Registry für alle E-Mail Reports.
Neue Reports registrieren sich hier automatisch.

Verwendung in Report-Scripts:
    from reports.registry import register_report

    register_report('mein_report', {
        'name': 'Mein Report',
        'description': 'Beschreibung...',
        ...
    })

TAG 135 - Report-Subscriptions System
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from api.db_connection import get_db, convert_placeholders

# ============================================================================
# REPORT REGISTRY - Alle verfügbaren Reports
# ============================================================================

REPORT_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Standard-Reports registrieren
def _init_standard_reports():
    """Registriert die Standard-Reports beim Import"""

    REPORT_REGISTRY['tek_daily'] = {
        'name': 'TEK Tagesreport (Gesamt)',
        'description': 'Tägliche Erfolgskontrolle mit DB1, Marge, Breakeven-Analyse',
        'script': 'scripts/send_daily_tek.py',
        'schedule': '17:30 Mo-Fr',
        'supports_standort': True,
        'standort_optionen': ['DEG', 'LAN'],
        'supports_bereiche': True,
        'bereiche_optionen': ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'],
        'icon': '📊',
        'category': 'controlling'
    }

    # TAG140: Neue TEK-Reports für Abteilungsleiter und Filialleiter
    REPORT_REGISTRY['tek_filiale'] = {
        'name': 'TEK Filiale',
        'description': 'TEK für Filialleiter - alle Bereiche eines Standorts',
        'script': 'scripts/send_daily_tek.py',
        'schedule': '17:30 Mo-Fr',
        'supports_standort': True,
        'standort_optionen': ['DEG', 'LAN'],
        'supports_bereiche': False,
        'icon': '🏢',
        'category': 'controlling'
    }

    REPORT_REGISTRY['tek_nw'] = {
        'name': 'TEK Neuwagen',
        'description': 'TEK für Verkaufsleiter NW - nur Neuwagen-Bereich',
        'script': 'scripts/send_daily_tek.py',
        'schedule': '17:30 Mo-Fr',
        'supports_standort': True,
        'standort_optionen': ['DEG', 'LAN'],
        'supports_bereiche': False,
        'icon': '🚗',
        'category': 'controlling'
    }

    REPORT_REGISTRY['tek_gw'] = {
        'name': 'TEK Gebrauchtwagen',
        'description': 'TEK für Verkaufsleiter GW - nur GW-Bereich',
        'script': 'scripts/send_daily_tek.py',
        'schedule': '17:30 Mo-Fr',
        'supports_standort': True,
        'standort_optionen': ['DEG', 'LAN'],
        'supports_bereiche': False,
        'icon': '🚙',
        'category': 'controlling'
    }

    REPORT_REGISTRY['tek_teile'] = {
        'name': 'TEK Teile',
        'description': 'TEK für Teileleiter - nur Teile-Bereich',
        'script': 'scripts/send_daily_tek.py',
        'schedule': '17:30 Mo-Fr',
        'supports_standort': True,
        'standort_optionen': ['DEG', 'LAN'],
        'supports_bereiche': False,
        'icon': '🔩',
        'category': 'controlling'
    }

    REPORT_REGISTRY['tek_werkstatt'] = {
        'name': 'TEK Werkstatt',
        'description': 'TEK für Serviceleiter - nur Werkstatt-Bereich',
        'script': 'scripts/send_daily_tek.py',
        'schedule': '17:30 Mo-Fr',
        'supports_standort': True,
        'standort_optionen': ['DEG', 'LAN'],
        'supports_bereiche': False,
        'icon': '🔧',
        'category': 'controlling'
    }

    REPORT_REGISTRY['auftragseingang'] = {
        'name': 'Auftragseingang',
        'description': 'Verkauf Stückzahlen nach Verkäufer (NW/GW/TV)',
        'script': 'scripts/send_daily_auftragseingang.py',
        'schedule': '17:15 Mo-Fr',
        'supports_standort': False,
        'supports_bereiche': False,
        'icon': '🚗',
        'category': 'verkauf'
    }

    REPORT_REGISTRY['werkstatt_tagesbericht'] = {
        'name': 'Werkstatt Tagesbericht',
        'description': 'Leistungsgrad, Nachkalkulation, Top-Mechaniker Ranking',
        'script': 'scripts/reports/werkstatt_tagesbericht_email.py',
        'schedule': '18:00 Mo-Fr',
        'supports_standort': True,
        'standort_optionen': ['DEG', 'LAN'],
        'supports_bereiche': False,
        'icon': '🔧',
        'category': 'werkstatt'
    }

# Beim Import initialisieren
_init_standard_reports()


# ============================================================================
# REGISTRY API
# ============================================================================

def register_report(report_id: str, config: dict) -> None:
    """
    Neuen Report in der Registry registrieren.

    Args:
        report_id: Eindeutiger Identifier (z.B. 'tek_daily')
        config: Report-Konfiguration mit:
            - name: Anzeigename
            - description: Beschreibung
            - script: Pfad zum Script
            - schedule: Zeitplan-Beschreibung
            - supports_standort: Bool - Standort-Filter möglich?
            - standort_optionen: Liste der Standorte (wenn supports_standort)
            - supports_bereiche: Bool - Bereichs-Filter möglich?
            - bereiche_optionen: Liste der Bereiche (wenn supports_bereiche)
            - icon: Emoji-Icon
            - category: Kategorie (controlling, verkauf, werkstatt, etc.)
    """
    required_fields = ['name', 'description', 'script', 'schedule', 'icon']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Report-Config muss '{field}' enthalten")

    # Defaults setzen
    config.setdefault('supports_standort', False)
    config.setdefault('supports_bereiche', False)
    config.setdefault('category', 'sonstige')

    REPORT_REGISTRY[report_id] = config


def get_all_reports() -> Dict[str, Dict[str, Any]]:
    """Alle registrierten Reports zurückgeben"""
    return REPORT_REGISTRY.copy()


def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    """Einzelnen Report aus Registry holen"""
    return REPORT_REGISTRY.get(report_id)


def report_exists(report_id: str) -> bool:
    """Prüfen ob Report existiert"""
    return report_id in REPORT_REGISTRY


# ============================================================================
# DATABASE OPERATIONS - Subscriptions
# TAG142: Umgestellt auf PostgreSQL via get_db()
# ============================================================================

# get_db() wird jetzt direkt aus api.db_connection importiert (SSOT)


def init_subscriptions_table():
    """
    Tabelle für Report-Subscriptions erstellen falls nicht vorhanden.
    TAG142: PostgreSQL-kompatibel
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_subscriptions (
            id SERIAL PRIMARY KEY,
            report_type TEXT NOT NULL,
            email TEXT NOT NULL,
            standort TEXT DEFAULT '',
            bereiche TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            UNIQUE(report_type, email, standort)
        )
    """)

    # Index für schnelle Abfragen
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_report_subscriptions_type
        ON report_subscriptions(report_type, active)
    """)

    conn.commit()
    conn.close()


def get_subscribers(report_type: str, standort: str = None, active_only: bool = True) -> List[Dict]:
    """
    Empfänger für einen Report holen.
    TAG142: Umgestellt auf PostgreSQL

    Args:
        report_type: Report-ID aus Registry
        standort: Optional - nur Empfänger für bestimmten Standort
        active_only: Nur aktive Subscriptions

    Returns:
        Liste von Subscriber-Dicts mit email, standort, bereiche
    """
    conn = get_db()
    cursor = conn.cursor()

    sql = "SELECT * FROM report_subscriptions WHERE report_type = %s"
    params = [report_type]

    if active_only:
        sql += " AND active = 1"

    if standort:
        # Empfänger für spezifischen Standort ODER für alle Standorte (leer)
        sql += " AND (standort = %s OR standort = '')"
        params.append(standort)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        # Konvertiere leeren String zurück zu None für API-Konsistenz
        standort_val = row['standort'] if row['standort'] else None
        result.append({
            'id': row['id'],
            'email': row['email'],
            'standort': standort_val,
            'bereiche': json.loads(row['bereiche']) if row['bereiche'] else None,
            'active': bool(row['active']),
            'created_at': row['created_at'],
            'created_by': row['created_by']
        })

    return result


def get_subscriber_emails(report_type: str, standort: str = None) -> List[str]:
    """
    Nur E-Mail-Adressen für einen Report holen (für Scripts).

    Args:
        report_type: Report-ID
        standort: Optional Standort-Filter

    Returns:
        Liste von E-Mail-Adressen
    """
    subscribers = get_subscribers(report_type, standort)
    return list(set(s['email'] for s in subscribers))


def add_subscriber(
    report_type: str,
    email: str,
    standort: str = None,
    bereiche: List[str] = None,
    created_by: str = None
) -> bool:
    """
    Neuen Empfänger hinzufügen.
    TAG142: Umgestellt auf PostgreSQL

    Returns:
        True bei Erfolg, False wenn bereits vorhanden
    """
    if not report_exists(report_type):
        raise ValueError(f"Report '{report_type}' existiert nicht in Registry")

    conn = get_db()
    cursor = conn.cursor()

    # Konvertiere None zu leerem String für DB
    standort_db = standort or ''

    try:
        cursor.execute("""
            INSERT INTO report_subscriptions
            (report_type, email, standort, bereiche, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            report_type,
            email.lower().strip(),
            standort_db,
            json.dumps(bereiche) if bereiche else None,
            created_by
        ))
        conn.commit()
        return True
    except Exception as e:
        # Bereits vorhanden (UNIQUE violation) - reaktivieren falls inaktiv
        conn.rollback()
        cursor.execute("""
            UPDATE report_subscriptions
            SET active = 1, created_by = %s
            WHERE report_type = %s AND email = %s AND standort = %s
        """, (created_by, report_type, email.lower().strip(), standort_db))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def remove_subscriber(report_type: str, email: str, standort: str = None) -> bool:
    """
    Empfänger entfernen (deaktivieren).
    TAG142: Umgestellt auf PostgreSQL

    Returns:
        True bei Erfolg
    """
    conn = get_db()
    cursor = conn.cursor()

    standort_db = standort or ''

    cursor.execute("""
        UPDATE report_subscriptions
        SET active = 0
        WHERE report_type = %s AND email = %s AND standort = %s
    """, (report_type, email.lower().strip(), standort_db))

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def delete_subscriber(subscription_id: int) -> bool:
    """Subscription komplett löschen (nicht nur deaktivieren)"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM report_subscriptions WHERE id = %s", (subscription_id,))

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def toggle_subscriber(subscription_id: int) -> bool:
    """Subscription aktivieren/deaktivieren togglen"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE report_subscriptions
        SET active = CASE WHEN active = 1 THEN 0 ELSE 1 END
        WHERE id = %s
    """, (subscription_id,))

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def get_all_subscriptions_with_counts() -> Dict[str, Dict]:
    """
    Alle Reports mit Subscriber-Counts für Admin-UI.

    Returns:
        Dict mit report_id -> {report_info, subscriber_count, subscribers}
    """
    result = {}

    for report_id, report_config in REPORT_REGISTRY.items():
        subscribers = get_subscribers(report_id, active_only=False)
        active_count = sum(1 for s in subscribers if s['active'])

        result[report_id] = {
            **report_config,
            'id': report_id,
            'subscriber_count': active_count,
            'total_subscribers': len(subscribers),
            'subscribers': subscribers
        }

    return result


# ============================================================================
# MIGRATION - Bestehende Empfänger übernehmen
# ============================================================================

def migrate_existing_subscribers():
    """
    Migriert die hardcoded Empfänger aus den bestehenden Scripts in die DB.
    Sollte einmalig ausgeführt werden.
    """
    init_subscriptions_table()

    # TEK Daily
    tek_empfaenger = [
        ("peter.greiner@auto-greiner.de", None),
        ("florian.greiner@auto-greiner.de", None),
        ("anton.suess@auto-greiner.de", None),
        ("matthias.koenig@auto-greiner.de", None),
        ("christian.aichinger@auto-greiner.de", None),
    ]

    for email, standort in tek_empfaenger:
        try:
            add_subscriber('tek_daily', email, standort, created_by='migration')
        except:
            pass

    # Auftragseingang
    auftragseingang_empfaenger = [
        "peter.greiner@auto-greiner.de",
        "rolf.sterr@auto-greiner.de",
        "anton.suess@auto-greiner.de",
        "florian.greiner@auto-greiner.de",
        "margit.loibl@auto-greiner.de",
        "jennifer.bielmeier@auto-greiner.de"
    ]

    for email in auftragseingang_empfaenger:
        try:
            add_subscriber('auftragseingang', email, created_by='migration')
        except:
            pass

    # Werkstatt Tagesbericht
    werkstatt_empfaenger = [
        ("florian.greiner@auto-greiner.de", None),  # Für alle Standorte
    ]

    for email, standort in werkstatt_empfaenger:
        try:
            add_subscriber('werkstatt_tagesbericht', email, standort, created_by='migration')
        except:
            pass

    print("Migration abgeschlossen!")


# Tabelle beim Import initialisieren
try:
    init_subscriptions_table()
except:
    pass  # Ignorieren wenn DB nicht verfügbar (z.B. beim Import-Check)
