# Konzept: Tägliches Erfolgsreporting für Greiner DRIVE

**Erstellt:** 2025-12-21 (TAG 133)
**Für:** Geschäftsführung, Abteilungsleiter
**Status:** ENTWURF - Zur Abstimmung

---

## Problem-Analyse

### Aktueller Zustand: TEK mit Vollkosten

Die aktuelle TEK (Tägliche Erfolgskontrolle) zeigt:
- Umsatz, Einsatz, DB1 nach Bereichen (NW, GW, Teile, Lohn, Sonst)
- Vollkostenrechnung: Variable Kosten → Direkte Kosten → Umlage → BE
- Breakeven-Prognose auf Monatsbasis

### Warum das täglich keinen Sinn macht:

| Problem | Auswirkung |
|---------|------------|
| **Konzernumlage** wird erst am Monatsende gebucht | BE zeigt am Monatsanfang unrealistisch gute Werte |
| **Indirekte Kosten** fallen ungleichmäßig an | Am 5. des Monats fehlen noch 80% der Mietbuchungen |
| **Hochrechnung** mit Unvollständigen Daten | Prognose schwankt täglich stark |
| **Keine operativen KPIs** | Was ist heute wichtig? Wird nicht beantwortet |

### Branchenstandard (aus Recherche):

> "Ein Autohausunternehmer braucht **Echtzahlen – einige wenige reichen**, aber diese müssen den Allgemeinzustand bestmöglich abbilden."
> — kfz-betrieb.de

**Unterscheidung:**
- **Operative Tages-KPIs** = Zeigen, ob die *Arbeit* effizient ist (Produktivität, Abschlüsse, Liquidität)
- **Strategische Monats-KPIs** = Zeigen, ob das *Unternehmen* auf Kurs ist (BWA, Rentabilität, BE)

---

## Lösung: Zwei-Stufen-Reporting

```
┌───────────────────────────────────────────────────────────────┐
│                    GREINER DRIVE                               │
│                                                                 │
│  ┌─────────────────────────┐   ┌─────────────────────────┐    │
│  │  TAGES-COCKPIT          │   │  MONATS-CONTROLLING     │    │
│  │  (Operativ)             │   │  (Strategisch)          │    │
│  │                         │   │                         │    │
│  │  • Liquidität           │   │  • BWA Vollkosten       │    │
│  │  • Verkaufs-Abschlüsse  │   │  • BE nach Bereich      │    │
│  │  • Werkstatt-KPIs       │   │  • Plan/Ist-Vergleich   │    │
│  │  • Offene Forderungen   │   │  • Konzernumlage        │    │
│  │  • Alerts               │   │  • Rentabilität         │    │
│  │                         │   │                         │    │
│  │  📊 Täglich vor 9:00    │   │  📊 Monatlich (BWA+3)   │    │
│  │  📧 E-Mail an GF        │   │  📧 PDF-Report          │    │
│  └─────────────────────────┘   └─────────────────────────┘    │
│                                                                 │
│            ↓ Drill-Down               ↓ Drill-Down             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              ABTEILUNGS-DASHBOARDS                       │  │
│  │                                                           │  │
│  │  Verkauf         Werkstatt         Teile                 │  │
│  │  • Pipeline      • Produktivität   • Verfügbarkeit       │  │
│  │  • Conversion    • Leistungsgrad   • Lagerumschlag       │  │
│  │  • Forecast      • Auslastung      • Erlöse/MA           │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## 1. Tägliches GF-Cockpit (NEU)

### Zielgruppe
- Geschäftsführung (vor 9:00 Uhr)
- Abteilungsleiter (Überblick)

### Design-Prinzipien
- **5-7 Kern-KPIs** (nicht mehr!)
- **Ampel-Logik** (Grün/Gelb/Rot)
- **Trend-Pfeile** (↑↓→)
- **Drill-Down** bei Klick
- **E-Mail-Report** täglich 8:00 Uhr

### KPIs im Tages-Cockpit

| # | KPI | Quelle | Drill-Down |
|---|-----|--------|------------|
| 1 | **Liquidität heute** | Bankenspiegel (SQLite) | → Konten-Details |
| 2 | **Liquiditätsreichweite** | Berechnet (Bank/Ø Kosten) | → 3-Monats-Trend |
| 3 | **Verkauf gestern** | Locosoft (invoices) | → Einzelabschlüsse |
| 4 | **Verkauf Monat (vs. Ziel)** | Locosoft + Zielwert | → Verkäufer-Ranking |
| 5 | **Werkstatt-Produktivität** | Locosoft (work_times) | → pro Mechaniker |
| 6 | **Offene Forderungen** | Locosoft (open_items) | → Fälligkeiten |
| 7 | **Alerts** | Diverse | → Details |

### Mockup: Tages-Cockpit

```
┌─────────────────────────────────────────────────────────────────┐
│  🏢 GREINER DRIVE - GESCHÄFTSFÜHRUNGS-COCKPIT                   │
│  Stand: 21.12.2025, 08:47 Uhr        [Aktualisieren] [E-Mail ✉]│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │ 🏦 LIQUIDITÄT        │  │ 📅 REICHWEITE        │            │
│  │ 245.320 €            │  │ 4,2 Monate           │            │
│  │ ↑ +12.500 vs gestern │  │ ✅ OK (Ziel: 3+)     │            │
│  │ [Details ›]          │  │ [Trend ›]            │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │ 🚗 VERKAUF GESTERN   │  │ 📊 MONAT (vs Ziel)   │            │
│  │ 3 Abschlüsse         │  │ 42 / 50 = 84%        │            │
│  │ NW: 2 | GW: 1        │  │ ⚠️ 8 Stück Rückstand │            │
│  │ [Abschlüsse ›]       │  │ [Verkäufer ›]        │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │ 🔧 WERKSTATT         │  │ 💰 FORDERUNGEN       │            │
│  │ Produktivität: 87%   │  │ Gesamt: 128.500 €    │            │
│  │ ✅ Ziel: 85%         │  │ >30 Tage: 18.200 € ⚠│            │
│  │ [Mechaniker ›]       │  │ [Fälligkeiten ›]     │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ⚡ ALERTS (2)                                            │   │
│  │ ⚠️ Teileverfügbarkeit Bremsen: 68% (Ziel: 90%)         │   │
│  │ ⚠️ Verkauf: 8 Stück unter Monats-Soll                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Datenverfügbarkeit

