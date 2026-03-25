#!/usr/bin/env python3
"""
Führt Regelwerk_Hyundai.json und Regelwerk_Stellantis.json zu einem
Regelwerk_Vollstaendig.json zusammen und erzeugt die lesbare .md.

Verwendung:
  python scripts/verkauf/merge_regelwerk.py [--dir PFAD]
  python scripts/verkauf/merge_regelwerk.py --hyundai datei1.json --stellantis datei2.json -o /pfad/ausgabe

Ohne --hyundai/--stellantis werden im --dir (Standard: Kalkulationstool) die Dateien
Regelwerk_Hyundai.json und Regelwerk_Stellantis.json gesucht.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KALK_DIR_REPO = ROOT / "docs/workstreams/verkauf/Kalkulationstool"
KALK_DIR_SYNC = Path("/mnt/greiner-portal-sync/docs/workstreams/verkauf/Kalkulationstool")


def _load_programme(path: Path) -> list[dict]:
    """Lädt eine Regelwerk-JSON; gibt Liste der Programme (1 pro Hersteller) zurück."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    progs = data.get("programme")
    if isinstance(progs, list):
        return progs
    if isinstance(data, dict) and data.get("konditionen") is not None:
        return [data]
    return []


def _programme_to_md(prog: dict) -> str:
    """Ein Programm (Hersteller) als Markdown-Tabellen."""
    lines = []
    hersteller = prog.get("hersteller") or "Unbekannt"
    programm = prog.get("programm_bezeichnung") or ""
    quelle = prog.get("quelle") or ""
    von = prog.get("von_datum") or ""
    bis = prog.get("bis_datum") or ""

    lines.append(f"## {hersteller} — {programm}")
    lines.append("")
    lines.append(f"**Quelle:** {quelle}")
    if von or bis:
        lines.append(f"**Gültigkeit:** {von or '?'} – {bis or '?'}")
    else:
        lines.append("**Gültigkeit:** (laut PDF ggf. Quartalsende)")
    lines.append("")
    lines.append("| Aktionstyp | Modell / Reihe | Bonus | Typ | Wert |")
    lines.append("|------------|----------------|-------|-----|------|")

    for k in prog.get("konditionen") or []:
        if not isinstance(k, dict):
            continue
        at = (k.get("aktionstyp") or "").replace("|", "\\|")
        mod = (k.get("modell_pattern") or "—").replace("|", "\\|")
        for b in k.get("boni") or []:
            if not isinstance(b, dict):
                continue
            bez = (b.get("bezeichnung") or "").replace("|", "\\|")[:60]
            typ = b.get("typ") or "—"
            wert = b.get("wert")
            if wert is None:
                w = "—"
            elif typ == "eur":
                w = f"**{int(wert):,} €**".replace(",", ".")
            elif typ == "pct":
                w = f"**{wert} %**"
            else:
                w = f"**{wert}**" if wert != "" else "—"
            lines.append(f"| {at} | {mod} | {bez} | {typ} | {w} |")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge Regelwerk Hyundai + Stellantis → Vollständig JSON + .md")
    parser.add_argument("--dir", default=None, help="Ordner mit Regelwerk_Hyundai.json / Regelwerk_Stellantis.json")
    parser.add_argument("--hyundai", default=None, help="Pfad zu Regelwerk_Hyundai.json")
    parser.add_argument("--stellantis", default=None, help="Pfad zu Regelwerk_Stellantis.json")
    parser.add_argument("-o", "--output-dir", default=None, help="Ausgabeordner (Standard: --dir bzw. Kalkulationstool)")
    args = parser.parse_args()

    base = Path(args.dir) if args.dir else (KALK_DIR_SYNC if KALK_DIR_SYNC.exists() else KALK_DIR_REPO)
    out_dir = Path(args.output_dir) if args.output_dir else base
    hyundai_path = Path(args.hyundai) if args.hyundai else base / "Regelwerk_Hyundai.json"
    stellantis_path = Path(args.stellantis) if args.stellantis else base / "Regelwerk_Stellantis.json"

    programmes = []
    for name, path in [("Hyundai", hyundai_path), ("Stellantis", stellantis_path)]:
        p = _load_programme(path)
        if p:
            programmes.extend(p)
            print(f"Geladen: {path.name} ({len(p)} Programm(e))")
        else:
            if path.exists():
                print(f"Hinweis: {path.name} enthält keine programme.", file=sys.stderr)
            else:
                print(f"Hinweis: {path} nicht gefunden.", file=sys.stderr)

    if not programmes:
        print("Keine Programme zum Zusammenführen.", file=sys.stderr)
        return 1

    merged = {
        "programme": programmes,
        "quelle": "Merge aus " + ", ".join(p.get("quelle") or "?" for p in programmes[:5]),
    }
    json_path = out_dir / "Regelwerk_Vollstaendig.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Gespeichert: {json_path}")

    md_lines = [
        "# Verkaufsprogramme — Regelwerk (vollständig, lesbar)",
        "",
        "**Quelle:** Merge aus Regelwerk_Hyundai.json + Regelwerk_Stellantis.json (LM Studio, ein PDF pro Lauf, Chunk 6000).",
        "**Rohdaten:** `Regelwerk_Vollstaendig.json`",
        "",
        "---",
        "",
    ]
    for prog in programmes:
        md_lines.append(_programme_to_md(prog))
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    md_lines.extend([
        "## Legende",
        "",
        "- **Typ %** = Prozentsatz, **Typ €** = Betrag in Euro.",
        "- **Modell „—“** = für alle Modelle.",
        "",
        "## Technik",
        "",
        "- Einzel-PDFs: `vfw_rundschreiben_regelwerk_ki.py --pdf <datei> --chunk-size 6000 --timeout 300 -o Regelwerk_Hyundai.json` (bzw. Stellantis).",
        "- Merge: `merge_regelwerk.py --dir .../Kalkulationstool`",
        "",
    ])
    md_path = out_dir / "Regelwerk_Vollstaendig_lesbar.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Gespeichert: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
