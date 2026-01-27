# e-autoseller KPI Dashboard - Vorschläge für Verkaufsleitung

**Datum:** 2026-01-23  
**Status:** Vorschlag für Erweiterungen  
**Basis:** Aktuelles e-autoseller Live-Bestand Dashboard

---

## 📊 Aktuelle KPIs (Bereits vorhanden)

### Übersicht-Widgets
- ✅ **Verkäufe (Widget 202):** 4 - "Aus eAutoseller"
- ✅ **Bestand (Widget 203):** 35 - "Aktive Fahrzeuge"
- ✅ **Anfragen (Widget 204):** 10 - "Offene Anfragen"
- ✅ **Pipeline (Widget 205):** 32 - "In Bearbeitung"

### Standzeit-Analyse
- ✅ **Gesamt Fahrzeuge:** 367
- ✅ **OK (< 30 Tage):** 86
- ✅ **Warnung (30-60 Tage):** 60
- ✅ **Kritisch (> 60 Tage):** 221

---

## 🎯 Vorgeschlagene Erweiterungen

### 1. Erweiterte KPI-Widgets

#### 1.1 Umsatz-KPIs
```
┌─────────────────────────────────┐
│ Gesamtumsatz (Monat)            │
│ 1.245.680,00 €                  │
│ ↗ +12% vs. Vormonat             │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Durchschnittspreis              │
│ 28.450,00 €                     │
│ ↘ -3% vs. Vormonat              │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Lagerwert (Aktive Fahrzeuge)    │
│ 995.750,00 €                    │
│ (35 Fahrzeuge × Ø-Preis)        │
└─────────────────────────────────┘
```

#### 1.2 Performance-KPIs
```
┌─────────────────────────────────┐
│ Durchschnittliche Standzeit     │
│ 127 Tage                        │
│ (Gesamt / Anzahl Fahrzeuge)     │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Umschlagshäufigkeit             │
│ 2,3x pro Jahr                   │
│ (Verkäufe / Durchschnittsbestand)│
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Verkaufsrate                    │
│ 10,9%                           │
│ (Verkäufe / Bestand)            │
└─────────────────────────────────┘
```

#### 1.3 Markt-KPIs
```
┌─────────────────────────────────┐
│ Marktanteil (eAutoseller)       │
│ 15,2%                           │
│ (Unsere Verkäufe / Markt)       │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Durchschnittliche Antwortzeit   │
│ 2,3 Stunden                     │
│ (Anfragen → Kontakt)             │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Konversionsrate                 │
│ 28,6%                           │
│ (Verkäufe / Anfragen)           │
└─────────────────────────────────┘
```

#### 1.4 Risiko-KPIs
```
┌─────────────────────────────────┐
│ Kritische Fahrzeuge (Wert)      │
│ 6.285.450,00 €                  │
│ (221 Fahrzeuge × Ø-Preis)       │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Potenzielle Abschreibung        │
│ 125.709,00 €                    │
│ (2% p.a. × kritische Fahrzeuge) │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Durchschnittliche Standzeit     │
│ Kritische Fahrzeuge: 289 Tage   │
│ (Nur > 60 Tage)                 │
└─────────────────────────────────┘
```

---

### 2. Drill-Down Funktionalitäten

#### 2.1 Klickbare Widgets
- **Klick auf "Kritisch (221)":**
  - Filtert Tabelle automatisch auf kritische Fahrzeuge
  - Zeigt zusätzliche Spalte "Potenzielle Abschreibung"
  - Sortiert nach Standzeit (längste zuerst)

- **Klick auf "Verkäufe (4)":**
  - Zeigt Liste der verkauften Fahrzeuge
  - Mit Verkaufsdatum, Preis, Käufer
  - Vergleich mit Einkaufspreis (Gewinn)

- **Klick auf "Anfragen (10)":**
  - Zeigt offene Anfragen
  - Mit Kontaktdaten, Interessiertes Fahrzeug
  - Status: Neu, In Bearbeitung, Angebot erstellt

