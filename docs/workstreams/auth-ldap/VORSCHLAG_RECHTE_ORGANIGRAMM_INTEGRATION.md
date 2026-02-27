# Vorschlag: Integration Organigramm & Organisation in die Rechteverwaltung

**Stand:** 2026-02-19 | **2026-02-27:** Modul zur **LDAP-Bearbeitung** (LDAP-Infos im Portal bearbeiten / Zurückschreiben ins AD) ist **auf Eis gelegt** – siehe auth-ldap/CONTEXT.md.

**Kontext:** Rechteverwaltung (Option B) ist umgesetzt. Organigramm-Seite existiert mit Tabs (Abteilungen, Hierarchie, Vertretungen, Genehmiger), Teile sind vorbereitet, nicht fertig. Ziel: eine zentrale Stelle für **Organisation + Rechte**; LDAP-Edit-Funktionen vorerst zurückgestellt.

**Umsetzung 2026-02-19 (erster Schritt):** **Interaktives Organigramm** im Tab „Hierarchie“ umgesetzt: Tree-API liefert `team_size` und `pending_team_count` pro Knoten (`GET /api/organization/tree?with_vacation=1`); Frontend zeigt pro Vorgesetzten „n Mitarbeiter“, „X offen“ (Link zur Chef-Übersicht) und „Team anzeigen“/„Team ausblenden“. LDAP/AD bleibt führend; Schreibrechte evtl. später.

---

## 1. Was heute existiert (Kurzüberblick)

### Rechteverwaltung (Admin)
- **Route:** `/admin/rechte_verwaltung`
- **Inhalt:** User & Rollen (Portal-Rolle, Quelle), Rollen-Features, Matrix, Architektur, E-Mail Reports, Title-Mapping, Navigation.
- **Daten:** `users`, `user_roles`, `feature_access`, `navigation_items`, Portal-Rolle pro User.

### Organigramm (Admin)
- **Route:** `/admin/organigramm`
- **Tabs:** Abteilungen, Hierarchie, Vertretungen, Genehmiger.
- **APIs:** `api/organization_api.py`
  - `/api/organization/tree` – Baum aus `employees` (supervisor_id, department_name, location)
  - `/api/organization/departments` – Abteilungen mit Mitgliedern (aus `employees.department_name`)
  - `/api/organization/substitutes` – Vertretungsregeln (Tabelle `substitution_rules` – prüft auf SQLite, muss für PostgreSQL angepasst werden)
  - `/api/organization/approval-rules` – Genehmiger (liest/schreibt `vacation_approval_rules`: grp_code, standort, approver_ldap, priority)
- **Daten:** `employees` (department_name, location, supervisor_id, is_manager, …), `vacation_approval_rules`, ggf. `substitution_rules`.

### Urlaubsplaner – Genehmigung & Sichtbarkeit
- **Genehmiger:** `vacation_approval_rules` (Abteilung/Standort → wer genehmigt); zusätzlich AD-Manager und `vacation_approver_service.py` (Team = alle, deren AD manager = aktueller User).
- **Sichtbarkeit:** Wer was im Urlaubsplaner sieht, hängt an Rollen (z. B. Genehmiger, HR, Admin) und an den gleichen Regeln/Abteilungen.

### Mitarbeiterverwaltung (Admin)
- **Route:** `/admin/mitarbeiterverwaltung`
- **Inhalt:** Digitale Personalakte (Deckblatt, Adressdaten, Vertrag, Arbeitszeitmodell, Urlaubseinstellungen, …).
- **Daten:** `employees` + Erweiterungen (TAG 213), Locosoft-Sync, LDAP-Stammdaten.

### Navigation
- Unter **Admin** u. a.: Rechteverwaltung, Organigramm, Mitarbeiterverwaltung (einzeln erreichbar).

---

## 2. Zielbild: Eine „Organisation & Rechte“-Oberfläche

Statt drei getrennter Einstiege (Rechteverwaltung, Organigramm, Mitarbeiterverwaltung) soll es **eine** inhaltlich zusammenhängende Verwaltung geben, mit klarer Gliederung:

