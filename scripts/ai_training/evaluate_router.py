#!/usr/bin/env python3
"""
Vergleicht Gold-Intents aus queries.jsonl mit api.ai_api._detect_intent.

Usage (Repo-Root):
  python scripts/ai_training/evaluate_router.py
  python scripts/ai_training/evaluate_router.py --jsonl data/ai_training/queries.jsonl --verbose
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))

    parser = argparse.ArgumentParser(description="Evaluate rule-based intent router")
    parser.add_argument(
        "--jsonl",
        type=Path,
        default=root / "data" / "ai_training" / "queries.jsonl",
        help="Gold dataset",
    )
    parser.add_argument("--verbose", action="store_true", help="Fehler einzeln ausgeben")
    args = parser.parse_args()

    if not args.jsonl.is_file():
        print(f"FEHLT: {args.jsonl}", file=sys.stderr)
        return 2

    from api.ai_api import _detect_intent

    rows: list[dict] = []
    with args.jsonl.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append(json.loads(line))

    ok = 0
    wrong: list[tuple[str, str, str, str]] = []
    for row in rows:
        frage = row.get("frage") or ""
        bereich = row.get("bereich") or ""
        gold = row.get("gold_intent")
        pred = _detect_intent(frage, bereich=bereich).get("id")
        if pred == gold:
            ok += 1
        else:
            wrong.append((row.get("id", "?"), frage[:80], gold, pred or ""))

    n = len(rows)
    acc = ok / n if n else 0.0
    print(f"Datensatz: {args.jsonl}")
    print(f"Treffer:   {ok}/{n}  ({acc * 100:.1f} %)")

    if wrong and args.verbose:
        print("\nAbweichungen:")
        for rid, fq, g, p in wrong:
            print(f"  [{rid}] gold={g} pred={p}")
            print(f"      {fq!r}")

    # Kurz-Confusion: gold -> pred
    confusion = Counter((g, p) for _, _, g, p in wrong)
    if confusion:
        print("\nTop-Fehler (gold → pred):")
        for (g, p), c in confusion.most_common(8):
            print(f"  {g} → {p}: {c}")

    return 0 if ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
