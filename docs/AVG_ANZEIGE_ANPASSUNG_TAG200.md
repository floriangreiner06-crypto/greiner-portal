# AVG-Anzeige Anpassung - Abgerechnete Aufträge ausblenden

**Datum:** 2026-01-20  
**TAG:** 200

---

## 📋 ÄNDERUNG

**Hinweis vom Benutzer:**
> "Der AVG-Grund bleibt erhalten, wird nach Abrechnung nicht mehr bearbeitet. Es gibt eigentlich keinen Grund mehr die anzuzeigen."

**Konsequenz:**
- Abgerechnete Aufträge werden **nicht mehr im Portal angezeigt**
- Nur noch Aufträge mit **Termin vorbei, nicht abgerechnet** werden angezeigt
- Cleanup-Script bleibt verfügbar für manuelle Bereinigung

---

## ✅ DURCHGEFÜHRTE ÄNDERUNGEN

### 1. Frontend (`templates/aftersales/kapazitaetsplanung.html`)

**Vorher:**
- Zeigte beide Kategorien: Abgerechnet + Termin vorbei
- Warnung mit beiden Zahlen

**Nachher:**
- Zeigt nur noch: Termin vorbei, nicht abgerechnet
- Warnung nur mit relevanter Zahl
- Info-Text: "Diese sollten abgerechnet oder der AVG-Grund aktualisiert werden"

**Code:**
```javascript
// Nur Termin vorbei anzeigen (abgerechnete werden ignoriert)
const terminVorbei = problematischData.termin_vorbei || {};
const anzahlTerminVorbei = terminVorbei.anzahl || 0;
```

### 2. API (`api/werkstatt_live_api.py`)

**Anpassung:**
- `abgerechnet.auftraege` wird als leeres Array zurückgegeben
- `gesamt_problematisch` zählt nur noch Termin vorbei

**Code:**
```python
return {
    'abgerechnet': {
        'anzahl': len(abgerechnet_liste),
        'auftraege': []  # Nicht mehr anzeigen
    },
    'termin_vorbei': {
        'anzahl': len(termin_vorbei_liste),
        'auftraege': termin_vorbei_liste[:50]
    },
    'gesamt_problematisch': len(termin_vorbei_liste)  # Nur Termin vorbei zählt
}
```

---

## 📊 ERGEBNIS

**Vorher:**
- 108 problematische Aufträge (28 abgerechnet + 80 Termin vorbei)

**Nachher:**
- 80 problematische Aufträge (nur Termin vorbei)
- Abgerechnete werden nicht mehr angezeigt

---

## 🔧 CLEANUP-SCRIPT

**Bleibt verfügbar:**
- `scripts/cleanup_avg_verzoegerungsgruende.py`
- Kann manuell ausgeführt werden, um AVG-Gründe von abgerechneten Aufträgen zu entfernen
- Wird nicht automatisch ausgeführt

---

**Erstellt von:** Claude AI  
**Datum:** 2026-01-20  
**TAG:** 200