- **A) Rechte & Zugriff** (bereits umgesetzt)
  - User & Rollen, Rollen-Features, Matrix, Architektur, E-Mail Reports, Nach Feature, Title-Mapping, Navigation.

- **B) Organisation & Struktur** (aus Organigramm + Erweiterungen)
  - **Abteilungsverwaltung:** Abteilungen definieren/bearbeiten, Mitarbeiter zuordnen (Abteilung + ggf. Unterabteilung).
  - **Standortverwaltung:** Standorte (DEG, HYU, LAN) als Stammdaten; Mitarbeiter einem Standort zuordnen (bereits in `employees.subsidiary`/location vorhanden).
  - **Zugehörigkeit des Mitarbeiters:** Pro Mitarbeiter: Abteilung, Standort, Vorgesetzter (supervisor_id), „ist Manager“ – **editierbar im Portal** (nicht nur aus LDAP/Locosoft lesen).
  - **Vertretungsregeln:** Wer vertritt wen (Tabelle `substitution_rules` in PostgreSQL bringen, UI zum Anlegen/Löschen).
  - **Genehmiger Urlaubsplaner:** Wer darf für wen genehmigen – weiterhin abgebildet in `vacation_approval_rules`, aber **konfigurierbar in derselben Oberfläche** (z. B. Tab „Genehmiger“ mit Zuordnung Abteilung/Standort → Genehmiger + Priorität).
  - **Sichtbarkeit Urlaubsplaner:** Wer darf was im Urlaubsplaner sehen (Chef-Übersicht, Admin-Funktionen, nur eigener Urlaub) – bleibt rollenbasiert, kann in Rechteverwaltung (Rollen-Features) dokumentiert/gesteuert werden.

- **C) Organigramm als Ausgabe**
  - **Editierbares Organigramm:** Die gleichen Daten (Abteilungen, Vorgesetzte, Standorte) speisen eine **visualisierte Hierarchie** (Baum/Struktur). Organigramm wird also **nicht** als eigener Datenbereich, sondern als **Ansicht** auf die gepflegten Stammdaten (Abteilung, Vorgesetzter, Standort).
  - Technisch: Bestehende APIs `/api/organization/tree` und `/api/organization/departments` weiter nutzen; Datenquelle = `employees` (und ggf. eine Tabelle `departments`, falls Abteilungen künftig als Stammdaten geführt werden).

- **D) LDAP-Infos „editierbar“**
  - Heute: Viele Felder (Abteilung, Title, Standort) kommen aus LDAP/Locosoft.
  - Ziel: **Im Portal Overrides** speichern (z. B. `employees.department_name`, `employees.subsidiary`, `employees.supervisor_id` im Portal pflegen; Sync überschreibt nur, wenn kein Portal-Override gesetzt – oder Portal hat Priorität für Anzeige/Organigramm). So können Abteilungs-/Standort-/Vorgesetzten-Zuordnungen auch ohne AD-Änderung angepasst werden.

---

## 3. Vorschlag zur Umsetzung (ohne Code, nur Struktur)

### Option A: Rechteverwaltung um Tabs „Organisation“ erweitern
- **Eine** Route bleibt: `/admin/rechte_verwaltung` (oder umbenennen in `/admin/verwaltung`).
- Neue Tabs in derselben Seite:
  - **Organisation** (oder Unter-Tabs: Abteilungen | Standorte | Zugehörigkeit | Vertretungen | Genehmiger).
  - **Organigramm** (nur Ansicht/Link oder eingebettete Visualisierung).
- Vorteil: Alles an einem Ort. Nachteil: Seite wird sehr tab-lastig.

### Option B: Eigenes Modul „Organisation“, gemeinsamer Einstieg „Verwaltung“
- Route z. B. `/admin/verwaltung` mit zwei großen Blöcken:
  1. **Rechte** (aktueller Inhalt Rechteverwaltung).
  2. **Organisation** (Abteilungen, Standorte, Zugehörigkeit, Vertretungen, Genehmiger, Organigramm-Ansicht).