| KPI | Datenquelle | Status | Aufwand |
|-----|-------------|--------|---------|
| Liquidität | `bwa_monatswerte.bank_summe` | ✅ Vorhanden | Gering |
| Reichweite | Berechnet | 🔧 Neu | Gering |
| Verkauf gestern | Locosoft `invoices` | ✅ Vorhanden | Gering |
| Verkauf Monat | Locosoft `invoices` | ✅ Vorhanden | Gering |
| Werkstatt-Produktivität | Locosoft `work_times` | 🔍 Prüfen | Mittel |
| Offene Forderungen | Locosoft `open_items`? | 🔍 Prüfen | Mittel |
| Alerts | Berechnet | 🔧 Neu | Mittel |

---

## 2. Monatliches Controlling (Bestehend)

### Anpassungen

Die bestehende TEK/BWA bleibt für die **monatliche** strategische Analyse:

| Änderung | Details |
|----------|---------|
| **Umbenennung** | TEK → "Monatliches Controlling" oder "BWA-Dashboard" |
| **Zeitraum-Default** | "Letzter abgeschlossener Monat" statt "Aktueller Monat" |
| **Infobox** | Hinweis: "Für tägliche KPIs → GF-Cockpit nutzen" |
| **Vollkosten** | BE nur für abgeschlossene Monate aussagekräftig |

### Verbleibende Features
- DB1 nach Bereichen (NW, GW, Teile, Lohn)
- Vollkosten-Kaskade (Variable → Direkte → Indirekte → BE)
- Konzernumlage-Betrachtung (bereinigt/unbereinigt)
- Drill-Down bis Einzelbuchung

---

## 3. Abteilungs-Dashboards

### Verkauf-Dashboard (für Verkaufsleiter)

