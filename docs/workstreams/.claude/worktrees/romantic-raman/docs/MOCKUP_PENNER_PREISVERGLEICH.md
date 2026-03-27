# MOCKUP: Automatischer Penner-Preisvergleich für Matthias

**Erstellt:** 2025-12-29 (TAG 142)
**Ziel:** Matthias soll auf einen Blick sehen, welche Penner-Teile verkäuflich sind

---

## Das Problem

- **170.000€** in Lagerleichen (24+ Monate ohne Verkauf)
- **71.000€** in Pennern (12-24 Monate)
- Matthias muss jeden Artikel einzeln googlen
- Keine Ahnung ob ein Teil noch Marktpreis hat

---

## Die Lösung: Automatischer Preisvergleich

### Dashboard-Erweiterung: "Verkaufschancen"

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🏷️ PENNER-VERKAUFSCHANCEN                              [Aktualisieren] 📥  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 📊 ZUSAMMENFASSUNG                                                   │   │
│  │                                                                      │   │
│  │   🟢 Gute Chancen: 47 Teile (23.450€)  - Marktpreis gefunden        │   │
│  │   🟡 Prüfen:       89 Teile (41.200€)  - Angebote vorhanden         │   │
│  │   🔴 Schwierig:   156 Teile (98.100€)  - Kaum Nachfrage             │   │
│  │                                                                      │   │
│  │   💰 Geschätzter Erlös bei Verkauf: 35.000€ - 48.000€               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Filter: [Alle ▼] [Min. Lagerwert: 50€] [Nur mit Marktpreis ☑]             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🟢 GUTE VERKAUFSCHANCEN (Top 10 nach Potenzial)                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  1. 1K0 615 301 AA - Bremsscheibe VA                                │   │
│  │     ├─ Bestand: 4 Stk │ EK: 45€ │ Lagerwert: 180€                   │   │
│  │     ├─ Letzter Verkauf: vor 18 Monaten                              │   │
│  │     │                                                                │   │
│  │     │  📈 MARKTANALYSE:                                             │   │
│  │     │  ┌──────────────────────────────────────────────────────┐     │   │
│  │     │  │ eBay.de:        12 Angebote │ Ø 52€ │ 38€ - 69€      │     │   │
│  │     │  │ Daparto:         8 Angebote │ Ø 48€ │ ab 41€         │     │   │
│  │     │  │ Autoteile-Markt: 3 Angebote │ Ø 35€ │ gebraucht      │     │   │
│  │     │  └──────────────────────────────────────────────────────┘     │   │
│  │     │                                                                │   │
│  │     │  💡 EMPFEHLUNG: Bei eBay für 45€ einstellen                   │   │
│  │     │     Erwarteter Erlös: 160-180€ (4 Stk)                        │   │
│  │     │                                                                │   │
│  │     └─ [🛒 Bei eBay listen] [📋 Auf Merkliste] [❌ Ignorieren]      │   │
│  │                                                                      │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                      │   │
│  │  2. 5Q0 959 455 AJ - Lüftermotor                                    │   │
│  │     ├─ Bestand: 1 Stk │ EK: 189€ │ Lagerwert: 189€                  │   │
│  │     ├─ Letzter Verkauf: vor 26 Monaten                              │   │
│  │     │                                                                │   │
│  │     │  📈 MARKTANALYSE:                                             │   │
│  │     │  ┌──────────────────────────────────────────────────────┐     │   │
│  │     │  │ eBay.de:         5 Angebote │ Ø 165€ │ 140€ - 210€   │     │   │
│  │     │  │ Daparto:         2 Angebote │ Ø 198€ │ ab 185€       │     │   │
│  │     │  │ Google Shopping: 4 Angebote │ Ø 175€                 │     │   │
│  │     │  └──────────────────────────────────────────────────────┘     │   │
│  │     │                                                                │   │
│  │     │  💡 EMPFEHLUNG: Bei eBay für 155€ einstellen                  │   │
│  │     │     EK-Verlust: -34€ │ Aber: Kapital frei + Lagerplatz!       │   │
│  │     │                                                                │   │
│  │     └─ [🛒 Bei eBay listen] [📋 Auf Merkliste] [❌ Ignorieren]      │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🟡 PRÜFEN - Markt vorhanden, aber wenig Angebote                    │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  • 4G0 941 531 B - Sensor │ 2 Stk │ 340€ │ eBay: 2 Angebote Ø 95€   │   │
│  │  • 8K0 615 601 M - Bremssattel │ 1 Stk │ 285€ │ Daparto: ab 220€    │   │
│  │  • 3C0 857 511 - Spiegelglas │ 3 Stk │ 120€ │ eBay: 4 Angebote      │   │
│  │  ...                                                                 │   │
│  │                                                     [Alle 89 zeigen] │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🔴 SCHWIERIG - Kein/kaum Markt gefunden                             │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  • DPF aus 2011 │ 1.450€ │ Keine Angebote │ ⚠️ Verschrotten?        │   │
│  │  • Spezial-Dichtung XYZ │ 89€ │ Obsolet │ ⚠️ Abschreiben           │   │
│  │  ...                                                                 │   │
│  │                                    [Alle 156 zeigen] [CSV Export]    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technische Umsetzung

