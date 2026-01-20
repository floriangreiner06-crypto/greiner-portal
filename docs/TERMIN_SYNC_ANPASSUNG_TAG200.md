# Termin-Sync Anpassung (TAG 200)

**Datum:** 2026-01-20  
**Problem:** Termine erscheinen als generische "Anlieferung"-Termine ohne Auftragsnummer/Fahrzeugdaten

---

## 🔍 PROBLEM-ANALYSE

### Beobachtung aus Screenshots:
- ✅ Termine werden erstellt (validiert per SOAP)
- ❌ Erscheinen als generische "Anlieferung"-Termine
- ❌ Keine Auftragsnummern sichtbar
- ❌ "ohne Fahrzeug" angezeigt (obwohl Fahrzeug vorhanden)
- ❌ Generischer Text: "[Anlieferung] KUS : KO - NIEDRIGER IN-USE-PERFORMANCE-RATIO EIN"

### Mögliche Ursachen:
1. **Termin-Typ:** `type: 'loose'` = lose Anlieferung (nicht als Werkstatt-Termin)
2. **Text-Feld:** Zu generisch, wird möglicherweise überschrieben
3. **Fehlende Parameter:** `comment`, `bringServiceAdvisor` fehlen
4. **Verknüpfung:** `workOrderNumber` wird möglicherweise nicht richtig angezeigt

---

## ✅ DURCHGEFÜHRTE ÄNDERUNGEN

### 1. Termin-Typ geändert:
```python
# VORHER:
'type': 'loose'  # Lose Anlieferung

# NACHHER:
'type': 'fix'  # Fester Werkstatt-Termin
```

### 2. Text-Feld angepasst:
```python
# VORHER:
'text': f'Termin aus Gudat (Test) - Auftrag: {auftrag_nr or "neu"}'

# NACHHER:
'text': f'Auftrag #{auftrag_nr}' if auftrag_nr else 'Neuer Termin'
```

### 3. Comment-Feld hinzugefügt:
```python
'comment': f'Gudat-Sync - Auftrag {auftrag_nr}' if auftrag_nr else 'Gudat-Sync'
```

### 4. Serviceberater hinzugefügt:
```python
# Hole Serviceberater aus Auftrag
if 'serviceberater_nr' in locals() and serviceberater_nr:
    appointment_data['bringServiceAdvisor'] = serviceberater_nr
```

### 5. Erweiterte Auftragsdaten:
```python
# Hole zusätzlich:
- service_advisor (Serviceberater-Nr)
- manufacturer (Hersteller)
- model (Modell)
```

---

## 🧪 NÄCHSTER TEST

**Bitte erneut testen:**
```bash
POST /api/gudat-locosoft/test-sync-termin
{
  "auftrag_nr": 40167,
  "date": "2026-01-22",
  "time": "09:00"
}
```

**Erwartetes Ergebnis:**
- ✅ Termin als "fix" (fester Werkstatt-Termin)
- ✅ Text: "Auftrag #40167"
- ✅ Comment: "Gudat-Sync - Auftrag 40167"
- ✅ Serviceberater zugeordnet (falls vorhanden)
- ✅ Fahrzeugdaten sollten sichtbar sein

---

## ⚠️ HINWEIS

Falls Termine weiterhin als generische "Anlieferung" erscheinen:
1. **Locosoft-Konfiguration prüfen:** Möglicherweise werden Termine mit `workOrderNumber` anders behandelt
2. **Termin-Ansicht prüfen:** In Locosoft möglicherweise andere Ansicht/Filter aktiv
3. **SOAP-Parameter prüfen:** Möglicherweise fehlen weitere Parameter für vollständige Verknüpfung
