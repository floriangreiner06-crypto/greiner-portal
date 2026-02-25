# AfA: Automatisierung Bestand DRIVE/Locosoft + E-Mail-Report

**Stand:** 2026-02-25  
**Workstream:** Controlling (AfA-Modul)  
**Ziel:** Abgleich „AfA-Bestand DRIVE“ vs. „Bestand Locosoft“ automatisieren und Ergebnis per E-Mail melden (neue Fahrzeuge in Locosoft, offene Abgänge in DRIVE).

---

## 1. Ausgangslage

- **„Bestand laden“** im AfA-Dashboard ruft `GET /api/afa/locosoft-kandidaten` auf und zeigt VFW/Mietwagen aus Locosoft, die **noch nicht** in `afa_anlagevermoegen` sind → manueller Klick nötig.
- **Abgangs-Kontrolle** (`GET /api/afa/abgangs-kontrolle`) vergleicht DRIVE mit Locosoft: „DRIVE aktiv, Locosoft verkauft“ → „Bitte Abgang in DRIVE prüfen“; „Abgang in DRIVE“ mit Locosoft-Rechnungsdatum.
- Beides soll **automatisch** laufen und als **E-Mail-Report** an Buchhaltung/Controlling gehen.

---

## 2. Ziel des Reports

**E-Mail enthält:**

1. **Neue Fahrzeuge in Locosoft (noch nicht in AfA DRIVE)**  
   - Liste wie „Bestand laden“: Kennzeichen, VIN, Bezeichnung, Art (VFW/Mietwagen), Anschaffung, EK netto.  
   - Handlungsaufforderung: „Bitte im AfA-Modul prüfen und ggf. importieren.“

2. **Bitte Abgang in DRIVE prüfen**  
   - Fahrzeuge, die in DRIVE noch **aktiv** sind, in Locosoft aber **verkauft** (Rechnungsdatum gesetzt).  
   - Handlungsaufforderung: „Abgang in DRIVE erfassen.“

Optional (später): Kurze Sektion „Abgang in DRIVE“ (bereits abgegangen, mit Locosoft-Datum zur Kontrolle) oder nur bei Abweichungen senden.

---

## 3. Datenquellen (Wiederverwendung, keine neuen Logiken)

| Inhalt Report        | Quelle im System |
|---------------------|------------------|
| Neue in Locosoft     | Gleiche Logik wie `GET /api/afa/locosoft-kandidaten`: Locosoft-Abfrage (VFW/Mietwagen, `out_invoice_date IS NULL`) minus bereits in `afa_anlagevermoegen` vorhandene VINs/IDs. Entweder API intern aufrufen oder dieselbe SQL/Helper in einem Script/Task nutzen. |
| Abgang prüfen       | Gleiche Logik wie `GET /api/afa/abgangs-kontrolle`: DRIVE `afa_anlagevermoegen` (aktiv) mit Locosoft `out_invoice_date` abgleichen. |

Referenz-Implementierung: `api/afa_api.py` – `locosoft_kandidaten()`, `abgangs_kontrolle()`.

---

## 4. Konkrete Umsetzungsschritte

### 4.1 Datenbeschaffung im Task/Script

- **Option A (empfohlen):** Neues Script (z. B. `scripts/send_afa_bestand_report.py`) oder Celery-Task ruft die **bestehende API-Logik** auf (z. B. per HTTP GET gegen lokales Flask oder durch direkten Import und Aufruf der Funktionen aus `afa_api` bzw. aus einem gemeinsamen Modul, das von API und Script genutzt wird).
- **Option B:** Die Abfrage-Logik (Locosoft-SQL für Kandidaten, DRIVE + Locosoft für Abgang) in ein gemeinsames Modul auslagern (z. B. `api/afa_bestand_abgleich.py`); API und Report-Script importieren daraus. So bleibt eine SSOT für Filter und Vergleich.

Ergebnis: zwei Listen – `kandidaten` (neu in Locosoft), `abgang_pruefen` (aktiv in DRIVE, verkauft in Locosoft).

### 4.2 E-Mail-Inhalt (HTML)

- **Betreff:** z. B. „DRIVE AfA: Bestandsabgleich DRIVE/Locosoft – [Datum]“.
- **Body:** HTML (wie TEK-Reports):
  - Kurzer Einleitungstext (Stichtag, Hinweis Locosoft-Update ca. 18–19 Uhr).
  - Tabelle **„Neue Fahrzeuge in Locosoft“** (Spalten: Kennzeichen, VIN, Bezeichnung, Art, Anschaffung, EK netto); wenn leer: „Keine neuen Fahrzeuge.“
  - Tabelle **„Bitte Abgang in DRIVE prüfen“** (Spalten: Kennzeichen, VIN, Bezeichnung, Locosoft Rechnungsdatum); wenn leer: „Keine offenen Abgänge.“
  - Link zum AfA-Dashboard: `http://drive/controlling/afa`.

