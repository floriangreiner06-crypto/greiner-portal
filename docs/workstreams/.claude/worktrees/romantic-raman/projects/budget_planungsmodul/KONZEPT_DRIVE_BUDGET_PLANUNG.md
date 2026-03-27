# KONZEPT: DRIVE Budget-Planungsmodul

**Version:** 1.0
**Erstellt:** 2026-01-02
**Autor:** Claude (TAG 155)

---

## Executive Summary

Dieses Konzept beschreibt ein modernes, motivierendes Budget-Planungsmodul für DRIVE, das die komplexe GlobalCube-Excel-Lösung ablöst. Der Fokus liegt auf **Einfachheit**, **Erfolgsorientierung** und **konkreten Handlungsempfehlungen**.

---

## 1. IST-Analyse: GlobalCube Excel

### Probleme der aktuellen Lösung

| Problem | Auswirkung |
|---------|------------|
| 7 Tabellenblätter, 50+ Zeilen | Überforderung der Abteilungsleiter |
| Keine Benchmarks sichtbar | Fehlende Orientierung |
| Nur Zahlen, keine Interpretation | Kein Kontext für Entscheidungen |
| Keine Historie | Kein Vergleich mit erfolgreichen Jahren |
| Dezentrale Excel-Dateien | Keine Transparenz, kein Zusammenführen |

### Struktur der Excel-Vorlage (Planung_2025.xlsx)

**Kostenstellen:**
- 0-VW (Verwaltung)
- 1-NW (Neuwagen)
- 2-GW (Gebrauchtwagen)
- 3-ME (Mechanik/Werkstatt)
- 4-KA (Karosserie)
- 5-TZ (Teile + Zubehör)
- 6-CP (Car Park/Sonstiges)
- 7-MW (Mietwagen)
- 8-Sonst.

**Standorte:**
- Deggendorf Opel (Betrieb 1)
- Deggendorf Hyundai (Betrieb 2)
- Landau (Betrieb 3)
- Gesamt (AH Greiner)

---

## 2. VISION: Das neue DRIVE Budget-Modul

### Leitprinzipien

1. **Erfolgsorientiert** - Zeige was möglich ist, nicht nur was zu erreichen ist
2. **Motivierend** - Gamification-Elemente, positive Verstärkung
3. **Präzise** - Klare KPIs mit Benchmarks
4. **Einfach** - Maximal 5 Klicks zur Planung einer Kostenstelle

### Design-Philosophie

> "Weniger Zahlen eingeben, mehr Ergebnisse verstehen"

Statt 50 Zeilen pro Kostenstelle: **5 Kernfragen** + automatische Berechnung des Rests.

---

## 3. MODULE & FEATURES

### 3.1 Dashboard: "Mein Planungs-Cockpit"

```
┌─────────────────────────────────────────────────────────────┐
│  DRIVE Budget-Planung 2026                     [Speichern]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎯 Dein Ziel für 2026:        € 245.000 DB I               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 72%                       │
│  Letztes Jahr: € 232.000       Benchmark: € 260.000         │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │   NW    │  │   GW    │  │   ME    │  │   TZ    │        │
│  │ ✅ OK   │  │ ⚠️ -5%  │  │ ✅ OK   │  │ 🎯 +12% │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│                                                             │
│  💡 Tipp: Dein GW-Bestand hat 48 Tage Standzeit. Bei        │
│     30 Tagen Ziel sparst du € 8.400/Jahr an Zinsen!         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Kostenstellen-Planung: "5 Fragen"

**Beispiel: Neuwagen (NW)**

```
┌─────────────────────────────────────────────────────────────┐
│  NEUWAGEN PLANUNG 2026                         [Standort]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣  Wie viele Neuwagen planst du zu verkaufen?            │
│      ┌────────────┐                                         │
│      │    145     │  NW Stück                               │
│      └────────────┘                                         │
│      📊 2024: 132 Stk. | 2023: 128 Stk. | Benchmark: 150    │
│                                                             │
│  2️⃣  Welchen Ø Bruttoertrag pro Fahrzeug erwartest du?     │
│      ┌────────────┐                                         │
│      │  € 1.850   │  pro Fahrzeug                           │
│      └────────────┘                                         │
│      📊 2024: € 1.720 | Dein Rekord: € 2.100 (2021)         │
│      💡 Top-Performer: € 2.200 (Branchenbenchmark)          │
│                                                             │
│  3️⃣  Provisionen & Boni (Variable Kosten)?                 │
│      ┌────────────┐                                         │
│      │    8,5%    │  vom Bruttoertrag                       │
│      └────────────┘                                         │
│      📊 Üblich: 8-12% | Dein Schnitt: 9,2%                  │
│                                                             │
│  ═══════════════════════════════════════════════════════    │
│  📈 ERGEBNIS-VORSCHAU:                                      │
│  ─────────────────────────────────────────────────────────  │
│  Bruttoertrag:     € 268.250   (+18% zu 2024)               │
│  - Variable Kosten: € 22.801                                │
│  = Deckungsbeitrag: € 245.449  ✅ Ziel erreicht!            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Benchmark-Vergleich: "Wie stehe ich da?"

