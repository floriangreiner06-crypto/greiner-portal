# Qualitätscheck DRIVE — Phase-1-Ergebnis

**Datum:** 2026-02-24  
**Scope:** `api/`, `routes/`, `auth/`, `celery_app/`  
**Referenz:** [QUALITAETSCHECK_VORSCHLAG.md](QUALITAETSCHECK_VORSCHLAG.md)

---

## 1. Ruff (Linting & Style)

**Befehl:** `ruff check api/ routes/ auth/ celery_app/`

| Kennzahl | Wert |
|----------|------|
| **Gesamt-Fehler** | 5.220 |
| **Davon automatisch behebbar** | 4.206 (mit `--fix`) |
| **+ mit --unsafe-fixes** | weitere 896 |

### Top-Fehler (Anzahl)

| Code | Bedeutung | Anzahl |
|------|-----------|--------|
| W293 | Blank line contains whitespace | 4.172 |
| W291 | Trailing whitespace | 357 |
| I001 | Import block un-sorted | 211 |
| F401 | Unused import | 193 |
| F841 | Unused variable | 80 |
| E722 | Bare except | 71 |
| F541 | f-string without placeholders | 49 |
| E402 | Import not at top of file | 22 |
| B007 | Unused loop variable | 17 |
| F811 | Redefined while unused | 16 |
| B905 | zip() without strict= | 10 |
| … | (weitere wenige) | … |

### Bewertung

- **Baseline:** 5.220 Fehler als aktuellen Stand akzeptieren; keine sofortige Pflicht zur Bereinigung.
- **Empfehlung:** Zuerst `ruff check ... --fix` (ohne unsafe) laufen lassen → reduziert auf ca. 1.000 Fehler. Rest schrittweise pro Modul/Workstream.
- **Kritisch prüfen:** F821 (undefined name, 3×), F811 (redefined, 16×), E722 (bare except, 71×) – können echte Bugs sein.

---

## 2. Bandit (Sicherheit)

**Befehl:** `bandit -r api/ routes/ auth/ celery_app/ -x .venv`

| Kennzahl | Wert |
|----------|------|
| **Zeilen gescannt** | 67.477 |
| **Issues gesamt** | 536 |
| **High** | 2 |
| **Medium** | 395 |
| **Low** | 139 |

### Nach Confidence

| Confidence | Anzahl |
|------------|--------|
| High | 141 |
| Medium | 202 |
| Low | 193 |

### Typische Findings

- **B608 (hardcoded_sql_expressions):** Sehr häufig – f-Strings in SQL (z. B. `f"SELECT ... {variable}"`). Viele Fälle sind **parametrisierte** Queries (Werte über `%s`/Parameter), nur der Filter-Teil ist eingebettet; Risiko je nach Variable zu prüfen. Echte SQL-Injection-Risiken priorisieren (user-input in SQL-String).
- **High-Severity (2):** Manuell prüfen (Bandit-Report nach „High“ durchsuchen).
- **Weitere:** B105 (hardcoded password), B104 (bind all interfaces) etc. – Stichproben prüfen.

### Bewertung

- **Erledigt (2026-02-24):** Die 2 High-Issues wurden behoben – siehe [QUALITAETSCHECK_BANDIT_HIGH_VORSCHLAG.md](QUALITAETSCHECK_BANDIT_HIGH_VORSCHLAG.md) (B324: MD5 `usedforsecurity=False` in `jahrespraemie_api.py`; B201: `debug` aus `FLASK_DEBUG` in `routes/app.py`).
- **Backlog:** B608-Liste nach „user input“ / externen Daten filtern; nur diese zuerst auf echte Injection prüfen. Viele B608 sind False Positives bei intern gebauten Filter-Strings.

---

## 3. pip-audit (Dependencies)

**Befehl:** `pip-audit`

| Paket | Aktuell | CVE/ID | Fix-Version |
|-------|---------|--------|-------------|
| cryptography | 46.0.4 | CVE-2026-26007 | 46.0.5 |
| flask | 3.0.0 | CVE-2026-27205 | 3.1.3 |
| gunicorn | 21.2.0 | CVE-2024-1135, CVE-2024-6827 | 22.0.0 |
| pdfminer-six | 20231228 | CVE-2025-64512, CVE-2025-70559 | 20251107 / 20251230 |
| pillow | 12.1.0 | CVE-2026-25990 | 12.1.1 |
| pip | 24.0 | CVE-2025-8869, CVE-2026-1703 | 25.3 / 26.0 |
| werkzeug | 3.1.5 | CVE-2026-27199 | 3.1.6 |

**Gesamt:** 10 bekannte Schwachstellen in 7 Paketen.

### Bewertung

- **Empfehlung:** Fix-Versionen in `requirements.txt` eintragen und nach Test-Upgrade deployen (Flask, gunicorn, werkzeug, cryptography, pillow, pdfminer-six). pip-Version separat (System/venv).
- **Priorität:** Hoch für flask, gunicorn, werkzeug (Web-Stack); dann cryptography, pillow, pdfminer-six.

---

## 4. Nächste Schritte (Backlog)

1. **Ruff:** Optional einmal `ruff check api/ routes/ auth/ celery_app/ --fix` ausführen; Baseline in CI/Doku auf neuen Stand setzen. F821/F811/E722 stichprobenartig prüfen.
2. **Bandit:** 2 High-Issues lokalisieren und beheben oder begründet abhaken; B608-Liste nach echten Injection-Stellen durchgehen.
3. **pip-audit:** requirements.txt auf Fix-Versionen aktualisieren und Upgrade testen.
4. **Checkliste Säule E:** Siehe [QUALITAETSCHECK_CHECKLISTE_CONTEXT_SSOT.md](QUALITAETSCHECK_CHECKLISTE_CONTEXT_SSOT.md) – bei Bedarf einmalig durchgehen.

---

## 5. Reproduktion

```bash
cd /opt/greiner-portal
.venv/bin/pip install ruff bandit pip-audit   # falls noch nicht installiert
.venv/bin/ruff check api/ routes/ auth/ celery_app/ --statistics
.venv/bin/bandit -r api/ routes/ auth/ celery_app/ -x .venv --format txt
.venv/bin/pip-audit
```

Oder einheitlich: `./scripts/qa_check.sh` (siehe dort).