- Mitarbeiterverwaltung kann weiterhin eigener Link bleiben („Mitarbeiterverwaltung“ = Personalakte pro Person), verweist aber in der Organisation auf dieselben Stammdaten (Abteilung, Standort, Vorgesetzter).

### Option C: Organigramm-Seite zur „Organisationszentrale“ ausbauen
- **Organigramm** wird der **Hauptort** für Struktur: Abteilungen, Standorte, Zugehörigkeit, Vertretungen, Genehmiger dort bearbeiten; **Rechteverwaltung** bleibt eigener Navi-Punkt (User, Rollen, Features).
- Organigramm-Seite bekommt die fehlenden UIs (Abteilung/Standort/Vorgesetzter editierbar, Vertretungsregeln, Genehmiger) und die Organigramm-Visualisierung als Ausgabe.
- Rechteverwaltung verlinkt ggf. auf „Organisation“ für Kontext (wer darf was sehen).

**Empfehlung:** **Option B** oder **Option C**.
- **Option B**, wenn Rechte und Organisation als **eine** „Admin-Verwaltung“ geführt werden sollen (ein Einstieg, zwei Bereiche).
- **Option C**, wenn ihr Organigramm/Struktur klar von „Rechten“ trennen und den bestehenden Organigramm-Screen zum zentralen Ort für Struktur machen wollt.

---

## 4. Konkrete Bausteine (unabhängig von A/B/C)

1. **Abteilungsverwaltung**
   - Entweder: Abteilungen nur aus `employees.department_name` ableiten (wie heute) und dort **editierbar** pro Mitarbeiter.
   - Oder: Tabelle `departments` (id, name, standort, reihenfolge) + `employees.department_id`; dann Abteilungen als Stammdaten, Mitarbeiter zuordnen.
   - UI: Liste/Grid Abteilungen, pro Abteilung Mitarbeiter zuordnen; bei Mitarbeiterbearbeitung Abteilung wählbar.

2. **Standortverwaltung**
   - Standorte sind fest (DEG, HYU, LAN) – ggf. Tabelle `standorte` oder Konstante.
   - Pro Mitarbeiter: Standort (subsidiary/location) **im Portal editierbar** (Override oder Hauptquelle).
   - UI: In „Zugehörigkeit“ oder in Mitarbeiterverwaltung: Dropdown Standort.

3. **Zugehörigkeit des Mitarbeiters**
   - Felder: Abteilung, Standort, Vorgesetzter (supervisor_id), ist Manager.
   - Editierbar in einer gemeinsamen Maske (z. B. in Organisation oder in Mitarbeiterverwaltung mit Link).
   - Klärung: Überschreibt Portal die Werte aus LDAP/Locosoft oder nur Anzeige? Vorschlag: Portal-Override-Felder (z. B. `department_override`, `supervisor_id`), Anzeige = Override falls gesetzt, sonst Sync-Wert.

4. **Vertretungsregeln**
   - Tabelle `substitution_rules` in PostgreSQL definieren (falls noch SQLite-Check in API), API anpassen.
   - UI: Tab „Vertretungen“ – Wer vertritt wen (z. B. A vertritt B), Liste + Anlegen/Löschen.

5. **Genehmiger Urlaubsplaner**
   - Bereits in `vacation_approval_rules` abgebildet. UI im Organigramm/Organisation: Tab „Genehmiger“ – Regeln anzeigen, hinzufügen, deaktivieren (wie API bereits anbietet); Zuordnung nach Abteilung/Standort (grp_code, subsidiary) und Priorität.
   - Keine zweite Logik erfinden – eine Quelle `vacation_approval_rules` + ggf. AD-Manager für „Team des Vorgesetzten“.

6. **Sichtbarkeit Urlaubsplaner**
   - Bereits über Rollen (Genehmiger, HR, Admin) und Feature-Zugriff steuerbar. In Rechteverwaltung unter „Rollen-Features“ bzw. „Nach Feature“ abbilden (Feature z. B. `urlaubsplaner_chef`, `urlaubsplaner_admin`). Kein eigener neuer Baustein nötig, nur klare Doku.