### 1. Preisabfrage-Service (Backend)

```python
# api/preisvergleich_api.py

class PreisvergleichService:
    """
    Holt automatisch Marktpreise von externen Quellen.
    Cached Ergebnisse für 24h um Rate-Limits zu vermeiden.
    """

    QUELLEN = [
        'ebay_de',      # eBay.de API oder Scraping
        'daparto',       # Daparto Preisvergleich
        'autodoc',       # Autodoc.de
        'google_shopping' # Google Shopping API
    ]

    def get_marktpreis(self, teilenummer: str) -> dict:
        """
        Holt Marktpreise für eine Teilenummer.

        Returns:
            {
                'teilenummer': '1K0 615 301 AA',
                'quellen': [
                    {
                        'name': 'eBay.de',
                        'anzahl_angebote': 12,
                        'preis_min': 38.00,
                        'preis_max': 69.00,
                        'preis_avg': 52.00,
                        'typ': 'neu+gebraucht'
                    },
                    ...
                ],
                'empfehlung': {
                    'verkaufspreis': 45.00,
                    'plattform': 'eBay.de',
                    'chance': 'hoch'  # hoch/mittel/gering
                },
                'cached_at': '2025-12-29T10:00:00'
            }
        """
```

### 2. Batch-Verarbeitung (Nacht-Job)

```python
# Celery Task: Jede Nacht um 3:00 Uhr
@celery.task
def update_penner_marktpreise():
    """
    Aktualisiert Marktpreise für alle Penner/Leichen.

    - Holt Liste aller Penner (>12 Monate ohne Verkauf)
    - Fragt Marktpreise ab (mit Pausen für Rate-Limits)
    - Speichert in Cache-Tabelle
    - Generiert Report für Matthias
    """

    penner = get_penner_teile(min_lagerwert=50)  # ~300 Teile

    for teil in penner:
        preise = preisvergleich.get_marktpreis(teil['part_number'])
        cache_marktpreis(teil['part_number'], preise)
        time.sleep(2)  # Rate-Limit beachten

    # E-Mail an Matthias mit Top 20 Verkaufschancen
    send_penner_report(empfaenger='matthias@greiner.de')
```

### 3. Datenbank-Schema

```sql
-- Cache für Marktpreise
CREATE TABLE penner_marktpreise (
    id SERIAL PRIMARY KEY,
    part_number VARCHAR(50) NOT NULL,

    -- Zusammenfassung
    anzahl_quellen INTEGER,
    anzahl_angebote INTEGER,
    preis_min DECIMAL(10,2),
    preis_max DECIMAL(10,2),
    preis_avg DECIMAL(10,2),

    -- Empfehlung
    empf_verkaufspreis DECIMAL(10,2),
    empf_plattform VARCHAR(50),
    verkaufschance VARCHAR(20),  -- hoch/mittel/gering/keine

    -- Meta
    abgefragt_am TIMESTAMP DEFAULT NOW(),
    raw_data JSONB,  -- Vollständige API-Antworten

    UNIQUE(part_number)
);

-- Index für schnelle Abfragen
CREATE INDEX idx_penner_chance ON penner_marktpreise(verkaufschance, preis_avg DESC);
```

### 4. API Endpoints

```
GET /api/lager/verkaufschancen
    ?min_lagerwert=50
    ?chance=hoch,mittel
    ?limit=50

    -> Liste mit Penner + Marktpreisen + Empfehlungen

GET /api/lager/verkaufschancen/stats
    -> Zusammenfassung (Anzahl pro Kategorie, Gesamtpotenzial)

POST /api/lager/verkaufschancen/refresh
    -> Manuelles Update der Marktpreise (async)

GET /api/lager/verkaufschancen/export
    -> CSV für Excel mit allen Daten
```

