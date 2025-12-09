#!/usr/bin/env python3
"""
Parser für Stellantis Teile-Lieferscheine (XQ0093 Format)
Liest Fixed-Width Dateien und importiert in SQLite
"""

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

# Konfiguration
LIEFERSCHEIN_DIR = "/mnt/loco-teilelieferscheine"
SQLITE_DB = "/opt/greiner-portal/data/greiner_controlling.db"

def parse_lieferschein_zeile(line):
    """
    Parsed eine Zeile aus dem XQ0093 Lieferschein-Format
    
    Beispiel:
    1DEOVDEZ185    DEZ185102 891673    6050 20251126        1JAR67UFH 590981    20251126ZVOR55486055          RÜCKLAUFLEIT...
    """
    if len(line) < 200:
        return None
    
    try:
        # Record-Type muss 1 sein
        if line[0] != '1':
            return None
        
        # Standort extrahieren (Position 5-11)
        standort_raw = line[4:15].strip()
        # DEZ185 oder DE08250 extrahieren
        standort_match = re.search(r'(DEZ?\d+|DE\d+)', standort_raw)
        standort = standort_match.group(1) if standort_match else standort_raw[:6]
        
        # Lieferschein-Nummer (number_main) - ca. Position 25-35
        # Suche nach 6-10 stelliger Zahl nach dem Standort-Block
        rest = line[15:80]
        ls_match = re.search(r'(\d{6,10})', rest)
        lieferschein_nr = ls_match.group(1).strip() if ls_match else ''
        
        # Zeile (4-stellig, z.B. 6050)
        zeile_match = re.search(r'\s(\d{4})\s+\d{8}', line[25:60])
        zeile = int(zeile_match.group(1)) if zeile_match else 0
        
        # ServiceBox Bestellnummer (1J + 7 Zeichen)
        bestell_match = re.search(r'(1J[A-Z0-9]{7})', line)
        servicebox_bestellnr = bestell_match.group(1) if bestell_match else ''
        
        # Lieferanten-Note (6-10 stellige Zahl nach Bestellnr)
        if servicebox_bestellnr:
            pos = line.find(servicebox_bestellnr) + len(servicebox_bestellnr)
            lief_rest = line[pos:pos+20]
            lief_match = re.search(r'(\d{6,10})', lief_rest)
            lieferanten_note = lief_match.group(1) if lief_match else ''
        else:
            lieferanten_note = ''
        
        # Datum (YYYYMMDD)
        datum_match = re.search(r'(202[0-9]{5})', line)
        lieferdatum = datum_match.group(1) if datum_match else ''
        if lieferdatum:
            lieferdatum = f"{lieferdatum[:4]}-{lieferdatum[4:6]}-{lieferdatum[6:8]}"
        
        # Teilenummer (7-10 stellig, nach ZVOR/ZSTO etc.)
        # Suche nach Pattern wie "ZVOR55486055" oder "ZSTO42506900"
        teil_match = re.search(r'Z[A-Z]{3}(\d{7,10})', line)
        if teil_match:
            teilenummer = teil_match.group(1)
        else:
            # Alternative: Suche nach längerer Teilenummer
            teil_match2 = re.search(r'(\d{8,10})\s+[A-Z]', line[80:150])
            teilenummer = teil_match2.group(1) if teil_match2 else ''
        
        # Beschreibung (nach Teilenummer, vor den Nullen)
        if teilenummer:
            desc_start = line.find(teilenummer) + len(teilenummer)
            desc_raw = line[desc_start:desc_start+30]
            # Bereinigen
            beschreibung = re.sub(r'^[^A-Za-z]*', '', desc_raw)
            beschreibung = re.sub(r'\d{5,}.*', '', beschreibung).strip()
            beschreibung = beschreibung[:50]  # Max 50 Zeichen
        else:
            beschreibung = ''
        
        # Preise (in Cent, am Ende der Zeile)
        # Format: ...000000000000712400000048440000000920M EUR
        preis_match = re.search(r'(\d{12})(\d{8})(\d{8})', line[200:])
        if preis_match:
            preis_ek_cent = int(preis_match.group(1)[-8:])  # letzte 8 Stellen
            preis_vk_cent = int(preis_match.group(2))
        else:
            preis_ek_cent = 0
            preis_vk_cent = 0
        
        # Empfänger (DE + 5 Zeichen, am Ende)
        empf_match = re.search(r'(DE\d{2}[A-Z0-9]{2}\d?)', line[-100:])
        empfaenger = empf_match.group(1) if empf_match else ''
        
        return {
            'standort': standort,
            'lieferschein_nr': lieferschein_nr,
            'zeile': zeile,
            'lieferdatum': lieferdatum,
            'servicebox_bestellnr': servicebox_bestellnr,
            'lieferanten_note': lieferanten_note,
            'teilenummer': teilenummer,
            'beschreibung': beschreibung,
            'preis_ek_cent': preis_ek_cent,
            'preis_vk_cent': preis_vk_cent,
            'empfaenger': empfaenger
        }
        
    except Exception as e:
        print(f"  ⚠️ Parse-Fehler: {e}")
        return None


