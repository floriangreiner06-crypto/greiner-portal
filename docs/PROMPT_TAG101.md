# PROMPT FÜR NÄCHSTE SESSION - TAG 101

**Datum:** 2025-12-07  
**Letzter Stand:** TAG 100 - Teile-Status Dashboard

---

## 🎯 KONTEXT FÜR CLAUDE

Ich entwickle das **Greiner Portal DRIVE** - ein ERP-System für ein Autohaus.

### Letzte Session (TAG 100):
1. **Stempeluhr Leerlauf-Fix**: Außerhalb Arbeitszeit (06:30-18:00) wird kein Leerlauf mehr angezeigt
2. **Teile-Status Dashboard**: `/werkstatt/teile-status` zeigt Aufträge die auf Teile warten
3. **Lieferzeit-Analyse**: Historische Daten analysiert (65.957 Lieferscheine, 329 Lieferanten)

### Wichtige Erkenntnisse TAG 100:

**Lieferzeiten pro Lieferant:**
- BTZ (Stellantis): Ø 9.2 Tage (4.573 Lieferungen)
- Hyundai: Ø 9.6 Tage (2.145 Lieferungen)  
- Opel direkt: Ø 13.2 Tage (langsamer als BTZ!)
- EFA Autoteilewelt: Ø 8.4 Tage

**Kritische Aufträge gefunden:**
- #20853: 642 Tage offen (fast 2 Jahre!)
- #21607: 607 Tage, 1.514€ Teilewert
- → Müssen mit Serviceleiter besprochen werden

**Daten für ML vorhanden:**
- 55.726 Lieferscheine (2024+)
- 17.981 verschiedene Teile
- ML-Training für Lieferzeit-Prognose möglich

---

## 📁 RELEVANTE DATEIEN

### Neue Dateien TAG 100:
- `api/teile_status_api.py` - Teile-Status API
- `templates/aftersales/werkstatt_teile_status.html` - Dashboard

### Geänderte Dateien:
- `api/werkstatt_live_api.py` - Leerlauf-Fix
- `app.py` - Blueprint registriert, Route hinzugefügt
- `templates/base.html` - Menü erweitert

### Wichtige Docs:
- `docs/SESSION_WRAP_UP_TAG100.md` - Vollständige Doku
- `docs/GUDAT_API_INTEGRATION.md` - Gudat-Anbindung
- `docs/DB_SCHEMA_LOCOSOFT.md` - Locosoft-Tabellen

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
```

---

## ⏳ OFFENE TODOS

### PRIO 1: Mit Serviceleiter besprechen
- [ ] Kritische Aufträge prüfen (>500 Tage offen)
- [ ] Back-Order Teile Kennzeichnung?
- [ ] Garantie-Teile Handling?

### PRIO 2: ML für Lieferzeit-Prognose
- [ ] Training mit historischen Daten
- [ ] Features: Lieferant, Teilekategorie, Wochentag
- [ ] Integration in Teile-Status Dashboard

### PRIO 3: Dashboard-Verbesserungen
- [ ] E-Mail Alert bei kritischen Aufträgen
- [ ] Wöchentlicher Teile-Report
- [ ] Export nach Excel

### PRIO 4: Werkstatt-Konsolidierung
- [ ] Dashboard-Aufräumen (viele ähnliche Seiten)
- [ ] Rollenbasierte Startseiten

---

## 💡 ARBEITSWEISE MIT CLAUDE

### Du (Florian) gibst mir:
1. **Screenshots** wenn etwas nicht funktioniert
2. **Terminal-Output** nach Script-Ausführung
3. **Konkreten Fokus** was gemacht werden soll

### Ich (Claude) gebe dir:
1. **Copy-Paste-fertige Scripts** für Terminal
2. **Komplette Dateien** für den Server
3. **Git-Befehle** am Ende der Session
4. **Wrap-Up** mit allem Wichtigen

### Kommunikation:
- Ich schreibe Scripts die du in Putty kopierst
- Du kopierst Output zurück zu mir
- Ich analysiere und gebe nächsten Schritt

---

## 🚀 SCHNELLSTART

```
Hallo Claude, wir machen weiter mit dem Greiner Portal.

Letzte Session: TAG 100 - Teile-Status Dashboard
Server: 10.80.80.20 (bin per Putty verbunden)

Heute möchte ich: [DEIN ZIEL]

Relevante Docs sind im Projekt unter /docs/
```

---

## 📊 AKTUELLE ARCHITEKTUR

```
GREINER DRIVE
│
├── Controlling (BWA, TEK, Bankenspiegel)
├── Verkauf (Auftragseingang, Auslieferungen, Leasys)
├── Urlaubsplaner V2
│
└── After Sales
    ├── Serviceberater Controlling
    ├── Teile
    │   ├── Teilebestellungen
    │   ├── Preisradar
    │   └── **Teile-Status** (NEU TAG 100)
    │
    └── Werkstatt
        ├── **Cockpit** (Ampel-System)
        ├── Aufträge & Prognose (ML)
        ├── Stempeluhr + Monitor
        ├── Leistungsübersicht
        └── Tagesbericht
```

---

**Erstellt:** 2025-12-07  
**Projekt:** GREINER DRIVE
