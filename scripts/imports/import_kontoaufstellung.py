#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import-Script für Kontenaufstellung.xlsx (NUR FÜR MANUELLE KONTROLLE)
=====================================================================
TAG 180: Importiert Kontoinformationen und historische Snapshots

⚠️  WICHTIG: Dieses Script ist NUR für manuelle Kontrolle gedacht!
Die Daten kommen normalerweise automatisch aus:
- MT940 Import (3x täglich)
- Hypovereinsbank PDF Import (täglich)

Dieses Script sollte nur verwendet werden, wenn:
- Manuelle Kontrolle der Excel-Datei aus der Buchhaltung
- Historische Daten nachträglich importieren
- Kreditlinien-Informationen manuell aktualisieren

Features:
- Aktualisiert Kontoinformationen (kreditlinie, kontotyp, kontoinhaber)
- Erstellt historische Snapshots in konto_snapshots
- Normalisiert IBANs (Leerzeichen entfernen)
- Matching via IBAN

Verwendung:
    python scripts/imports/import_kontoaufstellung.py /mnt/greiner-portal-sync/docs/Kontoaufstellung.xlsx
    python scripts/imports/import_kontoaufstellung.py /mnt/greiner-portal-sync/docs/Kontoaufstellung.xlsx --stichtag 2025-11-11
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, date
import re

# Projekt-Pfad hinzufügen
sys.path.insert(0, '/opt/greiner-portal')

import pandas as pd
from api.db_utils import db_session, row_to_dict
from api.db_connection import sql_placeholder, get_db_type

