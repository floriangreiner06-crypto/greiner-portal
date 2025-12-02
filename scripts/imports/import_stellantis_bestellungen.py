#!/usr/bin/env python3
"""
Stellantis Bestellungen Import Script
======================================
Importiert Bestellungen aus servicebox_bestellungen_details_complete.json
in die SQLite-Datenbank.

Usage:
    python3 import_stellantis_bestellungen.py [JSON_FILE]

Autor: TAG 72
Datum: 2025-11-21
"""

import json
import sqlite3
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================================
# KONFIGURATION
# ============================================================================

DB_PATH = "data/greiner_controlling.db"
DEFAULT_JSON_FILE = "logs/servicebox_bestellungen_details_complete.json"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_datum(datum_str: str) -> Optional[datetime]:
    """
    Parst Datum-String im Format "20.11.25, 15:39" zu datetime
    
    Args:
        datum_str: Datum-String aus JSON
        
    Returns:
        datetime object oder None bei Fehler
    """
    if not datum_str:
        return None
    
    try:
        # Format: "20.11.25, 15:39"
        # Annahme: Jahr 20XX (z.B. 25 = 2025)
        parts = datum_str.split(", ")
        if len(parts) != 2:
            print(f"⚠️  Warnung: Unerwartetes Datumsformat: {datum_str}")
            return None
        
        datum_teil = parts[0]  # "20.11.25"
        zeit_teil = parts[1]   # "15:39"
        
        # Zerlege Datum
        tag, monat, jahr_kurz = datum_teil.split(".")
        
        # Jahr: 25 -> 2025
        jahr = f"20{jahr_kurz}"
        
        # Baue datetime
        datum_neu = f"{jahr}-{monat}-{tag} {zeit_teil}:00"
        return datetime.strptime(datum_neu, "%Y-%m-%d %H:%M:%S")
        
    except Exception as e:
        print(f"❌ Fehler beim Parsen von Datum '{datum_str}': {e}")
        return None


def parse_preis(preis_str: str) -> Optional[float]:
    """
    Parst Preis-String im Format "167,82   EUR" zu float
    
    Args:
        preis_str: Preis-String aus JSON
        
    Returns:
        float oder None bei Fehler
    """
    if not preis_str:
        return None
    
    try:
        # Entferne EUR und Whitespace
        preis_clean = preis_str.replace("EUR", "").strip()
        
        # Ersetze Komma durch Punkt
        preis_clean = preis_clean.replace(",", ".")
        
        return float(preis_clean)
        
    except Exception as e:
        print(f"⚠️  Warnung: Kann Preis nicht parsen: '{preis_str}' - {e}")
        return None


def parse_menge(menge_str: str) -> Optional[float]:
    """
    Parst Mengen-String im Format "1,00" zu float
    
    Args:
        menge_str: Mengen-String aus JSON
        
    Returns:
        float oder None bei Fehler
    """
    if not menge_str:
        return None
    
    try:
        # Ersetze Komma durch Punkt
        menge_clean = menge_str.replace(",", ".")
        return float(menge_clean)
        
    except Exception as e:
        print(f"⚠️  Warnung: Kann Menge nicht parsen: '{menge_str}' - {e}")
        return None


# ============================================================================
# DATENBANK FUNCTIONS
# ============================================================================

