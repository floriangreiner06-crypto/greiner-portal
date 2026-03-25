#!/usr/bin/env python3
"""
Test: Verkaufsprogramm-PDFs (Rundschreiben) mit pdfplumber lesen und per LM Studio
ein strukturiertes "Regelwerk" (Programm, Gültigkeit, Konditionen, Boni) extrahieren.

Verwendung:
  python scripts/verkauf/vfw_rundschreiben_regelwerk_ki.py [--dir PFAD] [--max-chars N] [--output DATEI]
  python scripts/verkauf/vfw_rundschreiben_regelwerk_ki.py --full [--output DATEI]   # gesamte PDF(s)
  python scripts/verkauf/vfw_rundschreiben_regelwerk_ki.py --chunk-size 12000        # lange PDFs in Blöcken

Längen/Timeout: LM Studio hat ein Input-Limit (~6–8k Zeichen sicher). Empfohlen: ein PDF pro Lauf, --chunk-size 6000 --timeout 300.
Bei 400/Timeout: automatischer Retry mit halbiertem Chunk (bis min. 2000 Zeichen).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Chunk/Retry: LM Studio verträgt ~6k Zeichen; bei 400/Timeout Retry mit Halbierung
MIN_CHUNK_RETRY = 2000
DEFAULT_CHUNK_SIZE = 6000
DEFAULT_CHUNK_TIMEOUT = 300

# Projekt-Root
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Maximale Zeichen pro PDF für KI (LM Studio Token-Limit)
DEFAULT_MAX_CHARS = 18000
# Sync-Pfad falls vorhanden
KALK_DIR_SYNC = Path("/mnt/greiner-portal-sync/docs/workstreams/verkauf/Kalkulationstool")
KALK_DIR_REPO = ROOT / "docs/workstreams/verkauf/Kalkulationstool"

REGELWERK_PROMPT = """Du bist ein Assistent, der aus Hersteller-Rundschreiben (Verkaufsprogramme für Vorführwagen/Tageszulassungen) ein strukturiertes Regelwerk extrahiert.

WICHTIG – Prämien und Boni:
- Jede Prämie/Bonus-Position MUSS einen konkreten Zahlenwert haben, wenn im Text eine Zahl genannt wird. Suche aktiv nach: Prozentangaben (z.B. "6 %", "8 %", "1,99 %") und Euro-Beträgen (z.B. "500 €", "1.500", "3.000 €", "1.800").
- In Tabellen: Spalten oft "Prämie", "Bonus", "Restmarge", "KAP", "Reg.-Budget", "VFW", "Endkundenprämie" – die zugehörige Zahl in derselben Zeile/Spalte ist der "wert".
- typ "pct" = Prozent (Wert als Zahl: 6 für 6 %, 1.99 für 1,99 %). typ "eur" = fester Betrag in Euro (Wert als Zahl: 500, 1800, 3000).
- Nur wenn im Text für eine Position wirklich KEINE Zahl steht, setze "wert": null.

Aus dem Text sollst du:
1. Hersteller (Hyundai, Stellantis/Opel, Leapmotor) erkennen
2. Programm-Bezeichnung und Gültigkeitszeitraum (von_datum, bis_datum, Format YYYY-MM-DD)
3. Konditionen: Aktionstyp (VFW gef., VFW n.gef., TW, Netprice, B2C, B2B), ggf. Modell/Reihe
4. Pro Kondition ALLE Bonus-/Prämien-Positionen mit Bezeichnung, typ (pct/eur) und dem ZAHLENWERT aus dem Text

Antworte AUSSCHLIESSLICH mit einem gültigen JSON-Objekt (kein anderer Text):
{{ "quelle": "...", "hersteller": "...", "programm_bezeichnung": "...", "von_datum": "YYYY-MM-DD", "bis_datum": "YYYY-MM-DD", "konditionen": [ {{ "aktionstyp": "...", "modell_pattern": null oder "Modellname", "boni": [ {{ "bezeichnung": "...", "typ": "pct", "wert": 6.0 }}, {{ "bezeichnung": "...", "typ": "eur", "wert": 500 }} ] }} ] }}

- wert bei pct: Zahl (z.B. 6, 8, 1.99). wert bei eur: Zahl in Euro (z.B. 500, 1800, 3000). Nur wenn nirgends eine Zahl steht: null.
- Datum unbekannt: von_datum/bis_datum auf null setzen.

