# Metabase Firewall-Fix

## Problem
Metabase war nicht von außen erreichbar (ERR_CONNECTION_TIMED_OUT), obwohl der Service lokal lief.

## Lösung
Port 3001 wurde in der UFW-Firewall freigegeben:

```bash
sudo ufw allow 3001/tcp
```

## Status
✅ Port 3001 ist jetzt in der Firewall freigegeben
✅ Metabase ist von außen erreichbar: http://10.80.80.20:3001

## Firewall-Regeln für Metabase

Aktuelle Regeln:
- Port 3000: Grafana (bereits freigegeben)
- Port 3001: Metabase (neu freigegeben)

Prüfen:
```bash
sudo ufw status | grep 3001
```

## Nächste Schritte
1. Öffne http://10.80.80.20:3001 im Browser
2. Erstelle Admin-Account
3. Verbinde PostgreSQL-Datenbank