Referenz HTML-Bau: `scripts/send_daily_tek.py` – `build_gesamt_email_html` bzw. ähnliche Tabellen-Builder.

### 4.3 Versand

- **Kanal:** Wie TEK (Microsoft Graph oder SMTP, Absender z. B. `drive@auto-greiner.de`). Bestehende Versand-Infrastruktur aus `scripts/send_daily_tek.py` oder `reports/send_test.py` wiederverwenden.
- **Empfänger:**
  - **Variante 1:** Feste Liste (z. B. in Config oder .env: `AFA_REPORT_EMAILS`).
  - **Variante 2:** Neuer Report-Typ in der Report-Registry (`reports/registry.py`) und Tabelle `report_subscriptions` (z. B. `afa_bestand_report`), dann Empfänger in der Admin-UI „Report-Abonnements“ verwalten (wie bei TEK).

### 4.4 Zeitsteuerung (Celery Beat)

- **Task:** z. B. `email_afa_bestand_report` in `celery_app/tasks.py` (analog `email_tek_daily`).
- **Schedule:** 1× täglich **nach** Locosoft-Update, z. B. **20:00 Uhr Mo–Fr** (crontab: `minute=0, hour=20, day_of_week='mon-fri'`). Locosoft-Befüllung laut CONTEXT ca. 18–19 Uhr.
- Task kann optional `force=True` unterstützen für manuellen Versand aus Admin/Celery-UI.

### 4.5 Option: Nur bei Abweichung senden

- Wenn **beide** Listen leer sind: keine E-Mail senden (oder nur kurze E-Mail „AfA-Bestand heute abgeglichen – keine Aktionen.“). Entscheidung produktionsseitig („immer kurz melden“ vs. „nur bei Handlungsbedarf“).

---

## 5. Dateien / Änderungen (Übersicht)

| Bereich            | Änderung |
|--------------------|----------|
| **API**            | Optional: Abfrage-Logik in `api/afa_bestand_abgleich.py` auslagern, damit API und Report eine SSOT nutzen. Sonst: Report ruft bestehende API-Endpunkte oder interne Funktionen auf. |
| **Script/Task**    | Neues Script `scripts/send_afa_bestand_report.py` ODER reiner Celery-Task, der (1) Daten holt, (2) HTML baut, (3) E-Mail versendet. |
| **Celery**         | Task `email_afa_bestand_report` in `celery_app/tasks.py`; Eintrag in `beat_schedule` in `celery_app/__init__.py` (z. B. 20:00 Mo–Fr). |
| **Admin/Celery-UI**| Task in der Liste manuell startbar machen (wie `email_tek_daily`). |
| **Report-Registry**| Optional: `afa_bestand_report` in `reports/registry.py` anlegen; Migration/Default-Empfänger für `report_subscriptions` falls gewünscht. |

---

## 6. Abhängigkeiten und Tests

- **Locosoft:** Gleiche Abhängigkeit wie TEK – Daten nach täglichem Update (ca. 18–19 Uhr). Task erst danach ausführen.
- **Test:** Report einmal mit `force=True` bzw. per Script-Aufruf senden; Prüfung: E-Mail empfangen, Tabellen lesbar, Link zum AfA-Dashboard funktioniert. Leere Listen testen („Keine neuen Fahrzeuge“ / „Keine offenen Abgänge“).

---

## 7. Geschätzter Aufwand

- **Ohne Report-Registry (feste E-Mail-Liste):** ~1 Tag (Task, HTML-Builder, Celery-Beatz, Versand, Test).
- **Mit Report-Registry und Admin-UI-Abonnement:** ~1,5–2 Tage (zusätzlich Registry-Eintrag, ggf. Migration, UI bereits vorhanden).

---

## 8. Referenzen

- **APIs:** `api/afa_api.py` – `locosoft_kandidaten()`, `abgangs_kontrolle()`
- **TEK E-Mail:** `scripts/send_daily_tek.py`, `celery_app/tasks.py` (`email_tek_daily`), `celery_app/__init__.py` (beat_schedule)
- **Report-Registry / Abonnements:** `reports/registry.py`, `get_subscriber_emails()`, Tabelle `report_subscriptions`
- **CONTEXT Controlling:** `docs/workstreams/controlling/CONTEXT.md`
- **Validierung AfA:** `docs/workstreams/controlling/AfA/ANLEITUNG_AFA_MODUL_VALIDIERUNG.md`
