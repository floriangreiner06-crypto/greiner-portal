# Metabase Installation - Schritt für Schritt

## Voraussetzungen

- Server-Zugriff mit sudo-Rechten
- PostgreSQL läuft und ist erreichbar
- Port 3001 ist frei (Grafana nutzt Port 3000)

## Installation

### Schritt 1: Installation ausführen

```bash
cd /opt/greiner-portal
sudo bash scripts/install_metabase_jar.sh
```

Das Skript:
- Installiert Java (falls nicht vorhanden)
- Lädt Metabase JAR herunter
- Erstellt systemd Service
- Startet Metabase

### Schritt 2: Installation prüfen

```bash
# Status prüfen
sudo systemctl status metabase

# Logs anzeigen (warten bis "Metabase initialization complete")
sudo journalctl -u metabase -f
```

Warte ca. 30-60 Sekunden bis Metabase vollständig gestartet ist.

### Schritt 3: Ersten Admin-Account erstellen

1. Öffne im Browser: **http://10.80.80.20:3001** (Grafana läuft auf Port 3000)
2. Erstelle einen Admin-Account:
   - Name: z.B. "Admin"
   - E-Mail: z.B. "admin@auto-greiner.de"
   - Passwort: [sicheres Passwort]

### Schritt 4: Datenbank verbinden

1. Klicke auf **"Add your data"** → **"PostgreSQL"**
2. Fülle die Verbindungsdaten aus:

```
Display name: DRIVE Portal
Host: localhost
Port: 5432
Database name: drive_portal
Username: drive_user
Password: [aus DB-Konfiguration]
```

3. Klicke auf **"Save"**

### Schritt 5: Erste Query testen

1. Klicke auf **"New"** → **"Question"**
2. Wähle **"Native query"**
3. Kopiere diese Test-Query:

```sql
SELECT 
    COUNT(*) as anzahl_tabellen
FROM information_schema.tables
WHERE table_schema = 'public';
```

4. Klicke auf **"Run"** (sollte eine Zahl zurückgeben)

## Beispiel-Dashboards erstellen

### TEK Dashboard

1. **Neue Question erstellen:**
   - Name: "TEK Gesamt - Monat kumuliert"
   - Query aus `docs/metabase_queries.sql` kopieren (erste Query)
   - Visualisierung: **Table** oder **Bar Chart**

2. **Weitere Questions hinzufügen:**
   - "TEK nach Standort" (zweite Query)
   - "TEK Verlauf" (dritte Query)
   - "TEK Drill-Down NW/GW" (vierte Query)

3. **Dashboard erstellen:**
   - Klicke auf **"New"** → **"Dashboard"**
   - Name: "TEK Dashboard"
   - Füge alle Questions hinzu

### BWA Dashboard

1. **Questions erstellen:**
   - "BWA Monatswerte" (fünfte Query)
   - "BWA Verlauf" (sechste Query)
   - "BWA Umsatz nach Konten" (siebte Query)
   - "BWA Variable Kosten" (achte Query)
   - "BWA Vergleich Vorjahr" (neunte Query)

2. **Dashboard erstellen:**
   - Name: "BWA Dashboard"
   - Alle BWA-Questions hinzufügen

## Integration in DRIVE Portal

### Option 1: Link in Navigation

In `templates/base.html` oder entsprechender Nav-Datei:

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

Template `templates/controlling/bi_dashboards.html`:

```html
{% extends "base.html" %}
{% block content %}
<div class="container-fluid">
    <h1>Business Intelligence Dashboards</h1>
    <ul class="nav nav-tabs">
        <li class="nav-item">
            <a class="nav-link active" data-bs-toggle="tab" href="#tek">TEK</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-bs-toggle="tab" href="#bwa">BWA</a>
        </li>
    </ul>
    <div class="tab-content">
        <div id="tek" class="tab-pane active">
            <iframe 
                src="http://10.80.80.20:3001/public/dashboard/[TEK-DASHBOARD-ID]"
                width="100%" 
                height="800px"
                frameborder="0">
            </iframe>
        </div>
        <div id="bwa" class="tab-pane">
            <iframe 
                src="http://10.80.80.20:3001/public/dashboard/[BWA-DASHBOARD-ID]"
                width="100%" 
                height="800px"
                frameborder="0">
            </iframe>
        </div>
    </div>
</div>
{% endblock %}
```

## Troubleshooting

### Metabase startet nicht

```bash
# Prüfe Java
java -version

# Prüfe Port
sudo netstat -tlnp | grep 3001

# Prüfe Logs
sudo journalctl -u metabase -n 100
```

### Datenbankverbindung fehlgeschlagen

```bash
# Prüfe PostgreSQL
sudo systemctl status postgresql

# Teste Verbindung
PGPASSWORD=[PASSWORD] psql -h localhost -U drive_user -d drive_portal -c "SELECT 1;"

# Prüfe Firewall
sudo ufw status
```

### Performance-Probleme

Bearbeite `/etc/systemd/system/metabase.service`:

```ini
Environment="JAVA_OPTS=-Xmx4g -Xms2g"
```

Dann:
```bash
sudo systemctl daemon-reload
sudo systemctl restart metabase
```

## Nächste Schritte

1. ✅ Metabase installiert
2. ✅ Datenbank verbunden
3. ⏳ Beispiel-Dashboards erstellen
4. ⏳ In DRIVE Portal integrieren
5. ⏳ Nutzer-Schulung

## Vorteile

- **Interaktiv:** Filter, Drill-Down, Zeiträume ändern
- **Echtzeit:** Daten werden live aus DB geholt
- **Flexibel:** Nutzer können eigene Queries erstellen
- **Sharing:** Dashboards können geteilt werden
- **Alerts:** Automatische Benachrichtigungen möglich
