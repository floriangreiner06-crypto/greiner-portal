W# WORKFLOW-ANLEITUNG: Taegliche Entwicklung und Deployment

**Zielgruppe:** Florian (Projektleiter/Entwickler) und Vanessa (Tester/Entwicklerin)
**Stand:** 2026-03-27

---

## 1. Taegliche Arbeit

So laeuft ein normaler Arbeitstag ab:

1. **VS Code oeffnen** auf dem lokalen Rechner
2. **SSH-Verbindung herstellen** zu `10.80.80.20` (ag-admin)
3. **Ordner oeffnen:** `/opt/greiner-test/` (das ist die Entwicklungsumgebung, NICHT Produktion)
4. **Session starten:** `/session-start` eintippen — Claude laedt den Kontext und zeigt offene Aufgaben
5. **Arbeiten:** Code aendern, Funktionen bauen, Bugs beheben
6. **Testen:** Im Browser `http://drive:5002` oeffnen — das ist die Test-Instanz
7. **Commit erstellen:** `/commit` eintippen — Claude schreibt die Commit-Message und committet
8. **Session beenden:** `/session-end` eintippen — Claude aktualisiert die Doku und erstellt ein Wrap-Up

---

## 2. Feature fertig deployen

Wenn ein Feature fertig entwickelt und getestet ist und in Produktion soll:

1. `/deploy` eintippen
2. Claude fuehrt automatisch durch:
   - Pusht `develop` nach Remote
   - Merged `develop` nach `main` (via Git)
   - Startet den Produktions-Service neu
   - Pusht `main` und prueft den Service-Status

**Ergebnis:** Das neue Feature laeuft auf `http://drive` (Produktion, Port 80).

---

## 3. Bug in Produktion beheben (Hotfix)

Wenn ein kritischer Bug direkt in Produktion behoben werden muss:

1. **Zweites VS Code Fenster oeffnen** (parallel zum Entwicklungs-Fenster)
2. **SSH-Verbindung** zu `10.80.80.20`
3. **Ordner oeffnen:** `/opt/greiner-portal/` (das ist Produktion, hier nur fuer Hotfixes!)
4. **Bug beheben** — nur die betroffene Datei/Stelle anfassen
5. `/hotfix` eintippen — Claude committet den Fix, synchronisiert ihn rueckwaerts nach Develop und startet Produktion neu

**Ergebnis:** Der Fix ist sowohl in Produktion (`main`) als auch in der Entwicklungsumgebung (`develop`) vorhanden. Kein Auseinanderlaufen der Branches.

---

## 4. Vanessa holt Updates

Wenn Florian Aenderungen committed hat und Vanessa mit dem aktuellen Stand arbeiten moechte:

1. `/sync` eintippen
2. Claude pullt den aktuellen `develop`-Stand und startet die Test-Instanz neu falls noetig

**Ergebnis:** `/opt/greiner-test/` ist auf dem neuesten Stand, `drive:5002` zeigt die aktuellen Aenderungen.

---

## 5. Dos and Don'ts

| | Was | Warum |
|---|---|---|
| **DO** | In `/opt/greiner-test/` entwickeln | Das ist die sichere Entwicklungsumgebung, Produktion bleibt stabil |
| **DO** | `/commit` zum Committen nutzen | Saubere Commit-Messages, CONTEXT.md wird automatisch aktualisiert |
| **DO** | `/deploy` zum Deployen nutzen | Korrekte Merge-Reihenfolge, kein vergessener Neustart |
| **DO** | Auf `drive:5002` testen | Test-Instanz ist von Produktion getrennt |
| **DO** | `/sync` fuer Updates nutzen | Sicherere Alternative zu manuellem `git pull` |
| **DO** | `/hotfix` fuer Produktions-Bugs nutzen | Haelt develop und main synchron |
| **DON'T** | In `/opt/greiner-portal/` entwickeln | Direkte Aenderungen in Produktion — ausser bei explizitem Hotfix |
| **DON'T** | Dateien manuell per `cp` oder `rsync` kopieren | Umgeht Git, erzeugt unkontrollierte Staende |
| **DON'T** | `git pull` manuell ausfuehren | Kann Konflikte erzeugen, Doku wird nicht aktualisiert |
| **DON'T** | Auf `drive` (Produktion) testen | Echte Nutzer sehen fehlerhafte Zwischenzustaende |

