# 📋 TODO FÜR CLAUDE SESSION START - TAG 73

**Letzter Stand:** TAG 72 - Stellantis ServiceBox API komplett  
**Datum:** 2025-11-21  
**Branch:** `feature/controlling-charts-tag71`

---

## ✅ STATUS NACH TAG 72

**Stellantis Teilebestellungen:**
- ✅ DB-Schema: `stellantis_bestellungen` + `stellantis_positionen`
- ✅ Import-Script: `scripts/imports/import_stellantis_bestellungen.py`
- ✅ REST-API: `api/stellantis_api.py` (8 Endpoints)
- ✅ 104 Bestellungen importiert (24.806 EUR)
- ✅ Service läuft produktiv

**Was FEHLT:**
- ❌ Frontend/Dashboard für Teilebestellungen
- ❌ Integration in Navigationsmenü
- ❌ After Sales Bereich-Konzept
- ❌ Weitere Datenquellen (Hyundai, Werkstatt)

---

## 🎯 HAUPTAUFGABE TAG 73

**AFTER SALES BEREICH KONZIPIEREN & STARTEN** 🔧

---

## 🏗️ AFTER SALES BEREICH - KONZEPT

### **Was ist After Sales?**

**Greiner ist Händler & Service-Partner für:**
- 🚗 **Opel** (Stellantis)
- 🚗 **Leapmotor** (Stellantis)  
- 🚗 **Hyundai**

**After Sales umfasst:**
```
AFTER SALES
├── 📦 TEILE
│   ├── Bestellungen (Stellantis ServiceBox) ✅ HEUTE FERTIG!
│   ├── Lagerbestand
│   └── Lieferanten
│
├── 🔧 WERKSTATT
│   ├── Reparaturaufträge
│   ├── Mechaniker-Auslastung
│   └── Durchlaufzeiten
│
├── 📋 SERVICE
│   ├── Wartungsverträge
│   ├── Garantie-Abwicklung
│   └── Kundenkommunikation
│
└── 📊 AFTER SALES CONTROLLING
    ├── Umsatz Service/Teile
    ├── Deckungsbeiträge
    └── KPIs (Durchlaufzeit, Auslastung)
```

---

## 🎯 OPTIONEN FÜR TAG 73

### **OPTION A: Frontend für Teilebestellungen (2h)** 🖥️

**Ziel:** Daten sichtbar machen, die wir bereits haben!

**Features:**
- Bestellübersicht-Tabelle (Filter: Datum, Absender, lokale_nr)
- Detail-Ansicht einer Bestellung
- Top-Teile Widget
- Statistik-Cards
- Suche

**Files zu erstellen:**
```
routes/aftersales_routes.py          (Flask Routes)
templates/aftersales/
  ├── teilebestellungen.html          (Übersicht)
  └── bestellung_detail.html          (Detail)
static/
  ├── css/aftersales/teilebestellungen.css
  └── js/aftersales/teilebestellungen.js
```

**Integration:**
- Navigation in `templates/base.html` erweitern
- Neuer Menüpunkt "After Sales" → "Teilebestellungen"

**Zeitaufwand:** ~2h

---

### **OPTION B: Controlling Charts (2h)** 📊

**Ziel:** Ursprüngliches Ziel von TAG 71 nachholen!

**4 Charts für Controlling Dashboard:**
1. Liquiditäts-Verlauf (12 Monate)
2. Umsatz vs. Kosten (Bar Chart)
3. Kosten-Breakdown (Pie Chart)
4. Konten-Übersicht (Horizontal Bar)

**Files zu bearbeiten:**
```
routes/controlling_routes.py           (API-Endpoints für Charts)
templates/controlling/dashboard.html   (Chart.js Integration)
static/js/controlling/dashboard.js     (Chart-Logik)
```

**Zeitaufwand:** ~2h

---

### **OPTION C: After Sales Bereich - Komplett-Setup (4-6h)** 🏗️

**Ziel:** Vollständige After Sales Struktur anlegen!

**Phase 1: Struktur (30 Min)**
```bash
# Verzeichnisse
mkdir -p routes/aftersales
mkdir -p templates/aftersales
mkdir -p static/css/aftersales
mkdir -p static/js/aftersales
mkdir -p api/aftersales

# Files
touch routes/aftersales/__init__.py
touch routes/aftersales/teile_routes.py
touch routes/aftersales/werkstatt_routes.py
touch api/aftersales/__init__.py
touch api/aftersales/teile_api.py
```

