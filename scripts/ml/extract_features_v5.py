#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
GREINER DRIVE - Feature Extraktion V5.1 (TAG 119 - DUPLICATE FIX)
=============================================================================
QUALITÄTSGEPRÜFTE Stempeluhr-Daten + DEDUPLIZIERT!

Verbesserungen gegenüber V4:
- Qualitätsfilter: Nur plausible Daten
- Cross-Check: Stempelzeit vs. Durchlaufzeit
- Konfidenz-Score pro Datensatz

QUALITÄTSKRITERIEN:
1. Mindestens 2 Stempel (Start + Ende)
2. Effizienz-Ratio zwischen 0.3 und 8.0
3. Mindestens 1 Stempel pro Arbeitsposition
4. Cross-Check mit Durchlaufzeit (optional)

SOLL (Vorgabe):
- Herstellervorgabe: SUM(labours.time_units) * 6 Minuten

IST (Tatsächlich):
- ECHTE ARBEITSZEIT aus times-Tabelle (Stempeluhr!)
- SUM(times.duration_minutes) pro Auftrag
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

OUTPUT_PATH = "/opt/greiner-portal/data/ml/auftraege_features_v5.csv"

# Qualitätsfilter-Parameter
MIN_STEMPEL = 2           # Mindestens Start + Ende
MIN_RATIO = 0.3           # Minimum IST/SOLL (darunter = verdächtig schnell)
MAX_RATIO = 8.0           # Maximum IST/SOLL (darüber = verdächtig langsam)
MIN_STEMPEL_PRO_POS = 0.5 # Mindestens 0.5 Stempel pro Position


def get_locosoft_connection():
    return psycopg2.connect(**LOCO_CONFIG)


def extract_orders_with_quality_check(conn, start_date='2023-01-01', end_date=None):
    """
    Extrahiert Aufträge mit ECHTEN Stempelzeiten UND Qualitätsprüfung.

    Zusätzlich: Cross-Check mit Durchlaufzeit (Invoice - Ankunft)
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
            o.estimated_inbound_time,
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
                 o.order_classification_flag, o.urgency, o.vehicle_number,
                 o.estimated_inbound_time
    ),
    unique_times AS (
        -- DISTINCT um Duplikate pro Arbeitsposition zu entfernen (TAG 119 FIX)
        SELECT DISTINCT
            order_number,
            employee_number,
            start_time,
            end_time,
            duration_minutes
        FROM times
        WHERE order_number > 0
          AND duration_minutes > 0
          AND start_time >= %s
    ),
    order_times AS (
        -- IST: Echte Arbeitszeit aus Stempeluhr (DEDUPLIZIERT!)
        SELECT
            order_number,
            COUNT(DISTINCT employee_number) as anzahl_mechaniker,
            COUNT(*) as anzahl_stempel,
            SUM(duration_minutes) as ist_dauer_min,
            MIN(start_time) as erste_buchung,
            MAX(end_time) as letzte_buchung
        FROM unique_times
        GROUP BY order_number
    ),
    order_parts AS (
        SELECT
            order_number,
            COUNT(*) as anzahl_teile
        FROM parts
        WHERE is_invoiced = true
        GROUP BY order_number
    ),
    order_invoice AS (
        -- Für Cross-Check: Durchlaufzeit
        SELECT
            order_number,
            MIN(internal_created_time) as invoice_time
        FROM invoices
        WHERE is_canceled = false
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
        COALESCE(op.anzahl_teile, 0) as anzahl_teile,
        -- Cross-Check Daten
        ol.estimated_inbound_time,
        oi.invoice_time,
        CASE
            WHEN ol.estimated_inbound_time IS NOT NULL AND oi.invoice_time IS NOT NULL
            THEN EXTRACT(EPOCH FROM (oi.invoice_time - ol.estimated_inbound_time)) / 60
            ELSE NULL
        END as durchlaufzeit_min
    FROM order_labours ol
    INNER JOIN order_times ot ON ol.order_number = ot.order_number
    LEFT JOIN order_parts op ON ol.order_number = op.order_number
    LEFT JOIN order_invoice oi ON ol.order_number = oi.order_number
    WHERE ol.soll_aw > 0
      AND ot.ist_dauer_min > 0
      -- Basis-Filter: Realistische Werte
      AND ot.ist_dauer_min BETWEEN 5 AND 600  -- 5 min bis 10 Stunden
      AND ol.soll_aw * 6 BETWEEN 3 AND 500     -- Plausible Vorgabe
    ORDER BY ol.order_date DESC
    """

    print(f"  Lade Aufträge von {start_date} bis {end_date}...")
    df = pd.read_sql(query, conn, params=(start_date, end_date, start_date))
    print(f"  {len(df):,} Aufträge mit Stempelzeiten geladen (vor Qualitätsfilter)")

    return df


