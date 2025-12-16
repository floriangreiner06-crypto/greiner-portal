#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
GREINER DRIVE - Labour Correction Factors Extraction (TAG 119)
=============================================================================

Extrahiert Korrekturfaktoren pro Arbeitsposition und Lohnart aus Locosoft.
Berücksichtigt Unterschiede zwischen:
- W (Werkstatt) - freie Kalkulation
- G (Garantie) - Herstellervorgaben (oft zu knapp!)
- I (Intern)
- V (Versicherung)

Output: JSON-Datei mit Korrekturfaktoren für DRIVE ML
"""

import psycopg2
import json
import os
from datetime import datetime
from collections import defaultdict
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """JSON Encoder für Decimal-Typen"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# =============================================================================
# KONFIGURATION
# =============================================================================
OUTPUT_DIR = "/opt/greiner-portal/data/ml"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "labour_corrections.json")

DB_CONFIG = {
    'host': '10.80.80.8',
    'port': 5432,
    'database': 'loco_auswertung_db',
    'user': 'loco_auswertung_benutzer',
    'password': 'loco'
}

# Minimum Anzahl Datenpunkte für validen Korrekturfaktor
MIN_SAMPLES = 5

# Ratio-Grenzen für Plausibilität
MIN_RATIO = 0.2
MAX_RATIO = 5.0


def extract_correction_factors():
    """Extrahiert Korrekturfaktoren aus Locosoft-Daten"""

    query = """
    WITH
    -- Nur Aufträge mit genau einer Arbeitsposition (sauberer Vergleich)
    single_labour AS (
        SELECT order_number
        FROM labours
        WHERE time_units > 0 AND order_number > 30000
        GROUP BY order_number
        HAVING COUNT(*) = 1
    ),
    -- SOLL-Zeiten aus labours
    soll AS (
        SELECT
            l.order_number,
            TRIM(l.labour_operation_id) as labour_op,
            l.labour_type,
            l.time_units as soll_aw
        FROM labours l
        JOIN single_labour s ON l.order_number = s.order_number
        WHERE l.time_units > 0
    ),
    -- IST-Zeiten aus times (dedupliziert!)
    ist AS (
        SELECT DISTINCT ON (order_number, employee_number, start_time)
            order_number, duration_minutes
        FROM times
        WHERE duration_minutes > 0 AND start_time >= '2023-01-01'
    ),
    ist_agg AS (
        SELECT order_number, SUM(duration_minutes) as ist_min
        FROM ist
        GROUP BY order_number
    ),
    -- Kombiniert mit Ratio-Berechnung
    combined AS (
        SELECT
            s.labour_op,
            s.labour_type,
            s.soll_aw,
            i.ist_min,
            i.ist_min / NULLIF(s.soll_aw * 6, 0) as ratio
        FROM soll s
        JOIN ist_agg i ON s.order_number = i.order_number
        WHERE s.soll_aw > 0 AND i.ist_min > 0
    )
    SELECT
        labour_op,
        labour_type,
        COUNT(*) as n,
        ROUND(AVG(soll_aw)::numeric, 1) as avg_soll_aw,
        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ratio)::numeric, 3) as median_ratio,
        ROUND(AVG(ratio)::numeric, 3) as avg_ratio,
        ROUND(STDDEV(ratio)::numeric, 3) as std_ratio
    FROM combined
    WHERE ratio BETWEEN %s AND %s
      AND labour_op IS NOT NULL
      AND labour_op != ''
    GROUP BY labour_op, labour_type
    HAVING COUNT(*) >= %s
    ORDER BY n DESC
    """

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(query, (MIN_RATIO, MAX_RATIO, MIN_SAMPLES))
    rows = cur.fetchall()

    # Strukturiere Daten
    corrections = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'min_samples': MIN_SAMPLES,
            'ratio_range': [MIN_RATIO, MAX_RATIO],
            'total_entries': len(rows)
        },
        'by_operation_and_type': {},  # labour_op -> labour_type -> factor
        'by_operation': {},           # labour_op -> factor (aggregiert)
        'by_type': {},                # labour_type -> factor (global)
        'statistics': {
            'by_type': {}
        }
    }

    # Aggregiere nach labour_type für Fallback
    type_ratios = defaultdict(list)
    op_ratios = defaultdict(list)

    for row in rows:
        labour_op, labour_type, n, avg_soll_aw, median_ratio, avg_ratio, std_ratio = row

        # Speichere pro Operation + Type
        if labour_op not in corrections['by_operation_and_type']:
            corrections['by_operation_and_type'][labour_op] = {}

        corrections['by_operation_and_type'][labour_op][labour_type] = {
            'factor': float(median_ratio),
            'avg_factor': float(avg_ratio),
            'std': float(std_ratio) if std_ratio else 0,
            'n': n,
            'avg_soll_aw': float(avg_soll_aw)
        }

        # Für Aggregation
        type_ratios[labour_type].append((median_ratio, n))
        op_ratios[labour_op].append((median_ratio, n))

    # Berechne gewichteten Durchschnitt pro labour_type
    for lt, ratios in type_ratios.items():
        total_n = sum(r[1] for r in ratios)
        weighted_avg = sum(r[0] * r[1] for r in ratios) / total_n
        corrections['by_type'][lt] = round(weighted_avg, 3)
        corrections['statistics']['by_type'][lt] = {
            'factor': round(weighted_avg, 3),
            'n_operations': len(ratios),
            'n_samples': total_n
        }

    # Berechne gewichteten Durchschnitt pro Operation (über alle Types)
    for op, ratios in op_ratios.items():
        total_n = sum(r[1] for r in ratios)
        weighted_avg = sum(r[0] * r[1] for r in ratios) / total_n
        corrections['by_operation'][op] = round(weighted_avg, 3)

    conn.close()
    return corrections


