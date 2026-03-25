#!/usr/bin/env python3
"""
Führt mehrere .jsonl zu einer Datei zusammen (eindeutige id).

Usage:
  python scripts/ai_training/build_dataset.py \\
    --inputs data/ai_training/queries.jsonl data/ai_training/queries_team.jsonl \\
    --output data/ai_training/merged.jsonl
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def load_lines(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{lineno}: JSON {e}") from e
    return rows


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Merge AI router JSONL files")
    parser.add_argument(
        "--inputs",
        nargs="+",
        type=Path,
        required=True,
        help="Input .jsonl files (Reihenfolge: spätere überschreiben bei gleicher id)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output .jsonl",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="validate_dataset.py nicht aufrufen",
    )
    args = parser.parse_args()

    merged: dict[str, dict] = {}
    for p in args.inputs:
        if not p.is_file():
            print(f"FEHLT: {p}", file=sys.stderr)
            return 2
        for row in load_lines(p):
            rid = row.get("id")
            if not isinstance(rid, str):
                print(f"Ungültige Zeile ohne String-id in {p}", file=sys.stderr)
                return 2
            merged[rid] = row

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        # stabile Sortierung nach id
        for rid in sorted(merged.keys()):
            out.write(json.dumps(merged[rid], ensure_ascii=False) + "\n")

    print(f"Geschrieben: {args.output} ({len(merged)} Einträge)")

    if not args.no_validate:
        validate = root / "scripts" / "ai_training" / "validate_dataset.py"
        r = subprocess.run(
            [sys.executable, str(validate), "--path", str(args.output)],
            cwd=str(root),
        )
        return int(r.returncode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