**Phase 2: Navigation (30 Min)**
```python
# templates/base.html - Neuer Menüpunkt
<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" id="navbarAfterSales">
        <i class="bi bi-tools"></i> After Sales
    </a>
    <ul class="dropdown-menu">
        <li><a class="dropdown-item" href="/aftersales/teile/bestellungen">
            📦 Teilebestellungen
        </a></li>
        <li><a class="dropdown-item" href="/aftersales/werkstatt">
            🔧 Werkstatt
        </a></li>
        <li><a class="dropdown-item" href="/aftersales/service">
            📋 Service
        </a></li>
        <li><hr class="dropdown-divider"></li>
        <li><a class="dropdown-item" href="/aftersales/controlling">
            📊 After Sales Controlling
        </a></li>
    </ul>
</li>
```

**Phase 3: Teilebestellungen-Frontend (2h)**
- Wie Option A

**Phase 4: Platzhalter für Werkstatt/Service (1h)**
- Einfache "Coming Soon" Seiten
- Struktur vorbereitet

**Phase 5: After Sales Controlling (1,5h)**
- Dashboard mit Umsatz Service/Teile
- Charts aus Locosoft-Daten

**Zeitaufwand:** ~5h (vollständig)

---

### **OPTION D: Mehr Stellantis-Daten importieren (3h)** 📦

**Ziel:** Alle verfügbaren Bestellungen holen!

**Aktuell:** 104 Bestellungen (aus 10 Seiten)
**Verfügbar:** 1.315 Bestellungen (132 Seiten)

**Script anpassen:**
```python
# tools/scrapers/servicebox_detail_scraper_pagination_final.py
MAX_PAGES = 132  # Statt 10
```

**Zeitaufwand:** ~3h (Scraping dauert!)

---

## 💡 EMPFEHLUNG

**Meine Empfehlung: OPTION A** 🖥️

**Warum?**
1. ✅ Wir haben bereits Daten (104 Bestellungen)
2. ✅ API ist fertig (8 Endpoints)
3. ✅ Schneller Erfolg (2h)
4. ✅ Nutzer können Daten sehen
5. ✅ Basis für After Sales Bereich geschaffen

**Danach:** Option B (Controlling Charts) oder Option C (Komplett-Setup)

---

## 📝 QUICK-START FÜR TAG 73

### **1. Session-Start Checks**
```bash
# Server verbinden
ssh ag-admin@10.80.80.20

# Projekt öffnen
cd /opt/greiner-portal
source venv/bin/activate

# Git-Status
git status
git log --oneline -3

# Service-Status
sudo systemctl status greiner-portal

# API testen
curl -s http://localhost:5000/api/stellantis/health | python3 -m json.tool
```

**Erwartung:**
- Branch: `feature/controlling-charts-tag71`
- Letzter Commit: `5c6dac5` (TAG 72)
- Service: active (running)
- API: 104 Bestellungen, 185 Positionen

---

### **2. Datenstand prüfen**
```bash
# Bestellungen
sqlite3 data/greiner_controlling.db "
SELECT 
    COUNT(*) as anzahl,
    MIN(bestelldatum) as aelteste,
    MAX(bestelldatum) as neueste
FROM stellantis_bestellungen;
"

# Positionen mit Preis
sqlite3 data/greiner_controlling.db "
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN preis_ohne_mwst IS NOT NULL THEN 1 END) as mit_preis,
    ROUND(SUM(summe_inkl_mwst), 2) as gesamtwert
FROM stellantis_positionen;
"
```

**Erwartung:**
- 104 Bestellungen (14.11. - 20.11.2025)
- 185 Positionen, 180 mit Preis
- Gesamtwert: 24.806 EUR

---

### **3. Entscheidung treffen**

**Frage den User:**
```
"Welche Option möchtest du für TAG 73?

A) Frontend für Teilebestellungen (2h) - EMPFOHLEN
B) Controlling Charts (2h)
C) After Sales Komplett-Setup (5h)
D) Mehr Daten importieren (3h)

Oder hast du eine andere Idee?"
```

