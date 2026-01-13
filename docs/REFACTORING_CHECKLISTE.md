# 🔄 Refactoring-Checkliste

**Zweck:** Sicherstellen, dass beim Refactoring keine Features verloren gehen

**Erstellt:** TAG 184 (13.01.2026)  
**Anlass:** Positionen-Extraktion ging bei API-Scraper-Refactoring verloren

---

## 📋 Checkliste vor Refactoring

### 1. Bestandsaufnahme (MUSS)

- [ ] **Alle Features dokumentieren**
  - [ ] Welche Funktionen hat der alte Code?
  - [ ] Welche Daten werden extrahiert/verarbeitet?
  - [ ] Welche Edge-Cases werden behandelt?
  - [ ] Welche Fehlerbehandlungen gibt es?

- [ ] **Code-Analyse**
  - [ ] Alle Funktionen auflisten
  - [ ] Alle Datenfelder identifizieren
  - [ ] Alle Abhängigkeiten prüfen
  - [ ] Alle Tests/Validierungen finden

- [ ] **Dokumentation prüfen**
  - [ ] Session-Wrap-Ups lesen
  - [ ] TODO-Dateien prüfen
  - [ ] Kommentare im Code lesen
  - [ ] Git-Historie prüfen (warum wurde Code so geschrieben?)

---

## 📋 Checkliste während Refactoring

### 2. Feature-Portierung (MUSS)

- [ ] **Jede Funktion portieren**
  - [ ] Funktion 1: ✅ Portiert
  - [ ] Funktion 2: ✅ Portiert
  - [ ] Funktion 3: ✅ Portiert
  - [ ] ... (für jede Funktion)

- [ ] **Daten-Extraktion portieren**
  - [ ] Feld 1: ✅ Portiert
  - [ ] Feld 2: ✅ Portiert
  - [ ] Feld 3: ✅ Portiert
  - [ ] ... (für jedes Datenfeld)

- [ ] **Edge-Cases portieren**
  - [ ] Edge-Case 1: ✅ Portiert
  - [ ] Edge-Case 2: ✅ Portiert
  - [ ] ... (für jeden Edge-Case)

- [ ] **Fehlerbehandlung portieren**
  - [ ] Try-Catch-Blöcke: ✅ Portiert
  - [ ] Validierungen: ✅ Portiert
  - [ ] Fallbacks: ✅ Portiert

- [ ] **Keine TODO-Kommentare**
  - [ ] ❌ Keine "TODO: Später implementieren"
  - [ ] ❌ Keine "TODO: Kann erweitert werden"
  - [ ] ✅ Alles vollständig implementiert ODER explizit dokumentiert

---

## 📋 Checkliste nach Refactoring

### 3. Vergleich & Validierung (MUSS)

- [ ] **Funktionaler Vergleich**
  - [ ] Alte vs. neue Ausgabe vergleichen
  - [ ] Alle Datenfelder prüfen
  - [ ] Edge-Cases testen
  - [ ] Fehlerbehandlung testen

- [ ] **Daten-Validierung**
  - [ ] Alte JSON vs. neue JSON vergleichen
  - [ ] Alle Felder vorhanden?
  - [ ] Alle Werte korrekt?
  - [ ] Keine Daten verloren?

- [ ] **Integrationstest**
  - [ ] Mit echten Daten testen
  - [ ] Alle Workflows testen
  - [ ] End-to-End testen
  - [ ] Performance prüfen

- [ ] **Code-Review**
  - [ ] Alle Funktionen vorhanden?
  - [ ] Keine TODO-Kommentare?
  - [ ] Code-Qualität OK?
  - [ ] Dokumentation aktualisiert?

---

## 📋 Spezielle Checklisten

### 4. Scraper-Refactoring

- [ ] **Daten-Extraktion**
  - [ ] Alle HTML-Elemente extrahiert?
  - [ ] Alle Tabellen geparst?
  - [ ] Alle Positionen erfasst?
  - [ ] Alle Metadaten vorhanden?

- [ ] **Parsing-Logik**
  - [ ] Regex-Patterns portiert?
  - [ ] BeautifulSoup-Logik portiert?
  - [ ] Selenium-Logik portiert (falls relevant)?
  - [ ] Edge-Cases (leere Felder, Sonderzeichen) behandelt?

- [ ] **Output-Format**
  - [ ] JSON-Struktur identisch?
  - [ ] Alle Felder vorhanden?
  - [ ] Datentypen korrekt?
  - [ ] Encoding korrekt (UTF-8)?

---

### 5. API-Refactoring

- [ ] **Endpoints**
  - [ ] Alle Endpoints vorhanden?
  - [ ] Alle Parameter unterstützt?
  - [ ] Response-Format identisch?
  - [ ] Error-Handling identisch?

- [ ] **Datenbank-Zugriffe**
  - [ ] Alle Queries portiert?
  - [ ] SQL-Syntax korrekt (PostgreSQL vs. SQLite)?
  - [ ] Transaktionen korrekt?
  - [ ] Rollback-Logik vorhanden?

---

### 6. Frontend-Refactoring

- [ ] **UI-Elemente**
  - [ ] Alle Buttons vorhanden?
  - [ ] Alle Modals funktionieren?
  - [ ] Alle Links funktionieren?
  - [ ] Alle Formulare funktionieren?

- [ ] **JavaScript**
  - [ ] Alle Funktionen portiert?
  - [ ] Event-Handler vorhanden?
  - [ ] AJAX-Calls korrekt?
  - [ ] Error-Handling vorhanden?

