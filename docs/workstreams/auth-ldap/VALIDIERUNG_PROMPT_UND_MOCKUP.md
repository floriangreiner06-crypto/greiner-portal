# Validierung: CURSOR_PROMPT_RECHTEVERWALTUNG.md + rechteverwaltung_mockup.jsx

**Stand:** Abgleich mit dem aktuellen Drive-Portal (Option B bereits umgesetzt).  
**Quelle:** Prompt und Mockup liegen im Sync-Verzeichnis (von Claude erstellt), kennen nicht den vollen Drive-Stand.  
**Auftrag:** Prüfen, validieren, Kommentar zur Umsetzbarkeit und zu Bedenken — **noch nichts coden**.

---

## 1. Ist-Zustand im Drive (bereits umgesetzt)

| Thema | Drive heute |
|-------|-------------|
| **Option B** | ✅ Umgesetzt. Wirksame Rolle = admin (user_roles) **oder** `users.portal_role_override` **oder** Default `mitarbeiter`. LDAP-Titel wird **nicht** mehr für Berechtigungen verwendet. |
| **DB** | ✅ `users.portal_role_override` existiert (Migration `add_portal_role_override.sql`, VARCHAR(50)). |
| **auth_manager.py** | ✅ Login und `get_user_by_id` nutzen die Kaskade (admin → override → mitarbeiter). Kein `get_role_from_title()` für Zugriff. |
| **API** | ✅ `POST /api/admin/user/<id>/portal-role` (Body: `portal_role`). ✅ `POST /api/admin/role/<role_name>/features` (Body: `features`). |
| **Rechte-UI** | ✅ Tab „User & Rollen“: User-Tabelle, Spalte „Rolle (wirksam)“, Dropdown „Rolle zuweisen“ (— Bitte zuweisen — + alle Rollen). ✅ Tab „Feature-Zugriff“: Block „Rollen & Feature-Zugriff“ (Rolle wählen, Checkboxen, Speichern) + „Nach Feature“ (Karten). Zusätzlich Tabs: E-Mail Reports, Title-Mapping, Navigation. |
| **feature_access** | ✅ Tabelle + Merge mit Config (`get_feature_access_from_db()`). Config dient noch als Fallback, **nicht** reine DB-SSOT. |
| **TITLE_TO_ROLE / get_role_from_title** | ✅ Noch vorhanden in `roles_config.py`. Werden **nur** noch für Anzeige genutzt (Tab „Title-Mapping“, Diagnose-Script), **nicht** für Berechtigungen. |

Der Prompt beschreibt den Wechsel **zu** Option B; im Drive ist Option B **bereits** der aktuelle Stand. Die Beschreibung im Prompt („Problem: portal_role aus LDAP … hat keine Auswirkung“) entspricht dem **historischen** Zustand vor der Umstellung.

---

## 2. Abgleich Prompt ↔ Drive

### Was der Prompt vorschlägt und was schon stimmt

- **Schritt 1 (DB-Migration):** Bereits erledigt (`portal_role_override` vorhanden). Prompt nutzt `TEXT`, Drive hat `VARCHAR(50)` — ausreichend.
- **Schritt 2 (Migrations-Script):** Im Drive **nicht** umgesetzt. Bestehende User haben `portal_role_override = NULL` und erhalten effektiv `mitarbeiter`. Ein einmaliges „Title → Override“-Script würde bestehende Rollen ins Portal übernehmen; optional, kein Muss für Option B.
- **Schritt 3 (auth_manager):** Logik bereits wie beschrieben (Kaskade, kein Title für Zugriff). ✅
- **Schritt 4 (roles_config):** Prompt will `TITLE_TO_ROLE` und `get_role_from_title()` **entfernen**. Im Drive werden sie noch für **Title-Mapping-Tab** und Diagnose-Script genutzt. Entfernen würde diese Anzeigen kaputt machen, es sei denn, man ersetzt sie durch reine „Info aus users.title“ ohne Rollen-Mapping.
- **Schritt 5 (Endpoints):** `portal-role` und `role/<name>/features` existieren. Prompt sieht zusätzlich **GET** `/admin/role/<name>/features` vor; im Drive wird die Feature-Liste pro Rolle aus der bestehenden `feature-access`-Antwort abgeleitet. GET pro Rolle wäre eine sinnvolle Ergänzung, aber nicht zwingend.
- **Schritt 6 (navigation_utils):** Verwendet bereits `current_user.portal_role` und `can_access_feature`. ✅
- **Schritt 7 (Template Redesign):** Siehe Abschnitt Mockup unten.
- **Schritt 8 (Diagnose-Script):** Script existiert, Hinweistext bereits auf Option B umgestellt. Optional: Ausgabe um „Quelle (Portal/Default)“ ergänzen.

