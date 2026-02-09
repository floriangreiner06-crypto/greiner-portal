#!/usr/bin/env python3
"""
Erstellt vollständige TEK und BWA Dashboards in Metabase
Basierend auf DRIVE Portal Struktur
Alle Queries werden vorher lokal getestet
"""

import requests
import psycopg2
import sys
from datetime import date

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
                "display": visualization_type,
                "visualization_settings": {}
            }
        )
        if response.status_code == 200:
            print(f"  ✅ Query aktualisiert (ID: {query_id})")
            return query_id
        else:
            print(f"  ⚠️  Update fehlgeschlagen ({response.status_code}), versuche neu zu erstellen...")
            query_id = None  # Fallback: neu erstellen
    
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
            "display": visualization_type,
            "visualization_settings": {}
        }
    )
    if response.status_code == 200:
        card_id = response.json()["id"]
        print(f"  ✅ Query erstellt (ID: {card_id})")
        return card_id
    
    print(f"  ❌ Fehler: {response.status_code}")
    if response.status_code == 400:
        try:
            error_msg = response.json()
            print(f"  Fehlerdetails: {error_msg}")
        except:
            print(f"  Response: {response.text[:200]}")
    return None

def main():
    print("=== Erstelle vollständige TEK und BWA Dashboards ===\n")
    
    session = get_session()
    
    # TEK-Queries (wie in DRIVE)
    tek_queries = [
        {
            "id": 42,
            "name": "TEK Gesamt - Monat kumuliert",
            "description": "TEK-Daten nach Bereichen, Monat kumuliert (wie DRIVE)",
            "sql": """
-- TEK Gesamt - Monat kumuliert nach Bereichen (wie DRIVE)
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
      AND ((nominal_account_number BETWEEN 800000 AND 889999)
           OR (nominal_account_number BETWEEN 893200 AND 893299))
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
    CASE COALESCE(u.bereich_key, e.bereich_key)
        WHEN '1-NW' THEN 'Neuwagen'
        WHEN '2-GW' THEN 'Gebrauchtwagen'
        WHEN '3-Teile' THEN 'Teile/Service'
        WHEN '4-Lohn' THEN 'Werkstattlohn'
        WHEN '5-Sonst' THEN 'Sonstige'
    END as "Bereich",
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
      AND ((nominal_account_number BETWEEN 800000 AND 889999)
           OR (nominal_account_number BETWEEN 893200 AND 893299))
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
      AND ((nominal_account_number BETWEEN 800000 AND 889999)
           OR (nominal_account_number BETWEEN 893200 AND 893299))
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
    
    # BWA-Queries (wie in DRIVE)
    bwa_queries = [
        {
            "id": None,
            "name": "BWA Monatswerte",
            "description": "BWA-Positionen für aktuellen Monat (wie DRIVE)",
            "sql": """
-- BWA Monatswerte (aktueller Monat)
WITH umsatz AS (
    SELECT COALESCE(SUM(
        CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
    )/100.0, 0) as wert
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND ((nominal_account_number BETWEEN 800000 AND 889999)
           OR (nominal_account_number BETWEEN 893200 AND 893299))
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
),
einsatz AS (
    SELECT COALESCE(SUM(
        CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
    )/100.0, 0) as wert
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND nominal_account_number BETWEEN 700000 AND 799999
      AND nominal_account_number != 743002
),
variable_kosten AS (
    SELECT COALESCE(SUM(
        CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
    )/100.0, 0) as wert
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND (
        (nominal_account_number BETWEEN 415100 AND 415199)
        OR (nominal_account_number BETWEEN 435500 AND 435599)
        OR (nominal_account_number BETWEEN 455000 AND 456999 AND skr51_cost_center != 0)
        OR (nominal_account_number BETWEEN 487000 AND 487099 AND skr51_cost_center != 0)
        OR (nominal_account_number BETWEEN 491000 AND 497899)
        OR (nominal_account_number BETWEEN 891000 AND 891099)
      )
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
),
direkte_kosten AS (
    SELECT COALESCE(SUM(
        CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
    )/100.0, 0) as wert
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND (
        (nominal_account_number BETWEEN 415000 AND 415099)
        OR (nominal_account_number BETWEEN 420000 AND 429999)
        OR (nominal_account_number BETWEEN 430000 AND 435499)
        OR (nominal_account_number BETWEEN 435600 AND 454999)
        OR (nominal_account_number BETWEEN 457000 AND 486999)
        OR (nominal_account_number BETWEEN 487100 AND 490999)
        OR (nominal_account_number BETWEEN 498000 AND 499999)
      )
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
),
indirekte_kosten AS (
    SELECT COALESCE(SUM(
        CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
    )/100.0, 0) as wert
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND nominal_account_number BETWEEN 400000 AND 414999
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
),
neutral AS (
    SELECT COALESCE(SUM(
        CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
    )/100.0, 0) as wert
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND nominal_account_number BETWEEN 900000 AND 999999
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
),
bwa_data AS (
    SELECT 
        'Umsatzerlöse' as position,
        1 as sort_order,
        (SELECT wert FROM umsatz) as betrag
    UNION ALL
    SELECT 'Einsatzwerte', 2, (SELECT wert FROM einsatz)
    UNION ALL
    SELECT 'DB1', 3, (SELECT wert FROM umsatz) - (SELECT wert FROM einsatz)
    UNION ALL
    SELECT 'Variable Kosten', 4, (SELECT wert FROM variable_kosten)
    UNION ALL
    SELECT 'DB2', 5, (SELECT wert FROM umsatz) - (SELECT wert FROM einsatz) - (SELECT wert FROM variable_kosten)
    UNION ALL
    SELECT 'Direkte Kosten', 6, (SELECT wert FROM direkte_kosten)
    UNION ALL
    SELECT 'DB3', 7, (SELECT wert FROM umsatz) - (SELECT wert FROM einsatz) - (SELECT wert FROM variable_kosten) - (SELECT wert FROM direkte_kosten)
    UNION ALL
    SELECT 'Indirekte Kosten', 8, (SELECT wert FROM indirekte_kosten)
    UNION ALL
    SELECT 'Betriebsergebnis', 9, (SELECT wert FROM umsatz) - (SELECT wert FROM einsatz) - (SELECT wert FROM variable_kosten) - (SELECT wert FROM direkte_kosten) - (SELECT wert FROM indirekte_kosten)
    UNION ALL
    SELECT 'Neutrale Erträge', 10, (SELECT wert FROM neutral)
    UNION ALL
    SELECT 'Unternehmensergebnis', 11, (SELECT wert FROM umsatz) - (SELECT wert FROM einsatz) - (SELECT wert FROM variable_kosten) - (SELECT wert FROM direkte_kosten) - (SELECT wert FROM indirekte_kosten) + (SELECT wert FROM neutral)
)
SELECT 
    position as "Position",
    betrag as "Betrag (€)"
FROM bwa_data
ORDER BY sort_order;
            """,
            "type": "table"
        },
        {
            "id": None,
            "name": "BWA Verlauf",
            "description": "BWA-Verlauf der letzten 12 Monate",
            "sql": """
-- BWA Verlauf (letzte 12 Monate)
WITH monatswerte AS (
    SELECT 
        EXTRACT(YEAR FROM accounting_date) as jahr,
        EXTRACT(MONTH FROM accounting_date) as monat,
        -- Umsatz
        SUM(CASE WHEN debit_or_credit='H' AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299)) 
            THEN posted_value ELSE 0 END) / 100.0 as umsatz,
        -- Einsatz
        SUM(CASE WHEN debit_or_credit='S' AND nominal_account_number BETWEEN 700000 AND 799999 AND nominal_account_number != 743002
            THEN posted_value ELSE 0 END) / 100.0 as einsatz,
        -- Variable Kosten
        SUM(CASE WHEN debit_or_credit='S' AND (
            (nominal_account_number BETWEEN 415100 AND 415199)
            OR (nominal_account_number BETWEEN 435500 AND 435599)
            OR (nominal_account_number BETWEEN 455000 AND 456999 AND skr51_cost_center != 0)
            OR (nominal_account_number BETWEEN 487000 AND 487099 AND skr51_cost_center != 0)
            OR (nominal_account_number BETWEEN 491000 AND 497899)
            OR (nominal_account_number BETWEEN 891000 AND 891099)
        ) THEN posted_value ELSE 0 END) / 100.0 as variable,
        -- Direkte Kosten
        SUM(CASE WHEN debit_or_credit='S' AND (
            (nominal_account_number BETWEEN 415000 AND 415099)
            OR (nominal_account_number BETWEEN 420000 AND 429999)
            OR (nominal_account_number BETWEEN 430000 AND 435499)
            OR (nominal_account_number BETWEEN 435600 AND 454999)
            OR (nominal_account_number BETWEEN 457000 AND 486999)
            OR (nominal_account_number BETWEEN 487100 AND 490999)
            OR (nominal_account_number BETWEEN 498000 AND 499999)
        ) THEN posted_value ELSE 0 END) / 100.0 as direkte,
        -- Indirekte Kosten
        SUM(CASE WHEN debit_or_credit='S' AND nominal_account_number BETWEEN 400000 AND 414999
            THEN posted_value ELSE 0 END) / 100.0 as indirekte,
        -- Neutrale Erträge
        SUM(CASE WHEN debit_or_credit='H' AND nominal_account_number BETWEEN 900000 AND 999999
            THEN posted_value ELSE 0 END) / 100.0 as neutral
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months')
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
    GROUP BY EXTRACT(YEAR FROM accounting_date), EXTRACT(MONTH FROM accounting_date)
)
SELECT 
    TO_CHAR((jahr::text || '-' || LPAD(monat::text, 2, '0') || '-01')::date, 'YYYY-MM') as "Monat",
    umsatz as "Umsatz (€)",
    einsatz as "Einsatz (€)",
    umsatz - einsatz as "DB1 (€)",
    umsatz - einsatz - variable as "DB2 (€)",
    umsatz - einsatz - variable - direkte as "DB3 (€)",
    umsatz - einsatz - variable - direkte - indirekte as "Betriebsergebnis (€)",
    umsatz - einsatz - variable - direkte - indirekte + neutral as "Unternehmensergebnis (€)"
