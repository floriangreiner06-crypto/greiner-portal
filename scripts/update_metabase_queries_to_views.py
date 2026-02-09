#!/usr/bin/env python3
"""
Aktualisiert Metabase-Queries, um Materialized Views zu nutzen
Statt direkt auf loco_journal_accountings zuzugreifen, nutzen wir fact_bwa und dim_*
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

def update_query(session_token, query_id, name, description, sql, visualization_type="table"):
    """Aktualisiert eine Query"""
    # Teste zuerst lokal
    print(f"  Teste lokal...")
    ok, result = test_query(sql)
    if not ok:
        print(f"  ❌ Lokaler Test fehlgeschlagen: {result}")
        return False
    
    print(f"  ✅ Lokaler Test erfolgreich ({result} Zeilen)")
    
    # Update Query
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
        return True
    else:
        print(f"  ❌ Fehler: {response.status_code}")
        try:
            error = response.json()
            print(f"  Details: {error}")
        except:
            print(f"  Response: {response.text[:200]}")
        return False

def main():
    print("=== Aktualisiere Metabase-Queries auf Materialized Views ===\n")
    
    session = get_session()
    
    # TEK-Queries mit Views
    tek_queries = [
        {
            "id": 42,
            "name": "TEK Gesamt - Monat kumuliert",
            "description": "TEK nach Bereichen inkl. Vormonat/Vorjahr (wie DRIVE). Stück/DB-Stück nur in DRIVE (Locosoft).",
            "sql": """
