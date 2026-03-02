# Rechteverwaltung – Kontext & Vorschlag Entschlackung

**Stand:** 2026-03-02  
**Anlass:** Rechteverwaltung wurde kürzlich überarbeitet, wirkt aber weiterhin zu komplex. Vorschlag zur Vereinfachung – **ohne Code**, nur Konzept.

---

## 1. Kontext: Was wurde schon gemacht (Überarbeitung 2026-02)

- **Option B (Rechte nur aus Portal):** Zugriff kommt nur noch aus der Rechteverwaltung. LDAP liefert nur Identität. Pro User **eine Portal-Rolle** (Dropdown „Rolle zuweisen“).
- **Ein Tab „Feature-Zugriff“** ersetzt die drei Tabs „Rollen-Features“, „Matrix“, „Nach Feature“. Darin: Pills „Nach Rolle“, „Nach Feature“, „Matrix (Übersicht)“ – ein Speicher-Pfad, eine Quelle der Wahrheit.
- **Cache-Bug behoben:** Feature-Zugriff wird nicht mehr pro Worker gecacht; Speichern wirkt sofort.
- **Navigation:** Nur berechtigte Menüpunkte; Startseite nur nach Rolle; Filter-Verhalten (nur eigene / alle) pro Feature konfigurierbar.
- **Wirksame Rolle:** admin (user_roles) **oder** portal_role_override (Rechteverwaltung) **oder** Default „mitarbeiter“.

Trotzdem: Viele Tabs, viele Konzepte (Rolle, Feature, Filter-Modus, Navigation, Title-Mapping, Mitarbeiter-Konfig, Urlaub, …) an einem Ort – für Admins weiterhin schwer zu überblicken.

---

## 2. Was heute noch komplex wirkt

| Thema | Aktuell | Warum anstrengend |
|-------|---------|--------------------|
| **Viele Tabs** | User & Rollen, Feature-Zugriff, Architektur, E-Mail Reports, Title-Mapping, Navigation, Mitarbeiter-Konfig, Urlaubsverwaltung, Mitarbeiterverwaltung | Unklar, wohin man für welche Aufgabe muss; „Rechte“ vermischt mit Organigramm, Urlaub, Reports. |
| **Feature-Zugriff: drei Sichten** | Nach Rolle (Buttons + Checkboxen), Nach Feature (Dropdown + Karten), Matrix (read-only) | Dieselben Daten, drei Wege – „Wo ändere ich was?“ bleibt Frage. |
| **Zwei Ebenen** | (1) User → Rolle zuweisen. (2) Rolle → Features zuweisen. | Logisch, aber getrennt in zwei Tabs; Zusammenhang nicht auf einen Blick. |
| **Filter-Verhalten** | Eigene Karte „Filter-Verhalten für Listen“ (Auftragseingang, Auslieferungen, OPOS, …) pro Rolle | Noch eine Dimension: nicht nur „darf sehen“, sondern „nur eigene / alle / filterbar“. Erhöht kognitive Last. |
| **Navigation-Tab** | Menüpunkte, requires_feature, Struktur | Nur für Menü-Struktur nötig; Feature-Zugriff wird woanders gepflegt – Verweis nötig. |
| **Title-Mapping** | LDAP-Titel → Portal-Rolle (Fallback, wenn kein Override) | Für Option B eher Randthema; wirkt technisch. |
| **Begriffe** | Portal-Rolle, Feature, requires_feature, Filter-Modus, Quelle (Default/Override) | Viele Fachbegriffe in einem Screen. |

---

## 3. Vorschlag: Entschlackung (ohne Code-Änderung hier)

### 3.1 Oberziel

- **Eine klare Hauptaufgabe pro Bereich:** „Wer sieht was?“ getrennt von „Struktur/Urlaub/Reports“.
- **Weniger Klicks und weniger Tabs** für die typischen Aufgaben: Rolle zuweisen, Features für eine Rolle anpassen.
- **Matrix/Nach Feature** nur noch als Hilfsansicht, nicht als gleichberechtigte Bearbeitungswege.

### 3.2 Vorschlag A: Zwei „Bereiche“ statt neun Tabs

Statt einer langen Tab-Leiste zwei klar getrennte Bereiche (z. B. zwei Seiten oder ein Umschalter oben):