7. **Editierbares Organigramm**
   - Organigramm = **Visualisierung** der Hierarchie (tree) aus `employees` (supervisor_id, department_name, …). Sobald Abteilung/Vorgesetzter/Standort im Portal editierbar sind, „ergibt sich“ das Organigramm aus den gepflegten Daten.
   - Optional: Klick auf Person → Link zur Mitarbeiterverwaltung oder Popup „Zugehörigkeit bearbeiten“.

8. **Obsolete Navi-Punkte**
   - Wenn Organisation (Abteilungen, Standorte, Vertretungen, Genehmiger, Organigramm) **in** der Rechte-/Verwaltungsseite integriert wird: **Navigationspunkt „Organigramm“ kann entfallen** (Inhalt wandert in „Rechteverwaltung“ bzw. „Verwaltung“).
   - „Mitarbeiterverwaltung“ kann bleiben (Fokus: Personalakte pro Person), mit Verweis/Link von Organisation auf „Mitarbeiter bearbeiten“.

---

## 5. Reihenfolge (Phasen)

- **Phase 1 – Datenbasis:**  
  - `employees`: Klarheit, welche Felder im Portal editierbar sind (department, subsidiary, supervisor_id); ggf. Override-Spalten.  
  - `substitution_rules` in PostgreSQL (Schema + Migration), API von SQLite-Check auf PostgreSQL umstellen.

- **Phase 2 – Organisation-UI:**  
  - Abteilungen (Liste + Zuordnung), Standorte (Zuordnung), Zugehörigkeit (Vorgesetzter, Abteilung, Standort) in einer Oberfläche (Organigramm-Seite oder Rechteverwaltung je nach gewählter Option).  
  - Vertretungsregeln: CRUD-UI.  
  - Genehmiger: bestehende API anbinden, UI Tab „Genehmiger“ befüllen.

- **Phase 3 – Organigramm als Ausgabe:**  
  - Tree/Hierarchie aus aktuellen Daten zeichnen; ggf. Klick → Bearbeiten/Link Mitarbeiterverwaltung.

- **Phase 4 – Navigation aufräumen:**  
  - Organigramm-Navi entfernen oder durch einen Einstieg „Verwaltung“ ersetzen (Rechte + Organisation).

---

## 6. Offene Entscheidungen

- **Option A, B oder C** für die Platzierung (Rechteverwaltung erweitern vs. gemeinsamer Einstieg „Verwaltung“ vs. Organigramm als Organisationszentrale).
- **Abteilungen:** Nur aus Mitarbeitern abgeleitet und pro MA editierbar, oder eigene Tabelle `departments` mit Stammdaten?
- **LDAP-Override:** Portal-Werte für Abteilung/Standort/Vorgesetzter – überschreiben sie Sync (LDAP/Locosoft) dauerhaft oder nur Anzeige/Organigramm (Sync schreibt weiter, Portal hat Priorität bei Anzeige)?

Wenn diese Punkte entschieden sind, kann die Implementierung schrittweise (Phase 1 → 4) erfolgen.

---

## 7. Chef-Übersicht vs. Organigramm – Klarstellung und Option „Interaktives Organigramm“

### Wie die Chef-Übersicht heute entsteht

Die **Chef-Übersicht** (Urlaubsplaner) wird **nicht** aus der Organigramm-Hierarchie gebaut, sondern aus:

1. **Genehmiger-Liste:** Alle Einträge in `vacation_approval_rules` mit `active = 1` und `priority IN (1, 2)` → das sind die „Chefs“ in der Übersicht.
2. **Team pro Chef:** Für jeden Genehmiger wird das Team so ermittelt: Alle Mitarbeiter, bei denen **Abteilung** (`employees.department_name`) und **Standort** (`employees.location`) zu einer Regel dieses Genehmigers passen (Regel = `loco_grp_code` + `subsidiary`). Es gibt zusätzlich einen Alias z. B. „Service & Empfang“ → „Service“.