def import_lieferschein_datei(filepath):
    """Importiert eine einzelne Lieferschein-Datei"""
    datei_name = os.path.basename(filepath)
    positionen = []
    
    with open(filepath, 'r', encoding='latin-1', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parsed = parse_lieferschein_zeile(line)
            if parsed and parsed['teilenummer']:
                parsed['datei_name'] = datei_name
                positionen.append(parsed)
    
    return positionen


def save_to_sqlite(positionen):
    """Speichert Positionen in SQLite"""
    conn = sqlite3.connect(SQLITE_DB)
    cur = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for pos in positionen:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO teile_lieferscheine 
                (datei_name, standort, lieferschein_nr, zeile, lieferdatum,
                 servicebox_bestellnr, lieferanten_note, teilenummer, beschreibung,
                 preis_ek_cent, preis_vk_cent, empfaenger)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pos['datei_name'],
                pos['standort'],
                pos['lieferschein_nr'],
                pos['zeile'],
                pos['lieferdatum'],
                pos['servicebox_bestellnr'],
                pos['lieferanten_note'],
                pos['teilenummer'],
                pos['beschreibung'],
                pos['preis_ek_cent'],
                pos['preis_vk_cent'],
                pos['empfaenger']
            ))
            
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
                
        except Exception as e:
            print(f"  ❌ DB-Fehler: {e}")
            skipped += 1
    
    conn.commit()
    conn.close()
    
    return inserted, skipped


def main():
    print("=" * 70)
    print("TEILE-LIEFERSCHEIN IMPORT")
    print(f"Verzeichnis: {LIEFERSCHEIN_DIR}")
    print("=" * 70)
    
    # Alle Dateien sammeln
    files = sorted(Path(LIEFERSCHEIN_DIR).glob("XQ0093*"))
    print(f"\n📁 {len(files)} Dateien gefunden")
    
    # Nur neue Dateien (letzte 7 Tage)
    cutoff = datetime.now().timestamp() - (7 * 24 * 60 * 60)
    recent_files = [f for f in files if f.stat().st_mtime > cutoff]
    print(f"📅 {len(recent_files)} Dateien der letzten 7 Tage")
    
    total_positionen = 0
    total_inserted = 0
    total_skipped = 0
    
    for filepath in recent_files:
        positionen = import_lieferschein_datei(filepath)
        if positionen:
            inserted, skipped = save_to_sqlite(positionen)
            total_positionen += len(positionen)
            total_inserted += inserted
            total_skipped += skipped
            print(f"  ✓ {filepath.name}: {len(positionen)} Pos, {inserted} neu, {skipped} übersprungen")
    
    print("\n" + "=" * 70)
    print(f"ERGEBNIS:")
    print(f"  Positionen gesamt: {total_positionen}")
    print(f"  Neu eingefügt:     {total_inserted}")
    print(f"  Übersprungen:      {total_skipped}")
    print("=" * 70)


if __name__ == "__main__":
    main()
