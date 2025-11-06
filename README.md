# Greiner Portal

Internes Portal für Auto Greiner mit folgenden Modulen:

## Module

- **Urlaubsplaner V2** - Urlaubsverwaltung mit Genehmigungsworkflow
- **Bankenspiegel** - Transaktionsübersicht aller Bankkonten
- **Stellantis-Integration** - Fahrzeugfinanzierungen
- **Fahrzeugverkäufe** - Verkaufsauswertungen
- **Locosoft-Sync** - Synchronisation mit Locosoft-System

## Tech Stack

- Python 3.12 + Flask
- SQLite (Datenbank)
- Gunicorn (WSGI Server)
- Nginx (Reverse Proxy)
- Grafana (Analytics & Monitoring)

## Server

- OS: Ubuntu 24.04 LTS
- Location: 10.80.80.20
- Installation: November 2025

## Dokumentation

Siehe `/docs` für detaillierte Anleitungen.

## Setup
```bash
cd /opt/greiner-portal
source venv/bin/activate
python app/app.py
```
