# Vorschlag: Urlaub & Genehmiger – UI aufräumen und vereinheitlichen

**Kontext:** Option A (vacation_approval_rules als SSOT) ist umgesetzt. Die Oberflächen für Urlaub, Genehmiger und Organisation sind gewachsen und wirken an mehreren Stellen; hier ein Vorschlag für eine **ordentliche, aufgeräumte UI**.

---

## 1. Aktuelle Oberflächen (Ist)

| Bereich | Route | Zweck | Zielgruppe |
|--------|--------|--------|------------|
| **Urlaubsplaner** | `/urlaubsplaner` (→ v2) | Kalender, eigene Buchungen, „Zu genehmigen“ | Alle MA, Genehmiger |
| **Urlaubsplaner Admin** | `/urlaubsplaner/admin` | Ansprüche, Urlaubssperren, Mitarbeiter-Tabelle | HR/Admin |
| **Chef-Übersicht** | `/urlaubsplaner/chef` | Alle Genehmiger + Teams + offene Anträge | Geschäftsführung / Admin |
| **Team Greiner (Organigramm)** | `/admin/organigramm` | Abteilungen, Hierarchie, **Vertretungen**, **Genehmiger**, Abwesenheitsgrenzen | Admin |

**Probleme:**
- **Genehmiger** erscheinen an zwei Orten: Organigramm-Tab „Genehmiger“ (Konfiguration) und Chef-Übersicht (Lese-Ansicht). Unklar: „Wo ist die eine Quelle?“
- **Urlaub** hat drei Einstiege: Planer, Admin, Chef – ohne klares Dach.
- Unterschiedliche **Design-Sprachen**: Admin rot, Chef dunkel/lila, Organigramm lila/weiß, Planer lila – kein einheitliches „Urlaub/Team“-Look.
- Navigation: Chef-Übersicht von Admin aus verlinkt; Organigramm unter „Admin“; Urlaub oft über Navi „Team Greiner“ oder eigenes „Urlaub“.

---

## 2. Vorschlag: Ein Dach „Team & Urlaub“, eine Design-Sprache

### 2.1 Information Architecture (vereinfacht)

```
Team Greiner (oder "Personal / Team")
├── Übersicht (Dashboard: Kapazität heute, offene Anträge, Schnelllinks)
├── Abteilungen (wie bisher: Liste nach Abteilung)
├── Hierarchie (wie bisher: Baum)
├── Vertretungen (wer vertritt wen – unverändert)
├── Genehmiger für Urlaub (eine Seite: Regeln pflegen + optional „Vorschau Teams“)
└── Abwesenheitsgrenzen (wie bisher)

Urlaub (eigener Menüpunkt oder Unterpunkt von Team)
├── Mein Urlaub / Kalender (aktueller Planer v2 – für alle)
├── Zu genehmigen (für Genehmiger: gleiche Box wie heute, evtl. eigener Tab oder hervorgehoben)
├── Chef-Übersicht (alle Genehmiger + Teams + offene Anträge – nur für Admin/GL)
└── Administration (Ansprüche, Sperren – nur HR/Admin)
```

**Kernidee:**
- **Eine Stelle für „Wer genehmigt für wen?“** = Team Greiner → **Genehmiger für Urlaub**. Dort nur die Tabelle + „Neue Regel“; kein zweiter Ort mit anderer Semantik.
- **Chef-Übersicht** = reine **Lese-/Übersichtsseite** (keine Konfiguration), klar als „Übersicht für GL/Admin“ beschriftet und von Team Greiner aus verlinkt („Als Übersicht anzeigen“).
- **Urlaub** = ein Modul mit klaren Unterpunkten: Kalender (alle), Zu genehmigen (Genehmiger), Chef-Übersicht (Admin/GL), Administration (HR/Admin).

### 2.2 Einheitliche Design-Sprache

