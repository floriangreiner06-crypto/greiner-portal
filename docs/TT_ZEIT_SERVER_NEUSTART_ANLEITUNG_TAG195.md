# TT-Zeit: Server-Neustart Anleitung - TAG 195

**Datum:** 2026-01-16  
**Status:** Server muss manuell neu gestartet werden

---

## ⚠️ WICHTIG

**Der Server muss neu gestartet werden, damit die neue TT-Zeit-Route verfügbar ist!**

---

## 🔄 SERVER NEU STARTEN

### Auf dem Server (10.80.80.20):

```bash
sudo systemctl restart greiner-portal
```

### Status prüfen:

```bash
sudo systemctl status greiner-portal
```

**Erwartet:**
- Status: `active (running)`
- Keine Fehler in Logs

---

## ✅ VERIFIZIERUNG

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
- [ ] Status prüfen: `sudo systemctl status greiner-portal`
- [ ] Route testen (curl)
- [ ] Browser-Refresh (Strg+F5)
- [ ] Erneut testen: "TT-Zeit prüfen" klicken

---

## 🎯 NACH DEM NEUSTART

**Erwartetes Verhalten:**
1. Button "TT-Zeit prüfen" klicken
2. Spinner wird angezeigt
3. Modal öffnet sich mit Analyse-Ergebnissen
4. Keine Fehler in Browser-Konsole

**Falls weiterhin Fehler:**
- Browser-Konsole prüfen (F12)
- Server-Logs prüfen
- Route testen (curl)

---

**Erstellt:** TAG 195  
**Status:** Wartet auf Server-Neustart
