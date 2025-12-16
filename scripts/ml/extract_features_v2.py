#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
GREINER DRIVE - Feature Extraktion V2 (TAG 119)
=============================================================================
Extrahiert erweiterte Features aus Locosoft PostgreSQL für ML-Training.

Neue Features:
- order_classification_flag (Auftragstyp)
- urgency (Dringlichkeit)
- productivity_factor (Mechaniker-Produktivität)
- years_experience (Erfahrung in Jahren)
- labour_type (Arbeitstyp)
- charge_type (Lohnart)
- anzahl_positionen (Arbeitspositionen pro Auftrag)
- anzahl_teile (Teile pro Auftrag)
- power_kw (Motorleistung)
- cubic_capacity (Hubraum)
- team_auslastung (Abwesenheitsquote Team)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import psycopg2
import os
import sys

# Locosoft DB-Verbindung
LOCO_CONFIG = {
    'host': '10.80.80.8',
    'port': 5432,
    'database': 'loco_auswertung_db',
    'user': 'loco_auswertung_benutzer',
    'password': 'loco'
}

OUTPUT_PATH = "/opt/greiner-portal/data/ml/auftraege_features_v2.csv"


def get_locosoft_connection():
    """Erstellt Verbindung zur Locosoft PostgreSQL DB"""
    return psycopg2.connect(**LOCO_CONFIG)


