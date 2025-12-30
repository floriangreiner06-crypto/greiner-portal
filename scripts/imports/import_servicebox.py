#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ServiceBox JSON → DB Import
Importiert gematchte Bestellungen in die Datenbank

TAG83 - Läuft nach Scraper + Matcher
TAG136 - PostgreSQL-kompatibel via db_utils
"""

import os
import sys
import json
from datetime import datetime

# Projekt-Pfad hinzufügen
sys.path.insert(0, '/opt/greiner-portal')
from api.db_utils import db_session, row_to_dict
from api.db_connection import sql_placeholder, get_db_type

BASE_DIR = "/opt/greiner-portal"
MATCHED_JSON = f"{BASE_DIR}/logs/servicebox_matched.json"
LOG_FILE = f"{BASE_DIR}/logs/servicebox_db_import.log"

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def parse_datum(datum_str):
    """Konvertiert '25.11.25, 15:09' zu datetime"""
    if not datum_str:
        return None
    try:
        # Format: DD.MM.YY, HH:MM
        return datetime.strptime(datum_str, "%d.%m.%y, %H:%M")
    except:
        try:
            # Alternatives Format
            return datetime.strptime(datum_str, "%d.%m.%Y, %H:%M")
        except:
            return None

def parse_preis(preis_str):
    """Konvertiert '3,27   EUR' zu float"""
    if not preis_str:
        return None
    try:
        # Entferne EUR, ersetze Komma, strip
        clean = preis_str.replace('EUR', '').replace(',', '.').strip()
        return float(clean)
    except:
        return None

def parse_menge(menge_str):
    """Konvertiert '3,00' zu float"""
    if not menge_str:
        return None
    try:
        return float(menge_str.replace(',', '.'))
    except:
        return None

def main():
    log("\n" + "="*80)
    log("📥 SERVICEBOX JSON → DB IMPORT")
    log("="*80)
    
    # JSON laden
    if not os.path.exists(MATCHED_JSON):
        log(f"❌ Datei nicht gefunden: {MATCHED_JSON}")
        update_sync_status(None, 'error', 0, 0, 'JSON nicht gefunden')
        return False
    
    try:
        with open(MATCHED_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        log(f"❌ JSON-Fehler: {e}")
        update_sync_status(None, 'error', 0, 0, str(e))
        return False
    
    bestellungen = data.get('bestellungen', [])
    log(f"📋 {len(bestellungen)} Bestellungen geladen")

    # DB-Verbindung via db_session
    conn = db_session().__enter__()
    cursor = conn.cursor()
    ph = sql_placeholder()

    stats = {'inserted': 0, 'updated': 0, 'errors': 0, 'matched': 0}
    
    for best in bestellungen:
        try:
            bestellnummer = best.get('bestellnummer')
            if not bestellnummer:
                continue
            
            # Daten extrahieren
            historie = best.get('historie', {})
            absender = best.get('absender', {})
            empfaenger = best.get('empfaenger', {})
            parsed = best.get('parsed', {})
            match = best.get('locosoft_match', {})
            
            bestelldatum = parse_datum(historie.get('bestelldatum'))

            # Prüfen ob Bestellung existiert
            cursor.execute(f"SELECT id FROM stellantis_bestellungen WHERE bestellnummer = {ph}", (bestellnummer,))
            existing = cursor.fetchone()

            # CURRENT_TIMESTAMP funktioniert in beiden DBs
            if existing:
                # UPDATE
                cursor.execute(f"""
                    UPDATE stellantis_bestellungen SET
                        bestelldatum = {ph},
                        absender_code = {ph},
                        absender_name = {ph},
                        empfaenger_code = {ph},
                        lokale_nr = {ph},
                        url = {ph},
                        kommentar_werkstatt = {ph},
                        parsed_kundennummer = {ph},
                        parsed_vin = {ph},
                        parsed_werkstattauftrag = {ph},
                        match_typ = {ph},
                        match_kunde_name = {ph},
                        match_confidence = {ph},
                        import_timestamp = CURRENT_TIMESTAMP
                    WHERE bestellnummer = {ph}
                """, (
                    bestelldatum,
                    absender.get('code'),
                    absender.get('name'),
                    empfaenger.get('code'),
                    parsed.get('lokale_nr') or best.get('lokale_nr'),
                    best.get('url'),
                    parsed.get('kommentar_werkstatt'),
                    parsed.get('kundennummer'),
                    parsed.get('vin'),
                    parsed.get('werkstattauftrag'),
                    match.get('match_typ'),
                    match.get('kunde', {}).get('name') if match.get('kunde') else None,
                    match.get('confidence'),
                    bestellnummer
                ))
                existing_dict = row_to_dict(existing)
                bestellung_id = existing_dict['id']
                stats['updated'] += 1
            else:
                # INSERT
                cursor.execute(f"""
                    INSERT INTO stellantis_bestellungen (
                        bestellnummer, bestelldatum, absender_code, absender_name,
                        empfaenger_code, lokale_nr, url, kommentar_werkstatt,
                        parsed_kundennummer, parsed_vin, parsed_werkstattauftrag,
                        match_typ, match_kunde_name, match_confidence
                    ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                """, (
                    bestellnummer,
                    bestelldatum,
                    absender.get('code'),
                    absender.get('name'),
                    empfaenger.get('code'),
                    parsed.get('lokale_nr') or best.get('lokale_nr'),
                    best.get('url'),
                    parsed.get('kommentar_werkstatt'),
                    parsed.get('kundennummer'),
                    parsed.get('vin'),
                    parsed.get('werkstattauftrag'),
                    match.get('match_typ'),
                    match.get('kunde', {}).get('name') if match.get('kunde') else None,
                    match.get('confidence')
                ))
                bestellung_id = cursor.lastrowid
                stats['inserted'] += 1
            
            # Matching-Statistik
            if match.get('matched'):
                stats['matched'] += 1
            
            # Positionen
            positionen = best.get('positionen', [])
            if positionen and not existing:  # Nur bei neuen Bestellungen Positionen einfügen
                # Alte Positionen löschen (falls Update)
                cursor.execute(f"DELETE FROM stellantis_positionen WHERE bestellung_id = {ph}", (bestellung_id,))

                for pos in positionen:
                    cursor.execute(f"""
                        INSERT INTO stellantis_positionen (
                            bestellung_id, teilenummer, beschreibung,
                            menge, menge_in_lieferung, menge_in_bestellung,
                            preis_ohne_mwst_text, preis_mit_mwst_text, summe_inkl_mwst_text,
                            preis_ohne_mwst, preis_mit_mwst, summe_inkl_mwst
                        ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    """, (
                        bestellung_id,
                        pos.get('teilenummer'),
                        pos.get('beschreibung'),
                        parse_menge(pos.get('menge')),
                        parse_menge(pos.get('menge_in_lieferung')),
                        parse_menge(pos.get('menge_in_bestellung')),
                        pos.get('preis_ohne_mwst'),
                        pos.get('preis_mit_mwst'),
                        pos.get('summe_inkl_mwst'),
                        parse_preis(pos.get('preis_ohne_mwst')),
                        parse_preis(pos.get('preis_mit_mwst')),
                        parse_preis(pos.get('summe_inkl_mwst'))
                    ))
                    
        except Exception as e:
            log(f"⚠️ Fehler bei {bestellnummer}: {e}")
            stats['errors'] += 1
    
    conn.commit()

    # Sync-Status aktualisieren
    cursor.execute(f"""
        UPDATE sync_status SET
            last_run = CURRENT_TIMESTAMP,
            status = 'success',
            records_processed = {ph},
            records_matched = {ph},
            error_message = NULL
        WHERE sync_name = 'servicebox'
    """, (stats['inserted'] + stats['updated'], stats['matched']))
    
    conn.commit()
    conn.close()
    
    log(f"\n✅ IMPORT ABGESCHLOSSEN:")
    log(f"   - Neu: {stats['inserted']}")
    log(f"   - Aktualisiert: {stats['updated']}")
    log(f"   - Gematcht: {stats['matched']}")
    log(f"   - Fehler: {stats['errors']}")
    log("="*80)
    
    return True

def update_sync_status(conn, status, processed, matched, error=None):
    """Aktualisiert sync_status bei Fehler"""
    if conn is None:
        conn = db_session().__enter__()
    cursor = conn.cursor()
    ph = sql_placeholder()
    cursor.execute(f"""
        UPDATE sync_status SET
            last_run = CURRENT_TIMESTAMP,
            status = {ph},
            records_processed = {ph},
            records_matched = {ph},
            error_message = {ph}
        WHERE sync_name = 'servicebox'
    """, (status, processed, matched, error))
    conn.commit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
