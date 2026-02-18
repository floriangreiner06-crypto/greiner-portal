# Auswertung: HAR-Dateien personal-login.de (kvg-hzf)

**Datum:** 2026-02  
**Dateien:**  
- `kvg-hzf.personal-login.de_Berechtigungen.har` (pageId 87)  
- `kvg-hzf.personal-login.de_Arbeitszeitmodell.har` (pageId 11, Mitarbeiter-Maske)

---

## Bringen die HARs was?

**Ja – für Verständnis und Nachbau von Logik.**  
**Nein – es gibt keine REST-API zum Anbinden.**

---

## Was die HARs zeigen

### 1. Keine API, nur Form-POSTs

- **Alle relevanten Requests:** `POST https://kvg-hzf.personal-login.de/` (gleiche URL).
- **Kein** `/api/...`, kein JSON-Request/Response für Fachdaten.
- Antworten sind **HTML** (vollständige Seiten), keine strukturierten JSON-Daten.

→ Eine saubere Integration „per API“ ist so nicht möglich. Wer automatisieren will, müsste Formulare nachbilden und HTML parsen (oder den Anbieter nach API/Export fragen).

### 2. Session & Navigation

- **Session:** Parameter `ses` (z.B. `ses=24vkna971focjun8mh2eamoiqq`) – Session-ID, bei jedem Request mitgeschickt.
- **Seitensteuerung:** `pageId` + ggf. `pageName`, `modul`, `popup`, `sicht`, `viewDS` usw.
  - **pageId=11:** Mitarbeiter-Stammdaten / Arbeitszeitmodell (eine konkrete MA-Maske).
  - **pageId=87:** Berechtigungen (`viewDS=226`).
- Weitere Requests: nur statische Ressourcen (JS, CSS, Bilder) unter `/versionen/v2.5.8/`, `/global/` usw.

→ Die HARs dokumentieren, **wie** man sich in der Anwendung bewegt (welche Parameter für welche Seite). Nützlich, um Nachbau oder automatisierte Navigation zu verstehen – nicht für eine offizielle API.

### 3. Datenmodell Urlaub (aus Arbeitszeitmodell-HAR)

Über die Form-Parameter sieht man **Feldnamen** des Referenzsystems (ohne personenbezogene Werte hier zu wiederholen):

| Parameter | Bedeutung (erschlossen) |
|-----------|-------------------------|
| `ds_URLAUB_ANSPRUCH` | Urlaubsanspruch (z.B. 27) |
| `ds_full_UP_MAX_UEBERTRAG`, `ds_dez_UP_MAX_UEBERTRAG` | Max. Übertrag (z.B. 999) |
| `ds_MAXURLAUBLAENGE` | Max. Urlaubslänge (z.B. 14) |
| `ds_UP_KEIN_VERFALL` | Kein Verfall (Flag) |
| `ds_date_UP_BUCHEN_VON` / `_BIS` | Buchungszeitraum |
| `ds_UP_WF_MAIN_ID`, `ds_UP_WF_AUSGLEICH_MAIN_ID` | Workflow-/Ausgleichs-ID |
| `ds_UP_WERTUNGSSKRIPTE_ID` | Wertungsskript |
| `ds_UP_FREISCHALTUNG` | Freischaltung Urlaubsplaner |
| Weitere `ds_*` | Stammdaten (Name, Eintritt, etc.), `ro_*` = read-only |

→ Nützlich als **Referenz für Feature-Parität**: welche Konzepte (Anspruch, Übertrag, Max-Länge, Workflow, Freischaltung) es im Referenzsystem gibt und wie sie heißen. Für DRIVE-Urlaubsplaner kann man daraus eine Checkliste für Felder/Logik ableiten.

### 4. Technologie

- Version aus Pfaden: **v2.5.8** (Personal-Planer).
- Klassisches Stack: Form-POSTs, jQuery, DataTables, Chosen, WYSIWYG, jsTree – keine SPA mit eigenem REST-Backend.

---

## Fazit für den DRIVE-Urlaubsplaner

| Frage | Antwort |
|-------|---------|
| **Bringen die HARs was?** | Ja: Verständnis von Navigation (pageId, ses), von Feldnamen und Urlaubs-Logik (ds_URLAUB_*, ds_UP_*). |
| **Eignung für API-Integration?** | Nein – keine API, nur HTML-Formulare. |
| **Eignung für Scraper?** | Theoretisch: Form-Parameter und Reihenfolge sind sichtbar; praktisch: Session-Handling, HTML-Parsing und Pflegeaufwand bleiben hoch; rechtlich/ToS prüfen. |
| **Pragmatischer Nutzen** | Feldnamen und Konzepte als **Feature-Referenz** nutzen; fehlende Funktionen im DRIVE-Urlaubsplaner gezielt nachbauen (ohne Abhängigkeit von Scraping). |

---

## Empfehlung

1. **HARs als Referenz behalten** – für Begriffe und Felder (Anspruch, Übertrag, Max-Länge, Workflow, Freischaltung etc.).
2. **Keine Integration per Scraper** auf Basis dieser HARs ohne Klärung mit dem Anbieter.
3. **Feature-Liste** aus den erkannten Konzepten ableiten und im DRIVE-Urlaubsplaner schrittweise umsetzen (Daten aus Locosoft/Portal, nicht aus personal-login).

---

**Hinweis:** In den HAR-Dateien stehen reale Stammdaten (Name, Adresse, E-Mail, Geburtsdatum etc.). Für Weitergabe oder Versionierung HARs anonymisieren oder nur diese Auswertung weitergeben.
