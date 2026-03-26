# mobile.de — Neueingestellte Inserate & Zukauf-Prüfung (API-Optionen)

**Datum:** 2026-02-12  
**Workstream:** Verkauf  
**Ziel:** Neueingestellte Inserate auf mobile.de möglichst schnell finden und Zukauf durch uns prüfen können (ohne Scraping).

---

## Ausgangslage

- **Scraping** von mobile.de funktioniert nicht — mobile.de blockt das.
- Ihr seid **Kunde** (Händler) und habt Zugang zu mobile.de.
- Ziel: Neue Inserate (auch von anderen Anbietern/Privat) schnell sichten, um Zukauf-Kandidaten zu prüfen.

---

## Ergebnis: Es gibt offizielle APIs

mobile.de bietet unter **https://services.mobile.de/** mehrere APIs. Für euer Ziel (Neueingestellte finden, Zukauf prüfen) sind zwei relevant:

### 1. Search-API (Ad-Integration / Inserats-Einbindung)

- **Zweck:** Suche nach Inseraten nach Kriterien, inkl. **Erstellungs- und Änderungszeit**.
- **Account:** Verfügbar für **API-Account** und **Dealer-Account** (Händlerkunde).
- **Relevante Parameter für „Neueingestellte“:**
  - `creationTime.min` / `creationTime.max` — Inserate **erstellt** nach/vor Zeitpunkt
  - `modificationTime.min` / `modificationTime.max` — Inserate **geändert** nach/vor Zeitpunkt
  - **Sortierung:** `sort.field=modificationTime` & `sort.order=DESCENDING` → neueste zuerst
- **Beispiel-URL (Doku):**  
  `https://services.mobile.de/search-api/search?country=DE&sort.field=modificationTime&sort.order=DESCENDING`
- **Weitere Filter:** Marke/Modell (`classification`), Preis, Kilometer, Erstzulassung, Kraftstoff, Händler/Privat (`customerNumber`/`customerId`) usw.
- **Authentifizierung:** HTTP Basic Auth (Username/Passwort) — Zugangsdaten von mobile.de.
- **Formate:** XML (Legacy), JSON, New XML.

**Einsatz:** Regelmäßiger Abruf (z. B. alle 15–60 Min) mit `creationTime.min=<letzter Lauf>` oder `modificationTime.min=...`, um nur neue/geänderte Inserate zu holen. Kein Scraping nötig.

---

### 2. Ad-Stream (WebSocket, Echtzeit-Push)

- **Zweck:** Push-Meldungen über **neu erstellte und geänderte** Inserate auf der Plattform.
- **Account:** Nur **API-Account** (Aktivierung über Kundenservice).
- **Technik:** WebSocket: `wss://services.mobile.de/ad-stream/events`
- **Events:** z. B. `AD_CREATE_OR_UPDATE` — sobald ein Inserat erstellt/geändert wird und sichtbar ist, bekommt ihr die Meldung inkl. Ad-Daten (Fahrzeug, Preis, Händler, etc.).
- **Filter:** Möglich (z. B. nur Privatverkäufer) — „Please contact Customer Support for filters activation“.
- **Option:** `catchup=true` — bei Wiederverbindung werden verpasste Events der letzten 24 h nachgeliefert.

**Einsatz:** Maximale Geschwindigkeit für „Neueingestellte“ — kein Polling nötig, Push bei jedem neuen/geänderten Inserat. Ideal für Zukauf-Scouting.

---

## Account-Arten (mobile.de Doku)

| Account        | Beschreibung                    | Search-API     | Ad-Stream   |
|----------------|----------------------------------|----------------|------------|
| **Dealer-Account** | An euren Händler-Vertrag gekoppelt | Ja (Credentials aus Dealer-Area) | Nein       |
| **API-Account**   | Zusätzlicher API-Zugang          | Ja (nach Freischaltung) | Ja (nach Freischaltung) |

- **Dealer-Account:** Zugangsdaten ggf. im **Dealer-Area** (Händlerbereich) von mobile.de einsehbar.
- **API-Account:** Freischaltung und Zugangsdaten nur über **mobile.de Kundenservice**.

---

## Nächste Schritte (Empfehlung)

1. **Kurzfristig (ohne zusätzliche Freischaltung):**
   - Im **Dealer-Area** (Händlerbereich) von mobile.de prüfen, ob für euren Account **Search-API** (Ad-Integration) angeboten wird und ob Zugangsdaten (User/Passwort) dort hinterlegt sind.
   - Falls ja: Search-API mit `creationTime.min` / `modificationTime.min` und `sort.field=modificationTime&sort.order=DESCENDING` nutzen; z. B. per Celery-Task alle 15–30 Min abfragen und neue Inserate im Portal anzeigen/zur Zukauf-Prüfung vorhalten.

2. **Für Echtzeit (Neueingestellte möglichst schnell):**
   - Beim **mobile.de Kundenservice** anfragen:
     - **API-Account** anlegen bzw. aktivieren (falls noch nicht vorhanden),
     - **Ad-Stream** freischalten,
     - optional: **Filter** (z. B. nur Privatverkäufer) für den Ad-Stream anfragen.
   - Anschließend im DRIVE Portal einen WebSocket-Client (z. B. Celery Worker oder separater Service) an `wss://services.mobile.de/ad-stream/events` anbinden, Events verarbeiten und neue Inserate zur Zukauf-Prüfung bereitstellen.

3. **Rechtliches/Nutzungsbedingungen:**  
   Vor Implementierung die **API-Nutzungsbedingungen** von mobile.de prüfen (Impressum/API-Doku: https://services.mobile.de/).

---

## Referenzen

- **APIs Übersicht:** https://services.mobile.de/
- **Search-API Doku:** https://services.mobile.de/manual/search-api.html (bzw. https://services.mobile.de/docs/search-api.html)
- **Ad-Stream Doku:** https://services.mobile.de/manual/ad-stream.html
- **Kundenservice Deutschland:** Tel. +49 (0) 30 81097500, [Kontaktformular](https://www.mobile.de/service/contactForm?subject=API+support+request+GERMANY)

---

## Kurzfassung

| Frage | Antwort |
|-------|--------|
| Scraping nutzbar? | Nein — blockiert. |
| Offizielle Alternative? | Ja: **Search-API** (Polling) und **Ad-Stream** (Push). |
| Als Händlerkunde sofort möglich? | Search-API ggf. mit Dealer-Account (im Dealer-Area prüfen). Ad-Stream nur mit API-Account (Kundenservice). |
| Neueingestellte schnell finden? | Ja — Search-API mit `creationTime.min`/Sortierung oder Ad-Stream für Echtzeit. |
| Zukauf prüfen? | Ja — gefundene Inserate (Ad-Daten) im DRIVE anzeigen, verknüpfen, Prüf-Workflow abbilden. |
