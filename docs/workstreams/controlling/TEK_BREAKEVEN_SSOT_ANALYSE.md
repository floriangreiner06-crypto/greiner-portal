# TEK Breakeven – SSOT umgesetzt (2026-02-13)

**Status:** SSOT implementiert. Portal und PDF nutzen dieselbe Logik aus `api/controlling_data.py`.

## Ehemaliges Problem

Portal (TEK-Dashboard) und PDF/E-Mail (TEK-Report) zeigen unterschiedliche Werte für **Prognose** und **Breakeven**. Ursache: **zwei getrennte Berechnungswege**, keine gemeinsame SSOT.

## Aktuelle Datenflüsse

| Quelle | Verwendung | Breakeven („Kosten“) | Prognose |
|--------|------------|----------------------|----------|
| **Portal** (`routes/controlling_routes.py`) | TEK-Dashboard im Browser | `berechne_breakeven_prognose()`: Variable + Direkte + Indirekte (BWA-Kontenklassen), 3 Monate, /3 | `(operativ_db1 / tage_mit_daten) * werktage_gesamt` (echte Werktage des Monats, z. B. 20 im Feb 2026) |
| **get_tek_data** (`api/controlling_data.py`) | PDF, send_daily_tek, E-Mail | Summe **alle** 4xxxxx, `CURRENT_DATE - 3 months` bis heute, /3, mit umlage_kosten_filter | `(total_db1 / tage_mit_daten) * 22` (**fix 22 Werktage**) |

## Konkrete Unterschiede

1. **Breakeven**
   - Portal: nur bestimmte Konten (Variable/Direkte/Indirekte nach BWA-Logik), gleitender 3-Monats-Zeitraum.
   - PDF: alle Konten 400000–499999 (mit Umlage-Filter), gleitender 3-Monats-Zeitraum.
   → Andere Konten → andere „Kosten“ (z. B. Portal 388.114 € vs. PDF 444.355 €).

2. **Prognose**
   - Portal: Hochrechnung mit **tatsächlichen Werktagen des Monats** (z. B. 20).
   - PDF: Hochrechnung mit **festem Wert 22** Werktage.
   → Andere Hochrechnung (z. B. Portal 402.014 € vs. PDF 389.006 €).

3. **DB1 aktuell**
   - Kann abweichen durch unterschiedliche Filter (Umlage, G&V, Stichtag).

## Wo steht was

- **Portal:** `api_tek()` baut Umsatz/Einsatz/DB1 selbst, ruft dann `berechne_breakeven_prognose()` (in derselben Datei). **Nutzt get_tek_data nicht** für Breakeven/Prognose.
- **controlling_data.py** behauptet: *„Garantiert 100% Konsistenz zwischen Web-UI und Reports!“* – trifft für Breakeven/Prognose **nicht** zu, weil die Web-UI eine andere Logik verwendet.

## Empfehlung: SSOT einführen

**Eine** fachliche Breakeven/Prognose-Logik als SSOT, genutzt von Portal und von PDF/E-Mail.

- **Sinnvoll als SSOT:** Die **Portal-Logik** (`berechne_breakeven_prognose`), weil:
  - echte Werktage pro Monat,
  - BWA-konforme Kosten (Variable/Direkte/Indirekte),
  - gleitender 3-Monats-Durchschnitt,
  - bereits Standort-/Firma-Filter.

**Umsetzung (Vorschlag):**

1. **Breakeven/Prognose-Logik zentral legen**
   - Option A: `berechne_breakeven_prognose` (und ggf. `berechne_breakeven_prognose_standort`) in ein gemeinsames Modul verschieben, z. B. `api/controlling_data.py` oder neues `api/tek_breakeven.py`.
   - Option B: In `api/controlling_data.py` eine neue Funktion `get_tek_breakeven_prognose(monat, jahr, aktueller_db1, firma_filter_umsatz, firma_filter_kosten, firma_filter_einsatz)` die **dieselbe** Logik wie `berechne_breakeven_prognose` kapselt (evtl. durch Aufruf der aus den Routes ausgelagerten Funktion).

2. **Portal**
   - `api_tek()` ruft weiterhin diese zentrale Funktion (nach Verschiebung/Anbindung).

3. **get_tek_data (PDF/E-Mail)**
   - Statt eigener Breakeven/Prognose-Berechnung:
     - gleiche Filter (firma, standort) wie Portal bauen,
     - **eine** zentrale Breakeven/Prognose-Funktion aufrufen,
     - `gesamt['breakeven']` = `breakeven_schwelle` aus dieser Funktion,
     - `gesamt['prognose']` = `hochrechnung_db1` aus dieser Funktion (mit gleicher Werktage-/Tage-Logik).

4. **Abhängigkeiten**
   - `get_werktage_monat` muss für die SSOT-Funktion verfügbar sein (z. B. aus `controlling_routes` in ein gemeinsames Modul wie `utils/werktage.py` oder in `controlling_data` übernommen).

Ergebnis: **Eine** Berechnung = eine SSOT; Portal und PDF zeigen dieselben Werte für Breakeven und Prognose (bei gleichem Stichtag und gleichen Filtern).

---

## Umgesetzte Lösung (2026-02-13)

- **SSOT:** `api/controlling_data.py` – `berechne_breakeven_prognose()` und `berechne_breakeven_prognose_standort()`.
- **Werktage:** `utils/werktage.py` – `get_werktage_monat(jahr, monat, stichtag=None)`, `get_werktage()` (mit Feiertagen 2025/2026). **Datenstichtag (2026-02-17):** Vor 19:00 Uhr wird Stichtag = gestern übergeben, damit „verbleibend“ den heutigen Tag mitzählt (9 WT morgens), da Locosoft erst abends liefert.
- **Portal:** `routes/controlling_routes.py` importiert Breakeven und Werktage aus den obigen Modulen.
- **PDF/E-Mail:** `get_tek_data()` ruft `berechne_breakeven_prognose()` auf und setzt `gesamt['prognose']` und `gesamt['breakeven']` aus dem Ergebnis.
- **Einsatz-Filter:** In `get_tek_data` wurde `firma_filter_einsatz` ergänzt (TAG157, 6. Ziffer bei Stellantis), damit DB1 und Breakeven mit dem Portal übereinstimmen.