-- TEK Gesamt - Monat kumuliert + Vormonat/Vorjahr (nutzt fact_bwa)
WITH umsatz_data AS (
    SELECT 
        CASE WHEN konto_id BETWEEN 810000 AND 819999 THEN '1-NW' WHEN konto_id BETWEEN 820000 AND 829999 THEN '2-GW'
        WHEN konto_id BETWEEN 830000 AND 839999 THEN '3-Teile' WHEN konto_id BETWEEN 840000 AND 849999 THEN '4-Lohn'
        WHEN konto_id BETWEEN 860000 AND 869999 THEN '5-Sonst' ELSE NULL END as bereich_key,
        SUM(-betrag) as umsatz
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE) AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND ((konto_id BETWEEN 800000 AND 889999) OR (konto_id BETWEEN 893200 AND 893299)) AND debit_or_credit = 'H'
      AND NOT (standort_id = 0 AND document_number::text LIKE 'GV%')
    GROUP BY bereich_key
),
einsatz_data AS (
    SELECT 
        CASE WHEN konto_id BETWEEN 710000 AND 719999 THEN '1-NW' WHEN konto_id BETWEEN 720000 AND 729999 THEN '2-GW'
        WHEN konto_id BETWEEN 730000 AND 739999 THEN '3-Teile' WHEN konto_id BETWEEN 740000 AND 749999 THEN '4-Lohn'
        WHEN konto_id BETWEEN 760000 AND 769999 THEN '5-Sonst' ELSE NULL END as bereich_key,
        SUM(betrag) as einsatz
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE) AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND konto_id BETWEEN 700000 AND 799999 AND debit_or_credit = 'S'
    GROUP BY bereich_key
),
vm_umsatz AS (
    SELECT 
        CASE WHEN konto_id BETWEEN 810000 AND 819999 THEN '1-NW' WHEN konto_id BETWEEN 820000 AND 829999 THEN '2-GW'
        WHEN konto_id BETWEEN 830000 AND 839999 THEN '3-Teile' WHEN konto_id BETWEEN 840000 AND 849999 THEN '4-Lohn'
        WHEN konto_id BETWEEN 860000 AND 869999 THEN '5-Sonst' END as bereich_key, SUM(-betrag) as umsatz
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND zeit_id < DATE_TRUNC('month', CURRENT_DATE)
      AND ((konto_id BETWEEN 800000 AND 889999) OR (konto_id BETWEEN 893200 AND 893299)) AND debit_or_credit = 'H'
      AND NOT (standort_id = 0 AND document_number::text LIKE 'GV%')
    GROUP BY 1
),
vm_einsatz AS (
    SELECT 
        CASE WHEN konto_id BETWEEN 710000 AND 719999 THEN '1-NW' WHEN konto_id BETWEEN 720000 AND 729999 THEN '2-GW'
        WHEN konto_id BETWEEN 730000 AND 739999 THEN '3-Teile' WHEN konto_id BETWEEN 740000 AND 749999 THEN '4-Lohn'
        WHEN konto_id BETWEEN 760000 AND 769999 THEN '5-Sonst' END as bereich_key, SUM(betrag) as einsatz
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND zeit_id < DATE_TRUNC('month', CURRENT_DATE)
      AND konto_id BETWEEN 700000 AND 799999 AND debit_or_credit = 'S'
    GROUP BY 1
),
vj_umsatz AS (
    SELECT 
        CASE WHEN konto_id BETWEEN 810000 AND 819999 THEN '1-NW' WHEN konto_id BETWEEN 820000 AND 829999 THEN '2-GW'
        WHEN konto_id BETWEEN 830000 AND 839999 THEN '3-Teile' WHEN konto_id BETWEEN 840000 AND 849999 THEN '4-Lohn'
        WHEN konto_id BETWEEN 860000 AND 869999 THEN '5-Sonst' END as bereich_key, SUM(-betrag) as umsatz
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', (CURRENT_DATE - INTERVAL '1 year')::date)
      AND zeit_id < DATE_TRUNC('month', (CURRENT_DATE - INTERVAL '1 year')::date) + INTERVAL '1 month'
      AND ((konto_id BETWEEN 800000 AND 889999) OR (konto_id BETWEEN 893200 AND 893299)) AND debit_or_credit = 'H'
      AND NOT (standort_id = 0 AND document_number::text LIKE 'GV%')
    GROUP BY 1
),
vj_einsatz AS (
    SELECT 
        CASE WHEN konto_id BETWEEN 710000 AND 719999 THEN '1-NW' WHEN konto_id BETWEEN 720000 AND 729999 THEN '2-GW'
        WHEN konto_id BETWEEN 730000 AND 739999 THEN '3-Teile' WHEN konto_id BETWEEN 740000 AND 749999 THEN '4-Lohn'
        WHEN konto_id BETWEEN 760000 AND 769999 THEN '5-Sonst' END as bereich_key, SUM(betrag) as einsatz
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', (CURRENT_DATE - INTERVAL '1 year')::date)
      AND zeit_id < DATE_TRUNC('month', (CURRENT_DATE - INTERVAL '1 year')::date) + INTERVAL '1 month'
      AND konto_id BETWEEN 700000 AND 799999 AND debit_or_credit = 'S'
    GROUP BY 1
),
cur AS (
    SELECT COALESCE(u.bereich_key, e.bereich_key) as bereich_key,
           COALESCE(u.umsatz, 0) as umsatz, COALESCE(e.einsatz, 0) as einsatz
    FROM umsatz_data u
    FULL OUTER JOIN einsatz_data e ON u.bereich_key = e.bereich_key
    WHERE COALESCE(u.bereich_key, e.bereich_key) IS NOT NULL
),
vm AS (
    SELECT u.bereich_key, COALESCE(u.umsatz, 0) - COALESCE(e.einsatz, 0) as db1
    FROM vm_umsatz u
    FULL OUTER JOIN vm_einsatz e ON u.bereich_key = e.bereich_key
),
vj AS (
    SELECT u.bereich_key, COALESCE(u.umsatz, 0) - COALESCE(e.einsatz, 0) as db1
    FROM vj_umsatz u
    FULL OUTER JOIN vj_einsatz e ON u.bereich_key = e.bereich_key
)
SELECT 
    CASE c.bereich_key WHEN '1-NW' THEN 'Neuwagen' WHEN '2-GW' THEN 'Gebrauchtwagen' WHEN '3-Teile' THEN 'Teile/Service'
    WHEN '4-Lohn' THEN 'Werkstattlohn' WHEN '5-Sonst' THEN 'Sonstige' END as "Bereich",
    ROUND(c.umsatz, 2) as "Erlös (€)",
    ROUND(c.einsatz, 2) as "Einsatz (€)",
    ROUND(c.umsatz - c.einsatz, 2) as "DB1 (€)",
    NULL::int as "Stück",
    NULL::numeric as "DB/Stück (€)",
    ROUND(CASE WHEN c.umsatz > 0 THEN (c.umsatz - c.einsatz) / c.umsatz * 100 ELSE 0 END, 2) as "DB1 (%)",
    ROUND(vm.db1, 2) as "VM DB1 (€)",
    ROUND(vj.db1, 2) as "VJ DB1 (€)"
