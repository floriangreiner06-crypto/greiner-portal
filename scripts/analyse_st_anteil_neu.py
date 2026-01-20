#!/usr/bin/env python3
"""
Neue Analyse: St-Anteil-Berechnung komplett neu
Vergleicht verschiedene Berechnungsvarianten mit Locosoft-Werten
"""

import sys
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor


def test_variante_1_roh_stempelungen(mech_nr: int, von: date, bis: date):
    """Variante 1: Summe aller Stempelungen (roh, dedupliziert pro Auftrag/Zeit)"""
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT 
                SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as minuten
            FROM (
                SELECT DISTINCT ON (employee_number, order_number, start_time, end_time)
                    employee_number, start_time, end_time
                FROM times
                WHERE type = 2
                    AND end_time IS NOT NULL
                    AND order_number > 31
                    AND employee_number = %s
                    AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                ORDER BY employee_number, order_number, start_time, end_time
            ) t
        """
        cursor.execute(query, [mech_nr, von, bis])
        row = cursor.fetchone()
        return float(row['minuten'] or 0)


def test_variante_2_mit_positionen(mech_nr: int, von: date, bis: date):
    """Variante 2: Summe aller Stempelungen MIT Positionen (dedupliziert pro Position/Zeit)"""
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT 
                SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as minuten
            FROM (
                SELECT DISTINCT ON (employee_number, order_number, order_position, order_position_line, start_time, end_time)
                    employee_number, start_time, end_time
                FROM times
                WHERE type = 2
                    AND end_time IS NOT NULL
                    AND order_number > 31
                    AND order_position IS NOT NULL
                    AND order_position_line IS NOT NULL
                    AND employee_number = %s
                    AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                ORDER BY employee_number, order_number, order_position, order_position_line, start_time, end_time
            ) t
        """
        cursor.execute(query, [mech_nr, von, bis])
        row = cursor.fetchone()
        return float(row['minuten'] or 0)


def test_variante_3_mit_aw_filter(mech_nr: int, von: date, bis: date):
    """Variante 3: Summe Stempelungen auf Positionen MIT AW"""
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT 
                SUM(EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60) as minuten
            FROM (
                SELECT DISTINCT ON (t.employee_number, t.order_number, t.start_time, t.end_time)
                    t.employee_number, t.order_number, t.start_time, t.end_time
                FROM times t
                WHERE t.type = 2
                    AND t.end_time IS NOT NULL
                    AND t.order_number > 31
                    AND t.employee_number = %s
                    AND t.start_time >= %s AND t.start_time < %s + INTERVAL '1 day'
                    AND EXISTS (
                        SELECT 1 FROM labours l
                        WHERE l.order_number = t.order_number
                            AND l.time_units > 0
                    )
                ORDER BY t.employee_number, t.order_number, t.start_time, t.end_time
            ) t
        """
        cursor.execute(query, [mech_nr, von, bis])
        row = cursor.fetchone()
        return float(row['minuten'] or 0)


def test_variante_4_ohne_pause(mech_nr: int, von: date, bis: date):
    """Variante 4: Wie Variante 1, aber Mittagspause (12:00-12:44) abziehen"""
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT 
                SUM(
                    EXTRACT(EPOCH FROM (end_time - start_time)) / 60
                    - CASE
                        WHEN start_time::time < TIME '12:00:00' 
                             AND end_time::time > TIME '12:44:00' THEN 44.0
                        WHEN start_time::time >= TIME '12:00:00' 
                             AND start_time::time < TIME '12:44:00' 
                             AND end_time::time > TIME '12:44:00' THEN
                            EXTRACT(EPOCH FROM (TIME '12:44:00' - start_time::time)) / 60
                        WHEN start_time::time < TIME '12:00:00' 
                             AND end_time::time > TIME '12:00:00' 
                             AND end_time::time <= TIME '12:44:00' THEN
                            EXTRACT(EPOCH FROM (end_time::time - TIME '12:00:00')) / 60
                        WHEN start_time::time >= TIME '12:00:00' 
                             AND end_time::time <= TIME '12:44:00' THEN
                            EXTRACT(EPOCH FROM (end_time - start_time)) / 60
                        ELSE 0.0
                    END
                ) as minuten
            FROM (
                SELECT DISTINCT ON (employee_number, order_number, start_time, end_time)
                    employee_number, start_time, end_time
                FROM times
                WHERE type = 2
                    AND end_time IS NOT NULL
                    AND order_number > 31
                    AND employee_number = %s
                    AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                ORDER BY employee_number, order_number, start_time, end_time
            ) t
        """
        cursor.execute(query, [mech_nr, von, bis])
        row = cursor.fetchone()
        return float(row['minuten'] or 0)


