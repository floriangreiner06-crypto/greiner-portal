# Einschätzung: Wieso nicht „am User“ bearbeiten?

**Stand:** 2026-03-02  
**Frage:** Wieso können wir nicht an User bearbeiten? Wieder zu viel Komplexität?

---

## Was wir heute „am User“ haben

| Aktion | Wo | Am User? |
|--------|-----|----------|
| **Rolle zuweisen** | User & Rollen, Dropdown/Stift pro Zeile | ✅ Ja – genau „am User“ |
| **Startseite setzen** | Haus-Icon pro User | ✅ Ja |
| **Admin-Rolle (user_roles)** | Rollen-Modal (admin an/ab) | ✅ Ja |

Was wir **nicht** am User haben: die **Feature-Liste** (welche Module dieser User sieht) und die **Navi** direkt pro User **bearbeiten**. Die Features hängen an der **Rolle**, nicht am User.

---

## Warum es so gebaut ist

- **Modell:** Ein User hat **eine** Portal-Rolle. Die Rolle hat eine **Feature-Liste** (in der DB: `role_features`). Was der User sieht = was seine Rolle hat.
- **Vorteil:** Einmal „Rolle Verkauf“ konfigurieren → alle Verkäufer haben dieselben Rechte. Kein 1:1-Pflegen pro Person.
- **Nachteil:** Will man „nur für Max Mustermann“ ein Feature mehr/weniger, geht das nicht ohne Extra-Konzept (Rolle ändern oder User-Override).

Also: Es ist nicht „wieder zu viel Komplexität“, sondern **bewusst rollenbasiert**. Bearbeitung „am User“ gibt es für **Rolle und Startseite**; die **Features** sind absichtlich **pro Rolle** definiert.

---

## Was „am User bearbeiten“ zusätzlich heißen könnte

### Variante A: Nur Kontext, keine neue Logik

- Beim User: Modal „Rechte & Navi“ mit **Anzeige** von Rolle, Features, Navi.
- **Bearbeitung** weiter wie heute: Rolle in der Tabelle ändern; Features unter „Rollen & Module“ für die **Rolle** ändern.
- **Komplexität:** Gering. Kein neues Datenmodell, nur eine Lesemaske „für diesen User“.

### Variante B: Features direkt am User (User-Overrides)

- Pro User speichern: „hat Feature X“ / „hat Feature X nicht“ als **Ausnahme** zur Rolle.
- Logik: Anzeige/Recht = Rolle-Features + User-Adds − User-Removals.
- **Vorteil:** „Max soll Verkauf sein, aber ohne OPOS“ ohne neue Rolle.
- **Komplexität:** Deutlich höher:
  - Neue Tabelle/Spalten (user_feature_override oder ähnlich),
  - Auth/Login muss Rolle + User-Overrides zusammenführen,
  - UI: pro User eine Feature-Liste (Häkchen) zusätzlich zur Rolle,
  - Klarheit: „Wo ist was definiert?“ – Rolle vs. User.

### Variante C: Komplett ohne Rollen (nur User-Features)

- Jeder User hat eine eigene Feature-Liste, keine Rolle mehr für Rechte.
- **Komplexität:** Hoch; Rollen-Konzept fällt weg oder wird nur noch Label. Bei vielen Usern: viel Redundanz oder „Rolle als Vorlage“ – dann wieder rollenbasiert.

---

## Kurze Einschätzung

- **„Wieso können wir nicht am User bearbeiten?“**  
  **Rolle** und **Startseite** bearbeiten wir schon am User. **Features** bewusst nicht – sie sind der Rolle zugeordnet, damit nicht jeder User einzeln durchkonfiguriert werden muss.

- **Ist das „wieder zu viel Komplexität?“**  
  Nein. Das aktuelle Modell ist **einfach**: eine Rolle pro User, Features pro Rolle. Zusätzliche **User-Feature-Overrides** (Variante B) wären der Komplexitätsgewinn – mehr Flexibilität, mehr Quellen der Wahrheit und mehr UI.

- **Sinnvoller nächster Schritt ohne Modell-Änderung:**  
  **Variante A:** Am User **nur anzeigen**, was er sieht (Rolle, Features, Navi) – z. B. Modal „Rechte & Navi“. Bearbeitung bleibt: Rolle in der Tabelle, Features unter „Rollen & Module“. Das beantwortet „Was hat dieser User?“ ohne neue Komplexität.

- **Falls ihr wirklich Einzelfall-Ausnahmen braucht** („dieser eine User soll Feature X nicht haben“): Dann wäre Variante B (User-Overrides) der passende, aber aufwendigere Schritt – mit klarer Entscheidung: wollen wir diese zweite Ebene (Rolle + User-Ausnahmen)?
