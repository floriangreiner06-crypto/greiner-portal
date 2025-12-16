#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
GREINER DRIVE - Feature Extraktion V4 (TAG 119)
=============================================================================
ECHTE STEMPELUHR-DATEN!

SOLL (Vorgabe):
- Herstellervorgabe: SUM(labours.time_units) * 6 Minuten

IST (Tatsächlich):
- ECHTE ARBEITSZEIT aus times-Tabelle (Stempeluhr!)
- SUM(times.duration_minutes) pro Auftrag

Das ist die GOLDENE Datenquelle für ML!
"""

import pandas as pd
import numpy as np
from datetime import datetime
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

OUTPUT_PATH = "/opt/greiner-portal/data/ml/auftraege_features_v4.csv"


def get_locosoft_connection():
    return psycopg2.connect(**LOCO_CONFIG)


def extract_orders_with_real_times(conn, start_date='2023-01-01', end_date=None):
    """
    Extrahiert Aufträge mit ECHTEN Stempeluhr-Zeiten!

    SOLL = Herstellervorgabe (AW × 6 min)
    IST = Echte Arbeitszeit aus times-Tabelle
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    query = """
    WITH order_labours AS (
        -- SOLL: Herstellervorgabe aus labours
        SELECT
            l.order_number,
            o.subsidiary as betrieb,
            o.order_date,
            o.order_classification_flag,
            o.urgency,
            o.vehicle_number,
            SUM(l.time_units) as soll_aw,
            COUNT(DISTINCT l.order_position) as anzahl_positionen,
            MAX(l.charge_type) as charge_type,
            MAX(l.labour_type) as labour_type,
            MIN(l.mechanic_no) as mechaniker_nr
        FROM labours l
        JOIN orders o ON l.order_number = o.number
        WHERE l.time_units > 0
          AND l.is_invoiced = true
          AND o.order_date >= %s
          AND o.order_date <= %s
        GROUP BY l.order_number, o.subsidiary, o.order_date,
                 o.order_classification_flag, o.urgency, o.vehicle_number
    ),
    order_times AS (
        -- IST: Echte Arbeitszeit aus Stempeluhr!
        SELECT
            order_number,
            COUNT(DISTINCT employee_number) as anzahl_mechaniker,
            COUNT(*) as anzahl_stempel,
            SUM(duration_minutes) as ist_dauer_min,
            MIN(start_time) as erste_buchung,
            MAX(end_time) as letzte_buchung
        FROM times
        WHERE order_number > 0
          AND duration_minutes > 0
          AND start_time >= %s
        GROUP BY order_number
    ),
    order_parts AS (
        SELECT
            order_number,
            COUNT(*) as anzahl_teile
        FROM parts
        WHERE is_invoiced = true
        GROUP BY order_number
    )
    SELECT
        ol.order_number,
        ol.betrieb,
        ol.order_date,
        ol.order_classification_flag as auftragstyp,
        ol.urgency,
        ol.vehicle_number,
        -- SOLL
        ol.soll_aw,
        ol.soll_aw * 6 as soll_dauer_min,
        -- IST (ECHTE STEMPELZEIT!)
        ot.ist_dauer_min,
        ot.anzahl_mechaniker,
        ot.anzahl_stempel,
        ot.erste_buchung,
        ot.letzte_buchung,
        -- Features
        ol.anzahl_positionen,
        ol.charge_type,
        ol.labour_type,
        ol.mechaniker_nr,
        COALESCE(op.anzahl_teile, 0) as anzahl_teile
    FROM order_labours ol
    INNER JOIN order_times ot ON ol.order_number = ot.order_number
    LEFT JOIN order_parts op ON ol.order_number = op.order_number
    WHERE ol.soll_aw > 0
      AND ot.ist_dauer_min > 0
      -- Filter: Realistische Werte
      AND ot.ist_dauer_min BETWEEN 5 AND 600  -- 5 min bis 10 Stunden
      AND ol.soll_aw * 6 BETWEEN 3 AND 500     -- Plausible Vorgabe
    ORDER BY ol.order_date DESC
    """

    print(f"  Lade Aufträge von {start_date} bis {end_date}...")
    df = pd.read_sql(query, conn, params=(start_date, end_date, start_date))
    print(f"  {len(df):,} Aufträge mit echten Stempelzeiten geladen!")

    return df


