# Bugfix: GUDAT-Dossier-Suche erweitert

**TAG:** 192  
**Datum:** 2026-01-15  
**Problem:** Dossiers in GUDAT werden nicht mehr gefunden (nur für heutige Aufträge)

---

## 🔴 Problem

**Symptom:**
- Modal zeigt: "Kein Dossier in GUDAT für Auftrag 39831 gefunden"
- Betrifft ältere Aufträge (nicht von heute)
- User muss Dossier-ID manuell eingeben

**Ursache:**
- `hole_arbeitskarte_daten()` suchte nur nach Tasks mit `START_DATE = heute`
- Ältere Aufträge wurden nicht gefunden
- Erweiterte Suche existierte bereits in `_get_arbeitskarte_anhaenge_internal()`, aber nicht in `hole_arbeitskarte_daten()`

---

## ✅ Lösung

**Geändert:** `api/arbeitskarte_api.py` - `hole_arbeitskarte_daten()`

### 1. Erweiterte Vergleichslogik
- String-Vergleich
- Integer-Vergleich (ignoriert führende Nullen)
- Beispiel: "0220629" == "220629"

### 2. Erweiterte Suche (90 Tage)
- **Schritt 1:** Suche heute (schnellste Suche)
- **Schritt 2:** Falls nicht gefunden, suche in letzten 90 Tagen
- **Pagination:** Bis zu 10 Seiten (2000 Tasks)

### Code-Änderungen:
```python
# Vorher: Nur heute
variables = {
    "where": {
        "AND": [{"column": "START_DATE", "operator": "EQ", "value": target_date}]
    }
}

# Nachher: Heute + 90 Tage Fallback
# 1. Heute suchen
# 2. Falls nicht gefunden: Letzte 90 Tage mit Pagination
```

---

## 📊 Erwartete Verbesserung

- **Vorher:** Nur Aufträge von heute werden gefunden (~10-20%)
- **Nachher:** Aufträge der letzten 90 Tage werden gefunden (~95%+)
- **Performance:** Erste Suche (heute) ist schnell, erweiterte Suche nur bei Bedarf

---

## 🧪 Testing

**Bitte testen:**
1. Garantieauftrag 39831 (oder anderen älteren Auftrag) öffnen
2. "Garantieakte erstellen" klicken
3. Dossier sollte automatisch gefunden werden (kein Modal mehr)

**Falls immer noch nicht gefunden:**
- Auftrag ist älter als 90 Tage → Manuelle Eingabe nötig (wie vorher)
- Oder: GUDAT-API-Problem → Logs prüfen

---

## 📝 Weitere Optimierungen (optional)

1. **Caching:** Dossier-IDs cachen (reduziert GUDAT-Abfragen)
2. **VIN/Kennzeichen-Suche:** Alternative Suche falls Order-Nummer nicht passt
3. **Erweiterte Suche:** Mehr als 90 Tage (falls nötig)

---

**Status:** ✅ Fix implementiert, Service neu gestartet