def extract_orders_with_times(conn, start_date='2023-01-01', end_date=None):
    """
    Extrahiert Aufträge mit IST-Zeiten aus labours Tabelle.

    Berechnet IST-Dauer basierend auf time_units (AW = Arbeitswerte).
    1 AW = ca. 6 Minuten → IST-Dauer = time_units * 6
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    query = """
    WITH order_times AS (
        -- Aggregiere Arbeitszeiten pro Auftrag
        SELECT
            l.order_number,
            o.subsidiary as betrieb,
            o.order_date,
            o.order_classification_flag,
            o.urgency,
            o.vehicle_number,
            o.order_customer,
            SUM(l.time_units) as total_aw,
            COUNT(DISTINCT l.order_position) as anzahl_positionen,
            COUNT(CASE WHEN l.labour_type IS NOT NULL THEN 1 END) as anzahl_arbeiten,
            MAX(l.charge_type) as charge_type,
            MAX(l.labour_type) as labour_type,
            MIN(l.mechanic_no) as mechaniker_nr
        FROM labours l
        JOIN orders o ON l.order_number = o.number
        WHERE o.order_date >= %s
          AND o.order_date <= %s
          AND l.time_units > 0
          AND l.is_invoiced = true
        GROUP BY l.order_number, o.subsidiary, o.order_date,
                 o.order_classification_flag, o.urgency, o.vehicle_number, o.order_customer
    ),
    order_parts AS (
        -- Zähle Teile pro Auftrag
        SELECT
            order_number,
            COUNT(*) as anzahl_teile,
            SUM(amount) as teile_menge
        FROM parts
        WHERE is_invoiced = true
        GROUP BY order_number
    )
    SELECT
        ot.*,
        COALESCE(op.anzahl_teile, 0) as anzahl_teile,
        COALESCE(op.teile_menge, 0) as teile_menge
    FROM order_times ot
    LEFT JOIN order_parts op ON ot.order_number = op.order_number
    WHERE ot.total_aw > 0
    ORDER BY ot.order_date DESC
    """

    print(f"  Lade Aufträge von {start_date} bis {end_date}...")
    df = pd.read_sql(query, conn, params=(start_date, end_date))
    print(f"  {len(df):,} Aufträge geladen")

    # IST-Dauer berechnen (AW × 6 Minuten)
    df['ist_dauer_min'] = df['total_aw'] * 6

    return df


def extract_vehicle_features(conn, vehicle_numbers):
    """Extrahiert Fahrzeug-Features"""
    if len(vehicle_numbers) == 0:
        return pd.DataFrame()

    query = """
    SELECT
        v.internal_number as vehicle_number,
        v.make_number,
        m.description as marke,
        v.model_code,
        v.first_registration_date,
        v.power_kw,
        v.cubic_capacity,
        v.mileage_km as km_stand,
        CASE
            WHEN v.first_registration_date IS NOT NULL
            THEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, v.first_registration_date))
            ELSE NULL
        END as fahrzeug_alter_jahre
    FROM vehicles v
    LEFT JOIN makes m ON v.make_number = m.make_number
    WHERE v.internal_number = ANY(%s)
    """

    print(f"  Lade Fahrzeug-Features für {len(vehicle_numbers):,} Fahrzeuge...")
    df = pd.read_sql(query, conn, params=(list(vehicle_numbers),))
    print(f"  {len(df):,} Fahrzeuge gefunden")

    return df


def extract_employee_features(conn, employee_numbers):
    """Extrahiert Mitarbeiter-Features (Produktivität, Erfahrung)"""
    if len(employee_numbers) == 0:
        return pd.DataFrame()

    query = """
    SELECT
        e.mechanic_number as mechaniker_nr,
        e.employee_number,
        e.name as mechaniker_name,
        e.productivity_factor,
        e.employment_date,
        e.is_master_craftsman,
        e.subsidiary,
        CASE
            WHEN e.employment_date IS NOT NULL
            THEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.employment_date))
            ELSE NULL
        END as years_experience
    FROM employees_history e
    WHERE e.is_latest_record = true
      AND e.mechanic_number = ANY(%s)
    """

    print(f"  Lade Mitarbeiter-Features für {len(employee_numbers):,} Mechaniker...")
    df = pd.read_sql(query, conn, params=(list(employee_numbers),))
    print(f"  {len(df):,} Mechaniker gefunden")

    return df


def extract_team_workload(conn, date, subsidiary=None):
    """
    Berechnet Team-Auslastung basierend auf Abwesenheiten.
    Gibt Prozentsatz der anwesenden Mitarbeiter zurück.
    """
    query = """
    WITH total_employees AS (
        SELECT COUNT(DISTINCT employee_number) as total
        FROM employees_history
        WHERE is_latest_record = true
          AND mechanic_number IS NOT NULL
          AND (subsidiary = %s OR %s IS NULL)
    ),
    absent_employees AS (
        SELECT COUNT(DISTINCT employee_number) as absent
        FROM absence_calendar
        WHERE date = %s
          AND day_contingent >= 0.5
    )
    SELECT
        t.total,
        COALESCE(a.absent, 0) as absent,
        CASE
            WHEN t.total > 0
            THEN ROUND((1.0 - COALESCE(a.absent, 0)::decimal / t.total) * 100, 1)
            ELSE 100
        END as anwesenheitsquote
    FROM total_employees t
    CROSS JOIN absent_employees a
    """

    df = pd.read_sql(query, conn, params=(subsidiary, subsidiary, date))
    if len(df) > 0:
        return df.iloc[0]['anwesenheitsquote']
    return 100.0


def extract_all_features(start_date='2023-01-01', end_date=None):
    """
    Hauptfunktion: Extrahiert alle Features und kombiniert sie.
    """
    print("=" * 70)
    print("GREINER DRIVE - Feature Extraktion V2 (TAG 119)")
    print("=" * 70)

    conn = get_locosoft_connection()

    try:
        # 1. Basis-Aufträge mit Zeiten
        print("\n[1/5] Lade Basis-Aufträge...")
        df_orders = extract_orders_with_times(conn, start_date, end_date)

        if len(df_orders) == 0:
            print("FEHLER: Keine Aufträge gefunden!")
            return None

        # 2. Fahrzeug-Features
        print("\n[2/5] Lade Fahrzeug-Features...")
        vehicle_numbers = [int(x) for x in df_orders['vehicle_number'].dropna().unique()]
        df_vehicles = extract_vehicle_features(conn, vehicle_numbers)

        # 3. Mitarbeiter-Features
        print("\n[3/5] Lade Mitarbeiter-Features...")
        employee_numbers = [int(x) for x in df_orders['mechaniker_nr'].dropna().unique()]
        df_employees = extract_employee_features(conn, employee_numbers)

        # 4. Kombinieren
        print("\n[4/5] Kombiniere Features...")

        # Fahrzeug-Features joinen
        df = df_orders.merge(
            df_vehicles[['vehicle_number', 'marke', 'power_kw', 'cubic_capacity',
                        'km_stand', 'fahrzeug_alter_jahre']],
            on='vehicle_number',
            how='left'
        )

        # Mitarbeiter-Features joinen
        df = df.merge(
            df_employees[['mechaniker_nr', 'productivity_factor', 'years_experience',
                         'is_master_craftsman']],
            on='mechaniker_nr',
            how='left'
        )

        # 5. Feature Engineering
        print("\n[5/5] Feature Engineering...")

        # Zeitfeatures extrahieren
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['wochentag'] = df['order_date'].dt.dayofweek  # 0=Montag
        df['monat'] = df['order_date'].dt.month
        df['start_stunde'] = df['order_date'].dt.hour
        df['kalenderwoche'] = df['order_date'].dt.isocalendar().week

        # Vorgabe-AW berechnen (falls vorhanden)
        df['vorgabe_aw'] = df['total_aw']  # Kann später mit Soll-Zeiten verglichen werden

        # Fehlende Werte behandeln
        df['marke'] = df['marke'].fillna('Unbekannt')
        df['power_kw'] = df['power_kw'].fillna(df['power_kw'].median())
        df['cubic_capacity'] = df['cubic_capacity'].fillna(df['cubic_capacity'].median())
        df['km_stand'] = df['km_stand'].fillna(df['km_stand'].median())
        df['fahrzeug_alter_jahre'] = df['fahrzeug_alter_jahre'].fillna(
            df['fahrzeug_alter_jahre'].median()
        )
        df['productivity_factor'] = df['productivity_factor'].fillna(1.0)
        df['years_experience'] = df['years_experience'].fillna(
            df['years_experience'].median()
        )
        df['urgency'] = df['urgency'].fillna(0)
        df['order_classification_flag'] = df['order_classification_flag'].fillna('X')
        df['charge_type'] = df['charge_type'].fillna(0)
        df['labour_type'] = df['labour_type'].fillna('N')
        df['is_master_craftsman'] = df['is_master_craftsman'].fillna(False).astype(int)

        # Spalten umbenennen für Konsistenz
        df = df.rename(columns={
            'order_classification_flag': 'auftragstyp',
            'is_master_craftsman': 'meister'
        })

        # Nur relevante Spalten behalten
        feature_columns = [
            'order_number', 'order_date', 'betrieb',
            # Target
            'ist_dauer_min', 'total_aw', 'vorgabe_aw',
            # Zeitfeatures
            'wochentag', 'monat', 'start_stunde', 'kalenderwoche',
            # Auftragsfeatures
            'auftragstyp', 'urgency', 'anzahl_positionen', 'anzahl_teile',
            'charge_type', 'labour_type',
            # Fahrzeugfeatures
            'marke', 'power_kw', 'cubic_capacity', 'km_stand', 'fahrzeug_alter_jahre',
            # Mechanikerfeatures
            'mechaniker_nr', 'productivity_factor', 'years_experience', 'meister'
        ]

        df_final = df[[c for c in feature_columns if c in df.columns]].copy()

        # Statistiken
        print("\n" + "=" * 70)
        print("FEATURE-STATISTIKEN")
        print("=" * 70)
        print(f"\nDatensätze: {len(df_final):,}")
        print(f"Features: {len(df_final.columns)}")
        print(f"\nIST-Dauer (Minuten):")
        print(f"  Min:    {df_final['ist_dauer_min'].min():.0f}")
        print(f"  Max:    {df_final['ist_dauer_min'].max():.0f}")
        print(f"  Median: {df_final['ist_dauer_min'].median():.0f}")
        print(f"  Mean:   {df_final['ist_dauer_min'].mean():.0f}")

        print(f"\nMarken-Verteilung:")
        for marke, count in df_final['marke'].value_counts().head(5).items():
            print(f"  {marke}: {count:,} ({count/len(df_final)*100:.1f}%)")

        print(f"\nAuftragstyp-Verteilung:")
        for typ, count in df_final['auftragstyp'].value_counts().head(5).items():
            print(f"  {typ}: {count:,} ({count/len(df_final)*100:.1f}%)")

        # Speichern
        print(f"\nSpeichere nach: {OUTPUT_PATH}")
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        df_final.to_csv(OUTPUT_PATH, index=False)
        print(f"Datei gespeichert ({os.path.getsize(OUTPUT_PATH) / 1024 / 1024:.1f} MB)")

        return df_final

    finally:
        conn.close()


if __name__ == "__main__":
    # Kommandozeilenargumente
    start_date = sys.argv[1] if len(sys.argv) > 1 else '2023-01-01'
    end_date = sys.argv[2] if len(sys.argv) > 2 else None

    df = extract_all_features(start_date, end_date)

    if df is not None:
        print("\n" + "=" * 70)
        print("EXTRAKTION ABGESCHLOSSEN!")
        print("=" * 70)
        print(f"\nNächster Schritt: python train_auftragsdauer_model_v2.py")
