# DRIVE Handbuch - IT & Administration

**Zielgruppe:** IT-Abteilung, Systemadministratoren
**Rolle im System:** admin
**Stand:** Dezember 2025

---

## Übersicht Admin-Module

| Modul | URL | Funktion |
|-------|-----|----------|
| Celery Tasks | /admin/celery | Job-Überwachung |
| Report-Subscriptions | /admin/reports | E-Mail-Reports |
| Rechteverwaltung | /admin/rechte | Benutzer-Rollen |
| Mitarbeiter-Sync | /admin/mitarbeiter | LDAP-Abgleich |
| System-Status | /admin/system | Health-Checks |
| API-Dokumentation | /api/docs | Swagger UI |

---

## 1. Celery Task Manager

**URL:** https://drive.auto-greiner.de/admin/celery/

### Übersicht
Zeigt alle **geplanten Hintergrund-Jobs**:
- Daten-Syncs (Locosoft, ServiceBox, MT940)
- Report-Generierung
- E-Mail-Versand
- Cleanup-Tasks

### Job-Status
| Status | Bedeutung |
|--------|-----------|
| SUCCESS | Job erfolgreich abgeschlossen |
| FAILURE | Job fehlgeschlagen (Logs prüfen!) |
| PENDING | Job in Warteschlange |
| STARTED | Job läuft gerade |
| REVOKED | Job abgebrochen |

### Manuelle Ausführung
1. Job in der Liste finden
2. "Jetzt ausführen" klicken
3. Status überwachen

### Flower Dashboard
Detailliertes Monitoring: http://10.80.80.20:5555
- Task-Historie
- Worker-Status
- Queues
- Rate Limiting

### Wichtige Tasks
| Task | Zeitplan | Beschreibung |
|------|----------|--------------|
| sync_locosoft | Alle 15 Min | Werkstatt-Daten |
| import_mt940 | 06:00 täglich | Bank-Transaktionen |
| import_santander | 07:00 täglich | Santander-Finanzierungen |
| send_daily_tek | 17:30 Mo-Fr | TEK-Report |
| send_daily_auftragseingang | 17:15 Mo-Fr | Verkaufs-Report |
| cleanup_old_logs | 02:00 täglich | Log-Bereinigung |

---

## 2. Report-Subscriptions

**URL:** https://drive.auto-greiner.de/admin/reports

### Report-Typen
| Report | Frequenz | Empfänger |
|--------|----------|-----------|
| TEK Daily | Täglich 17:30 | GF, Controlling |
| TEK Filiale | Täglich 17:30 | Standortleiter |
| Auftragseingang | Täglich 17:15 | Verkaufsleitung |
| Werkstatt Tagesbericht | Täglich 18:00 | Werkstattleitung |
| Penner Weekly | Montags 07:00 | Teileleitung |
| Zinsfreiheit Alert | Bei Fälligkeit | GF, Finanzen |

### Empfänger verwalten
1. Report auswählen
2. E-Mail hinzufügen/entfernen
3. Standort-Filter setzen (optional)
4. Speichern

### Report testen
1. Report auswählen
2. "Test-E-Mail senden" klicken
3. Geht an den angemeldeten Admin

---

## 3. Rechteverwaltung

**URL:** https://drive.auto-greiner.de/admin/rechte

### Rollen-Hierarchie
```
admin
├── buchhaltung
├── controlling
├── verkauf_leitung
│   └── verkauf
├── werkstatt_leitung
│   └── werkstatt
├── service_leitung
│   └── serviceberater
├── teile_leitung
│   └── teile
└── hr
```

### Rolle zuweisen
1. Benutzer suchen (Name oder E-Mail)
2. Rolle aus Dropdown wählen
3. Speichern

### LDAP-Abgleich
Rollen werden primär aus Active Directory übernommen:
- OU-Mapping (z.B. OU=Geschäftsleitung → admin)
- Manuelle Zuweisung überschreibt AD-Rolle
- Bei AD-Änderung: Sync ausführen

### Modul-Berechtigungen
| Modul | Erlaubte Rollen |
|-------|-----------------|
| Bankenspiegel | admin, buchhaltung |
| TEK | admin, controlling, *_leitung |
| Verkauf | admin, verkauf_leitung, verkauf |
| Werkstatt | admin, werkstatt_leitung, werkstatt, service* |
| Urlaubsplaner | alle (eingeschränkt nach Rolle) |
| Admin | nur admin |

---

## 4. System-Architektur

### Server-Infrastruktur
```
10.80.80.20 (srvlinux01)
├── Flask App (Port 5000)
├── Celery Workers (4x)
├── Redis (Message Broker)
├── PostgreSQL (DRIVE Portal DB)
└── Nginx (Reverse Proxy)

10.80.80.8 (Locosoft)
└── PostgreSQL (loco_auswertung_db)
```

### Dienste
| Dienst | Systemd-Unit | Port |
|--------|--------------|------|
| Flask App | greiner-portal | 5000 |
| Celery Worker | celery-worker | - |
| Celery Beat | celery-beat | - |
| Flower | flower | 5555 |
| Redis | redis | 6379 |
| PostgreSQL | postgresql | 5432 |

### Neustart-Befehle
```bash
# Flask App
sudo systemctl restart greiner-portal

# Celery (alle)
sudo systemctl restart celery-worker celery-beat

# Einzelne Worker
sudo systemctl restart celery-worker@1
```

---

## 5. Datenbanken