- **Klick auf "Pipeline (32)":**
  - Zeigt Fahrzeuge in Verhandlung
  - Mit Verkaufschance (%), Erwartetes Verkaufsdatum
  - Zuordnung zu Verkäufer

#### 2.2 Erweiterte Filter
```
┌─────────────────────────────────────────────┐
│ Filter:                                     │
│                                             │
│ [ ] Marke: [Alle ▼]                        │
│ [ ] Preis: [Min: ___] [Max: ___]           │
│ [ ] Kilometerstand: [Min: ___] [Max: ___]  │
│ [ ] Baujahr: [Von: ___] [Bis: ___]         │
│ [ ] Kraftstoff: [Alle ▼]                   │
│ [ ] Verkäufer: [Alle ▼]                    │
│                                             │
│ [ ] Nur mit Bildern                        │
│ [ ] Nur reservierte                        │
│ [ ] Nur verfügbare                         │
│                                             │
│ [Filter anwenden] [Zurücksetzen]           │
└─────────────────────────────────────────────┘
```

---

### 3. Trend-Analysen

#### 3.1 Zeitreihen-Diagramme
```
┌─────────────────────────────────────────────┐
│ Verkäufe (letzte 12 Monate)                │
│                                             │
│  [Line Chart: Monatliche Verkäufe]        │
│  Trend: ↗ Steigend                         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Bestandsentwicklung (letzte 12 Monate)     │
│                                             │
│  [Area Chart: Bestand über Zeit]           │
│  Trend: ↘ Leicht fallend                   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Standzeit-Verteilung (letzte 12 Monate)    │
│                                             │
│  [Stacked Bar Chart: OK/Warnung/Kritisch]  │
│  Trend: ⚠ Kritische Fahrzeuge steigen      │
└─────────────────────────────────────────────┘
```

#### 3.2 Vergleichs-KPIs
```
┌─────────────────────────────────────────────┐
│ Vergleich: Aktuell vs. Vormonat            │
│                                             │
│ Verkäufe:     4  →  5  (+25%)              │
│ Bestand:     35  →  38  (+8,6%)            │
│ Anfragen:    10  →  12  (+20%)              │
│ Pipeline:    32  →  28  (-12,5%)            │
│                                             │
│ Kritisch:   221  →  215  (-2,7%) ✅         │
└─────────────────────────────────────────────┘
```

---

### 4. Aktionen & Workflows

#### 4.1 Schnellaktionen in Tabelle
```
┌─────────────────────────────────────────────┐
│ Fahrzeugliste                                │
│                                             │
│ [Marke] [Modell] [Preis] [Standzeit] [Aktionen]
│ Opel    Corsa   26.165€  289 Tage  [📧] [💰] [📊]
│                                             │
│ Aktionen:                                    │
│ 📧 E-Mail an Verkäufer senden              │
│ 💰 Preisvorschlag anzeigen                 │
│ 📊 Statistiken anzeigen                     │
│ 🖼️ Bilder hochladen                        │
│ 📝 Notiz hinzufügen                         │
└─────────────────────────────────────────────┘
```

#### 4.2 Bulk-Aktionen
```
┌─────────────────────────────────────────────┐
│ Ausgewählte Fahrzeuge (5):                 │
│                                             │
│ [ ] Alle auswählen                          │
│                                             │
│ Aktionen:                                   │
│ [ ] Preis reduzieren um: [___]%             │
│ [ ] Marktplatz aktualisieren                │
│ [ ] E-Mail-Kampagne starten                 │
│ [ ] Exportieren (Excel/PDF)                 │
│                                             │
│ [Aktionen ausführen]                        │
└─────────────────────────────────────────────┘
```

#### 4.3 Automatisierte Aktionen
- **Automatische E-Mail-Benachrichtigungen:**
  - Täglich: Liste kritischer Fahrzeuge (> 60 Tage)
  - Wöchentlich: Zusammenfassung Verkäufe, Bestand, Pipeline
  - Bei Status-Änderung: Benachrichtigung bei Verkauf/Reservierung

