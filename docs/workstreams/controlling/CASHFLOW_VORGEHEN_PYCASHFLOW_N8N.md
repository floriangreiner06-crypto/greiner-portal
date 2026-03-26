# Cashflow-Modul: Vorgehen, PyCashFlow-Ideen, n8n-Einschätzung

**Workstream:** Controlling  
**Stand:** 2026-03-02

---

## 1. Wie gehen wir jetzt vor?

### Empfohlene Reihenfolge

| Phase | Inhalt | Abhängigkeiten |
|-------|--------|----------------|
| **0 – Datenbasis klären** | **Cashflow Data Audit** ausführen (Prompt: `CURSOR_PROMPT_CASHFLOW_ANALYSE.md`). Ergebnis: `CASHFLOW_DATA_AUDIT.md` mit „Vorhanden / Aufbereitung nötig / Manuell / Ungeklärt“. | Keine – nur Analyse, kein Code. |
| **1 – Sofort nutzbar** | Auf Basis des Audits: (1) **IST-Vorschau** aus bestehenden Daten: Salden (v_aktuelle_kontostaende/salden) + Transaktionen (kategorisiert) + Tilgungen (tilgungen) als Zeitreihe „Saldo + erwartete Bewegungen“. (2) Ggf. fehlende Kategorien in der bestehenden Kategorisierung ergänzen (Regeln/KI). | Kategorisierung läuft schon; Tilgungen-Tabelle vorhanden. |
| **2 – Nach Konfiguration** | **Geplante Zahlungen** abbilden: Wiederkehrende Posten (z. B. Gehalt, Miete, USt) entweder aus Transaktions-Mustern ableiten oder in neuer Tabelle „geplante_cashflow_positionen“ (Datum, Betrag, Typ, Kategorie) pflegen. Projektionslogik: Laufender Saldo + IST-Transaktionen + geplante + Tilgungen. | Audit zeigt, was aus FIBU/Locosoft automatisch kommt; Rest manuell oder halbautomatisch. |
| **3 – Mittelfristig** | Hersteller-Abschläge (E4), Fahrzeugeinkauf (A1) aus Locosoft/FIBU in die Prognose einbeziehen; Mindestbestand-Warnung; optional E-Mail-Report „Liquiditätsvorschau“. | Klärung mit Florian/Buchhaltung, welche Konten/Buchungstexte für E4/A1 genutzt werden (siehe Audit „Ungeklärt“). |

### Konkret als nächster Schritt

1. **Data Audit durchführen** (mit dem angepassten Prompt): Schritte 1–9 aus `CURSOR_PROMPT_CASHFLOW_ANALYSE.md` auf drive_portal + Locosoft-Spiegel ausführen, Befunde in `CASHFLOW_DATA_AUDIT.md` dokumentieren.
2. **Audit auswerten:** Phase-1-Liste (sofort nutzbar) vs. Phase-2/3 (Konfiguration/Rückfragen).
3. **Kleinstes lieferbares Modul definieren:** Z. B. „Liquiditätsvorschau 30/60/90 Tage“ = heutiger Gesamtsaldo + Transaktionen bis Stichtag + Tilgungen (tilgungen) + optional erste „geplante“ Fixposten aus Regeln/Muster.
4. **Implementierung:** Eine SSOT für die Projektion (z. B. in `api/controlling_data.py` oder neues Modul `api/cashflow_vorschau.py`), API für Frontend, Route unter Controlling; Darstellung Chart + Tabelle (analog TEK/Dashboard).

---

## 2. Können wir uns von PyCashFlow etwas abschauen?

**Ja – Konzepte und Logik, kein Code-Import.** PyCashFlow ist ein eigenständiges Produkt (eigenes Auth, eigenes Datenmodell, keine MT940/Locosoft-Anbindung). Für DRIVE sinnvoll sind:

| Von PyCashFlow | Nutzen im DRIVE |
|----------------|-----------------|
| **12-Monats-Projektion als Zeitreihe** | Vorschau als „Saldo pro Tag/Woche/Monat“ über N Monate; Ausgabe: Liste/Chart mit Laufendem Saldo. |
| **Wiederkehrende Transaktionen (Frequenzen)** | Logik für „monatlich“, „wöchentlich“, „quartalsweise“ – bei uns: entweder aus `transaktionen` (Mustererkennung) oder aus Tabelle „geplante_cashflow_positionen“ mit Frequenz + nächstem Fälligkeitsdatum. |
| **Business-Day-Logik** | Wochenende: Gehalt/Einzahlung „letzter Werktag davor“, Ausgabe „nächster Werktag danach“ – optional für Plan-Positionen; DRIVE hat bereits `utils/werktage.py` (TEK). |
| **Laufender Saldo (running balance)** | Pro Datum: Saldo = Saldo Vortag + Einzahlungen − Auszahlungen. Bei uns: Start aus v_aktuelle_kontostaende, dann Transaktionen + geplante + Tilgungen durchiterieren. |
| **Mindestbestand-Warnung** | Wenn projizierter Saldo unter Schwellwert (z. B. konfigurierbar pro Konto oder global) → Hinweis im UI oder im Report. |
| **60-Tage-Transaktions-Preview** | Als Liste „erwartete Bewegungen“ (aus Plan + Tilgungen) für die nächsten 60 Tage – gut für DRIVE als Tabelle unter dem Chart. |

