# Werkstatt & Aftersales — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-11

## Beschreibung

Werkstatt und Aftersales umfassen TEK-Dashboard, Stempeluhr/Live-Monitoring, Mechaniker-Leistung, ML-Prognosen, Gudat-Integration, Serviceberater-Dashboard, Garantie-Aufträge und -Akte, Arbeitskarte, Reparaturpotenzial, SOAP-Schnittstellen und ServiceBox-Scraper.

## Module & Dateien

### APIs
- `api/werkstatt_api.py`, `api/werkstatt_data.py` — Werkstatt-Kern
- `api/werkstatt_live_api.py` — Stempeluhr, Live-Monitoring
- `api/unfall_wissensbasis_api.py` — Versicherungs-Rechnungsprüfung M4 (Checkliste, Urteile)
- `api/serviceberater_api.py`, `api/serviceberater_data.py` — Serviceberater-Dashboard
- `api/garantie_auftraege_api.py` — Garantie-Aufträge
- `api/arbeitskarte_api.py` — Arbeitskarte
- `api/reparaturpotenzial_api.py` — Reparaturpotenzial
- `api/gudat_api.py`, `api/gudat_data.py` — Gudat-Integration
- `api/ml_api.py`, `api/ai_api.py` — ML/Prognosen

### Templates
- `templates/aftersales/*.html` (inkl. `unfall_wissensdatenbank.html`)
- `templates/controlling/tek_dashboard.html`

### Tools / Scripts
- `tools/gudat_*.py`
- `tools/scrapers/servicebox_*.py`
- `scripts/ml/`

### Celery Tasks
- `werkstatt_leistung`, `servicebox_*`, `email_werkstatt_tagesbericht`, `email_tek_daily`, `ml_retrain`, `benachrichtige_serviceberater_ueberschreitungen`

## DB-Tabellen (PostgreSQL drive_portal)

- `orders`, `labours`, View `times`, `employees_history`, `absence_calendar`, `werkstatt_leistung_daily`, `delivery_notes`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ TEK-Dashboard, Stempeluhr, Serviceberater, Gudat-Anbindung in Nutzung
- 🔧 ML, Garantieakte, ServiceBox je nach Projektstand
- ✅ **Versicherungs-Rechnungsprüfung:** DB-Schema (7 Tabellen) + M4 Wissensdatenbank (API + UI + Seed) fertig; M1/M2/M3 folgen
- ❌ Offene Punkte ggf. in Session-TODOs

## Offene Entscheidungen

- (Keine festgehalten)

---

## Neues Modul: Versicherungs-Rechnungsprüfung für Unfallschäden (Feature-Plan)

**Status:** DB-Schema + M4 umgesetzt; M1 (Vollständigkeitscheck), M2, M3 offen.

### Kontext & Ziele

Autohaus Greiner repariert Unfallschäden und stellt Rechnungen an gegnerische Haftpflichtversicherungen. Prüfdienstleister (v.a. ControlExpert/Allianz) kürzen Rechnungen systematisch; branchenüblich werden ca. 10–35 % ungerechtfertigt gekürzt. Das Modul soll:

1. Rechnungen **vor dem Versand** auf Vollständigkeit prüfen
2. Vergessene berechtigte Positionen erkennen
3. Bei Kürzungen sofort passende **Rechtsprechung** parat haben
4. **Tracking**: Wie viel geht durch Kürzungen verloren?

### Datenquellen im Autohaus

- Werkstattaufträge aus **Locosoft** (PostgreSQL)
- Sachverständigengutachten (PDF)
- Rechnungen an Versicherungen (Locosoft oder PDF)
- Prüfberichte ControlExpert/Versicherungen (PDF, eingescannt)
- Zahlungseingänge (Bankenspiegel/MT940)

### Workstream-Zuordnung

- **Hauptbereich:** werkstatt (Aftersales/Unfallreparatur)
- **Berührungspunkte:** controlling (Zahlungseingänge, offene Forderungen), integrations (PDF-Parsing für Prüfberichte)

### Feature-Architektur (4 Module)

