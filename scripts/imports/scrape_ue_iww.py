#!/usr/bin/env python3
"""
UE IWW Textbausteine scrapen (ue.iww.de)
========================================
Lädt alle Download-Items von https://www.iww.de/ue/downloads (paginiert),
extrahiert Metadaten (TB-Nummer, Titel, H/K, Beschreibung, URL) und
importiert in unfall_textbausteine (PostgreSQL drive_portal).

Lauf von Projektroot: python scripts/imports/scrape_ue_iww.py

Optionen:
  --no-db       Nur JSON exportieren (data/ue_iww_export.json), kein DB-Import
  --pages N     Max. N Seiten scrapen (Default: alle)
  --dry-run     Nur erste Seite scrapen, JSON ausgeben
  --from-json   Kein Scrape; aus data/ue_iww_export.json laden, DB-Import + Seed
  --seed-only   Nur Mapping unfall_textbausteine_positionen seeden
"""

import os
import sys
import re
import json
import time
import argparse
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Projektroot für Imports (api.db_connection)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

BASE_URL = "https://www.iww.de"
DOWNLOADS_URL = "https://www.iww.de/ue/downloads"
RATE_LIMIT_SEC = 1.5
EXPORT_JSON_PATH = os.path.join(PROJECT_ROOT, "data", "ue_iww_export.json")


def parse_meta_line(h3_text):
    """Extrahiert aus h3-Text: datum, typ, thema, rubrik."""
    parts = [p.strip() for p in (h3_text or "").split("·")]
    datum = parts[0] if len(parts) > 0 else None
    typ = parts[1] if len(parts) > 1 else None
    thema = parts[2] if len(parts) > 2 else None
    rubrik = parts[3] if len(parts) > 3 else None
    # Datum ggf. zu ISO
    if datum and re.match(r"\d{2}\.\d{2}\.\d{4}", datum):
        d = datum.split(".")
        datum = f"{d[2]}-{d[1]}-{d[0]}"
    return {"datum": datum, "typ": typ, "thema": thema, "rubrik": rubrik}


def parse_titel_and_nummer(link_text):
    """
    Extrahiert aus Link-Text wie "657: Abwehr Probefahrtkostenregress (H)" oder "RA072: ..."
    -> tb_nummer, titel, kategorie_hk, ist_anwaltsbaustein
    """
    text = (link_text or "").strip()
    tb_nummer = None
    titel = text
    kategorie_hk = None
    ist_anwaltsbaustein = False
    # (H), (K), (H/K) am Ende
    m = re.search(r"\s*\((H/K|H|K)\)\s*$", text, re.I)
    if m:
        kategorie_hk = m.group(1).upper().replace("/", "/")
        text = text[: m.start()].strip()
    # Nummer am Anfang: "657:" oder "RA072:"
    m = re.match(r"^(RA\d+|\d+):\s*(.+)$", text, re.I)
    if m:
        tb_nummer = m.group(1).upper() if "RA" in m.group(1).upper() else m.group(1)
        titel = m.group(2).strip()
        ist_anwaltsbaustein = (tb_nummer or "").upper().startswith("RA")
    return {"tb_nummer": tb_nummer, "titel": titel, "kategorie_hk": kategorie_hk, "ist_anwaltsbaustein": ist_anwaltsbaustein}


def parse_page(html, page_url):
    """Parst eine Downloads-Seite und gibt Liste von Item-Dicts zurück."""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    # Struktur: h3 (Meta), h2 mit <a> (Titel + Link), p (Beschreibung)
    h3s = soup.find_all("h3")
    for h3 in h3s:
        meta = parse_meta_line(h3.get_text(strip=True))
        # Nächstes h2 mit Link
        h2 = h3.find_next("h2")
        if not h2:
            continue
        a = h2.find("a", href=True)
        if not a:
            continue
        href = a.get("href", "")
        if not href or "/ue/" not in href:
            continue
        full_url = urljoin(BASE_URL, href)
        link_text = a.get_text(strip=True)
        parsed = parse_titel_and_nummer(link_text)
        # Nächstes p als Beschreibung (bis zum nächsten h3)
        p = h2.find_next("p")
        beschreibung = p.get_text(strip=True) if p else None
        if beschreibung:
            beschreibung = re.sub(r"\s*>?\s*weiter\s*$", "", beschreibung, flags=re.I).strip()
        # "weiter"-Link ignorieren, wir haben schon die Haupt-URL
        items.append({
            "tb_nummer": parsed["tb_nummer"],
            "titel": parsed["titel"],
            "beschreibung": beschreibung,
            "kategorie_hk": parsed["kategorie_hk"],
            "datum": meta["datum"],
            "typ": meta["typ"],
            "thema": meta["thema"],
            "rubrik": meta["rubrik"],
            "iww_url": full_url,
            "ist_anwaltsbaustein": parsed["ist_anwaltsbaustein"],
        })
    return items