**Konsequenz:** Die Chef-Übersicht ist ein **Spiegel der Genehmiger-Regeln** plus Abteilungs-/Standort-Zuordnung der MA. Sie ist **unabhängig** von der Hierarchie (Vorgesetzter, `supervisor_id`). Organigramm nutzt dagegen **supervisor_id** für den Baum. Beide können also **auseinanderlaufen** (z. B. anderer „Chef“ in der Übersicht als im Organigramm).

### Zwei Wege: synchronisieren oder zusammenführen

**Variante A – Synchron halten (zwei Ansichten, eine Logik)**  
- **Eine führende Quelle** festlegen: entweder **Hierarchie** (Organigramm, `supervisor_id`) oder **weiterhin Genehmiger-Regeln**.  
- Wenn **Hierarchie führend** ist: Genehmiger-Logik so umbauen, dass „wer genehmigt“ aus dem Vorgesetzten im Organigramm kommt (plus ggf. Rolle „Genehmiger“). Dann entsteht die Chef-Übersicht aus **demselben** Baum wie das Organigramm (pro Knoten mit Untergebenen = eine Karte mit Team + offene Anträge).  
- Wenn **Regeln führend** bleiben: Organigramm und Chef-Übersicht bleiben getrennt; Abteilungen/Standorte in beiden aus derselben Stammdaten (`employees`) pflegen, damit Abteilungs-/Standort-Zuordnung übereinstimmt.

**Variante B – Eine Ansicht: Interaktives Organigramm (Empfehlung)**  
- **Chef-Übersicht als eigene Seite abschaffen** und durch ein **interaktives Organigramm** ersetzen.  
- Das Organigramm wird aus der **Hierarchie** (`supervisor_id`) und den gepflegten Stammdaten (Abteilung, Standort) aufgebaut.  
- **Interaktiv** bedeutet z. B.:  
  - Baum mit Expand/Collapse (wie heute „Team anzeigen“).  
  - Pro Vorgesetzten-Knoten: Anzeige von **Teamgröße**, **offenen Urlaubsanträgen**, optional **Resturlaub** (wie in der heutigen Chef-Übersicht).  
  - Klick auf einen Knoten → Detail/Seite mit Teamliste, offenen Anträgen, Aktion „Genehmigen“ (wie heute in der Chef-Übersicht).  
- **Vorteil:** Nur noch **eine** Struktur (Organigramm), eine Quelle (Hierarchie + Stammdaten). Keine zweite Logik für „wer ist Chef von wem“. Genehmiger-Rechte weiterhin über Rollen oder über „ist Vorgesetzter von X“ ableitbar; `vacation_approval_rules` könnte schrittweise durch „Vorgesetzter im Organigramm“ ergänzt oder ersetzt werden.

### Konkrete Empfehlung

- **Kurzfristig:** In der Doku und im Code festhalten, **wie** die Chef-Übersicht entsteht (Genehmiger-Regeln + Abteilung/Standort-Match), damit das für alle nachvollziehbar ist.  
- **Mittelfristig:** **Interaktives Organigramm** als Zielbild: Eine Baumansicht (Hierarchie), die pro Knoten (Vorgesetzter) die gleichen Infos wie die heutige Chef-Übersicht anzeigt (Team, offene Anträge, ggf. Genehmigen). Die heutige Seite „Urlaubsplaner – Chef-Übersicht“ wird dann durch diese Organigramm-Ansicht ersetzt oder als „Urlaubsplaner-View“ darauf umgeleitet (z. B. Filter: nur Knoten mit offenen Anträgen).  
- **Daten:** Hierarchie (`supervisor_id`) und Abteilungen/Standorte im Portal editierbar pflegen (wie in Abschnitt 4 beschrieben); Organigramm und „Chef-Übersicht“-Logik nutzen dieselbe Quelle. Ob `vacation_approval_rules` dauerhaft für Ausnahmen (z. B. Stellvertreter ohne Vorgesetzten-Rolle) bleibt oder ob alles über Hierarchie + Vertretungsregeln abgebildet wird, ist eine weitere Entscheidung.

---

## 8. Zurückschreiben in LDAP (Active Directory)

### Frage: Können wir Änderungen aus dem Portal zurück ins AD schreiben?

