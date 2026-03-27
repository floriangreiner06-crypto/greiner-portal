# SESSION WRAP-UP TAG 125

**Datum:** 2025-12-18
**Branch:** feature/tag82-onwards

---

## Zusammenfassung

Werkstatt Live-Board komplett neu implementiert mit Karten-basierter UI und Gudat-Integration.

---

## Erledigte Aufgaben

### 1. Werkstatt Live-Board API (`api/werkstatt_live_api.py`)

- **Neuer Endpoint:** `/api/werkstatt/live/board` - Liefert alle Mechaniker mit aktuellen Aufträgen
- **Gudat-Integration:** GraphQL-Query für `workshopTasks` um disponierte Aufträge aus Gudat zu holen
- **Name-Matching:** Funktion zum Mapping von Gudat-Namen ("Vorname Nachname") zu Locosoft-Namen ("Nachname, Vorname")
- **Daten-Merge:** Wenn ein Auftrag sowohl in Locosoft als auch in Gudat existiert, werden AW und Kennzeichen aus Gudat ergänzt
- **Auftragsdetails für Live-Stempelungen:** Neue Query um AW/Kennzeichen/Kunde für alle Live-Aufträge aus Locosoft zu holen
- **Retired-Employee-Filter:** `leave_date IS NULL` Filter um ausgeschiedene Mitarbeiter auszublenden

### 2. Werkstatt Live-Board UI (`templates/aftersales/werkstatt_liveboard.html`)

- **Komplett neue Karten-basierte Ansicht** statt Gantt-View
- **Mechaniker-Karten** mit:
  - Avatar mit Initialen
  - Status-Farben (Aktiv=Grün, Verfügbar=Grau, Abwesend=Rot)
  - Aktueller Auftrag mit Laufzeit und Fortschrittsbalken
  - Warteschlange der nächsten Aufträge (Gudat=Orange, Locosoft=Blau)
- **Auftrag-Detail-Modal** bei Klick auf Aufträge:
  - Fahrzeug-Info (Kennzeichen, VIN, Marke/Modell, KM-Stand)
  - Auftrag-Info (Auftrag-Nr, Standort, Serviceberater)
  - Planung (Eingang/Fertig)
  - AW-Summen (Gesamt, Offen, Fakturiert)
  - Arbeitspositionen mit Beschreibung und Mechaniker
  - Teile-Liste mit Preisen
- **Betrieb-Filter:** Alle Standorte / Deggendorf / Landau
- **Auto-Refresh:** Alle 30 Sekunden

### 3. Route (`routes/werkstatt_routes.py`)

- Neue Route `/werkstatt/liveboard` und `/werkstatt/drive/liveboard`

---

## Behobene Fehler

1. **`e.short_name` existiert nicht** → Aus Query entfernt, aus Namen abgeleitet
2. **`egm.subsidiary` existiert nicht** → Geändert zu `e.subsidiary`
3. **`e.employment_end` existiert nicht** → Filter entfernt
4. **`ac.absence_type` existiert nicht** → Geändert zu `ac.type`
5. **`mk.free_form_make_text` existiert nicht** → Geändert zu `v.free_form_make_text`
6. **Rentner "Robert" angezeigt** → Filter `leave_date IS NULL` hinzugefügt
7. **Auftrag 38422 zeigt 0 AW** → Gudat-Daten werden in bestehende Locosoft-Einträge gemerged
8. **AW fehlen bei Ad-hoc Aufträgen** → Neue Query für Auftragsdetails aller Live-Stempelungen

---

## Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `api/werkstatt_live_api.py` | +606 Zeilen - Live-Board Endpoint mit Gudat-Integration |
| `templates/aftersales/werkstatt_liveboard.html` | Neu - Karten-basierte UI mit Modal |
| `routes/werkstatt_routes.py` | +2 Routes für Liveboard |

---

## Sync-Befehle (für Server)

```bash
# API
cp /mnt/greiner-portal-sync/api/werkstatt_live_api.py /opt/greiner-portal/api/

# Template
cp /mnt/greiner-portal-sync/templates/aftersales/werkstatt_liveboard.html /opt/greiner-portal/templates/aftersales/

# Routes
cp /mnt/greiner-portal-sync/routes/werkstatt_routes.py /opt/greiner-portal/routes/

# Neustart
sudo systemctl restart greiner-portal
```

---

## Offene Punkte / Nächste Schritte

- Gudat-Aufträge könnten noch Start-/Endzeiten aus der Disposition bekommen (aktuell geschätzt)
- Live-Board könnte um Sound-Benachrichtigungen erweitert werden
- Mobile-Optimierung für Tablet-Nutzung in der Werkstatt

---

*Session beendet: 2025-12-18*