### Abweichungen / fehlende Kenntnis

- **API-Pfad:** Prompt schreibt `/admin/user/...`, Drive nutzt `/api/admin/user/...`. Nur Doku-Anpassung.
- **feature_access als reine SSOT:** Prompt will „kein Fallback auf Python-Config“. Drive hat bewusst einen Merge (DB + Config) und Cache; reine DB-SSOT wäre eine weitere Änderung (z. B. alle Features in DB pflegen, Config nur für Initial-Befüllung).
- **Audit-Log:** Prompt verlangt Logging bei Rollenänderung. Im Drive aktuell nicht umgesetzt; sinnvoll, aber eigener kleiner Task.

---

## 3. Abgleich Mockup (React/JSX) ↔ Drive (Jinja2/Bootstrap)

Das Mockup ist eine **React-Komponente** (JSX) mit eigenem State; das Portal nutzt **Jinja2 + Bootstrap 5 + jQuery**, keine React-Runtime. Eine 1:1-Übernahme des Codes ist **nicht** möglich. Das Mockup dient als **konzeptionelles und visuelles Vorbild**, die Logik und das Layout sind in Jinja/JS nachzubauen.

### Inhaltliche Übereinstimmung

- **Tab „User & Rollen“:** User-Liste, Portal-Rolle (Dropdown), Quelle (Portal/Default), Aktion „Rolle ändern“ — entspricht der aktuellen Rechte-UI (inkl. „— Bitte zuweisen —“).
- **Tab „Rollen-Features“:** Rolle wählen (Buttons), Feature-Checkboxen gruppiert, Speichern — entspricht dem Block „Rollen & Feature-Zugriff“ im Tab Feature-Zugriff.
- **Tab „Matrix“:** Read-only Feature × Rolle — im Drive **nicht** vorhanden; wäre eine sinnvolle Ergänzung (Übersicht ohne Bearbeitung).
- **Tab „Architektur“:** Erklärung der Kaskade — im Drive nur als Text im Info-Banner; eigener Tab wie im Mockup optional (z. B. für Onboarding).

### Unterschiede Mockup ↔ Drive

| Aspekt | Mockup | Drive |
|--------|--------|--------|
| **Rollen** | 9 Rollen (u. a. geschaeftsfuehrung, teile) | 14 Rollen in `PORTAL_ROLES_FOR_ADMIN` (inkl. serviceberater, disposition, lager, callcenter, marketing) |
| **Features** | Andere IDs (z. B. provision, fahrzeugbestand, mitarbeiter_verwaltung, rechteverwaltung) | Echte Feature-IDs aus `FEATURE_ACCESS` (z. B. bankenspiegel, controlling, opos, verkauf_dashboard, sb_dashboard, whatsapp_teile) |
| **Standort-Filter** | Filter „Standort“ (Deggendorf/Landau) | User-Liste ohne Standort-Filter (Standort kommt aus company/AD, nicht in users-Tabelle) |
| **Filter „Ohne Rolle“ / „Mit Portal-Rolle“** | Vorhanden | Aktuell nur Suche; Filter nach „ohne Rolle“ wäre einfach ergänzbar |
| **Quelle „Portal ✓“ / „Default“** | Eigene Spalte | Könnte als kleine Kennzeichnung neben der wirksamen Rolle ergänzt werden |
| **Weitere Tabs** | Nur 4 (User, Rollen-Features, Matrix, Architektur) | Zusätzlich: E-Mail Reports, Title-Mapping, Navigation |

