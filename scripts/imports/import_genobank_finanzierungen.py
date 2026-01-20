#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genobank-Finanzierungen Import aus Locosoft
Holt Fahrzeuge mit Codefeld "Brief" = "Genobank" aus Locosoft
und speichert sie in fahrzeugfinanzierungen-Tabelle

Zinsbeginn-Logik:
1. Erstelldatum aus codes_vehicle_date (wenn vorhanden)
2. Oder: VIN nicht mehr in Stellantis Bestand UND Brief-Flag aktiv
"""

import sys
from datetime import datetime, date, timedelta

# Projekt-Pfad für Imports
sys.path.insert(0, '/opt/greiner-portal')
from api.db_connection import get_db
from api.db_utils import locosoft_session, db_session, row_to_dict, rows_to_list

print("\n" + "="*80)
print("📦 GENOBANK-FINANZIERUNGEN IMPORT AUS LOCOSOFT")
print("="*80 + "\n")

# PostgreSQL-Verbindung (DRIVE Portal)
drive_conn = get_db()
drive_cursor = drive_conn.cursor()

# 1. Alte Genobank-Finanzierungen löschen
print("🗑️  Lösche alte Genobank-Finanzierungen...")
drive_cursor.execute("DELETE FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Genobank'")
deleted = drive_cursor.rowcount
drive_conn.commit()
print(f"   ✓ {deleted} alte Einträge gelöscht\n")

# 2. Hole Genobank-Fahrzeuge aus Locosoft
print("📋 Hole Genobank-Fahrzeuge aus Locosoft...")

with locosoft_session() as loco_conn:
    loco_cursor = loco_conn.cursor()
    
    # Query: Fahrzeuge mit Brief="Genobank" UND noch im Bestand (nicht verkauft)
    # WICHTIG: Starte mit codes_vehicle_list (hat die Brief-Flags) und joine dann zu vehicles
    query = """
        SELECT DISTINCT
            dv.dealer_vehicle_number,
            dv.dealer_vehicle_type,
            v.vin,
            v.free_form_model_text as modell,
            v.first_registration_date as ez,
            dv.in_arrival_date as eingang,
            dv.created_date,
            -- EK-Rechnung Nettowert (bereits NETTO in Locosoft!)
            COALESCE(dv.calc_basic_charge, 0) + COALESCE(dv.calc_accessory, 0)
                + COALESCE(dv.calc_extra_expenses, 0)
                + COALESCE(dv.calc_usage_value_encr_internal, 0)
                + COALESCE(dv.calc_usage_value_encr_external, 0) as ek_netto,
            dv.in_buy_invoice_no_date as ek_rechnung_datum,
            -- Brief-Flag Erstelldatum (aus codes_vehicle_date)
            cv_date.date as brief_erstellt_am
        FROM codes_vehicle_list cv
        INNER JOIN vehicles v
            ON cv.vehicle_number = v.internal_number
        INNER JOIN dealer_vehicles dv
            ON v.dealer_vehicle_number = dv.dealer_vehicle_number
            AND v.dealer_vehicle_type = dv.dealer_vehicle_type
        LEFT JOIN codes_vehicle_date cv_date
            ON v.internal_number = cv_date.vehicle_number
            AND UPPER(TRIM(cv_date.code)) = 'BRIEF'
        WHERE UPPER(TRIM(cv.code)) = 'BRIEF'
          AND (UPPER(TRIM(cv.value_text)) = 'GENOBANK' 
               OR UPPER(TRIM(cv.value_text)) = 'GENBANK'
               OR UPPER(TRIM(cv.value_text)) LIKE '%GENO%BANK%'
               OR UPPER(TRIM(cv.value_text)) LIKE '%GENBANK%')
          AND dv.out_invoice_date IS NULL  -- Noch nicht verkauft
          AND v.vin IS NOT NULL
          AND v.vin != ''
        ORDER BY dv.dealer_vehicle_number
    """
    
    loco_cursor.execute(query)
    genobank_fahrzeuge = rows_to_list(loco_cursor.fetchall(), loco_cursor)
    
    print(f"   ✓ {len(genobank_fahrzeuge)} Fahrzeuge gefunden\n")

# 3. Prüfe Stellantis Bestand für Zinsbeginn-Logik
print("🔍 Prüfe Stellantis Bestand für Zinsbeginn-Logik...")
drive_cursor.execute("""
    SELECT DISTINCT vin
    FROM fahrzeugfinanzierungen
    WHERE finanzinstitut = 'Stellantis' AND aktiv = true
