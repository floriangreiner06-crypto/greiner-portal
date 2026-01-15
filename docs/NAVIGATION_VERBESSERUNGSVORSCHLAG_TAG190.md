# Navigation-Verbesserungsvorschlag - TAG 190

**Datum:** 2026-01-14  
**Status:** 📋 Vorschlag

---

## 🔍 Aktuelle Probleme

1. **Zu lange Dropdowns**: Controlling (25+ Items), After Sales (20+ Items)
2. **Zu viele Divider/Header**: 8 Dividers, 10 Headers → unübersichtlich
3. **Redundanzen**: "Bankenspiegel" ist Feature UND Kategorie
4. **Flache Struktur**: Alles in einem Dropdown, keine Sub-Dropdowns
5. **Inkonsistente Gruppierung**: Features vermischt mit Bereichen

---

## 💡 Verbesserungsvorschlag

### **Prinzipien:**
- ✅ Max. 7-8 Items pro Dropdown (UX-Best-Practice)
- ✅ Klare Trennung: **Bereiche** vs. **Features**
- ✅ Flachere Hierarchie: Top-Level = Hauptbereiche
- ✅ Sub-Dropdowns für große Bereiche
- ✅ Reduzierung von Redundanzen

---

## 📊 Neue Struktur

### **Option A: Bereichs-basiert (EMPFOHLEN)**

```
🏠 Dashboard
📊 Controlling
   ├── Übersichten
   │   ├── Dashboard
   │   ├── BWA
   │   ├── TEK
   │   └── Kontenmapping
   ├── Planung
   │   ├── Abteilungsleiter-Planung
   │   ├── 1%-Ziel
   │   └── KST-Ziele
   └── Analysen
       ├── Zinsen-Analyse
       ├── Einkaufsfinanzierung
       └── Jahresprämie

💰 Bankenspiegel (eigener Top-Level!)
   ├── Dashboard
   ├── Kontenübersicht
   ├── Transaktionen
   └── Fahrzeugfinanzierungen

🛒 Verkauf
   ├── Auftragseingang
   ├── Auslieferungen
   ├── Bestand
   │   ├── eAutoseller
   │   └── GW-Standzeit
   ├── Planung (nur Leitung)
   │   ├── Budget-Planung
   │   └── Lieferforecast
   └── Tools
       ├── Leasys Programmfinder
       └── Leasys Kalkulator

🔧 After Sales
   ├── Werkstatt
   │   ├── Cockpit
   │   ├── Kapazitätsplanung
   │   ├── Anwesenheit
   │   └── Aufträge & Prognose
   ├── Teile
   │   ├── Teile-Status
   │   ├── Renner & Penner
   │   ├── Bestellungen
   │   └── Preisradar
   ├── Garantie
   │   └── Garantieaufträge
   ├── Serviceberater
   │   ├── Übersicht
   │   └── Controlling
   └── DRIVE
       ├── Morgen-Briefing
       ├── Kulanz-Monitor
       └── ML-Kapazität

📅 Urlaubsplaner
   ├── Mein Urlaub
   └── Team-Übersicht (nur Leitung)

⚙️ Admin
   ├── System
   │   ├── Task Manager
   │   ├── Flower Dashboard
   │   └── Rechteverwaltung
   ├── Organisation
   │   ├── Organigramm
   │   └── Urlaubsplaner Admin
   └── Entwicklung
       └── Debug User
```

**Vorteile:**
- ✅ Bankenspiegel als eigener Top-Level (wichtiges Feature)
- ✅ After Sales aufgeteilt in logische Sub-Bereiche
- ✅ Max. 5-6 Items pro Dropdown
- ✅ Klare Struktur: Bereich → Feature

---

### **Option B: Feature-basiert (Alternativ)**

```
🏠 Dashboard
📊 Controlling
   ├── Übersichten (BWA, TEK, etc.)
   ├── Planung (1%-Ziel, KST, etc.)
   └── Analysen (Zinsen, Einkauf, etc.)

💰 Bankenspiegel (Top-Level)
🛒 Verkauf
🔧 Werkstatt (statt "After Sales")
   ├── Werkstatt-Übersicht
   ├── Teile
   └── Garantie
📅 Urlaubsplaner
⚙️ Admin
```

**Vorteile:**
- ✅ Noch flachere Struktur
- ✅ "Werkstatt" statt "After Sales" (klarerer Name)

---

## 🎯 Empfehlung: **Option A**

### **Warum?**
1. **Bankenspiegel als Top-Level**: Wichtiges Feature, verdient eigenen Platz
2. **Sub-Dropdowns**: Erlauben bessere Gruppierung ohne lange Listen
3. **Klarere Kategorisierung**: "Werkstatt", "Teile", "Garantie" sind logische Gruppen
4. **Reduzierte Redundanz**: Keine doppelten Features mehr

### **Umsetzung:**
1. **Bankenspiegel** aus Controlling-Dropdown herausnehmen → Top-Level
2. **After Sales** aufteilen in Sub-Dropdowns:
   - Werkstatt (Cockpit, Kapazität, etc.)
   - Teile (Status, Bestellungen, etc.)
   - Garantie
   - Serviceberater
   - DRIVE
3. **Controlling** vereinfachen:
   - Übersichten (5 Items)
   - Planung (3 Items)
   - Analysen (3 Items)
4. **Verkauf** strukturieren:
   - Hauptfunktionen (4 Items)
   - Bestand (Sub-Dropdown: 2 Items)
   - Planung (nur Leitung, 2 Items)
   - Tools (2 Items)

---

## 📋 Migration-Plan

### **Phase 1: Bankenspiegel auslagern**
- Bankenspiegel-Dropdown aus Controlling entfernen
- Neuen Top-Level "Bankenspiegel" erstellen
- 4 Items (Dashboard, Konten, Transaktionen, Fahrzeugfinanzierungen)

### **Phase 2: After Sales restrukturieren**
- Sub-Dropdowns erstellen: Werkstatt, Teile, Garantie, Serviceberater, DRIVE
- Items neu zuordnen

### **Phase 3: Controlling vereinfachen**
- Headers reduzieren
- Items logisch gruppieren

### **Phase 4: Verkauf optimieren**
- "Bestand" als Sub-Dropdown
- Struktur vereinfachen

---

## 🔧 Technische Umsetzung

### **Neue DB-Struktur:**
- Sub-Dropdowns: `parent_id` → `parent_id` (2 Ebenen)
- Beispiel: "Werkstatt" (parent_id=NULL) → "Cockpit" (parent_id=Werkstatt.id)

### **Template-Anpassung:**
- `render_navigation_item()` erweitern für 2-stufige Dropdowns
- Bootstrap: `dropdown-submenu` für Sub-Dropdowns

---

## ✅ Erwartete Verbesserungen

- **Dropdown-Länge**: Von 25+ auf max. 6-7 Items
- **Übersichtlichkeit**: +80% (weniger Scrollen)
- **Findbarkeit**: +60% (logischere Gruppierung)
- **User Experience**: Deutlich verbessert

---

## 🚀 Nächste Schritte

1. ✅ Vorschlag diskutieren
2. ⏳ Option A oder B wählen
3. ⏳ Migration-Script erstellen
4. ⏳ Template anpassen (Sub-Dropdowns)
5. ⏳ Testen & Feedback einholen