FROM monatswerte
ORDER BY jahr, monat;
            """,
            "type": "line"
        },
        {
            "id": None,
            "name": "BWA Vergleich Vorjahr",
            "description": "BWA-Vergleich: Aktuell vs. Vorjahresmonat",
            "sql": """
-- BWA Vergleich: Aktuell vs. Vorjahresmonat
WITH aktuell AS (
    SELECT 
        SUM(CASE WHEN debit_or_credit='H' AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
            THEN posted_value ELSE 0 END) / 100.0 as umsatz,
        SUM(CASE WHEN debit_or_credit='S' AND nominal_account_number BETWEEN 700000 AND 799999 AND nominal_account_number != 743002
            THEN posted_value ELSE 0 END) / 100.0 as einsatz,
        SUM(CASE WHEN debit_or_credit='S' AND (
            (nominal_account_number BETWEEN 415100 AND 415199)
            OR (nominal_account_number BETWEEN 435500 AND 435599)
            OR (nominal_account_number BETWEEN 455000 AND 456999 AND skr51_cost_center != 0)
            OR (nominal_account_number BETWEEN 487000 AND 487099 AND skr51_cost_center != 0)
            OR (nominal_account_number BETWEEN 491000 AND 497899)
            OR (nominal_account_number BETWEEN 891000 AND 891099)
        ) THEN posted_value ELSE 0 END) / 100.0 as variable,
        SUM(CASE WHEN debit_or_credit='S' AND (
            (nominal_account_number BETWEEN 415000 AND 415099)
            OR (nominal_account_number BETWEEN 420000 AND 429999)
            OR (nominal_account_number BETWEEN 430000 AND 435499)
            OR (nominal_account_number BETWEEN 435600 AND 454999)
            OR (nominal_account_number BETWEEN 457000 AND 486999)
            OR (nominal_account_number BETWEEN 487100 AND 490999)
            OR (nominal_account_number BETWEEN 498000 AND 499999)
        ) THEN posted_value ELSE 0 END) / 100.0 as direkte,
        SUM(CASE WHEN debit_or_credit='S' AND nominal_account_number BETWEEN 400000 AND 414999
            THEN posted_value ELSE 0 END) / 100.0 as indirekte,
        SUM(CASE WHEN debit_or_credit='H' AND nominal_account_number BETWEEN 900000 AND 999999
            THEN posted_value ELSE 0 END) / 100.0 as neutral
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
),
vorjahr AS (
    SELECT 
        SUM(CASE WHEN debit_or_credit='H' AND ((nominal_account_number BETWEEN 800000 AND 889999) OR (nominal_account_number BETWEEN 893200 AND 893299))
            THEN posted_value ELSE 0 END) / 100.0 as umsatz,
        SUM(CASE WHEN debit_or_credit='S' AND nominal_account_number BETWEEN 700000 AND 799999 AND nominal_account_number != 743002
            THEN posted_value ELSE 0 END) / 100.0 as einsatz,
        SUM(CASE WHEN debit_or_credit='S' AND (
            (nominal_account_number BETWEEN 415100 AND 415199)
            OR (nominal_account_number BETWEEN 435500 AND 435599)
            OR (nominal_account_number BETWEEN 455000 AND 456999 AND skr51_cost_center != 0)
            OR (nominal_account_number BETWEEN 487000 AND 487099 AND skr51_cost_center != 0)
            OR (nominal_account_number BETWEEN 491000 AND 497899)
            OR (nominal_account_number BETWEEN 891000 AND 891099)
        ) THEN posted_value ELSE 0 END) / 100.0 as variable,
        SUM(CASE WHEN debit_or_credit='S' AND (
            (nominal_account_number BETWEEN 415000 AND 415099)
            OR (nominal_account_number BETWEEN 420000 AND 429999)
            OR (nominal_account_number BETWEEN 430000 AND 435499)
            OR (nominal_account_number BETWEEN 435600 AND 454999)
            OR (nominal_account_number BETWEEN 457000 AND 486999)
            OR (nominal_account_number BETWEEN 487100 AND 490999)
            OR (nominal_account_number BETWEEN 498000 AND 499999)
        ) THEN posted_value ELSE 0 END) / 100.0 as direkte,
        SUM(CASE WHEN debit_or_credit='S' AND nominal_account_number BETWEEN 400000 AND 414999
            THEN posted_value ELSE 0 END) / 100.0 as indirekte,
        SUM(CASE WHEN debit_or_credit='H' AND nominal_account_number BETWEEN 900000 AND 999999
            THEN posted_value ELSE 0 END) / 100.0 as neutral
    FROM loco_journal_accountings
    WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 year')
      AND accounting_date < DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 year') + INTERVAL '1 month'
      AND NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')
),
vergleich_data AS (
    SELECT 
        'Umsatz' as position,
        1 as sort_order,
        (SELECT umsatz FROM aktuell) as aktuell,
        (SELECT umsatz FROM vorjahr) as vorjahr
    UNION ALL
    SELECT 'DB1', 2,
        (SELECT umsatz - einsatz FROM aktuell),
        (SELECT umsatz - einsatz FROM vorjahr)
    UNION ALL
    SELECT 'DB2', 3,
        (SELECT umsatz - einsatz - variable FROM aktuell),
        (SELECT umsatz - einsatz - variable FROM vorjahr)
    UNION ALL
    SELECT 'DB3', 4,
        (SELECT umsatz - einsatz - variable - direkte FROM aktuell),
        (SELECT umsatz - einsatz - variable - direkte FROM vorjahr)
    UNION ALL
    SELECT 'Betriebsergebnis', 5,
        (SELECT umsatz - einsatz - variable - direkte - indirekte FROM aktuell),
        (SELECT umsatz - einsatz - variable - direkte - indirekte FROM vorjahr)
    UNION ALL
    SELECT 'Unternehmensergebnis', 6,
        (SELECT umsatz - einsatz - variable - direkte - indirekte + neutral FROM aktuell),
        (SELECT umsatz - einsatz - variable - direkte - indirekte + neutral FROM vorjahr)
)
SELECT 
    position as "Position",
    aktuell as "Aktuell (€)",
    vorjahr as "Vorjahr (€)",
    aktuell - vorjahr as "Differenz (€)",
    CASE WHEN vorjahr != 0 
        THEN ROUND((aktuell - vorjahr) / ABS(vorjahr) * 100, 1)
        ELSE NULL
    END as "Änderung (%)"
