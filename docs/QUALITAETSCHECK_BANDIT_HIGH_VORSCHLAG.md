# Vorschlag: Abarbeitung der 2 Bandit-High-Findings

**Stand:** 2026-02-24  
**Referenz:** [QUALITAETSCHECK_ERGEBNIS_2026-02-24.md](QUALITAETSCHECK_ERGEBNIS_2026-02-24.md)

---

## Übersicht

| # | Bandit-ID | Datei:Zeile | Kurzbeschreibung |
|---|-----------|-------------|------------------|
| 1 | B324 (hashlib) | `api/jahrespraemie_api.py:639` | MD5-Hash ohne `usedforsecurity=False` |
| 2 | B201 (flask_debug_true) | `routes/app.py:354` | `app.run(..., debug=True)` |

---

## 1. B324 – MD5 in `api/jahrespraemie_api.py`

**Kontext:** MD5 wird für einen **Datei-Inhalt-Hash** genutzt (Lohnjournal-Upload), um Duplikate/Änderungen zu erkennen – **nicht** für Passwörter oder kryptographische Sicherheit.

**Empfehlung:** Bandit-Fix umsetzen: `usedforsecurity=False` setzen. Das kennzeichnet den Aufruf als nicht sicherheitsrelevant und unterdrückt die Warnung; MD5 für Datei-Checksums ist in dem Kontext unkritisch.

**Änderung (eine Zeile):**

```python
# Vorher
file_hash = hashlib.md5(open(temp_path, 'rb').read()).hexdigest()

# Nachher
file_hash = hashlib.md5(open(temp_path, 'rb').read(), usedforsecurity=False).hexdigest()
```

**Hinweis:** `hashlib.md5(data, usedforsecurity=False)` ist ab Python 3.9 verfügbar; Projekt nutzt Python 3.12 → unkritisch.

---

## 2. B201 – `debug=True` in `routes/app.py`

**Kontext:** Die Zeile steht unter `if __name__ == '__main__':` – sie wird nur ausgeführt, wenn die App direkt gestartet wird (z. B. `python -m routes.app` oder direkter Aufruf). **Produktion** läuft über Gunicorn ohne diesen Block; der Debugger ist dort nicht aktiv.

**Risiko:** Falls jemand auf dem Server versehentlich die App direkt startet, wäre der Werkzeug-Debugger erreichbar (Code-Ausführung möglich). Besser: Debug nur per Konfiguration aktivieren und standardmäßig aus.

**Empfehlung:** Debug über Umgebungsvariable steuern, Default `False`:

```python
# Vorher
app.run(host='0.0.0.0', port=5000, debug=True)

# Nachher (z. B.)
import os
DEBUG = os.environ.get('FLASK_DEBUG', '0').strip().lower() in ('1', 'true', 'yes')
app.run(host='0.0.0.0', port=5000, debug=DEBUG)
```

Falls `os` im File weiter oben schon importiert ist, nur die zwei Zeilen mit `DEBUG` und `app.run(..., debug=DEBUG)` anpassen.

**Alternativ (minimal):** Einfach `debug=False` setzen und bei Bedarf lokal manuell auf `True` stellen. Dann verschwindet die Bandit-Warnung; direkter Start ohne FLASK_DEBUG wäre immer ohne Debugger.

---

## 3. Reihenfolge & Aufwand

| Finding | Aufwand | Risiko bei Änderung |
|---------|---------|----------------------|
| B324 (MD5) | 1 Zeile | Keins – reine Kennzeichnung |
| B201 (debug) | 2–3 Zeilen | Keins – Verhalten nur bei direktem Start; Prod unverändert |

Beide Änderungen können sofort umgesetzt werden. Danach erneut `bandit -r api/ routes/ auth/ celery_app/ -x .venv` ausführen; die 2 High-Findings sollten weg sein.

---

## 4. Umsetzung (2026-02-24)

- **B324:** In `api/jahrespraemie_api.py` wurde `usedforsecurity=False` ergänzt.
- **B201:** In `routes/app.py` wird `debug` aus der Umgebungsvariable `FLASK_DEBUG` gelesen (Default `0`/aus). Für lokalen Debug: `FLASK_DEBUG=1` setzen.

Nach erneutem Bandit-Lauf sollten die 2 High-Findings verschwinden.