""")
stellantis_vins = {row[0] for row in drive_cursor.fetchall() if row[0]}
print(f"   ✓ {len(stellantis_vins)} VINs im Stellantis Bestand\n")

# 4. Hole Genobank-Zinssatz aus Konto 4700057908 (sollzins-Feld)
print("📊 Hole Genobank-Zinssatz aus Bankenspiegel...")
drive_cursor.execute("""
    SELECT sollzins
    FROM konten
    WHERE kontonummer = '4700057908' OR iban LIKE '%4700057908%'
    LIMIT 1
""")
row = drive_cursor.fetchone()
if row and row[0]:
    genobank_zins = float(row[0])
    print(f"   ✓ Zinssatz aus Bankenspiegel: {genobank_zins}%")
else:
    # Fallback: ek_finanzierung_konditionen
    drive_cursor.execute("SELECT zinssatz FROM ek_finanzierung_konditionen WHERE finanzinstitut = 'Genobank'")
    row = drive_cursor.fetchone()
    if row and row[0]:
        genobank_zins = float(row[0])
        print(f"   ✓ Zinssatz aus ek_finanzierung_konditionen: {genobank_zins}%")
    else:
        genobank_zins = 5.5  # Default
        print(f"   ⚠️  Zinssatz nicht gefunden, verwende Default: {genobank_zins}%")
print()

# 5. Import in fahrzeugfinanzierungen
print("💾 Importiere Genobank-Finanzierungen...")

stats = {'importiert': 0, 'fehler': 0}

for fz in genobank_fahrzeuge:
    vin = None
    try:
        vin = fz.get('vin')
        if not vin:
            print(f"   ⚠️  Überspringe: Keine VIN (DV: {fz.get('dealer_vehicle_number')})")
            stats['fehler'] += 1
            continue
        
        modell = fz.get('modell') or 'Unbekannt'
        ek_netto = float(fz.get('ek_netto') or 0)
        ek_rechnung_datum = fz.get('ek_rechnung_datum')
        brief_erstellt_am = fz.get('brief_erstellt_am')
        eingang = fz.get('eingang')
        created_date = fz.get('created_date')
        
        # Zinsbeginn-Logik:
        # 1. Erstelldatum aus Brief-Flag (codes_vehicle_date)
        # 2. Oder: VIN nicht mehr in Stellantis Bestand UND Brief-Flag aktiv
        zins_startdatum = None
        
        if brief_erstellt_am:
            # Option 1: Erstelldatum aus Brief-Flag
            zins_startdatum = brief_erstellt_am
        elif vin not in stellantis_vins:
            # Option 2: VIN nicht mehr in Stellantis Bestand
            # Verwende EK-Rechnung Datum oder Eingangsdatum oder created_date
            zins_startdatum = ek_rechnung_datum or eingang or created_date
        
        # Alter berechnen (Tage seit Zinsbeginn oder seit Eingang)
        if zins_startdatum:
            if isinstance(zins_startdatum, str):
                zins_startdatum = datetime.strptime(zins_startdatum[:10], '%Y-%m-%d').date()
            alter_tage = (date.today() - zins_startdatum).days
        else:
            alter_tage = None
            if eingang:
                if isinstance(eingang, str):
                    eingang = datetime.strptime(eingang[:10], '%Y-%m-%d').date()
                alter_tage = (date.today() - eingang).days
        
        # Aktueller Saldo = EK-Nettowert (noch keine Tilgung)
        aktueller_saldo = ek_netto
        original_betrag = ek_netto
        
        # Marke aus Modell ableiten (verbessert)
        modell_str = str(modell).upper() if modell else ''
        hersteller = 'Unbekannt'
        
        if modell_str:
            # Opel-Modelle
            if any(x in modell_str for x in ['OPEL', 'ASTRA', 'CORSA', 'INSIGNIA', 'CROSSLAND', 'MOKKA', 'GRANDLAND', 'COMBO']):
                hersteller = 'Opel'
            # Hyundai-Modelle
            elif any(x in modell_str for x in ['HYUNDAI', 'KONA', 'TUCSON', 'IONIQ', 'I10', 'I20', 'I30', 'I40', 'BAYON', 'STARIA']):
                hersteller = 'Hyundai'
            # Weitere Marken
            elif any(x in modell_str for x in ['PEUGEOT', 'CITROEN', 'DS']):
                hersteller = 'Stellantis'
            elif any(x in modell_str for x in ['FORD', 'FOCUS', 'FIESTA', 'KUGA']):
                hersteller = 'Ford'
            elif any(x in modell_str for x in ['VW', 'VOLKSWAGEN', 'GOLF', 'POLO', 'PASSAT']):
                hersteller = 'VW'
            elif any(x in modell_str for x in ['BMW', 'X1', 'X3', 'X5', 'SERIE']):
                hersteller = 'BMW'
            elif any(x in modell_str for x in ['MERCEDES', 'BENZ', 'A-KLASSE', 'C-KLASSE', 'E-KLASSE']):
                hersteller = 'Mercedes'
        
        # Falls immer noch Unbekannt, versuche aus VIN zu erkennen (WMI - World Manufacturer Identifier)
        if hersteller == 'Unbekannt' and vin:
            vin_prefix = vin[:3].upper()
            # Opel: W0V, VXK (Opel/Vauxhall)
            if vin_prefix in ['W0V', 'VXK'] or vin.startswith('W0V') or vin.startswith('VXK'):
                hersteller = 'Opel'
            # Hyundai: KMH, KMF, TMA, NLH
            elif vin_prefix in ['KMH', 'KMF', 'TMA', 'NLH']:
                hersteller = 'Hyundai'
        
        # Prüfe ob bereits vorhanden
        drive_cursor.execute("""
            SELECT id FROM fahrzeugfinanzierungen 
            WHERE vin = %s AND finanzinstitut = 'Genobank'
        """, (vin,))
        existing = drive_cursor.fetchone()
        
        if existing:
            # Update
            drive_cursor.execute("""
                UPDATE fahrzeugfinanzierungen SET
                    modell = %s,
                    hersteller = %s,
                    aktueller_saldo = %s,
                    original_betrag = %s,
                    alter_tage = %s,
                    zins_startdatum = %s,
                    aktualisiert_am = NOW()
                WHERE vin = %s AND finanzinstitut = 'Genobank'
            """, (
                modell, hersteller,
                aktueller_saldo, original_betrag,
                alter_tage, zins_startdatum,
                vin
            ))
        else:
            # Insert
            drive_cursor.execute("""
                INSERT INTO fahrzeugfinanzierungen (
                    finanzinstitut, vin, modell, hersteller,
                    aktueller_saldo, original_betrag,
                    alter_tage, zins_startdatum,
                    aktiv, import_datum, aktualisiert_am
                ) VALUES (
                    'Genobank', %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    true, NOW(), NOW()
                )
            """, (
                vin, modell, hersteller,
                aktueller_saldo, original_betrag,
                alter_tage, zins_startdatum
            ))
        
        stats['importiert'] += 1
        if stats['importiert'] <= 3:  # Erste 3 für Debug
            print(f"   ✓ Importiert: VIN {vin}, Modell: {modell}, EK: {ek_netto}€")

    except Exception as e:
        vin_display = vin if vin else fz.get('dealer_vehicle_number', 'Unbekannt')
        print(f"   ⚠️  Fehler bei VIN {vin_display}: {e}")
        # Rollback für diesen Fehler, damit weitere Imports funktionieren
        drive_conn.rollback()
        stats['fehler'] += 1

drive_conn.commit()

print(f"\n✅ Import abgeschlossen:")
print(f"   ✓ {stats['importiert']} Fahrzeuge importiert")
if stats['fehler'] > 0:
    print(f"   ⚠️  {stats['fehler']} Fehler")

drive_conn.close()
print("\n" + "="*80)
print("✅ GENOBANK-IMPORT ERFOLGREICH")
print("="*80 + "\n")
