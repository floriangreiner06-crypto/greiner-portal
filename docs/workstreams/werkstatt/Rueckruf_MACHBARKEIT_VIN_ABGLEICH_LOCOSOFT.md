# Machbarkeit: Rückruf-VIN-Liste vs. Locosoft („bereits Kunde“ / „noch kein Kunde“)

**Stand:** 2026-02-20  
**Workstream:** werkstatt  
**Auslöser:** Serviceleiter stellt Stellantis-Rückruf-Listen (Excel + Rundschreiben) bereit; Abgleich gewünscht: Welche VINs sind in Locosoft bereits als Kundenfahrzeug vorhanden, welche noch nicht.

---

## 1. Ausgangslage

- **Quelle:** Excel-VIN-Listen von Stellantis (Rückrufe), unterschiedliche Rundschreiben pro Kampagne.
- **Ablage:** `docs/workstreams/werkstatt/Rückruf/` (Sync: `F:\Greiner Portal\Greiner_Portal_NEU\Server\docs\workstreams\werkstatt\Rückruf`).
- **Aktueller Inhalt (Beispiel):**
  - `KBM_de_DE.pdf` — Rundschreiben
  - `KBM_PLZ_94_1.xlsx` — VIN-Liste (Beispiel: erste Spalte = VIN, 17 Zeichen; weitere Spalten PLZ, Ort, Codes, ggf. Kundennummer/Name).
- **Anforderung:** Abgleich der VINs gegen Locosoft: „in Locosoft vorhanden“ (= bereits Kunde) vs. „noch kein Kunde“.

**Wichtig:** Die Excel-Listen für Rückrufe können von Rundschreiben zu Rundschreiben **unterschiedliche Spaltenlayouts** haben (VIN mal in Spalte A, mal woanders; mit oder ohne Kopfzeile).

---

## 2. Technische Machbarkeit — Kurzfassung

**Ja, machbar.** Es gibt im Projekt bereits alle nötigen Bausteine:

| Aspekt | Bewertung | Referenz im Projekt |
|--------|-----------|----------------------|
| Excel einlesen (variable Spalten) | Ja | `scripts/afa_abgleich_excel_locosoft.py`, `scripts/afa_vergleiche_buchhaltung_excel.py` (openpyxl, Header-Erkennung, Spalten-Mapping) |
| VIN in Excel erkennen | Ja | VIN-Spalte per Header („VIN“, „FIN“, „Fahrgestellnummer“) oder per Muster: 17 Zeichen, Zeichensatz ISO 3779 |
| Abfrage Locosoft „Fahrzeug mit VIN vorhanden?“ | Ja | Locosoft-Tabelle `vehicles` (Spalte `vin`); `get_locosoft_connection()`; Abfrage wie in `api/afa_api.py` oder View `loco_vehicles` in Fahrzeuganlage |
| VIN-Normalisierung | Ja | `api/fahrzeugschein_scanner.py`: `_normalize_vin`; optional Fuzzy (levenshtein) wie in Fahrzeuganlage |

**Hinweis Datenquelle:** Für „ist in Locosoft vorhanden?“ ist die **direkte Locosoft-Abfrage** (`vehicles.vin`) die passende SSOT; Portal-View `loco_vehicles` nur, wenn bewusst auf den Spiegel abgestellt wird.

---

## 3. Variable Spalten in Excel

- **Strategie 1 (empfohlen):** Kopfzeile suchen; Spalte mit „VIN“, „FIN“, „Fahrgestellnummer“ etc. → Spaltenindex für VIN.
- **Strategie 2:** Keine Kopfzeile: Zelle mit 17-stelligem VIN-Muster finden; sofern nur eine Spalte passt, diese als VIN-Spalte verwenden.
- **Strategie 3:** Konfiguration pro Datei (z. B. „VIN in Spalte A“) als Fallback.

Beispiel **KBM_PLZ_94_1.xlsx:** Keine Kopfzeile; erste Spalte = VIN (17 Zeichen).

---

## 4. Abgleichlogik (konzeptionell)

1. **Eingabe:** Excel-Datei(en) aus Rückruf-Ordner (oder konfigurierbar).
2. **VIN-Extraktion:** Pro Zeile VIN ermitteln (Header oder Muster); Duplikate ignorieren oder kennzeichnen.
3. **Normalisierung:** VIN trimmen, Leerzeichen/Bindestriche entfernen; nur 17 Zeichen gültige VINs.
4. **Locosoft-Abfrage:** `SELECT 1 FROM vehicles WHERE vin IS NOT NULL AND TRIM(vin) = %s`; optional Fuzzy-Match.
5. **Ausgabe:** „in Locosoft vorhanden“ / „nicht in Locosoft“; CSV oder Portal-Anzeige.

---

## 5. Mögliche Umsetzungsformen

- **Skript (CLI):** Analog `afa_abgleich_excel_locosoft.py`: Excel-Pfad, Ausgabe Konsole + optional CSV.
- **Portal-Modul:** Upload/Auswahl Excel, Abgleich, Ergebnis-Tabelle im Browser (Service/Werkstatt).

---

## 6. Abhängigkeiten / Risiken

- **openpyxl:** Bereits im Einsatz; in `requirements.txt` prüfen.
- **Locosoft:** Nur sinnvoll bei erreichbarer Locosoft-DB; Timeout/Fehlerbehandlung einplanen.
- **Datenschutz:** Rückruf-Listen nur intern; keine Weitergabe.

---

## 7. Nächste Schritte (wenn gewünscht)

1. Entscheidung: Nur Skript oder plus Portal-UI?
2. VIN-Erkennung: automatisch (Header + Muster) oder plus Konfiguration?
3. Implementierung: Skript zuerst (ein Excel, VIN auto/konfigurierbar, Abgleich, CSV-Report); bei Bedarf Portal.

---

## 8. Referenzen im Repo

- Locosoft-Schema: `docs/DB_SCHEMA_LOCOSOFT.md` (Tabelle `vehicles`, Spalte `vin`).
- Excel-Abgleich AfA: `scripts/afa_abgleich_excel_locosoft.py`.
- VIN/Dublettencheck: `api/fahrzeugschein_scanner.py`, `api/fahrzeuganlage_api.py` (check_duplicate).
- Locosoft: `api/db_utils.py` → `get_locosoft_connection()`.