- **Preisvorschläge:**
  - Automatische Preisvorschläge basierend auf:
    - Marktpreisen (eAutoseller API)
    - Standzeit
    - Marktlage
  - Vorschlag anzeigen, manuell bestätigen

---

### 5. Reporting & Export

#### 5.1 Vordefinierte Reports
```
┌─────────────────────────────────────────────┐
│ Reports:                                     │
│                                             │
│ 📊 Tagesbericht                              │
│    - Verkäufe heute                          │
│    - Neue Anfragen                           │
│    - Kritische Fahrzeuge                     │
│                                             │
│ 📊 Wochenbericht                             │
│    - Verkäufe Woche                          │
│    - Bestandsentwicklung                     │
│    - Top 10 Verkäufer                        │
│                                             │
│ 📊 Monatsbericht                             │
│    - Umsatz & Verkäufe                       │
│    - Bestandsanalyse                         │
│    - Standzeit-Verteilung                    │
│                                             │
│ 📊 Quartalsbericht                           │
│    - Vollständige Analyse                    │
│    - Trends & Prognosen                      │
│    - Vergleich Vorjahr                       │
└─────────────────────────────────────────────┘
```

#### 5.2 Export-Funktionen
- **Excel-Export:**
  - Gefilterte Fahrzeugliste
  - Mit allen Spalten
  - Formatierte für weitere Analyse

- **PDF-Export:**
  - Professioneller Report
  - Mit Charts & Diagrammen
  - Für Präsentationen

- **CSV-Export:**
  - Für Datenimport in andere Systeme
  - Kompatibel mit Excel, Power BI, etc.

---

### 6. Benutzerdefinierte Dashboards

#### 6.1 Dashboard-Konfiguration
```
┌─────────────────────────────────────────────┐
│ Dashboard anpassen                          │
│                                             │
│ Verfügbare Widgets:                         │
│                                             │
│ ☑ Verkäufe (Monat)                          │
│ ☑ Bestand (Aktive Fahrzeuge)                │
│ ☑ Anfragen (Offen)                          │
│ ☑ Pipeline (In Bearbeitung)                 │
│ ☐ Umsatz (Monat)                            │
│ ☐ Durchschnittspreis                        │
│ ☐ Lagerwert                                 │
│ ☐ Durchschnittliche Standzeit               │
│ ☐ Verkaufsrate                              │
│ ☐ Konversionsrate                           │
│ ☐ Kritische Fahrzeuge (Wert)                │
│ ☐ Potenzielle Abschreibung                  │
│                                             │
│ [Speichern] [Zurücksetzen]                  │
└─────────────────────────────────────────────┘
```

#### 6.2 Rollenbasierte Dashboards
- **Verkaufsleiter:**
  - Alle KPIs
  - Vollständige Übersicht
  - Alle Aktionen

- **Verkäufer:**
  - Eigene Pipeline
  - Zugewiesene Fahrzeuge
  - Eigene Verkäufe

- **Controlling:**
  - Finanz-KPIs
  - Lagerwert
  - Abschreibungen

---

### 7. Intelligente Insights

#### 7.1 Automatische Empfehlungen
```
┌─────────────────────────────────────────────┐
│ 💡 Empfehlungen                             │
│                                             │
│ ⚠ 15 Fahrzeuge nähern sich 60-Tage-Marke  │
│    → Preisreduktion empfehlen               │
│                                             │
│ ✅ 3 Fahrzeuge haben hohe Anfrage-Rate      │
│    → Verfügbarkeit prüfen                   │
│                                             │
│ 📈 Verkäufe steigen um 25%                  │
│    → Bestand aufstocken?                    │
│                                             │
│ ⚠ Durchschnittliche Standzeit steigt        │
│    → Verkaufsstrategie überprüfen           │
└─────────────────────────────────────────────┘
```