### PostgreSQL (DRIVE Portal)
```bash
# Verbinden
psql -h localhost -U drive_user -d drive_portal

# Backup
pg_dump drive_portal > backup_$(date +%Y%m%d).sql

# Restore
psql drive_portal < backup_20251229.sql
```

### PostgreSQL (Locosoft - readonly)
```bash
# Verbinden
PGPASSWORD=loco psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db

# Nur Lesezugriff!
```

### Wichtige Tabellen (Portal)
| Tabelle | Inhalt |
|---------|--------|
| employees | Mitarbeiter (aus LDAP) |
| vacation_bookings | Urlaubsbuchungen |
| konten | Bankkonten |
| transaktionen | Bank-Buchungen |
| fahrzeugfinanzierungen | Zinstracking |
| users | Portal-Benutzer |

---

## 6. Log-Dateien

### Pfade
```
/opt/greiner-portal/logs/
├── app.log              # Flask Anwendung
├── celery_worker.log    # Celery Tasks
├── celery_beat.log      # Scheduler
├── sync_locosoft.log    # Daten-Sync
└── error.log            # Kritische Fehler
```

### Log-Befehle
```bash
# Live-Logs
journalctl -u greiner-portal -f

# Letzte Fehler
journalctl -u greiner-portal -p err --since "1 hour ago"

# Celery-Logs
journalctl -u celery-worker -f
```

### Log-Rotation
Automatisch via logrotate:
- Täglich rotiert
- 30 Tage aufbewahrt
- Komprimiert nach 3 Tagen

---

## 7. Monitoring

### Health-Checks
```bash
# Flask App
curl http://localhost:5000/api/health

# Celery Worker
celery -A celery_app.celery_config inspect active

# Redis
redis-cli ping

# PostgreSQL
pg_isready -h localhost -p 5432
```

### Alerts
Bei kritischen Fehlern wird automatisch E-Mail an IT gesendet:
- DB-Verbindungsfehler
- Task-Failures (3x hintereinander)
- Sync-Fehler
- Hohe Memory-Auslastung

---

## 8. Deployment

### Code-Update
```bash
# Auf Server wechseln
ssh ag-admin@10.80.80.20

# Code synchronisieren
rsync -av --exclude '.git' /mnt/greiner-portal-sync/ /opt/greiner-portal/

# Neustart
sudo systemctl restart greiner-portal
sudo systemctl restart celery-worker celery-beat
```

### Rollback
```bash
# Git-Stand prüfen
cd /opt/greiner-portal
git log --oneline -10

# Auf vorherigen Stand zurück
git checkout <commit-hash>

# Neustart
sudo systemctl restart greiner-portal
```

### Templates
Templates brauchen **keinen Neustart**, nur Browser-Refresh (Strg+F5).

---

## 9. Backup & Recovery

### Automatische Backups
| Was | Wann | Aufbewahrung |
|-----|------|--------------|
| PostgreSQL | Täglich 03:00 | 30 Tage |
| Konfiguration | Wöchentlich | 12 Wochen |
| Logs | Täglich | 30 Tage |

### Backup-Pfad
```
/backup/greiner-portal/
├── db/          # Datenbank-Dumps
├── config/      # .env, nginx
└── logs/        # Log-Archive
```

### Recovery-Schritte
1. Dienste stoppen
2. DB-Dump einspielen
3. Code-Stand wiederherstellen (Git)
4. Dienste starten
5. Health-Check

---

## 10. Troubleshooting

### Häufige Probleme

#### 500 Internal Server Error
```bash
# Fehler in Logs finden
journalctl -u greiner-portal --since "5 minutes ago" | grep -i error

# Häufige Ursachen:
# - DB-Verbindung unterbrochen
# - Fehlende Umgebungsvariable
# - Python-Syntax-Fehler
```

#### Task läuft nicht
```bash
# Celery Worker prüfen
celery -A celery_app.celery_config inspect active

# Beat Scheduler prüfen
journalctl -u celery-beat --since "1 hour ago"

# Task manuell triggern
celery -A celery_app.celery_config call tasks.sync_locosoft
```

#### Daten nicht aktuell
```bash
# Letzten Sync prüfen
SELECT * FROM sync_log ORDER BY timestamp DESC LIMIT 10;

# Sync manuell starten
curl -X POST http://localhost:5000/admin/celery/run/sync_locosoft
```

#### LDAP-Login funktioniert nicht
```bash
# LDAP-Verbindung testen
ldapsearch -x -H ldap://10.80.80.1 -D "user@domain" -W -b "dc=domain,dc=local"

# AD-Server erreichbar?
ping 10.80.80.1
```

---

## 11. Sicherheit

### Best Practices
- **Passwörter:** In .env, nicht im Code
- **Zugriff:** Nur über VPN von extern
- **Updates:** Regelmäßige Security-Patches
- **Logs:** Keine sensiblen Daten loggen

### Credentials
Alle Zugangsdaten in:
```
/opt/greiner-portal/config/.env
```

**Niemals commiten!** Die .env ist in .gitignore.

### Firewall
| Port | Dienst | Zugriff |
|------|--------|---------|
| 80/443 | Nginx | Intern |
| 5000 | Flask | Localhost |
| 5432 | PostgreSQL | Localhost |
| 5555 | Flower | IT-Team |
| 6379 | Redis | Localhost |

---

## Kontakt

| Bereich | Ansprechpartner |
|---------|-----------------|
| Server-Probleme | Florian Greiner |
| Locosoft-DB | Locosoft-Support |
| Active Directory | Domain-Admin |
| Netzwerk | IT-Dienstleister |

---

*Letzte Aktualisierung: TAG 143 - Dezember 2025*
