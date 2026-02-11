# TODO für Claude - Session Start TAG 186

**Datum:** Nach Serviceleiter Rückmeldung von Locosoft  
**Status:** ⏳ Warte auf Locosoft-Rückmeldung

---

## 📋 ÜBERGABE VON TAG 185

### Was wurde erreicht:
- ✅ Locosoft Stempelzeit-Berechnung analysiert
- ✅ "Stmp.Anteil" Berechnung implementiert (Zeit-Spanne - Lücken - Pausen)
- ✅ Leistungsgrad-Berechnung reverse-engineered
- ✅ Umfassende Dokumentation erstellt (6 Dokumente)
- ✅ Alle Dokumente ins Windows-Sync kopiert

### Wichtigste Erkenntnisse:
1. **Locosoft verwendet unterschiedliche Stempelzeiten:**
   - "Stmp.Anteil": 8.483 Min = Zeit-Spanne (erste bis letzte, alle) - Lücken - Pausen
   - Leistungsgrad: 7.846 Min = Zeit-Spanne (erste alle bis letzte externe) - Lücken (10-60 Min, nur extern)

2. **Interne Aufträge werden anders behandelt:**
   - Zeit-Spanne: Erste Stempelung (auch intern) bis letzte externe Stempelung

3. **Pausen werden NICHT für Leistungsgrad abgezogen:**
   - Daher ist der Leistungsgrad in Locosoft höher (145,6% vs. DRIVE 140,8%)

---

## ⏳ OFFENE FRAGEN (Warte auf Locosoft-Rückmeldung)

### 1. Leistungsgrad-Stempelzeit Bestätigung
- **Frage:** Verwendet Locosoft wirklich "erste alle bis letzte externe" - Lücken (10-60 Min)?
- **Serviceleiter fragt bei Locosoft nach:**
  - Wie wird die Stempelzeit für den Leistungsgrad berechnet?
  - Welche Lücken werden abgezogen?
  - Werden Pausen abgezogen?

### 2. Interne Aufträge Behandlung
- **Frage:** Warum zählen interne Aufträge zur ersten Stempelung, aber nicht zur letzten?
- **Serviceleiter fragt bei Locosoft nach:**
  - Wie werden interne Aufträge (Kunde 3000001) behandelt?
  - Zählen sie zur Stempelzeit oder nicht?

### 3. Pausen-Berechnung
- **Frage:** Werden Pausen innerhalb von Stempelungen abgezogen?
- **Serviceleiter fragt bei Locosoft nach:**
  - Wie werden Pausen berechnet?
  - Werden Pausen innerhalb von Stempelungen abgezogen?

---

## 🚀 NÄCHSTE SCHRITTE (Nach Locosoft-Rückmeldung)

### Priorität HOCH:
1. ⏳ **Locosoft-Rückmeldung abwarten**
   - Was hat der Serviceleiter herausgefunden?
   - Bestätigen sich unsere Hypothesen?
   - Gibt es neue Erkenntnisse?

2. ⏳ **Leistungsgrad-Stempelzeit implementieren**
   - Wenn Locosoft-Berechnung bestätigt wurde
   - Formel: Zeit-Spanne (erste alle bis letzte externe) - Lücken (10-60 Min, nur extern)
   - Separate Berechnung für Leistungsgrad vs. "Stmp.Anteil"

### Priorität MITTEL:
3. ⏳ **Interne Aufträge Behandlung anpassen**
   - Wenn Locosoft-Bestätigung vorliegt
   - Zeit-Spanne-Berechnung anpassen

4. ⏳ **Pausen-Berechnung verfeinern**
   - Wenn Locosoft-Bestätigung vorliegt
   - Pausen innerhalb Stempelungen behandeln

### Priorität NIEDRIG:
5. ⏳ **Validierung mit weiteren Mitarbeitern**
   - Wenn Implementierung abgeschlossen
   - Weitere Mitarbeiter testen
   - Monatsvergleiche durchführen

---

## 📁 WICHTIGE DATEIEN

### Dokumentation (Windows Sync):
- `ANALYSE_STEMPELZEITEN_ABWEICHUNG_JAN_TAG185.md` - Dezember-Analyse
- `ANALYSE_STEMPELZEITEN_NOVEMBER_JAN_TAG185.md` - November-Analyse
- `ANALYSE_INTERNE_AUFTRAEGE_LOCOSOFT_TAG185.md` - Interne Aufträge Analyse
- `ANALYSE_LEISTUNGSGRAD_LOCOSOFT_TAG185.md` - Leistungsgrad Reverse Engineering
- `ZUSAMMENFASSUNG_LOCOSOFT_BEREchnung_TAG185.md` - Zusammenfassung
- `IMPLEMENTIERUNG_LOCOSOFT_STEMPELZEITEN_TAG185.md` - Implementierung

### Code:
- `api/werkstatt_data.py` - Locosoft-Stempelzeit-Berechnung
- `utils/kpi_definitions.py` - SSOT für KPI-Berechnungen

---

## 💡 ERINNERUNG

**Serviceleiter fragt bei Locosoft nach:**
- Alle Dokumente sind im Windows-Sync verfügbar
- Reverse Engineering zeigt: 7.846 Min für Leistungsgrad (nur 2 Min Abweichung!)
- Warte auf Bestätigung von Locosoft

**Aktueller Stand:**
- ✅ "Stmp.Anteil" Berechnung implementiert
- ⚠️ Leistungsgrad-Stempelzeit noch nicht implementiert (andere Logik)
- ⏳ Warte auf Locosoft-Rückmeldung

---

*Erstellt: TAG 185 | Autor: Claude AI*
