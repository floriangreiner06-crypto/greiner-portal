#!/usr/bin/env python3
"""
Sync Locosoft-Kundendaten → DRIVE PostgreSQL (locosoft_kunden_sync).
Für bessere Adressbuch-Suche mit Volltext (TAG 211).

Aufruf:
  cd /opt/greiner-portal && ./venv/bin/python scripts/sync_locosoft_kunden.py

Voraussetzung: Migration add_locosoft_kunden_sync_tag211.sql ausgeführt.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_utils import locosoft_session, db_session

# Gleiche Handy-Erkennung wie in locosoft_addressbook_api
_MOBILE_CONDITION = """
    (n.com_type ILIKE '%mobil%' OR n.com_type ILIKE '%handy%'
     OR regexp_replace(n.phone_number, '[^0-9+]', '', 'g') ~ '^0?(49)?1[5-7][0-9]{7,}$'
     OR regexp_replace(n.phone_number, '[^0-9+]', '', 'g') ~ '^0?1[5-7][0-9]{7,}$')
"""


def fetch_from_locosoft():
    """Liest alle Kunden inkl. Telefon/E-Mail aus Locosoft."""
    with locosoft_session() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT
                c.customer_number,
                c.subsidiary,
                c.first_name,
                c.family_name,
                c.home_street,
                c.zip_code,
                c.home_city,
                c.country_code,
                (
                    SELECT n.phone_number
                    FROM customer_com_numbers n
                    WHERE n.customer_number = c.customer_number
                      AND n.phone_number IS NOT NULL AND TRIM(n.phone_number) != ''
                      AND {_MOBILE_CONDITION.strip()}
                    ORDER BY n.is_reference DESC NULLS LAST, n.counter
                    LIMIT 1
                ) AS phone_mobile,
                (
                    SELECT n.phone_number
                    FROM customer_com_numbers n
                    WHERE n.customer_number = c.customer_number
                      AND n.phone_number IS NOT NULL AND TRIM(n.phone_number) != ''
                    ORDER BY CASE WHEN {_MOBILE_CONDITION.strip()} THEN 0 ELSE 1 END,
                             n.is_reference DESC NULLS LAST, n.counter
                    LIMIT 1
                ) AS phone,
                (
                    SELECT n.address
                    FROM customer_com_numbers n
                    WHERE n.customer_number = c.customer_number
                      AND n.address IS NOT NULL AND n.address LIKE '%%@%%'
                    ORDER BY n.is_reference DESC NULLS LAST, n.counter
                    LIMIT 1
                ) AS email
            FROM customers_suppliers c
            WHERE c.is_supplier = false
            ORDER BY c.customer_number
            """
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        return [dict(zip(cols, r)) for r in rows] if cols and rows else []


def upsert_drive(rows):
    """Upsert in DRIVE locosoft_kunden_sync."""
    with db_session() as conn:
        cur = conn.cursor()
        for r in rows:
            cust_nr = r.get("customer_number")
            first = (r.get("first_name") or "").strip()
            family = (r.get("family_name") or "").strip()
            display_name = f"{first} {family}".strip() or f"Kunde {cust_nr}"
            cur.execute(
                """
                INSERT INTO locosoft_kunden_sync (
                    customer_number, subsidiary, first_name, family_name, display_name,
                    home_street, zip_code, home_city, country_code,
                    phone, phone_mobile, email, synced_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (customer_number) DO UPDATE SET
                    subsidiary = EXCLUDED.subsidiary,
                    first_name = EXCLUDED.first_name,
                    family_name = EXCLUDED.family_name,
                    display_name = EXCLUDED.display_name,
                    home_street = EXCLUDED.home_street,
                    zip_code = EXCLUDED.zip_code,
                    home_city = EXCLUDED.home_city,
                    country_code = EXCLUDED.country_code,
                    phone = EXCLUDED.phone,
                    phone_mobile = EXCLUDED.phone_mobile,
                    email = EXCLUDED.email,
                    synced_at = CURRENT_TIMESTAMP
                """,
                (
                    cust_nr,
                    r.get("subsidiary"),
                    first or None,
                    family or None,
                    display_name,
                    (r.get("home_street") or "").strip() or None,
                    (r.get("zip_code") or "").strip() or None,
                    (r.get("home_city") or "").strip() or None,
                    (r.get("country_code") or "").strip() or None,
                    (r.get("phone") or "").strip() or None,
                    (r.get("phone_mobile") or "").strip() or None,
                    (r.get("email") or "").strip() or None,
                ),
            )
        conn.commit()
    return len(rows)


def main():
    print("Locosoft → DRIVE Kunden-Sync starten...")
    rows = fetch_from_locosoft()
    print(f"  Locosoft: {len(rows)} Kunden gelesen.")
    if not rows:
        print("  Keine Daten. Ende.")
        return
    n = upsert_drive(rows)
    print(f"  DRIVE: {n} Zeilen in locosoft_kunden_sync übernommen.")
    print("Fertig.")


if __name__ == "__main__":
    main()