- **Bereich 1 – Rechte & Rollen**
  - **User & Rolle:** Liste User, pro User eine Rolle zuweisen (wie heute). Optional: Startseite, „Ohne Rolle“-Filter.
  - **Rollen & Module:** Eine einzige Bearbeitungsansicht: Rolle wählen (Dropdown oder Buttons) → Liste der Module/Features mit Checkboxen → ein Speicher-Button. Keine zweite Sicht „Nach Feature“, keine Matrix in der Hauptarbeit.
  - Optional: Link „Matrix-Übersicht (nur Lesen)“ für Power-User.

- **Bereich 2 – Struktur, Urlaub, Sonstiges**
  - Mitarbeiter-Konfig (Abteilung, Vertretung, Genehmiger, Locosoft-ID).
  - Urlaubsverwaltung (Ansprüche, Sperren).
  - Mitarbeiterverwaltung (falls weiter nötig).
  - E-Mail Reports, Architektur, Title-Mapping, Navigation: entweder hier als Unterpunkte oder in ein Admin-„Einstellungen“-Menü auslagern.

**Effekt:** Wer nur „Rolle zuweisen“ oder „Features für Verkauf anpassen“ will, bleibt in Bereich 1 und muss nicht durch viele Tabs.

### 3.3 Vorschlag B: Feature-Zugriff auf eine Sicht reduzieren

- **Nur noch „Nach Rolle“** als Bearbeitung: Rolle wählen → Checkboxen für Features → Speichern.
- **„Nach Feature“** entfernen (oder nur als read-only „Welche Rollen haben Feature X?“).
- **Matrix** nur noch als ausklappbare oder separate **Lesende Übersicht**, mit Hinweis: „Zum Ändern: oben Rolle wählen und Checkboxen setzen.“

**Effekt:** Ein klares mentales Modell: „Ich wähle eine Rolle und stelle die Häkchen.“ Kein zweiter Weg über „Feature wählen → Rollen setzen“.

### 3.4 Vorschlag C: Filter-Verhalten weich integrieren

- Filter-Verhalten („Nur eigene“ / „Eigene, filterbar“ / „Alle“) nicht als eigene große Karte, sondern **pro Modul** in der gleichen Rollen-Ansicht: Bei den bekannten Listen-Features (Auftragseingang, Auslieferungen, OPOS, Leistungsübersicht Werkstatt) ein **kleines Dropdown** neben dem Feature-Haken (oder nur für diese Features sichtbar).
- So bleibt „Rolle → Features“ eine Liste; die Filter-Option ist Zusatzinfo bei den betroffenen Zeilen, keine eigene Konzept-Ebene.

### 3.5 Vorschlag D: Weniger Tabs, klare Gruppierung

Falls die Oberfläche bei einer Seite bleibt:

- **Haupt-Tabs nur noch z. B. 3–4:**
  1. **User & Rollen** (User-Liste + Rollen-Zuweisung + **Rollen & Module** in einem Tab, z. B. oben User, unten „Features für gewählte Rolle“).
  2. **Mitarbeiter & Urlaub** (Mitarbeiter-Konfig, Urlaubsverwaltung, ggf. Mitarbeiterverwaltung).
  3. **Einstellungen** (Navigation, Title-Mapping, E-Mail Reports, Architektur – alles, was seltener gebraucht wird).

Damit sinkt die Zahl der sichtbaren Tabs; „Rechte“ = im Wesentlichen Tab 1.

---

## 4. Kurzempfehlung (Priorität)

1. **Sofort mental entlastend:** Feature-Zugriff **nur eine Bearbeitungsansicht** (Nach Rolle); Matrix nur Lesen (Vorschlag B).
2. **Struktur:** Rechte (User + Rollen + Features) von „Struktur/Urlaub/Sonstiges“ trennen – zwei Bereiche oder stark gruppierte Tabs (Vorschlag A oder D).
3. **Filter-Verhalten:** In die Rollen-/Feature-Liste integrieren statt eigene große Karte (Vorschlag C).
4. **Optional:** Selten genutzte Sachen (Navigation, Title-Mapping, Architektur, Reports) in einen gemeinsamen „Einstellungen“-Bereich (Vorschlag D).

---

## 5. Was unverändert bleiben kann (fachlich)

- **Eine Portal-Rolle pro User** (Dropdown in Rechteverwaltung).
- **DB als Quelle:** role_features, portal_role_override, feature_filter_mode – keine Änderung am Modell nötig.
- **Admin sieht alles;** Option B (Rechte nur aus Portal) bleibt.

Nur die **Darstellung und Anordnung** in der Rechteverwaltung werden vereinfacht; die Logik dahinter kann gleich bleiben.

