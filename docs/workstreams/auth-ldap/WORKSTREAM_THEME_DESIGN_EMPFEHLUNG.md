# Workstream für Theme/Design: neuer Workstream oder nicht?

## Kurzantwort

**Meine Empfehlung: vorerst keinen neuen Workstream.** Theme, Mockups und Design-Einschätzung können bei **auth-ldap** bleiben. Einen eigenen Workstream „Design“ oder „Portal-UI“ würde ich nur anlegen, wenn ihr das Thema dauerhaft und breiter führen wollt.

---

## Warum bei auth-ldap bleiben kann

- **Startseite, Badges, Startseiten-Konfiguration** sind stark mit **Rollen und Rechten** verknüpft (Badges pro Rolle, Startseite pro User, Rechteverwaltung). Das ist inhaltlich auth-ldap.
- Die **Theme-Mockups** und die **Einschätzung Design-Anpassung** dienen der gleichen Sache: „Wie soll DRIVE aussehen und wie setzen wir es um?“ – das steht sinnvoll im Umfeld von Startseite/Rechteverwaltung.
- **Ein Workstream weniger** bedeutet weniger Kontext-Wechsel; alles zu „Wer sieht was wo“ (inkl. Look & Feel der Startseite) bleibt an einem Ort.

**Risiko:** auth-ldap wird thematisch etwas breiter (nicht nur Login/Rollen, sondern auch UI-Basis). Das ist vertretbar, solange die CONTEXT.md das abbildet (z. B. „Dashboard-Personalisierung, Startseiten-Badges, Theme-Vorschläge“).

---

## Wann ein eigener Workstream sinnvoll wäre

Einen Workstream **design** oder **portal-ui** würde ich anlegen, wenn:

- ihr ein **dauerhaftes Design-System** plant (zentrales Theme, Komponenten-Bibliothek, Barrierefreiheit, spätere Redesigns), **oder**
- ihr die Trennung scharf haben wollt: **auth-ldap** = nur Rechte/Login/Rollen, **design** = alles zu Farben, Schriften, Layout, Mockups.

Dann:

- `docs/workstreams/design/` (oder `portal-ui/`) anlegen,
- `CONTEXT.md` mit Kurzbeschreibung (Theme, Design-System, Mockups),
- Theme-Mockups, `EINSCHAETZUNG_DRIVE_DESIGN_ANPASSUNG.md`, ggf. `VORSCHLAG_DASHBOARD_BADGES_PRO_ROLLE.md` dorthin verschieben oder dort verlinken,
- in **auth-ldap** in der CONTEXT.md nur noch auf „Startseiten-Konfiguration / Badges pro Rolle“ verweisen und den Link zum Design-Workstream setzen.

---

## Praktische Empfehlung

- **Jetzt:** Keinen neuen Workstream anlegen. In **auth-ldap CONTEXT.md** einen kurzen Abschnitt ergänzen, z. B.:  
  „**Theme & Design:** Vorschläge und Mockups für zentrales DRIVE-Theme liegen in diesem Ordner (MOCKUP_THEME_*.html, EINSCHAETZUNG_DRIVE_DESIGN_ANPASSUNG.md, README_THEME_MOCKUPS.md). Umsetzung Theme/Badges pro Rolle wird hier mitgeführt.“
- **Später:** Wenn ihr ein klares, längerfristiges „Design-System“-Thema habt, einen Workstream **design** (oder **portal-ui**) anlegen und die genannten Docs dorthin verschieben bzw. verlinken.

Damit bleibt die Entscheidung flexibel und die aktuelle Struktur überschaubar.
