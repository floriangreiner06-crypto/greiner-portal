#!/usr/bin/env python3
"""
=============================================================================
GREINER DRIVE - ML Daten-Vorbereitung V2 (mit Qualitäts-Filter)
=============================================================================
Erstellt bereinigten Datensatz für Machine Learning:
- Filtert Azubis raus
- Filtert unplausible Stempelungen
- Nur Mechaniker mit ausreichend Daten
"""

import psycopg2
import pandas as pd
from datetime import datetime
import os

print("=" * 60)
print("GREINER DRIVE - ML Daten-Vorbereitung V2 (GEFILTERT)")
print("=" * 60)

# Locosoft Connection
conn = psycopg2.connect(
    host="10.80.80.8",
    database="loco_auswertung_db",
    user="loco_auswertung_benutzer",
    password="loco"
)

# =============================================================================
# 1. AUFTRÄGE MIT ZEITEN - GEFILTERT
# =============================================================================
print("\n[1/3] Lade Aufträge mit Qualitäts-Filter...")

query_auftraege = """
WITH mechaniker_stats AS (
    -- Berechne €/h pro Mechaniker für Plausibilitäts-Check
    SELECT 
        t.employee_number,
        COUNT(DISTINCT i.invoice_number) as rechnungen,
        SUM(t.duration_minutes) / 60.0 as gestempelt_h,
        SUM(i.job_amount_net) as kassiert_eur,
        CASE 
            WHEN SUM(t.duration_minutes) > 0 
            THEN SUM(i.job_amount_net) / (SUM(t.duration_minutes) / 60.0)
            ELSE 0 
        END as eur_pro_h
    FROM times t
    JOIN invoices i ON t.order_number = i.order_number
    WHERE i.invoice_date >= '2024-01-01'
        AND i.is_canceled = false
        AND t.duration_minutes > 0
    GROUP BY t.employee_number
),
plausible_mechaniker AS (
    -- Nur Mechaniker mit plausiblen Daten
    SELECT employee_number
    FROM mechaniker_stats
    WHERE rechnungen >= 100           -- Genug Daten
        AND eur_pro_h BETWEEN 150 AND 1200  -- Realistischer Bereich
        AND gestempelt_h >= 500       -- Min. 500h gestempelt
)
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
-- NUR plausible Mechaniker (keine Azubis, keine Ausreißer)
JOIN plausible_mechaniker pm ON t.employee_number = pm.employee_number
WHERE t.duration_minutes > 0
    AND t.duration_minutes < 480          -- Max 8h pro Position
    AND l.time_units > 0
    AND l.time_units < 100                -- Realistische Vorgaben
    AND o.order_date >= '2024-01-01'
    -- Plausibilitäts-Filter auf Einzelauftrags-Ebene
    AND t.duration_minutes >= l.time_units * 2    -- Min. 20% der Vorgabe
    AND t.duration_minutes <= l.time_units * 50   -- Max. 5x der Vorgabe
"""

df_auftraege = pd.read_sql(query_auftraege, conn)
print(f"   Gefilterte Aufträge: {len(df_auftraege):,}")

# =============================================================================
# 2. MECHANIKER-QUALITÄTS-REPORT
# =============================================================================
print("\n[2/3] Erstelle Mechaniker-Qualitäts-Report...")

query_qualitaet = """
SELECT 
    t.employee_number as mechaniker_nr,
    e.name as mechaniker_name,
    CASE WHEN e.mechanic_number IS NOT NULL THEN 'Mechaniker' ELSE 'Kein Mechaniker' END as typ,
    COUNT(DISTINCT i.invoice_number) as rechnungen,
    ROUND(SUM(t.duration_minutes)::numeric / 60, 1) as gestempelt_h,
    ROUND(SUM(i.job_amount_net)::numeric, 0) as kassiert_eur,
    ROUND((SUM(i.job_amount_net) / NULLIF(SUM(t.duration_minutes) / 60.0, 0))::numeric, 0) as eur_pro_h,
    CASE 
        WHEN COUNT(DISTINCT i.invoice_number) < 100 THEN 'Zu wenig Daten'
        WHEN SUM(t.duration_minutes) / 60.0 < 500 THEN 'Zu wenig Stunden'
        WHEN (SUM(i.job_amount_net) / NULLIF(SUM(t.duration_minutes) / 60.0, 0)) < 150 THEN 'Stempelt zu viel'
        WHEN (SUM(i.job_amount_net) / NULLIF(SUM(t.duration_minutes) / 60.0, 0)) > 1200 THEN 'Stempelt zu wenig'
        ELSE 'OK - Plausibel'
    END as status
FROM times t
JOIN invoices i ON t.order_number = i.order_number
JOIN employees e ON t.employee_number = e.employee_number AND e.is_latest_record = true
WHERE i.invoice_date >= '2024-01-01'
    AND i.is_canceled = false
    AND t.duration_minutes > 0
GROUP BY t.employee_number, e.name, e.mechanic_number
ORDER BY eur_pro_h DESC NULLS LAST
"""

