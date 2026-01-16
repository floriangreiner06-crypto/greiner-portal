# Fahrzeugbeschreibung-Generierung mit KI - TAG 195

**Erstellt:** 2026-01-16  
**Use Case:** Verkauf - Fahrzeugbeschreibung für Verkaufsplattformen  
**Status:** ✅ Implementiert - Bereit für Testing

---

## 🎯 ÜBERBLICK

**Problem:**
- Fahrzeugbeschreibungen müssen manuell geschrieben werden
- Zeitaufwendig: **10-15 Min pro Fahrzeug**
- Inkonsistente Qualität
- SEO-Optimierung fehlt oft

**KI-Lösung:**
- ✅ Automatische Generierung von marktgerechten Beschreibungen
- ✅ Verkaufsargumente extrahieren
- ✅ SEO-Keywords generieren
- ✅ Konsistente Qualität

**ROI:** ~1.500€/Jahr (10 Fahrzeuge/Monat × 12 Min × 12 Monate)

---

## 📋 API-ENDPOINT

### POST `/api/ai/generiere/fahrzeugbeschreibung/<dealer_vehicle_number>`

**Beschreibung:** Generiert eine professionelle Fahrzeugbeschreibung basierend auf Fahrzeugdaten aus Locosoft.

**Parameter:**
- `dealer_vehicle_number` (int, URL-Parameter) - Locosoft dealer_vehicle_number

**Request:**
```bash
curl -X POST http://localhost:5000/api/ai/generiere/fahrzeugbeschreibung/12345 \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..."
```

**Response:**
```json
{
  "success": true,
  "dealer_vehicle_number": 12345,
  "fahrzeug": {
    "marke": "Hyundai",
    "modell": "i30",
    "fahrzeugtyp": "Gebrauchtwagen",
    "erstzulassung": "03/2020",
    "kilometerstand": "45.000 km",
    "verkaufspreis": "18.500,00 €",
    "standzeit_tage": 45
  },
  "beschreibung": {
    "haupttext": "Professionelle Beschreibung...",
    "verkaufsargumente": [
      "Niedrige Laufleistung",
      "Gepflegter Zustand",
      "Erstzulassung 2020"
    ],
    "seo_keywords": [
      "Hyundai i30",
      "Gebrauchtwagen",
      "2020",
      "Niedrige Laufleistung"
    ],
    "zusammenfassung": "Kurze Zusammenfassung...",
    "rohe_antwort": "..."
  }
}
```

---

## 🔧 DATENQUELLEN

**Locosoft-Tabellen:**
- `dealer_vehicles` - Bestand, Kalkulation, Preise
- `vehicles` - Stammdaten (VIN, Modell, Marke, EZ, KM-Stand)
- `makes` - Marken
- `models` - Modell-Details

**Verwendete Felder:**
- Marke (`makes.description`)
- Modell (`vehicles.free_form_model_text` oder `models.description`)
- Fahrzeugtyp (`dealer_vehicle_type`: G/N/D/V/T/L)
  - **WICHTIG:** `V` = Vorführwagen (nicht Vermietwagen!)
  - `D` = Vorführwagen (Demo)
  - `G` = Gebrauchtwagen
  - `N` = Neuwagen
  - `T` = Tauschfahrzeug
  - `L` = Leihgabe/Mietwagen
- Erstzulassung (`vehicles.first_registration_date`)
- Kilometerstand (`vehicles.mileage_km`)
- Verkaufspreis (`dealer_vehicles.out_sale_price`)
- Standzeit (`CURRENT_DATE - in_arrival_date`)
- VIN (`vehicles.vin`)

---

## 🧪 TESTING

### 1. Test mit echtem Fahrzeug

**Schritt 1:** Finde ein Test-Fahrzeug
```sql
SELECT dealer_vehicle_number, free_form_model_text, first_registration_date, mileage_km
FROM dealer_vehicles dv
LEFT JOIN vehicles v ON dv.vehicle_number = v.internal_number
WHERE dv.out_invoice_date IS NULL  -- Noch nicht verkauft
  AND dv.dealer_vehicle_type = 'G'  -- Gebrauchtwagen
LIMIT 1;
```

**Schritt 2:** API-Call testen
```bash
curl -X POST http://localhost:5000/api/ai/generiere/fahrzeugbeschreibung/12345 \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..."
```

**Schritt 3:** Ergebnis prüfen
- Beschreibung lesbar und professionell?
- Verkaufsargumente relevant?
- SEO-Keywords passend?
- Keine negativen Formulierungen?

### 2. Test mit verschiedenen Fahrzeugtypen

- **Gebrauchtwagen (G):** Standard-Test
- **Neuwagen (N):** Andere Argumente (Neuheit, Garantie)
- **Vorführwagen (D):** Betonung auf "wie neu"
- **Lange Standzeit:** Positive Formulierung

---

## 📊 PROMPT-ENGINEERING

**System-Prompt:**
```
Du bist ein Experte für Fahrzeugverkauf und Autohaus-Marketing. 
Du schreibst professionelle, ansprechende Fahrzeugbeschreibungen 
für Verkaufsplattformen.
```

**User-Prompt enthält:**
- Alle Fahrzeugdaten (Marke, Modell, EZ, KM, Preis, Standzeit)
- Anforderungen (Länge, Stil, SEO)
- Format (JSON mit Beschreibung, Argumente, Keywords)

**Temperature:** 0.7 (etwas kreativer für Beschreibungen)

**Max Tokens:** 800 (für vollständige Beschreibung + Argumente)

