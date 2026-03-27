# TODO FÜR CLAUDE SESSION START - TAG 79

**Letzter Stand:** TAG 78 - Hyundai Zinsen + API  
**Datum:** 2025-11-24  
**Branch:** feature/controlling-charts-tag71

---

## 🎯 WAS WURDE IN TAG 78 GEMACHT

1. ✅ Hyundai CSV-Pfad korrigiert
2. ✅ Hyundai Zinsen-Berechnung (4,68% p.a.)
3. ✅ Zins-API erweitert mit Hyundai

### Aktuelle Zinskosten:
| Quelle | Monat | Jahr |
|--------|-------|------|
| Konten Sollzinsen | 528 € | 6.334 € |
| Stellantis (7 Fz über Zinsfreiheit) | 1.831 € | 21.966 € |
| Santander (42 Fz) | 1.894 € | 22.730 € |
| Hyundai (24 Fz mit Zinsen) | 2.702 € | 32.418 € |
| **GESAMT** | **6.954 €** | **83.449 €** |

---

## 📊 HANDLUNGSBEDARF

- **7 Stellantis-Fahrzeuge** über Zinsfreiheit (243k€)
- **15 Stellantis-Fahrzeuge** bald ablaufend (<14 Tage, 416k€)
- **24 Hyundai-Fahrzeuge** mit laufenden Zinsen

---

## 🎯 TODO TAG 79

### Prio 1: Dashboard-Widget im Frontend
- [ ] Zins-KPI-Widget auf Bankenspiegel-Dashboard
- [ ] Tabelle: Fahrzeuge mit Handlungsbedarf
- [ ] Ampel-System für Status

### Prio 2: Stellantis Zinsen in DB
- [ ] `import_stellantis.py` erweitern
- [ ] Zinsen für Fahrzeuge über Zinsfreiheit berechnen
- [ ] In `zinsen_gesamt` speichern

### Prio 3: Cron-Job Pfade prüfen
- [ ] Sicherstellen dass alle Pfade korrekt sind
- [ ] Logging verbessern

---

## 🚀 QUICK-START
```bash
cd /opt/greiner-portal
source venv/bin/activate
git pull

# Status prüfen
curl -s http://localhost:5000/api/zinsen/dashboard | python3 -m json.tool

# EK-Finanzierung Bestand
sqlite3 data/greiner_controlling.db "
SELECT finanzinstitut, COUNT(*), ROUND(SUM(aktueller_saldo),0), ROUND(SUM(zinsen_gesamt),0)
FROM fahrzeugfinanzierungen GROUP BY finanzinstitut;
"
```

---

## 📁 WICHTIGE DATEIEN
```
api/zins_optimierung_api.py              ← Zins-API (TAG 78)
scripts/imports/import_hyundai_finance.py ← Mit Zinsen (TAG 78)
scripts/imports/import_stellantis.py      ← Noch ohne Zinsen
docs/SESSION_WRAP_UP_TAG78.md            ← Letzte Session
```

---

## 💡 WICHTIGE ERKENNTNISSE

1. **Korrekter Hyundai-Pfad:**
```
   /mnt/buchhaltung/Buchhaltung/Kontoauszüge/HyundaiFinance/
```

2. **Hyundai Zinssatz:** 4,68% p.a. (aus ek_finanzierung_konditionen)

3. **Stellantis Zinssatz:** 9,03% p.a.

4. **Santander Zinssätze:** 4-5,5% (variabel, aus CSV)
