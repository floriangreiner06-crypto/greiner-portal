# Garantie-Bedingungen & Rundschreiben bereitstellen – Plan (inkl. Upload in DRIVE)

**Stand:** 2026-03  
**Workstream:** werkstatt  
**Status:** Plan (keine Implementierung)

---

## 1. Ausgangslage

- **Ja, zuerst bereitstellen.** Bevor die LM-Studio-Prüfung/Empfehlung sinnvoll arbeitet, sollten **alle** relevanten Garantie-Bedingungen und Rundschreiben zentral verfügbar sein. Das ist die Grundlage für (1) manuelles Nachschlagen und (2) spätere KI-Nutzung (Kontext für LM Studio).
- **Aktuell:** Nur eine feste Liste von vier Handbüchern in `garantie_routes.py`; Dateien liegen im Sync-Verzeichnis `docs/workstreams/werkstatt/garantie/`. Kein Upload im Portal – wenn eine Datei nicht per Sync liegt, steht „Datei noch nicht synchronisiert“.

---

## 2. Ziele

1. **Vollständigkeit:** Handbücher **und** Rundschreiben (Hersteller-Rundschreiben zu Garantie) an einer Stelle sichtbar und nutzbar.
2. **Aktualität:** User sollen die Unterlagen **aktuell halten** können, ohne zwingend auf Windows-Sync oder IT zu warten.
3. **Übersicht:** Klare Trennung z. B. „Handbücher & Richtlinien“ vs. „Rundschreiben“ (optional weitere Kategorien), einheitliche Anzeige (Titel, Marke, Stand, Link Öffnen/Download).

---

## 3. Optionen

### Option A: Nur Sync, Liste erweitern (minimal)

- **Handbücher:** Wie bisher, feste Liste in Code (z. B. um weitere Einträge ergänzen).
- **Rundschreiben:** Zweite feste Liste „Rundschreiben“ (Dateinamen + Anzeigetitel, Marke, Stand), gleicher Ordner `garantie/`.
- **Ablage:** Alle PDFs weiterhin nur per Sync (F:\…\Server\docs\workstreams\werkstatt\garantie) auf den Server legen. Kein Upload im Portal.
- **Vorteil:** Sehr wenig Aufwand, keine neuen Rechte/Upload-Logik.  
- **Nachteil:** Aktualisierung nur über Sync/IT; neue Rundschreiben erfordern Code-Anpassung (neue Zeile in Liste).

---

### Option B: Upload in DRIVE (empfohlen)

- **Speicherort:** Weiterhin ein gemeinsamer Ordner auf dem Server, z. B. `docs/workstreams/werkstatt/garantie/` oder (für klare Trennung) `data/uploads/garantie/` (analog zu `data/uploads/fahrzeugscheine`). PDFs nur auf Server, nicht im Git (.gitignore).
- **Wer darf hochladen:** Nur berechtigte Nutzer (z. B. Feature `garantie_dokumente_upload` oder Rollen admin / Werkstatt-Leitung). Bereits heute: Handbücher-Seite ist nur nach Login sichtbar; Upload zusätzlich per Feature/Rolle einschränken.
- **Was hochgeladen werden kann:** Nur PDF. Dateiname bereinigt (kein Path-Traversal, nur erlaubte Zeichen), Maximalgröße z. B. 20–50 MB.
- **UI:** Auf der Seite „Garantie – Handbücher & Richtlinien“:
  - Bereiche „Handbücher“ und „Rundschreiben“ (siehe Option C für dynamische Liste).
  - Für Berechtigte: **Button „Dokument hochladen“** (oder „Rundschreiben hochladen“). Modal/Formular: Datei wählen, optional **Titel**, **Marke** (z. B. Hyundai, Opel, Übergreifend), **Stand** (z. B. 01/2026), **Typ** (Handbuch / Richtlinie / Rundschreiben). Beim Speichern: Datei auf Server speichern, Metadaten in DB (siehe Option C) oder als Dateiname-Konvention.
- **Vorteil:** User können neue Rundschreiben und neue Versionen von Handbüchern selbst einspielen, ohne Sync/Code-Änderung.  
- **Nachteil:** Implementierungsaufwand (API, Rechte, UI, ggf. DB).

---

### Option C: Dynamische Liste mit Metadaten (DB) + Upload

- **Datenbank:** Tabelle z. B. `garantie_dokumente`:
  - `id`, `dateiname` (Speichername auf Server), `titel` (Anzeige), `marke` (Hyundai, Opel, Leapmotor, Übergreifend), `stand` (z. B. 01/2026), `typ` (handbuch | richtlinie | rundschreiben), `created_at`, `created_by` (user_id oder username), optional `bemerkung`.
- **Speicherung:** PDF-Dateien in einem Ordner (z. B. `data/uploads/garantie/`); Dateiname eindeutig (z. B. Originalname bereinigt + Zeitstempel oder UUID), Referenz in DB.
- **Seite „Handbücher & Richtlinien“:** Liste kommt aus DB (plus optional feste „Standard“-Einträge für bekannte Handbücher, die beim ersten Setup angelegt werden). Filter/Tabs: z. B. „Handbücher & Richtlinien“ | „Rundschreiben“.
- **Upload:** Neue Datei + Metadaten (Titel, Marke, Stand, Typ) → Speichern in Ordner + INSERT in `garantie_dokumente`. Bestehende Einträge: „Ersetzen“ = neue Datei hochladen, gleicher Eintrag, `updated_at`/`updated_by` setzen.
- **Vorteil:** Voll dynamisch; neue Dokumente und Rundschreiben ohne Code; Nutzer halten die Infos aktuell; LM Studio kann später auf dieselbe Liste/DB zugreifen (welche Dokumente als Kontext nutzen).  
- **Nachteil:** Größter Aufwand (Migration, CRUD-API, UI inkl. Ersetzen/Löschen nur für Berechtigte).