- **Eine Farbe für „Urlaub / Abwesenheit“**: z. B. ein kräftiges Blau oder ein Grün (nicht rot für Admin, um Verwechslung mit „Fehler“ zu vermeiden).  
  Vorschlag: **Urlaub = Blau/Lila** (wie aktuell Planer), **Admin/HR-Funktionen = dezent grau oder gleiches Blau mit „Admin“-Badge**.
- **Karten/Layout:** überall gleiche Karten (weiß, leichter Schatten, abgerundete Ecken), gleiche Abstände, gleiche Typo (Überschriften, Tabellen).
- **Buttons:** ein Primär-Button-Style (z. B. „DRIVE-Blau“) für Hauptaktionen; Sekundär für „Zurück“/„Abbrechen“; Gefahr nur für Löschen.
- **Tabellen:** ein gemeinsames `.table-module` (Header grau, Hover-Zeile, klare Trennlinien) für Vertretungen, Genehmiger, Abwesenheitsgrenzen, Admin-Mitarbeiterliste.

### 2.3 Konkrete Aufräum-Maßnahmen

| Maßnahme | Beschreibung |
|----------|--------------|
| **1. Team Greiner: Tab „Genehmiger“ umbenennen** | In „Genehmiger für Urlaub“ oder „Urlaub genehmigen – Regeln“. Kurzer Hinweistext oben: „Diese Regeln steuern, wer im Urlaubsplaner Anträge genehmigen darf. Chef-Übersicht zeigt die Teams.“ |
| **2. Chef-Übersicht: Verweis auf eine Quelle** | Oben einen Satz: „Basierend auf den Genehmigungsregeln unter Team Greiner → Genehmiger.“ + Link dorthin. |
| **3. Urlaubsplaner: Klare Karte „Zu genehmigen“** | Box „Zu genehmigen“ immer sichtbar für Genehmiger (wie jetzt), aber mit klarem Titel und evtl. Icon; leer = „Keine offenen Anträge“. |
| **4. Admin-Seite Urlaub: Verlinkung vereinheitlichen** | Oben drei Buttons: „← Kalender“, „Chef-Übersicht“, „Team Greiner → Genehmiger“ (so ist klar: Konfiguration dort). |
| **5. Navigation (DB/Navi)** | Ein Eintrag „Urlaub“ mit Unterpunkten (Kalender, Chef-Übersicht, Administration) ODER „Team Greiner“ mit Unterpunkt „Urlaub“ – je nach aktuellem Navi-Aufbau; wichtig: nur eine logische Gruppe. |
| **6. Redundanz vermeiden** | Keine zweite „Genehmiger konfigurieren“-Seite neben Team Greiner. Chef-Übersicht nur Anzeige. |

---

## 3. Optional: Eigenes kleines „Urlaub“-Dashboard

Statt direkt in den Kalender zu springen, könnte **Urlaub** eine kleine Startseite haben:

- **Als MA:** eine Karte „Mein Urlaub“ (Resturlaub, Link zum Kalender) + ggf. „Meine Anträge“.
- **Als Genehmiger:** zusätzlich Karte „Zu genehmigen (N)“ mit Link in den Kalender (Filter auf „Zu genehmigen“).
- **Als Admin:** zusätzlich Links „Chef-Übersicht“, „Administration“.

Das wäre ein optionaler Schritt; der aktuelle Einstieg „Kalender direkt“ kann beibehalten werden, wenn gewünscht.

---

## 4. Kurz-Checkliste für die Umsetzung

- [ ] Tab „Genehmiger“ im Organigramm: Beschriftung + Hinweistext (eine Quelle).
- [ ] Chef-Übersicht: Hinweis + Link zu Team Greiner → Genehmiger.
- [ ] Urlaubsplaner: „Zu genehmigen“-Karte klar und immer sichtbar für Genehmiger.
- [ ] Urlaubs-Admin: Links zu Kalender, Chef-Übersicht, Genehmiger.
- [ ] Gemeinsame CSS-Klassen/Komponenten für Karten, Tabellen, Buttons (z. B. in `base.html` oder einem gemeinsamen `urlaub-org.css`).
- [ ] Navi: Einträge so setzen, dass „Urlaub“ und „Team Greiner“ eindeutig und ohne Doppelung sind.

