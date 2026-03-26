# Konten & Bankverbindungen verwaltbar machen — Vorschlag

**Stand:** 2026-03-02  
**Workstream:** Controlling  
**Auslöser:** Änderungen an Bankverbindungen/Krediten; Kontenübersicht soll editierbar und verwaltbar werden.

---

## Ausgangslage

- **URL:** http://drive/bankenspiegel/konten
- **Aktuell:** Rein lesende Übersicht (Status, Bank, Kontoname, IBAN, Saldo, Kreditlinie, Verfügbar, Aktionen → Transaktionen).
- **API:** `GET /api/bankenspiegel/konten` liefert nur **aktive** Konten; keine PATCH/PUT/POST für Konten oder Banken.
- **DB:** `konten` (u.a. bank_id, kontoname, iban, kreditlinie, aktiv, kontoinhaber, sort_order), `banken` (bank_name, bank_typ, aktiv).

Saldo und „Verfügbar“ sind berechnet (Salden/Transaktionen) und sollen **nicht** direkt editierbar sein.  
Editierbar/verwaltbar sollen sein: **Status (aktiv/inaktiv), Bank, Kontoname, IBAN, Kreditlinie**, ggf. Kontoinhaber, Sortierung; optional neues Konto anlegen, Banken pflegen.

---

## Option A: Eigene Verwaltungsseite (empfohlen)

**URL:** `/admin/konten-verwaltung` (zentral unter Admin, wie Provisionsarten und ServiceBox; siehe auch **ADMIN_KONFIGURATION_HUB_VORSCHLAG.md**).

**Vorteile:**

- Klare Trennung: Die bestehende Kontenübersicht bleibt für alle unverändert (schnell, lesbar, nur „Transaktionen“).
- Nur Berechtigte (admin, buchhaltung) sehen den Link „Konten verwalten“ und können Änderungen vornehmen.
- Weniger Risiko von versehentlichen Klicks; Verwaltung kann inkl. **inaktiver** Konten und „Neues Konto“/„Bank anlegen“ an einer Stelle gebündelt werden.
- Erweiterbar: später Audit-Log, Banken-CRUD, Import-Hinweise.

**Inhalt der Seite:**

- Tabelle aller Konten (aktiv + inaktiv), Spalten z. B.: Status, Bank, Kontoname, IBAN, Kreditlinie, Saldo (nur Anzeige), Aktionen (Bearbeiten, ggf. Aktivieren/Deaktivieren).
- „Bearbeiten“ öffnet Modal (oder eigene Zeile): Kontoname, IBAN, Bank (Dropdown aus `banken`), Kreditlinie, Kontoinhaber, Sortierung, Aktiv (Ja/Nein). Saldo/Verfügbar nur anzeigen, nicht editierbar.
- Optional: Button „Neues Konto“, „Bank verwalten“ (CRUD für `banken`), wenn gewünscht.

**Handelbar / Berechtigungen:**

- Link „Konten verwalten“ nur anzeigen, wenn User Feature `bankenspiegel` hat (bereits admin, buchhaltung). Kein neues Feature nötig; bei Bedarf später eigenes Feature `bankenspiegel_verwalten` für feinere Steuerung.
- API: neue Endpoints nur für berechtigte Nutzer (gleicher Decorator wie bestehende Bankenspiegel-APIs).

---

## Option B: Bearbeitung auf derselben URL (/bankenspiegel/konten)

- Auf der bestehenden Kontenübersicht für admin/buchhaltung zusätzlich:
  - „Bearbeiten“-Button pro Zeile **oder**
  - Inline-Edit (z. B. nur Kreditlinie und Kontoname direkt in der Tabelle).
- Filter „Nur aktive“ um „Alle (inkl. inaktive)“ erweitern, damit inaktive Konten sichtbar und editierbar sind.

**Vorteile:** Alles an einem Ort.  
**Nachteile:** Seite wird voller; höheres Risiko versehentlicher Änderungen; Mix aus „Lesen für alle“ und „Schreiben für wenige“ auf einer View.

---

## Empfehlung

**Option A (eigene Verwaltungsseite)**:

1. Änderungen an Bankverbindungen/Krediten sind eher selten; eine dedizierte Verwaltungsseite bleibt übersichtlich und fehlerarm.
2. Die normale Kontenübersicht bleibt für alle Nutzer unverändert und schnell.
3. Rechte sind klar: Lesen = `bankenspiegel`, Schreiben = gleiche Rolle (admin/buchhaltung), aber nur auf der Verwaltungsseite.
4. Erweiterbar um Banken-Verwaltung, neues Konto anlegen, Audit ohne die Lese-Ansicht zu überfrachten.

---

## Technische Umsetzung (Kurzplan)

1. **API erweitern**
   - `GET /api/bankenspiegel/konten?alle=1` — liefert auch inaktive Konten (für Verwaltung).
   - `PATCH /api/bankenspiegel/konten/<id>` — Body: kontoname, iban, bank_id, kreditlinie, aktiv, kontoinhaber, sort_order (nur erlaubte Felder). Validierung: Pflichtfelder, Kreditlinie ≥ 0, ggf. IBAN-Format.
   - Optional: `POST /api/bankenspiegel/konten` (Neues Konto), `GET/PATCH /api/bankenspiegel/banken` (Banken lesen/aktualisieren).

2. **Route & Template**
   - Route: `/admin/konten-verwaltung` (in `admin_routes.py`, wie provision-config).
   - Template: z. B. `admin/konten_verwaltung.html` mit Tabelle + Bearbeiten-Modal; JS ruft PATCH auf, danach Liste neu laden.

3. **Navigation**
   - **Zentrale Konfiguration:** Link „Konten & Banken“ auf der Hub-Seite `/admin/konfiguration` (siehe ADMIN_KONFIGURATION_HUB_VORSCHLAG.md).
   - **Admin-Dropdown:** Eintrag „Konten & Banken“ oder „Konten verwalten“ (admin/buchhaltung).
   - **Bankenspiegel-Kontenübersicht:** Button „Konten verwalten“ (nur für Berechtigte) → `/admin/konten-verwaltung`.

4. **DB**
   - Keine Schema-Änderung nötig; `konten` und `banken` haben bereits die nötigen Spalten. Bei PATCH `aktualisiert_am = NOW()` setzen.

---

## Nächster Schritt

Entscheidung: Option A umsetzen (eigene Seite) oder Option B (Bearbeitung auf /bankenspiegel/konten). Danach kann die konkrete Implementierung (API + Route + Template + Navi-Link) folgen.
