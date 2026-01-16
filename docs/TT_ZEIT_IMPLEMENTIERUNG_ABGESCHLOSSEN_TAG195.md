# TT-Zeit-Optimierung: Implementierung abgeschlossen - TAG 195

**Datum:** 2026-01-16  
**Status:** ✅ Implementiert (ohne automatische Prüfung)

---

## ✅ IMPLEMENTIERT

### API-Endpoint

**Datei:** `api/ai_api.py`

**Endpoint:**
```
POST /api/ai/analysiere/tt-zeit/<auftrag_id>
```

**Funktionen:**
1. ✅ Technische Prüfung (automatisch)
   - Garantieauftrag?
   - Stempelzeiten vorhanden?
   - TT-Zeit bereits eingereicht?
   - Schadhaften Teil identifiziert?

2. ✅ KI-Analyse (automatisch)
   - Begründung generieren
   - Empfehlung geben
   - Bewertung (hoch/mittel/niedrig)
   - Hinweise

3. ✅ Warnung für manuelle Prüfung
   - Hinweis: "Bitte im GSW Portal prüfen!"
   - Teilenummer anzeigen

4. ✅ Abrechnungsregeln
   - Bis 0,9 Stunden (9 AW): Ohne Freigabe
   - Ab 1,0 Stunden (10 AW): Freigabe erforderlich

---

## 📋 HILFSFUNKTIONEN

### `check_garantieauftrag(auftrag_id)`
- Prüft ob Auftrag ein Garantieauftrag ist
- Prüft `charge_type = 60` oder `labour_type IN ('G', 'GS')` oder `invoice_type = 6`

### `hole_schadhaftes_teil(auftrag_id)`
- Identifiziert schadhaften Teil aus `loco_parts` (invoice_type = 6)
- Gibt Teilenummer, Beschreibung, Menge zurück

### `get_stempelzeiten(auftrag_id)`
- Holt Stempelzeiten aus `loco_times` (type = 2)
- Gibt Anzahl und Dauer in Minuten zurück

### `check_tt_zeit_vorhanden(auftrag_id)`
- Prüft ob TT-Zeit bereits eingereicht wurde
- Sucht nach `labour_operation_id LIKE '%RTT'` oder `'%HTT'`

### `get_auftrag_info(auftrag_id)`
- Holt grundlegende Auftragsinformationen
- Gibt Nummer, Datum, Standort, Kennzeichen, VIN, Marke zurück

---

## 📊 RESPONSE-FORMAT

```json
{
  "success": true,
  "auftrag_id": 202665,
  "auftrag_info": {
    "nummer": 202665,
    "datum": "2023-03-13",
    "standort": 2,
    "kennzeichen": "DEG-CM 169",
    "vin": "KMHKR81CPNU005366",
    "marke": "Hyundai"
  },
  "technische_pruefung": {
    "is_garantie": true,
    "stempelzeiten_vorhanden": true,
    "stempelzeiten_anzahl": 3,
    "stempelzeiten_minuten": 125.5,
    "stempelzeiten_stunden": 2.09,
    "tt_zeit_vorhanden": false,
    "schadhaftes_teil": {
      "teilenummer": "98850J7500",
      "beschreibung": "Teil XYZ",
      "menge": 1,
      "abgerechnet": false,
      "position": 1
    }
  },
  "ki_analyse": {
    "begruendung": "Komplexe Diagnose erforderlich...",
    "empfehlung": "TT-Zeit prüfen",
    "bewertung": "hoch",
    "hinweise": ["Hinweis 1", "Hinweis 2"]
  },
  "warnung": {
    "manuelle_pruefung_erforderlich": true,
    "text": "⚠️ WICHTIG: Bitte im GSW Portal prüfen, ob für Teil 98850J7500 eine Arbeitsoperationsnummer mit Vorgabezeit vorhanden ist!",
    "hinweis": "TT-Zeit ist nur möglich, wenn KEINE Arbeitsoperationsnummer mit Vorgabezeit im GSW Portal vorhanden ist!"
  },
  "tt_zeit_moeglich": null,
  "abrechnungsregeln": {
    "bis_09_stunden": {
      "max_aw": 9,
      "max_minuten": 54,
      "max_stunden": 0.9,
      "verguetung_max": 75.87,
      "freigabe_erforderlich": false
    },
    "ab_10_stunden": {
      "min_aw": 10,
      "min_minuten": 60,
      "min_stunden": 1.0,
      "freigabe_erforderlich": true,
      "freigabe_ueber": "GWMS (Antragstyp: T, Freigabetyp: DK)"
    }
  }
}
```

---

## 🎯 NÄCHSTE SCHRITTE

### 1. Frontend-Integration ⏳

**Benötigt:**
- Button in Arbeitskarte-Ansicht
- Modal mit:
  - Technische Prüfung anzeigen
  - KI-Analyse anzeigen
  - Warnung anzeigen
  - Bestätigungs-Button: "✅ GSW Portal geprüft - Keine Arbeitsoperationsnummer"

**Beispiel:**
```html
<button onclick="pruefeTTZeit({{ auftrag_id }})">
    TT-Zeit prüfen
</button>
```

### 2. Bestätigung speichern ⏳

**Optional (später):**
- Datenbank-Tabelle für Prüfungen
- Speichere: "TT-Zeit abgerechnet für Teil X"
- Speichere: "Manuelle Prüfung bestätigt"
- Speichere: "KI-Empfehlung: ..."

### 3. Testing ⏳

**Zu testen:**
- API-Endpoint mit echten Aufträgen
- KI-Analyse funktioniert
- Alle Prüfungen korrekt

---

## 📝 ZUSAMMENFASSUNG

**Implementiert:**
- ✅ API-Endpoint für TT-Zeit-Analyse
- ✅ Technische Prüfung (automatisch)
- ✅ KI-Analyse (Begründung, Empfehlung)
- ✅ Warnung für manuelle Prüfung
- ✅ Abrechnungsregeln

**Noch zu tun:**
- ⏳ Frontend-Integration
- ⏳ Bestätigung speichern (optional)
- ⏳ Testing

**Status:** ✅ Backend fertig, Frontend folgt

---

**Erstellt:** TAG 195  
**Status:** Implementierung abgeschlossen, bereit für Frontend-Integration