Wenn du willst, können wir als Nächstes **nur die Texte/Links** (Hinweistexte, Tab-Beschriftung, Buttons) umsetzen und danach schrittweise das gemeinsame Styling (Karten, Tabellen) anpassen.

---

## 5. Vergleich: Dein Vorschlag vs. meiner

**Dein Vorschlag (kurz):**
- **Mitarbeiter im Organigramm bearbeiten:** Abteilung, Genehmiger, Vertritt, wird vertreten – alles an einer Stelle pro Person.
- **Organigramm unter Mitarbeiterverwaltung** – nicht mehr eigenständig im Admin-Dropdown, sondern Unterpunkt von „Mitarbeiterverwaltung“.
- **Urlaubsplaner Admin** als eigener Menüpunkt **entfällt** – die Funktion (Ansprüche, Sperren) muss woanders leben.

**Mein Vorschlag (kurz):**
- Team Greiner/Organigramm bleibt eigener Einstieg (oder unter Team Greiner); Genehmiger = **Regel-Tabelle** (Gruppe/Standort → Genehmiger), nicht pro MA.
- Urlaub mit Unterpunkten: Kalender, Zu genehmigen, Chef-Übersicht, **Administration** (Ansprüche, Sperren) – „Urlaubsplaner Admin“ bleibt inhaltlich, nur besser verlinkt.

| Thema | Dein Vorschlag | Meiner | Bewertung |
|-------|----------------|--------|-----------|
| **Wo wird konfiguriert?** | Pro Mitarbeiter im Organigramm (Abteilung, Genehmiger, Vertritt, wird vertreten) | Regeln-Tabelle „Gruppe → Genehmiger“ + Vertretungen-Tabelle; Abteilung kommt aus MA-Stammdaten | Dein Ansatz: **eine Oberfläche** pro Person, sehr aufgeräumt. Meiner: eine Tabelle für viele. Beides konsistent – deiner ist näher an „eine Person, ein Dialog“. |
| **Organigramm unter Mitarbeiterverwaltung** | Ja | Ich hatte Organigramm/Team Greiner als eigenen Eintrag gelassen | **Dein Vorschlag ist klarer:** Alles rund um MA (Stammdaten, Struktur, Vertretung, Genehmiger) unter einem Dach „Mitarbeiterverwaltung“. Weniger Punkte im Admin-Menü. |
| **Urlaubsplaner Admin „entfällt“** | Ja, als Menüpunkt weg | Bei mir blieb die **Seite** (Ansprüche, Sperren), nur besser eingebunden | Wenn der Menüpunkt wegfällt: Die **Inhalte** (Ansprüche bearbeiten, Sperren) brauchen einen Ort. Mögliche Orte: (a) **In Urlaub** als „Administration“ / „Urlaubsansprüche“ (nur für Admin), (b) **In Mitarbeiterverwaltung** als Unterpunkt „Urlaub & Ansprüche“ oder beim Bearbeiten eines MA. Option (a) hält Urlaub geschlossen; Option (b) hält alles Personal unter Mitarbeiterverwaltung. |

**Fazit / Empfehlung**

- **Organigramm unter Mitarbeiterverwaltung** und **Urlaubsplaner Admin als Menüpunkt streichen** finde ich **sehr gut** – weniger Einträge, klare Hierarchie.
- **Mitarbeiter im Organigramm bearbeiten** (Abteilung, Genehmiger, Vertritt, wird vertreten) ist **stark**: eine Stelle pro Person statt Regeln und Vertretungen an getrennten Tabs. Dafür muss geklärt werden:
  - **Genehmiger:** Entweder pro MA ein Feld „Genehmiger“ (dann könnte die Regel-Tabelle aus Option A aus den **Daten** der MA abgeleitet werden), oder wir behalten die Regel-Tabelle und im Organigramm bearbeiten wir nur **Abteilung** (und Standort) – der Genehmiger folgt dann aus „Gruppe → Genehmiger“. Beides ist konsistent mit Option A möglich; pro MA ist intuitiver („Für Susanne ist Margit zuständig“).