df_qualitaet = pd.read_sql(query_qualitaet, conn)
print(f"   Mechaniker analysiert: {len(df_qualitaet)}")

# Status-Übersicht
status_counts = df_qualitaet['status'].value_counts()
print(f"\n   Status-Übersicht:")
for status, count in status_counts.items():
    print(f"      {status}: {count}")

# =============================================================================
# 3. TEILE AUF AUFTRÄGEN (unverändert)
# =============================================================================
print("\n[3/3] Lade Teile auf Aufträgen...")

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
print(f"   Teile-Positionen: {len(df_teile):,}")

conn.close()

# =============================================================================
# SPEICHERN
# =============================================================================
print("\n" + "=" * 60)
print("SPEICHERE DATENSÄTZE...")
print("=" * 60)

output_dir = "/opt/greiner-portal/data/ml"
os.makedirs(output_dir, exist_ok=True)

# Gefilterte Daten speichern
df_auftraege.to_csv(f"{output_dir}/auftraege_mit_zeiten_v2.csv", index=False)
print(f"✅ {output_dir}/auftraege_mit_zeiten_v2.csv ({len(df_auftraege):,} Zeilen)")

df_qualitaet.to_csv(f"{output_dir}/mechaniker_qualitaet.csv", index=False)
print(f"✅ {output_dir}/mechaniker_qualitaet.csv ({len(df_qualitaet)} Zeilen)")

df_teile.to_csv(f"{output_dir}/teile_auf_auftraegen.csv", index=False)
print(f"✅ {output_dir}/teile_auf_auftraegen.csv ({len(df_teile):,} Zeilen)")

# =============================================================================
# VERGLEICH: VORHER vs. NACHHER
# =============================================================================
print("\n" + "=" * 60)
print("VERGLEICH: UNGEFILTERT vs. GEFILTERT")
print("=" * 60)

# Alte Daten laden falls vorhanden
try:
    df_alt = pd.read_csv(f"{output_dir}/auftraege_mit_zeiten.csv")
    print(f"\n   VORHER (ungefiltert):  {len(df_alt):,} Datensätze")
    print(f"   NACHHER (gefiltert):   {len(df_auftraege):,} Datensätze")
    print(f"   Entfernt:              {len(df_alt) - len(df_auftraege):,} ({100*(len(df_alt)-len(df_auftraege))/len(df_alt):.1f}%)")
except:
    pass

# =============================================================================
# STATISTIK
# =============================================================================
print("\n" + "=" * 60)
print("STATISTIK (GEFILTERTE DATEN)")
print("=" * 60)

print(f"\n📊 AUFTRÄGE:")
print(f"   Zeitraum: {df_auftraege['order_date'].min()} bis {df_auftraege['order_date'].max()}")
print(f"   Mechaniker: {df_auftraege['mechaniker_nr'].nunique()}")
print(f"   Ø Vorgabe: {df_auftraege['vorgabe_aw'].mean():.1f} AW")
print(f"   Ø IST-Dauer: {df_auftraege['ist_dauer_min'].mean():.1f} min")

# Verhältnis IST/Vorgabe
df_auftraege['verhaeltnis'] = df_auftraege['ist_dauer_min'] / (df_auftraege['vorgabe_aw'] * 10)
print(f"   Ø Verhältnis IST/Vorgabe: {df_auftraege['verhaeltnis'].mean():.2f}x")

print(f"\n📊 MARKEN:")
print(df_auftraege['marke'].value_counts().head(5).to_string())

print("\n✅ FERTIG! Daten bereit für ML-Training V2")
