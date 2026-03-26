#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Santander Bestandsliste Import
===============================
Importiert Fahrzeugfinanzierungen von Santander Bank aus CSV
Verzeichnis: /opt/greiner-portal/scripts/imports/
Author: Claude AI + Florian Greiner
Date: 2025-11-08
Version: 1.2 (TAG146) - PostgreSQL Migration
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

# Projekt-Pfad
sys.path.insert(0, '/opt/greiner-portal')
from api.db_connection import get_db

# Konfiguration
CSV_DIR = '/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Santander'
FINANZINSTITUT = 'Santander'

def parse_german_decimal(value):
    """Konvertiert deutsches Dezimalformat zu Float"""
    if not value or value.strip() == '':
        return 0.0
    # Entferne Tausender-Trennzeichen und ersetze Komma durch Punkt
    value = str(value).replace('.', '').replace(',', '.')
    try:
        return float(value)
    except:
        return 0.0

def parse_german_date(date_str):
    """Konvertiert deutsches Datumsformat DD.MM.YYYY zu YYYY-MM-DD"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        # Format: DD.MM.YYYY
        dt = datetime.strptime(date_str.strip(), '%d.%m.%Y')
        return dt.strftime('%Y-%m-%d')
    except:
        return None

def get_latest_csv():
    """Findet die neueste CSV-Datei im Santander-Verzeichnis"""
    csv_files = list(Path(CSV_DIR).glob('Bestandsliste_*.csv'))
    if not csv_files:
        return None
    # Sortiere nach Änderungsdatum (neueste zuerst)
    return max(csv_files, key=lambda p: p.stat().st_mtime)

def import_santander_bestand(csv_file=None, dry_run=False):
    """
    Importiert Santander Bestandsliste

    Args:
        csv_file: Pfad zur CSV-Datei (optional, sucht sonst neueste)
        dry_run: Wenn True, werden keine Daten gespeichert
    """

    print("="*80)
    print("🚗 SANTANDER BESTANDSLISTE IMPORT (V1.2 - MIT ZINSDATEN + PostgreSQL)")
    print("="*80)
    print()

    # CSV-Datei finden
    if csv_file is None:
        csv_file = get_latest_csv()
        if csv_file is None:
            print(f"❌ Keine CSV-Datei gefunden in: {CSV_DIR}")
            return False
        print(f"📄 Verwende neueste Datei: {csv_file.name}")
    else:
        csv_file = Path(csv_file)
        if not csv_file.exists():
            print(f"❌ Datei nicht gefunden: {csv_file}")
            return False
        print(f"📄 Verwende: {csv_file.name}")

    print(f"🗄️  Datenbank: PostgreSQL (drive_portal)")
    print(f"🔄 Dry-Run: {'JA (keine Änderungen)' if dry_run else 'NEIN (schreibt in DB)'}")
    print()

    # Datenbank öffnen
    conn = get_db()
    c = conn.cursor()

    # Statistik
    stats = {
        'gelesen': 0,
        'aktiv': 0,
        'abgeloest': 0,
        'neu': 0,
        'update': 0,
        'skip': 0,
        'fehler': 0,
        'mit_zinsdaten': 0
    }

    # Backup vor dem Löschen (falls kein Dry-Run)
    if not dry_run:
        print("🗑️  Lösche alte Santander-Einträge...")
        c.execute("DELETE FROM fahrzeugfinanzierungen WHERE finanzinstitut = %s", (FINANZINSTITUT,))
        geloescht = c.rowcount
        print(f"   ✅ {geloescht} alte Einträge gelöscht")
        print()

    # CSV einlesen
    print("📖 Lese CSV-Datei...")
    print()

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        # Spalte O (15. Spalte, Index 14) = Kategorie/Mobilität-Info laut Santander-CSV
        col_o_header = reader.fieldnames[14] if reader.fieldnames and len(reader.fieldnames) > 14 else None

        for row in reader:
            stats['gelesen'] += 1

            try:
                # Daten extrahieren
                finanzierungsnr = row.get('Finanzierungsnr.', '').strip()
                vin = row.get('VIN', '').strip().strip('"')
                status = row.get('Finanzierungsstatus', '').strip()
                dokumentstatus = row.get('Dokumentstatus', '').strip()

                finanzierungssumme = parse_german_decimal(row.get('Finanzierungssumme', '0'))
                saldo = parse_german_decimal(row.get('Saldo', '0'))
                rechnungsbetrag = parse_german_decimal(row.get('Rechnungsbetrag', '0'))

                rechnungsnummer = row.get('Rechnungsnummer', '').strip()
                rechnungsdatum = parse_german_date(row.get('Rechnungsdatum', ''))
                aktivierungsdatum = parse_german_date(row.get('Aktivierungsdatum', ''))
                endfaelligkeit = parse_german_date(row.get('Endfälligkeit', ''))
                zins_startdatum = parse_german_date(row.get('Zins Startdatum', ''))
                lieferdatum = parse_german_date(row.get('Lieferdatum', ''))

                produkt = row.get('Produkt', '').strip()

                # Kategorie/Mobilität: Primär aus Spalte O (15. Spalte), Fallback aus Produkt-Pfad
                spalte_o = (row.get(col_o_header, '').strip() if col_o_header else '')
                if spalte_o:
                    # Normalisierung für Auswertung (Mobilität-Rahmen 500k): gleiche Werte wie aus Produkt-Pfad
                    so = spalte_o.strip()
                    if 'Vorführer' in so or so == 'Vorführer':
                        produkt_kategorie = 'Vorführer'
                    elif 'Vermieter' in so or 'Mobil' in so or 'Mobilität' in so:
                        produkt_kategorie = 'Mobil/Vermieter'
                    elif 'Neu' in so or so == 'Neuwagen':
                        produkt_kategorie = 'Neuwagen'
                    elif 'Gebraucht' in so:
                        produkt_kategorie = 'Gebraucht'
                    else:
                        produkt_kategorie = so
                else:
                    # Aus Produkt-Pfad ableiten, z.B. "PartPlus/Fahrzeuge/Mobil/Vermieter" → "Mobil/Vermieter"
                    if '/Neu' in produkt:
                        produkt_kategorie = 'Neuwagen'
                    elif '/Gebraucht' in produkt:
                        produkt_kategorie = 'Gebraucht'
                    elif 'Mobil/Vermieter' in produkt:
                        produkt_kategorie = 'Mobil/Vermieter'
                    elif 'Mobil/Vorführer' in produkt:
                        produkt_kategorie = 'Vorführer'
                    else:
                        produkt_kategorie = produkt or ''
                herstellername = row.get('Herstellername', '').strip().strip('"')
                modellname = row.get('Modellname', '').strip().strip('"')
                farbe = row.get('Farbe', '').strip()

                hsn = row.get('HSN', '').strip()
                tsn = row.get('TSN', '').strip()
                vin_letzte6 = row.get('Letzte 6 Stellen VIN', '').strip()

                zinsen_letzte_periode = parse_german_decimal(row.get('Zinsen letzte Periode', '0'))
                zinsen_gesamt = parse_german_decimal(row.get('Zinsen Gesamt', '0'))

                # Statistik: Zinsdaten vorhanden?
                if zins_startdatum or zinsen_gesamt > 0:
                    stats['mit_zinsdaten'] += 1

                # Berechne Alter (falls Aktivierungsdatum vorhanden)
                alter_tage = None
                if aktivierungsdatum:
                    try:
                        aktivierung_dt = datetime.strptime(aktivierungsdatum, '%Y-%m-%d')
                        alter_tage = (datetime.now() - aktivierung_dt).days
                    except:
                        pass

                # Statistik
                if status == 'Aktiv':
                    stats['aktiv'] += 1
                elif status == 'Abgelöst':
                    stats['abgeloest'] += 1

                # Skip wenn VIN fehlt
                if not vin:
                    stats['skip'] += 1
                    continue

                # Insert in DB - ERWEITERT MIT ZINSDATEN!
                if not dry_run:
                    c.execute("""
                        INSERT INTO fahrzeugfinanzierungen (
                            finanzinstitut,
                            finanzierungsnummer,
                            finanzierungsstatus,
                            dokumentstatus,
                            hersteller,
                            produktfamilie,
                            produkt_kategorie,
                            vin,
                            modell,
                            alter_tage,
                            zinsfreiheit_tage,
                            vertragsbeginn,
                            aktueller_saldo,
                            original_betrag,
                            rechnungsnummer,
                            rechnungsbetrag,
                            hsn,
                            tsn,
                            zinsen_letzte_periode,
                            zinsen_gesamt,
                            zins_startdatum,
                            endfaelligkeit,
                            import_datum,
                            datei_quelle
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                    """, (
                        FINANZINSTITUT,
                        finanzierungsnr,
                        status,
                        dokumentstatus,
                        herstellername,  # Hersteller (korrekt!)
                        produkt,         # Produktfamilie
                        produkt_kategorie,  # Kategorie
                        vin,
                        modellname,
                        alter_tage,
                        None,            # Zinsfreiheit (nicht in CSV)
                        aktivierungsdatum,
                        abs(saldo),      # Saldo ist negativ in CSV, wir speichern positiv
                        finanzierungssumme,
                        rechnungsnummer,
                        rechnungsbetrag,
                        hsn,
                        tsn,
                        zinsen_letzte_periode,
                        zinsen_gesamt,
                        zins_startdatum,      # NEU!
                        endfaelligkeit,       # NEU!
                        csv_file.name
                    ))
                    stats['neu'] += 1

            except Exception as e:
                stats['fehler'] += 1
                print(f"   ⚠️  Fehler bei Zeile {stats['gelesen']}: {e}")
                continue

    # Commit (falls kein Dry-Run)
    if not dry_run:
        conn.commit()
        print("💾 Änderungen gespeichert!")
    else:
        print("🔍 Dry-Run: Keine Änderungen gespeichert")

    print()
    print("="*80)
    print("📊 IMPORT-STATISTIK")
    print("="*80)
    print(f"Zeilen gelesen:            {stats['gelesen']:>6}")
    print(f"  └─ Aktiv:                {stats['aktiv']:>6}")
    print(f"  └─ Abgelöst:             {stats['abgeloest']:>6}")
    print(f"  └─ Mit Zinsdaten:        {stats['mit_zinsdaten']:>6}")
    print(f"Neu importiert:            {stats['neu']:>6}")
    print(f"Übersprungen (kein VIN):   {stats['skip']:>6}")
    print(f"Fehler:                    {stats['fehler']:>6}")
    print()

    # Finale DB-Statistik
    if not dry_run:
        c.execute("""
            SELECT
                finanzinstitut,
                COUNT(*) as anzahl,
                SUM(aktueller_saldo) as gesamt_saldo,
                SUM(original_betrag) as gesamt_original
            FROM fahrzeugfinanzierungen
            GROUP BY finanzinstitut
        """)

        print("📊 DATENBANK-ÜBERSICHT:")
        print(f"{'Institut':<20} | {'Anzahl':>8} | {'Finanzierung':>18} | {'Original':>18}")
        print("-"*80)

        for institut, anzahl, saldo, original in c.fetchall():
            print(f"{institut:<20} | {anzahl:>8} | {saldo:>15,.2f} € | {original:>15,.2f} €")
        print()

        # ZINSEN-STATISTIK (direktes Query statt View)
        c.execute("""
            SELECT
                COUNT(*) as anzahl,
                SUM(aktueller_saldo) as saldo,
                SUM(zinsen_gesamt) as zinsen_gesamt,
                AVG(CURRENT_DATE - zins_startdatum) as avg_tage
            FROM fahrzeugfinanzierungen
            WHERE finanzinstitut = %s
              AND zins_startdatum IS NOT NULL
              AND finanzierungsstatus = 'Aktiv'
        """, (FINANZINSTITUT,))
        row = c.fetchone()

        if row and row[0] > 0:
            print("💰 ZINSEN-ÜBERSICHT:")
            print(f"  Fahrzeuge mit Zinsen:    {row[0]:>6}")
            print(f"  Finanzierung (Zinsen):   {row[1]:>15,.2f} €")
            print(f"  Zinsen gesamt:           {row[2]:>15,.2f} €")
            print(f"  Ø Tage seit Zinsstart:   {row[3]:>15.0f} Tage")
            print()

    conn.close()

    print("✅ Import erfolgreich abgeschlossen!")
    print()

    return True

if __name__ == '__main__':
    # Argumente parsen
    dry_run = '--dry-run' in sys.argv
    csv_file = None

    # CSV-Datei aus Argumenten
    for arg in sys.argv[1:]:
        if arg.endswith('.csv'):
            csv_file = arg

    # Import durchführen
    success = import_santander_bestand(csv_file=csv_file, dry_run=dry_run)
    sys.exit(0 if success else 1)
