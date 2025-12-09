# PROMPT FÜR NÄCHSTE SESSION - TAG 103

**Datum:** 2025-12-08  
**Letzter Stand:** TAG 102 - HR Datenqualitäts-Check

---

## 🎯 KONTEXT FÜR CLAUDE

Ich entwickle das **Greiner Portal DRIVE** - ein ERP-System für ein Autohaus.

### Letzte Session (TAG 102):
- HR Datenqualitäts-Check Script für Locosoft erstellt
- Anleitung für Vanessa (HR) mit konkreten MA-Listen
- Locosoft-Schema analysiert (is_latest_record ist immer NULL!)
- 15 MA ohne Pausen, 9 MA mit unvollständigen Arbeitszeiten gefunden

---

## 📁 RELEVANTE DATEIEN

### Neue Dateien TAG 102:
- `scripts/hr_datenqualitaet_check.py` - Prüft Locosoft-Datenqualität
- `docs/HR_LOCOSOFT_DATENPFLEGE_ANLEITUNG_V2.md` - Anleitung für HR

### Wichtige Docs:
- `docs/SESSION_WRAP_UP_TAG102.md` - Vollständige Doku
- `docs/DB_SCHEMA_LOCOSOFT.md` - Locosoft-Tabellen
- `docs/DB_SCHEMA_SQLITE.md` - Portal-Tabellen

---

## 🔧 SERVER-ZUGANG

```bash
# SSH
ssh ag-admin@10.80.80.20

# Projekt
cd /opt/greiner-portal
source venv/bin/activate

# Service
sudo systemctl restart greiner-portal
sudo journalctl -u greiner-portal -f

# Sync-Mount (Windows-Share)
/mnt/greiner-portal-sync/

# Dateien kopieren
cp /mnt/greiner-portal-sync/[pfad] /opt/greiner-portal/[pfad]
```

---

## 🎨 FRONTEND-WEITERENTWICKLUNG - IDEEN

### Dashboard-Konsolidierung:
- [ ] Werkstatt: Viele ähnliche Seiten → vereinheitlichen
- [ ] Rollenbasierte Startseiten (Werkstattleiter vs. Serviceberater)
- [ ] Mobile-Optimierung für Werkstatt-Monitor

### Neue Features:
- [ ] HR Überstunden-Dashboard (`/hr/ueberstunden`)
- [ ] Teile-Status Verbesserungen (Alerts, Export)
- [ ] Controlling-Dashboard Refresh

### UX-Verbesserungen:
- [ ] Einheitliche Farbgebung/Icons
- [ ] Loading-States verbessern
- [ ] Fehlerbehandlung im Frontend

---

## 💡 ARBEITSWEISE MIT CLAUDE

### Du (Florian) gibst mir:
1. **Konkreten Fokus** was gemacht werden soll
2. **Screenshots** wenn etwas nicht funktioniert
3. **Terminal-Output** nach Script-Ausführung

### Ich (Claude) gebe dir:
1. **Komplette Dateien** für den Server (im Sync-Verzeichnis)
2. **Copy-Befehle** zum Kopieren auf den Server
3. **Git-Befehle** am Ende der Session
4. **Wrap-Up** mit allem Wichtigen

### Kommunikation:
- Ich schreibe Dateien ins Sync-Verzeichnis
- Du kopierst sie mit `cp /mnt/greiner-portal-sync/... /opt/greiner-portal/...`
- Bei Python-Änderungen: `sudo systemctl restart greiner-portal`

---

## 🚀 SCHNELLSTART

```
Hallo Claude, wir machen weiter mit dem Greiner Portal.

Letzte Session: TAG 102 - HR Datenqualitäts-Check
Server: 10.80.80.20 (bin per Putty verbunden)

Heute möchte ich: FRONTEND WEITERENTWICKELN

Konkret: [WAS GENAU?]
- Dashboard X verbessern?
- Neue Seite Y erstellen?
- Mobile-Optimierung?
- UX-Verbesserungen?

Relevante Docs im Sync-Verzeichnis:
\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\docs\
```

---

## 📊 AKTUELLE ARCHITEKTUR

```
GREINER DRIVE
│
├── Controlling
│   ├── BWA Dashboard
│   ├── TEK (Tägliche Erfolgskosten)
│   └── Bankenspiegel
│
├── Verkauf
│   ├── Auftragseingang
│   ├── Auslieferungen
│   └── Leasys Kalkulator
│
├── HR
│   ├── Urlaubsplaner V2
│   ├── Stempeluhr + Monitor
│   └── [NEU] Datenqualitäts-Check
│
└── After Sales
    ├── Serviceberater Controlling
    ├── Teile (Bestellungen, Preisradar, Status)
    └── Werkstatt
        ├── Cockpit (Ampel-System)
        ├── Aufträge & Prognose (ML)
        ├── Stempeluhr + Monitor
        ├── Leistungsübersicht
        └── Tagesbericht
```

---

## ⚠️ WICHTIGE HINWEISE

1. **Sync-Verzeichnis nutzen:** Dateien in `\\Srvrdb01\...\Server\` schreiben
2. **Copy-Befehl geben:** `cp /mnt/greiner-portal-sync/... /opt/greiner-portal/...`
3. **Kein rsync!** Einfacher `cp` Befehl reicht
4. **Templates:** Kein Restart nötig - nur Browser-Refresh (Strg+F5)
5. **Python-Code:** `sudo systemctl restart greiner-portal` nach Änderungen

---

**Erstellt:** 2025-12-08  
**Projekt:** GREINER DRIVE
