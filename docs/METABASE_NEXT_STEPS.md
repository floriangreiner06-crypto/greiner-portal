# Metabase - Nächste Schritte

## ✅ Status
- Metabase installiert und erreichbar: http://10.80.80.20:3001
- Admin-Account erstellt: admin@auto-greiner.de

## Schritt 1: PostgreSQL-Datenbank verbinden

1. In Metabase: Klicke auf **"Daten"** → **"Datenbanken"** → **"Datenbank hinzufügen"**
2. Wähle **"PostgreSQL"**
3. Fülle die Verbindungsdaten aus:

```
Anzeigename: DRIVE Portal
Host: localhost
Port: 5432
Datenbankname: drive_portal
Benutzername: drive_user
Passwort: [aus DB-Konfiguration - bitte in .env oder db_connection.py prüfen]
```

4. Klicke auf **"Speichern"**

## Schritt 2: Erste Queries testen

Nach der Datenbankverbindung kannst du die Queries aus `docs/metabase_queries.sql` verwenden:

### TEK-Query testen:
1. Klicke auf **"Neu"** → **"Frage"** → **"Native query"**
2. Kopiere eine Query aus `docs/metabase_queries.sql`
3. Klicke auf **"Abfrage ausführen"**

### Beispiel: TEK Gesamt - Monat kumuliert
```sql
SELECT 
    b.name as "Bereich",
    COALESCE(SUM(cd.erloes), 0) as "Erlös (€)",
    COALESCE(SUM(cd.einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(cd.db1), 0) as "DB1 (€)",
    CASE 
        WHEN SUM(cd.erloes) > 0 
        THEN ROUND(SUM(cd.db1) / SUM(cd.erloes) * 100, 2)
        ELSE 0 
    END as "DB1 (%)",
    COALESCE(SUM(cd.stueck), 0) as "Menge (Stück)"
FROM (
    SELECT 
        bereich_id,
        standort_id,
        jahr,
        monat,
        SUM(erloes) as erloes,
        SUM(einsatz) as einsatz,
        SUM(db1) as db1,
        SUM(stueck) as stueck
    FROM controlling_data
    WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
      AND monat <= EXTRACT(MONTH FROM CURRENT_DATE)
    GROUP BY bereich_id, standort_id, jahr, monat
) cd
JOIN bereiche b ON cd.bereich_id = b.id
GROUP BY b.name, b.sort_order
ORDER BY b.sort_order;
```

## Schritt 3: Dashboards erstellen

### TEK Dashboard
1. Erstelle mehrere Questions (Queries) für:
   - TEK Gesamt
   - TEK nach Standort
   - TEK Verlauf
   - TEK Drill-Down NW/GW

2. Erstelle ein Dashboard: **"Neu"** → **"Dashboard"**
3. Name: **"TEK Dashboard"**
4. Füge alle TEK-Questions hinzu

### BWA Dashboard
1. Erstelle Questions für:
   - BWA Monatswerte
   - BWA Verlauf
   - BWA Umsatz nach Konten
   - BWA Variable Kosten
   - BWA Vergleich Vorjahr

2. Erstelle Dashboard: **"BWA Dashboard"**

## Schritt 4: Integration in DRIVE Portal

### Option 1: Link in Navigation
In `templates/base.html`:
```html
<li class="nav-item">
    <a class="nav-link" href="http://10.80.80.20:3001" target="_blank">
        <i class="fas fa-chart-line"></i> BI Dashboards
    </a>
</li>
```

### Option 2: Iframe-Einbindung
Neue Route in `routes/controlling_routes.py`:
```python
@controlling_bp.route('/bi/dashboards')
@login_required
def bi_dashboards():
    return render_template('controlling/bi_dashboards.html')
```

## Verfügbare Ressourcen

- **SQL-Queries:** `/opt/greiner-portal/docs/metabase_queries.sql`
- **Dokumentation:** `/opt/greiner-portal/docs/METABASE_*.md`
- **Rollback:** `/opt/greiner-portal/scripts/metabase_rollback.sh`

## Tipps

1. **Visualisierungen:** Experimentiere mit verschiedenen Chart-Typen (Bar, Line, Table, etc.)
2. **Filter:** Füge Filter für Standort, Zeitraum, etc. hinzu
3. **Sharing:** Dashboards können geteilt werden (öffentliche Links)
4. **Alerts:** Setze Alerts für Schwellwerte (z.B. DB1 < 0)