Text des Rundschreibens:
---
{text}
---
"""


def extract_pdf_text(filepath: Path, max_chars: int | None = None) -> str | None:
    try:
        import pdfplumber
    except ImportError:
        print("Fehler: pdfplumber nicht installiert. pip install pdfplumber", file=sys.stderr)
        return None
    text_parts = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    text = "\n".join(text_parts) if text_parts else None
    if text and max_chars and len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... Text gekürzt ...]"
    return text


def _call_lm_studio_once(text: str, quelle: str, timeout: int) -> dict | None:
    """Einmaliger Aufruf LM Studio (ohne Retry)."""
    try:
        from api.ai_api import lm_studio_client
    except ImportError as e:
        print(f"Fehler: ai_api/lm_studio nicht verfügbar: {e}", file=sys.stderr)
        return None
    prompt = REGELWERK_PROMPT.format(text=text)
    messages = [
        {"role": "system", "content": "Du extrahierst strukturierte Daten aus deutschen Verkaufsprogramm-Rundschreiben. Antworte ausschließlich mit gültigem JSON, kein anderer Text."},
        {"role": "user", "content": prompt}
    ]
    response = lm_studio_client.chat_completion(
        messages=messages,
        max_tokens=4000,
        temperature=0.2,
        timeout=timeout
    )
    if not response:
        return None
    raw = response.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            data = {"programme": data, "quelle": quelle}
        elif isinstance(data, dict) and "quelle" not in data:
            data["quelle"] = quelle
        return data
    except json.JSONDecodeError as e:
        print(f"LM Studio Antwort war kein gültiges JSON: {e}", file=sys.stderr)
        print("Rohe Antwort (Auszug):", raw[:500], file=sys.stderr)
        return None


def lm_studio_regelwerk(text: str, quelle: str = "PDF", timeout: int = 240) -> dict | None:
    """Sendet extrahierten Text an LM Studio. Bei 400/Timeout: Retry mit halbiertem Chunk."""
    return _regelwerk_with_retry(text, quelle, timeout, min_chunk=MIN_CHUNK_RETRY)


def _regelwerk_with_retry(text: str, quelle: str, timeout: int, min_chunk: int) -> dict | None:
    result = _call_lm_studio_once(text, quelle, timeout)
    if result is not None:
        return result
    if len(text) <= min_chunk:
        return None
    half = len(text) // 2
    # Überlappung 400 Zeichen, damit keine Zeilengrenze verloren geht
    overlap = min(400, half // 5)
    part1 = text[: half + overlap]
    part2 = text[half - overlap :]
    print(f"    Retry: Chunk halbiert ({len(text)} → {len(part1)} + {len(part2)} Zeichen)")
    r1 = _regelwerk_with_retry(part1, quelle, timeout, min_chunk)
    r2 = _regelwerk_with_retry(part2, quelle, timeout, min_chunk)
    if r1 is None and r2 is None:
        return None
    programme_list = []
    for r in (r1, r2):
        if r is None:
            continue
        progs = r.get("programme")
        if isinstance(progs, list):
            programme_list.extend(progs)
        elif isinstance(r, dict) and r.get("konditionen") is not None:
            programme_list.append(r)
    if not programme_list:
        return r1 or r2
    return {"programme": _merge_programme(programme_list), "quelle": quelle}


def _merge_programme(programme_list: list) -> list:
    """Fasst mehrere KI-Ausgaben (pro Chunk) zu einer Programm-Liste zusammen. Gleicher Hersteller → Konditionen zusammenführen."""
    by_hersteller: dict = {}
    for prog in programme_list:
        if not isinstance(prog, dict):
            continue
        h = (prog.get("hersteller") or "").strip() or "Unbekannt"
        if h not in by_hersteller:
            by_hersteller[h] = {
                "quelle": prog.get("quelle"),
                "hersteller": prog.get("hersteller"),
                "programm_bezeichnung": prog.get("programm_bezeichnung"),
                "von_datum": prog.get("von_datum"),
                "bis_datum": prog.get("bis_datum"),
                "konditionen": [],
            }
        existing = by_hersteller[h]["konditionen"]
        for k in prog.get("konditionen") or []:
            if isinstance(k, dict) and k not in existing:
                existing.append(k)
    return list(by_hersteller.values())


def main():
    parser = argparse.ArgumentParser(description="Verkaufsprogramm-PDFs → LM Studio → Regelwerk (JSON)")
    parser.add_argument("--dir", default=None, help="Ordner mit PDFs (Standard: Kalkulationstool)")
    parser.add_argument("--max-chars", type=int, default=None, help="Max Zeichen pro PDF (Standard: 18000; bei --full unbegrenzt)")
    parser.add_argument("--max-input", type=int, default=None, help="Max Zeichen gesamt an KI (Standard 8000; bei --full 50000)")
    parser.add_argument("--full", action="store_true", help="Gesamte PDF(s) parsen (kein Kürzen, Timeout 300s, max-input 50000)")
    parser.add_argument("--chunk-size", type=int, default=0, help=f"Blöcke dieser Größe (Empfehlung: {DEFAULT_CHUNK_SIZE}); bei 400/Timeout Retry mit Halbierung")
    parser.add_argument("--timeout", type=int, default=None, help=f"Timeout pro Request in Sekunden (Standard: {DEFAULT_CHUNK_TIMEOUT} bei Chunk-Modus, sonst 240)")
    parser.add_argument("--output", "-o", default=None, help="Ausgabe-JSON-Datei (Standard: Regelwerk_<timestamp>.json im Ordner)")
    parser.add_argument("--pdf", action="append", help="Einzelne PDF-Datei (mehrfach möglich)")
    args = parser.parse_args()

    if args.max_chars is None:
        args.max_chars = None if args.full else DEFAULT_MAX_CHARS
    if args.max_input is None:
        args.max_input = 50000 if args.full else 8000
    use_chunk = args.chunk_size > 0
    if args.timeout is not None:
        timeout = args.timeout
    else:
        timeout = DEFAULT_CHUNK_TIMEOUT if use_chunk else (300 if args.full else 240)

    base_dir = Path(args.dir) if args.dir else (KALK_DIR_SYNC if KALK_DIR_SYNC.exists() else KALK_DIR_REPO)
    if not base_dir.exists():
        print(f"Ordner existiert nicht: {base_dir}", file=sys.stderr)
        return 2

    if args.pdf:
        pdf_files = [Path(p) for p in args.pdf if Path(p).exists()]
    else:
        pdf_files = sorted(base_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"Keine PDF-Dateien in {base_dir}", file=sys.stderr)
        return 1

    print(f"Gefunden: {len(pdf_files)} PDF(s)")
    all_text_parts = []
    for pf in pdf_files:
        print(f"  Lese: {pf.name}")
        text = extract_pdf_text(pf, max_chars=args.max_chars)
        if text:
            all_text_parts.append(f"=== {pf.name} ===\n{text}")
        else:
            print(f"    Kein Text extrahiert.")
    if not all_text_parts:
        print("Kein Text aus PDFs extrahiert.", file=sys.stderr)
        return 1

    combined = "\n\n".join(all_text_parts)
    quellen_str = ", ".join(p.name for p in pdf_files)

    if use_chunk and len(combined) > args.chunk_size:
        # Chunk-Modus: Text in Blöcke teilen, pro Block LM Studio (mit Retry bei 400/Timeout), dann merge
        chunk_size = args.chunk_size
        overlap = min(600, chunk_size // 10)
        chunks = []
        start = 0
        while start < len(combined):
            end = start + chunk_size
            chunk = combined[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - overlap if end < len(combined) else len(combined)
        print(f"Chunk-Modus: {len(chunks)} Blöcke (à {chunk_size} Zeichen), Timeout {timeout}s pro Block.")
        programme_list = []
        for i, chunk in enumerate(chunks):
            print(f"  Block {i+1}/{len(chunks)} ({len(chunk)} Zeichen) ...")
            block_result = lm_studio_regelwerk(chunk, quelle=quellen_str, timeout=timeout)
            if block_result:
                progs = block_result.get("programme")
                if isinstance(progs, list):
                    programme_list.extend(progs)
                elif isinstance(block_result, dict) and block_result.get("konditionen") is not None:
                    programme_list.append(block_result)
                elif isinstance(progs, dict):
                    programme_list.append(progs)
        result = {"programme": _merge_programme(programme_list), "quelle": quellen_str} if programme_list else None
    else:
        max_input = args.max_input
        if len(combined) > max_input:
            combined = combined[:max_input] + "\n\n[... Text gekürzt für KI ...]"
            print(f"Hinweis: Text auf {max_input} Zeichen gekürzt.")
        print(f"Gesamtlänge Text: {len(combined)} Zeichen. Sende an LM Studio (Timeout {timeout}s) ...")
        result = lm_studio_regelwerk(combined, quelle=quellen_str, timeout=timeout)

    if not result:
        print("LM Studio lieferte kein gültiges Regelwerk.", file=sys.stderr)
        return 1

    out_path = args.output
    if not out_path:
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = base_dir / f"Regelwerk_{ts}.json"
    else:
        out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Regelwerk gespeichert: {out_path}")
    print("\n--- Inhalt (Auszug) ---")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:2500])
    if len(json.dumps(result)) > 2500:
        print("...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
