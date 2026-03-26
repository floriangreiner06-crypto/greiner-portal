#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft, ob die Hilfe-KI-Kontext-Registry noch zu den Quell-Dateien passt.
Für Session-End: Wenn Quellen neuer als die Registry sind, Einträge prüfen/aktualisieren.

Nutzung: Aus Projektroot aufrufen: python3 scripts/check_hilfe_registry.py
Exit 0: Keine Aktion nötig. Exit 1: Mindestens ein Eintrag hat neuere Quellen → prüfen.
"""
import os
import sys
from pathlib import Path

# Projektroot (Script liegt in scripts/)
ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PY = ROOT / "api" / "hilfe_bedrock_service.py"
REGISTRY_MD = ROOT / "docs" / "workstreams" / "Hilfe" / "hilfe_ki_kontext_registry.md"

# Quellen pro Registry-Eintrag (wie in REGISTRY_AKTUELL_HALTEN.md)
SOURCES_BY_ENTRY = {
    "tek": [
        "api/controlling_data.py",
        "docs/workstreams/controlling/CONTEXT.md",
    ],
    "urlaub": [
        "api/vacation_api.py",
        "api/vacation_locosoft_service.py",
        "docs/workstreams/urlaubsplaner/STELLUNGNAHME_ROLLOUT_SSOT_OHNE_LOCOSOFT.md",
        "docs/workstreams/urlaubsplaner/RESTURLAUB_KEINE_KRANKHEIT.md",
        "docs/workstreams/urlaubsplaner/CONTEXT.md",
    ],
}


def mtime(path: Path) -> float:
    """Letzte Änderung in Sekunden; 0 wenn Datei fehlt."""
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def main():
    os.chdir(ROOT)
    registry_py_mtime = mtime(REGISTRY_PY)
    registry_md_mtime = mtime(REGISTRY_MD)
    registry_mtime = max(registry_py_mtime, registry_md_mtime)

    needs_review = []
    for entry, rel_paths in SOURCES_BY_ENTRY.items():
        for rel in rel_paths:
            p = ROOT / rel
            if not p.exists():
                continue
            t = mtime(p)
            if t > registry_mtime:
                needs_review.append((entry, rel, t))

    if not needs_review:
        print("Hilfe-Registry: Keine neuere Quellen als Registry – keine Aktion nötig.")
        return 0

    print("Hilfe-Registry: Folgende Quellen sind neuer als die Registry – Einträge prüfen:")
    for entry, rel in sorted(set((e, r) for e, r, _ in needs_review)):
        print(f"  - Eintrag '{entry}': {rel}")
    print("\n→ Siehe docs/workstreams/Hilfe/REGISTRY_AKTUELL_HALTEN.md")
    print("→ Prüfen: api/hilfe_bedrock_service.py (HILFE_KI_KONTEXT_REGISTRY), hilfe_ki_kontext_registry.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())
