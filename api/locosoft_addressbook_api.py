"""
Locosoft Adressbuch-API – Kundendaten aus Locosoft oder DRIVE-Sync
==================================================================
TAG 211: Adressbuch (z. B. WhatsApp „Neuer Chat“).

- Wenn locosoft_kunden_sync (DRIVE) befüllt ist: Suche dort mit Volltext (bessere Suche).
- Sonst: Live-Abfrage an Locosoft (customers_suppliers + customer_com_numbers).
"""

import logging
from typing import List, Dict, Any, Optional

from api.db_utils import locosoft_session, db_session

logger = logging.getLogger(__name__)


def match_customer_by_phone(phone_number_normalized: str) -> Optional[Dict[str, Any]]:
    """
    Sucht in locosoft_kunden_sync einen Kunden mit passender Telefonnummer (phone oder phone_mobile).
    Für Matching eingehender WhatsApp-Nachrichten: Absender-Nummer → Kundenname.

    Args:
        phone_number_normalized: Bereits normalisierte Nummer (nur Ziffern, z. B. 491761234567)

    Returns:
        Dict mit customer_number, display_name, first_name oder None
    """
    if not phone_number_normalized or not phone_number_normalized.strip():
        return None
    digits = "".join(c for c in phone_number_normalized if c.isdigit())
    if not digits:
        return None
    try:
        with db_session() as conn:
            cur = conn.cursor()
            # Normalisierung in DB: nur Ziffern, führende 0 → 49; auch 49... mit 0... und 176... abgleichen
            cur.execute(
                """
                SELECT customer_number, display_name, first_name, family_name
                FROM locosoft_kunden_sync
                WHERE regexp_replace(regexp_replace(COALESCE(phone, ''), '[^0-9]', '', 'g'), '^0', '49') = %s
                   OR regexp_replace(regexp_replace(COALESCE(phone_mobile, ''), '[^0-9]', '', 'g'), '^0', '49') = %s
                   OR (length(%s) >= 12 AND substring(%s from 1 for 2) = '49'
                       AND (regexp_replace(COALESCE(phone, ''), '[^0-9]', '', 'g') = substring(%s from 3)
                            OR regexp_replace(COALESCE(phone_mobile, ''), '[^0-9]', '', 'g') = substring(%s from 3)))
                LIMIT 1
                """,
                (digits, digits, digits, digits, digits, digits),
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description] if cur.description else []
            return dict(zip(cols, row)) if cols else None
    except Exception as e:
        logger.debug(f"match_customer_by_phone: {e}")
        return None


# Deutsche Handy-Nummer: 15x, 16x, 17x (com_type Mobil oder Nummer 0176/49176...)
# Beispiele: 0176 1234567 (11 Ziffern), 491761234567 (12 Ziffern) – nach 1[5-7] mind. 7 Ziffern
def _mobile_phone_sql(alias: str) -> str:
    # Nach Bereinigung (nur Ziffern): 0176..., 49176..., 176...; mind. 7 Ziffern nach 1[5-7]
    return (
        f"({alias}.com_type ILIKE '%mobil%' OR {alias}.com_type ILIKE '%handy%' "
        f"OR regexp_replace({alias}.phone_number, '[^0-9+]', '', 'g') ~ '^0?(49)?1[5-7][0-9]{{7,}}$' "
        f"OR regexp_replace({alias}.phone_number, '[^0-9+]', '', 'g') ~ '^0?1[5-7][0-9]{{7,}}$')"
    )