---

## 4. Empfehlung

- **Kurzfristig (ohne Upload):** Option A umsetzen – feste Liste um **Rundschreiben** ergänzen (sofern ihr konkrete Rundschreiben-PDFs habt), gleicher Ordner. So sind „alle“ Bedingungen und Rundschreiben an einer Stelle sichtbar, sobald die Dateien per Sync liegen.
- **Mittelfristig (mit Upload):** **Option B + C kombinieren:** Tabelle `garantie_dokumente` + Upload-Button in DRIVE. So können User die Infos selbst aktuell halten; keine Abhängigkeit von Sync oder Code-Änderung für neue Rundschreiben. Handbücher können weiterhin als feste „Vorlage“-Einträge in der DB angelegt werden (z. B. beim ersten Rollout), danach bei Bedarf per Upload ersetzt werden.

---

## 5. Konkrete Schritte (Plan, Reihenfolge)

1. **Inhalt klären:** Welche Garantie-Rundschreiben gibt es? (Dateinamen, Marken, ggf. Stand.) Liste sammeln wie bei den Handbüchern.
2. **Ohne Upload (schnell):** In `GARANTIE_HANDBUECHER` bzw. einer zweiten Liste „Rundschreiben“ alle bekannten Dokumente eintragen; UI um Abschnitt „Rundschreiben“ erweitern. PDFs in `garantie/` legen (per Sync). Dokumentation (README im Ordner) anpassen: Handbücher + Rundschreiben.
3. **Mit Upload (geplant):**
   - **Migration:** Tabelle `garantie_dokumente` anlegen (Felder wie oben), optional Start-Daten aus der bisherigen festen Liste importieren.
   - **API:**  
     - `GET /api/garantie/dokumente` – Liste (optional gefiltert nach typ/marke) aus DB + Prüfung ob Datei auf Disk existiert.  
     - `POST /api/garantie/dokumente/upload` – Datei + Metadaten (Titel, Marke, Stand, Typ), nur für User mit Berechtigung; Speichern in `data/uploads/garantie/` (oder bestehendem Ordner), Eintrag in DB.  
     - Optional: `PUT` zum Ersetzen einer Datei, `DELETE` zum Entfernen eines Eintrags (nur für Berechtigte).
   - **Rechte:** Feature z. B. `garantie_dokumente_upload` (oder Nutzung bestehender Rolle) in `auth` prüfen; Navigation/Seite Handbücher bereits geschützt.
   - **UI:** Auf der Handbücher-Seite: zwei Bereiche (Handbücher & Richtlinien / Rundschreiben), Daten aus API. Für Berechtigte: Button „Dokument hochladen“, Modal mit Dateiauswahl + Titel, Marke, Stand, Typ; nach Upload Liste neu laden.
4. **LM Studio:** Sobald alle Bedingungen und Rundschreiben zentral verfügbar sind (und ggf. in DB mit Typ/Marke), kann die Prüfung/Empfehlung (siehe `GARANTIE_BEDINGUNGEN_LM_STUDIO_PRUEFUNG_PLAN.md`) auf diese Quellen zugreifen (Kontext pro Marke aus den richtigen Dokumenten).

---

## 6. Technik-Hinweise (für spätere Umsetzung)

- **Upload-Pattern im Projekt:** Ähnlich wie `api/fahrzeuganlage_api.py` (request.files, Pfad in `data/uploads/...`) oder `api/jahrespraemie_api.py` (upload mit Berechnung-ID). Kein öffentlicher Zugriff auf Upload-Ordner; Auslieferung nur über Route (wie bisher `garantie_handbuch_pdf`), mit Prüfung ob Eintrag in DB existiert und User berechtigt ist.
- **.gitignore:** `data/uploads/garantie/` (oder den gewählten Ordner) ignorieren, damit PDFs nicht ins Repo kommen.
- **Sync:** Wenn ihr den bestehenden Ordner `docs/workstreams/werkstatt/garantie/` weiter für Sync nutzt, kann Upload entweder in denselben Ordner schreiben (dann Sync-backup nach Windows möglich) oder in `data/uploads/garantie/` (dann klar getrennt: Portal-Uploads vs. Sync-Inhalt). Beides ist möglich; Entscheidung: Ein Ordner = eine Quelle vereinfacht die Logik.

---

## 7. Zusammenfassung

| Frage | Antwort |
|-------|--------|
| Sollten wir zuerst alle Garantie-Bedingungen und Rundschreiben bereitstellen? | **Ja.** Das ist die Basis für Nachschlagen und für die LM-Studio-Prüfung. |
| Wie machen wir das am besten? | (1) Liste um Rundschreiben erweitern, ein Ordner für alle PDFs. (2) Mittelfristig: DB-Tabelle `garantie_dokumente` + Ablage auf Server, dynamische Anzeige. |
| Upload-Button in DRIVE? | **Ja, sinnvoll.** Nur für berechtigte User; PDF-Upload + Metadaten (Titel, Marke, Stand, Typ); so können User die Infos aktuell halten ohne Sync/IT. |

---

*Nur Plan; keine Code-Änderungen. Referenzen: `routes/aftersales/garantie_routes.py`, `docs/workstreams/werkstatt/garantie/README.md`, `api/fahrzeuganlage_api.py` (Upload), `GARANTIE_BEDINGUNGEN_LM_STUDIO_PRUEFUNG_PLAN.md`.*
