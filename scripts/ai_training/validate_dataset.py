#!/usr/bin/env python3
"""
Validiert queries.jsonl (Schema + JSON pro Zeile).

Usage (Repo-Root):
  python scripts/ai_training/validate_dataset.py
  python scripts/ai_training/validate_dataset.py --path data/ai_training/queries.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ALLOWED_INTENTS = frozenset({
    "tek_summary",
    "verkauf_auftragseingang",
    "teile_lager",
    "servicebox_bestellungen",
    "kunden_suche",
})

REQUIRED_KEYS = frozenset({"id", "frage", "gold_intent"})


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Validate AI router JSONL dataset")
    parser.add_argument(
        "--path",
        type=Path,
        default=root / "data" / "ai_training" / "queries.jsonl",
        help="Path to .jsonl file",
    )
    args = parser.parse_args()
    path: Path = args.path
    if not path.is_file():
        print(f"FEHLT: {path}", file=sys.stderr)
        return 2

    errors = 0
    seen_ids: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Zeile {lineno}: JSON-Fehler: {e}", file=sys.stderr)
                errors += 1
                continue
            if not isinstance(row, dict):
                print(f"Zeile {lineno}: Objekt erwartet", file=sys.stderr)
                errors += 1
                continue
            missing = REQUIRED_KEYS - row.keys()
            if missing:
                print(f"Zeile {lineno}: fehlende Keys {missing}", file=sys.stderr)
                errors += 1
            gid = row.get("gold_intent")
            if gid not in ALLOWED_INTENTS:
                print(f"Zeile {lineno}: ungültiges gold_intent {gid!r}", file=sys.stderr)
                errors += 1
            rid = row.get("id")
            if not isinstance(rid, str) or not rid.strip():
                print(f"Zeile {lineno}: id muss nicht-leerer String sein", file=sys.stderr)
                errors += 1
            elif rid in seen_ids:
                print(f"Zeile {lineno}: doppelte id {rid!r}", file=sys.stderr)
                errors += 1
            else:
                seen_ids.add(rid)
            fr = row.get("frage")
            if not isinstance(fr, str) or not fr.strip():
                print(f"Zeile {lineno}: frage muss nicht-leerer String sein", file=sys.stderr)
                errors += 1

    if errors:
        print(f"Validierung: {errors} Fehler in {path}", file=sys.stderr)
        return 1
    print(f"OK: {path} ({len(seen_ids)} Einträge)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
