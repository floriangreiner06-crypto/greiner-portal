#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyundai Finance - CSV Import Script
===================================
Importiert Bestandsliste und Tilgungen aus CSV-Dateien
"""

import os
import sys
import csv
import sqlite3
from datetime import datetime, date
from pathlib import Path

# Pfade
BASE_DIR = Path("/opt/greiner-portal")
DB_PATH = BASE_DIR / "data" / "greiner_controlling.db"
DATA_DIR = BASE_DIR / "data" / "hyundai"

# Hyundai Konditionen
ZINSSATZ = 4.68 / 100  # 4.68% p.a.
FINANZINSTITUT = "Hyundai Finance"


def parse_german_float(value):
    """Konvertiert deutsche Zahlenformate (1.234,56) zu float"""
    if not value or value == '-':
        return 0.0
    value = str(value).replace('"', '').strip()
    value = value.replace('.', '').replace(',', '.')
    try:
        return float(value)
    except ValueError:
        return 0.0


def parse_date(value):
    """Konvertiert Datumsstrings zu date"""
    if not value or value == '-':
        return None
    value = str(value).replace('"', '').strip()
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def import_bestandsliste(conn, csv_path):
    """Importiert Bestandsliste CSV in fahrzeugfinanzierungen"""
    
    print("\n" + "="*60)
    print("📋 BESTANDSLISTE IMPORT")
    print("="*60)
    
    cursor = conn.cursor()
    today = date.today()
    import_datei = os.path.basename(csv_path)
    
    # Statistik
    stats = {'neu': 0, 'aktualisiert': 0, 'fehler': 0}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            try:
                vin = row['VIN'].replace('"', '').strip()
                if not vin:
                    continue
                
                # Daten extrahieren
                saldo = abs(parse_german_float(row.get('Saldo, €', 0)))
                finanz_betrag = parse_german_float(row.get('Finanz.-Betrag, €', 0))
                zinsbeginn = parse_date(row.get('Zinsbeginn'))
                finanz_beginn = parse_date(row.get('Finanzierungsbeginn'))
                finanz_ende = parse_date(row.get('Finanzierungsende'))
                lieferdatum = parse_date(row.get('Lieferdatum'))
                anlagedatum = parse_date(row.get('Anlagedatum'))
                rechnungsdatum = parse_date(row.get('Rechnungsdatum'))
                
                # Produkt aufschlüsseln (z.B. "Hyundai/HNC1/Demo")
                produkt_raw = row.get('Produkt', '').replace('"', '')
                produkt_parts = produkt_raw.split('/')
                produkt_marke = produkt_parts[0] if len(produkt_parts) > 0 else None
                produkt_typ = produkt_parts[1] if len(produkt_parts) > 1 else None
                produkt_kategorie = produkt_parts[2] if len(produkt_parts) > 2 else None
                
                # Zinsfreiheit berechnen
                zinsfreiheit_tage = None
                if zinsbeginn and finanz_beginn:
                    zinsfreiheit_tage = (zinsbeginn - finanz_beginn).days
                
                # Tage seit Zinsbeginn
                tage_seit_zinsbeginn = 0
                if zinsbeginn and zinsbeginn <= today:
                    tage_seit_zinsbeginn = (today - zinsbeginn).days
                
                # Zinsen berechnen
                zinsen_berechnet = 0.0
                if tage_seit_zinsbeginn > 0 and saldo > 0:
                    zinsen_berechnet = round(saldo * ZINSSATZ * tage_seit_zinsbeginn / 365, 2)
                
                # Prüfen ob VIN bereits existiert
                cursor.execute(
                    "SELECT id FROM fahrzeugfinanzierungen WHERE vin = ? AND finanzinstitut = ?",
                    (vin, FINANZINSTITUT)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # UPDATE
                    cursor.execute("""
                        UPDATE fahrzeugfinanzierungen SET
                            modell = ?,
                            farbe = ?,
                            finanzierungsstatus = ?,
                            dokumentstatus = ?,
                            produkt = ?,
                            produkt_marke = ?,
                            produkt_typ = ?,
                            produkt_kategorie = ?,
                            finanzierungsbetrag = ?,
                            aktueller_saldo = ?,
                            zinsbeginn = ?,
                            vertragsbeginn = ?,
                            finanzierungsende = ?,
                            lieferdatum = ?,
                            anlagedatum = ?,
                            rechnungsnummer = ?,
                            rechnungsdatum = ?,
                            finanzierungsnummer = ?,
                            einreicher_id = ?,
                            zinsfreiheit_tage = ?,
                            tage_seit_zinsbeginn = ?,
                            zinsen_berechnet = ?,
                            import_datei = ?,
                            import_datum = ?,
                            aktualisiert_am = ?
                        WHERE id = ?
                    """, (
                        row.get('Modell', '').replace('"', ''),
                        row.get('Farbe', '').replace('"', ''),
                        row.get('Finanzierungsstatus', '').replace('"', ''),
                        row.get('Dokumentenstatus', '').replace('"', ''),
                        produkt_raw,
                        produkt_marke,
                        produkt_typ,
                        produkt_kategorie,
                        finanz_betrag,
                        saldo,
                        zinsbeginn,
                        finanz_beginn,
                        finanz_ende,
                        lieferdatum,
                        anlagedatum,
                        row.get('Rechnungsnr.', '').replace('"', ''),
                        rechnungsdatum,
                        row.get('Finanzierungsnr', '').replace('"', ''),
                        row.get('Einreicher', '').replace('"', ''),
                        zinsfreiheit_tage,
                        tage_seit_zinsbeginn,
                        zinsen_berechnet,
                        import_datei,
                        datetime.now(),
                        datetime.now(),
                        existing[0]
                    ))
                    stats['aktualisiert'] += 1
                else:
                    # INSERT
                    cursor.execute("""
                        INSERT INTO fahrzeugfinanzierungen (
                            vin, vin_kurz, modell, farbe, finanzierungsstatus, dokumentstatus,
                            produkt, produkt_marke, produkt_typ, produkt_kategorie,
                            finanzierungsbetrag, aktueller_saldo, waehrung,
                            zinsbeginn, vertragsbeginn, finanzierungsende,
                            lieferdatum, anlagedatum, rechnungsnummer, rechnungsdatum,
                            finanzierungsnummer, einreicher_id, hersteller,
                            zinsfreiheit_tage, tage_seit_zinsbeginn, zinsen_berechnet,
                            finanzinstitut, import_datei, import_datum, aktiv
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        vin,
                        vin[-8:],
                        row.get('Modell', '').replace('"', ''),
                        row.get('Farbe', '').replace('"', ''),
                        row.get('Finanzierungsstatus', '').replace('"', ''),
                        row.get('Dokumentenstatus', '').replace('"', ''),
                        produkt_raw,
                        produkt_marke,
                        produkt_typ,
                        produkt_kategorie,
                        finanz_betrag,
                        saldo,
                        'EUR',
                        zinsbeginn,
                        finanz_beginn,
                        finanz_ende,
                        lieferdatum,
                        anlagedatum,
                        row.get('Rechnungsnr.', '').replace('"', ''),
                        rechnungsdatum,
                        row.get('Finanzierungsnr', '').replace('"', ''),
                        row.get('Einreicher', '').replace('"', ''),
                        row.get('Hersteller', '').replace('"', ''),
                        zinsfreiheit_tage,
                        tage_seit_zinsbeginn,
                        zinsen_berechnet,
                        FINANZINSTITUT,
                        import_datei,
                        datetime.now(),
                        1
                    ))
                    stats['neu'] += 1
                    
            except Exception as e:
                print(f"   ❌ Fehler bei VIN {row.get('VIN', '?')}: {e}")
                stats['fehler'] += 1
    
    conn.commit()
    
    print(f"\n📊 Ergebnis:")
    print(f"   ✅ Neu: {stats['neu']}")
    print(f"   🔄 Aktualisiert: {stats['aktualisiert']}")
    print(f"   ❌ Fehler: {stats['fehler']}")
    
    return stats