def init_schema(conn: sqlite3.Connection, schema_file: str = "scripts/migrations/stellantis_schema.sql"):
    """
    Initialisiert das Datenbank-Schema
    
    Args:
        conn: SQLite Connection
        schema_file: Pfad zur Schema-SQL-Datei
    """
    print("📋 Initialisiere Datenbank-Schema...")
    
    # Lese Schema-File
    schema_path = Path(schema_file)
    if not schema_path.exists():
        print(f"⚠️  Schema-File nicht gefunden: {schema_file}")
        print("   Erstelle Basis-Schema...")
        
        # Basis-Schema inline
        schema_sql = """
        CREATE TABLE IF NOT EXISTS stellantis_bestellungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bestellnummer TEXT UNIQUE NOT NULL,
            bestelldatum DATETIME,
            absender_code TEXT,
            absender_name TEXT,
            empfaenger_code TEXT,
            lokale_nr TEXT,
            url TEXT,
            import_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            import_datei TEXT
        );
        
        CREATE TABLE IF NOT EXISTS stellantis_positionen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bestellung_id INTEGER NOT NULL,
            teilenummer TEXT NOT NULL,
            beschreibung TEXT,
            menge REAL,
            menge_in_lieferung REAL,
            menge_in_bestellung REAL,
            preis_ohne_mwst_text TEXT,
            preis_mit_mwst_text TEXT,
            summe_inkl_mwst_text TEXT,
            preis_ohne_mwst REAL,
            preis_mit_mwst REAL,
            summe_inkl_mwst REAL,
            import_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bestellung_id) REFERENCES stellantis_bestellungen(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_stellantis_bestellungen_datum ON stellantis_bestellungen(bestelldatum);
        CREATE INDEX IF NOT EXISTS idx_stellantis_bestellungen_lokale_nr ON stellantis_bestellungen(lokale_nr);
        CREATE INDEX IF NOT EXISTS idx_stellantis_positionen_bestellung ON stellantis_positionen(bestellung_id);
        CREATE INDEX IF NOT EXISTS idx_stellantis_positionen_teilenummer ON stellantis_positionen(teilenummer);
        """
        
        conn.executescript(schema_sql)
    else:
        # Führe Schema-File aus
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        conn.executescript(schema_sql)
    
    conn.commit()
    print("✅ Schema initialisiert!")


def import_bestellung(
    conn: sqlite3.Connection,
    bestellung: Dict,
    import_datei: str
) -> Tuple[bool, Optional[int]]:
    """
    Importiert eine einzelne Bestellung
    
    Args:
        conn: SQLite Connection
        bestellung: Bestellungs-Dict aus JSON
        import_datei: Name der Import-Datei
        
    Returns:
        (success, bestellung_id)
    """
    cursor = conn.cursor()
    
    # Extrahiere Daten
    bestellnummer = bestellung.get('bestellnummer')
    if not bestellnummer:
        print("❌ Bestellung ohne Bestellnummer - überspringe!")
        return False, None
    
    # Duplikat-Check
    cursor.execute(
        "SELECT id FROM stellantis_bestellungen WHERE bestellnummer = ?",
        (bestellnummer,)
    )
    existing = cursor.fetchone()
    if existing:
        # Bereits vorhanden - überspringe
        return False, existing[0]
    
    # Parse Datum
    bestelldatum_str = bestellung.get('historie', {}).get('bestelldatum')
    bestelldatum = parse_datum(bestelldatum_str) if bestelldatum_str else None
    
    # Insert Bestellung
    try:
        cursor.execute("""
            INSERT INTO stellantis_bestellungen (
                bestellnummer,
                bestelldatum,
                absender_code,
                absender_name,
                empfaenger_code,
                lokale_nr,
                url,
                import_datei
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bestellnummer,
            bestelldatum,
            bestellung.get('absender', {}).get('code'),
            bestellung.get('absender', {}).get('name'),
            bestellung.get('empfaenger', {}).get('code'),
            bestellung.get('kommentare', {}).get('lokale_nr'),
            bestellung.get('url'),
            import_datei
        ))
        
        bestellung_id = cursor.lastrowid
        
        # Import Positionen
        positionen = bestellung.get('positionen', [])
        for position in positionen:
            cursor.execute("""
                INSERT INTO stellantis_positionen (
                    bestellung_id,
                    teilenummer,
                    beschreibung,
                    menge,
                    menge_in_lieferung,
                    menge_in_bestellung,
                    preis_ohne_mwst_text,
                    preis_mit_mwst_text,
                    summe_inkl_mwst_text,
                    preis_ohne_mwst,
                    preis_mit_mwst,
                    summe_inkl_mwst
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bestellung_id,
                position.get('teilenummer'),
                position.get('beschreibung'),
                parse_menge(position.get('menge', '')),
                parse_menge(position.get('menge_in_lieferung', '')),
                parse_menge(position.get('menge_in_bestellung', '')),
                position.get('preis_ohne_mwst'),
                position.get('preis_mit_mwst'),
                position.get('summe_inkl_mwst'),
                parse_preis(position.get('preis_ohne_mwst', '')),
                parse_preis(position.get('preis_mit_mwst', '')),
                parse_preis(position.get('summe_inkl_mwst', ''))
            ))
        
        return True, bestellung_id
        
    except sqlite3.IntegrityError as e:
        print(f"⚠️  Integrity Error bei {bestellnummer}: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Fehler beim Import von {bestellnummer}: {e}")
        return False, None


