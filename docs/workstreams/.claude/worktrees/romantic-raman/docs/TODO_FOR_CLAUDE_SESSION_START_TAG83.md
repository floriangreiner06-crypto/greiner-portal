# TODO FOR CLAUDE - SESSION START TAG83
**Datum:** 25. November 2025  
**Vorherige Session:** TAG82

---

## 🎯 PRIORITÄT 1: User-Feedback aus Disposition

### 1.1 Modellbezeichnung im Auftragseingang falsch
**Problem:** Fahrzeug zeigt Code `2GU93KHOXKB0A0E5P0PR35FX` statt "Movano"  
**Ursache:** Wahrscheinlich Mapping aus Locosoft (`model_key` statt `model_description`)  
**Lösung:** 
- Prüfen woher die Modellbezeichnung kommt
- `api/verkauf_api.py` oder `sync_sales.py` anpassen
- Evtl. JOIN auf Fahrzeug-Stammdaten

### 1.2 Bruttoertrag nach Faktura aktualisieren
**Problem:** Bruttoertrag wird nach Faktura nicht mehr aktualisiert  
**Ursache:** Daten werden evtl. nur bei Auftragsanlage geholt  
**Lösung:**
- Prüfen welches Feld in Locosoft den finalen Ertrag enthält
- Sync anpassen um auch fakturierte Aufträge zu aktualisieren

### 1.3 Werkstattaufträge zum Fahrzeug anzeigen
**Problem:** Disposition will offene interne WA sehen  
**Anforderung:** 
- Neue Abfrage in Locosoft (Tabelle `werkstattauftrag` oder ähnlich)
- In Fahrzeug-Detail oder Auslieferungs-Detail anzeigen
- Filter auf VIN/Fahrzeug-ID

### 1.4 Farben erklären / vereinfachen
**Problem:** Farben (grün, gelb, blau, rot) unklar  
**Anforderung:** 
- Legende hinzufügen ODER
- Auf grün/rot reduzieren
- Prüfen wo Farben verwendet werden

---

## 📁 RELEVANTE DATEIEN

```
api/verkauf_api.py          → Verkauf-API (Version 2.2-vin)
scripts/sync/sync_sales.py  → Verkaufsdaten-Sync aus Locosoft
templates/verkauf_*.html    → Verkauf-Templates
```

---

## 🔧 SERVER-INFO

```
Server: 10.80.80.20 (srvlinux01)
Portal: https://drive.auto-greiner.de
Branch: feature/tag82-onwards
```

---

## ✅ ERLEDIGTE FEATURES (TAG82)

- VIN-Filter + aufklappbare Auslieferungen
- Zinsen-Zugriff für Verkauf/Disposition
- Admin-Dashboard im User-Menü
- Log-Anzeige + Status-Fix
- Backup-Scripts

---

## 📋 QUICK START

```bash
# Server-Verbindung
ssh ag-admin@10.80.80.20

# Ins Projektverzeichnis
cd /opt/greiner-portal

# Venv aktivieren
source venv/bin/activate

# Status prüfen
curl -s http://localhost:5000/api/verkauf/health
```

---

*Erstellt: 25.11.2025*
