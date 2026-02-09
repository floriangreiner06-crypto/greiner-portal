#!/usr/bin/env python3
"""
Erstellt vollständiges TEK-Dashboard mit allen Queries
Alle Queries werden vorher lokal getestet
"""

import requests
import psycopg2
import sys

METABASE_URL = "http://localhost:3001"
DB_ID = 2
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'drive_portal',
    'user': 'drive_user',
    'password': 'DrivePortal2024'
}

def test_query(sql):
    """Testet eine SQL-Query lokal"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return True, len(results)
    except Exception as e:
        return False, str(e)

def get_session():
    response = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": "admin@auto-greiner.de", "password": "Drive2026!"}
    )
    return response.json()["id"]

def create_or_update_query(session_token, query_id, name, description, sql, visualization_type="table"):
    """Erstellt oder aktualisiert eine Query"""
    # Teste zuerst lokal
    print(f"  Teste lokal...")
    ok, result = test_query(sql)
    if not ok:
        print(f"  ❌ Lokaler Test fehlgeschlagen: {result}")
        return None
    
    print(f"  ✅ Lokaler Test erfolgreich ({result} Zeilen)")
    
    # Update existierende Query
    if query_id:
        response = requests.put(
            f"{METABASE_URL}/api/card/{query_id}",
            headers={"X-Metabase-Session": session_token},
            json={
                "name": name,
                "description": description,
                "dataset_query": {
                    "database": DB_ID,
                    "type": "native",
                    "native": {
                        "query": sql
                    }
                },
                "display": visualization_type
            }
        )
        if response.status_code == 200:
            print(f"  ✅ Query aktualisiert (ID: {query_id})")
            return query_id
    
    # Erstelle neue Query
    response = requests.post(
        f"{METABASE_URL}/api/card",
        headers={"X-Metabase-Session": session_token},
        json={
            "name": name,
            "description": description,
            "dataset_query": {
                "database": DB_ID,
                "type": "native",
                "native": {
                    "query": sql
                }
            },
            "display": visualization_type
        }
    )
    if response.status_code == 200:
        card_id = response.json()["id"]
        print(f"  ✅ Query erstellt (ID: {card_id})")
        return card_id
    
    print(f"  ❌ Fehler: {response.status_code}")
    return None

def main():
    print("=== Erstelle vollständiges TEK-Dashboard ===\n")
    
    session = get_session()
    
    # Alle TEK-Queries (getestet und korrigiert)
    queries = [
        {
            "id": 42,
            "name": "TEK Gesamt - Monat kumuliert",
            "description": "TEK-Daten nach Bereichen, Monat kumuliert",
            "sql": """