- **Wo die Admin-Inhalte (Ansprüche, Sperren) leben**, wenn „Urlaubsplaner Admin“ weg ist: Am wenigsten Verwirrung entsteht, wenn sie **unter dem Urlaubsplaner** erreichbar sind (z. B. Link „Administration“ / „Urlaubsansprüche“ für Berechtigte im Planer oder auf einer kleinen Urlaub-Startseite), **ohne** eigenen Admin-Menüpunkt. So bleibt „Urlaubsplaner Admin“ in der Navi weg, die Funktion bleibt aber auffindbar für Admins im Kontext Urlaub.

**Kurz:** Dein Vorschlag (Organigramm unter Mitarbeiterverwaltung, Bearbeiten pro MA im Organigramm, Urlaubsplaner Admin-Menüpunkt weg) geht in die richtige Richtung und ist mit meinem Vorschlag vereinbar; ich würde nur die Admin-Funktion (Ansprüche, Sperren) weiter unter **Urlaub** erreichbar lassen (als Unterpunkt/Link), nicht als eigenen Admin-Eintrag.

---

## 6. Erweiterung: Alles in Rechteverwaltung (aktueller Vorschlag)

**Idee:** Die **gesamte** Urlaubsverwaltung und Mitarbeiter-Konfiguration in die **Rechteverwaltung** legen – ein zentraler Admin-Ort für „Wer darf was?“ und „Wer ist wem zugeordnet?“.

**Rechteverwaltung** (SSOT: Portal, Option A) hat heute:
- User & Rollen (Portal-Rolle pro User, Rollen-Features, Matrix, Architektur, E-Mail Reports, Nach Feature, Title-Mapping, Navigation).

**Erweiterung – neue Tabs/Bereiche:**
- **Mitarbeiter-Konfig** (oder „Struktur & Vertretung“):  
  Pro Mitarbeiter bearbeitbar: Abteilung, Standort, Genehmiger (für Urlaub), Vertritt, wird vertreten. Entspricht dem bisherigen Organigramm-Inhalt (Abteilungen, Hierarchie, Vertretungen, Genehmiger) – aber als **eine Liste/Matrix User → Felder** oder mit Klick „Bearbeiten“ pro Zeile wie bei User & Rollen.
- **Urlaubsverwaltung:**  
  Ansprüche pro Jahr/MA, Urlaubssperren, ggf. Genehmiger-Regeln (falls weiter als Gruppe/Standort → Genehmiger gepflegt), Link zur Chef-Übersicht. Entspricht der bisherigen „Urlaubsplaner Admin“-Seite.

**Admin-Menü danach:**
- **Mitarbeiterverwaltung** → entfällt (Inhalt in Rechteverwaltung).
- **Organigramm** → entfällt (Mitarbeiter-Konfig in Rechteverwaltung).
- **Urlaubsplaner Admin** → entfällt (Urlaubsverwaltung in Rechteverwaltung).
- **Rechteverwaltung** bleibt der **einzige** Einstieg für: Rollen, Mitarbeiter-Struktur/Genehmiger/Vertretung, Urlaub (Ansprüche, Sperren).

**Vorteile:** Ein Ort für alle personal- und berechtigungsrelevanten Einstellungen; gleiche UX (Tabs, Tabelle, Bearbeiten pro Zeile); keine verstreuten Admin-Punkte mehr.

**Optional:** Rechteverwaltung umbenennen in z. B. **„Rechte & Personal“** oder **„Personal & Zugriff“**, damit klar ist, dass hier nicht nur Rollen, sondern auch Struktur und Urlaub konfiguriert werden.
