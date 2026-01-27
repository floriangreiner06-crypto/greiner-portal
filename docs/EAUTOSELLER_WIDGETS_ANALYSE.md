# e-autoseller Widgets - Analyse & Verbesserungsvorschläge

**Datum:** 2026-01-23  
**Status:** Analyse der aktuellen Widgets

---

## 📊 Aktuelle Widgets - Erklärung

### Reihe 1: eAutoseller KPIs (aus startdata.asp)
✅ **Diese sind sinnvoll:**
- **Verkäufe (Widget 202):** 4 - Anzahl verkaufter Fahrzeuge
- **Bestand (Widget 203):** 35 - Aktive Fahrzeuge (verkaufsbereit)
- **Anfragen (Widget 204):** 10 - Offene Kundenanfragen
- **Pipeline (Widget 205):** 32 - Fahrzeuge in Verhandlung

**Bedeutung:** Direkt aus eAutoseller, zeigen aktuelle Verkaufsaktivität.

---

### Reihe 2: Standzeit-Analyse
✅ **Diese sind sinnvoll:**
- **Gesamt Fahrzeuge:** 367 - Alle Fahrzeuge im System
- **OK (< 30 Tage):** 86 - Kurze Standzeit, gut
- **Warnung (30-60 Tage):** 60 - Mittlere Standzeit, beobachten
- **Kritisch (> 60 Tage):** 221 - Lange Standzeit, Handlungsbedarf

**Bedeutung:** Zeigt Altersstruktur des Bestands, wichtig für Lageroptimierung.

**Problem:** "Gesamt Fahrzeuge" (367) vs. "Bestand" (35) - Was ist der Unterschied?
- **Bestand (35):** Aktive, verkaufsbereite Fahrzeuge
- **Gesamt (367):** Alle Fahrzeuge (inkl. in Vorbereitung, reserviert, etc.)

---

### Reihe 3: Erweiterte KPIs - PROBLEME

#### ❌ **Ø Standzeit: 127 Tage**
**Berechnung:** Durchschnitt aller 367 Fahrzeuge
**Problem:** 
- Mischt aktive (35) mit inaktiven Fahrzeugen
- Sollte nur aktive Fahrzeuge berücksichtigen
- Oder: "Ø Standzeit (Aktive)" vs. "Ø Standzeit (Gesamt)"

#### ❌ **Lagerwert: ~9,6 Mio. €**
**Berechnung:** Summe aller Preise (367 Fahrzeuge)
**Problem:**
- Enthält auch inaktive/reservierte Fahrzeuge
- Sollte nur aktive Fahrzeuge (35) berücksichtigen
- Oder: "Lagerwert (Aktive)" vs. "Lagerwert (Gesamt)"

#### ❌ **Verkaufsrate: 1,1%**
**Berechnung:** Verkäufe (4) / Gesamt (367) = 1,1%
**Problem:**
- Falsch! Sollte sein: Verkäufe (4) / Bestand (35) = 11,4%
- Oder: Verkäufe (4) / Gesamt (367) = 1,1% (aber dann ist es "Umschlagshäufigkeit", nicht "Verkaufsrate")

#### ⚠️ **Kritisch (Wert): ~6,3 Mio. €**
**Berechnung:** Summe der Preise aller kritischen Fahrzeuge (221)
**Bedeutung:** Potenzieller Wertverlust
**Problem:**
- Enthält auch inaktive kritische Fahrzeuge
- Sollte nur aktive kritische Fahrzeuge berücksichtigen
- Oder: "Kritisch (Wert) - Aktive" vs. "Kritisch (Wert) - Gesamt"

#### ⚠️ **Ø Preis: ~26.000 €**
**Berechnung:** Durchschnittspreis aller 367 Fahrzeuge
**Problem:**
- Enthält auch inaktive Fahrzeuge
- Sollte nur aktive Fahrzeuge berücksichtigen
- Oder: "Ø Preis (Aktive)" vs. "Ø Preis (Gesamt)"

#### ❌ **Pot. Abschreibung: ~99.000 €**
**Berechnung:** 2% p.a. auf kritische Fahrzeuge (Wert)
**Problem:**
- 2% p.a. ist sehr grob geschätzt
- Berücksichtigt nicht tatsächliche Standzeit
- Sollte sein: 2% × (Standzeit / 365) × Wert
- Oder: Realistischere Abschreibung basierend auf tatsächlicher Standzeit

---

## 🎯 Verbesserungsvorschläge

### Option 1: Nur aktive Fahrzeuge berücksichtigen
**Änderung:** Alle Berechnungen nur für aktive Fahrzeuge (35)