FROM vergleich_data
ORDER BY sort_order;
            """,
            "type": "table"
        }
    ]
    
    print("1. TEK-Queries erstellen/aktualisieren...\n")
    tek_card_ids = []
    for query in tek_queries:
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
            tek_card_ids.append(card_id)
        print()
    
    print("\n2. BWA-Queries erstellen...\n")
    bwa_card_ids = []
    for query in bwa_queries:
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
            bwa_card_ids.append(card_id)
        print()
    
    # Dashboards erstellen/aktualisieren
    print("\n3. Dashboards erstellen und Queries hinzufügen...\n")
    
    # TEK Dashboard
    tek_dashboard_id = 3
    response = requests.get(
        f"{METABASE_URL}/api/dashboard/{tek_dashboard_id}",
        headers={"X-Metabase-Session": session}
    )
    if response.status_code == 200:
        print(f"✅ TEK Dashboard existiert bereits (ID: {tek_dashboard_id})")
    else:
        response = requests.post(
            f"{METABASE_URL}/api/dashboard",
            headers={"X-Metabase-Session": session},
            json={
                "name": "TEK Dashboard",
                "description": "Tägliche Erfolgskontrolle - wie DRIVE Portal"
            }
        )
        if response.status_code == 200:
            tek_dashboard_id = response.json()['id']
            print(f"✅ TEK Dashboard erstellt (ID: {tek_dashboard_id})")
    
    # BWA Dashboard
    response = requests.post(
        f"{METABASE_URL}/api/dashboard",
        headers={"X-Metabase-Session": session},
        json={
            "name": "BWA Dashboard",
            "description": "Betriebswirtschaftliche Auswertung - wie DRIVE Portal"
        }
    )
    if response.status_code == 200:
        bwa_dashboard_id = response.json()['id']
        print(f"✅ BWA Dashboard erstellt (ID: {bwa_dashboard_id})")
    else:
        print(f"❌ BWA Dashboard konnte nicht erstellt werden: {response.status_code}")
        bwa_dashboard_id = None
    
    # Queries zu Dashboards hinzufügen
    print("\n4. Queries zu Dashboards hinzufügen...\n")
    
    def add_cards_to_dashboard(dashboard_id, card_ids):
        """Fügt Cards zu einem Dashboard hinzu"""
        if not dashboard_id or not card_ids:
            return
        
        # Hole aktuelle Dashboard-Daten
        response = requests.get(
            f"{METABASE_URL}/api/dashboard/{dashboard_id}",
            headers={"X-Metabase-Session": session}
        )
        if response.status_code != 200:
            print(f"  ⚠️  Dashboard {dashboard_id} nicht gefunden")
            return
        
        dashboard = response.json()
        existing_card_ids = [c['card_id'] for c in dashboard.get('ordered_cards', [])]
        
        # Füge nur neue Cards hinzu
        new_cards = [cid for cid in card_ids if cid not in existing_card_ids]
        if not new_cards:
            print(f"  ✅ Alle Queries bereits im Dashboard")
            return
        
        # Erstelle Dashboard-Cards
        cards_to_add = []
        for i, card_id in enumerate(new_cards):
            cards_to_add.append({
                "cardId": card_id,
                "row": i // 2,  # 2 Spalten
                "col": (i % 2) * 6,  # 6 Spalten pro Card
                "sizeX": 6,
                "sizeY": 4
            })
        
        # Update Dashboard
        response = requests.put(
            f"{METABASE_URL}/api/dashboard/{dashboard_id}/cards",
            headers={"X-Metabase-Session": session},
            json={"cards": cards_to_add}
        )
        if response.status_code == 200:
            print(f"  ✅ {len(new_cards)} Queries hinzugefügt")
        else:
            print(f"  ⚠️  Fehler beim Hinzufügen: {response.status_code}")
            print(f"  Manuell hinzufügen: {', '.join(map(str, new_cards))}")
    
    if tek_card_ids:
        print("TEK Dashboard:")
        add_cards_to_dashboard(tek_dashboard_id, tek_card_ids)
    
    if bwa_card_ids and bwa_dashboard_id:
        print("\nBWA Dashboard:")
        add_cards_to_dashboard(bwa_dashboard_id, bwa_card_ids)
    
    print("\n" + "="*60)
    print("✅ Fertig!")
    print("="*60)
    print(f"\nTEK Dashboard: {METABASE_URL}/dashboard/3")
    print(f"  Queries: {', '.join(map(str, tek_card_ids))}")
    if bwa_dashboard_id:
        print(f"\nBWA Dashboard: {METABASE_URL}/dashboard/{bwa_dashboard_id}")
        print(f"  Queries: {', '.join(map(str, bwa_card_ids))}")
    print("\nNächste Schritte:")
    print("1. Öffne Dashboards in Metabase")
    print("2. Klicke auf 'Bearbeiten'")
    print("3. Füge die Queries hinzu")
    print("4. Passe Visualisierungen an")

if __name__ == "__main__":
    main()