---

## 6. Befehlsuebersicht

| Befehl | Beschreibung | Wann nutzen |
|--------|-------------|-------------|
| `/session-start` | Laedt Kontext, zeigt offene Aufgaben und letzten Stand | Zu Beginn jeder Arbeitssitzung |
| `/session-end` | Aktualisiert Doku, erstellt Wrap-Up, committed Aenderungen | Am Ende jeder Arbeitssitzung |
| `/commit` | Erstellt Git-Commit mit passender Message | Nach abgeschlossenem Teilschritt oder Feature |
| `/deploy` | Merged develop nach main, deployed in Produktion | Wenn Feature fertig und getestet ist |
| `/hotfix` | Committed Fix direkt in main, synchronisiert nach develop | Bei kritischen Bugs in Produktion |
| `/sync` | Aktualisiert lokalen develop-Stand | Wenn Vanessa Florians neue Commits holen will |
| `/test` | Startet oder prueft die Test-Instanz auf drive:5002 | Nach groesseren Aenderungen am Backend |
| `/status` | Zeigt Git-Status, Service-Status und offene TODOs | Zur Orientierung waehrend der Session |
| `/logs` | Zeigt aktuelle Service-Logs (greiner-portal, celery) | Bei Fehlern oder unerwartetem Verhalten |
| `/db` | PostgreSQL-Abfragen (erkennt Prod/Dev automatisch) | Bei Daten pruefen oder Debugging |

---

## 7. Welcher Ordner wofuer

```
SERVER: 10.80.80.20 (auto-greiner.de)
|
+-- /opt/greiner-test/          ENTWICKLUNGSUMGEBUNG
|   |
|   |-- Branch:    develop
|   |-- URL:       http://drive:5002
|   |-- Datenbank: drive_portal_dev
|   |-- Zweck:     Hier wird entwickelt und getestet
|   |              Kein Risiko fuer echte Nutzer
|   |
|   +-- Wer arbeitet hier?
|       - Florian (taeglich)
|       - Vanessa (taeglich)
|
+-- /opt/greiner-portal/        PRODUKTION
    |
    |-- Branch:    main
    |-- URL:       http://drive  (Port 80)
    |-- Datenbank: drive_portal
    |-- Zweck:     Laufendes System fuer alle Mitarbeiter
    |              Nur via /deploy oder /hotfix veraendern
    |
    +-- Wer arbeitet hier?
        - Niemand direkt (ausser Hotfix-Szenario)
        - Aenderungen kommen ausschliesslich durch /deploy oder /hotfix
```

### Fluss einer normalen Aenderung

```
Entwicklung              Test                    Produktion
     |                     |                          |
/opt/greiner-test/   drive:5002              /opt/greiner-portal/
   (develop)          (Test-URL)                  (main)
     |                     |                          |
     | Code aendern        |                          |
     +-------------------->|                          |
     |               Testen & pruefen                 |
     |                     |                          |
     |  /deploy            |                          |
     +----------------------------------------------->|
                                               Mitarbeiter sehen
                                               neue Funktion
```

### Fluss eines Hotfixes

```
/opt/greiner-portal/    /opt/greiner-test/
    (main/Prod)             (develop)
         |                      |
   Bug entdeckt                 |
         |                      |
   /hotfix ausfuehren           |
         |                      |
   Fix in main  <-- Claude -->  Fix auch in develop
         |                      |
   Produktion neu gestartet      |
                           naechstes /sync
                           holt den Fix
```

---

## Hinweise

- **Passwort:** Niemals Passwoerter im Chat oder in Kommandos tippen. Claude nutzt `sudo -n` mit hinterlegten NOPASSWD-Regeln.
- **Templates:** Aenderungen an HTML-Templates brauchen keinen Service-Neustart — Strg+F5 im Browser genuegt.
- **Python/Backend:** Nach jeder Aenderung an `.py`-Dateien ist ein Neustart des Services noetig. Claude erledigt das automatisch bei `/commit`, `/deploy` und `/hotfix`.
- **Datenbank-Migrationen:** Neue `.sql`-Dateien in `migrations/` werden von Claude automatisch ausgefuehrt — nicht manuell per psql.
