# Warum greift die Rolle nicht? + Vorschlag granularere Rechte

**Stand:** 2026-02-19  
**Anlass:** Silvia Eiglmaier – Rolle von Buchhaltung auf Verkauf geändert, in Drive weiterhin voller Zugriff auf alle Navi-Punkte.

---

## 1. Prüfung Silvia Eiglmaier (Diagnose vom 19.02.2026)

Ausführung: `python scripts/checks/check_user_portal_role.py "Eiglmaier"`

| Feld | Wert |
|------|------|
| **username** | silvia.eiglmaier@auto-greiner.de |
| **ou (AD)** | **Buchhaltung** |
| **title (AD→DB)** | **Mitarbeiterin Buchhaltung** |
| **user_roles** | buchhaltung |
| **→ portal_role** | buchhaltung |
| **→ Features** | 19 (u.a. bankenspiegel, controlling, auftragseingang, …) |

**Fazit:** Im System kommt die Rolle weiterhin aus dem **LDAP**:  
- **OU** = Buchhaltung (nicht Verkauf)  
- **Title** = „Mitarbeiterin Buchhaltung“

Solange im AD beides so bleibt, wird bei jedem Login `users.title` und `users.ou` aus dem LDAP aktualisiert und die abgeleitete **portal_role** bleibt „buchhaltung“ – mit Zugriff auf fast alle fachlichen Features.

---

## 2. Warum „Rolle in Drive geändert“ nicht greift

### Zwei getrennte Quellen

| Quelle | Verwendung | Wo geändert? |
|--------|-------------|--------------|
| **LDAP: Title** | → **portal_role** (für Navi + `can_access_feature`) | Nur im **AD** (Feld „Titel“ / title). |
| **LDAP: OU** | → Einträge in **user_roles** (z.B. buchhaltung, verkauf) | Nur im **AD** (Organisationseinheit). |

- **Rechteverwaltung im Portal** (`/admin/rechte_verwaltung`) ändert nur **user_roles** (Tabelle `user_roles`).
- **Navigation und Feature-Zugriff** nutzen aber **portal_role** und **allowed_features**, die aus **users.title** kommen (über `get_role_from_title()`), nicht aus den in der Rechteverwaltung zugewiesenen Rollen.

Ausnahme: Ist in **user_roles** die Rolle **admin** zugewiesen, wird die Portal-Rolle auf „admin“ gesetzt und alle Features werden freigegeben. Für alle anderen Rollen (z. B. „Verkauf“) hat die Rechteverwaltung **keine** Auswirkung auf Navi/Features.

### Ablauf konkret

1. **Login:** LDAP liefert `title` + `ou` → `portal_role = get_role_from_title(title)`; `_cache_user()` schreibt `title`/`ou` in `users` und schreibt **user_roles** aus der OU (außer bei Admin).
2. **Session-Reload (get_user_by_id):** `portal_role` wird aus **users.title** berechnet, nicht aus **user_roles**. Nur bei Rolle „admin“ in **user_roles** gibt es den Override.

Wenn also nur in der **Portal-Rechteverwaltung** „Verkauf“ zugewiesen wurde, aber im AD **OU** und **Title** weiter „Buchhaltung“ / „Mitarbeiterin Buchhaltung“ sind, bleibt **portal_role = buchhaltung** und der Zugriff bleibt unverändert.

---

## 3. Sofortmaßnahme für Silvia

- **Im AD anpassen:**  
  - **OU** auf z. B. „Verkauf“ stellen.  
  - **Titel** auf einen Eintrag setzen, der in `config/roles_config.py` unter `TITLE_TO_ROLE` auf „verkauf“ abgebildet ist (z. B. „Verkäuferin“, „Verkaufsberaterin“, „Automobilkauffrau“).
- **Silvia:** Einmal **abmelden und wieder anmelden**, damit `users.title`/`ou` und damit **portal_role** neu aus dem LDAP gesetzt werden.

Optional: Aktuellen Stand prüfen mit  
`python scripts/checks/check_user_portal_role.py "Eiglmaier"`.

---

## 4. Vorschlag: Granularere Rechteverwaltung

Der Umfang der Features ist gewachsen; eine klarere und granularere Rechteverwaltung ist sinnvoll.

### 4.1 Kurzfristig (minimaler Aufwand)

**Portal-Rollen-Override in der Rechteverwaltung**

