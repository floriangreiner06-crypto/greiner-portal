# Predictive Scoring – Verbesserung durch externe Quellen

**Stand:** 2026-02-21  
**Kontext:** Unser Scoring nutzt heute nur **Locosoft** (Aufträge, km-Stand, Arbeitspositionen). Externe Quellen können km-Genauigkeit, Intervall-Logik und Kontakt-Steuerung verbessern.

---

## 1. Übersicht: Wo unser Scoring heute limitiert ist

| Aspekt | Heute (nur Locosoft) | Mögliche Verbesserung |
|--------|----------------------|------------------------|
| **km-Schätzung** | Nur Werkstatt-Aufträge, ~80 % mit km; 1 Messung = MEDIUM | Offizielle HU-Km, KBA, Connected Car → präzisere Schätzung |
| **Service-Intervalle** | Einheitlich pro Kategorie (z. B. Zahnriemen 90.000 km) | Hersteller-Intervall pro Modell/Motor (Opel/Hyundai variiert) |
| **„Bereits kontaktiert“** | Nicht abgebildet | Catch/Veact/CRM-Rückmeldung → Priorität runter oder Ausschluss |
| **Rückrufe** | Nicht einbezogen | KBA/Hersteller-Rückrufe → eigene Priorität oder Hinweis |
| **Saison** | Optional (Winterreifen, Klima) | Wetter/Region → bessere Timing-Empfehlung |

---

## 2. Externe Quellen (konkret)

### 2.1 Km-Stand / Laufleistung (bessere Schätzung, höhere Confidence)

| Quelle | Was sie liefert | Integration | Aufwand / Hinweise |
|--------|-----------------|-------------|--------------------|
| **TÜV / DEKRA HU-Daten** | Offizieller km-Stand bei Hauptuntersuchung (alle ~2 Jahre) | API oder Abo-Datenlieferung (z. B. TÜV SÜD, DEKRA Auswertung); Abgleich über Kennzeichen/VIN | Oft kostenpflichtig; DSGVO-konform prüfen (Auftragsverarbeitung) |
| **KBA (Kraftfahrt-Bundesamt)** | Zulassungsdaten, ggf. km bei Ummeldung (nicht flächendeckend) | KBA-Statistik/Abruf – eher aggregiert als Einzelfahrzeug | Für Einzel-Fahrzeug-km begrenzt; eher für Parc-Statistik |
| **Connected Car / Hersteller-Portal** | Live oder periodischer km-Stand (Opel Connect, Hyundai Bluelink) | API der Hersteller an Werkstatt/Händler | Händlerzugang nötig; Nutzung in Hersteller-Apps prüfen |
| **Reifendruck-/Telematik-Systeme** | Teilweise km-Stand bei Nachrüstern | Eigene Backends der Anbieter | Nur wenn ihr solche Systeme im Einsatz habt |

**Empfehlung:** Zuerst prüfen, ob TÜV/DEKRA als Datenlieferant für HU-km infrage kommt (z. B. für Fahrzeuge mit nur 1 Locosoft-Messung → Upgrade auf HIGH Confidence). Connected Car nur, wenn ihr ohnehin Hersteller-APIs nutzt.

---

### 2.2 Hersteller-Intervalle (präzisere Kategorien-Intervalle)

| Quelle | Was sie liefert | Integration | Aufwand / Hinweise |
|--------|-----------------|-------------|--------------------|
| **Opel / Stellantis Service-Pläne** | Inspektions- und Verschleiß-Intervalle pro Modell/Motor (z. B. Zahnriemen 120.000 km vs. 180.000 km) | Manuell oder API (falls Händler-Zugang): Modell/Engine → interval_km, interval_years | Tabelle pro Modell in `repair_categories` oder neue Tabelle `repair_interval_by_model`; Locosoft hat model_code, evtl. engine |
| **Hyundai Service-Pläne** | Analog (z. B. 15.000 / 30.000 km Inspektion, Zahnriemen je Modell) | Wie oben | Gleiche Logik: Fahrzeug-Modell aus Locosoft → Intervall aus externer Tabelle |

**Empfehlung:** Intervall-Logik erweitern: Statt fester Werte in `repair_categories` optional **modellabhängige Intervalle** aus einer Tabelle oder CSV (Quelle: Hersteller-Dokumentation). Scoring-Script liest dann pro Fahrzeug das passende Intervall (Fallback: aktuelles Kategorie-Intervall).

---

### 2.3 „Bereits kontaktiert“ / Kampagnen-Status (Doppel-Ansprache vermeiden)

| Quelle | Was sie liefert | Integration | Aufwand / Hinweise |
|--------|-----------------|-------------|--------------------|
| **Catch (Prof4net)** | Welche Fahrzeuge/Kunden bereits in Kampagne oder bereits angerufen | Export aus Catch oder API (falls vorhanden): vehicle_number / Kennzeichen / Kundennr. + Status | CSV-Import oder API-Aufruf → Tabelle `marketing_contact_status` (vehicle_number, campaign_id, contacted_at, outcome); Filter in Liste/Export „noch nicht kontaktiert“ |
| **Veact** | Ähnlich: Kampagnen- und Kontakt-Status | Siehe [VEACT_ERKENNTNISSE_UND_NAECHSTE_SCHRITTE.md](VEACT_ERKENNTNISSE_UND_NAECHSTE_SCHRITTE.md) – API/DataHub anfragen | Nur wenn Veact als führende Quelle für „bereits kontaktiert“ genutzt wird |
| **Eigene CRM-/Call-Liste** | Manuell gepflegte Liste „schon angerufen“ | Einfacher CSV-Import (vehicle_number oder Kennzeichen) → gleiche Tabelle wie oben | Schnell umsetzbar; reicht für den Start |

