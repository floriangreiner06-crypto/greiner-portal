# TODO TAG 97 - ML Werkstatt Intelligence Weiterentwicklung

**Erstellt:** 2025-12-06  
**Priorität:** Hoch  
**Abhängigkeit:** TAG 96 abgeschlossen ✅

---

## 🎯 ZIELE TAG 97

### PRIO 1: Dashboard-Verbesserungen
- [ ] Mechaniker-Namen statt Nummern anzeigen (JOIN mit employees)
- [ ] Ranking-Filter auf gefilterte Daten umstellen (API nutzt noch alle)
- [ ] Mechaniker-Dropdown im Vorhersage-Tool mit echten Namen
- [ ] Link im Menü unter "After Sales" hinzufügen

### PRIO 2: TecDoc/TecRMI Integration prüfen
- [ ] Mit Florian klären ob Zugang vorhanden
- [ ] Falls ja: Schnittstelle recherchieren
- [ ] Hersteller-Vorgaben als Benchmark einbinden

### PRIO 3: Datenqualitäts-Report für HR/Werkstattleiter
- [ ] Report-Seite erstellen: Wer stempelt unplausibel?
- [ ] Export als Excel für HR
- [ ] Samstags-Arbeitszeiten in Locosoft korrigieren lassen

### PRIO 4: Weitere ML-Modelle (optional)
- [ ] Upselling-Empfehlung (welche Teile werden oft zusammen verbaut?)
- [ ] HU/AU Reminder (Fahrzeuge mit fälligen Terminen)
- [ ] Wiederkehr-Prognose (wann kommt Kunde wieder?)

---

## 📋 TECHNISCHE TODOS

### API-Verbesserungen
```python
# ml_api.py - Mechaniker-Namen hinzufügen
# Bei mechaniker-ranking: JOIN mit employees-Tabelle
# Response erweitern: mechaniker_name zusätzlich zu mechaniker_nr
```

### Frontend-Verbesserungen
```javascript
// werkstatt_intelligence.html
// Dropdown mit echten Mechanikern aus /api/ml/mechaniker-ranking füllen
// Namen statt Nummern im Ranking anzeigen
```

### Menü-Integration
```python
# In base.html oder Navigation:
# After Sales → Werkstatt Intelligence hinzufügen
```

---

## 🔧 OFFENE BUGS

1. **Ranking zeigt gefilterte Mechaniker (5027, 1014)**
   - Ursache: `/api/ml/mechaniker-ranking` lädt CSV ohne Filter
   - Fix: Direkt aus DB laden ODER nur plausible aus CSV

2. **Statistik zeigt 19 Mechaniker statt 11**
   - Ursache: `/api/ml/statistik` lädt alte CSV
   - Fix: V2-CSV verwenden oder `modell_performance` aktualisieren

---

## 📂 RELEVANTE DATEIEN

```
api/ml_api.py                              # API anpassen
templates/werkstatt_intelligence.html      # Frontend anpassen
scripts/ml/prepare_werkstatt_ml_data_v2.py # Daten-Export (falls Anpassung)
data/ml/mechaniker_qualitaet.csv           # Qualitäts-Report für HR
docs/SESSION_WRAP_UP_TAG96.md              # Kontext
```

---

## ⚠️ WORKFLOW-REMINDER

1. **IMMER im Sync-Verzeichnis arbeiten:**
   ```
   \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\
   ```

2. **NIE rsync komplett ausführen!** Nur einzelne Dateien kopieren:
   ```bash
   cp /mnt/greiner-portal-sync/[datei] /opt/greiner-portal/[datei]
   ```

3. **Nach Änderungen:**
   ```bash
   sudo systemctl restart greiner-portal
   ```

4. **Locosoft-Credentials:**
   ```
   Host: 10.80.80.8
   DB: loco_auswertung_db
   User: loco_auswertung_benutzer
   Password: loco
   ```
