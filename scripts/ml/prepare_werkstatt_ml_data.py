#!/usr/bin/env python3
"""
=============================================================================
GREINER DRIVE - Werkstatt ML Trainings-Daten
=============================================================================
Erstellt kompletten Datensatz für Machine Learning:
- Auftragsdauer-Vorhersage
- Upselling-Empfehlungen  
- Teile-Analyse
- HU/AU Reminder
"""

import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime
import os

print("=" * 60)
print("GREINER DRIVE - ML Daten-Vorbereitung")
print("=" * 60)

# Locosoft Connection
conn = psycopg2.connect(
    host="10.80.80.8",
    database="loco_auswertung_db",
    user="loco_auswertung_benutzer",
    password="loco"
)

# =============================================================================
# 1. AUFTRÄGE MIT ZEITEN (für Dauer-Vorhersage)
# =============================================================================
print("\n[1/4] Lade Aufträge mit Arbeitszeiten...")

query_auftraege = """
SELECT 
    t.order_number,
    t.order_position,
    t.employee_number as mechaniker_nr,
    t.duration_minutes as ist_dauer_min,
    l.time_units as vorgabe_aw,
    l.labour_operation_id as arbeitsart_id,
    l.labour_type,
    o.subsidiary as betrieb,
    o.order_date,
    EXTRACT(DOW FROM o.order_date) as wochentag,
    EXTRACT(MONTH FROM o.order_date) as monat,
    EXTRACT(HOUR FROM t.start_time) as start_stunde,
    v.mileage_km as km_stand,
    m.description as marke,
    v.first_registration_date,
    v.next_general_inspection_date as naechste_hu,
    v.next_emission_test_date as naechste_au,
    DATE_PART('year', AGE(o.order_date, v.first_registration_date)) as fahrzeug_alter_jahre
FROM times t
JOIN labours l ON t.order_number = l.order_number 
    AND t.order_position = l.order_position
JOIN orders o ON t.order_number = o.number
LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
LEFT JOIN makes m ON v.make_number = m.make_number
WHERE t.duration_minutes > 0
    AND t.duration_minutes < 480
    AND l.time_units > 0
    AND l.time_units < 100
    AND o.order_date >= '2024-01-01'
"""

df_auftraege = pd.read_sql(query_auftraege, conn)
print(f"   Aufträge geladen: {len(df_auftraege):,}")

# =============================================================================
# 2. TEILE AUF AUFTRÄGEN (für Upselling)
# =============================================================================
print("\n[2/4] Lade Teile auf Aufträgen...")

query_teile = """
SELECT 
    p.order_number,
    p.part_number,
    p.amount as menge,
    p.sum as preis,
    pm.description as teil_beschreibung,
    pm.parts_type as teil_typ
FROM parts p
LEFT JOIN parts_master pm ON p.part_number = pm.part_number
JOIN orders o ON p.order_number = o.number
WHERE o.order_date >= '2024-01-01'
    AND p.amount > 0
"""

df_teile = pd.read_sql(query_teile, conn)
print(f"   Teile-Positionen geladen: {len(df_teile):,}")

# =============================================================================
# 3. TEILE-KOMBINATIONEN (welche Teile werden zusammen verbaut?)
# =============================================================================
print("\n[3/4] Analysiere Teile-Kombinationen...")

teile_pro_auftrag = df_teile.groupby('order_number')['part_number'].apply(list).reset_index()
teile_pro_auftrag.columns = ['order_number', 'teile_liste']
print(f"   Aufträge mit Teilen: {len(teile_pro_auftrag):,}")

# =============================================================================
# 4. FAHRZEUGE MIT HU/AU STATUS
# =============================================================================
print("\n[4/4] Lade Fahrzeuge mit HU/AU Terminen...")

query_fahrzeuge = """
SELECT 
    v.internal_number,
    v.license_plate as kennzeichen,
    m.description as marke,
    v.first_registration_date,
    v.next_general_inspection_date as naechste_hu,
    v.next_emission_test_date as naechste_au
FROM vehicles v
LEFT JOIN makes m ON v.make_number = m.make_number
WHERE v.next_general_inspection_date IS NOT NULL
    OR v.next_emission_test_date IS NOT NULL
"""

df_fahrzeuge = pd.read_sql(query_fahrzeuge, conn)
print(f"   Fahrzeuge mit HU/AU: {len(df_fahrzeuge):,}")

conn.close()

# =============================================================================
# SPEICHERN
# =============================================================================
print("\n" + "=" * 60)
print("SPEICHERE DATENSÄTZE...")
print("=" * 60)

output_dir = "/opt/greiner-portal/data/ml"
os.makedirs(output_dir, exist_ok=True)

df_auftraege.to_csv(f"{output_dir}/auftraege_mit_zeiten.csv", index=False)
print(f"✅ {output_dir}/auftraege_mit_zeiten.csv ({len(df_auftraege):,} Zeilen)")

df_teile.to_csv(f"{output_dir}/teile_auf_auftraegen.csv", index=False)
print(f"✅ {output_dir}/teile_auf_auftraegen.csv ({len(df_teile):,} Zeilen)")

df_fahrzeuge.to_csv(f"{output_dir}/fahrzeuge_hu_au.csv", index=False)
print(f"✅ {output_dir}/fahrzeuge_hu_au.csv ({len(df_fahrzeuge):,} Zeilen)")

# =============================================================================
# STATISTIK
# =============================================================================
print("\n" + "=" * 60)
print("STATISTIK")
print("=" * 60)

print(f"\n📊 AUFTRÄGE:")
print(f"   Zeitraum: {df_auftraege['order_date'].min()} bis {df_auftraege['order_date'].max()}")
print(f"   Mechaniker: {df_auftraege['mechaniker_nr'].nunique()}")
print(f"   Ø Vorgabe: {df_auftraege['vorgabe_aw'].mean():.1f} AW")
print(f"   Ø IST-Dauer: {df_auftraege['ist_dauer_min'].mean():.1f} min")

print(f"\n📊 MARKEN:")
print(df_auftraege['marke'].value_counts().head(5).to_string())

print(f"\n📊 TEILE:")
print(f"   Verschiedene Teile: {df_teile['part_number'].nunique():,}")
print(f"   Ø Teile pro Auftrag: {df_teile.groupby('order_number').size().mean():.1f}")

print(f"\n📊 HU/AU DATEN:")
print(f"   Fahrzeuge mit HU-Termin: {df_fahrzeuge['naechste_hu'].notna().sum()}")
print(f"   Fahrzeuge mit AU-Termin: {df_fahrzeuge['naechste_au'].notna().sum()}")

print("\n✅ FERTIG!")