**Nicht übernehmen:** Eigenes User-/Account-Modell, IMAP-Salden-Update (wir haben MT940/PDF-Import), Passkey/Corbado, Docker-first-Deployment. Unsere Datenquelle ist Bankenspiegel + Locosoft + tilgungen, nicht PyCashFlow-Schedules.

**Technik:** PyCashFlow nutzt Pandas/NumPy für Berechnungen und Plotly für Charts. Im DRIVE: Berechnung in Python (ohne zwingend Pandas), Frontend Chart.js (wie TEK/Bankenspiegel) oder Plotly nur wenn gewünscht.

---

## 3. Einsatz von n8n für Workflow – Einschätzung

### Was ist n8n?

n8n ist eine Open-Source-Workflow-Automatisierung (Self-hosted oder Cloud): visuelle Knoten für Trigger (Cron, Webhook, E-Mail) und Aktionen (HTTP, DB, E-Mail, Script). Typisch für: Integration externer Dienste, wiederkehrende Abläufe ohne Code, schnelle Anpassung durch Fachabteilung.

### Aktueller Stand im DRIVE

- **Kein n8n im Einsatz.** Geplante/wiederkehrende Abläufe laufen über **Celery + Redis** (Beat für Cron-ähnliche Tasks), z. B. MT940-Import, TEK-E-Mail, AfA-Bericht, Sync zu Locosoft.
- APIs und Business-Logik liegen in **Flask**; Daten in **PostgreSQL**.

### Wann wäre n8n sinnvoll?

| Szenario | Mit n8n | Ohne n8n (DRIVE-Stand) |
|----------|---------|--------------------------|
| **MT940-Import zeitgesteuert** | n8n-Cron → Aufruf Script/API | ✅ Celery Beat + Task `import_mt940` |
| **Transaktionen kategorisieren (täglich)** | n8n-Cron → HTTP POST Kategorisieren-API | ✅ Celery Task oder manuell/on-demand |
| **Bei neuem Bank-PDF etwas auslösen** | n8n Webhook + Aktion | ✅ Watch-Ordner + Script oder Celery |
| **E-Mail „Liquiditätswarnung“ bei Unterschreitung** | n8n-Cron → DB abfragen → E-Mail | ✅ Celery Task + gleiche Logik |
| **Viele externe SaaS anbinden (z. B. Buchhaltung, Banking-API)** | n8n als Kleber zwischen Diensten | DRIVE spricht direkt mit Locosoft/DB; Banking = MT940-Dateien |

### Einschätzung: **für Cashflow-Modul aktuell nicht nötig**

- **Redundanz:** Alles, was n8n für Cashflow tun würde (zeitgesteuerte Jobs, DB lesen, E-Mails versenden), deckt ihr bereits mit **Celery** und **Flask** ab. Ein zweites Orchestrierungssystem erhöht Wartung, Dokumentation und Fehlerquellen („Läuft das jetzt in n8n oder in Celery?“).
- **SSOT:** Projektionslogik und Auslöser sollten im DRIVE-Code liegen (eine Codebasis, eine Config), nicht in n8n-Workflows verteilt.
- **Sinnvoll wäre n8n**, wenn ihr künftig **viele** externe Systeme (z. B. Open-Banking-APIs, weitere Cloud-Dienste) **ohne Python-Code** anbinden oder von Fachabteilungen **visuell** Workflows anpassen lassen wollt. Das ist für die aktuelle Cashflow-Vorschau und die bestehende Architektur (MT940, Locosoft, PostgreSQL) nicht die Anforderung.

### Empfehlung

- **Cashflow-Workflows (Import, Kategorisierung, Reports, Warnungen)** weiter mit **Celery + Flask** umsetzen.
- **n8n** nur einführen, wenn es einen **konkreten** Use Case gibt, den Celery/Flask schlecht abdecken (z. B. viele unterschiedliche Webhook-Quellen, stark wechselnde Integrationen durch Nicht-Entwickler). Dann n8n **zusätzlich** und klar getrennt von der DRIVE-Kernlogik (n8n ruft DRIVE-APIs auf, nicht umgekehrt).

---

## 4. Kurzfassung

| Frage | Antwort |
|-------|---------|
| **Vorgehen** | (0) Data Audit mit `CURSOR_PROMPT_CASHFLOW_ANALYSE.md` → (1) IST-Vorschau aus Salden + Transaktionen + Tilgungen → (2) Geplante Positionen (Tabelle oder Muster) → (3) Hersteller/Fahrzeugeinkauf, Warnung, Report. |
| **PyCashFlow** | Konzepte abschauen: Zeitreihe Projektion, Frequenzen, Laufender Saldo, Business Days, Mindestbestand-Warnung, Preview-Liste. Kein Code-Import; Datenbasis bleibt Bankenspiegel + Locosoft + tilgungen. |
| **n8n** | Für das Cashflow-Modul **nicht empfohlen**; Celery + Flask decken Zeitsteuerung und Logik ab. n8n nur erwägen, wenn später viele externe Systeme/visuelle Workflows ohne Code gewünscht sind. |
