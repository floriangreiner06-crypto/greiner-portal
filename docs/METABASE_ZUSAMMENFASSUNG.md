# Metabase Installation - Zusammenfassung

## ✅ Vorbereitung abgeschlossen

### Port-Konfiguration
- **Grafana:** Port 3000 (bereits installiert)
- **Metabase:** Port 3001 (wird installiert)

### Warum Metabase zusätzlich zu Grafana?

**Grafana** ist perfekt für:
- System-Monitoring
- Real-time Metriken
- Performance-Tracking

**Metabase** ist besser für:
- ✅ **TEK-Reports** (Tägliche Erfolgskontrolle)
- ✅ **BWA-Analysen** (Betriebswirtschaftliche Auswertung)
- ✅ **Business Intelligence** (selbst für Nicht-Techniker)
- ✅ **Drill-Down** (einfache Navigation durch Finanzdaten)

**Fazit:** Beide Tools parallel nutzen - jedes für seinen Zweck!

## Installation

```bash
cd /opt/greiner-portal
sudo bash scripts/install_metabase_safe.sh
```

Das Skript:
- ✅ Erstellt automatisch Backup
- ✅ Installiert auf Port 3001
- ✅ Ermöglicht Rollback bei Problemen

## Nach der Installation

1. **Öffne:** http://10.80.80.20:3001
2. **Erstelle Admin-Account**
3. **Verbinde PostgreSQL:**
   - Host: `localhost`
   - Port: `5432`
   - Database: `drive_portal`
   - User: `drive_user`

## Rollback

Bei Problemen:
```bash
BACKUP_DIR=$(ls -td /opt/greiner-portal/backups/metabase_* | head -1)
sudo bash /opt/greiner-portal/scripts/metabase_rollback.sh $BACKUP_DIR
```

## Erstellte Dateien

- ✅ Installationsskripte (mit Rollback)
- ✅ SQL-Queries für TEK & BWA
- ✅ Dokumentation
- ✅ Backup-System

## Nächste Schritte

1. Installation durchführen
2. Datenbank verbinden
3. Beispiel-Dashboards erstellen (Queries in `docs/metabase_queries.sql`)
4. In DRIVE Portal integrieren