def _search_customers_sync(
    q: str = "",
    subsidiary: Optional[int] = None,
    limit: int = 100,
    mobile_only: bool = False,
) -> Optional[List[Dict[str, Any]]]:
    """
    Sucht in DRIVE locosoft_kunden_sync mit Volltext (tsvector).
    Gibt None zurück, wenn Tabelle leer/fehlt oder Fehler.
    """
    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM locosoft_kunden_sync LIMIT 1",
            )
            if not cur.fetchone():
                return None
            where = ["1=1"]
            params: list = []
            if subsidiary is not None:
                where.append("subsidiary = %s")
                params.append(subsidiary)
            if mobile_only:
                where.append("(phone_mobile IS NOT NULL AND TRIM(phone_mobile) != '')")
            if q and q.strip():
                term = q.strip()
                where.append(
                    "(search_vector @@ plainto_tsquery('german', %s) "
                    "OR display_name ILIKE %s OR first_name ILIKE %s OR family_name ILIKE %s "
                    "OR customer_number::text LIKE %s)"
                )
                like_term = f"%{term}%"
                params.extend([term, like_term, like_term, like_term, like_term])
            params.append(limit)
            cur.execute(
                f"""
                SELECT customer_number, subsidiary, first_name, family_name, display_name,
                       home_street, zip_code, home_city, country_code,
                       COALESCE(phone_mobile, phone) AS phone,
                       phone AS phone_fallback,
                       email
                FROM locosoft_kunden_sync
                WHERE {" AND ".join(where)}
                ORDER BY family_name NULLS LAST, first_name NULLS LAST, customer_number
                LIMIT %s
                """,
                params,
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
            if not cols or not rows:
                return []
            out = []
            for r in rows:
                item = dict(zip(cols, r))
                item["contact_name"] = item.get("display_name") or f"Kunde {item.get('customer_number', '')}"
                item["phone_number"] = item.get("phone") or item.get("phone_fallback")
                item.pop("phone_fallback", None)
                out.append(item)
            return out
    except Exception as e:
        logger.debug(f"Sync-Tabelle Suche: {e}")
        return None


def search_customers(
    q: str = "",
    subsidiary: Optional[int] = None,
    limit: int = 100,
    mobile_only: bool = False,
) -> List[Dict[str, Any]]:
    """
    Sucht Kunden: zuerst in DRIVE locosoft_kunden_sync (Volltext), sonst Live in Locosoft.

    Args:
        q: Suchbegriff (Name, Kundennummer)
        subsidiary: Optional Locosoft subsidiary (1=DEG Opel, 2=HYU, 3=LAN)
        limit: Max. Anzahl Treffer
        mobile_only: Wenn True, nur Kunden mit Handynummer

    Returns:
        Liste von Dicts: customer_number, display_name, first_name, family_name,
        phone, email, home_street, zip_code, home_city, subsidiary
    """
    sync_result = _search_customers_sync(q=q, subsidiary=subsidiary, limit=limit, mobile_only=mobile_only)
    if sync_result is not None:
        return sync_result
    return _search_customers_locosoft_live(q=q, subsidiary=subsidiary, limit=limit, mobile_only=mobile_only)


def _search_customers_locosoft_live(
    q: str = "",
    subsidiary: Optional[int] = None,
    limit: int = 100,
    mobile_only: bool = False,
) -> List[Dict[str, Any]]:
    """Live-Suche in Locosoft (Fallback)."""
    result: List[Dict[str, Any]] = []
    try:
        with locosoft_session() as conn:
            cursor = conn.cursor()
            # Nur Kunden (keine Lieferanten), optional Standort
            where_clauses = ["c.is_supplier = false"]
            params: list = []
            if subsidiary is not None:
                where_clauses.append("c.subsidiary = %s")
                params.append(subsidiary)
            if q and q.strip():
                where_clauses.append(
                    "(c.family_name ILIKE %s OR c.first_name ILIKE %s OR c.customer_number::text LIKE %s)"
                )
                term = f"%{q.strip()}%"
                params.extend([term, term, term])
            if mobile_only:
                where_clauses.append(
                    "EXISTS (SELECT 1 FROM customer_com_numbers n2 WHERE n2.customer_number = c.customer_number "
                    "AND n2.phone_number IS NOT NULL AND TRIM(n2.phone_number) != '' AND " + _mobile_phone_sql("n2") + ")"
                )
            where_sql = " AND ".join(where_clauses)
            params.append(limit)

            phone_subquery_extra = (" AND " + _mobile_phone_sql("n")) if mobile_only else ""

            # Telefon: erste passende Nummer (bei mobile_only: nur Handy)
            # E-Mail: address-Feld, wenn es @ enthält
            cursor.execute(
                f"""
                SELECT
                    c.customer_number,
                    c.subsidiary,
                    c.first_name,
                    c.family_name,
                    TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.family_name, '')) AS display_name,
                    c.home_street,
                    c.zip_code,
                    c.home_city,
                    c.country_code,
                    (
                        SELECT n.phone_number
                        FROM customer_com_numbers n
                        WHERE n.customer_number = c.customer_number
                          AND n.phone_number IS NOT NULL
                          AND TRIM(n.phone_number) != ''
                          {phone_subquery_extra}
                        ORDER BY n.is_reference DESC NULLS LAST, n.counter
                        LIMIT 1
                    ) AS phone,
                    (
                        SELECT n.address
                        FROM customer_com_numbers n
                        WHERE n.customer_number = c.customer_number
                          AND n.address IS NOT NULL
                          AND n.address LIKE '%%@%%'
                        ORDER BY n.is_reference DESC NULLS LAST, n.counter
                        LIMIT 1
                    ) AS email
                FROM customers_suppliers c
                WHERE {where_sql}
                ORDER BY c.family_name NULLS LAST, c.first_name NULLS LAST, c.customer_number
                LIMIT %s
                """,
                params,
            )
            rows = cursor.fetchall()
            if not rows:
                return result
            desc = [d[0] for d in cursor.description] if cursor.description else []
            for row in rows:
                item = dict(zip(desc, row)) if desc and row else {}
                if item.get("display_name") is None or str(item.get("display_name", "")).strip() == "":
                    item["display_name"] = f"Kunde {item.get('customer_number', '')}"
                result.append(item)
    except Exception as e:
        logger.error(f"Locosoft Adressbuch-Suche: {e}")
        raise
    return result
