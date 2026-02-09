# Metabase Setup für DRIVE Portal

## Übersicht

Metabase ist ein Open-Source Business Intelligence Tool, das interaktive Dashboards und Reports für TEK und BWA-Daten ermöglicht.

## Installation

### Option 1: JAR-Installation (Empfohlen)

```bash
sudo /opt/greiner-portal/scripts/install_metabase_jar.sh
```

### Option 2: Docker-Installation

```bash
sudo /opt/greiner-portal/scripts/install_metabase.sh
```

## Zugriff

Nach der Installation:
- **Metabase URL:** http://10.80.80.20:3001
- **Grafana URL:** http://10.80.80.20:3000 (bereits installiert)
- Erster Start: Admin-Account erstellen

## Datenbankverbindung

### PostgreSQL-Verbindung einrichten:

1. In Metabase: **Add Database** → **PostgreSQL**
2. Verbindungsdaten:
   - **Host:** `localhost` (oder `127.0.0.1`)
   - **Port:** `5432`
   - **Database name:** `drive_portal`
   - **Username:** `drive_user`
   - **Password:** [aus DB-Konfiguration]

## Beispiel-Dashboards

### TEK Dashboard

**Datenquelle:** `controlling_data` View oder direkte Tabellen

**Beispiel-Queries:**

1. **TEK Gesamt - Monat kumuliert:**
```sql
SELECT 
    b.name as bereich,
    SUM(erloes) as erloes,
    SUM(einsatz) as einsatz,
    SUM(db1) as db1,
    SUM(stueck) as menge
FROM controlling_data cd
JOIN bereiche b ON cd.bereich_id = b.id
WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
  AND monat <= EXTRACT(MONTH FROM CURRENT_DATE)
GROUP BY b.name
ORDER BY b.name;
```

2. **TEK nach Standort:**
```sql
SELECT 
    s.name as standort,
    b.name as bereich,
    SUM(erloes) as erloes,
    SUM(db1) as db1
FROM controlling_data cd
JOIN standorte s ON cd.standort_id = s.id
JOIN bereiche b ON cd.bereich_id = b.id
WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
  AND monat = EXTRACT(MONTH FROM CURRENT_DATE)
GROUP BY s.name, b.name
ORDER BY s.name, b.name;
```

### BWA Dashboard

**Datenquelle:** `loco_journal_accountings` + berechnete Views

**Beispiel-Queries:**

1. **BWA Monatswerte:**
```sql
SELECT 
    position,
    betrag,
    jahr,
    monat
FROM bwa_monatswerte
WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
ORDER BY monat, position;
```

2. **BWA Drill-Down (Umsatz nach Konto):**
```sql
SELECT 
    nominal_account_number as konto,
    SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0 as umsatz
FROM loco_journal_accountings
WHERE accounting_date >= DATE_TRUNC('month', CURRENT_DATE)
  AND accounting_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
  AND nominal_account_number BETWEEN 800000 AND 899999
GROUP BY nominal_account_number
ORDER BY umsatz DESC;
```

## Service-Management

### Status prüfen:
```bash
sudo systemctl status metabase
```

### Logs anzeigen:
```bash
sudo journalctl -u metabase -f
```

### Neustart:
```bash
sudo systemctl restart metabase
```

### Stoppen:
```bash
sudo systemctl stop metabase
```

## Integration in DRIVE Portal

### Option 1: Iframe-Einbindung

In `templates/controlling/tek_dashboard.html` oder neuer Seite:

```html
<iframe 
    src="http://10.80.80.20:3001/public/dashboard/[DASHBOARD-ID]?standort=[STANDORT]"
    width="100%" 
    height="800px"
    frameborder="0">
</iframe>
```

### Option 2: Link-Integration

Einfacher Link zu Metabase-Dashboards in der Navigation.

## Vorteile gegenüber PDF-Reports

1. **Interaktivität:** Filter, Drill-Down, Zeiträume ändern
2. **Echtzeit:** Daten werden live aus DB geholt
3. **Flexibilität:** Nutzer können eigene Queries erstellen
4. **Sharing:** Dashboards können geteilt werden
5. **Alerts:** Automatische Benachrichtigungen bei Schwellwerten

## Troubleshooting

### Metabase startet nicht:
- Prüfe Java: `java -version`
- Prüfe Port 3001: `sudo netstat -tlnp | grep 3001`
- Prüfe Logs: `sudo journalctl -u metabase -n 50`

### Datenbankverbindung fehlgeschlagen:
- Prüfe PostgreSQL läuft: `sudo systemctl status postgresql`
- Prüfe Firewall: `sudo ufw status`
- Teste Verbindung: `psql -h localhost -U drive_user -d drive_portal`

### Performance-Probleme:
- Erhöhe Java Memory: `JAVA_OPTS=-Xmx4g` in `/etc/systemd/system/metabase.service`
- Nutze Materialized Views für komplexe Queries
- Cache-Einstellungen in Metabase optimieren
