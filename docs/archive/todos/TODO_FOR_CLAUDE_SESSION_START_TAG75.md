# 📋 TODO FÜR CLAUDE SESSION START - TAG 75

**Letzter Stand:** TAG 74 - After Sales Teilebestellungen gefixt ✅  
**Datum:** 24. November 2025  
**Branch:** `feature/controlling-charts-tag71`

---

## 🎯 HAUPTZIEL: QUALITÄTS-CHECK

### 🐛 BUG 1: Login-Seite Verhalten
**Problem:** Login-Seite bleibt geöffnet und öffnet neues Fenster
**Erwartung:** Nach Login sollte nur das Portal offen sein, Login-Fenster schließen

**Zu prüfen:**
- `templates/login.html` - JavaScript nach Login
- `auth/auth_manager.py` - Redirect-Logik
- `app.py` - Login-Route

---

### 🐛 BUG 2: Urlaubsplaner - Alter Stand
**Problem:** Urlaubsplaner zeigt veraltete Daten/Design
**Erwartung:** Urlaubsplaner V2 sollte aktuell sein

**Zu prüfen:**
- Welches Template wird verwendet? (`urlaubsplaner.html` vs `urlaubsplaner_v2.html`)
- Route in `app.py` oder `routes/`
- Datenbank-Stand (vacation_entitlements, vacation_bookings)

---

### 🐛 BUG 3: Keine Top-Navigation
**Problem:** Navigation fehlt auf bestimmten Seiten
**Erwartung:** Alle Seiten sollten die Top-Navigation haben

**Zu prüfen:**
- Welche Seiten betroffen?
- Erben diese von `base.html`?
- Block-Struktur korrekt?

---

## 🔍 DEBUG-PLAN

### STEP 1: Login-Problem analysieren
```bash
# Login-Template prüfen
grep -n "window.open\|target=\|redirect\|location" templates/login.html

# Login-Route prüfen
grep -n "login\|redirect" app.py | head -20
```

### STEP 2: Urlaubsplaner prüfen
```bash
# Welche Route wird verwendet?
grep -n "urlaubsplaner" app.py routes/*.py

# Welches Template?
ls -la templates/urlaubsplaner*.html
```

### STEP 3: Navigation prüfen
```bash
# Welche Templates erben NICHT von base.html?
grep -L "extends.*base" templates/*.html
```

---

## ✅ DEFINITION OF DONE - TAG 75

- [ ] Login öffnet kein neues Fenster mehr
- [ ] Urlaubsplaner zeigt aktuellen Stand
- [ ] Alle Seiten haben Top-Navigation
- [ ] Alles getestet im Browser
- [ ] Git committed

---

**Branch:** `feature/controlling-charts-tag71`  
**Fokus:** Qualitäts-Check & Bug-Fixes
