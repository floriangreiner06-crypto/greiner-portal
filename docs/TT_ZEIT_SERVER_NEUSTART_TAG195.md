# TT-Zeit: Server-Neustart erforderlich - TAG 195

**Datum:** 2026-01-16  
**Problem:** Route gibt 404 zurück

---

## ⚠️ PROBLEM

**Fehler:** 404 Not Found bei `/api/ai/analysiere/tt-zeit/<id>`

**Ursache:**
- Python-Code wurde geändert (`api/ai_api.py`)
- Server wurde nicht neu gestartet
- Neue Route ist nicht aktiv

---

## ✅ LÖSUNG

### Server neu starten:

```bash
sudo systemctl restart greiner-portal
```

**Wichtig:** Nach Änderungen an Python-Dateien ist Neustart erforderlich!

---

## 🔍 VERIFIZIERUNG

### 1. Prüfe ob Route verfügbar ist:

```bash
curl -X POST http://localhost:5000/api/ai/analysiere/tt-zeit/22073 \
  -H "Content-Type: application/json" \
  -v
```

**Erwartet:**
- Status: 200 oder 401 (nicht 404!)
- Content-Type: application/json

### 2. Prüfe Server-Logs:

```bash
journalctl -u greiner-portal -f --no-pager | grep -i "ai\|tt-zeit"
```

**Suche nach:**
- `✅ AI API (LM Studio) registriert`
- Keine Fehler bei `ai_api`

---

## 📋 CHECKLISTE

- [ ] Server neu starten: `sudo systemctl restart greiner-portal`
- [ ] Route testen (curl)
- [ ] Browser-Refresh (Strg+F5)
- [ ] Erneut testen

---

**Erstellt:** TAG 195  
**Status:** Server-Neustart erforderlich