def extract_vehicle_features(conn, vehicle_numbers):
    """Extrahiert Fahrzeug-Features"""
    if len(vehicle_numbers) == 0:
        return pd.DataFrame()

    query = """
    SELECT
        v.internal_number as vehicle_number,
        m.description as marke,
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

    df = pd.read_sql(query, conn, params=(list(vehicle_numbers),))
    return df


def extract_employee_features(conn, employee_numbers):
    """Extrahiert Mitarbeiter-Features"""
    if len(employee_numbers) == 0:
        return pd.DataFrame()

    query = """
    SELECT
        e.mechanic_number as mechaniker_nr,
        e.name as mechaniker_name,
        e.productivity_factor,
        CASE
            WHEN e.employment_date IS NOT NULL
            THEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.employment_date))
            ELSE NULL
        END as years_experience,
        e.is_master_craftsman as meister
    FROM employees_history e
    WHERE e.is_latest_record = true
      AND e.mechanic_number = ANY(%s)
    """

    df = pd.read_sql(query, conn, params=(list(employee_numbers),))
    return df


def extract_all_features(start_date='2023-01-01', end_date=None):
    """Hauptfunktion: Echte Stempeluhr-Daten für ML"""

    print("=" * 70)
    print("GREINER DRIVE - Feature Extraktion V4")
    print("ECHTE STEMPELUHR-DATEN!")
    print("=" * 70)

    conn = get_locosoft_connection()

    try:
        # 1. Aufträge mit echten Zeiten
        print("\n[1/5] Lade Aufträge mit ECHTEN Stempelzeiten...")
        df_orders = extract_orders_with_real_times(conn, start_date, end_date)

        if len(df_orders) == 0:
            print("FEHLER: Keine Aufträge gefunden!")
            return None

        # 2. Fahrzeug-Features
        print("\n[2/5] Lade Fahrzeug-Features...")
        vehicle_numbers = [int(x) for x in df_orders['vehicle_number'].dropna().unique()]
        df_vehicles = extract_vehicle_features(conn, vehicle_numbers)
        print(f"  {len(df_vehicles):,} Fahrzeuge")

        # 3. Mitarbeiter-Features
        print("\n[3/5] Lade Mitarbeiter-Features...")
        employee_numbers = [int(x) for x in df_orders['mechaniker_nr'].dropna().unique()]
        df_employees = extract_employee_features(conn, employee_numbers)
        print(f"  {len(df_employees):,} Mechaniker")

        # 4. Kombinieren
        print("\n[4/5] Kombiniere Features...")

        df = df_orders.merge(
            df_vehicles[['vehicle_number', 'marke', 'power_kw', 'cubic_capacity',
                        'km_stand', 'fahrzeug_alter_jahre']],
            on='vehicle_number', how='left'
        )

        df = df.merge(
            df_employees[['mechaniker_nr', 'productivity_factor', 'years_experience', 'meister']],
            on='mechaniker_nr', how='left'
        )

        # 5. Feature Engineering
        print("\n[5/5] Feature Engineering...")

        df['order_date'] = pd.to_datetime(df['order_date'])
        df['erste_buchung'] = pd.to_datetime(df['erste_buchung'])

        # Zeitfeatures
        df['wochentag'] = df['erste_buchung'].dt.dayofweek
        df['monat'] = df['erste_buchung'].dt.month
        df['start_stunde'] = df['erste_buchung'].dt.hour
        df['kalenderwoche'] = df['erste_buchung'].dt.isocalendar().week

        # Effizienz berechnen
        df['effizienz_ratio'] = df['ist_dauer_min'] / df['soll_dauer_min']
        df['abweichung_min'] = df['ist_dauer_min'] - df['soll_dauer_min']
        df['abweichung_prozent'] = (df['abweichung_min'] / df['soll_dauer_min'] * 100)

        # Fehlende Werte
        df['marke'] = df['marke'].fillna('Unbekannt')
        df['power_kw'] = df['power_kw'].fillna(df['power_kw'].median())
        df['cubic_capacity'] = df['cubic_capacity'].fillna(df['cubic_capacity'].median())
        df['km_stand'] = df['km_stand'].fillna(df['km_stand'].median())
        df['fahrzeug_alter_jahre'] = df['fahrzeug_alter_jahre'].fillna(df['fahrzeug_alter_jahre'].median())
        df['productivity_factor'] = df['productivity_factor'].fillna(1.0)
        df['years_experience'] = df['years_experience'].fillna(df['years_experience'].median())
        df['urgency'] = df['urgency'].fillna(0)
        df['auftragstyp'] = df['auftragstyp'].fillna('X')
        df['charge_type'] = df['charge_type'].fillna(0)
        df['labour_type'] = df['labour_type'].fillna('N')
        df['meister'] = df['meister'].fillna(False).astype(int)

        # Finale Spalten
        feature_columns = [
            'order_number', 'order_date', 'betrieb',
            # SOLL und IST
            'soll_aw', 'soll_dauer_min', 'ist_dauer_min',
            'effizienz_ratio', 'abweichung_min', 'abweichung_prozent',
            # Stempel-Infos
            'anzahl_mechaniker', 'anzahl_stempel',
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
        print("FEATURE-STATISTIKEN (ECHTE STEMPELUHR-DATEN!)")
        print("=" * 70)

        print(f"\nDatensätze: {len(df_final):,}")
        print(f"Features: {len(df_final.columns)}")
        print(f"Zeitraum: {df_final['order_date'].min()} bis {df_final['order_date'].max()}")

        print(f"\n{'='*50}")
        print("SOLL-Dauer (Herstellervorgabe):")
        print(f"  Min:    {df_final['soll_dauer_min'].min():.0f} min")
        print(f"  Max:    {df_final['soll_dauer_min'].max():.0f} min")
        print(f"  Median: {df_final['soll_dauer_min'].median():.0f} min")
        print(f"  Mean:   {df_final['soll_dauer_min'].mean():.0f} min")

        print(f"\n{'='*50}")
        print("IST-Dauer (ECHTE STEMPELZEIT!):")
        print(f"  Min:    {df_final['ist_dauer_min'].min():.0f} min")
        print(f"  Max:    {df_final['ist_dauer_min'].max():.0f} min")
        print(f"  Median: {df_final['ist_dauer_min'].median():.0f} min")
        print(f"  Mean:   {df_final['ist_dauer_min'].mean():.0f} min")

        print(f"\n{'='*50}")
        print("Effizienz (IST/SOLL):")
        print(f"  Min:    {df_final['effizienz_ratio'].min():.2f}x")
        print(f"  Max:    {df_final['effizienz_ratio'].max():.2f}x")
        print(f"  Median: {df_final['effizienz_ratio'].median():.2f}x")
        print(f"  Mean:   {df_final['effizienz_ratio'].mean():.2f}x")

        # Effizienz-Verteilung
        schneller = (df_final['effizienz_ratio'] < 1).sum()
        normal = ((df_final['effizienz_ratio'] >= 1) & (df_final['effizienz_ratio'] <= 1.5)).sum()
        langsamer = (df_final['effizienz_ratio'] > 1.5).sum()
        print(f"\n  Schneller als Vorgabe: {schneller:,} ({schneller/len(df_final)*100:.1f}%)")
        print(f"  Im Rahmen (1-1.5x):    {normal:,} ({normal/len(df_final)*100:.1f}%)")
        print(f"  Langsamer (>1.5x):     {langsamer:,} ({langsamer/len(df_final)*100:.1f}%)")

        print(f"\n{'='*50}")
        print("Marken-Verteilung:")
        for marke, count in df_final['marke'].value_counts().head(5).items():
            print(f"  {marke}: {count:,} ({count/len(df_final)*100:.1f}%)")

        # Speichern
        print(f"\n{'='*50}")
        print(f"Speichere nach: {OUTPUT_PATH}")
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        df_final.to_csv(OUTPUT_PATH, index=False)
        print(f"Datei gespeichert ({os.path.getsize(OUTPUT_PATH) / 1024:.1f} KB)")

        return df_final

    finally:
        conn.close()


if __name__ == "__main__":
    start_date = sys.argv[1] if len(sys.argv) > 1 else '2023-01-01'
    end_date = sys.argv[2] if len(sys.argv) > 2 else None

    df = extract_all_features(start_date, end_date)

    if df is not None:
        print("\n" + "=" * 70)
        print("V4 EXTRAKTION ABGESCHLOSSEN!")
        print("=" * 70)
        print(f"\nNächster Schritt:")
        print(f"  python train_auftragsdauer_model_v2.py /opt/greiner-portal/data/ml/auftraege_features_v4.csv")
