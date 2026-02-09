#!/usr/bin/env python3
"""
Aktualisiert TEK-Queries in Metabase mit getesteten SQL-Statements
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

def update_query(session_token, query_id, name, sql):
    """Aktualisiert eine Query in Metabase"""
    # Teste zuerst lokal
    print(f"  Teste lokal...")
    ok, result = test_query(sql)
    if not ok:
        print(f"  ❌ Lokaler Test fehlgeschlagen: {result}")
        return False
    
    print(f"  ✅ Lokaler Test erfolgreich ({result} Zeilen)")
    
    # Update in Metabase
    response = requests.put(
        f"{METABASE_URL}/api/card/{query_id}",
        headers={"X-Metabase-Session": session_token},
        json={
            "dataset_query": {
                "database": DB_ID,
                "type": "native",
                "native": {
                    "query": sql
                }
            }
        }
    )
    
    if response.status_code == 200:
        print(f"  ✅ Metabase Update erfolgreich")
        return True
    else:
        print(f"  ❌ Metabase Update fehlgeschlagen: {response.status_code}")
        print(f"     {response.text}")
        return False

def main():
    print("=== Update TEK-Queries in Metabase (mit Tests) ===\n")
    
    session = get_session()
    
    # Getestete Queries
    queries = [
        (42, "TEK Gesamt - Monat kumuliert", """
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
        """),
        (44, "TEK Verlauf", """
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
        """),
        (43, "TEK nach Standort", """
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
        WHEN u.branch_number = 1 THEN 'Deggendorf Opel'
        WHEN u.branch_number = 3 THEN 'Landau'
        WHEN u.branch_number = 2 THEN 'Deggendorf Hyundai'
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
GROUP BY u.branch_number, COALESCE(u.bereich, e.bereich)
ORDER BY u.branch_number, COALESCE(u.bereich, e.bereich);
        """)
    ]
    
    all_ok = True
    for query_id, name, sql in queries:
        print(f"\n{name} (ID: {query_id}):")
        if update_query(session, query_id, name, sql):
            print(f"  ✅ Erfolgreich aktualisiert")
        else:
            print(f"  ❌ Fehler beim Update")
            all_ok = False
    
    print("\n" + "="*50)
    if all_ok:
        print("✅ Alle Queries erfolgreich getestet und aktualisiert!")
    else:
        print("❌ Einige Queries konnten nicht aktualisiert werden")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