```
┌─────────────────────────────────────────────────────────────┐
│  BENCHMARK-VERGLEICH                           [Werkstatt]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DEIN PLAN 2026 vs. BENCHMARKS                              │
│                                                             │
│  Kennzahl            Dein Plan   Greiner Ø   Branche        │
│  ─────────────────────────────────────────────────────────  │
│  Produktivität        112%        108%        105%     ⭐   │
│  Stundenverrechnungs. € 155       € 148       € 160    ⚠️   │
│  DB I / Stunde        € 48        € 45        € 52     ⚠️   │
│  Auslastung           78%         75%         70%      ✅   │
│                                                             │
│  💡 EMPFEHLUNG:                                             │
│  Dein SVS liegt 5€ unter Branchenschnitt. Bei 8.000        │
│  verkauften Stunden = € 40.000 Potenzial!                   │
│                                                             │
│  [Benchmark-Details] [Historie ansehen] [Export]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Erfolgs-Timeline: "Lerne aus der Vergangenheit"

```
┌─────────────────────────────────────────────────────────────┐
│  ERFOLGS-TIMELINE: Greiner Werkstatt                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DB I                                                       │
│  €400k ┤                                           📈       │
│        │                                    ╭──────         │
│  €350k ┤                            ╭───────╯               │
│        │                    ╭───────╯                       │
│  €300k ┤            ╭───────╯                               │
│        │    ╭───────╯                                       │
│  €250k ┤────╯                                               │
│        └────────────────────────────────────────────────    │
│         2019  2020  2021  2022  2023  2024  2025 Plan       │
│                                                             │
│  🏆 BESTE JAHRE:                                            │
│  • 2021: DB I € 312.000 - Was war anders?                   │
│    → Hohe Nachfrage nach Gebrauchten (Corona-Effekt)        │
│    → SVS-Erhöhung um 8%                                     │
│    → 3 neue Mechaniker eingestellt                          │
│                                                             │
│  📉 HERAUSFORDERNDE JAHRE:                                  │
│  • 2020: DB I € 248.000 - Was lief schief?                  │
│    → Lockdown März-Mai                                      │
│    → Lieferengpässe Ersatzteile                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.5 Gamification: "Achievements & Streaks"