def test_variante_5_summe_pro_position(mech_nr: int, von: date, bis: date):
    """Variante 5: Summe pro Position (jede Position einzeln gezählt)"""
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT 
                SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as minuten
            FROM times
            WHERE type = 2
                AND end_time IS NOT NULL
                AND order_number > 31
                AND order_position IS NOT NULL
                AND order_position_line IS NOT NULL
                AND employee_number = %s
                AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
        """
        cursor.execute(query, [mech_nr, von, bis])
        row = cursor.fetchone()
        return float(row['minuten'] or 0)


def test_variante_6_zeit_spanne(mech_nr: int, von: date, bis: date):
    """Variante 6: Zeit-Spanne pro Tag (erste bis letzte Stempelung)"""
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            WITH tages_spannen AS (
                SELECT
                    employee_number,
                    DATE(start_time) as datum,
                    MIN(start_time) as erste,
                    MAX(end_time) as letzte
                FROM times
                WHERE type = 2
                    AND end_time IS NOT NULL
                    AND order_number > 31
                    AND employee_number = %s
                    AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                GROUP BY employee_number, DATE(start_time)
            )
            SELECT 
                SUM(EXTRACT(EPOCH FROM (letzte - erste)) / 60) as minuten
            FROM tages_spannen
        """
        cursor.execute(query, [mech_nr, von, bis])
        row = cursor.fetchone()
        return float(row['minuten'] or 0)


def test_variante_7_zeit_spanne_minus_luecken(mech_nr: int, von: date, bis: date):
    """Variante 7: Zeit-Spanne MINUS Lücken zwischen Stempelungen"""
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            WITH
            stempelungen_dedupliziert AS (
                SELECT DISTINCT ON (employee_number, DATE(start_time), start_time, end_time)
                    employee_number,
                    DATE(start_time) as datum,
                    start_time,
                    end_time
                FROM times
                WHERE type = 2
                    AND end_time IS NOT NULL
                    AND order_number > 31
                    AND employee_number = %s
                    AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                ORDER BY employee_number, DATE(start_time), start_time, end_time
            ),
            tages_spannen AS (
                SELECT
                    employee_number,
                    datum,
                    MIN(start_time) as erste,
                    MAX(end_time) as letzte,
                    EXTRACT(EPOCH FROM (MAX(end_time) - MIN(start_time))) / 60 as spanne_minuten
                FROM stempelungen_dedupliziert
                GROUP BY employee_number, datum
            ),
            luecken_pro_tag AS (
                SELECT
                    s1.employee_number,
                    s1.datum,
                    SUM(EXTRACT(EPOCH FROM (s2.start_time - s1.end_time)) / 60) as luecken_minuten
                FROM stempelungen_dedupliziert s1
                JOIN stempelungen_dedupliziert s2 
                    ON s1.employee_number = s2.employee_number 
                    AND s1.datum = s2.datum
                    AND s2.start_time > s1.end_time
                    AND NOT EXISTS (
                        SELECT 1 FROM stempelungen_dedupliziert s3
                        WHERE s3.employee_number = s1.employee_number
                          AND s3.datum = s1.datum
                          AND s3.start_time > s1.end_time
                          AND s3.start_time < s2.start_time
                    )
                GROUP BY s1.employee_number, s1.datum
            )
            SELECT 
                SUM(ts.spanne_minuten - COALESCE(l.luecken_minuten, 0)) as minuten
            FROM tages_spannen ts
            LEFT JOIN luecken_pro_tag l 
                ON ts.employee_number = l.employee_number 
                AND ts.datum = l.datum
        """
        cursor.execute(query, [mech_nr, von, bis])
        row = cursor.fetchone()
        return float(row['minuten'] or 0)


def test_variante_8_roh_ohne_deduplizierung(mech_nr: int, von: date, bis: date):
    """Variante 8: Summe ALLER Stempelungen (KEINE Deduplizierung)"""
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT 
                SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as minuten
            FROM times
            WHERE type = 2
                AND end_time IS NOT NULL
                AND order_number > 31
                AND employee_number = %s
                AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
        """
        cursor.execute(query, [mech_nr, von, bis])
        row = cursor.fetchone()
        return float(row['minuten'] or 0)