| KPI | Beschreibung | Frequenz |
|-----|--------------|----------|
| Vertriebstrichter | Anfragen → Angebote → Abschlüsse | Täglich |
| Conversion Rate | % Angebote → Abschlüsse | Wöchentlich |
| Ø Bruttogewinn | Pro verkauftem Fahrzeug | Monatlich |
| Pipeline-Wert | Offene Angebote in € | Täglich |
| Lagerbestand | Tage auf Hof (Standzeit) | Wöchentlich |

### Werkstatt-Dashboard (für Serviceleiter)

| KPI | Beschreibung | Frequenz |
|-----|--------------|----------|
| Produktivität | Auftrags-Std / Anwesenheits-Std | Täglich |
| Leistungsgrad | Verrechnete / Gestempelte Std | Täglich |
| Auslastung | Repair Orders vs. Kapazität | Täglich |
| Durchlaufzeit | Ø Tage Auftrag bis Abschluss | Wöchentlich |
| Service-No-Shows | Nicht erschienene Termine | Täglich |

### Teile-Dashboard (für Teileleiter)

| KPI | Beschreibung | Frequenz |
|-----|--------------|----------|
| Verfügbarkeit | Lagerteile für Werkstatt-Aufträge | Täglich |
| Lagerumschlag | Verkaufte / Bestand | Monatlich |
| Erlöse/MA | Teileerlös pro Mitarbeiter | Monatlich |
| Theken-Umsatz | Direktverkauf an Kunden | Täglich |

---

## 4. E-Mail-Report (Tages-Zusammenfassung)

### Empfänger
- Geschäftsführung: Vollständiges Cockpit
- Abteilungsleiter: Eigener Bereich + Alerts

### Zeitpunkt
- Täglich 08:00 Uhr (vor Arbeitsbeginn)
- Nur an Werktagen (Mo-Fr)

### Format

```
═══════════════════════════════════════════════════════════════
     🏢 GREINER DRIVE - TAGES-REPORT
     Samstag, 21. Dezember 2025
═══════════════════════════════════════════════════════════════

🏦 LIQUIDITÄT
   Gesamt: 245.320 € (+12.500 € vs. Vortag)
   Reichweite: 4,2 Monate ✅

🚗 VERKAUF (Freitag, 20.12.)
   Abschlüsse: 3 (NW: 2, GW: 1)
   Monat: 42/50 (84%) ⚠️ 8 unter Ziel

🔧 WERKSTATT
   Produktivität: 87% ✅
   Leistungsgrad: 96% ✅
   Aufträge: 24 (+3 vs. Ø)

💰 FORDERUNGEN
   Gesamt: 128.500 €
   Überfällig (>30 Tage): 18.200 € ⚠️

⚡ ALERTS
   • Teileverfügbarkeit Bremsen: 68%
   • Verkauf unter Monats-Soll

───────────────────────────────────────────────────────────────
📊 Details im Portal: https://drive.auto-greiner.de/cockpit
═══════════════════════════════════════════════════════════════
```

---

## 5. Technische Umsetzung

### Neue Komponenten

```
Server/
├── api/
│   └── cockpit_api.py          # NEU: Tages-KPIs
├── templates/
│   └── controlling/
│       └── cockpit.html         # NEU: GF-Cockpit
├── scheduler/
│   └── jobs/
│       └── send_daily_report.py # NEU: E-Mail-Job
```

### API-Endpoints

```python
# Cockpit-API
GET /api/cockpit/summary
    → { liquiditaet, reichweite, verkauf_gestern, verkauf_monat,
        werkstatt_produktivitaet, forderungen, alerts }

GET /api/cockpit/liquiditaet
    → { bank_konten: [...], summe, trend_7_tage }

GET /api/cockpit/verkauf?datum=2025-12-20
    → { abschluesse: [...], nw, gw, monat_ist, monat_soll }

GET /api/cockpit/werkstatt?datum=2025-12-20
    → { produktivitaet, leistungsgrad, auftraege, mechaniker: [...] }

GET /api/cockpit/forderungen
    → { gesamt, ueberfaellig_30, ueberfaellig_60, kunden: [...] }
```

### Scheduler-Job