def apply_quality_filters(df):
    """
    Wendet Qualitätsfilter an und berechnet Konfidenz-Score.
    """
    original_count = len(df)

    # Effizienz berechnen
    df['effizienz_ratio'] = df['ist_dauer_min'] / df['soll_dauer_min']
    df['stempel_pro_pos'] = df['anzahl_stempel'] / df['anzahl_positionen']

    print(f"\n  QUALITÄTSFILTER:")

    # Filter 1: Mindestens 2 Stempel
    before = len(df)
    df = df[df['anzahl_stempel'] >= MIN_STEMPEL].copy()
    removed = before - len(df)
    print(f"    - Min. {MIN_STEMPEL} Stempel: {removed:,} entfernt ({removed/original_count*100:.1f}%)")

    # Filter 2: Plausible Effizienz-Ratio
    before = len(df)
    df = df[(df['effizienz_ratio'] >= MIN_RATIO) & (df['effizienz_ratio'] <= MAX_RATIO)].copy()
    removed = before - len(df)
    print(f"    - Ratio {MIN_RATIO}-{MAX_RATIO}x: {removed:,} entfernt ({removed/original_count*100:.1f}%)")

    # Filter 3: Mindestens X Stempel pro Position
    before = len(df)
    df = df[df['stempel_pro_pos'] >= MIN_STEMPEL_PRO_POS].copy()
    removed = before - len(df)
    print(f"    - Min. {MIN_STEMPEL_PRO_POS} Stempel/Pos: {removed:,} entfernt ({removed/original_count*100:.1f}%)")

    print(f"\n  Nach Qualitätsfilter: {len(df):,} Aufträge ({len(df)/original_count*100:.1f}% behalten)")

    # Konfidenz-Score berechnen (0-100)
    df['konfidenz_score'] = calculate_confidence_score(df)

    return df


