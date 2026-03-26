# AI Router / Intent – Trainingsdaten & Evaluation

Ziel: **Intent-Routing** für `/api/ai/query` und den KI-Assistenten messbar verbessern – ohne KPIs aus dem LLM zu erfinden (SSOT bleibt in den Query-Funktionen).

## SSOT für Routing (aktuell)

Die Regel-Engine ist `api/ai_api.py` → `_detect_intent(frage, bereich)`.

Erlaubte **`gold_intent`**-Werte (müssen mit `_detect_intent` übereinstimmen, sonst schlägt die Evaluation fehl):

| `gold_intent` | Kurzbeschreibung |
|---------------|------------------|
| `tek_summary` | TEK, DB1, Breakeven, Marge, Controlling |
| `verkauf_auftragseingang` | Auftragseingang, Auslieferung, Verkäufer |
| `teile_lager` | Lager, Teilenummer, Teilebegriff |
| `servicebox_bestellungen` | ServiceBox, Teilebestellungen, „für X bestellt“ |
| `kunden_suche` | Kunde, Adressbuch, Telefon, E-Mail |

Optionaler Kontext: **`bereich`** wie im API-Body (`controlling`, `verkauf`, `teile`, …) – gleiche Semantik wie im Portal.

## Dateiformat: `queries.jsonl`

Eine Zeile = ein JSON-Objekt (UTF-8), **kein** Pretty-Print innerhalb der Zeile.

### Pflichtfelder

- **`id`**: eindeutiger String (z. B. `seed_001`)
- **`frage`**: Nutzerfrage (Originalsprache, wie im Portal)
- **`gold_intent`**: einer der Werte aus der Tabelle oben

### Empfohlene Felder

- **`bereich`**: `""` oder Domain-Hint (wie API)
- **`tags`**: Liste kurzer Stichworte (`smoke`, `tek`, `verkauf`, …)
- **`notes`**: kurze Begründung für Menschen / Review
- **`needs_clarification_expected`**: `true`/`false` – für spätere Zeit-/Entity-Rückfragen (Evaluation ignoriert das vorerst, außer mit `--strict-clarification`)

### Optional (Roadmap)

- **`gold_entities`**: z. B. `{ "month": 3, "year": 2026 }` – sobald wir Entity-Extraktion testen
- **`locale`**: `de`

## Verzeichnis

- **Seed-Datensatz:** `data/ai_training/queries.jsonl`
- **Eigene Erweiterungen:** z. B. `data/ai_training/queries_team.jsonl` (nicht committen, wenn personenbezogen)

## Skripte

Voraussetzung: Repo-Root `/opt/greiner-portal`, virtuelle Umgebung aktiv.

```bash
cd /opt/greiner-portal
source .venv/bin/activate   # optional

# Zeilen prüfen (Schema + JSON)
python scripts/ai_training/validate_dataset.py

# Router gegen Gold vergleichen (nutzt _detect_intent)
python scripts/ai_training/evaluate_router.py

# Mehrere .jsonl zusammenführen (eindeutige id)
python scripts/ai_training/build_dataset.py \
  --inputs data/ai_training/queries.jsonl data/ai_training/queries_local.jsonl \
  --output data/ai_training/merged.jsonl
```

## Workflow (pragmatisch)

1. **Seed** pflegen und erweitern (`queries.jsonl`).
2. **`validate_dataset.py`** in CI oder vor Commit.
3. **`evaluate_router.py`** nach jeder Änderung an `_detect_intent` (Ziel: 100 % auf dem Seed; bei bewusstem Routing-Change Gold anpassen).
4. Später: Export aus anonymisierten Logs → zweite Datei → `build_dataset.py`.
5. Fine-Tuning / externes Modell: JSONL in Tool-spezifisches Format konvertieren (separates Skript, sobald Modell feststeht).

## Datenschutz

Keine echten Kundennamen, Telefonnummern oder internen Personen in committed Dateien. Für echte Chats: anonymisieren oder nur `data/ai_training/*.local.jsonl` (gitignore).

## Letzte Aktualisierung

2026-03-24 – Initial (Seed + Skripte).