Die Feature-Liste im Mockup ist **vereinfacht** und weicht von den echten Feature-Namen und -Gruppen in Drive ab. Bei einem UI-Redesign müssen die **tatsächlichen** Features aus `feature_access`/Config und die echten Rollen aus `PORTAL_ROLES_FOR_ADMIN` verwendet werden.

---

## 4. Umsetzbarkeit — Kurzfassung

- **Fachlich:** Der Prompt beschreibt Option B, die im Drive **bereits umgesetzt** ist. Kein zweiter großer „Option-B-Umbau“ nötig.
- **Technisch:**  
  - **Prompt-Umsetzung „1:1“:** Teilweise obsolet (DB, Auth, Endpoints sind da). Offen: Migrations-Script (Title → Override), optional GET pro Rolle, evtl. TITLE_TO_ROLE nur für Anzeige behalten oder ersetzen, Audit-Log, feature_access als reine SSOT.  
  - **Mockup umsetzen:** Umsetzbar, aber als **Redesign der bestehenden Rechte-UI** (Jinja2/Bootstrap/jQuery), nicht als Einbau der React-Datei. Matrix-Tab und klarere Filter/Quelle-Anzeige sind naheliegende Erweiterungen.
- **Risiken:**  
  - Wenn `TITLE_TO_ROLE` und `get_role_from_title()` entfernt werden, müssen Title-Mapping-Tab und Diagnose-Script angepasst werden (nur Anzeige ohne Rollen-Mapping oder explizite „wirksame Rolle“ aus Kaskade).  
  - Reine DB-SSOT für Features: Alle heute nur in Config definierten Features müssten in der DB gepflegt werden, sonst „verschwinden“ sie nach einer Umstellung.

---

## 5. Empfehlung (ohne Code)

1. **Prompt als Referenz behalten,** aber mit dem Hinweis: „Option B ist in Drive bereits aktiv; Schritte 1, 3, 5 (teilw.), 6 sind erledigt.“  
2. **Mockup als UI-Vorlage** nutzen: Tabs und Interaktionen (User + Rolle, Rollen-Features, Matrix, ggf. Architektur) in die bestehende `rechte_verwaltung.html` übernehmen — mit echten Drive-Rollen und -Features, ohne React.  
3. **Optional umsetzen:**  
   - Migrations-Script: bestehende User einmalig von Title → `portal_role_override` übernehmen.  
   - Tab „Matrix“ (Feature × Rolle, read-only).  
   - Filter „Ohne Rolle“ / „Mit Portal-Rolle“ in der User-Liste.  
   - Quelle „Portal“ vs. „Default“ sichtbar machen.  
   - Audit-Log für Rollenänderungen.  
4. **Nicht voreilig:** `TITLE_TO_ROLE`/`get_role_from_title()` nur entfernen, wenn Title-Mapping und Diagnose neu definiert sind (z. B. nur noch Anzeige, keine Rollen-Ableitung).  
5. **SSOT feature_access:** Erst klären, ob alle Features in der DB gepflegt werden sollen; dann schrittweise Config-Fallback zurückfahren.

---

## 6. Dateien

- **Prompt:** `CURSOR_PROMPT_RECHTEVERWALTUNG.md` (im Sync; sollte ins Repo unter `docs/workstreams/auth-ldap/` übernommen werden).  
- **Mockup:** `rechteverwaltung_mockup.jsx` (im Sync; als Referenz z. B. `docs/workstreams/auth-ldap/rechteverwaltung_mockup.jsx` ins Repo, **nicht** als lauffähige App-Komponente).

Diese Validierung ersetzt keine Code-Änderungen; sie dient der Einordnung und Planung.