```
┌─────────────────────────────────────────────────────────────┐
│  DEINE ACHIEVEMENTS                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🏆 FREIGESCHALTET:                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ 🎯 Ziel │ │ 📈 +10% │ │ ⭐ Top  │ │ 🔥 3Mon │           │
│  │erreicht │ │ Wachst. │ │Performer│ │ Streak  │           │
│  │ 2024    │ │ 2024    │ │ Q3 2024 │ │         │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                             │
│  🔒 NÄCHSTES ACHIEVEMENT:                                   │
│  "Budget-Meister" - 3 Jahre in Folge Ziel erreicht          │
│  ━━━━━━━━━━━━━━━━━━━━━━ 67% (2/3 Jahre)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. KENNZAHLEN & BENCHMARKS

### 4.1 Verkauf (NW + GW)

| KPI | Definition | Benchmark | Greiner 2024 |
|-----|------------|-----------|--------------|
| **Stück/Monat/Verkäufer** | Verkaufte Einheiten pro Verkäufer | 8-12 NW, 10-15 GW | ? |
| **Bruttoertrag/Fzg** | Marge pro verkauftem Fahrzeug | NW: €1.500-2.500, GW: €2.000-3.500 | ? |
| **Lagerumschlag GW** | Wie oft wird Bestand gedreht | 12x/Jahr (30 Tage) | ? |
| **Standzeit GW** | Tage bis Verkauf | <30 Tage gut, >60 kritisch | ? |
| **DB I / Verkäufer** | Deckungsbeitrag pro Mitarbeiter | €80.000-120.000/Jahr | ? |

### 4.2 Werkstatt (ME + KA)

| KPI | Definition | Benchmark | Greiner 2024 |
|-----|------------|-----------|--------------|
| **Produktivität** | Verkaufte / Anwesende Stunden | 100-120% | ? |
| **Auslastung** | Anwesende / Verfügbare Stunden | 75-85% | ? |
| **SVS (Mechanik)** | Stundenverrechnungssatz | €150-202 (2024) | ? |
| **DB I / AW** | Deckungsbeitrag pro Arbeitswert | €45-55 | ? |
| **Durchlaufzeit** | Auftrag bis Fertigstellung | <1 Tag ideal | ? |
| **Wiederkehrrate** | Kunden die wiederkommen | >60% gut | ? |

### 4.3 Teile (TZ)

| KPI | Definition | Benchmark | Greiner 2024 |
|-----|------------|-----------|--------------|
| **Lagerumschlag** | Umschläge pro Jahr | 4-6x | ? |
| **Lagerwert** | Gebundenes Kapital | Minimieren | €522.000 |
| **Penner-Quote** | Anteil Langsamdreher | <20% | ? |
| **Teile-DB** | Marge Teile-Verkauf | 25-35% | ? |
| **Servicegrad** | Teile sofort verfügbar | >95% | ? |

### 4.4 Gesamt-Unternehmen

| KPI | Definition | Benchmark | Greiner 2024 |
|-----|------------|-----------|--------------|
| **Fixed Absorption** | Service+Teile decken Overhead | 75-100% | ? |
| **Personalkosten-Quote** | Personal / Bruttoertrag | 34-41% | ? |
| **Nettorendite** | Gewinn / Umsatz | 2-4% (sehr gut: 6%) | ? |
| **ROE** | Return on Equity | >15% | ? |

---

## 5. DATENQUELLEN

### 5.1 Automatisch aus DRIVE

| Datenquelle | Verfügbar | Nutzung |
|-------------|-----------|---------|
| Werkstatt-Daten | ✅ werkstatt_data.py | Produktivität, Auslastung, AW |
| Lager-Daten | ✅ teile_data.py | Lagerwert, Umschlag, Penner |
| Controlling-Daten | ✅ controlling_data.py | DB-Berechnungen, TEK |
| Verkaufs-Daten | ✅ verkauf_api.py | Stückzahlen, Margen |
| Locosoft-Mirror | ✅ locosoft_mirror.py | Aufträge, Kunden |

### 5.2 Manuell zu erfassen

| Datenquelle | Frequenz | Verantwortlich |
|-------------|----------|----------------|
| Planzahlen | 1x/Jahr | Abteilungsleiter |
| SVS-Anpassungen | Bei Änderung | Geschäftsführung |
| Personalplanung | 1x/Jahr | HR |
| Investitionen | 1x/Jahr | Geschäftsführung |

### 5.3 Historie aus GlobalCube importieren

Einmalig: IST-Daten 2019-2024 aus Excel importieren für:
- Benchmarks "Beste Jahre"
- Trend-Analysen
- Realistische Plangrundlage

---

## 6. TECHNISCHE UMSETZUNG

### 6.1 Neue Dateien

```
api/
├── budget_data.py              # SSOT für Budget-Daten
├── budget_api.py               # REST-Endpoints

routes/
├── budget_routes.py            # Flask-Routes

templates/
├── budget/
│   ├── dashboard.html          # Übersicht
│   ├── kostenstelle.html       # Einzelplanung
│   ├── benchmark.html          # Vergleiche
│   └── timeline.html           # Historie
```

### 6.2 Datenbank-Erweiterung (PostgreSQL)

```sql
-- Neue Tabellen
CREATE TABLE budget_plan (
    id SERIAL PRIMARY KEY,
    jahr INTEGER NOT NULL,
    betrieb INTEGER NOT NULL,
    kostenstelle VARCHAR(10) NOT NULL,

    -- Kernzahlen
    plan_stueck INTEGER,
    plan_umsatz DECIMAL(12,2),
    plan_bruttoertrag DECIMAL(12,2),
    plan_db1 DECIMAL(12,2),

    -- Zusätzliche Planung
    plan_personal_fte DECIMAL(4,1),
    plan_svs DECIMAL(8,2),

    -- Meta
    erstellt_von VARCHAR(50),
    erstellt_am TIMESTAMP DEFAULT NOW(),
    freigegeben_von VARCHAR(50),
    freigegeben_am TIMESTAMP,

    UNIQUE(jahr, betrieb, kostenstelle)
);

