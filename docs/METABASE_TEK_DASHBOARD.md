# TEK Dashboard in Metabase - Manuell zusammenstellen

## ✅ Status

**Queries erstellt:**
- ✅ TEK Gesamt - Monat kumuliert (ID: 42)
- ✅ TEK nach Standort (ID: 43)
- ✅ TEK Verlauf (ID: 44)
- ✅ TEK Drill-Down NW/GW (ID: 45)

**Dashboard erstellt:**
- ✅ TEK Dashboard (ID: 3)
- URL: http://10.80.80.20:3001/dashboard/3

## Manuell Cards hinzufügen

Da die API-Methode zum automatischen Hinzufügen nicht funktioniert, füge die Queries manuell hinzu:

### Schritt-für-Schritt:

1. **Öffne Dashboard:** http://10.80.80.20:3001/dashboard/3
2. **Klicke auf "Bearbeiten"** (Edit) oben rechts
3. **Klicke auf "+"** (Add a question)
4. **Wähle eine der erstellten Queries:**
   - "TEK Gesamt - Monat kumuliert"
   - "TEK nach Standort"
   - "TEK Verlauf"
   - "TEK Drill-Down NW/GW"
5. **Wiederhole für alle 4 Queries**
6. **Speichere Dashboard**

## Alternative: Queries direkt verwenden

Du kannst die Queries auch direkt verwenden:

1. **Öffne Metabase:** http://10.80.80.20:3001
2. **Klicke auf "Unsere Analysen"** oder "Deine persönliche Sammlung"
3. **Die 4 TEK-Queries sollten sichtbar sein**
4. **Klicke auf eine Query** um sie auszuführen

## Query-IDs

- Query 1 (TEK Gesamt): ID 42
- Query 2 (TEK Standort): ID 43
- Query 3 (TEK Verlauf): ID 44
- Query 4 (TEK Drill-Down): ID 45

## Nächste Schritte

1. ✅ Queries sind erstellt und funktionsfähig
2. ⏳ Dashboard manuell zusammenstellen (siehe oben)
3. ⏳ Visualisierungen anpassen (Chart-Typen, Farben, etc.)
4. ⏳ Filter hinzufügen (Standort, Zeitraum, etc.)

## Queries testen

Jede Query kann einzeln getestet werden:
- Öffne die Query in Metabase
- Klicke auf "Abfrage ausführen"
- Prüfe die Ergebnisse
- Passe Visualisierung an (Tabelle, Bar Chart, Line Chart, etc.)