- **Ziel:** Änderungen in der Rechteverwaltung sollen die **tatsächlich genutzte** Portal-Rolle und damit Navi/Features steuern.
- **Umsetzung:**  
  - In der Rechteverwaltung eine **Portal-Rolle** pro User pflegbar machen (z. B. Auswahl: wie in `roles_config.TITLE_TO_ROLE` / `FEATURE_ACCESS`: admin, buchhaltung, verkauf, verkauf_leitung, …).  
  - Diese in der DB speichern (z. B. neues Feld **users.portal_role_override** oder Tabelle **user_portal_role_override**).  
  - In **auth_manager** (Login + **get_user_by_id**):  
    - Wenn für den User ein **portal_role_override** gesetzt ist → **portal_role** und **allowed_features** daraus ableiten.  
    - Sonst wie bisher: **portal_role** aus **users.title** (LDAP).
- **Effekt:** Silvia (und andere) können im Portal auf „Verkauf“ gestellt werden, ohne dass der AD-Titel sofort angepasst werden muss; die Navigation reagiert sofort nach dem nächsten Request/Relogin.

### 4.2 Mittelfristig (strukturell)

**Feature-Zugriff pro User/Rolle granular**

- **Ziel:** Nicht nur grobe Rollen (admin, buchhaltung, verkauf), sondern gezielter Zugriff auf Features (z. B. „nur Bankenspiegel“, „nur Urlaubsplaner“, „Verkauf + ausgewählte Reports“).
- **Bausteine:**  
  - Tabelle **feature_access** (bereits vorhanden) für Rollen nutzen bzw. erweitern.  
  - Optional: **user_feature_override** (user_id, feature_name, allow/deny), um Abweichungen pro User zu erlauben.  
  - **Navigation:** Bereits an `requires_feature` und `role_restriction` angebunden; Logik in `navigation_utils.get_navigation_for_user()` und `can_access_feature` beibehalten und ggf. um User-Override erweitern.

**Einheitliche Rolle pro Request**

- **portal_role** und **allowed_features** aus **einer** logischen Quelle:  
  - Entweder **Override** (Rechteverwaltung) **oder** LDAP (title).  
  - Keine versteckte Doppelung (OU vs. Title); **user_roles** nur noch für „admin“-Override oder für künftige feinere Aktionen (z. B. „darf Genehmigungen für Abteilung X“).

### 4.3 Optional: SSOT-Dokumentation

- In **CLAUDE.md** oder **CONTEXT.md** auth-ldap festhalten:  
  - „Portal-Rolle und Feature-Zugriff kommen aus: 1) users.portal_role_override (falls gesetzt), 2) sonst users.title (LDAP). user_roles nur für Admin-Override.“  
- So vermeidet man künftig Missverständnisse wie „Rolle in Rechteverwaltung geändert, aber nichts passiert“.

---

## 5. Dateien / Stellen im Code

| Thema | Datei | Stelle |
|-------|-------|--------|
| portal_role beim Login | `auth/auth_manager.py` | `authenticate_user`: `get_role_from_title(ldap_title)`; `_cache_user(title=...)` |
| portal_role bei Session | `auth/auth_manager.py` | `get_user_by_id`: `user_title = user_row['title']`, `portal_role = get_role_from_title(user_title)`; Admin-Override wenn `'admin' in roles` |
| Navi-Filter | `api/navigation_utils.py` | `get_navigation_for_user`: `user_role = current_user.portal_role`; Filter nach `requires_feature` und `role_restriction` |
| Feature-Zugriff | `config/roles_config.py` | `get_role_from_title`, `FEATURE_ACCESS`, `get_allowed_features`, `get_feature_access_from_db()` |
| Rechteverwaltung (nur user_roles) | `api/admin_api.py` | `assign_role` / `remove_role` schreiben nur in `user_roles` |

---

## 6. Diagnose-Script

- **Script:** `scripts/checks/check_user_portal_role.py`  
- **Aufruf:**  
  - Alle User: `python scripts/checks/check_user_portal_role.py`  
  - Ein User: `python scripts/checks/check_user_portal_role.py "Eiglmaier"`  
- Zeigt pro User: **username**, **ou**, **title**, **user_roles**, abgeleitete **portal_role** und Hinweis, ob der Title in `TITLE_TO_ROLE` vorkommt.