---

## 📋 Migration-Checkliste

### 7. Datenbank-Migration

- [ ] **Schema-Migration**
  - [ ] Alle Tabellen migriert?
  - [ ] Alle Spalten vorhanden?
  - [ ] Indizes vorhanden?
  - [ ] Constraints vorhanden?

- [ ] **Daten-Migration**
  - [ ] Alle Daten migriert?
  - [ ] Daten-Integrität geprüft?
  - [ ] Keine Daten verloren?
  - [ ] Rollback möglich?

---

## 📋 Deployment-Checkliste

### 8. Vor Deployment

- [ ] **Code-Qualität**
  - [ ] Linter-Fehler behoben?
  - [ ] Tests bestanden?
  - [ ] Code-Review durchgeführt?

- [ ] **Dokumentation**
  - [ ] README aktualisiert?
  - [ ] Session-Wrap-Up erstellt?
  - [ ] Breaking Changes dokumentiert?
  - [ ] Migration-Guide erstellt (falls nötig)?

- [ ] **Backup**
  - [ ] Datenbank-Backup erstellt?
  - [ ] Alte Version gesichert?
  - [ ] Rollback-Plan vorhanden?

---

## 📋 Nach Deployment

### 9. Monitoring & Validierung

- [ ] **Logs prüfen**
  - [ ] Keine Fehler in Logs?
  - [ ] Alle Tasks laufen?
  - [ ] Performance OK?

- [ ] **Funktionalität prüfen**
  - [ ] Alle Features funktionieren?
  - [ ] Daten korrekt?
  - [ ] UI funktioniert?
  - [ ] API funktioniert?

- [ ] **User-Feedback**
  - [ ] User testen lassen?
  - [ ] Feedback eingeholt?
  - [ ] Probleme behoben?

---

## 🎯 Best Practices

### DO's ✅

1. **Vollständige Portierung**
   - Immer alle Features portieren
   - Nie "später" denken
   - Immer vollständig implementieren

2. **Vergleich & Validierung**
   - Alte vs. neue Ausgabe vergleichen
   - Mit echten Daten testen
   - Edge-Cases testen

3. **Dokumentation**
   - Jede Änderung dokumentieren
   - Breaking Changes dokumentieren
   - Migration-Guide erstellen

4. **Schrittweise Migration**
   - Nicht alles auf einmal
   - Schritt für Schritt
   - Jeden Schritt testen

### DON'Ts ❌

1. **Keine TODO-Kommentare**
   - Nie "TODO: Später implementieren"
   - Nie "TODO: Kann erweitert werden"
   - Immer vollständig implementieren

2. **Keine Annahmen**
   - Nie annehmen, dass Code "einfach" ist
   - Nie annehmen, dass Features "nicht wichtig" sind
   - Immer prüfen und testen

3. **Keine halben Sachen**
   - Nie nur "Haupt-Features" portieren
   - Nie "Edge-Cases später" denken
   - Immer vollständig portieren

---

## 📝 Template für Refactoring-Session

### Vor Refactoring

```markdown
## Refactoring: [Name]

**Datum:** [Datum]
**Alter Code:** [Pfad]
**Neuer Code:** [Pfad]
**Grund:** [Warum refactoring?]

### Bestandsaufnahme

#### Funktionen im alten Code:
- [ ] Funktion 1: [Beschreibung]
- [ ] Funktion 2: [Beschreibung]
- [ ] ...

#### Datenfelder im alten Code:
- [ ] Feld 1: [Typ, Beschreibung]
- [ ] Feld 2: [Typ, Beschreibung]
- [ ] ...

#### Edge-Cases im alten Code:
- [ ] Edge-Case 1: [Beschreibung]
- [ ] Edge-Case 2: [Beschreibung]
- [ ] ...
```

### Während Refactoring

```markdown
## Portierungs-Status

### Funktionen:
- [x] Funktion 1: ✅ Portiert
- [x] Funktion 2: ✅ Portiert
- [ ] Funktion 3: ⏳ In Arbeit
- [ ] Funktion 4: ❌ Noch nicht portiert

### Datenfelder:
- [x] Feld 1: ✅ Portiert
- [x] Feld 2: ✅ Portiert
- [ ] Feld 3: ❌ Noch nicht portiert
```

### Nach Refactoring

```markdown
## Validierung

### Vergleich:
- [x] Alte vs. neue Ausgabe: ✅ Identisch
- [x] Alle Datenfelder: ✅ Vorhanden
- [x] Edge-Cases: ✅ Getestet

### Tests:
- [x] Unit-Tests: ✅ Bestanden
- [x] Integration-Tests: ✅ Bestanden
- [x] E2E-Tests: ✅ Bestanden
```

---

## 🔗 Referenzen

- **TAG 173:** ServiceBox API-Scraper Refactoring (Positionen-Extraktion ging verloren)
- **TAG 184:** Positionen-Extraktion wiederhergestellt

---

## 💡 Lessons Learned

1. **Nie TODO-Kommentare bei Refactoring**
   - Immer vollständig portieren
   - Oder explizit dokumentieren, warum nicht

2. **Immer Vergleich & Validierung**
   - Alte vs. neue Ausgabe vergleichen
   - Mit echten Daten testen

3. **Schrittweise Migration**
   - Nicht alles auf einmal
   - Jeden Schritt testen

4. **Dokumentation ist wichtig**
   - Jede Änderung dokumentieren
   - Breaking Changes dokumentieren

---

**Letzte Aktualisierung:** TAG 184 (13.01.2026)