def calculate_confidence_score(df):
    """
    Berechnet Konfidenz-Score (0-100) basierend auf Datenqualität.

    Faktoren:
    - Anzahl Stempel (mehr = besser)
    - Effizienz-Ratio nähe zu 1.0-2.0 (typisch = besser)
    - Stempel pro Position
    - Cross-Check mit Durchlaufzeit (wenn verfügbar)
    """
    scores = pd.DataFrame(index=df.index)

    # Faktor 1: Anzahl Stempel (max 30 Punkte)
    # 2 Stempel = 10, 5+ Stempel = 30
    scores['stempel_score'] = np.clip((df['anzahl_stempel'] - 1) * 6, 0, 30)

    # Faktor 2: Effizienz-Ratio Plausibilität (max 40 Punkte)
    # Optimal bei 1.0-2.5x, schlechter bei Extremen
    ratio = df['effizienz_ratio']
    scores['ratio_score'] = 40 - np.clip(np.abs(ratio - 1.5) * 15, 0, 35)

    # Faktor 3: Stempel pro Position (max 20 Punkte)
    scores['spp_score'] = np.clip(df['stempel_pro_pos'] * 10, 0, 20)

    # Faktor 4: Cross-Check mit Durchlaufzeit (max 10 Punkte)
    # Wenn Stempelzeit < Durchlaufzeit und > 50% davon = gut
    if 'durchlaufzeit_min' in df.columns:
        dl = df['durchlaufzeit_min'].fillna(df['ist_dauer_min'] * 2)
        ist = df['ist_dauer_min']
        # Score hoch wenn IST zwischen 30% und 100% der Durchlaufzeit
        ratio_dl = ist / dl.replace(0, 1)
        scores['crosscheck_score'] = np.where(
            (ratio_dl >= 0.3) & (ratio_dl <= 1.0),
            10,
            np.where(ratio_dl < 0.3, ratio_dl * 30, 10 - (ratio_dl - 1) * 10)
        )
        scores['crosscheck_score'] = np.clip(scores['crosscheck_score'], 0, 10)
    else:
        scores['crosscheck_score'] = 5  # Neutral wenn nicht verfügbar

    # Gesamtscore
    total = scores['stempel_score'] + scores['ratio_score'] + scores['spp_score'] + scores['crosscheck_score']
    return np.clip(total, 0, 100).astype(int)


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
    """Hauptfunktion: Qualitätsgeprüfte Stempeluhr-Daten für ML"""

    print("=" * 70)
    print("GREINER DRIVE - Feature Extraktion V5")
    print("QUALITÄTSGEPRÜFTE STEMPELUHR-DATEN!")
    print("=" * 70)
    print(f"\nQualitätskriterien:")
    print(f"  - Min. Stempel: {MIN_STEMPEL}")
    print(f"  - Ratio-Bereich: {MIN_RATIO}x - {MAX_RATIO}x")
    print(f"  - Min. Stempel/Position: {MIN_STEMPEL_PRO_POS}")

    conn = get_locosoft_connection()

    try:
        # 1. Aufträge mit echten Zeiten + Cross-Check Daten
        print(f"\n[1/6] Lade Aufträge mit Stempelzeiten...")
        df_orders = extract_orders_with_quality_check(conn, start_date, end_date)

        if len(df_orders) == 0:
            print("FEHLER: Keine Aufträge gefunden!")
            return None

        # 2. Qualitätsfilter anwenden
        print(f"\n[2/6] Wende Qualitätsfilter an...")
        df_orders = apply_quality_filters(df_orders)

        if len(df_orders) == 0:
            print("FEHLER: Keine Aufträge nach Qualitätsfilter!")
            return None

        # 3. Fahrzeug-Features
        print(f"\n[3/6] Lade Fahrzeug-Features...")
        vehicle_numbers = [int(x) for x in df_orders['vehicle_number'].dropna().unique()]
        df_vehicles = extract_vehicle_features(conn, vehicle_numbers)
        print(f"  {len(df_vehicles):,} Fahrzeuge")

        # 4. Mitarbeiter-Features
        print(f"\n[4/6] Lade Mitarbeiter-Features...")
        employee_numbers = [int(x) for x in df_orders['mechaniker_nr'].dropna().unique()]
        df_employees = extract_employee_features(conn, employee_numbers)
        print(f"  {len(df_employees):,} Mechaniker")

        # 5. Kombinieren
        print(f"\n[5/6] Kombiniere Features...")

        df = df_orders.merge(
            df_vehicles[['vehicle_number', 'marke', 'power_kw', 'cubic_capacity',
                        'km_stand', 'fahrzeug_alter_jahre']],
            on='vehicle_number', how='left'
        )

        df = df.merge(
            df_employees[['mechaniker_nr', 'productivity_factor', 'years_experience', 'meister']],
            on='mechaniker_nr', how='left'
        )

        # 6. Feature Engineering
        print(f"\n[6/6] Feature Engineering...")

        df['order_date'] = pd.to_datetime(df['order_date'])
        df['erste_buchung'] = pd.to_datetime(df['erste_buchung'])

        # Zeitfeatures
        df['wochentag'] = df['erste_buchung'].dt.dayofweek
        df['monat'] = df['erste_buchung'].dt.month
        df['start_stunde'] = df['erste_buchung'].dt.hour
        df['kalenderwoche'] = df['erste_buchung'].dt.isocalendar().week

        # Abweichungen
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

        # Finale Spalten (inkl. Konfidenz-Score!)
        feature_columns = [
            'order_number', 'order_date', 'betrieb',
            # SOLL und IST
            'soll_aw', 'soll_dauer_min', 'ist_dauer_min',
            'effizienz_ratio', 'abweichung_min', 'abweichung_prozent',
            # Qualitäts-Features
            'anzahl_mechaniker', 'anzahl_stempel', 'stempel_pro_pos', 'konfidenz_score',
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
        print("FEATURE-STATISTIKEN (QUALITÄTSGEPRÜFTE DATEN!)")
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
        print("IST-Dauer (QUALITÄTSGEPRÜFTE STEMPELZEIT!):")
        print(f"  Min:    {df_final['ist_dauer_min'].min():.0f} min")
        print(f"  Max:    {df_final['ist_dauer_min'].max():.0f} min")
        print(f"  Median: {df_final['ist_dauer_min'].median():.0f} min")
        print(f"  Mean:   {df_final['ist_dauer_min'].mean():.0f} min")

        print(f"\n{'='*50}")
        print("Effizienz (IST/SOLL) - nur plausible Daten:")
        print(f"  Min:    {df_final['effizienz_ratio'].min():.2f}x")
        print(f"  Max:    {df_final['effizienz_ratio'].max():.2f}x")
        print(f"  Median: {df_final['effizienz_ratio'].median():.2f}x")
        print(f"  Mean:   {df_final['effizienz_ratio'].mean():.2f}x")

        print(f"\n{'='*50}")
        print("Konfidenz-Score:")
        print(f"  Min:    {df_final['konfidenz_score'].min()}")
        print(f"  Max:    {df_final['konfidenz_score'].max()}")
        print(f"  Median: {df_final['konfidenz_score'].median():.0f}")
        print(f"  Mean:   {df_final['konfidenz_score'].mean():.0f}")

        # Konfidenz-Verteilung
        hoch = (df_final['konfidenz_score'] >= 70).sum()
        mittel = ((df_final['konfidenz_score'] >= 40) & (df_final['konfidenz_score'] < 70)).sum()
        niedrig = (df_final['konfidenz_score'] < 40).sum()
        print(f"\n  Hohe Konfidenz (>=70):    {hoch:,} ({hoch/len(df_final)*100:.1f}%)")
        print(f"  Mittlere Konfidenz (40-69): {mittel:,} ({mittel/len(df_final)*100:.1f}%)")
        print(f"  Niedrige Konfidenz (<40):   {niedrig:,} ({niedrig/len(df_final)*100:.1f}%)")

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
        print("V5 EXTRAKTION ABGESCHLOSSEN!")
        print("=" * 70)
        print(f"\nNächster Schritt:")
        print(f"  python train_auftragsdauer_model_v2.py /opt/greiner-portal/data/ml/auftraege_features_v5.csv")
