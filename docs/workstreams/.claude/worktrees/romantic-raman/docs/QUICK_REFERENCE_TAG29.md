# 🚀 QUICK REFERENCE - TAG 29

**Status:** ✅ VERKAUF-MODUL PRODUKTIONSREIF  
**Server:** 10.80.80.20  
**Port:** 5000 (unified)

---

## ⚡ TESTING-URLS

```
✅ http://10.80.80.20/verkauf/auftragseingang
✅ http://10.80.80.20/verkauf/auftragseingang/detail
✅ http://10.80.80.20/verkauf/auslieferung/detail
✅ http://10.80.80.20/bankenspiegel/fahrzeugfinanzierungen
```

---

## 🔧 SERVER-BEFEHLE

### Service
```bash
# Status
sudo systemctl status greiner-portal

# Restart
sudo systemctl restart greiner-portal

# Logs
journalctl -u greiner-portal -f
```

### Health-Checks
```bash
curl http://localhost:5000/health
curl http://localhost:5000/api/verkauf/health
```

---

## 📊 NEUE FEATURES

### Filter-Optionen
- **Zeitraum:** Tag/Monat
- **Standort:** Deggendorf (1) / Landau (2)
- **Verkäufer:** Alle (inkl. ehemalige)
- **Kategorien:** Neu/Test/Gebraucht

### API-Endpoints
```
GET /api/verkauf/auftragseingang/summary
GET /api/verkauf/auftragseingang/detail
GET /api/verkauf/auslieferung/summary
GET /api/verkauf/auslieferung/detail
```

---

## 🐛 BUGS GEFIXT

- ✅ Urlaubsplaner 502 → Port unified
- ✅ Fahrzeugfinanzierungen Menü → Hinzugefügt
- ✅ Auftragseingang Detail 404 → APIs erstellt
- ✅ Auslieferungen Detail 404 → APIs erstellt

---

## 💾 GIT-COMMITS

```bash
cd /opt/greiner-portal
./git_commit_tag29.sh
```

---

## 🚨 TROUBLESHOOTING

### 502 Bad Gateway
```bash
sudo ss -tlnp | grep :5000
sudo systemctl status greiner-portal
```

### 404 Not Found
```bash
grep "@.*_bp.route" routes/*.py
journalctl -u greiner-portal -n 50
```

---

**Erstellt:** 11.11.2025  
**Version:** 1.0
