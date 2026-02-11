# TODO FÜR CLAUDE SESSION START - TAG 80

**Letzter Stand:** TAG 79 - Stellantis Zinsen + Locosoft Sync  
**Datum:** 2025-11-24  
**Branch:** feature/controlling-charts-tag71  
**Server:** 10.80.80.20

---

## 🎯 WAS WURDE IN TAG 79 GEMACHT

1. ✅ Stellantis Zinsen-Berechnung (9,03% p.a.) in DB
2. ✅ API angepasst - liest aus DB statt selbst zu berechnen
3. ✅ Import-Script erweitert (automatische Zinsberechnung)
4. ✅ Cron-Jobs geprüft - alle Pfade korrekt
5. ✅ Locosoft-Datenanreicherung analysiert
6. ✅ Neues Script: sync_fahrzeug_stammdaten.py (HSN/TSN Sync)
7. ✅ Cron für Stammdaten-Sync eingerichtet (täglich 9:30)

---

## 📊 AKTUELLE ZINSKOSTEN

| Quelle | Monat | Jahr |
|--------|-------|------|
| Konten Sollzinsen | 528 € | 6.334 € |
| Stellantis (7 Fz über Zinsfreiheit) | 1.805 € | 21.666 € |
| Santander (42 Fz) | 1.894 € | 22.730 € |
| Hyundai (46 Fz) | 2.702 € | 32.418 € |
| **GESAMT** | **6.929 €** | **83.149 €** |

---

## 🎯 TODO TAG 80

### Prio 1: Dashboard-Widget im Frontend
- [ ] Zins-KPI-Widget auf Bankenspiegel-Dashboard
- [ ] Tabelle: Fahrzeuge mit Handlungsbedarf
- [ ] Ampel-System (grün/gelb/rot)

### Prio 2: Weitere Optimierungen
- [ ] Stellantis "bald ablaufend" mit Zinsprognose
- [ ] Export-Funktion für Handlungsbedarf-Liste

---

## 🚀 QUICK-START
```bash
cd /opt/greiner-portal
source venv/bin/activate
git pull

# Zins-API testen
curl -s http://localhost:5000/api/zinsen/dashboard | python3 -m json.tool

# EK-Finanzierung Bestand
sqlite3 data/greiner_controlling.db "
SELECT finanzinstitut, COUNT(*), ROUND(SUM(aktueller_saldo),0), ROUND(SUM(zinsen_gesamt),0)
FROM fahrzeugfinanzierungen GROUP BY finanzinstitut;
"
```

---

## 📁 WICHTIGE DATEIEN

- api/zins_optimierung_api.py - Zins-API
- scripts/imports/import_stellantis.py - Mit Zinsen
- scripts/imports/import_hyundai_finance.py - Mit Zinsen
- scripts/sync/sync_fahrzeug_stammdaten.py - HSN/TSN Sync
- templates/bankenspiegel_dashboard.html - Hier Widget einbauen

---

## 📈 API-ENDPOINTS
```
GET /api/zinsen/dashboard          → KPIs kompakt
GET /api/zinsen/report             → Vollständiger Report
GET /api/zinsen/umbuchung-empfehlung → Umbuchungs-Empfehlungen
```

---

*Erstellt: 24.11.2025*