def test_variante_9_mit_positionen_ohne_aw(mech_nr: int, von: date, bis: date):
    """Variante 9: Summe Stempelungen auf Positionen (auch OHNE AW)"""
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT 
                SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as minuten
            FROM (
                SELECT DISTINCT ON (employee_number, order_number, order_position, order_position_line, start_time, end_time)
                    employee_number, start_time, end_time
                FROM times
                WHERE type = 2
                    AND end_time IS NOT NULL
                    AND order_number > 31
                    AND order_position IS NOT NULL
                    AND order_position_line IS NOT NULL
                    AND employee_number = %s
                    AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
                ORDER BY employee_number, order_number, order_position, order_position_line, start_time, end_time
            ) t
        """
        cursor.execute(query, [mech_nr, von, bis])
        row = cursor.fetchone()
        return float(row['minuten'] or 0)


def main():
    mech_nr = 5007
    von = date(2026, 1, 1)
    bis = date(2026, 1, 15)
    locosoft_wert = 4971.0  # 82:51 aus Screenshot
    
    print(f"\n{'='*80}")
    print(f"NEUE ANALYSE: St-Anteil für Mechaniker {mech_nr}")
    print(f"Zeitraum: {von} bis {bis}")
    print(f"Locosoft-Wert: {locosoft_wert:.1f} Min ({locosoft_wert/60:.2f} h)")
    print(f"{'='*80}\n")
    
    varianten = [
        ("Variante 1: Roh-Stempelungen (dedupliziert pro Auftrag/Zeit)", test_variante_1_roh_stempelungen),
        ("Variante 2: Mit Positionen (dedupliziert pro Position/Zeit)", test_variante_2_mit_positionen),
        ("Variante 3: Nur Aufträge MIT AW", test_variante_3_mit_aw_filter),
        ("Variante 4: Roh-Stempelungen OHNE Pause", test_variante_4_ohne_pause),
        ("Variante 5: Summe pro Position (keine Deduplizierung)", test_variante_5_summe_pro_position),
        ("Variante 6: Zeit-Spanne pro Tag", test_variante_6_zeit_spanne),
        ("Variante 7: Zeit-Spanne MINUS Lücken", test_variante_7_zeit_spanne_minus_luecken),
        ("Variante 8: ALLE Stempelungen (KEINE Deduplizierung)", test_variante_8_roh_ohne_deduplizierung),
        ("Variante 9: Mit Positionen (auch OHNE AW)", test_variante_9_mit_positionen_ohne_aw),
    ]
    
    results = []
    for name, func in varianten:
        try:
            wert = func(mech_nr, von, bis)
            diff = wert - locosoft_wert
            diff_pct = (diff / locosoft_wert) * 100 if locosoft_wert > 0 else 0
            results.append((name, wert, diff, diff_pct))
        except Exception as e:
            print(f"❌ {name}: Fehler - {e}")
            results.append((name, None, None, None))
    
    # Sortiere nach geringster Abweichung
    results.sort(key=lambda x: abs(x[2]) if x[2] is not None else float('inf'))
    
    print("📊 Ergebnisse (sortiert nach geringster Abweichung):\n")
    for name, wert, diff, diff_pct in results:
        if wert is not None:
            status = "✅" if abs(diff_pct) < 5 else "⚠️" if abs(diff_pct) < 20 else "❌"
            print(f"{status} {name}")
            print(f"   Wert: {wert:.1f} Min ({wert/60:.2f} h)")
            print(f"   Diff: {diff:+.1f} Min ({diff_pct:+.1f}%)")
            print()
        else:
            print(f"❌ {name}: Fehler")
            print()
    
    # Zeige beste Variante
    if results and results[0][1] is not None:
        best_name, best_wert, best_diff, best_diff_pct = results[0]
        print(f"\n{'='*80}")
        print(f"🏆 BESTE VARIANTE: {best_name}")
        print(f"   Wert: {best_wert:.1f} Min ({best_wert/60:.2f} h)")
        print(f"   Diff zu Locosoft: {best_diff:+.1f} Min ({best_diff_pct:+.1f}%)")
        print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
