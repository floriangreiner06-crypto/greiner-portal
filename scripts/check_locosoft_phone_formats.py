#!/usr/bin/env python3
"""
Prüft Telefonnummern und com_type für Kunden in Locosoft (z. B. "Greiner").
Hilft beim Debuggen des Filters "Nur Handynummern".

Aufruf: python scripts/check_locosoft_phone_formats.py [Suchbegriff]
Beispiel: python scripts/check_locosoft_phone_formats.py greiner
"""

import os
import sys

# Projekt-Root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_utils import locosoft_session


def main():
    q = (sys.argv[1] if len(sys.argv) > 1 else "greiner").strip()
    term = f"%{q}%"
    print(f"Suche Kunden: {q!r}")
    print("-" * 80)
    with locosoft_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.customer_number, c.first_name, c.family_name,
                   n.com_type, n.phone_number,
                   regexp_replace(n.phone_number, '[^0-9+]', '', 'g') AS cleaned
            FROM customers_suppliers c
            JOIN customer_com_numbers n ON n.customer_number = c.customer_number
            WHERE c.is_supplier = false
              AND n.phone_number IS NOT NULL AND TRIM(n.phone_number) != ''
              AND (c.family_name ILIKE %s OR c.first_name ILIKE %s)
            ORDER BY c.family_name, c.first_name, n.counter
            LIMIT 50
        """, (term, term))
        rows = cursor.fetchall()
        if not rows:
            print("Keine Einträge gefunden.")
            return
        for r in rows:
            cust_nr, first, family, com_type, phone, cleaned = r[0], r[1], r[2], r[3], r[4], r[5]
            name = f"{first or ''} {family or ''}".strip() or "-"
            # Handy-Erkennung (wie in locosoft_addressbook_api)
            cleaned_s = (cleaned or "").strip()
            is_mobile = (
                (com_type and ("mobil" in (com_type or "").lower() or "handy" in (com_type or "").lower()))
                or (len(cleaned_s) >= 10 and cleaned_s.lstrip("0").lstrip("49").startswith(("15", "16", "17")))
            )
            print(f"  {cust_nr} | {name[:30]:30} | com_type={com_type!r:12} | phone={phone!r:25} | cleaned={cleaned!r:15} | Handy={is_mobile}")
    print("-" * 80)
    print("Falls com_type leer oder anders (z. B. 'Telefon') und Nummer 015x/016x/017x: Filter erkennt nur 'mobil'/'handy' oder Nummernmuster 15/16/17.")


if __name__ == "__main__":
    main()