# ============================================================================
# MAIN IMPORT
# ============================================================================

def main():
    """Haupt-Import-Funktion"""
    
    # Parse Arguments
    json_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON_FILE
    
    print("=" * 80)
    print("🚗 STELLANTIS BESTELLUNGEN IMPORT")
    print("=" * 80)
    print(f"JSON-File:    {json_file}")
    print(f"Datenbank:    {DB_PATH}")
    print()
    
    # Prüfe JSON-File
    json_path = Path(json_file)
    if not json_path.exists():
        print(f"❌ JSON-File nicht gefunden: {json_file}")
        sys.exit(1)
    
    # Lade JSON
    print(f"📥 Lade JSON-Datei...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Fehler beim Laden der JSON-Datei: {e}")
        sys.exit(1)
    
    bestellungen = data.get('bestellungen', [])
    print(f"✅ {len(bestellungen)} Bestellungen gefunden")
    print()
    
    # Verbinde zur DB
    print(f"🔌 Verbinde zur Datenbank...")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        print(f"✅ Verbunden!")
        print()
    except Exception as e:
        print(f"❌ Fehler beim Verbinden zur Datenbank: {e}")
        sys.exit(1)
    
    # Initialisiere Schema
    init_schema(conn)
    print()
    
    # Import
    print(f"📦 Starte Import...")
    print()
    
    stats = {
        'importiert': 0,
        'duplikate': 0,
        'fehler': 0,
        'positionen': 0
    }
    
    try:
        for idx, bestellung in enumerate(bestellungen, 1):
            bestellnummer = bestellung.get('bestellnummer', f'Unknown-{idx}')
            
            success, bestellung_id = import_bestellung(
                conn,
                bestellung,
                json_path.name
            )
            
            if success:
                stats['importiert'] += 1
                anzahl_positionen = len(bestellung.get('positionen', []))
                stats['positionen'] += anzahl_positionen
                
                if idx % 10 == 0:
                    print(f"✅ {idx}/{len(bestellungen)} - {bestellnummer} ({anzahl_positionen} Pos.)")
            elif bestellung_id:
                stats['duplikate'] += 1
                if idx % 50 == 0:
                    print(f"⏭️  {idx}/{len(bestellungen)} - Duplikate: {stats['duplikate']}")
            else:
                stats['fehler'] += 1
                print(f"❌ {idx}/{len(bestellungen)} - Fehler bei {bestellnummer}")
        
        # Commit
        conn.commit()
        print()
        print("✅ Alle Transaktionen committed!")
        
    except Exception as e:
        print(f"\n❌ Fehler beim Import: {e}")
        conn.rollback()
        print("🔄 Rollback durchgeführt!")
        sys.exit(1)
    
    finally:
        conn.close()
    
    # Statistik
    print()
    print("=" * 80)
    print("📊 IMPORT-STATISTIK")
    print("=" * 80)
    print(f"Bestellungen importiert:  {stats['importiert']}")
    print(f"Bestellungen duplikate:   {stats['duplikate']}")
    print(f"Bestellungen fehler:      {stats['fehler']}")
    print(f"Positionen importiert:    {stats['positionen']}")
    print(f"Ø Positionen/Bestellung:  {stats['positionen'] / max(stats['importiert'], 1):.1f}")
    print("=" * 80)
    print()
    
    if stats['fehler'] > 0:
        print(f"⚠️  {stats['fehler']} Bestellungen konnten nicht importiert werden!")
    
    if stats['importiert'] > 0:
        print(f"🎉 Import erfolgreich abgeschlossen!")
    else:
        print(f"ℹ️  Keine neuen Bestellungen importiert (alle bereits vorhanden)")


if __name__ == '__main__':
    main()