**Vorteile:**
- ✅ Realistischere Werte
- ✅ Fokus auf verkaufsbereite Fahrzeuge
- ✅ Verkaufsrate wird korrekt (4/35 = 11,4%)

**Nachteile:**
- ❌ Verliert Übersicht über Gesamtbestand

### Option 2: Zwei Spalten (Aktive vs. Gesamt)
**Änderung:** Jedes Widget zeigt zwei Werte

**Beispiel:**
```
┌─────────────────────────────────┐
│ Lagerwert                       │
│ Aktive: 995.750 € (35 Fahrzeuge)│
│ Gesamt: 9.600.000 € (367 Fahrzeuge)│
└─────────────────────────────────┘
```

**Vorteile:**
- ✅ Vollständige Übersicht
- ✅ Klare Unterscheidung

**Nachteile:**
- ❌ Mehr Platz benötigt
- ❌ Komplexer

### Option 3: Fokus auf relevante KPIs
**Änderung:** Nur die wichtigsten KPIs anzeigen

**Empfohlene Widgets:**
1. ✅ **Verkäufe** (4) - Aus eAutoseller
2. ✅ **Bestand** (35) - Aktive Fahrzeuge
3. ✅ **Anfragen** (10) - Offene Anfragen
4. ✅ **Pipeline** (32) - In Verhandlung
5. ✅ **Kritisch** (221) - Anzahl kritischer Fahrzeuge
6. ✅ **Kritisch (Wert)** - Nur aktive kritische Fahrzeuge
7. ✅ **Lagerwert (Aktive)** - Nur aktive Fahrzeuge
8. ✅ **Verkaufsrate** - Verkäufe / Bestand (korrekt berechnet)

**Entfernen:**
- ❌ Ø Standzeit (zu abstrakt)
- ❌ Ø Preis (wenig aussagekräftig)
- ❌ Pot. Abschreibung (zu grob geschätzt)

---

## 💡 Konkrete Verbesserungen

### 1. Lagerwert korrigieren
**Aktuell:** Summe aller 367 Fahrzeuge
**Soll:** Summe nur aktiver Fahrzeuge (35)

### 2. Verkaufsrate korrigieren
**Aktuell:** Verkäufe (4) / Gesamt (367) = 1,1%
**Soll:** Verkäufe (4) / Bestand (35) = 11,4%

### 3. Kritisch (Wert) korrigieren
**Aktuell:** Summe aller kritischen Fahrzeuge (221)
**Soll:** Summe nur aktiver kritischer Fahrzeuge

### 4. Ø Standzeit präzisieren
**Aktuell:** Durchschnitt aller 367 Fahrzeuge
**Soll:** Durchschnitt nur aktiver Fahrzeuge
**Oder:** Entfernen (zu abstrakt)

### 5. Pot. Abschreibung verbessern
**Aktuell:** 2% p.a. auf kritische Fahrzeuge
**Soll:** 2% × (tatsächliche Standzeit / 365) × Wert
**Oder:** Entfernen (zu grob geschätzt)

### 6. Ø Preis präzisieren
**Aktuell:** Durchschnitt aller 367 Fahrzeuge
**Soll:** Durchschnitt nur aktiver Fahrzeuge
**Oder:** Entfernen (wenig aussagekräftig)

---

## 🔧 Empfohlene Lösung

### Fokus auf relevante KPIs für Verkaufsleitung:

**Reihe 1: eAutoseller KPIs (bleibt)**
- Verkäufe, Bestand, Anfragen, Pipeline

**Reihe 2: Standzeit-Analyse (bleibt)**
- Gesamt, OK, Warnung, Kritisch

**Reihe 3: Finanz-KPIs (korrigiert)**
- **Lagerwert (Aktive):** Nur aktive Fahrzeuge
- **Kritisch (Wert - Aktive):** Nur aktive kritische Fahrzeuge
- **Verkaufsrate:** Verkäufe / Bestand (korrekt)
- **Umschlagshäufigkeit:** Verkäufe / Gesamt (optional)

**Entfernen:**
- Ø Standzeit (zu abstrakt)
- Ø Preis (wenig aussagekräftig)
- Pot. Abschreibung (zu grob)

---

## 📝 Nächste Schritte

1. **Welche Widgets sind wichtig?**
   - Welche KPIs nutzt die Verkaufsleitung wirklich?
   - Welche können entfernt werden?

2. **Berechnungen korrigieren:**
   - Nur aktive Fahrzeuge berücksichtigen?
   - Oder zwei Spalten (Aktive vs. Gesamt)?

3. **Beschriftungen verbessern:**
   - Klarstellen was "Aktive" vs. "Gesamt" bedeutet
   - Tooltips hinzufügen

---

**Status:** Analyse abgeschlossen, wartet auf Feedback
