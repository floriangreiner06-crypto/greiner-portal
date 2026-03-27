# ✅ ACTION ITEMS - TAG 29

**Datum:** 11.11.2025  
**Status:** Verkauf-Modul PRODUKTIONSREIF

---

## 🚀 SOFORT (HEUTE)

### 1. Git-Commits durchführen ⏱️ 10 Min

```bash
cd /opt/greiner-portal
source venv/bin/activate
chmod +x git_commit_tag29.sh
./git_commit_tag29.sh
```

**Checklist:**
- [ ] Commit 1: Port-Config
- [ ] Commit 2: Navigation
- [ ] Commit 3: Verkauf-Detail
- [ ] Push to origin

---

### 2. System-Status prüfen ⏱️ 5 Min

```bash
sudo systemctl status greiner-portal
curl http://localhost:5000/health
curl http://localhost:5000/api/verkauf/health
```

**Checklist:**
- [ ] Service läuft
- [ ] Health-Check OK
- [ ] Keine Fehler in Logs

---

## 📊 DIESE WOCHE

### 3. User-Testing vorbereiten ⏱️ 30 Min

**Test-URLs:**
```
✅ http://10.80.80.20/verkauf/auftragseingang
✅ http://10.80.80.20/verkauf/auftragseingang/detail
✅ http://10.80.80.20/verkauf/auslieferung/detail
```

**Checklist:**
- [ ] Verkaufsleitung kontaktiert
- [ ] Termin für Live-Demo
- [ ] Präsentation vorbereitet

---

### 4. Live-Demo durchführen ⏱️ 1 Std

**Agenda:**
1. Überblick (5 Min)
2. Dashboard zeigen (10 Min)
3. Filter demonstrieren (15 Min)
4. Detail-Ansichten (15 Min)
5. Q&A (10 Min)
6. Feedback (5 Min)

---

### 5. Feedback auswerten ⏱️ 1 Std

**Kategorien:**
- [ ] Funktionalität OK?
- [ ] Performance OK?
- [ ] Usability gut?
- [ ] Fehlende Features?

---

## 🔄 NÄCHSTE WOCHE

### 6. Feedback umsetzen

**Option A:** Kleine Anpassungen (<2h)
**Option B:** Neue Features (>2h)

---

### 7. Entscheidung nächste Features

- **Option A:** Urlaubsplaner (~4h)
- **Option B:** Automatisierung (1-2d)
- **Option C:** Weitere Verkauf-Features

---

## 📋 MANUELLE GIT-COMMITS

Falls Script nicht funktioniert:

```bash
# Commit 1
git add config/gunicorn.conf.py install_nginx_config.sh greiner-portal.conf
git commit -m "fix(config): Unified port 5000"

# Commit 2
git add templates/base.html
git commit -m "feat(nav): Add Fahrzeugfinanzierungen"

# Commit 3
git add routes/verkauf_routes.py api/verkauf_api.py
git commit -m "feat(verkauf): Complete detail views"

# Push
git push origin feature/bankenspiegel-komplett
```

---

**Erstellt:** 11.11.2025  
**Status:** ✅ READY TO EXECUTE