| Modul | Kurzbeschreibung |
|-------|------------------|
| **M1: Rechnungs-Vollständigkeitscheck** | Auftrag aus Locosoft laden → Positionen gegen Checkliste prüfen → Ampelsystem (Grün/Gelb/Rot), Warnung bei fehlenden berechtigten Positionen |
| **M2: Kürzungs-Abwehr** | Prüfbericht erfassen (PDF/Manuell) → gekürzte Positionen erkennen → BGH-Urteil + Begründung pro Position → Muster-Widerspruch generieren → Eskalation (Widerspruch → Anwalt → Klage) |
| **M3: Kürzungs-Tracking & Reporting** | Pro Versicherung: Kürzungssumme, -häufigkeit, Widerspruchserfolg; Pro Position: Kürzungshäufigkeit; Jahresverlust, Trends; Dashboard mit KPIs |
| **M4: Wissensdatenbank** | Urteile (Aktenzeichen, Datum, Kurzfassung), Zuordnung Position ↔ Urteil, Suchfunktion, pflegbar |

### Typische Kürzungspositionen (Checkliste für M1/M2)

| Position | Häufigkeit | Rechtslage |
|----------|------------|------------|
| Verbringungskosten | Sehr häufig | BGH: fast immer berechtigt |
| UPE-Aufschläge | Sehr häufig | Berechtigt bei konkreter Abrechnung |
| Beilackierung angrenzender Bauteile | Häufig | Technisch notwendig (Farbtonsicherheit) |
| Desinfektionskosten | Häufig | Strittig, oft durchsetzbar |
| Stundenverrechnungssätze („günstigere Werkstatt“) | Sehr häufig | Markenwerkstatt steht Vertragswerkstatt zu |
| Kleinersatzteile / Befestigungssätze | Häufig | Pauschale branchenüblich |
| Probefahrtkosten | Mittel | Technisch notwendig (Qualitätssicherung) |
| Reinigung, Entsorgung, Ofentrocknung | Mittel | Berechtigt / real anfallend |
| Mietwagenkosten bei Verzögerung | Bei Verzug | Werkstattrisiko beim Schädiger (BGH) |
| Unfallverhütungskosten | Selten | Arbeitssicherheit, berechtigt |

### Rechtsprechung (Wissensbasis M2/M4)

- **BGH 16.01.2024:** 5 Urteile — Versicherung muss Werkstattrechnung ungekürzt zahlen; Geschädigter trägt kein Werkstattrisiko.
- **Grundsatzurteile:** BGH VI ZR 42/73 (Werkstattrisiko), AG Dinslaken 32 C 147/22 (Nebenpositionen), BGH VI ZR 53/09 (Markenwerkstatt <3 Jahre), BGH VI ZR 267/14 (Referenzwerkstatt 20 km unzumutbar).
- **Regeln:** § 249 BGB; Werkstattrisiko beim Schädiger; ControlExpert nicht sachverständig; Markenwerkstatt bei <3 Jahre oder regelmäßiger Markenwartung.

### Externe Referenzquellen (Links/Wissensbasis)

- ZKF (zkf.de), Captain HUK (captain-huk.de), schaden.news, Kanzlei Voigt/Schleyer, CarRight.de, Stiftung Warentest, ra-kotz.de

### Prüfdienstleister

ControlExpert, CarExpert, DEKRA, SSH, HP ClaimControlling, KRUG.

### DB-Tabellen (Vorschlag, PostgreSQL drive_portal)

| Tabelle | Zweck |
|---------|--------|
| `unfall_rechnungen` | Auftragsnummer, Versicherung, Gutachten-Nr, Rechnungsbetrag, Status |
| `unfall_positionen` | Position, Betrag, Kategorie (Checkliste), in_rechnung, gekürzt |
| `unfall_kuerzungen` | Prüfbericht-ID, Position, Kürzungsbetrag, Begründung, Widerspruch_Status |
| `unfall_urteile` | Aktenzeichen, Gericht, Datum, Position_Kategorie, Kurzfassung, Volltext_Link |
| `unfall_versicherungen` | Name, Prüfdienstleister, Kürzungsstatistik |

### Priorität & Aufwand

- **Priorität:** Hoch (jede nicht-widersprochene Kürzung kostet ca. 200–1.500 €).
- **Umsetzung:** Start nach ausdrücklichem OK.

---

## Abhängigkeiten

- HR/Locosoft (Mitarbeiter), Integrations (Locosoft SOAP, ServiceBox), Infrastruktur (Celery)