```python
# Daily Report Job (08:00 Uhr, Mo-Fr)
@scheduler.scheduled_job('cron', hour=8, minute=0, day_of_week='mon-fri')
def send_daily_gf_report():
    """Versendet täglichen GF-Report per E-Mail."""
    data = fetch_cockpit_summary()
    html = render_template('emails/daily_report.html', data=data)
    send_email(
        to=['gf@auto-greiner.de'],
        subject=f'DRIVE Tages-Report {datetime.now():%d.%m.%Y}',
        html=html
    )
```

### Datenbank (optional)

```sql
-- Für historische Trend-Analyse
CREATE TABLE daily_kpis (
    id INTEGER PRIMARY KEY,
    datum DATE NOT NULL UNIQUE,
    liquiditaet_summe REAL,
    reichweite_monate REAL,
    verkauf_nw INTEGER,
    verkauf_gw INTEGER,
    werkstatt_produktivitaet REAL,
    forderungen_gesamt REAL,
    forderungen_ueberfaellig REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. Roadmap / Umsetzungsplan

### Phase 1: Quick Win (2-3 Tage)
- [x] Konzept erstellen (dieses Dokument)
- [ ] Liquidität + Reichweite im Cockpit
- [ ] Link "Zum Tages-Cockpit" auf Startseite

### Phase 2: Verkaufs-KPIs (2-3 Tage)
- [ ] Verkauf gestern + Monat aus Locosoft
- [ ] Zielwert-Konfiguration (Monatsziele)
- [ ] Drill-Down zu Einzelabschlüssen

### Phase 3: Werkstatt-KPIs (3-4 Tage)
- [ ] Produktivitäts-Berechnung prüfen (Locosoft work_times)
- [ ] Leistungsgrad (verrechnete vs. gestempelte Stunden)
- [ ] Mechaniker-Übersicht

### Phase 4: Alerts + E-Mail (2-3 Tage)
- [ ] Alert-Schwellenwerte definieren
- [ ] Alert-Engine implementieren
- [ ] E-Mail-Template erstellen
- [ ] Scheduler-Job konfigurieren

### Phase 5: Abteilungs-Dashboards (5-7 Tage)
- [ ] Verkauf-Dashboard
- [ ] Werkstatt-Dashboard
- [ ] Teile-Dashboard

---

## 7. Offene Fragen

| # | Frage | Zu klären mit |
|---|-------|---------------|
| 1 | **Monatsziele Verkauf:** Wo kommen Sollwerte her? | GF |
| 2 | **Produktivität:** Sind work_times in Locosoft vollständig? | Serviceleiter |
| 3 | **Offene Forderungen:** Welche Tabelle in Locosoft? | Buchhaltung |
| 4 | **Alert-Schwellen:** Welche Werte sind kritisch? | GF + Abteilungsleiter |
| 5 | **E-Mail-Empfänger:** Wer bekommt welchen Report? | GF |

---

## 8. Quellen (Best Practices)

- **kfz-betrieb.de:** Tag für Tag effizientes Controlling
- **autohaus.de:** Operatives Controlling - Die wichtigsten Kennzahlen
- **haufe.de:** Autohaus-Controlling: Erste-Hilfe-Kennzahlen
- **caraconsult.de:** Produktivität und Leistungsgrad in der Werkstatt
- **TARGIT:** Top KPIs for Fixed Operations in Car Dealerships
- **Cox Automotive:** 12 metrics every dealer needs to track

---

## Fazit

**Kernerkenntnisse:**

1. **TEK mit Vollkosten macht täglich keinen Sinn** weil Umlagen/Kosten erst zum Monatsende vollständig sind

2. **Zwei-Stufen-Ansatz:**
   - **Täglich:** Operative KPIs (Liquidität, Abschlüsse, Produktivität)
   - **Monatlich:** Strategische Analyse (BWA, BE, Rentabilität)

3. **5-7 Kern-KPIs** für GF-Cockpit reichen (kein Overload!)

4. **Drill-Down** ermöglicht Detailanalyse bei Bedarf

5. **E-Mail-Report** vor 9:00 Uhr liefert Infos zum Arbeitsbeginn

---

**Nächster Schritt:** Abstimmung mit GF über Priorisierung und Zielwerte

---

*Erstellt: 2025-12-21 | Autor: Claude | Version: 1.0*