---

## 6. Aufwand & Risiken (Coding)

### Aufwand (grobe Schätzung)

| Maßnahme | Aufwand | Betroffene Stellen |
|--------|--------|---------------------|
| **Vorschlag B:** Nur „Nach Rolle“ bearbeitbar, „Nach Feature“ entfernen oder read-only, Matrix nur Lesen | **gering (½–1 Tag)** | Eine Datei: `templates/admin/rechte_verwaltung.html` (~2550 Zeilen). Pills/Tab „Nach Feature“ ausblenden oder Inhalt read-only; `saveRoleFeatures()` nutzt bereits nur einen Speicher-Pfad, Logik bleibt. Matrix bleibt, nur Hinweis-Text ergänzen. |
| **Vorschlag C:** Filter-Verhalten in Rollen-Liste integrieren (Dropdown pro Listen-Feature) | **mittel (1–2 Tage)** | Template + ggf. kleines API-Tuning. Filter-Modus pro (Rolle, Feature) ist schon in DB/API; UI: statt eigener Karte Dropdowns in der Feature-Checkbox-Liste einbauen, gleiche API `feature-filter-mode` nutzen. |
| **Vorschlag D:** Tabs auf 3–4 reduzieren (User & Rollen inkl. Rollen & Module; Mitarbeiter & Urlaub; Einstellungen) | **mittel (1–2 Tage)** | Nur Template: Tab-Inhalte verschieben, Tab-Leiste umbauen, keine neuen Routen. Viel Copy/Paste und IDs/Event-Handler prüfen. |
| **Vorschlag A:** Zwei getrennte Bereiche/Seiten (Rechte vs. Struktur/Urlaub) | **höher (2–4 Tage)** | Entweder zweite Route + Template (z. B. `/admin/rechte` vs. `/admin/rechte-struktur`) oder eine Seite mit starkem UI-Umschalter. Mehr Strukturänderung, mehr Testfälle. |

**Gesamt für B + C + D (ohne A):** etwa **2–4 Tage** (eine Person, inkl. Test und Abnahme).  
**Mit Vorschlag A:** etwa **4–7 Tage**.

### Risiken

| Risiko | Wahrscheinlichkeit | Auswirkung | Mitigation |
|--------|--------------------|------------|------------|
| **Speicher-Bug wie 2026-02** (falscher Checkbox-Container ausgelesen) | niedrig | Nach „Speichern“ falsche Features gespeichert | Bereits behoben durch klaren Kontext (selectedRoleForFeatures / roleFeaturesGrouped). Bei Entfernung von „Nach Feature“ fällt eine Fehlerquelle weg; `saveRoleFeatures()` vereinfachen und nur noch grouped-Pfad nutzen. |
| **Regressions:** Bestehende Nutzer finden gewohnte Sicht nicht mehr | mittel | Verwirrung, Support-Anfragen | „Nach Feature“ nicht löschen, sondern als **nur Lesen** belassen mit Hinweis „Zum Ändern: Nach Rolle verwenden.“ So bleibt die Übersicht, keine zweite Bearbeitung. |
| **Tab-Umbau (D/A):** Event-Handler oder Daten nicht mehr angebunden | mittel | Buttons/Klicks tun nichts, Tab zeigt leere Daten | Systematisch durchklicken: User laden, Rolle zuweisen, Features speichern, Filter-Modus, Startseite, Navigation. Checkliste vor Go-live. |
| **Mobile/Responsive** | niedrig | Tabs/Bereiche auf kleinen Screens unübersichtlich | Rechteverwaltung ist typischerweise Admin am Desktop; bei Tab-Reduktion eher weniger Inhalte pro Tab, also tendenziell besser. |
| **Backend/API** | niedrig | Features oder Filter-Modus werden falsch gespeichert | Keine geplanten API-Änderungen; nur Frontend. Bestehende Endpoints (`/api/admin/role/<role>/features`, `feature-filter-mode`) weiterverwenden. |

### Empfehlung Reihenfolge

1. **Zuerst Vorschlag B** umsetzen (geringster Aufwand, sofort weniger Komplexität, kaum Risiko).
2. **Dann Vorschlag D** (Tabs zusammenfassen), danach optional **C** (Filter in Liste integrieren).
3. **Vorschlag A** (zwei Bereiche/Seiten) nur, wenn nach B/D die Akzeptanz gut ist und weiterer Wunsch nach Trennung besteht.
