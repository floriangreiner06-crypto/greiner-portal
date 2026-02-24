# Vorschlag: Kompletter Qualitätscheck DRIVE über alle Module

**Stand:** 2026-02-24  
**Ziel:** Einmalig oder wiederkehrend die Codequalität des Greiner Portals DRIVE über alle Module prüfen – ohne sofort alles umzusetzen; erst Konzept und Priorisierung.

---

## 1. Ausgangslage

- **Keine zentrale QA-Pipeline:** Kein `pyproject.toml`, kein Linter (Ruff/Flake8), kein Test-Runner (pytest), keine Type-Checks (mypy).
- **Großer Codebestand:** Viele API-Module (`api/*.py`), Routes (`routes/`), Templates, Scripts, Celery-Tasks.
- **SSOT & Workstreams:** Fachlogik soll an wenigen Stellen liegen; Modul-Grenzen und CONTEXT.md pro Workstream sind relevant.

Ein Qualitätscheck soll **alle Module** erfassen, aber schrittweise und priorisiert umsetzbar sein.

---

## 2. Vorschlag: Fünf Säulen

### Säule A: Statische Code-Analyse (Linting & Style)

| Tool | Zweck | Aufwand | Priorität |
|------|--------|---------|-----------|
| **Ruff** | Linting (pyflakes, isort, Teile von flake8) + optional Formatierung | Gering, ein Config-File | Hoch |
| **Black** (optional) | Einheitliches Format, wenn Ruff nicht für Format genutzt wird | Gering | Mittel |

**Vorgehen:**

1. `pyproject.toml` anlegen mit `[tool.ruff]` (inkl. Zeilenlänge, ausgeschlossene Verzeichnisse wie `.venv`, `scripts/` evtl. lockerer).
2. Einmal `ruff check api/ routes/ auth/ celery_app/` ausführen und Ergebnis als Baseline dokumentieren.
3. Entscheidung: Fehler sofort beheben **oder** nur neue Fehler verbieten („baseline“) und schrittweise abbauen.

**Nutzen:** Einheitlicher Stil, typische Bugs (unused imports, undefined names) werden gefunden.

---

### Säule B: Typen & Konsistenz (mypy)

| Tool | Zweck | Aufwand | Priorität |
|------|--------|---------|-----------|
| **mypy** | Statische Typ-Prüfung | Mittel bis hoch (viele Anpassungen bei bestehendem Code) | Mittel (langfristig) |

**Vorgehen:**

1. mypy nur für **neue** oder besonders kritische Module aktivieren (z. B. `api/db_connection.py`, `api/controlling_data.py`) **oder**
2. mypy im „soft“-Modus: nur warnen, nicht brechen; Baseline-Liste von Ignorierungen anlegen und schrittweise reduzieren.

**Nutzen:** Weniger Laufzeitfehler, bessere IDE-Unterstützung, klare Schnittstellen.

---

### Säule C: Sicherheit

| Tool | Zweck | Aufwand | Priorität |
|------|--------|---------|-----------|
| **bandit** | Typische Python-Sicherheitslücken (eval, unsichere Deserialisierung, Hardcoded Secrets) | Gering | Hoch |
| **pip-audit** oder **safety** | Bekannte Schwachstellen in Dependencies | Gering | Hoch |

**Vorgehen:**

1. Einmalig: `pip install bandit pip-audit` (oder safety), dann:
   - `bandit -r api/ routes/ auth/ celery_app/ -x .venv`
   - `pip-audit` (oder `safety check`)
2. Ergebnis in einer Checkliste festhalten; kritische Findings sofort prüfen, Rest priorisiert abarbeiten.
3. Optional: bandit/pip-audit in ein kleines „QA-Script“ packen, das ihr bei Bedarf manuell ausführt.

**Nutzen:** Keine neuen, vermeidbaren Sicherheitslücken; bekannte CVEs in Abhängigkeiten erkennen.

---

### Säule D: Tests

| Maßnahme | Zweck | Aufwand | Priorität |
|----------|--------|---------|-----------|
| **pytest** + Struktur | Unit-Tests für Kernlogik (SSOT-Funktionen) | Hoch | Hoch (langfristig) |
| **Coverage** | Sichtbarkeit, welche Bereiche getestet sind | Mittel | Mittel |
| **Smoke-Tests** | „App startet, Login-Seite lädt“ (z. B. mit requests oder Playwright) | Mittel | Mittel |

**Vorgehen:**

1. `tests/` anlegen, `pytest.ini` oder `pyproject.toml` mit pytest-Optionen.
2. Zuerst **kritische SSOT-Module** testen (z. B. `api/controlling_data.py` – TEK, Breakeven), dann schrittweise weitere APIs.
3. Kein „alles sofort testen“, sondern pro Workstream/Modul 1–2 repräsentative Tests; Coverage-Ziel z. B. erstmal nur für `api/controlling_data.py`, `api/db_connection.py`.

**Nutzen:** Refactorings werden abgesichert; Regressionen fallen auf.

