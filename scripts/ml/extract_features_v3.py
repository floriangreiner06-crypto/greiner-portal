#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
GREINER DRIVE - Feature Extraktion V3 (TAG 119)
=============================================================================
ECHTE SOLL vs IST Daten!

SOLL (Vorgabe):
- Herstellervorgabe: SUM(labours.time_units) * 6 Minuten

IST (Tatsächlich):
- Werkstatt-Durchlaufzeit: invoice_created - order_estimated_inbound
- Gefiltert auf realistische Werte (10-480 min)

Features:
- Alle V2-Features plus Zeitstempel-basierte IST-Dauer
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

OUTPUT_PATH = "/opt/greiner-portal/data/ml/auftraege_features_v3.csv"


def get_locosoft_connection():
    """Erstellt Verbindung zur Locosoft PostgreSQL DB"""
    return psycopg2.connect(**LOCO_CONFIG)


def extract_orders_with_real_times(conn, start_date='2023-01-01', end_date=None):
    """
    Extrahiert Aufträge mit ECHTEN SOLL vs IST Zeiten.

    SOLL = Herstellervorgabe (AW × 6 min)
    IST = Tatsächliche Werkstatt-Durchlaufzeit (Rechnung - Ankunft)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    query = """
    WITH order_base AS (
        SELECT
            o.number as order_number,
            o.subsidiary as betrieb,
            o.order_date,
            o.estimated_inbound_time,
            o.order_classification_flag,
            o.urgency,
            o.vehicle_number,
            o.order_customer,
            MIN(i.internal_created_time) as invoice_created_time
        FROM orders o
        JOIN invoices i ON o.number = i.order_number
        WHERE o.order_date >= %s
          AND o.order_date <= %s
          AND o.estimated_inbound_time IS NOT NULL
          AND i.internal_created_time IS NOT NULL
          AND i.internal_created_time > o.estimated_inbound_time
          AND i.is_canceled = false
        GROUP BY o.number, o.subsidiary, o.order_date, o.estimated_inbound_time,
                 o.order_classification_flag, o.urgency, o.vehicle_number, o.order_customer
    ),
    order_labours AS (
        SELECT
            l.order_number,
            SUM(l.time_units) as soll_aw,
            COUNT(DISTINCT l.order_position) as anzahl_positionen,
            MAX(l.charge_type) as charge_type,
            MAX(l.labour_type) as labour_type,
            MIN(l.mechanic_no) as mechaniker_nr
        FROM labours l
        WHERE l.time_units > 0
          AND l.is_invoiced = true
        GROUP BY l.order_number
    ),
    order_parts AS (
        SELECT
            order_number,
            COUNT(*) as anzahl_teile,
            SUM(amount) as teile_menge
        FROM parts
        WHERE is_invoiced = true
        GROUP BY order_number
    )
    SELECT
        ob.order_number,
        ob.betrieb,
        ob.order_date,
        ob.estimated_inbound_time,
        ob.invoice_created_time,
        ob.order_classification_flag,
        ob.urgency,
        ob.vehicle_number,
        -- SOLL: Herstellervorgabe in Minuten
        COALESCE(ol.soll_aw, 0) * 6 as soll_dauer_min,
        COALESCE(ol.soll_aw, 0) as soll_aw,
        -- IST: Tatsächliche Durchlaufzeit in Minuten
        EXTRACT(EPOCH FROM (ob.invoice_created_time - ob.estimated_inbound_time)) / 60 as ist_dauer_min,
        ol.anzahl_positionen,
        ol.charge_type,
        ol.labour_type,
        ol.mechaniker_nr,
        COALESCE(op.anzahl_teile, 0) as anzahl_teile,
        COALESCE(op.teile_menge, 0) as teile_menge
    FROM order_base ob
    LEFT JOIN order_labours ol ON ob.order_number = ol.order_number
    LEFT JOIN order_parts op ON ob.order_number = op.order_number
    WHERE ol.soll_aw > 0
      -- Filter: Realistische IST-Dauer (10 min bis 8 Stunden)
      AND EXTRACT(EPOCH FROM (ob.invoice_created_time - ob.estimated_inbound_time)) / 60 BETWEEN 10 AND 480
      -- Filter: SOLL muss kleiner als IST sein (sonst Datenfehler)
      AND ol.soll_aw * 6 < EXTRACT(EPOCH FROM (ob.invoice_created_time - ob.estimated_inbound_time)) / 60 * 2
    ORDER BY ob.order_date DESC
    """

    print(f"  Lade Aufträge von {start_date} bis {end_date}...")
    df = pd.read_sql(query, conn, params=(start_date, end_date))
    print(f"  {len(df):,} Aufträge mit echten SOLL/IST-Zeiten geladen")

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
    """Extrahiert Mitarbeiter-Features"""
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


def extract_all_features(start_date='2023-01-01', end_date=None):
    """
    Hauptfunktion: Extrahiert alle Features mit ECHTEN SOLL/IST.
    """
    print("=" * 70)
    print("GREINER DRIVE - Feature Extraktion V3 (ECHTE SOLL vs IST)")
    print("=" * 70)

    conn = get_locosoft_connection()

    try:
        # 1. Basis-Aufträge mit echten Zeiten
        print("\n[1/5] Lade Aufträge mit echten SOLL/IST-Zeiten...")
        df_orders = extract_orders_with_real_times(conn, start_date, end_date)

        if len(df_orders) == 0:
            print("FEHLER: Keine Aufträge mit gültigen Zeitstempeln gefunden!")
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
        df['estimated_inbound_time'] = pd.to_datetime(df['estimated_inbound_time'])
        df['wochentag'] = df['estimated_inbound_time'].dt.dayofweek
        df['monat'] = df['estimated_inbound_time'].dt.month
        df['start_stunde'] = df['estimated_inbound_time'].dt.hour
        df['kalenderwoche'] = df['estimated_inbound_time'].dt.isocalendar().week

        # Effizienz-Ratio berechnen (IST / SOLL)
        df['effizienz_ratio'] = df['ist_dauer_min'] / df['soll_dauer_min']

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

        # Spalten umbenennen
        df = df.rename(columns={
            'order_classification_flag': 'auftragstyp',
            'is_master_craftsman': 'meister'
        })

        # Relevante Spalten
        feature_columns = [
            'order_number', 'order_date', 'betrieb',
            # SOLL und IST (Target!)
            'soll_aw', 'soll_dauer_min', 'ist_dauer_min', 'effizienz_ratio',
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
        print("FEATURE-STATISTIKEN (ECHTE DATEN!)")
        print("=" * 70)
        print(f"\nDatensätze: {len(df_final):,}")
        print(f"Features: {len(df_final.columns)}")

        print(f"\nSOLL-Dauer (Herstellervorgabe):")
        print(f"  Min:    {df_final['soll_dauer_min'].min():.0f} min")
        print(f"  Max:    {df_final['soll_dauer_min'].max():.0f} min")
        print(f"  Median: {df_final['soll_dauer_min'].median():.0f} min")
        print(f"  Mean:   {df_final['soll_dauer_min'].mean():.0f} min")

        print(f"\nIST-Dauer (Tatsächlich):")
        print(f"  Min:    {df_final['ist_dauer_min'].min():.0f} min")
        print(f"  Max:    {df_final['ist_dauer_min'].max():.0f} min")
        print(f"  Median: {df_final['ist_dauer_min'].median():.0f} min")
        print(f"  Mean:   {df_final['ist_dauer_min'].mean():.0f} min")

        print(f"\nEffizienz-Ratio (IST/SOLL):")
        print(f"  Min:    {df_final['effizienz_ratio'].min():.2f}x")
        print(f"  Max:    {df_final['effizienz_ratio'].max():.2f}x")
        print(f"  Median: {df_final['effizienz_ratio'].median():.2f}x")
        print(f"  Mean:   {df_final['effizienz_ratio'].mean():.2f}x")

        print(f"\nMarken-Verteilung:")
        for marke, count in df_final['marke'].value_counts().head(5).items():
            print(f"  {marke}: {count:,} ({count/len(df_final)*100:.1f}%)")

        # Speichern
        print(f"\nSpeichere nach: {OUTPUT_PATH}")
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
        print("EXTRAKTION ABGESCHLOSSEN!")
        print("=" * 70)
        print(f"\nNächster Schritt:")
        print(f"  python train_auftragsdauer_model_v2.py /opt/greiner-portal/data/ml/auftraege_features_v3.csv")