---

## 🎨 DESIGN-HINWEISE (für Option A)

### **Teilebestellungen-Übersicht:**

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  📦 Teilebestellungen - Stellantis ServiceBox       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Filter: Datum] [Absender ▼] [Lokale Nr] [Suche] │
│                                                     │
│  ┌──────┬────────────┬────────┬───────┬──────────┐ │
│  │ Datum│Bestellnr   │Absender│Pos.   │Wert      │ │
│  ├──────┼────────────┼────────┼───────┼──────────┤ │
│  │20.11.│1JAGUMIBU   │BTZ     │1      │199,71 EUR│ │
│  │20.11.│1JAGTE8VI   │BTZ     │1      │210,83 EUR│ │
│  │...   │...         │...     │...    │...       │ │
│  └──────┴────────────┴────────┴───────┴──────────┘ │
│                                                     │
│  📊 Statistik:                                      │
│  ┌─────────────┬─────────────┬─────────────┐       │
│  │104 Best.    │185 Pos.     │24.806 EUR   │       │
│  └─────────────┴─────────────┴─────────────┘       │
└─────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Klick auf Zeile → Detail-Ansicht
- ✅ Filter speichern
- ✅ CSV-Export-Button
- ✅ Refresh-Button

---

## 🔄 AFTER SALES LANGFRIST-VISION

**Zukünftige Integrationen:**

1. **Hyundai Teile** (separate Quelle)
2. **Locosoft Werkstatt-Daten** (Reparaturaufträge aus PostgreSQL)
3. **Service-Verträge** (Wartung, Garantie)
4. **Teile-Lager** (Bestandsführung)
5. **Mechaniker-Dashboard** (Auslastung, Produktivität)

**After Sales Controlling:**
- Umsatz Service vs. Teile
- Deckungsbeiträge
- Durchlaufzeiten
- Kundenzufriedenheit

---

## ⚠️ WICHTIG

### **Branching-Strategie:**

Aktueller Branch: `feature/controlling-charts-tag71`

**Für After Sales:**
```bash
# Option 1: Im aktuellen Branch weiter (schneller)
# Einfach weitermachen

# Option 2: Neuer Branch (sauberer)
git checkout -b feature/aftersales-basis-tag73
git push -u origin feature/aftersales-basis-tag73
```

**Empfehlung:** Im aktuellen Branch bleiben (schneller, später refactoren)

---

## 📚 DOKUMENTATION ZUM LESEN

**Vor Start:**
1. `SESSION_WRAP_UP_TAG72.md` - Was heute passiert ist
2. `docs/FIRMENSTRUKTUR_UPDATE.md` - Greiner Marken & Struktur
3. `PROJECT_OVERVIEW.md` - Allgemeiner Überblick

**Bei Option C (Komplett-Setup):**
4. `docs/DATABASE_SCHEMA.md` - DB-Struktur
5. `LOCOSOFT_POSTGRESQL_DOKUMENTATION.md` - Externe Datenquellen

---

## ✅ DEFINITION OF DONE (für Option A)

- [ ] Route `/aftersales/teile/bestellungen` funktioniert
- [ ] Tabelle zeigt alle 104 Bestellungen
- [ ] Filter funktionieren (Datum, Absender, Suche)
- [ ] Detail-Ansicht zeigt Positionen
- [ ] Statistik-Cards zeigen korrekte Werte
- [ ] Navigation hat "After Sales" Menüpunkt
- [ ] CSV-Export funktioniert
- [ ] Service läuft stabil
- [ ] Git committed & gepusht
- [ ] Session Wrap-Up erstellt

---

## 🎯 ZUSAMMENFASSUNG

**Status:** 
- ✅ Stellantis API fertig (TAG 72)
- ⏳ Frontend fehlt noch
- 💡 After Sales Bereich = Strategische Erweiterung

**Empfehlung:** 
**Option A** - Frontend für Teilebestellungen (2h)
→ Schneller Erfolg, nutzt vorhandene Daten!

**Alternative:** 
Nach User-Wunsch eine andere Option wählen

---

**Branch:** `feature/controlling-charts-tag71`  
**Commit:** `5c6dac5`  
**Nächster Schritt:** User fragen welche Option! 🚀

**LOS GEHT'S!** 🔧
