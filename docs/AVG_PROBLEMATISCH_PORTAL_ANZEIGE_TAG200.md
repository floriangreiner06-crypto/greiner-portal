# AVG-Problematische Aufträge - Portal-Anzeige

**Datum:** 2026-01-20  
**TAG:** 200

---

## ✅ IMPLEMENTIERT

### 1. Cleanup-Script

**Datei:** `scripts/cleanup_avg_verzoegerungsgruende.py`

**Funktion:**
- Entfernt AVG-Gründe von abgerechneten Aufträgen
- Sicherheitsabfrage vor Ausführung
- Gruppiert nach AVG-Code

**Verwendung:**
```bash
python3 scripts/cleanup_avg_verzoegerungsgruende.py
# Eingabe: "ja" zum Bestätigen
```

---

### 2. Portal-Anzeige

**API-Endpunkt:** `GET /api/werkstatt/live/forecast`

**Neues Feld:** `avg_problematisch`

**Struktur:**
```json
{
  "avg_problematisch": {
    "abgerechnet": {
      "anzahl": 20,
      "auftraege": [
        {
          "auftrag_nr": 25546,
          "betrieb": 1,
          "betrieb_name": "Deggendorf",
          "avg_code": "R",
          "avg_text": "Teile im Rückstand",
          "invoice_number": 1118928,
          "invoice_date": "26.09.2024",
          "vorgabe_aw": 28.0,
          "problem": "abgerechnet"
        }
      ]
    },
    "termin_vorbei": {
      "anzahl": 43,
      "auftraege": [
        {
          "auftrag_nr": 30302,
          "betrieb": 1,
          "betrieb_name": "Deggendorf",
          "avg_code": "S",
          "avg_text": "Termin bereits vereinbart",
          "bringen_termin": "14.02.2025",
          "tage_vorbei": 340,
          "vorgabe_aw": 0.0,
          "problem": "termin_vorbei"
        }
      ]
    },
    "gesamt_problematisch": 63
  }
}
```

---

### 3. Frontend-Anzeige

**Template:** `templates/aftersales/kapazitaetsplanung.html`

**Neue Funktion:** `renderAVGProblematisch()`

**Anzeige:**
- **Warnung-Banner:** Zeigt Gesamtzahl problematischer Aufträge
- **Abgerechnete Aufträge:** Tabelle mit roter Markierung
  - Auftrag, Betrieb, AVG-Code, Rechnungsnummer, Rechnungsdatum, AW
- **Termin vorbei:** Tabelle mit gelber Markierung
  - Auftrag, Betrieb, AVG-Code, Termin, Tage vorbei (farbcodiert), AW

**Farbcodierung:**
- **Tage vorbei:**
  - > 30 Tage: Rot, fett
  - > 7 Tage: Gelb
  - ≤ 7 Tage: Grau

---

## 📊 AKTUELLE DATEN

**Betrieb 1 (Deggendorf):**
- ✅ **20 abgerechnete Aufträge** mit AVG-Grund
- ✅ **43 Aufträge** mit Termin vorbei, nicht abgerechnet
- ✅ **Gesamt: 63 problematische Aufträge**

**Beispiel abgerechnet:**
- #25546: Rechnung 1118928 vom 26.09.2024, 28 AW
- AVG: "R - Teile im Rückstand"

---

## 🔧 NÄCHSTE SCHRITTE

### Cleanup durchführen

1. **Script ausführen:**
   ```bash
   python3 scripts/cleanup_avg_verzoegerungsgruende.py
   ```

2. **Ergebnis prüfen:**
   - Script zeigt Zusammenfassung
   - AVG-Gründe werden von abgerechneten Aufträgen entfernt

3. **Portal prüfen:**
   - Nach Cleanup sollten weniger problematische Aufträge angezeigt werden
   - Abgerechnete Aufträge sollten nicht mehr in der Liste erscheinen

---

## 📝 CODE-REFERENZEN

**API:**
- `api/werkstatt_live_api.py` Zeile 1686-1794
  - `get_avg_problematische_auftraege_safe()` - Wrapper mit Fehlerbehandlung
  - `get_avg_problematische_auftraege()` - Hauptfunktion

**Frontend:**
- `templates/aftersales/kapazitaetsplanung.html`
  - Zeile 386-411: HTML-Container für problematische Aufträge
  - Zeile 816-900: `renderAVGProblematisch()` Funktion

**Scripts:**
- `scripts/cleanup_avg_verzoegerungsgruende.py` - Cleanup-Script
- `scripts/match_avg_gegen_locosoft.py` - Analyse-Script

---

**Erstellt von:** Claude AI  
**Datum:** 2026-01-20  
**TAG:** 200
