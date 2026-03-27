# TODO FOR CLAUDE - SESSION START TAG 162

**Letzte Session:** TAG 161 (2026-01-02)
**Fokus:** KST-Zielplanung API fertiggestellt

---

## KONTEXT

TAG 161 hat die KST-Zielplanung implementiert:

### Neue Komponenten:
- **Tabelle `kst_ziele`** - Monatliche Ziele pro Bereich
- **API `/api/kst-ziele/`** - IST/SOLL-Vergleich mit Hochrechnung
- Beispiel-Ziele fuer GJ 2025/26 eingefuegt

### API-Endpoints:
- `/health` - Health-Check
- `/dashboard` - Haupt-Dashboard mit Prognose
- `/ziele` - CRUD fuer Ziele
- `/status` - Taeglicher Status (Daumen hoch/runter)
- `/kumuliert` - YTD-Uebersicht

---

## AUFGABEN TAG 162

### Prioritaet 1: Taeglicher E-Mail-Report

Script fuer automatischen Versand des Ziel-Status:

```python
# scripts/send_daily_kst_status.py

def send_daily_status():
    # 1. Status von API holen
    # 2. HTML-E-Mail generieren
    # 3. An Geschaeftsleitung senden
```

**Empfaenger:**
- Florian Greiner
- Ggf. Bereichsleiter

**Inhalt:**
- Daumen hoch/runter pro Bereich
- Prognose vs. Ziel
- Handlungsempfehlungen
- Link zum Dashboard

### Prioritaet 2: Dashboard-UI

Template fuer Web-Oberflaeche:
- `/controlling/kst-ziele` Route
- Ampel-Anzeige pro Bereich
- Prognose-Balken
- Handlungsempfehlungen

### Prioritaet 3: Ziel-Editor

UI zum Bearbeiten der Ziele:
- Matrix: Monate x Bereiche
- Inline-Editing
- Speichern via API

---

## OFFENE PUNKTE AUS TAG 160

### CSV-Export GW-Dashboard

Der Export-Button in `/verkauf/gw-bestand` ist implementiert:
```javascript
function exportCSV() {
    window.location.href = `/api/fahrzeug/gw/export?${params}`;
}
```

**Status:** Muss getestet werden ob Endpoint existiert.

---

## ARCHITEKTUR-REFERENZ

### KST-Ziele Datenfluss
```
kst_ziele (Tabelle)
    ↓
kst_ziele_api.py
    ↓
/api/kst-ziele/dashboard
    ↓
Dashboard-UI (TODO)
```

### Dual-DB-Zugriff
```python
# DRIVE Portal (Ziele + FIBU)
with db_session() as conn:
    cursor.execute("SELECT ... FROM kst_ziele")
    cursor.execute("SELECT ... FROM loco_journal_accountings")

# Locosoft (Werkstatt/Fahrzeuge)
conn_loco = get_locosoft_connection()
cursor_loco.execute("SELECT ... FROM dealer_vehicles")
```

---

## WICHTIGE DATEIEN

```
api/kst_ziele_api.py      - KST-Zielplanung API (~550 LOC)
api/fahrzeug_data.py      - GW-Bestand SSOT
api/verkauf_data.py       - Verkaufs-Daten SSOT
api/controlling_data.py   - TEK-Daten
templates/verkauf_gw_dashboard.html - GW-Dashboard
```

---

## SERVER-BEFEHLE

```bash
# API testen
curl -s http://localhost:5000/api/kst-ziele/health
curl -s 'http://localhost:5000/api/kst-ziele/dashboard?monat=4' | python3 -m json.tool

# Sync nach Aenderungen
rsync -av /mnt/greiner-portal-sync/api/ /opt/greiner-portal/api/
rsync -av /mnt/greiner-portal-sync/scripts/ /opt/greiner-portal/scripts/

# Neustart
sudo systemctl restart greiner-portal

# Logs
journalctl -u greiner-portal -f --since "5 minutes ago"
```

---

*Vorbereitet fuer TAG 162*
