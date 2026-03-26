# DRIVE Navigator — Arbeitskontext

## Status: Aktiv (neu angelegt)
## Letzte Aktualisierung: 2026-03-24 (Workstream angelegt aus KI-Assistent-Chat)

## Beschreibung

`DRIVE Navigator` ist der Workstream für den KI-gestützten Navigator im Portal:
- natürliche Fragen auf DRIVE-Daten (`/api/ai/query`)
- Intent-Routing auf SSOT-Queries (kein KPI-Halluzinieren durch LLM)
- optionale Visualisierung im KI-Assistenten (`/ki-assistent`)
- Router-Qualität mit Trainings-/Eval-Datensatz messbar verbessern

## Scope (V1)

- **Hybrid Query API:** `api/ai_api.py` (`/api/ai/query`)
- **KI-Frontend:** `templates/ki_assistent.html` (Text + JSON + optionale Charts)
- **Intent-Router:** `_detect_intent()` inkl. Domain-Hints
- **Visualisierung:** TEK, Auftragseingang, ServiceBox (optional)
- **Training/Evaluation:** Seed-Datensatz + Scripts unter `data/ai_training/` und `scripts/ai_training/`

## Wichtige Dateien

### APIs
- `api/ai_api.py` — Intent-Erkennung, Query-Ausführung, Antwort-Komposition, optional `visualization`
- `api/verkaeufer_zielplanung_api.py` — Monatsziele (für Ziel-/Soll-Darstellung beim Auftragseingang)

### Templates
- `templates/ki_assistent.html` — UI, Feature-Flag (Checkbox), Chart-Rendering/Fallback
- `templates/base.html` — globale Chart.js-Einbindung

### Training/Evaluation
- `docs/AI_ROUTER_TRAINING.md` — Datensatzschema + Workflow
- `data/ai_training/queries.jsonl` — Seed-Fragen mit Gold-Intent
- `scripts/ai_training/validate_dataset.py` — JSONL-/Schema-Validierung
- `scripts/ai_training/evaluate_router.py` — Gold vs. `_detect_intent`
- `scripts/ai_training/build_dataset.py` — Merge mehrerer JSONL-Dateien

### Tests
- `tests/test_ki_visualization_builders.py` — Smoke-/Kompatibilitätstests für Visualisierungs-Builder

## Aktueller Stand (aus diesem Chat)

- ✅ KI-Assistent zeigt bei passenden Intents eine **Grafik**, wenn `visualization` vorhanden ist.
- ✅ Fallback robust: Ohne/fehlerhafte Visualisierung bleibt Text+JSON nutzbar.
- ✅ Verkauf-Visualisierung erweitert um **Ziel/Soll** (Monat + YTD), wenn Zielplanung verfügbar ist.
- ✅ Router-Training gestartet (Seed + Validator + Evaluator + Builder).
- ✅ Seed-Evaluation aktuell: **35/35 Treffer (100%)** auf `queries.jsonl`.

## Konkrete Regeln für DRIVE Navigator

- **SSOT first:** Zahlen/KPIs nur aus bestehenden Datenfunktionen (z. B. TEK, Verkauf, ServiceBox).
- **JSON-Vertrag stabil halten:** `success`, `answer_text`, `answer_data` immer; `visualization` nur optional.
- **Fail-safe:** Visual-Build darf Antwort nie brechen.
- **Permission-aware:** Keine Intent-Daten ohne bestehende Feature-Berechtigung.
- **Messbar verbessern:** Routing-Änderungen immer mit `evaluate_router.py` gegen Seed prüfen.

## Nächste Schritte

1. Export anonymisierter Realfragen in `*.local.jsonl` (nicht committen), dann Merge/Evaluation.
2. Confidence-Strategie ergänzen (bei Unsicherheit gezielte Rückfrage statt Default).
3. Entity-Evaluation ausbauen (`gold_entities`) für Monat/Jahr/Kunde/Teilenummer.
4. Weitere Visuals stufenweise: Kunden-/Teile-Lager nur wenn fachlich sinnvoll.
5. Optional später: kleines Intent-Modell/Fine-Tuning nur für Routing, nicht für KPI-Berechnung.

## Abhängigkeiten

- `auth-ldap` (Berechtigungen und API-Key-Scopes)
- `verkauf` (Zielplanung/Monatsziele)
- `controlling` (TEK-SSOT)
- `integrations` (ServiceBox/Kundenquellen)
