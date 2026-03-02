# Prompt: Rechteverwaltung – Stand, Komplexität, Recherche

**Zweck:** Diesen Abschnitt als Kontext an Claude geben oder als Basis für Web-Recherche nutzen („Wie machen andere RBAC/Rechteverwaltung in internen Portalen?“).

---

## Kontext in einem Absatz

Wir betreiben ein **internes Unternehmensportal** (Flask, PostgreSQL, LDAP/AD-Login) für ein Autohaus mit mehreren Standorten und Abteilungen (Verkauf, Buchhaltung, Werkstatt, Service, Admin). Der **Feature-Umfang** ist über die Zeit gewachsen (Controlling, Verkauf, Urlaub, Teile, WhatsApp, Navigation …). Wir haben eine **Rechteverwaltung** eingeführt: Zugriff soll **nur aus dem Portal** kommen (Option B), LDAP liefert nur Identität. Pro User weist ein Admin eine **Portal-Rolle** zu; pro Rolle sind **Features** (Bankenspiegel, Controlling, Verkauf, …) konfigurierbar. Die **Navigation** wird nach Rolle/Feature gefiltert. Wir fragen uns: **Wie baut man so etwas übersichtlich und wartbar?** Gibt es bewährte Muster, Begriffe oder Open-Source-Ansätze für „RBAC + Feature-Flags + Admin-UI“ in vergleichbarer Größe?

---

## Technischer Stand (kurz)

- **Auth:** LDAP/AD Login; Session mit Flask-Login; User-Objekt mit `portal_role`, `allowed_features`.
- **Wirksame Rolle:** (1) Wenn User in DB-Tabelle `user_roles` die Rolle **admin** hat → voller Zugriff. (2) Sonst: Spalte **users.portal_role_override** (von Admin im Portal gesetzt) → diese Rolle. (3) Sonst Default **mitarbeiter** (minimaler Zugriff). **Kein** LDAP-Titel/OU mehr für Berechtigungen.
- **Feature-Zugriff:** Tabelle **feature_access** (feature_name, role_name); Merge mit Fallback aus Config (`roles_config.FEATURE_ACCESS`). Abfrage: „Hat Rolle X Zugriff auf Feature Y?“ → Navigation + Route-Guards.
- **Navigation:** Tabelle **navigation_items** mit optionalem **requires_feature** und **role_restriction**. Beim Rendern: nur Einträge anzeigen, auf die der User (über seine Rolle) Zugriff hat.
- **Admin-UI (Rechteverwaltung):**
  - Tab **User & Rollen:** User-Liste, pro User ein Dropdown „Rolle zuweisen“ (Portal-Rolle), OU/Title aus LDAP nur zur Info.
  - Tab **Feature-Zugriff:** (a) „Rollen & Feature-Zugriff“: Rolle wählen, Checkboxen pro Feature, speichern. (b) „Nach Feature“: pro Feature die Rollen anzeigen/bearbeiten.
  - Tab **Navigation:** Baum aus DB, Bearbeiten (Label, URL, Feature, Rolle, Aktiv), Löschen.
- **Stack:** Flask 3, PostgreSQL, Jinja2, Bootstrap 5, kein separates Frontend-Framework.

---

## Wo es komplex wird

1. **Zwei Ebenen:** (a) **User → Rolle** (eine Rolle pro User), (b) **Rolle → Features** (viele-zu-viele). Beides in einer UI unterzubringen und trotzdem verständlich zu halten.
2. **Zwei Sichten in der UI:** „Nach Rolle“ (Rolle wählen, dann Features) vs. „Nach Feature“ (Feature wählen, dann Rollen). Beides nötig, aber wirkt schnell unübersichtlich.
3. **Begriffe:** Es gibt **user_roles** (DB, v. a. „admin“), **portal_role** (die eine wirksame Rolle für Navi/Features), **feature_access** (Rolle ↔ Feature). Für neue Admins nicht sofort klar.
4. **Hybrid Config/DB:** Feature-Zugriff kommt aus DB, mit Fallback aus Python-Config – Cache-Invalidierung und klare SSOT sind aufwändig.
5. **Navigation:** Jeder Eintrag kann `requires_feature` und/oder `role_restriction` haben; die Logik („User hat Rolle X → hat Feature Y?“) muss überall konsistent sein.

---

## Was wir klären wollen