class KontoaufstellungImporter:
    def __init__(self):
        self.stats = {
            'konten_gefunden': 0,
            'konten_aktualisiert': 0,
            'konten_nicht_gefunden': 0,
            'snapshots_erstellt': 0,
            'snapshots_ueberschrieben': 0,
            'fehler': 0
        }
        self.ph = sql_placeholder()

    def normalize_iban(self, iban):
        """IBAN normalisieren: Leerzeichen entfernen, Großbuchstaben"""
        if not iban or pd.isna(iban):
            return None
        # Leerzeichen entfernen
        iban_clean = re.sub(r'\s+', '', str(iban).strip().upper())
        return iban_clean if len(iban_clean) >= 15 else None

    def find_konto_by_iban(self, cursor, iban):
        """Konto in DB finden via IBAN"""
        if not iban:
            return None
        
        # Direkter Match
        cursor.execute(f"SELECT id FROM konten WHERE REPLACE(UPPER(iban), ' ', '') = {self.ph}", (iban,))
        result = cursor.fetchone()
        if result:
            return row_to_dict(result)['id']
        
        # Fallback: Teilstring-Match (letzte 10 Zeichen)
        if len(iban) >= 10:
            iban_suffix = iban[-10:]
            cursor.execute(f"SELECT id FROM konten WHERE REPLACE(UPPER(iban), ' ', '') LIKE {self.ph}", (f'%{iban_suffix}',))
            result = cursor.fetchone()
            if result:
                return row_to_dict(result)['id']
        
        return None

    def parse_stichtag(self, saldo_column_name, default_year=None):
        """Stichtag aus Spaltennamen extrahieren (z.B. 'Saldo per 11.11.' -> 2025-11-11)"""
        # Versuche Datum aus Spaltennamen zu extrahieren
        match = re.search(r'(\d{1,2})\.(\d{1,2})\.?', saldo_column_name)
        if match:
            tag = int(match.group(1))
            monat = int(match.group(2))
            jahr = default_year or datetime.now().year
            try:
                return date(jahr, monat, tag)
            except ValueError:
                pass
        
        # Fallback: Heute
        return date.today()

    def update_konto_info(self, cursor, konto_id, row_data):
        """Kontoinformationen aktualisieren"""
        updates = []
        params = []
        
        # Kreditlinie
        if pd.notna(row_data.get('Limit')):
            limit = float(row_data['Limit'])
            if limit > 0:
                updates.append(f"kreditlinie = {self.ph}")
                params.append(limit)
        
        # Kontotyp
        if pd.notna(row_data.get('Art')):
            kontotyp = str(row_data['Art']).strip()
            if kontotyp:
                updates.append(f"kontotyp = {self.ph}")
                params.append(kontotyp)
        
        # Kontoinhaber
        if pd.notna(row_data.get('Konto Inhaber')):
            inhaber = str(row_data['Konto Inhaber']).strip()
            if inhaber and inhaber != '-':
                updates.append(f"kontoinhaber = {self.ph}")
                params.append(inhaber)
        
        # BIC
        if pd.notna(row_data.get('BIC')):
            bic = str(row_data['BIC']).strip()
            if bic:
                updates.append(f"bic = {self.ph}")
                params.append(bic)
        
        if updates:
            params.append(konto_id)
            query = f"UPDATE konten SET {', '.join(updates)} WHERE id = {self.ph}"
            cursor.execute(query, params)
            return True
        
        return False

    def create_snapshot(self, cursor, konto_id, stichtag, saldo, kreditlinie=None):
        """Snapshot in konto_snapshots erstellen oder aktualisieren"""
        # Prüfe ob Snapshot für diesen Stichtag bereits existiert
        cursor.execute(f"""
            SELECT id FROM konto_snapshots 
            WHERE konto_id = {self.ph} AND stichtag = {self.ph}
        """, (konto_id, stichtag))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update
            snapshot_id = row_to_dict(existing)['id']
            cursor.execute(f"""
                UPDATE konto_snapshots 
                SET kapitalsaldo = {self.ph},
                    kreditlinie = {self.ph}
                WHERE id = {self.ph}
            """, (saldo, kreditlinie, snapshot_id))
            self.stats['snapshots_ueberschrieben'] += 1
        else:
            # Insert
            cursor.execute(f"""
                INSERT INTO konto_snapshots 
                (konto_id, stichtag, kapitalsaldo, kreditlinie)
                VALUES ({self.ph}, {self.ph}, {self.ph}, {self.ph})
            """, (konto_id, stichtag, saldo, kreditlinie))
            self.stats['snapshots_erstellt'] += 1

    def import_excel(self, excel_path, stichtag=None):
        """Excel-Datei importieren"""
        print(f"📊 Lade Excel-Datei: {excel_path}")
        
        try:
            df = pd.read_excel(excel_path, sheet_name='Tabelle1')
        except Exception as e:
            print(f"❌ Fehler beim Lesen der Excel-Datei: {e}")
            return False
        
        if df.empty:
            print("⚠️  Excel-Datei ist leer")
            return False
        
        print(f"✓ {len(df)} Zeilen gefunden")
        
        # Stichtag bestimmen
        saldo_column = None
        for col in df.columns:
            if 'saldo' in col.lower() or 'per' in col.lower():
                saldo_column = col
                break
        
        if not saldo_column:
            print("❌ Keine Saldo-Spalte gefunden")
            return False
        
        if not stichtag:
            stichtag = self.parse_stichtag(saldo_column)
        
        print(f"📅 Stichtag: {stichtag}")
        print()
        
        # Import durchführen
        with db_session() as conn:
            cursor = conn.cursor()
            
            for idx, row in df.iterrows():
                try:
                    # IBAN normalisieren
                    iban_raw = row.get('IBAN', '')
                    iban = self.normalize_iban(iban_raw)
                    
                    if not iban:
                        print(f"⚠️  Zeile {idx+1}: Keine IBAN gefunden, überspringe")
                        continue
                    
                    # Konto finden
                    konto_id = self.find_konto_by_iban(cursor, iban)
                    
                    if not konto_id:
                        print(f"⚠️  Zeile {idx+1}: Konto nicht gefunden (IBAN: {iban[:10]}...)")
                        self.stats['konten_nicht_gefunden'] += 1
                        continue
                    
                    self.stats['konten_gefunden'] += 1
                    
                    # Kontoinformationen aktualisieren
                    if self.update_konto_info(cursor, konto_id, row):
                        self.stats['konten_aktualisiert'] += 1
                    
                    # Saldo auslesen
                    saldo = row.get(saldo_column)
                    if pd.isna(saldo):
                        saldo = 0
                    else:
                        saldo = float(saldo)
                    
                    # Kreditlinie auslesen
                    kreditlinie = row.get('Limit')
                    if pd.isna(kreditlinie):
                        kreditlinie = None
                    else:
                        kreditlinie = float(kreditlinie) if float(kreditlinie) > 0 else None
                    
                    # Snapshot erstellen
                    self.create_snapshot(cursor, konto_id, stichtag, saldo, kreditlinie)
                    
                    print(f"✓ Zeile {idx+1}: Konto {konto_id} aktualisiert (IBAN: {iban[:10]}...)")
                    
                except Exception as e:
                    print(f"❌ Fehler in Zeile {idx+1}: {e}")
                    self.stats['fehler'] += 1
                    continue
            
            conn.commit()
            print()
            print("✅ Import abgeschlossen!")
            print()
            self.print_stats()
            return True

    def print_stats(self):
        """Statistik ausgeben"""
        print("="*80)
        print("📊 STATISTIK")
        print("="*80)
        print(f"  Konten gefunden:        {self.stats['konten_gefunden']}")
        print(f"  Konten aktualisiert:    {self.stats['konten_aktualisiert']}")
        print(f"  Konten nicht gefunden:  {self.stats['konten_nicht_gefunden']}")
        print(f"  Snapshots erstellt:     {self.stats['snapshots_erstellt']}")
        print(f"  Snapshots überschrieben: {self.stats['snapshots_ueberschrieben']}")
        print(f"  Fehler:                 {self.stats['fehler']}")
        print("="*80)


def main():
    parser = argparse.ArgumentParser(description='Import Kontenaufstellung.xlsx')
    parser.add_argument('excel_path', help='Pfad zur Excel-Datei')
    parser.add_argument('--stichtag', help='Stichtag (YYYY-MM-DD), optional')
    
    args = parser.parse_args()
    
    excel_path = Path(args.excel_path)
    if not excel_path.exists():
        print(f"❌ Datei nicht gefunden: {excel_path}")
        sys.exit(1)
    
    stichtag = None
    if args.stichtag:
        try:
            stichtag = datetime.strptime(args.stichtag, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ Ungültiges Datum: {args.stichtag} (Format: YYYY-MM-DD)")
            sys.exit(1)
    
    print("="*80)
    print("📥 KONTOAUFSTELLUNG IMPORT")
    print("="*80)
    print()
    
    importer = KontoaufstellungImporter()
    success = importer.import_excel(excel_path, stichtag)
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