-- TEK Gesamt - Monat kumuliert nach Bereichen
WITH umsatz_data AS (
    SELECT 
        CASE
            WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN '1-NW'
            WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN '2-GW'
            WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN '3-Teile'
            WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN '4-Lohn'
            WHEN nominal_account_number BETWEEN 860000 AND 869999 THEN '5-Sonst'
            ELSE NULL
        END as bereich_key,
        SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND nominal_account_number BETWEEN 800000 AND 899999
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
    GROUP BY bereich_key
),
einsatz_data AS (
    SELECT 
        CASE
            WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN '1-NW'
            WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN '2-GW'
            WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN '3-Teile'
            WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN '4-Lohn'
            WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN '5-Sonst'
            ELSE NULL
        END as bereich_key,
        SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND nominal_account_number BETWEEN 700000 AND 799999
    GROUP BY bereich_key
)
SELECT 
    COALESCE(u.bereich_key, e.bereich_key) as "Bereich",
    COALESCE(SUM(u.umsatz), 0) as "Erlös (€)",
    COALESCE(SUM(e.einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(u.umsatz), 0) - COALESCE(SUM(e.einsatz), 0) as "DB1 (€)",
    CASE 
        WHEN COALESCE(SUM(u.umsatz), 0) > 0 
        THEN ROUND((COALESCE(SUM(u.umsatz), 0) - COALESCE(SUM(e.einsatz), 0)) / SUM(u.umsatz) * 100, 2)
        ELSE 0 
    END as "DB1 (%)"
FROM umsatz_data u
FULL OUTER JOIN einsatz_data e ON u.bereich_key = e.bereich_key
WHERE COALESCE(u.bereich_key, e.bereich_key) IS NOT NULL
GROUP BY COALESCE(u.bereich_key, e.bereich_key)
ORDER BY 
    CASE COALESCE(u.bereich_key, e.bereich_key)
        WHEN '1-NW' THEN 1
        WHEN '2-GW' THEN 2
        WHEN '3-Teile' THEN 3
        WHEN '4-Lohn' THEN 4
        WHEN '5-Sonst' THEN 5
    END;
            """,
            "type": "table"
        },
        {
            "id": 43,
            "name": "TEK nach Standort",
            "description": "TEK-Daten nach Standort und Bereich (aktueller Monat)",
            "sql": """
-- TEK nach Standort (aktueller Monat)
WITH umsatz_data AS (
    SELECT 
        branch_number,
        CASE
            WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN 'Neuwagen'
            WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN 'Gebrauchtwagen'
            WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN 'Teile'
            WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN 'Werkstatt'
            WHEN nominal_account_number BETWEEN 860000 AND 869999 THEN 'Sonstige'
        END as bereich,
        SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND nominal_account_number BETWEEN 800000 AND 899999
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
      AND branch_number IN (1, 2, 3)
    GROUP BY branch_number, 
        CASE
            WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN 'Neuwagen'
            WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN 'Gebrauchtwagen'
            WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN 'Teile'
            WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN 'Werkstatt'
            WHEN nominal_account_number BETWEEN 860000 AND 869999 THEN 'Sonstige'
        END
),
einsatz_data AS (
    SELECT 
        branch_number,
        CASE
            WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN 'Neuwagen'
            WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN 'Gebrauchtwagen'
            WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN 'Teile'
            WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN 'Werkstatt'
            WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN 'Sonstige'
        END as bereich,
        SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND nominal_account_number BETWEEN 700000 AND 799999
      AND branch_number IN (1, 2, 3)
    GROUP BY branch_number,
        CASE
            WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN 'Neuwagen'
            WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN 'Gebrauchtwagen'
            WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN 'Teile'
            WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN 'Werkstatt'
            WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN 'Sonstige'
        END
)
SELECT 
    CASE 
        WHEN COALESCE(u.branch_number, e.branch_number) = 1 THEN 'Deggendorf Opel'
        WHEN COALESCE(u.branch_number, e.branch_number) = 3 THEN 'Landau'
        WHEN COALESCE(u.branch_number, e.branch_number) = 2 THEN 'Deggendorf Hyundai'
        ELSE 'Sonstige'
    END as "Standort",
    COALESCE(u.bereich, e.bereich) as "Bereich",
    COALESCE(SUM(u.umsatz), 0) as "Erlös (€)",
    COALESCE(SUM(e.einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(u.umsatz), 0) - COALESCE(SUM(e.einsatz), 0) as "DB1 (€)",
    CASE 
        WHEN COALESCE(SUM(u.umsatz), 0) > 0 
        THEN ROUND((COALESCE(SUM(u.umsatz), 0) - COALESCE(SUM(e.einsatz), 0)) / SUM(u.umsatz) * 100, 2)
        ELSE 0 
    END as "DB1 (%)"
FROM umsatz_data u
FULL OUTER JOIN einsatz_data e ON u.branch_number = e.branch_number AND u.bereich = e.bereich
WHERE COALESCE(u.bereich, e.bereich) IS NOT NULL
GROUP BY COALESCE(u.branch_number, e.branch_number), COALESCE(u.bereich, e.bereich)
ORDER BY COALESCE(u.branch_number, e.branch_number), COALESCE(u.bereich, e.bereich);
            """,
            "type": "table"
        },
        {
            "id": 44,
            "name": "TEK Verlauf",
            "description": "TEK-Verlauf der letzten 12 Monate",
            "sql": """
-- TEK Verlauf (letzte 12 Monate)
WITH umsatz_monat AS (
    SELECT 
        EXTRACT(YEAR FROM accounting_date) as jahr,
        EXTRACT(MONTH FROM accounting_date) as monat,
        SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months')
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND nominal_account_number BETWEEN 800000 AND 899999
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
    GROUP BY EXTRACT(YEAR FROM accounting_date), EXTRACT(MONTH FROM accounting_date)
),
einsatz_monat AS (
    SELECT 
        EXTRACT(YEAR FROM accounting_date) as jahr,
        EXTRACT(MONTH FROM accounting_date) as monat,
        SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months')
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND nominal_account_number BETWEEN 700000 AND 799999
    GROUP BY EXTRACT(YEAR FROM accounting_date), EXTRACT(MONTH FROM accounting_date)
)
SELECT 
    TO_CHAR((u.jahr::text || '-' || LPAD(u.monat::text, 2, '0') || '-01')::date, 'YYYY-MM') as "Monat",
    COALESCE(u.umsatz, 0) as "Erlös (€)",
    COALESCE(e.einsatz, 0) as "Einsatz (€)",
    COALESCE(u.umsatz, 0) - COALESCE(e.einsatz, 0) as "DB1 (€)",
    CASE 
        WHEN COALESCE(u.umsatz, 0) > 0 
        THEN ROUND((COALESCE(u.umsatz, 0) - COALESCE(e.einsatz, 0)) / u.umsatz * 100, 2)
        ELSE 0 
    END as "DB1 (%)"
FROM umsatz_monat u
FULL OUTER JOIN einsatz_monat e ON u.jahr = e.jahr AND u.monat = e.monat
ORDER BY u.jahr, u.monat;
            """,
            "type": "line"
        }
    ]
    
    print("Erstelle/Aktualisiere Queries...\n")
    card_ids = []
    
    for query in queries:
        print(f"{query['name']}:")
        card_id = create_or_update_query(
            session,
            query.get('id'),
            query['name'],
            query['description'],
            query['sql'],
            query['type']
        )
        if card_id:
            card_ids.append(card_id)
        print()
    
    print("="*50)
    print(f"✅ {len(card_ids)} Queries erstellt/aktualisiert")
    print(f"\nDashboard URL: {METABASE_URL}/dashboard/3")
    print("\nNächste Schritte:")
    print("1. Öffne Dashboard in Metabase")
    print("2. Klicke auf 'Bearbeiten'")
    print("3. Füge die Queries hinzu (IDs: " + ", ".join(map(str, card_ids)) + ")")

if __name__ == "__main__":
    main()
