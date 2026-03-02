# Nächster Schritt: Rechte & Navi am User prüfen

**Stand:** 2026-03-02  
**Anlass:** Rechteverwaltung ist entschlackt (B, C, D), aber Admins können **am User** nicht direkt sehen, welche Navi und welche Zugriffsrechte dieser User hat. Man müsste sich gedanklich durch „Rolle → Features → Navi“ hangeln oder als User einloggen.

---

## Ziel

**Am User seine Navi und seine Zugriffsrechte überprüfen können** – ohne Rollen-Tab und Navi-Tab zu wechseln und ohne sich als dieser User einzuloggen.

- Admin klickt auf einen User (oder öffnet eine „User-Sicht“) und sieht sofort:
  - **Wirksame Portal-Rolle** (bereits in der User-Tabelle)
  - **Features**, die dieser User hat (Liste, abgeleitet aus der Rolle)
  - **Navigation**, die dieser User sieht (Menüpunkte, die er laut Rechten sieht – z. B. als Baum oder Liste)

Optional: Startseite, Filter-Verhalten pro Listen-Feature (nur eigene / alle) für diesen User.

---

## Mögliche Umsetzung (Vorschlag)

### Option 1: Modal „Rechte & Navi für [Name]“

- In der User & Rollen-Tabelle: neuer Button pro Zeile, z. B. **„Rechte & Navi“** (Icon: Auge oder Liste).
- Klick öffnet ein Modal mit:
  - **Rolle:** z. B. „Verkauf“ (effective_portal_role).
  - **Features (Zugriff):** Liste der Feature-Namen, die diese Rolle hat (read-only, aus role_features/DB).
  - **Navigation (sichtbare Menüpunkte):** Liste oder Baum der Navi-Items, die für diese Rolle sichtbar wären (gleiche Logik wie in `navigation_utils` / Navi-Rendering: Filter nach requires_feature + role_restriction).
- Keine Bearbeitung im Modal – nur Anzeige. Bearbeitung bleibt: Rolle zuweisen in der Tabelle, Features in „Rollen & Module“.

**Vorteil:** Ein Klick pro User, alles an einem Ort.  
**Aufwand:** Backend: Endpoint z. B. `GET /api/admin/user/<id>/effective-rights` (effective_role, list of features, list of nav items). Frontend: Modal + Aufruf beim Klick.

### Option 2: Aufklappbare Zeile (Accordion) pro User

- Jede User-Zeile kann aufgeklappt werden (z. B. Klick auf Zeile oder kleines Chevron).
- Darunter erscheint ein Block: **Rolle | Features | Navi** (kompakt, gleiche Daten wie Option 1).

**Vorteil:** Kein Modal, alles in der Liste.  
**Nachteil:** Tabelle wird länger; bei vielen Usern evtl. unübersichtlich.

### Option 3: Eigener Bereich „Als User prüfen“

- Dropdown „User wählen“ (oder Suche) → Auswahl eines Users.
- Darunter: Anzeige von Rolle, Features, Navi (wie in Option 1), ggf. zusätzlich „Startseite“ und „Filter-Verhalten“ für Listen-Features.

**Vorteil:** Klar getrennte „Prüf-Ansicht“.  
**Nachteil:** Ein Klick mehr (User erst wählen).

---

## Empfehlung

**Option 1 (Modal „Rechte & Navi für [Name]“)** – geringer Aufwand, sofort nutzbar, stört das bestehende Layout nicht. Backend: ein Endpoint, der für eine User-ID die effective_role, die erlaubten Features und die sichtbaren Navi-Items zurückgibt (nutzt bestehende Logik aus auth_manager / roles_config / navigation_utils). Frontend: Button in der User-Tabelle, Modal mit drei Blöcken (Rolle, Features, Navi).

---

## Technik (Stichpunkte)

- **Effective Role:** Bereits in `usersData` bzw. API `users-roles` als `effective_portal_role` – kann wiederverwendet werden.
- **Features für Rolle:** `get_feature_access_from_db()` / `get_allowed_features(role)` – bereits vorhanden.
- **Navi für Rolle:** Gleiche Filterlogik wie in `api/navigation_utils.py` (Items mit requires_feature, role_restriction; Rekursion für Parent-Child). Entweder bestehende Funktion erweitern („get visible nav items for role“) oder im Backend für Admin-Endpoint nachbilden.
- **Neuer Endpoint:** z. B. `GET /api/admin/user/<user_id>/effective-rights` → `{ "effective_role": "verkauf", "features": ["auftragseingang", "auslieferungen", ...], "navigation": [ { "label": "...", "url": "...", "children": [...] } ] }`.

---

## Priorität

- Als **nächster Schritt** nach der Entschlackung sinnvoll: wenig UI-Änderung (ein Button + ein Modal), großer Nutzen für Admins („Was sieht Max Mustermann?“ sofort beantwortbar).
- Keine Änderung an der bestehenden Rollen-/Feature-Pflege – nur eine **Lese-Ansicht** pro User.
