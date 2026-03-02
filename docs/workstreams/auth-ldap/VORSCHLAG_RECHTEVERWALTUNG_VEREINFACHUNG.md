# Rechteverwaltung – Verbesserungsvorschlag (Redundanz & Administrierbarkeit)

**Stand:** 2026-02-27  
**Auslöser:** Redundanz zwischen Rollen-Features, Matrix, Nach Feature, Navigation; Bug (OPOS-Deaktivierung für Rolle „verkauf“ blieb nach Speichern nicht erhalten).

---

## 1. Aktueller Zustand (Kritik)

### Tabs und Redundanz

| Tab | Inhalt | Redundanz / Problem |
|-----|--------|----------------------|
| **User & Rollen** | Portal-Rolle pro User zuweisen | ✅ Kern, klar |
| **Rollen-Features** | Rolle wählen (Buttons) → Features an/ab → Speichern | Bearbeitung **nach Rolle** |
| **Matrix** | Tabelle Feature × Rolle (nur Lesen) | **Gleiche Daten** wie Rollen-Features, nur Ansicht |
| **Nach Feature** | Feature wählen → Rollen an/ab → Speichern | **Gleiche Daten**, Bearbeitung **nach Feature** |
| **Navigation** | Menüpunkte, requires_feature, Sichtbarkeit | Nutzt Feature-Zugriff, aber **eigener Bereich** (Menüstruktur) |

**Kernproblem:** Ein und dieselbe fachliche Information („Welche Rolle hat welches Feature?“) wird an **drei Stellen** angeboten:

- **Rollen-Features** = Bearbeiten nach Rolle (Rolle → Liste Features)
- **Nach Feature** = Bearbeiten nach Feature (Feature → Liste Rollen)
- **Matrix** = nur lesen (Feature × Rolle)

Das ist für Admins verwirrend („Wo ändere ich was?“) und fehleranfällig (z. B. unterschiedliche Speicher-Pfade, Cache-Probleme über mehrere Worker).

### Bug (behoben)

- **Symptom:** Unter Rollen-Features OPOS für Rolle „verkauf“ deaktivieren → Speichern → Erfolg → Nach Aktualisierung wieder aktiv.
- **Ursache:** `get_feature_access_from_db()` nutzte einen **pro Gunicorn-Worker In-Memory-Cache** (5 Min). Speicher-Request lief auf Worker A (Cache geleert), Reload auf Worker B (alter Cache) → alte Daten.
- **Fix:** Cache für Feature-Zugriff deaktiviert (`CACHE_TTL = timedelta(0)`), damit alle Worker sofort aus der DB lesen. Siehe `config/roles_config.py`.

---

## 2. Verbesserungsvorschlag

### Ziel

- **Eine** klare Stelle zum Pflegen von **Rolle ↔ Feature**.
- Keine doppelte Bearbeitung derselben Daten (entweder nur „nach Rolle“ oder nur „nach Feature“, oder eine Oberfläche mit klar getrennten Modi).
- Matrix nur noch als **Lesende Übersicht**, kein zweiter Speicher-Pfad.
- Navigation bleibt thematisch getrennt (Menüstruktur), aber Verweis auf die eine Stelle für Feature-Rechte.

### Option A: Eine Bearbeitungsansicht (empfohlen)

- **Ein Tab „Feature-Zugriff“** mit:
  - **Primär:** „Nach Rolle“ – Rollen-Buttons + Checkboxen pro Rolle (wie bisher Rollen-Features), ein **einziger** Speicher-Button.
  - **Optional:** Umschalter „Nach Rolle“ / „Nach Feature“ (gleiche Daten, andere Sortierung); Speichern immer über **dieselbe** Logik (z. B. immer „aktuelle Rolle“ oder „aktuelles Feature“ konsistent zurück in die DB schreiben).
- **Matrix** entweder:
  - als **Unterbereich** in demselben Tab (z. B. ausklappbare „Übersicht Feature × Rolle“), oder
  - als eigener **nur-Lesen** Tab mit Hinweis: „Zum Ändern: Tab Feature-Zugriff“.
- **Tab „Nach Feature“** in der heutigen Form **entfernen** (Funktion in „Feature-Zugriff“ integrieren, wenn gewünscht, über Umschalter).

Vorteil: Ein Speicher-Pfad, eine Quelle der Wahrheit, weniger Verwechslung und Cache-Probleme.

### Option B: Zwei Bearbeitungsansichten beibehalten, aber vereinheitlichen

- **Rollen-Features** und **Nach Feature** bleiben getrennt, aber:
  - Beide nutzen **dieselbe** API und **keinen** pro-Worker-Cache (erledigt).
  - Deutlicher Hinweis im UI: „Rollen-Features und Nach Feature ändern dieselben Einstellungen – nur die Sicht ist anders.“
  - **Matrix** als reine Übersicht mit Text: „Zum Bearbeiten: Rollen-Features oder Nach Feature.“

### Navigation

- Tab **Navigation** beibehalten für Menüpunkte, Reihenfolge, `requires_feature`-Zuweisung.
- Kurzer Hinweis im Tab: „Feature-Zugriff wird unter [Feature-Zugriff / Rollen-Features] gepflegt; hier nur das Menü und die Zuordnung Feature pro Menüpunkt.“

### Weitere Tabs

- **User & Rollen**, **Mitarbeiter-Konfig**, **Urlaubsverwaltung**, **Mitarbeiterverwaltung**, **E-Mail Reports**, **Title-Mapping**, **Architektur** unverändert sinnvoll; keine Reduktion nötig.

---

## 3. Kurzempfehlung

1. **Bug:** Cache für Feature-Zugriff deaktiviert (erledigt).
2. **Reduktion:** Ein Tab „Feature-Zugriff“ mit primär „Nach Rolle“-Bearbeitung; Matrix nur Lesen (evtl. eingebettet); Tab „Nach Feature“ entfernen oder als alternative Sicht in denselben Tab integrieren (Option A).
3. **Klarheit:** Ein Speicher-Button pro Kontext, ein Hinweis bei Navigation auf die eine Stelle für Feature-Rechte.

---

## 4. Technik (bereits umgesetzt)

- **Cache:** `config/roles_config.py` – `CACHE_TTL = timedelta(0)`, Abfrage in `get_feature_access_from_db()` liest immer aus der DB.
- **Speicher-Pfad Rollen-Features:** Bereits zuvor korrigiert (richtiger Checkbox-Container je Kontext: Rollen-Features-Tab vs. Feature-Zugriff-Dropdown).