def fetch_page(session, page_num, sort="a-z"):
    """Lädt eine Seite der Downloads (1-basiert)."""
    url = f"{DOWNLOADS_URL}?p={page_num}&s={sort}&a=alle&t=alle&st=alle"
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Fehler Seite {page_num}: {e}", file=sys.stderr)
        return None


def scrape_all(max_pages=None, dry_run=False):
    """Scrapt alle Seiten und gibt eine Liste aller Items zurück."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; GreinerPortal/1.0; +https://auto-greiner.de)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    })
    all_items = []
    page = 1
    seen_urls = set()
    while True:
        if max_pages and page > max_pages:
            break
        print(f"Seite {page} ...", flush=True)
        html = fetch_page(session, page)
        if not html:
            break
        items = parse_page(html, f"{DOWNLOADS_URL}?p={page}")
        if not items:
            break
        for it in items:
            url = it.get("iww_url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_items.append(it)
        if dry_run:
            print(json.dumps(items[:3], indent=2, ensure_ascii=False))
            return all_items
        page += 1
        time.sleep(RATE_LIMIT_SEC)
    return all_items


def export_json(items):
    """Schreibt items nach data/ue_iww_export.json."""
    os.makedirs(os.path.dirname(EXPORT_JSON_PATH), exist_ok=True)
    with open(EXPORT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Export: {EXPORT_JSON_PATH} ({len(items)} Einträge)")


def _sanitize(s, max_len=None):
    """Entfernt NUL (0x00) und begrenzt Länge – PostgreSQL erlaubt keine NUL in Strings."""
    if s is None:
        return None
    s = (s if isinstance(s, str) else str(s)).replace("\x00", "").strip()
    if max_len is not None and len(s) > max_len:
        s = s[:max_len]
    return s or None


def import_to_db(items):
    """Importiert Items in PostgreSQL unfall_textbausteine (UPSERT auf iww_url)."""
    from api.db_connection import get_db
    conn = get_db()
    cur = conn.cursor()
    try:
        for it in items:
            iww_url = _sanitize(it.get("iww_url")) or None
            if not iww_url:
                continue
            titel = _sanitize(it.get("titel"), 500) or "(ohne Titel)"
            beschreibung = _sanitize(it.get("beschreibung"), 10000) or ""
            cur.execute("""
                INSERT INTO unfall_textbausteine (
                    tb_nummer, titel, beschreibung, kategorie_hk, datum, typ, thema, rubrik, iww_url, ist_anwaltsbaustein
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (iww_url) DO UPDATE SET
                    tb_nummer = EXCLUDED.tb_nummer,
                    titel = EXCLUDED.titel,
                    beschreibung = EXCLUDED.beschreibung,
                    kategorie_hk = EXCLUDED.kategorie_hk,
                    datum = EXCLUDED.datum,
                    typ = EXCLUDED.typ,
                    thema = EXCLUDED.thema,
                    rubrik = EXCLUDED.rubrik,
                    ist_anwaltsbaustein = EXCLUDED.ist_anwaltsbaustein,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                _sanitize(it.get("tb_nummer"), 50),
                titel,
                beschreibung,
                _sanitize(it.get("kategorie_hk"), 10),
                _sanitize(it.get("datum"), 20),
                _sanitize(it.get("typ"), 100),
                _sanitize(it.get("thema"), 200),
                _sanitize(it.get("rubrik"), 200),
                _sanitize(iww_url, 2000),
                bool(it.get("ist_anwaltsbaustein")),
            ))
        conn.commit()
        print(f"DB-Import: {len(items)} Einträge in unfall_textbausteine.")
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def seed_mapping(conn=None):
    """
    Befüllt unfall_textbausteine_positionen mit bekanntem Mapping
    TB-Nummer / titel-Match → checkliste_position_id (1–12).
    """
    from api.db_connection import get_db
    if conn is None:
        conn = get_db()
    cur = conn.cursor()

    # Mapping: (tb_nummer oder Suchbegriff) -> checkliste_position_id (id aus unfall_checkliste_positionen)
    # checkliste_positionen: 1=Verbringung, 2=UPE, 3=Beilackierung, 4=Desinfektion, 5=Stundenverrechnung,
    # 6=Kleinersatzteile, 7=Probefahrt, 8=Reinigung, 9=Entsorgung, 10=Mietwagen, 11=Ofentrocknung, 12=Unfallverhütung
    mapping = [
        (["111", "393", "401", "425", "426"], 1),
        (["046", "154"], 2),
        (["214", "488"], 3),
        (["511", "RA031"], 4),
        (["154", "170", "178", "187", "189", "190", "311", "343"], 5),
        (["238", "316"], 6),
        (["352", "577", "657"], 7),
        (["325", "577"], 8),
        (["418"], 9),
        (["653"], 10),
        (["415"], 11),
        (["568"], None),  # Energiekosten - keine Position 12, evtl. weglassen oder eigener Eintrag
    ]
    # Nur Positionen 1–12 (id in unfall_checkliste_positionen)
    try:
        for tb_list, checkliste_id in mapping:
            if checkliste_id is None:
                continue
            for tb in tb_list:
                cur.execute(
                    "SELECT id FROM unfall_textbausteine WHERE tb_nummer = %s",
                    (tb,)
                )
                row = cur.fetchone()
                if not row:
                    continue
                tb_id = row[0] if hasattr(row, "__getitem__") else row["id"]
                cur.execute("""
                    INSERT INTO unfall_textbausteine_positionen (textbaustein_id, checkliste_position_id, relevanz)
                    VALUES (%s, %s, 'direkt')
                    ON CONFLICT (textbaustein_id, checkliste_position_id) DO NOTHING
                """, (tb_id, checkliste_id))
        conn.commit()
        print("Mapping unfall_textbausteine_positionen geseedet.")
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        if conn:
            conn.close()


