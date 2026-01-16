# TT-Zeit Fehlerbehebung - TAG 195

**Datum:** 2026-01-16  
**Problem:** "Unexpected token '<', "<!doctype "... is not valid JSON"

---

## 🔍 PROBLEM

**Fehlermeldung:**
```
Fehler: Unexpected token '<', "<!doctype "... is not valid JSON
```

**Ursache:**
- API gibt HTML statt JSON zurück
- Passiert bei:
  - 404 (Route nicht gefunden)
  - 500 (Server-Fehler)
  - 401/403 (Nicht autorisiert)

---

## ✅ LÖSUNG

### 1. Fehlerbehandlung verbessert

**Datei:** `templates/aftersales/garantie_auftraege_uebersicht.html`

**Änderung:**
- Prüft `Content-Type` Header
- Zeigt bessere Fehlermeldung wenn HTML zurückgegeben wird
- Gibt Hinweise zur Fehlerbehebung

### 2. Mögliche Ursachen prüfen

**A) Route nicht registriert:**
```bash
# Prüfe ob AI API registriert ist
grep -n "ai_api" /opt/greiner-portal/app.py
```

**B) Server nicht neu gestartet:**
```bash
# Server neu starten (nach Python-Änderungen)
sudo systemctl restart greiner-portal
```

**C) Python-Fehler in API:**
```bash
# Logs prüfen
journalctl -u greiner-portal -f --no-pager | tail -50
```

---

## 🔧 FEHLERBEHEBUNG

### Schritt 1: Server-Logs prüfen

```bash
journalctl -u greiner-portal -f --no-pager | tail -50
```

**Suche nach:**
- `ai_api` - Ist Blueprint geladen?
- `TT-Zeit` - Gibt es Fehler?
- `Traceback` - Python-Fehler?

### Schritt 2: Route testen

```bash
# Test API-Endpoint direkt
curl -X POST http://localhost:5000/api/ai/analysiere/tt-zeit/22073 \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -v
```

**Erwartete Antwort:**
- `Content-Type: application/json`
- JSON-Response mit `success: true/false`

### Schritt 3: Server neu starten

**Wenn Python-Code geändert wurde:**
```bash
sudo systemctl restart greiner-portal
```

**Wichtig:** Nach Änderungen an `api/ai_api.py` ist Neustart erforderlich!

---

## 📋 CHECKLISTE

- [ ] Server-Logs prüfen
- [ ] Route testen (curl)
- [ ] Server neu starten (falls nötig)
- [ ] Browser-Refresh (Strg+F5)
- [ ] Erneut testen

---

## 🎯 HÄUFIGE FEHLER

### Fehler 1: Route nicht gefunden (404)

**Symptom:** HTML-Fehlerseite statt JSON

**Lösung:**
- Prüfe ob Blueprint registriert ist
- Prüfe URL-Pfad: `/api/ai/analysiere/tt-zeit/<id>`

### Fehler 2: Server-Fehler (500)

**Symptom:** HTML-Fehlerseite statt JSON

**Lösung:**
- Logs prüfen
- Python-Fehler beheben
- Server neu starten

### Fehler 3: Nicht autorisiert (401/403)

**Symptom:** HTML-Login-Seite statt JSON

**Lösung:**
- Session prüfen
- Login erforderlich

---

## 📝 VERBESSERTE FEHLERMELDUNG

**Neue Fehlermeldung zeigt:**
- Klare Beschreibung des Problems
- Hinweise zur Fehlerbehebung
- Link zu Server-Logs

**Beispiel:**
```
Fehler bei TT-Zeit-Analyse: Server-Fehler: API hat HTML statt JSON zurückgegeben. Bitte Server-Logs prüfen.

Bitte prüfen Sie:
- Ist der Server gestartet?
- Gibt es Fehler in den Server-Logs?
```

---

**Erstellt:** TAG 195  
**Status:** Fehlerbehandlung verbessert