FROM cur c
LEFT JOIN vm ON vm.bereich_key = c.bereich_key
LEFT JOIN vj ON vj.bereich_key = c.bereich_key
ORDER BY CASE c.bereich_key WHEN '1-NW' THEN 1 WHEN '2-GW' THEN 2 WHEN '3-Teile' THEN 3 WHEN '4-Lohn' THEN 4 WHEN '5-Sonst' THEN 5 END;
            """,
            "type": "table"
        },
        {
            "id": 43,
            "name": "TEK nach Standort",
            "description": "TEK nach Standort und Bereich inkl. Kumulation pro Standort und pro Kostenstelle (Bereich). Stück/DB-Stück (Locosoft) in Metabase leer.",
            "sql": """
-- TEK nach Standort: Kumulation pro Standort + pro Kostenstelle (Bereich), Spalten Stück/DB-Stück
WITH umsatz_data AS (
    SELECT standort_id,
        CASE WHEN konto_id BETWEEN 810000 AND 819999 THEN 'Neuwagen' WHEN konto_id BETWEEN 820000 AND 829999 THEN 'Gebrauchtwagen'
        WHEN konto_id BETWEEN 830000 AND 839999 THEN 'Teile' WHEN konto_id BETWEEN 840000 AND 849999 THEN 'Werkstatt'
        WHEN konto_id BETWEEN 860000 AND 869999 THEN 'Sonstige' END as bereich,
        SUM(-betrag) as umsatz
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE) AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND ((konto_id BETWEEN 800000 AND 889999) OR (konto_id BETWEEN 893200 AND 893299)) AND debit_or_credit = 'H'
      AND NOT (standort_id = 0 AND document_number::text LIKE 'GV%') AND standort_id IN (1, 2, 3)
    GROUP BY standort_id, bereich
),
einsatz_data AS (
    SELECT standort_id,
        CASE WHEN konto_id BETWEEN 710000 AND 719999 THEN 'Neuwagen' WHEN konto_id BETWEEN 720000 AND 729999 THEN 'Gebrauchtwagen'
        WHEN konto_id BETWEEN 730000 AND 739999 THEN 'Teile' WHEN konto_id BETWEEN 740000 AND 749999 THEN 'Werkstatt'
        WHEN konto_id BETWEEN 760000 AND 769999 THEN 'Sonstige' END as bereich,
        SUM(betrag) as einsatz
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE) AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND konto_id BETWEEN 700000 AND 799999 AND debit_or_credit = 'S' AND standort_id IN (1, 2, 3)
    GROUP BY standort_id, bereich
),
detail AS (
    SELECT
        COALESCE(u.standort_id, e.standort_id) as standort_id,
        CASE COALESCE(u.standort_id, e.standort_id) WHEN 1 THEN 'Deggendorf Opel' WHEN 2 THEN 'Deggendorf Hyundai' WHEN 3 THEN 'Landau' ELSE 'Sonstige' END as standort_name,
        COALESCE(u.bereich, e.bereich) as bereich,
        COALESCE(SUM(u.umsatz), 0) as umsatz,
        COALESCE(SUM(e.einsatz), 0) as einsatz,
        CASE WHEN COALESCE(SUM(u.umsatz), 0) > 0 THEN (COALESCE(SUM(u.umsatz), 0) - COALESCE(SUM(e.einsatz), 0)) / SUM(u.umsatz) * 100 ELSE 0 END as db1_pct
    FROM umsatz_data u
    FULL OUTER JOIN einsatz_data e ON u.standort_id = e.standort_id AND u.bereich = e.bereich
    WHERE COALESCE(u.bereich, e.bereich) IS NOT NULL
    GROUP BY COALESCE(u.standort_id, e.standort_id), COALESCE(u.bereich, e.bereich)
),
summen_standort AS (
    SELECT standort_id, standort_name,
           SUM(umsatz) as umsatz, SUM(einsatz) as einsatz,
           CASE WHEN SUM(umsatz) > 0 THEN (SUM(umsatz) - SUM(einsatz)) / SUM(umsatz) * 100 ELSE 0 END as db1_pct
    FROM detail
    GROUP BY standort_id, standort_name
),
summen_bereich AS (
    SELECT bereich,
           SUM(umsatz) as umsatz, SUM(einsatz) as einsatz,
           CASE WHEN SUM(umsatz) > 0 THEN (SUM(umsatz) - SUM(einsatz)) / SUM(umsatz) * 100 ELSE 0 END as db1_pct
    FROM detail
    GROUP BY bereich
),
combined AS (
    SELECT 0 as sort_typ, standort_id, standort_name as "Standort", bereich as "Bereich",
           ROUND(umsatz, 2) as "Erlös (€)", ROUND(einsatz, 2) as "Einsatz (€)",
           ROUND(umsatz - einsatz, 2) as "DB1 (€)",
           NULL::int as "Stück", NULL::numeric as "DB/Stück (€)",
           ROUND(db1_pct, 2) as "DB1 (%)"
    FROM detail
    UNION ALL
    SELECT 0 as sort_typ, standort_id, standort_name as "Standort", 'Summe ' || standort_name as "Bereich",
           ROUND(umsatz, 2) as "Erlös (€)", ROUND(einsatz, 2) as "Einsatz (€)",
           ROUND(umsatz - einsatz, 2) as "DB1 (€)",
           NULL::int, NULL::numeric,
           ROUND(db1_pct, 2) as "DB1 (%)"
    FROM summen_standort
    UNION ALL
    SELECT 1 as sort_typ, NULL::int, 'Gesamt' as "Standort", 'Summe ' || bereich as "Bereich",
           ROUND(umsatz, 2) as "Erlös (€)", ROUND(einsatz, 2) as "Einsatz (€)",
           ROUND(umsatz - einsatz, 2) as "DB1 (€)",
           NULL::int, NULL::numeric,
           ROUND(db1_pct, 2) as "DB1 (%)"
    FROM summen_bereich
)
SELECT "Standort", "Bereich", "Erlös (€)", "Einsatz (€)", "DB1 (€)", "Stück", "DB/Stück (€)", "DB1 (%)"
FROM combined
ORDER BY sort_typ, standort_id NULLS LAST, CASE WHEN "Bereich" LIKE 'Summe %' THEN 1 ELSE 0 END,
         CASE "Bereich" WHEN 'Neuwagen' THEN 1 WHEN 'Gebrauchtwagen' THEN 2 WHEN 'Teile' THEN 3 WHEN 'Werkstatt' THEN 4 WHEN 'Sonstige' THEN 5 ELSE 6 END;
            """,
            "type": "table"
        },
        {
            "id": 44,
            "name": "TEK Verlauf",
            "description": "TEK-Verlauf der letzten 12 Monate (nutzt fact_bwa)",
            "sql": """