def import_tilgungen(conn, csv_path):
    """Importiert Tilgungen CSV in tilgungen Tabelle"""
    
    print("\n" + "="*60)
    print("💶 TILGUNGEN IMPORT")
    print("="*60)
    
    cursor = conn.cursor()
    import_datei = os.path.basename(csv_path)
    
    # Alte Hyundai-Tilgungen löschen (werden komplett neu importiert)
    cursor.execute("DELETE FROM tilgungen WHERE finanzinstitut = ?", (FINANZINSTITUT,))
    deleted = cursor.rowcount
    print(f"   🗑️ {deleted} alte Tilgungen gelöscht")
    
    stats = {'importiert': 0, 'fehler': 0}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            try:
                vin = row.get('Fahrgestellnr.', '').replace('"', '').strip()
                if not vin:
                    continue
                
                faellig_am = parse_date(row.get('Fällig am'))
                betrag = parse_german_float(row.get('Betrag, €', 0))
                
                # Fahrzeugfinanzierung-ID finden
                cursor.execute(
                    "SELECT id FROM fahrzeugfinanzierungen WHERE vin = ? AND finanzinstitut = ?",
                    (vin, FINANZINSTITUT)
                )
                fz_result = cursor.fetchone()
                fz_id = fz_result[0] if fz_result else None
                
                cursor.execute("""
                    INSERT INTO tilgungen (
                        fahrzeugfinanzierung_id, vin, finanzierungsnummer,
                        faellig_am, betrag, beschreibung, status,
                        lastschrift_referenz, oem_rechnungsnr,
                        finanzinstitut, import_datei
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fz_id,
                    vin,
                    row.get('Finanzierungsnr.', '').replace('"', ''),
                    faellig_am,
                    betrag,
                    row.get('Beschreibung', 'Tilgung').replace('"', ''),
                    row.get('Status', '').replace('"', '').strip(),
                    row.get('Lastschrift Referenz', '').replace('"', ''),
                    row.get('OEM Rechnungsnr.', '').replace('"', ''),
                    FINANZINSTITUT,
                    import_datei
                ))
                stats['importiert'] += 1
                
            except Exception as e:
                print(f"   ❌ Fehler: {e}")
                stats['fehler'] += 1
    
    conn.commit()
    
    print(f"\n📊 Ergebnis:")
    print(f"   ✅ Importiert: {stats['importiert']}")
    print(f"   ❌ Fehler: {stats['fehler']}")
    
    return stats


def print_summary(conn):
    """Zeigt Zusammenfassung nach Import"""
    
    print("\n" + "="*60)
    print("📊 ZUSAMMENFASSUNG")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Fahrzeuge
    cursor.execute("""
        SELECT COUNT(*), ROUND(SUM(aktueller_saldo), 2), ROUND(SUM(zinsen_berechnet), 2)
        FROM fahrzeugfinanzierungen 
        WHERE finanzinstitut = ? AND aktiv = 1
    """, (FINANZINSTITUT,))
    fz = cursor.fetchone()
    print(f"\n🚗 Fahrzeuge: {fz[0]}")
    print(f"   Gesamt-Saldo: {fz[1]:,.2f} €")
    print(f"   Berechnete Zinsen: {fz[2]:,.2f} €")
    
    # Tilgungen
    cursor.execute("""
        SELECT status, COUNT(*), ROUND(SUM(betrag), 2)
        FROM tilgungen
        WHERE finanzinstitut = ?
        GROUP BY status
    """, (FINANZINSTITUT,))
    print(f"\n💶 Tilgungen:")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]} Stück = {row[2]:,.2f} €")
    
    # Nächste 7 Tage
    cursor.execute("""
        SELECT faellig_am, vin, betrag, status
        FROM tilgungen
        WHERE finanzinstitut = ? 
          AND faellig_am BETWEEN date('now') AND date('now', '+7 days')
        ORDER BY faellig_am
    """, (FINANZINSTITUT,))
    tilgungen_7d = cursor.fetchall()
    if tilgungen_7d:
        print(f"\n⚡ Nächste 7 Tage:")
        for t in tilgungen_7d:
            print(f"   {t[0]} | ...{t[1][-8:]} | {t[2]:>10,.2f} € | {t[3]}")
    
    # Top 5 Zinskosten
    cursor.execute("""
        SELECT vin, modell, tage_seit_zinsbeginn, aktueller_saldo, zinsen_berechnet
        FROM fahrzeugfinanzierungen
        WHERE finanzinstitut = ? AND aktiv = 1 AND zinsen_berechnet > 0
        ORDER BY zinsen_berechnet DESC
        LIMIT 5
    """, (FINANZINSTITUT,))
    top5 = cursor.fetchall()
    if top5:
        print(f"\n🔥 Top 5 Zinskosten:")
        for t in top5:
            print(f"   ...{t[0][-8:]} | {t[2]:>3} Tage | {t[4]:>8,.2f} € Zinsen")


def main():
    print("\n" + "="*60)
    print("🚗 HYUNDAI FINANCE - DATEN-IMPORT")
    print("="*60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # CSV-Dateien finden
    bestandsliste = DATA_DIR / "hyundai_bestandsliste_latest.csv"
    tilgungen = DATA_DIR / "hyundai_tilgungen_latest.csv"
    
    if not bestandsliste.exists():
        print(f"❌ Bestandsliste nicht gefunden: {bestandsliste}")
        sys.exit(1)
    
    if not tilgungen.exists():
        print(f"❌ Tilgungen nicht gefunden: {tilgungen}")
        sys.exit(1)
    
    print(f"\n📁 Bestandsliste: {bestandsliste}")
    print(f"📁 Tilgungen: {tilgungen}")
    
    # Datenbank verbinden
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Imports
        import_bestandsliste(conn, bestandsliste)
        import_tilgungen(conn, tilgungen)
        
        # Zusammenfassung
        print_summary(conn)
        
    finally:
        conn.close()
    
    print("\n" + "="*60)
    print("✅ IMPORT ABGESCHLOSSEN")
    print("="*60)


if __name__ == "__main__":
    main()