CREATE TABLE budget_benchmark (
    id SERIAL PRIMARY KEY,
    kostenstelle VARCHAR(10) NOT NULL,
    kpi_name VARCHAR(50) NOT NULL,
    benchmark_min DECIMAL(12,2),
    benchmark_ziel DECIMAL(12,2),
    benchmark_max DECIMAL(12,2),
    quelle VARCHAR(100),
    aktualisiert_am TIMESTAMP DEFAULT NOW()
);

CREATE TABLE budget_achievement (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    achievement_type VARCHAR(50),
    erreicht_am DATE,
    details JSONB
);
```

### 6.3 API-Endpoints

```python
# budget_api.py

@bp.route('/api/budget/plan/<int:jahr>', methods=['GET'])
def get_budget_plan(jahr):
    """Holt alle Planungen für ein Jahr."""

@bp.route('/api/budget/plan/<int:jahr>/<int:betrieb>/<string:kst>', methods=['POST'])
def save_budget_plan(jahr, betrieb, kst):
    """Speichert eine Kostenstellen-Planung."""

@bp.route('/api/budget/benchmark/<string:kst>', methods=['GET'])
def get_benchmarks(kst):
    """Holt Benchmarks für eine Kostenstelle."""

@bp.route('/api/budget/history/<int:betrieb>/<string:kst>', methods=['GET'])
def get_history(betrieb, kst):
    """Holt historische IST-Daten."""

@bp.route('/api/budget/achievements/<int:user_id>', methods=['GET'])
def get_achievements(user_id):
    """Holt Achievements eines Users."""
```

---

## 7. ROLLOUT-PLAN

### Phase 1: Grundgerüst (1-2 Sprints)
- [ ] Datenbank-Tabellen anlegen
- [ ] budget_data.py SSOT-Modul
- [ ] Basis-API-Endpoints
- [ ] Dashboard-Template

### Phase 2: Kostenstellen (2-3 Sprints)
- [ ] Planungs-Formulare für NW, GW, ME, TZ
- [ ] Automatische Berechnungen
- [ ] Benchmark-Integration

### Phase 3: Analytics (1-2 Sprints)
- [ ] Historie-Import aus GlobalCube
- [ ] Trend-Visualisierungen
- [ ] Vergleichs-Ansichten

### Phase 4: Gamification (1 Sprint)
- [ ] Achievement-System
- [ ] Benachrichtigungen
- [ ] Team-Leaderboards (optional)

### Phase 5: Go-Live
- [ ] Schulung Abteilungsleiter
- [ ] Parallelbetrieb mit GlobalCube
- [ ] Feedback-Runde
- [ ] GlobalCube-Ablösung

---

## 8. ZUSAMMENFASSUNG

### Was macht das DRIVE Budget-Modul besser?

| Aspekt | GlobalCube (alt) | DRIVE (neu) |
|--------|------------------|-------------|
| Komplexität | 50+ Zeilen pro Kostenstelle | 5 Kernfragen |
| Benchmarks | Keine | Integriert & automatisch |
| Historie | Manuell zusammensuchen | Ein Klick |
| Motivation | Nur Zahlen | Achievements, Tipps, Erfolge |
| Zusammenarbeit | Dezentrale Excel | Zentrale Web-Lösung |
| Aktualität | Jährlich | Live-Vergleich Plan vs. IST |

### Nächste Schritte

1. **Feedback einholen** - Konzept mit Geschäftsführung besprechen
2. **Priorisierung** - Welche Kostenstellen zuerst?
3. **Daten sammeln** - Greiner-Benchmarks aus GlobalCube extrahieren
4. **Prototyp** - Werkstatt als Pilot

---

## Quellen

- [Haufe: Autohaus-Controlling Erste-Hilfe-Kennzahlen](https://www.haufe.de/controlling/controllerpraxis/autohaus-controlling-erste-hilfe-kennzahlen_112_609858.html)
- [Finception: Controlling in Autohäusern 2025](https://finception.de/controlling-in-autohausern/)
- [Kruse Control: Top KPIs for Car Dealerships](https://www.krusecontrolinc.com/top-kpis-for-car-dealerships-to-align-expenses-with-gross-profit/)
- [Cox Automotive: 12 Metrics Every Dealer Needs](https://www.coxautoinc.com/learning-center/used-car-kpis/)
- [Autohaus.de: Stundenverrechnungssätze 2024](https://www.autohaus.de/nachrichten/werkstatt/kostenexplosion-stundensatz-von-kfz-werkstaetten-erstmals-ueber-200-euro-3717519)
- [DEKRA: Reparatur-Stundensätze](https://www.dekra.de/de/reparatur-stundensaetze/)

---

*Erstellt: 2026-01-02 | TAG 155*