-- TEK Verlauf (letzte 12 Monate, nutzt fact_bwa)
WITH umsatz_monat AS (
    SELECT 
        EXTRACT(YEAR FROM zeit_id) as jahr,
        EXTRACT(MONTH FROM zeit_id) as monat,
        SUM(betrag) as umsatz
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months')
      AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND ((konto_id BETWEEN 800000 AND 889999)
           OR (konto_id BETWEEN 893200 AND 893299))
      AND debit_or_credit = 'H'
      AND NOT (standort_id = 0 AND document_number::text LIKE 'GV%')
    GROUP BY EXTRACT(YEAR FROM zeit_id), EXTRACT(MONTH FROM zeit_id)
),
einsatz_monat AS (
    SELECT 
        EXTRACT(YEAR FROM zeit_id) as jahr,
        EXTRACT(MONTH FROM zeit_id) as monat,
        SUM(betrag) as einsatz
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months')
      AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND konto_id BETWEEN 700000 AND 799999
      AND debit_or_credit = 'S'
    GROUP BY EXTRACT(YEAR FROM zeit_id), EXTRACT(MONTH FROM zeit_id)
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
    
    # BWA-Queries mit Views
    bwa_queries = [
        {
            "id": 49,
            "name": "BWA Monatswerte",
            "description": "BWA-Positionen für aktuellen Monat (nutzt fact_bwa)",
            "sql": """
-- BWA Monatswerte (nutzt fact_bwa Materialized View)
WITH umsatz AS (
    SELECT COALESCE(SUM(-betrag), 0) as wert
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE)
      AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND ((konto_id BETWEEN 800000 AND 889999)
           OR (konto_id BETWEEN 893200 AND 893299))
      AND debit_or_credit = 'H'
      AND NOT (standort_id = 0 AND document_number::text LIKE 'GV%')
      AND NOT (standort_id = 0 AND document_number::text LIKE 'GV%')
),
einsatz AS (
    SELECT COALESCE(SUM(betrag), 0) as wert
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE)
      AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND konto_id BETWEEN 700000 AND 799999
      AND konto_id != 743002
      AND debit_or_credit = 'S'
),
variable_kosten AS (
    SELECT COALESCE(SUM(betrag), 0) as wert
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE)
      AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND (
        (konto_id BETWEEN 415100 AND 415199)
        OR (konto_id BETWEEN 435500 AND 435599)
        OR (konto_id BETWEEN 455000 AND 456999 AND kst_id != 0)
        OR (konto_id BETWEEN 487000 AND 487099 AND kst_id != 0)
        OR (konto_id BETWEEN 491000 AND 497899)
        OR (konto_id BETWEEN 891000 AND 891099)
      )
      AND debit_or_credit = 'S'
),
direkte_kosten AS (
    SELECT COALESCE(SUM(betrag), 0) as wert
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE)
      AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND (
        (konto_id BETWEEN 415000 AND 415099)
        OR (konto_id BETWEEN 420000 AND 429999)
        OR (konto_id BETWEEN 430000 AND 435499)
        OR (konto_id BETWEEN 435600 AND 454999)
        OR (konto_id BETWEEN 457000 AND 486999)
        OR (konto_id BETWEEN 487100 AND 490999)
        OR (konto_id BETWEEN 498000 AND 499999)
      )
      AND debit_or_credit = 'S'
),
indirekte_kosten AS (
    SELECT COALESCE(SUM(betrag), 0) as wert
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE)
      AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND konto_id BETWEEN 400000 AND 414999
      AND debit_or_credit = 'S'
),
neutral AS (
    SELECT COALESCE(SUM(-betrag), 0) as wert
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE)
      AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
      AND konto_id BETWEEN 900000 AND 999999
      AND debit_or_credit = 'H'
      AND NOT (standort_id = 0 AND document_number::text LIKE 'GV%')
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
            "id": 50,
            "name": "BWA Verlauf",
            "description": "BWA-Verlauf der letzten 12 Monate (nutzt fact_bwa)",
            "sql": """
-- BWA Verlauf (letzte 12 Monate, nutzt fact_bwa)
WITH monatswerte AS (
    SELECT 
        EXTRACT(YEAR FROM zeit_id) as jahr,
        EXTRACT(MONTH FROM zeit_id) as monat,
        SUM(CASE WHEN debit_or_credit='H' AND ((konto_id BETWEEN 800000 AND 889999) OR (konto_id BETWEEN 893200 AND 893299)) 
            THEN -betrag ELSE 0 END) as umsatz,
        SUM(CASE WHEN debit_or_credit='S' AND konto_id BETWEEN 700000 AND 799999 AND konto_id != 743002
            THEN betrag ELSE 0 END) as einsatz,
        SUM(CASE WHEN debit_or_credit='S' AND (
            (konto_id BETWEEN 415100 AND 415199)
            OR (konto_id BETWEEN 435500 AND 435599)
            OR (konto_id BETWEEN 455000 AND 456999 AND kst_id != 0)
            OR (konto_id BETWEEN 487000 AND 487099 AND kst_id != 0)
            OR (konto_id BETWEEN 491000 AND 497899)
            OR (konto_id BETWEEN 891000 AND 891099)
        ) THEN betrag ELSE 0 END) as variable,
        SUM(CASE WHEN debit_or_credit='S' AND (
            (konto_id BETWEEN 415000 AND 415099)
            OR (konto_id BETWEEN 420000 AND 429999)
            OR (konto_id BETWEEN 430000 AND 435499)
            OR (konto_id BETWEEN 435600 AND 454999)
            OR (konto_id BETWEEN 457000 AND 486999)
            OR (konto_id BETWEEN 487100 AND 490999)
            OR (konto_id BETWEEN 498000 AND 499999)
        ) THEN betrag ELSE 0 END) as direkte,
        SUM(CASE WHEN debit_or_credit='S' AND konto_id BETWEEN 400000 AND 414999
            THEN betrag ELSE 0 END) as indirekte,
        SUM(CASE WHEN debit_or_credit='H' AND konto_id BETWEEN 900000 AND 999999
            THEN -betrag ELSE 0 END) as neutral
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months')
      AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
    GROUP BY EXTRACT(YEAR FROM zeit_id), EXTRACT(MONTH FROM zeit_id)
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
            "id": 51,
            "name": "BWA Vergleich Vorjahr",
            "description": "BWA-Vergleich: Aktuell vs. Vorjahresmonat (nutzt fact_bwa)",
            "sql": """
-- BWA Vergleich: Aktuell vs. Vorjahresmonat (nutzt fact_bwa)
WITH aktuell AS (
    SELECT 
        SUM(CASE WHEN debit_or_credit='H' AND ((konto_id BETWEEN 800000 AND 889999) OR (konto_id BETWEEN 893200 AND 893299))
            THEN betrag ELSE 0 END) as umsatz,
        SUM(CASE WHEN debit_or_credit='S' AND konto_id BETWEEN 700000 AND 799999 AND konto_id != 743002
            THEN betrag ELSE 0 END) as einsatz,
        SUM(CASE WHEN debit_or_credit='S' AND (
            (konto_id BETWEEN 415100 AND 415199)
            OR (konto_id BETWEEN 435500 AND 435599)
            OR (konto_id BETWEEN 455000 AND 456999 AND kst_id != 0)
            OR (konto_id BETWEEN 487000 AND 487099 AND kst_id != 0)
            OR (konto_id BETWEEN 491000 AND 497899)
            OR (konto_id BETWEEN 891000 AND 891099)
        ) THEN betrag ELSE 0 END) as variable,
        SUM(CASE WHEN debit_or_credit='S' AND (
            (konto_id BETWEEN 415000 AND 415099)
            OR (konto_id BETWEEN 420000 AND 429999)
            OR (konto_id BETWEEN 430000 AND 435499)
            OR (konto_id BETWEEN 435600 AND 454999)
            OR (konto_id BETWEEN 457000 AND 486999)
            OR (konto_id BETWEEN 487100 AND 490999)
            OR (konto_id BETWEEN 498000 AND 499999)
        ) THEN betrag ELSE 0 END) as direkte,
        SUM(CASE WHEN debit_or_credit='S' AND konto_id BETWEEN 400000 AND 414999
            THEN betrag ELSE 0 END) as indirekte,
        SUM(CASE WHEN debit_or_credit='H' AND konto_id BETWEEN 900000 AND 999999
            THEN -betrag ELSE 0 END) as neutral
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE)
      AND zeit_id < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
),
vorjahr AS (
    SELECT 
        SUM(CASE WHEN debit_or_credit='H' AND ((konto_id BETWEEN 800000 AND 889999) OR (konto_id BETWEEN 893200 AND 893299))
            THEN betrag ELSE 0 END) as umsatz,
        SUM(CASE WHEN debit_or_credit='S' AND konto_id BETWEEN 700000 AND 799999 AND konto_id != 743002
            THEN betrag ELSE 0 END) as einsatz,
        SUM(CASE WHEN debit_or_credit='S' AND (
            (konto_id BETWEEN 415100 AND 415199)
            OR (konto_id BETWEEN 435500 AND 435599)
            OR (konto_id BETWEEN 455000 AND 456999 AND kst_id != 0)
            OR (konto_id BETWEEN 487000 AND 487099 AND kst_id != 0)
            OR (konto_id BETWEEN 491000 AND 497899)
            OR (konto_id BETWEEN 891000 AND 891099)
        ) THEN betrag ELSE 0 END) as variable,
        SUM(CASE WHEN debit_or_credit='S' AND (
            (konto_id BETWEEN 415000 AND 415099)
            OR (konto_id BETWEEN 420000 AND 429999)
            OR (konto_id BETWEEN 430000 AND 435499)
            OR (konto_id BETWEEN 435600 AND 454999)
            OR (konto_id BETWEEN 457000 AND 486999)
            OR (konto_id BETWEEN 487100 AND 490999)
            OR (konto_id BETWEEN 498000 AND 499999)
        ) THEN betrag ELSE 0 END) as direkte,
        SUM(CASE WHEN debit_or_credit='S' AND konto_id BETWEEN 400000 AND 414999
            THEN betrag ELSE 0 END) as indirekte,
        SUM(CASE WHEN debit_or_credit='H' AND konto_id BETWEEN 900000 AND 999999
            THEN -betrag ELSE 0 END) as neutral
    FROM fact_bwa
    WHERE zeit_id >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 year')
      AND zeit_id < DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 year') + INTERVAL '1 month'
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
    
    print("1. TEK-Queries aktualisieren...\n")
    for query in tek_queries:
        print(f"{query['name']}:")
        update_query(session, query['id'], query['name'], query['description'], query['sql'], query['type'])
        print()
    
    print("\n2. BWA-Queries aktualisieren...\n")
    for query in bwa_queries:
        print(f"{query['name']}:")
        update_query(session, query['id'], query['name'], query['description'], query['sql'], query['type'])
        print()
    
    print("="*60)
    print("✅ Fertig! Alle Queries nutzen jetzt Materialized Views")
    print("="*60)
    print("\nHinweis: Views werden täglich um 19:20 automatisch aktualisiert")
    print("(via Celery-Task: refresh_finanzreporting_cube)")

if __name__ == "__main__":
    main()
