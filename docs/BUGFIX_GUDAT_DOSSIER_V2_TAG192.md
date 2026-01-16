# Bugfix: GUDAT-Dossier-Suche erweitert (V2)

**TAG:** 192  
**Datum:** 2026-01-15  
**Problem:** Dossiers werden immer noch nicht gefunden (z.B. Auftrag 39831)

---

## 🔴 Problem-Analyse

**Logs zeigen:**
```
⚠️ Auftrag 39831 nicht in historischen Order-Nummern. Gefunden: ['218814', '218249', ...]
Fahrzeug-Suche: Suche in letzten 180 Tagen nach Kennzeichen 'VIT-RW 56'
Anhänge-Response: 0 Anhänge, dossier_id=None
```

**Erkenntnisse:**
1. Order-Nummer-Suche durchsucht 10 Seiten (2000 Tasks) - nicht gefunden
2. Fahrzeug-Suche nach Kennzeichen sucht nur 180 Tage - möglicherweise zu kurz
3. VIN-Suche fehlt komplett

---

## ✅ Lösung (V2)

### 1. Zeitraum erweitert
- **Vorher:** 180 Tage
- **Nachher:** 365 Tage (1 Jahr)
- **Grund:** Ältere Aufträge werden jetzt gefunden

### 2. VIN-Suche hinzugefügt
- **Neu:** Suche nach VIN (eindeutiger als Kennzeichen)
- **Priorität:** VIN-Suche zuerst, dann Kennzeichen
- **Logik:** Wenn VIN passt, verwende Dossier auch wenn Order-Nummer nicht passt

### 3. GraphQL-Query erweitert
- **Vorher:** Nur `license_plate` in vehicle
- **Nachher:** `license_plate` + `vin` in vehicle

### Code-Änderungen:
```python
# VIN-Suche zuerst (eindeutiger)
if search_vin and task_vin and search_vin == task_vin:
    # VIN-Match gefunden - verwende Dossier
    dossier_id = dossier_task.get('id')
    # Auch wenn Order-Nummer nicht passt (VIN ist eindeutig)
```

---

## 📊 Erwartete Verbesserung

- **Vorher:** Nur 180 Tage, keine VIN-Suche
- **Nachher:** 365 Tage, VIN + Kennzeichen-Suche
- **Trefferquote:** Sollte deutlich höher sein

---

## 🧪 Testing

**Bitte testen:**
1. Garantieauftrag 39831 (oder anderen älteren Auftrag) öffnen
2. "Garantieakte erstellen" klicken
3. Dossier sollte jetzt gefunden werden (VIN oder Kennzeichen)

**Falls immer noch nicht gefunden:**
- Auftrag ist älter als 365 Tage → Manuelle Eingabe nötig
- Oder: VIN/Kennzeichen stimmen nicht überein → Logs prüfen

---

**Status:** ✅ Fix implementiert, Service neu gestartet
