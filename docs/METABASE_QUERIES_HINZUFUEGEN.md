# Metabase: Queries zu Dashboards hinzufügen

**Status:** ✅ Queries erstellt, müssen manuell zu Dashboards hinzugefügt werden

## Warum manuell?

Die Metabase API für Dashboard-Cards ist nicht zuverlässig. Die manuelle Methode ist einfacher und funktioniert immer.

## Anleitung: Queries zu Dashboards hinzufügen

### BWA Dashboard (ID: 8)

1. **Öffne Metabase:** http://10.80.80.20:3001
2. **Gehe zu:** Dashboards → **BWA Dashboard**
3. **Klicke auf:** **Bearbeiten** (Stift-Icon oben rechts)
4. **Füge Queries hinzu:**
   - Klicke auf **"+"** (oben links)
   - Wähle **"Add a question"**
   - Suche nach den folgenden Queries:
     - **"BWA Monatswerte"** (ID: 49)
     - **"BWA Verlauf"** (ID: 50)
     - **"BWA Vergleich Vorjahr"** (ID: 51)
   - Klicke auf jede Query, um sie hinzuzufügen

5. **Anordnung anpassen:**
   - Ziehe die Queries per Drag & Drop
   - Empfohlene Anordnung:
     - **BWA Monatswerte** (oben links, 6 Spalten breit)
     - **BWA Verlauf** (oben rechts, 6 Spalten breit)
     - **BWA Vergleich Vorjahr** (unten, 12 Spalten breit)

6. **Visualisierungen anpassen:**
   - **BWA Monatswerte:** Als Tabelle belassen
   - **BWA Verlauf:** Als Liniendiagramm (bereits konfiguriert)
   - **BWA Vergleich Vorjahr:** Als Tabelle oder Balkendiagramm

7. **Speichern:** Klicke auf **"Speichern"** (oben rechts)

### TEK Dashboard (ID: 3)

1. **Öffne Metabase:** http://10.80.80.20:3001
2. **Gehe zu:** Dashboards → **TEK Dashboard**
3. **Klicke auf:** **Bearbeiten** (Stift-Icon oben rechts)
4. **Füge Queries hinzu:**
   - Klicke auf **"+"** (oben links)
   - Wähle **"Add a question"**
   - Suche nach den folgenden Queries:
     - **"TEK Gesamt - Monat kumuliert"** (ID: 42)
     - **"TEK nach Standort"** (ID: 43)
     - **"TEK Verlauf"** (ID: 44)
   - Klicke auf jede Query, um sie hinzuzufügen

5. **Anordnung anpassen:**
   - Ziehe die Queries per Drag & Drop
   - Empfohlene Anordnung:
     - **TEK Gesamt** (oben links, 6 Spalten breit)
     - **TEK nach Standort** (oben rechts, 6 Spalten breit)
     - **TEK Verlauf** (unten, 12 Spalten breit)

6. **Visualisierungen anpassen:**
   - **TEK Gesamt:** Als Tabelle belassen
   - **TEK nach Standort:** Als Tabelle oder Pivot-Tabelle
   - **TEK Verlauf:** Als Liniendiagramm (bereits konfiguriert)

7. **Speichern:** Klicke auf **"Speichern"** (oben rechts)

## Query-IDs zur Referenz

### TEK Dashboard
- **ID 42:** TEK Gesamt - Monat kumuliert
- **ID 43:** TEK nach Standort
- **ID 44:** TEK Verlauf

### BWA Dashboard
- **ID 49:** BWA Monatswerte
- **ID 50:** BWA Verlauf
- **ID 51:** BWA Vergleich Vorjahr

## Tipps

1. **Query-Suche:** In Metabase kannst du nach Query-Namen suchen
2. **Größe anpassen:** Klicke auf eine Query im Dashboard → Ziehe die Ecken zum Vergrößern/Verkleinern
3. **Filter hinzufügen:** Später können Filter-Widgets hinzugefügt werden (z.B. Monat/Jahr)

## Nächste Schritte

Nachdem die Queries hinzugefügt sind:
1. ✅ Dashboards testen
2. ✅ Visualisierungen optimieren
3. ✅ Filter hinzufügen (optional)
4. ✅ Embedding in DRIVE vorbereiten