def get_correction_factor(corrections: dict, labour_op: str, labour_type: str) -> float:
    """
    Holt den Korrekturfaktor für eine Arbeitsposition.

    Fallback-Hierarchie:
    1. Exakter Match: labour_op + labour_type
    2. Operation ohne Type: labour_op (aggregiert)
    3. Type ohne Operation: labour_type (global)
    4. Default: 1.0 (keine Korrektur)
    """
    # 1. Exakter Match
    if labour_op in corrections.get('by_operation_and_type', {}):
        if labour_type in corrections['by_operation_and_type'][labour_op]:
            return corrections['by_operation_and_type'][labour_op][labour_type]['factor']

    # 2. Operation aggregiert
    if labour_op in corrections.get('by_operation', {}):
        return corrections['by_operation'][labour_op]

    # 3. Type global
    if labour_type in corrections.get('by_type', {}):
        return corrections['by_type'][labour_type]

    # 4. Default
    return 1.0


def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("DRIVE Labour Corrections Extraction")
    print("=" * 60)
    print()

    # Extrahiere Faktoren
    print("[1/2] Extrahiere Korrekturfaktoren aus Locosoft...")
    corrections = extract_correction_factors()

    print(f"  → {corrections['metadata']['total_entries']} Operation/Type-Kombinationen")
    print(f"  → {len(corrections['by_operation'])} eindeutige Operationen")
    print(f"  → {len(corrections['by_type'])} Lohnarten")
    print()

    # Zeige Statistiken pro Lohnart
    print("Korrekturfaktoren nach Lohnart:")
    print("-" * 40)
    for lt, stats in sorted(corrections['statistics']['by_type'].items(),
                            key=lambda x: x[1]['n_samples'], reverse=True):
        print(f"  {lt:3} | Faktor: {stats['factor']:.2f}x | "
              f"{stats['n_operations']:3} Ops | {stats['n_samples']:5} Samples")
    print()

    # Speichere
    print(f"[2/2] Speichere nach {OUTPUT_FILE}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(corrections, f, indent=2, ensure_ascii=False, cls=DecimalEncoder)

    print()
    print("=" * 60)
    print("FERTIG!")
    print("=" * 60)

    # Beispiel-Lookups
    print()
    print("Beispiel-Lookups:")
    print("-" * 40)
    examples = [
        ('INSP', 'W'),
        ('INSP', 'G'),
        ('30D079R0', 'G'),
        ('ZI', 'W'),
        ('UNKNOWN', 'G'),
        ('UNKNOWN', 'X'),
    ]
    for op, lt in examples:
        factor = get_correction_factor(corrections, op, lt)
        print(f"  {op:15} + {lt} → {factor:.2f}x")


if __name__ == '__main__':
    main()