def main():
    parser = argparse.ArgumentParser(description="UE IWW Textbausteine scrapen")
    parser.add_argument("--no-db", action="store_true", help="Nur JSON exportieren, kein DB-Import")
    parser.add_argument("--pages", type=int, default=None, help="Max. Anzahl Seiten")
    parser.add_argument("--dry-run", action="store_true", help="Nur erste Seite, JSON-Auszug")
    parser.add_argument("--seed-only", action="store_true", help="Nur Mapping seeden (kein Scrape)")
    parser.add_argument("--from-json", action="store_true", help="Aus data/ue_iww_export.json laden, DB-Import + Seed")
    args = parser.parse_args()

    if args.seed_only:
        seed_mapping()
        return

    if args.from_json:
        if not os.path.isfile(EXPORT_JSON_PATH):
            print(f"Datei nicht gefunden: {EXPORT_JSON_PATH}", file=sys.stderr)
            sys.exit(1)
        with open(EXPORT_JSON_PATH, "r", encoding="utf-8") as f:
            items = json.load(f)
        print(f"Geladen: {EXPORT_JSON_PATH} ({len(items)} Einträge)")
        import_to_db(items)
        seed_mapping()
        return

    max_pages = 1 if args.dry_run else args.pages
    items = scrape_all(max_pages=max_pages, dry_run=args.dry_run)
    if not items:
        print("Keine Items gefunden.", file=sys.stderr)
        sys.exit(1)
    export_json(items)

    if not args.no_db and not args.dry_run:
        import_to_db(items)
        seed_mapping()


if __name__ == "__main__":
    main()
