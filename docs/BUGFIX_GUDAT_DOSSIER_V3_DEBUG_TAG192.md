# Bugfix: GUDAT-Dossier-Suche V3 - Erweiterte Debug-Logging

**TAG:** 192  
**Datum:** 2026-01-15  
**Problem:** Dossier für Auftrag 39831 wird nicht gefunden, obwohl es in GUDAT vorhanden ist

---

## 🔴 Problem

**Auftrag:** 39831  
**Kennzeichen:** VIT-RW 56  
**VIN:** WOLSH9ED0B4160021 (im Bild) / W0LSH9ED0B4160021 (in Logs - möglicherweise 0 vs O Problem)  
**Datum:** 2026-01-07

**Symptome:**
- Order-Nummer 39831 wird nicht in 2343 Tasks (90 Tage) gefunden
- Alternative Suche nach Kennzeichen/VIN findet 0 Anhänge
- Dossier ist laut Benutzer in GUDAT vorhanden

---

## ✅ Lösung V3: Erweiterte Debug-Logging

### 1. Vehicle-Objekt-Status
- **Neu:** Zähle Tasks mit/ohne vehicle-Objekt
- **Zweck:** Prüfen ob GraphQL-Query vehicle-Objekt zurückgibt

### 2. VIN-Sammlung
- **Neu:** Sammle alle gefundenen VINs (nur erste 10 pro Seite)
- **Zweck:** Prüfen ob VIN überhaupt in Tasks vorhanden ist

### 3. VIN-Ähnlichkeits-Prüfung
- **Neu:** Prüfe auf VIN-Teil-Matches (letzte 8 Zeichen)
- **Neu:** Prüfe auf 0/O-Problem (VIN könnte 0 statt O enthalten oder umgekehrt)
- **Zweck:** Finden von VINs die ähnlich sind, aber nicht exakt passen

### 4. Zusammenfassung nach Seite 1
- **Neu:** Zeige Zusammenfassung nach Seite 1 wenn kein Match gefunden
- **Zweck:** Schnelle Diagnose ob Suche grundsätzlich funktioniert

### Code-Änderungen:
```python
# Vehicle-Objekt-Status
tasks_with_vehicle = 0
tasks_without_vehicle = 0
for task in tasks_vehicle:
    vehicle = task.get('dossier', {}).get('vehicle')
    if vehicle:
        tasks_with_vehicle += 1
    else:
        tasks_without_vehicle += 1

# VIN-Sammlung
found_vins = set()
if task_vin and len(found_vins) < 10:
    found_vins.add(task_vin)

# VIN-Ähnlichkeits-Prüfung
if len(search_vin_clean) >= 8 and len(task_vin_check) >= 8:
    if search_vin_clean[-8:] == task_vin_check[-8:]:
        logger.info(f"🔍 Mögliches VIN-Teil-Match gefunden...")
    # Prüfe auch auf ähnliche VINs (0 vs O Problem)
    search_vin_alt = search_vin_clean.replace('0', 'O').replace('O', '0')
    if search_vin_alt == task_vin_check:
        logger.info(f"🔍 Mögliches VIN-Ähnlichkeits-Match...")
```

---

## 📊 Erwartete Verbesserung

**Debug-Informationen:**
- Zeigt ob vehicle-Objekt in GraphQL-Response vorhanden ist
- Zeigt welche VINs/Kennzeichen gefunden werden
- Zeigt mögliche Teil-Matches oder 0/O-Probleme

**Nächste Schritte:**
1. Testen mit Auftrag 39831
2. Logs prüfen für:
   - Vehicle-Objekt-Status
   - Gefundene VINs/Kennzeichen
   - Mögliche Matches
3. Basierend auf Logs weitere Anpassungen vornehmen

---

## 🧪 Testing

**Bitte testen:**
1. Garantieauftrag 39831 öffnen
2. "Garantieakte erstellen" klicken
3. Logs prüfen für Debug-Informationen:
   ```bash
   journalctl -u greiner-portal --since "2 minutes ago" | grep -E "(Vehicle-Objekt|VIN|Kennzeichen|Fahrzeug-Suche)" -i
   ```

---

**Status:** ✅ Debug-Logging implementiert, Service neu gestartet