---

## Preisquellen-Optionen

### Option A: Web Scraping (kostenlos, aber fragil)

```python
# eBay.de Scraping
def scrape_ebay(teilenummer):
    url = f"https://www.ebay.de/sch/i.html?_nkw={teilenummer}"
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    preise = []
    for item in soup.select('.s-item'):
        preis = item.select_one('.s-item__price')
        if preis:
            preise.append(parse_preis(preis.text))

    return {
        'anzahl': len(preise),
        'min': min(preise),
        'max': max(preise),
        'avg': sum(preise) / len(preise)
    }
```

**Vorteile:** Kostenlos, sofort umsetzbar
**Nachteile:** Kann blockiert werden, HTML-Änderungen brechen es

### Option B: APIs (zuverlässig, teils kostenpflichtig)

| Quelle | API | Kosten |
|--------|-----|--------|
| eBay | eBay Browse API | Kostenlos (mit Limits) |
| Google Shopping | Content API | ~0.01€/Abfrage |
| Daparto | Keine öffentliche API | Scraping nötig |
| TecDoc | TecDoc API | Lizenz erforderlich |

### Option C: Hybrid (Empfehlung)

1. **eBay API** für Hauptpreise (kostenlos)
2. **Google Shopping** als Fallback
3. **Scraping** nur für Daparto

---

## Wöchentlicher Report für Matthias

```
═══════════════════════════════════════════════════════════════
📊 PENNER-VERKAUFSCHANCEN REPORT - KW 52/2025
═══════════════════════════════════════════════════════════════

Hallo Matthias,

hier dein wöchentlicher Überblick zu verkäuflichen Lagerleichen:

┌─────────────────────────────────────────────────────────────┐
│ 💰 DIESE WOCHE NEU ENTDECKT                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. 1K0 615 301 AA - Bremsscheibe VA                        │
│    Lagerwert: 180€ │ Marktpreis: ~52€/Stk                  │
│    → Bei eBay einstellen für ~160€ Erlös                   │
│                                                             │
│ 2. 5Q0 959 455 AJ - Lüftermotor                            │
│    Lagerwert: 189€ │ Marktpreis: ~165€                     │
│    → Schnäppchen-Preis 149€ = schneller Verkauf            │
│                                                             │
│ 3. 8K0 615 601 M - Bremssattel                             │
│    Lagerwert: 285€ │ Marktpreis: ~220€                     │
│    → Rückgabe an Lieferant prüfen!                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘

📈 GESAMTÜBERSICHT:
   • Penner mit Markt: 136 Teile (64.600€)
   • Geschätzter Erlös: 35.000€ - 48.000€
   • Empfehlung: Top 20 bei eBay listen = ~8.000€ Erlös

🔗 Details: https://drive.greiner.de/werkstatt/verkaufschancen

Viele Grüße,
DRIVE Portal

═══════════════════════════════════════════════════════════════
```

---

## Implementierungsplan

| Phase | Aufwand | Beschreibung |
|-------|---------|--------------|
| 1. MVP | 4h | Marktcheck-Links erweitern, manuelle Prüfung |
| 2. Scraping | 8h | eBay + Daparto automatisch abfragen |
| 3. Dashboard | 6h | Verkaufschancen-Übersicht |
| 4. Report | 4h | Wöchentlicher E-Mail-Report |
| 5. eBay-Integration | 8h | Direkt aus DRIVE bei eBay listen |

**Gesamt: ~30h für vollständige Lösung**

---

## Fragen an Matthias

1. **Welche Plattformen nutzt ihr bereits?**
   - eBay? eBay Kleinanzeigen? Autoteile-Markt?

2. **Wie viel Zeit pro Woche für Penner-Verkauf?**
   - Lohnt sich Automatisierung?

3. **Mindest-Lagerwert für Verkauf?**
   - Ab 50€? 100€? 200€?

4. **Rückgabe an Lieferant möglich?**
   - Welche Lieferanten nehmen zurück?

5. **Locosoft Ersatzteilpool aktiv?**
   - Falls ja: Können wir dort automatisch listen?

---

*Mockup erstellt von Claude - TAG 142*
