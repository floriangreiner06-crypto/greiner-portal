# DRIVE Navigator — START HERE

Diese Datei ist der schnelle Einstieg für neue Sessions im Workstream `drive-navigator`.

## 1) Zuerst lesen (2–3 Minuten)

1. `docs/workstreams/drive-navigator/CONTEXT.md`
2. `docs/AI_ROUTER_TRAINING.md`
3. Optional bei API-Änderungen: `api/ai_api.py` (Bereich `_detect_intent`, `/api/ai/query`, Visualisierung)

## 2) Schnellcheck vor Änderungen

- Läuft das Portal?  
  `sudo systemctl status greiner-portal`
- Funktioniert Seed-Evaluation?
  - `python scripts/ai_training/validate_dataset.py`
  - `python scripts/ai_training/evaluate_router.py`
- Tests Visualisierung:
  - `python -m unittest tests.test_ki_visualization_builders`

## 3) Architektur in 30 Sekunden

- Frontend `/ki-assistent` sendet Frage an `POST /api/ai/query`
- Router (`_detect_intent`) wählt Intent
- SSOT-Query liefert `answer_data`
- Antwort liefert immer Text + JSON, optional `visualization`
- UI rendert Chart nur wenn `visualization` vorhanden ist

## 4) Done-Definition für Änderungen

Eine Änderung gilt als fertig, wenn:

1. `validate_dataset.py` ist grün
2. `evaluate_router.py` ist grün (oder dokumentierte Abweichung)
3. relevante Tests sind grün (`tests/test_ki_visualization_builders.py`)
4. bei Backend-Änderung: `greiner-portal` wurde neu gestartet
5. `CONTEXT.md` wurde aktualisiert (kurzer Stand + nächste Schritte)

## 5) Typische Aufgaben im Workstream

- Neue Intent-Regeln ergänzen
- Seed-Fragen im JSONL erweitern
- Router-Fehlklassifikationen auswerten und beheben
- Visualisierungen pro Intent erweitern (immer fail-safe)
- Ziel-/Soll-Daten in Charts integrieren (nur SSOT-Quellen)

## 6) Sicherheits-/Qualitätsregeln

- Keine KPI-Berechnung im LLM — immer SSOT-Funktionen nutzen
- API-Vertrag stabil halten (`success`, `answer_text`, `answer_data`; `visualization` optional)
- Bei Unsicherheit lieber Rückfrage als falsches Routing
- Keine personenbezogenen Rohdaten in committed Trainingsdateien

## 7) Nächster sinnvoller Ausbau

1. anonymisierte Realfragen als `*.local.jsonl` erfassen
2. mit `build_dataset.py` mergen
3. Router-Evaluation regelmäßig laufen lassen (CI)
4. `gold_entities` schrittweise ergänzen (Monat/Jahr/Kunde/Teilenummer)
