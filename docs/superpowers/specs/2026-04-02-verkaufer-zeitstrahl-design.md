# Verkäufer-Zeitstrahl im Auftragseingang

## Zusammenfassung

Jeder Verkäufer sieht im Auftragseingang seinen persönlichen Fortschritt gegenüber NW- und GW-Zielen — sowohl in der Monats- als auch in der Jahresansicht. Die Verkaufsleitung (VKL), Geschäftsleitung (GL) und Vanessa sehen den Fortschritt aller Verkäufer.

## Anforderungen

### Zieldaten

- **NW (Neuwagen):** Normales Monatsziel (groß, mit Fortschrittsbalken) + kumuliertes Ziel aus der Zielprämie als kleiner Reminder darunter (nur Text, kein Balken). Kumuliert = Summe der Monatsziele Jan bis aktueller Monat, wie in `get_kumulierte_zielpraemie_daten()`.
- **GW (Gebrauchtwagen):** Normales Monatsziel aus `verkaeufer_ziele` / Saisonalität.

### Sichtbarkeit

- **Rolle `verkauf` (own_only):** Sieht nur eigenen Zeitstrahl.
- **VKL, GL, Vanessa (all_filterable):** Sehen Zeitstrahl für alle Verkäufer in der Tabelle. Bei Einzelfilter: Hero-Card für den gefilterten Verkäufer.
- Nutzt das bestehende `feature_filter_mode`-System.

### Farbschwellen

| Erfüllung | Farbe |
|-----------|-------|
| >= 100% | Grün (#198754) |
| 75–99% | Orange (#e67e22) |
| < 75% | Rot (#dc3545) |

### Nur absolut

Keine Zeitbereinigung — rein IST vs. Ziel.

## Design

### Komponente 1: Hero-Card (über der Tabelle)

Erscheint wenn ein einzelner Verkäufer gefiltert ist (oder bei Rolle `verkauf`).

#### Monatsansicht

- Überschrift: "Dein Monatsfortschritt — April 2026 — Roland Huber"
- Zwei Ziel-Boxen nebeneinander:
  - **NW:** Große Zahl "8 / 12", Fortschrittsbalken, "67% Zielerfüllung". Darunter dezenter Kum.-Reminder: "Kum. Jan–Apr: 33 / 42 (79%)" — nur Text, gestrichelter Trennstrich.
  - **GW:** Große Zahl "3 / 5", Fortschrittsbalken, "60% Zielerfüllung".
- Darunter: Mini-Timeline (12 Balken für Monate), Farbe nach kumulierter NW-Zielerfüllung, aktueller Monat hervorgehoben, zukünftige Monate grau.

#### Jahresansicht

- Überschrift: "Dein Jahresfortschritt 2026 — Roland Huber"
- Badge oben rechts: "79% NW kum."
- Zwei Ziel-Boxen nebeneinander:
  - **NW:** Große Zahl "33 / 120" (Jahresziel), Fortschrittsbalken, "28% vom Jahresziel". Kum.-Reminder: "Kum. Ziel bis Apr: 33 / 42 (79%)". Darunter Detail-Tabelle mit zwei Zeilen: Monat (Ist/Ziel pro Monat) und Kum. (kumuliert Ist/Ziel).
  - **GW:** Große Zahl "21 / 60" (Jahresziel), Fortschrittsbalken, "35% Zielerfüllung". Detail-Tabelle mit einer Zeile: Monat (Ist/Ziel).

### Komponente 2: Inline-Balken in Verkäufer-Tabelle

Erscheint für VKL/GL/Vanessa wenn "Alle Verkäufer" gewählt.

#### Monatsansicht — zwei neue Spalten

- **Ziel NW:** Fortschrittsbalken "8/12 (67%)" + darunter winzige Zeile "kum. 33/42 (79%)"
- **Ziel GW:** Fortschrittsbalken "3/5 (60%)"

#### Jahresansicht — zwei neue Spalten

- **NW Jahresziel:** Fortschrittsbalken "33/120 (28%)" + darunter winzige Zeile "kum. 33/42 (79%)"
- **GW Jahresziel:** Fortschrittsbalken "21/60 (35%)"

## Datenquellen

| Datenpunkt | Quelle | Funktion/Endpoint |
|------------|--------|-------------------|
| NW Monatsziel pro Verkäufer | verkaeufer_ziele + Saisonalität | `get_nw_ziel_verkaeufer_monat()` |
| NW kumuliertes Ziel | Summe Monatsziele Jan–aktuell | `get_kumulierte_zielpraemie_daten()` |
| GW Monatsziel pro Verkäufer | verkaeufer_ziele + Saisonalität | Monatsziele-API |
| NW/GW Ist (Monat) | sales-Tabelle | Auftragseingang-Detail-API |
| NW/GW Ist (Jahr kumuliert) | sales-Tabelle | Jahresübersicht-API |
| Jahresziel NW/GW | verkaeufer_ziele | Zielplanung-API |

## Betroffene Dateien

- `templates/verkauf_auftragseingang.html` — Hero-Card + Inline-Balken im JS-Rendering
- `api/verkauf_api.py` — Jahresübersicht-Endpoint erweitern (pro Verkäufer)
- `api/provision_service.py` — `get_kumulierte_zielpraemie_daten()` als SSOT für kum. NW-Ziele
- `api/verkaeufer_zielplanung_api.py` — Monatsziele-API (bereits vorhanden)

## Mockup

Statisches Mockup: `static/mockups/zeitstrahl_verkauf_v3.html`