**Empfehlung:** Tabelle `marketing_contact_status` (oder `potenzial_contact_log`) anlegen: vehicle_number, datum, quelle (Catch/Manuell/…), ergebnis (optional). API/Export um Filter „nur noch nicht kontaktiert“ erweitern. Catch-Export nach jedem Lauf oder wöchentlich einspielen.

---

### 2.4 Rückrufe (KBA / Hersteller)

| Quelle | Was sie liefert | Integration | Aufwand / Hinweise |
|--------|-----------------|-------------|--------------------|
| **KBA Rückrufe** | Offizielle Rückrufe (VIN-basiert) | KBA-Liste/API (z. B. „Rückrufdatenbank“) per VIN-Abfrage | VIN aus Locosoft (vehicles.vin) → Abgleich; eigene Priorität „Rückruf“ in der Liste, kein Verschleiß-Score ersetzen |
| **Hersteller-Rückrufe (Opel/Hyundai)** | Werkstatt-Rückrufe, oft im DMS/Locosoft abgebildet | Prüfen ob Locosoft bereits Rückruf-Status oder -Aufträge hat | Ggf. nur Nutzung bestehender Locosoft-Felder |

**Empfehlung:** Wenn ihr Rückrufe sichtbar machen wollt: VIN-Liste von KBA/Hersteller einspielen, mit Locosoft-VINs abgleichen, in UI/Export als zusätzliche Spalte „Rückruf offen“ anzeigen.

---

### 2.5 Saison / Region (optional)

| Quelle | Was sie liefert | Integration | Aufwand / Hinweise |
|--------|-----------------|-------------|--------------------|
| **Eigene Logik (Monat)** | Bereits in reparaturpotenzial_api (Wintercheck, Klimacheck) | Scoring-Script oder API: Monat → Empfehlung „Winterreifen“, „Klima“ verstärken | Gering; nur Gewichtung im Score oder Sortierung |
| **Wetter-/Region-Daten** | Extremwetter, Streusalz-Regionen | Externe API (z. B. Wetterdienst) | Nur bei Bedarf für feinere Saison-Empfehlung |

**Empfehlung:** Reicht zunächst, die bestehende Saison-Logik (Monate) in der Anzeige zu nutzen; externe Wetter-APIs nur bei konkretem Mehrwert.

---

## 3. Technische Umsetzung (priorisiert)

1. **Schnell umsetzbar (ohne neue Verträge)**  
   - **Modell-Intervalle:** CSV/Tabelle mit Hersteller-Intervallen pro Modell; Scoring liest `vehicles.model_code` (oder Äquivalent) aus Locosoft und wählt Intervall.  
   - **Kontakt-Status:** Tabelle `marketing_contact_status` + manueller CSV-Import oder wöchentlicher Catch-Export; Filter in API/Export „ohne bereits kontaktiert“.

2. **Mittelfristig (mit Anbietern)**  
   - **TÜV/DEKRA HU-km:** Anbieter anfragen (Datenformat, Preis, DSGVO); bei Einbindung: Abgleich VIN/Kennzeichen, Update von `vehicle_km_estimates` (zusätzliche Zeile oder neues Feld „km_quelle = HU“) und Confidence erhöhen.  
   - **Catch-API:** Falls Catch API anbietet, „bereits kontaktiert“ automatisch statt per CSV abrufen.

3. **Optional**  
   - **Rückrufe:** KBA-VIN-Abgleich, zusätzliche Spalte in Liste/Export.  
   - **Connected Car:** Nur wenn Hersteller-API für Händler verfügbar und gewünscht.

---

## 4. Datenschutz / DSGVO

- **Externe km-Daten (TÜV, KBA):** Nur mit Rechtsgrundlage und ggf. AV-Vertrag; Zweck „Werkstatt-Potenzialanalyse / Kundenansprache“ dokumentieren.  
- **Catch/Veact:** Bereits in Nutzung; Kontakt-Status ist erforderlich für Steuerung der Ansprache (berechtigtes Interesse / Vertrag).  
- **Export/CSV:** Nur für berechtigte Nutzer (Feature `marketing_potenzial`); keine Weitergabe an Dritte außer vereinbart (z. B. Catch als Auftragsverarbeiter).

---

## 5. Dateien / nächste Schritte

- **Scoring-Script:** `scripts/marketing/marketing_km_scoring.py` – hier könnten Aufrufe für externe km-Quellen oder modellabhängige Intervalle ergänzt werden.  
- **Tabellen:** `vehicle_km_estimates` (ggf. Feld `km_source` = 'locosoft' | 'hu' | 'connected_car'), `repair_categories` oder neue `repair_interval_by_model`.  
- **API:** Filter „ohne bereits kontaktiert“ sobald `marketing_contact_status` existiert.

Wenn ihr euch für eine konkrete Quelle entscheidet (z. B. Catch-Export, Modell-Intervalle), kann die nächste Umsetzung darauf ausgerichtet werden.