**Kurz: Ja, technisch möglich – aber mit Bedingungen.**

### Aktueller Stand im Portal

- **LDAP wird nur gelesen:** Login, Gruppen, User-Details; Sync „von LDAP → Portal“ (Mitarbeiterstammdaten). Es gibt **keine** Schreiboperationen (modify/add) in `auth/ldap_connector.py` oder anderswo.
- `_calculate_ldap_changes` im Employee-Sync berechnet nur **Differenzen LDAP → Portal** (für Anzeige/Overwrite), schreibt **nicht** ins AD.

### Was „Zurückschreiben“ bedeuten würde

- Im Portal geänderte Felder (z. B. Abteilung, Standort, Vorgesetzter) per **LDAP MODIFY** im AD setzen.
- Typische Attribute (je nach AD-Schema): `department`, `company`, `manager` (DN des Vorgesetzten). Optional weitere Attribute (z. B. `title`, `physicalDeliveryOfficeName`), wenn gewünscht.

### Voraussetzungen

1. **Rechte im AD:** Der **Service-Account** (LDAP_BIND_DN), mit dem das Portal verbindet, braucht **Schreibrechte** auf die betreffenden Attribute der User-Objekte (bzw. der OU). Oft wird dafür ein dedizierter Account mit eingeschränkten Rechten (nur bestimmte Attribute) angelegt.
2. **Schema:** Die gewünschten Attribute müssen im AD existieren und für User-Objekte erlaubt sein (`department`, `manager`, `company` sind Standard; bei „Standort“ ggf. `physicalDeliveryOfficeName` oder ein eigenes Attribut).
3. **Manager:** Das `manager`-Attribut erwartet die **DN** des Vorgesetzten. Dafür muss die Portal-Logik die Employee-ID des Vorgesetzten in eine AD-DN auflösen (z. B. über Suche nach `sAMAccountName` oder `userPrincipalName`).

### Technik (ldap3)

- Mit **ldap3** ist `connection.modify(dn, changes)` möglich, z. B. `{'department': [(MODIFY_REPLACE, ['Buchhaltung'])]}`. Dafür muss das Portal eine **schreibende** Verbindung mit dem Service-Account herstellen (wie beim Lesen, nur mit Berechtigung zum Ändern).
- Wichtig: Fehlerbehandlung (Rechte, Validierung, Replikation), Logging und ggf. Bestätigung im UI („Wirklich ins AD schreiben?“).

### Risiken / Nachteile

- **Abhängigkeit vom AD:** Ausfälle oder Rechteänderungen im AD blockieren Schreibvorgänge.
- **Konflikte:** Andere Systeme oder die Personalabteilung könnten dieselben Attribute im AD pflegen; dann braucht ihr Klarheit, wer „Master“ ist.
- **Sicherheit:** Schreibzugriff auf das AD muss restriktiv vergeben und überwacht werden.

### Alternative ohne LDAP-Schreibzugriff

- **Portal-Override:** Änderungen nur in der Portal-DB speichern (z. B. `department_override`, `supervisor_id`). Anzeige und Organigramm/Genehmiger-Logik nutzen diese Overrides; der Sync „LDAP → Portal“ überschreibt nur, wo kein Override gesetzt ist (oder Portal hat bei der Anzeige immer Priorität). **Vorteil:** Kein AD-Schreibzugriff nötig, einfacher zu betreiben und abzusichern.

### Empfehlung

- **Wenn** die IT/Organisation ausdrücklich will, dass Änderungen (Abteilung, Vorgesetzter, Standort) **zentral im AD** landen und von dort andere Systeme lesen: LDAP-Zurückschreiben ist umsetzbar, mit klarer Regelung für Rechte, Schema und Verantwortung.
- **Wenn** das Portal der Hauptort für Organisationsstruktur und Urlaub/Genehmiger sein soll und andere Systeme nicht zwingend aus dem AD lesen müssen: **Portal-Override** ist der pragmatischere Weg; LDAP-Zurückschreiben kann später ergänzt werden, sobald die Anforderung und die AD-Rechte geklärt sind.
