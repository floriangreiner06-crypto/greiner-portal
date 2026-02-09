# Metabase Dashboards - TEK und BWA

**Erstellt:** TAG 215  
**Status:** ✅ Queries erstellt, Dashboards vorbereitet

## Übersicht

Beide Dashboards wurden basierend auf der DRIVE Portal Struktur erstellt:

### TEK Dashboard (ID: 3)
**URL:** http://10.80.80.20:3001/dashboard/3

**Queries:**
- **ID 42:** TEK Gesamt - Monat kumuliert (Tabelle)
  - Zeigt alle Bereiche (NW, GW, Teile, Werkstatt, Sonstige)
  - Spalten: Bereich, Erlös, Einsatz, DB1 (€), DB1 (%)
  
- **ID 43:** TEK nach Standort (Tabelle)
  - Aufschlüsselung nach Standort (Deggendorf Opel, Landau, Deggendorf Hyundai)
  - Spalten: Standort, Bereich, Erlös, Einsatz, DB1 (€), DB1 (%)
  
- **ID 44:** TEK Verlauf (Liniendiagramm)
  - Verlauf der letzten 12 Monate
  - Spalten: Monat, Erlös, Einsatz, DB1 (€), DB1 (%)

### BWA Dashboard (ID: 8)
**URL:** http://10.80.80.20:3001/dashboard/8

**Queries:**
- **ID 49:** BWA Monatswerte (Tabelle)
  - Alle BWA-Positionen für aktuellen Monat
  - Spalten: Position, Betrag (€)
  - Positionen: Umsatzerlöse, Einsatzwerte, DB1, Variable Kosten, DB2, Direkte Kosten, DB3, Indirekte Kosten, Betriebsergebnis, Neutrale Erträge, Unternehmensergebnis
  
- **ID 50:** BWA Verlauf (Liniendiagramm)
  - Verlauf der letzten 12 Monate
  - Spalten: Monat, Umsatz, Einsatz, DB1, DB2, DB3, Betriebsergebnis, Unternehmensergebnis
  
- **ID 51:** BWA Vergleich Vorjahr (Tabelle)
  - Vergleich: Aktuell vs. Vorjahresmonat
  - Spalten: Position, Aktuell (€), Vorjahr (€), Differenz (€), Änderung (%)

## Nächste Schritte

### 1. Queries zu Dashboards hinzufügen (manuell)

1. Öffne Metabase: http://10.80.80.20:3001
2. Gehe zu **Dashboards** → **TEK Dashboard** (ID: 3)
3. Klicke auf **Bearbeiten** (Stift-Icon)
4. Klicke auf **+** → **Add a question**
5. Wähle die Queries aus:
   - TEK Gesamt - Monat kumuliert (ID: 42)
   - TEK nach Standort (ID: 43)
   - TEK Verlauf (ID: 44)
6. Wiederhole für **BWA Dashboard** (ID: 8) mit Queries 49, 50, 51

### 2. Visualisierungen anpassen

- **TEK Gesamt:** Als Tabelle belassen
- **TEK nach Standort:** Als Tabelle oder Pivot-Tabelle
- **TEK Verlauf:** Als Liniendiagramm (bereits konfiguriert)
- **BWA Monatswerte:** Als Tabelle belassen
- **BWA Verlauf:** Als Liniendiagramm (bereits konfiguriert)
- **BWA Vergleich Vorjahr:** Als Tabelle oder Balkendiagramm

### 3. Filter hinzufügen (optional)

- **Monat/Jahr Filter:** Für alle Queries
- **Standort Filter:** Für TEK nach Standort
- **Bereich Filter:** Für TEK Gesamt

### 4. Embedding in DRIVE Portal

**WICHTIG:** Erst nachdem Dashboards sauber konfiguriert sind!

**Option A: Public Embedding (einfach)**
1. Dashboard → **Sharing** → **Embed this dashboard**
2. Token generieren
3. Iframe in DRIVE Portal einbetten:
   ```html
   <iframe src="http://10.80.80.20:3001/embed/dashboard/TOKEN" 
           width="100%" height="800px" frameborder="0"></iframe>
   ```

**Option B: Embedded Analytics (erweitert)**
- Benötigt Metabase Pro/Enterprise
- SSO-Integration möglich
- Erweiterte Berechtigungen

## Technische Details

### Datenquelle
- **Datenbank:** `drive_portal` (PostgreSQL)
- **Tabelle:** `loco_journal_accountings`
- **Filter:** G&V-Abschlussbuchungen werden ausgeschlossen (`document_number LIKE 'GV%'`)

### SQL-Struktur
- Alle Queries verwenden **Native SQL**
- **CTEs (Common Table Expressions)** für komplexe Berechnungen
- **PostgreSQL-spezifische Funktionen:** `DATE_TRUNC`, `EXTRACT`, `TO_CHAR`

### Validierung
- ✅ Alle Queries wurden **lokal getestet** vor Erstellung
- ✅ Daten entsprechen **DRIVE Portal** Struktur
- ✅ G&V-Filter korrekt implementiert

## Bekannte Einschränkungen

1. **Automatisches Hinzufügen zu Dashboards:** Metabase API unterstützt das nicht zuverlässig
   - **Lösung:** Manuell über UI hinzufügen

2. **Filter-Parameter:** Noch nicht implementiert
   - **Lösung:** Über Metabase UI hinzufügen (Filter-Widgets)

3. **Embedding:** Noch nicht konfiguriert
   - **Grund:** Warten auf saubere Metabase-Konfiguration
   - **Nächster Schritt:** Nach manueller Dashboard-Konfiguration

## Support

Bei Fragen oder Problemen:
1. Prüfe Metabase-Logs: `journalctl -u metabase -f`
2. Teste Queries lokal: `psql -h localhost -U drive_user -d drive_portal`
3. Prüfe Metabase-Status: `systemctl status metabase`