- **Begriffe & Modelle:** Gibt es etablierte Begriffe für „Rolle“, „Permission“, „Feature“, „Scope“ in RBAC, die wir nutzen sollten (z. B. RBAC vs. ABAC, Permission vs. Feature-Flag)?
- **Admin-UI:** Bewährte Strukturen für „User verwalten + Rollen zuweisen + Rollen mit Berechtigungen verknüpfen“ – ein Dashboard, mehrere Tabs, oder klare Trennung (z. B. „Rollen“ vs. „Benutzer“)?
- **Granularität:** Sollen wir bei „eine Rolle pro User + Rolle hat N Features“ bleiben, oder lohnt sich ein Schritt zu „Permission/Feature pro User“ (feiner, aber mehr Komplexität)?
- **Open Source / Referenzen:** Gibt es kleine bis mittlere Open-Source-Portale oder Admin-Templates (Flask/Django/Python oder auch andere Stacks), die RBAC + Feature-Zugriff + Admin-UI vorbildlich umsetzen, an denen wir uns orientieren können?
- **LDAP-Integration:** Best Practice: Rechte **komplett** im Portal (wie unser Option B) vs. „Rollen aus AD-Gruppen übernehmen und im Portal nur verfeinern“?

---

## Suchbegriffe für Recherche

- RBAC admin UI best practices
- Role-based access control Flask Python
- Permission vs role vs feature flag terminology
- User role permission matrix UI design
- LDAP role sync vs application-managed roles
- Open source admin panel RBAC

---

## Kurzfassung für Copy-Paste (z. B. an Claude)

```
Wir haben ein internes Flask-Portal mit LDAP-Login. Rechte kommen nur aus dem Portal (eine Portal-Rolle pro User, zugewiesen von Admin). Pro Rolle sind Features (z. B. bankenspiegel, verkauf) in einer feature_access-Tabelle konfigurierbar; Navigation wird danach gefiltert. Admin-UI: User-Liste mit Rollen-Dropdown, plus getrennt "Rollen & Features" (Rolle wählen → Features an/ab) und "Nach Feature" (Feature → Rollen). Wo wird das schnell unübersichtlich: zwei Sichten (nach Rolle / nach Feature), Begriffe (user_roles, portal_role, feature_access), Hybrid Config/DB. Frage: Gibt es etablierte Begriffe, UI-Muster oder Open-Source-Referenzen für RBAC + Feature-Zugriff + Admin-Verwaltung in vergleichbarer Größe (kein Groß-Enterprise)?
```

---

## Recherche-Anhaltspunkte (Web, Stand grob 2025)

*Die folgenden Punkte stammen aus einer kurzen Web-Recherche; bitte selbst prüfen und vertiefen.*

### Begriffe & Modell

- **User, Role, Permission** klar trennen: User hat Rollen, Rolle hat Permissions (nicht alles in einer „Rolle“ mischen). Unser „Feature“ entspricht oft **Permission** oder **Capability**.
- **Principle of Least Privilege:** Nur das Minimum an Rechten vergeben; Rollen nach **Tätigkeit** definieren, nicht nur nach Jobtitel.
- **Rollen-Hierarchie:** Erlaubt Vererbung (z. B. „Verkaufsleitung“ erbt „Verkauf“) und reduziert Doppelpflege. Wir haben das bisher nur für Urlaub (ROLE_HIERARCHY), nicht für Features.

### UI / Admin

- Rollen **getrennt** von Benutzerverwaltung denken: zuerst „Rollen & Permissions“ definieren, dann „User → Rolle(n)“ zuweisen.
- Regelmäßige **Audits** und klare **Dokumentation** der Rechte werden empfohlen.
- Für KMU: „Kaufen statt selber bauen“ wird oft genannt – bei uns ist die Anforderung aber stark an LDAP und bestehende Strukturen gekoppelt.

### Technik (Flask)

- **Flask-RBAC** (flask-rbac.readthedocs.io, GitHub shonenada/flask-rbac): Rollen-Modelle, Whitelist/Denylist, DB-Anbindung (SQLAlchemy) – könnte als Referenz für Begriffe/Struktur dienen.
- **Permit.io** u. ä.: Policy-as-Code, feine Berechtigungen; eher für größere/cloudige Setups.
- Flask hat von Haus aus **kein** RBAC; viele Projekte bauen wie wir: eigene Tabellen (user_roles, feature_access) + Decorators.

### Nützliche Suchbegriffe

- `RBAC best practices small business`
- `Flask RBAC permission role`
- `role permission matrix UI`
- `LDAP application-managed roles vs sync`

### Links (zum Nachlesen)

- WorkOS Blog: RBAC best practices  
- Oso HQ: RBAC best practices  
- Flask-RBAC (Read the Docs)  
- Secure Identity Hub: RBAC for small enterprises  

*(URLs gezielt im Browser nachziehen, falls du die genauen Seiten brauchst.)*