#### 7.2 Prognosen
```
┌─────────────────────────────────────────────┐
│ 📊 Prognosen (nächste 30 Tage)              │
│                                             │
│ Erwartete Verkäufe: 12-15                  │
│ (Basierend auf historischen Daten)          │
│                                             │
│ Erwartete neue Anfragen: 25-30              │
│                                             │
│ Kritische Fahrzeuge (prognostiziert): 235   │
│ (Wenn keine Maßnahmen ergriffen werden)     │
└─────────────────────────────────────────────┘
```

---

## 🎯 Priorisierung

### PRIO 1 (Sofort umsetzbar) ⭐⭐⭐
1. **Erweiterte KPI-Widgets:**
   - Durchschnittliche Standzeit
   - Lagerwert (Aktive Fahrzeuge)
   - Verkaufsrate
   - Kritische Fahrzeuge (Wert)

2. **Drill-Down:**
   - Klickbare Widgets → Filtert Tabelle
   - Erweiterte Filter (Marke, Preis, etc.)

3. **Export:**
   - Excel-Export der Fahrzeugliste
   - PDF-Report (einfach)

### PRIO 2 (Kurzfristig) ⭐⭐
4. **Trend-Analysen:**
   - Zeitreihen-Diagramme (Chart.js)
   - Vergleich Vormonat

5. **Aktionen:**
   - Schnellaktionen in Tabelle
   - Bulk-Aktionen

6. **Reporting:**
   - Tages-/Wochen-/Monatsbericht
   - Automatische E-Mail-Benachrichtigungen

### PRIO 3 (Mittelfristig) ⭐
7. **Intelligente Insights:**
   - Automatische Empfehlungen
   - Prognosen

8. **Benutzerdefinierte Dashboards:**
   - Widget-Auswahl
   - Rollenbasierte Dashboards

---

## 💻 Technische Umsetzung

### Backend (API)
```python
# api/eautoseller_api.py

@eautoseller_api.route('/kpis/extended', methods=['GET'])
def get_extended_kpis():
    """Erweiterte KPIs für Dashboard"""
    # Berechne zusätzliche KPIs
    # - Durchschnittliche Standzeit
    # - Lagerwert
    # - Verkaufsrate
    # etc.
    pass

@eautoseller_api.route('/trends', methods=['GET'])
def get_trends():
    """Trend-Daten für Diagramme"""
    # Zeitreihen-Daten
    pass

@eautoseller_api.route('/insights', methods=['GET'])
def get_insights():
    """Intelligente Insights & Empfehlungen"""
    # Automatische Analysen
    pass
```

### Frontend (Templates)
```javascript
// templates/verkauf_eautoseller_bestand.html

// Chart.js für Diagramme
// Interaktive Widgets
// Drill-Down Funktionalität
// Export-Funktionen
```

---

## 📊 Beispiel-Dashboard-Layout

```
┌─────────────────────────────────────────────────────────────┐
│ eAutoseller KPI Dashboard - Verkaufsleitung                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ [Verkäufe] [Bestand] [Anfragen] [Pipeline]                  │
│    4         35        10         32                         │
│                                                               │
│ [Umsatz] [Ø-Preis] [Lagerwert] [Verkaufsrate]               │
│ 1.245k€   28.450€   995.750€     10,9%                      │
│                                                               │
│ [Gesamt] [OK] [Warnung] [Kritisch]                          │
│   367      86     60       221                               │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Trend: Verkäufe (letzte 12 Monate)                     │ │
│ │ [Line Chart]                                            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 💡 Empfehlungen                                         │ │
│ │ ⚠ 15 Fahrzeuge nähern sich 60-Tage-Marke               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ [Fahrzeugliste mit Filtern und Aktionen]                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Nächste Schritte

1. **Anforderungen sammeln:**
   - Welche KPIs sind am wichtigsten?
   - Welche Funktionalitäten werden am dringendsten benötigt?

2. **Prototyp erstellen:**
   - PRIO 1 Features implementieren
   - Testen mit Verkaufsleitung

3. **Iterative Verbesserung:**
   - Feedback einholen
   - PRIO 2 & 3 Features nach Bedarf

---

**Status:** Vorschlag erstellt  
**Nächster Schritt:** Anforderungen mit Verkaufsleitung besprechen