**Modell:** `mistralai/magistral-small-2509` (alternatives Modell für bessere JSON-Ausgabe)
- Standard-Modell (`allenai/olmo-3-32b-think`) ist ein "think"-Modell, das Denkprozess statt direkter Antwort ausgibt
- Alternatives Modell liefert bessere strukturierte JSON-Antworten

**Elektrofahrzeug-Erkennung:**
- Automatische Erkennung bei Modell-Namen mit: "ioniq", "kona electric", "electric", "ev", "e-", "elektro"
- Bei Elektrofahrzeugen: Erwähnung von Reichweite, Ladeleistung, Ausstattung (z.B. Ioniq 5: ~480 km WLTP, 800V-System)
- Modell-Name wird extrahiert (z.B. "Ioniq 5" statt nur "Hyundai")

---

## 🎨 FRONTEND-INTEGRATION (Geplant)

**Mögliche Integration-Punkte:**
1. **GW-Bestand-Ansicht** (`templates/verkauf/gw_bestand.html`)
   - Button "Beschreibung generieren" pro Fahrzeug
   - Modal mit generierter Beschreibung
   - Copy-to-Clipboard für Verkaufsplattformen

2. **Fahrzeug-Detail-Ansicht**
   - Automatische Beschreibung beim Öffnen
   - Editierbar (falls Anpassungen nötig)
   - Export als Text/PDF

3. **Batch-Generierung**
   - Mehrere Fahrzeuge auf einmal
   - Export als CSV/Excel

---

## ✅ QUALITÄTSKRITERIEN

**Gute Beschreibung:**
- ✅ 150-250 Wörter
- ✅ Professionell und vertrauenswürdig
- ✅ Relevante Verkaufsargumente
- ✅ SEO-optimiert (natürlich)
- ✅ Keine negativen Formulierungen
- ✅ Marke, Modell, EZ, KM erwähnt

**Schlechte Beschreibung:**
- ❌ Zu kurz (< 100 Wörter)
- ❌ Zu lang (> 400 Wörter)
- ❌ Generische Phrasen
- ❌ Negative Formulierungen
- ❌ Fehlende relevante Daten

---

## 🔄 NÄCHSTE SCHRITTE

### Kurzfristig (TAG 196)
1. [ ] Testing mit echten Fahrzeugen
2. [ ] Feedback sammeln
3. [ ] Prompt-Optimierung (falls nötig)

### Mittelfristig (TAG 197+)
4. [ ] Frontend-Integration (GW-Bestand)
5. [ ] Copy-to-Clipboard Feature
6. [ ] Batch-Generierung
7. [ ] Export-Funktionen

### Langfristig
8. [ ] Automatische Generierung bei Fahrzeug-Eingang
9. [ ] Integration mit Verkaufsplattformen (API)
10. [ ] Mehrsprachigkeit (DE/EN)

---

## 📝 BEISPIEL-OUTPUT

**Eingabe:**
- Marke: Hyundai
- Modell: i30
- Typ: Gebrauchtwagen
- EZ: 03/2020
- KM: 45.000
- Preis: 18.500€
- Standzeit: 45 Tage

**Test-Ergebnis (VIN: KMHKN81BFRU284185):**
- ✅ Fahrzeug gefunden (dealer_vehicle_number: 211151)
- ✅ Beschreibung generiert
- ✅ JSON erfolgreich geparst
- ✅ Verkaufsargumente extrahiert
- ✅ SEO-Keywords generiert
- ✅ Typ-Mapping korrigiert: `V` = Vorführwagen (nicht Vermietwagen!)

**Ausgabe (Beispiel):**
```json
{
  "beschreibung": "Dieser gepflegte Hyundai i30 aus dem Jahr 2020 überzeugt mit einer niedrigen Laufleistung von nur 45.000 km und einem ausgezeichneten Zustand. Das Fahrzeug wurde regelmäßig gewartet und steht für eine zuverlässige und sparsame Fahrt. Mit seiner modernen Ausstattung und dem zeitlosen Design ist dieser i30 ideal für alle, die Wert auf Qualität und Komfort legen. Der Wagen ist sofort verfügbar und kann nach Terminvereinbarung besichtigt werden.",
  "verkaufsargumente": [
    "Niedrige Laufleistung (45.000 km)",
    "Erstzulassung 2020 - noch sehr jung",
    "Gepflegter Zustand",
    "Sofort verfügbar",
    "Regelmäßige Wartung"
  ],
  "seo_keywords": [
    "Hyundai i30",
    "Gebrauchtwagen",
    "2020",
    "Niedrige Laufleistung",
    "45.000 km",
    "Gepflegter Zustand"
  ],
  "zusammenfassung": "Gepflegter Hyundai i30 von 2020 mit nur 45.000 km - sofort verfügbar!"
}
```

---

## 🔗 RELEVANTE DATEIEN

**Code:**
- `api/ai_api.py` - Endpoint `/api/ai/generiere/fahrzeugbeschreibung/<id>`
- `api/fahrzeug_data.py` - Fahrzeugdaten (kann für Erweiterungen genutzt werden)

**Dokumentation:**
- `docs/KI_USE_CASES_GREINER_AUTOHAUS_TAG195.md` - Use Cases Übersicht
- `docs/LM_STUDIO_INTEGRATION_DOKUMENTATION_TAG195.md` - LM Studio Integration

---

## ✅ STATUS

**TAG 195:**
- ✅ API-Endpoint implementiert
- ✅ Datenabfrage aus Locosoft
- ✅ KI-Prompt erstellt
- ✅ JSON-Parsing mit Fallback
- ⏳ Testing mit echten Daten
- ⏳ Frontend-Integration (geplant)

**Bereit für:** Testing und Feedback

---

**Erstellt:** TAG 195  
**Status:** Implementiert, bereit für Testing