---

### Säule E: Dokumentation & Struktur

| Prüfpunkt | Zweck | Aufwand | Priorität |
|-----------|--------|---------|-----------|
| **CONTEXT.md pro Workstream** | Ist der Arbeitskontext aktuell? | Manuell / Checkliste | Hoch |
| **SSOT-Check** | Gibt es doppelte Berechnungen/KPIs außerhalb der vereinbarten SSOT? | Manuell / Code-Review | Hoch |
| **Navigation & Rechte** | Sind Navi-Punkte und `requires_feature`/Rollen konsistent? | Manuell / kleines Script | Mittel |
| **DB-Schema vs. Code** | Stimmen Tabellen/Namen in `docs/DB_SCHEMA_POSTGRESQL.md` mit Migrationen und Code überein? | Manuell / Stichproben | Mittel |

**Vorgehen:**

1. Checkliste für „Qualitätscheck DRIVE“ anlegen (z. B. in `docs/` oder `docs/workstreams/infrastruktur/`).
2. Einmal pro Quartal oder vor größeren Releases: CONTEXT.md durchgehen, SSOT in CLAUDE.md gegen Code prüfen, grobe Abweichungen dokumentieren und priorisieren.

**Nutzen:** Onboarding und Wartung werden einfacher; Doppellogik wird sichtbar.

---

## 3. Priorisierung (Empfehlung)

- **Sofort umsetzbar, hoher Nutzen:**  
  **Säule A (Ruff)** + **Säule C (bandit + pip-audit)**  
  → Ein Config-File, zwei Befehle, Ergebnis dokumentieren; keine großen Code-Änderungen nötig.

- **Kurzfristig:**  
  **Säule E (Checkliste + einmaliger CONTEXT/SSOT-Check)**  
  → Kein neues Tool, nur Prozess und eine geführte Prüfung.

- **Mittelfristig:**  
  **Säule D (pytest für 2–3 Kernmodule + Smoke-Test)**  
  → Tests nur für SSOT und kritische Pfade; kein Vollcoverage-Ziel.

- **Langfristig:**  
  **Säule B (mypy)** schrittweise für neue/kritische Module; Rest optional.

---

## 4. Konkrete nächste Schritte (wenn ihr starten wollt)

1. **Entscheidung:** Nur Vorschlag lesen **oder** „Phase 1“ starten (A + C + E-Checkliste).
2. **Phase 1 umsetzen:**
   - `pyproject.toml` mit `[tool.ruff]` anlegen (inkl. exclude: `.venv`, ggf. `scripts/`).
   - Einmal ausführen:  
     `ruff check api/ routes/ auth/ celery_app/`  
     `bandit -r api/ routes/ auth/ celery_app/ -x .venv`  
     `pip-audit`
   - Ergebnis in `docs/QUALITAETSCHECK_ERGEBNIS_<Datum>.md` festhalten (Anzahl Findings, kritische Punkte, Verzicht/Backlog).
   - Kurze Checkliste für CONTEXT.md + SSOT in `docs/` oder unter `docs/workstreams/infrastruktur/` anlegen.
3. **Optional:** Ein Script `scripts/qa_run.py` oder `make qa` / `scripts/qa_check.sh`, das Ruff + bandit + pip-audit nacheinander ausführt und Exit-Code 0/1 setzt (z. B. für manuelles „Pre-Commit“ oder spätere CI).

---

## 5. Was wir bewusst nicht vorschlagen (erstmal)

- **Pre-commit-Hooks** oder **CI-Pipeline** (GitHub Actions etc.): erst sinnvoll, wenn Baseline (Ruff/bandit) vereinbart und wenigstens teilweise bereinigt ist.
- **Vollständige Test-Coverage:** unrealistisch für den bestehenden Bestand; besser gezielte Tests für SSOT und kritische Pfade.
- **Große Refactorings** nur „für Qualität“: nur dann, wenn ohnehin am Modul gearbeitet wird.

---

## 6. Kurzfassung

| Säule | Inhalt | Priorität | Aufwand |
|-------|--------|-----------|---------|
| A | Ruff (Lint/Style) | Hoch | Gering |
| B | mypy (Typen) | Mittel, langfristig | Mittel–hoch |
| C | bandit + pip-audit (Sicherheit) | Hoch | Gering |
| D | pytest + gezielte Tests + Smoke | Mittel, langfristig | Hoch |
| E | CONTEXT/SSOT-Checkliste + Doku | Hoch | Gering (Prozess) |

**Empfehlung:** Mit **A + C + E** starten (Vorschlag umsetzen, Ergebnis dokumentieren), dann **D** schrittweise für Kernmodule, **B** optional für neue/kritische Bereiche.

Wenn ihr wollt, kann als nächster Schritt nur **Phase 1** (Ruff-Config + einmalige Befehle + Ergebnis-Dokument + Checkliste) konkret ausformuliert und angelegt werden, ohne sofort alle Findings zu beheben.
