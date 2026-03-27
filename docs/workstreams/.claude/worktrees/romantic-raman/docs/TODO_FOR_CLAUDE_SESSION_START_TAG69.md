# TODO FÜR CLAUDE - SESSION START TAG69

**Datum:** 2025-11-20  
**Letzter Stand:** TAG68 abgeschlossen  
**Nächster Schritt:** Detail-Scraping für Service Box Bestellungen

---

## 🎯 HAUPT-AUFGABE

### **SERVICE BOX DETAIL-SCRAPER ENTWICKELN**

#### Was wurde bisher erreicht:
✅ Basic Scraper funktioniert (50 Bestellnummern gescraped)  
✅ Pagination durch 5 Seiten funktioniert  
✅ JSON-Export vorhanden

#### Was fehlt noch:
❌ Detail-Daten pro Bestellung scrapen  
❌ Tabelle "Einzelheiten der Bestellung" extrahieren  
❌ Strukturierte Speicherung aller Felder

---

## 📋 REQUIREMENTS

### Zu scrapende Daten:

**1. Informationen-Block:**
```
Absender:
  - Code Vertragspartner
  - Name
  - Adresse
  - Telefon
  - Benutzer

Empfänger:
  - Code Vertragspartner
  - Name
  - Adresse
  - Telefon
  - Benutzer
```

**2. Historie der Bestellung:**
```
- Bestelldatum (z.B. 19.11.25, 08:09 GMT+0)
- Bestätigungsdatum
- Letzte Rückmeldung DMS (Text)
```

**3. Einzelheiten der Bestellung (Tabelle):**
```
Pro Position:
  - Teilenummer (z.B. 1635290880)
  - Beschreibung (z.B. DICHTMASSE)
  - Menge (bestellt)
  - Menge in Lieferung
  - Menge in Bestellung
  - Preis ohne MwSt
  - Preis mit MwSt
  - Summe inkl. MwSt
  - Grund Ablehnung
```

**4. Summen:**
```
- Summe zzgl. MwSt
- Summe inkl. MwSt
```

---

## 🔧 TECHNISCHE UMSETZUNG

### Navigation-Flow:
```
1. Bestehenden Scraper laden (servicebox_scraper_complete.py)
2. Nach Scrapen der Liste: Iteration durch alle Bestellnummern
3. Pro Bestellung:
   - Klick auf Bestellnummer-Link
   - Warte auf Detail-Seite
   - Extrahiere alle Felder
   - Zurück-Navigation
   - Nächste Bestellung
4. Alle Details in JSON speichern
```

### Output-Struktur (JSON):
```json
{
  "timestamp": "2025-11-20T16:10:00",
  "anzahl_bestellungen": 50,
  "bestellungen": [
    {
      "bestellnummer": "1JADJCRS",
      "status": "Bestätigt",
      "absender": {
        "code": "DE08250",
        "name": "AUTOHAUS GREINER GMBH CO. KG",
        "adresse": "...",
        "telefon": "0991/25013-0",
        "benutzer": "BRUNO WIELAND (DD67364)"
      },
      "empfaenger": {
        "code": "DE10XX0",
        "name": "BTZ BAYERISCHES TEILEZENTRUM GMBH",
        "adresse": "...",
        "telefon": "0049 893 7003",
        "benutzer": "automatische Bestätigung"
      },
      "historie": {
        "bestelldatum": "2025-11-19T08:09:00+01:00",
        "bestaetigungsdatum": "2025-11-19T08:09:00+01:00",
        "letzte_rueckmeldung": "..."
      },
      "positionen": [
        {
          "teilenummer": "1635290880",
          "beschreibung": "DICHTMASSE",
          "menge": 2.00,
          "menge_in_lieferung": 2.00,
          "menge_in_bestellung": 0.00,
          "preis_ohne_mwst": 21.79,
          "preis_mit_mwst": 25.93,
          "summe_inkl_mwst": 51.86,
          "grund_ablehnung": ""
        }
      ],
      "summe_zzgl_mwst": 3422.80,
      "summe_inkl_mwst": 4072.87
    }
  ]
}
```

---

## 📁 DATEIEN

### Zu erstellen:
- `tools/scrapers/servicebox_detail_scraper.py` (NEU)

### Output:
- `logs/servicebox_bestellungen_details.json`
- `logs/servicebox_detail_screenshots/` (für Debugging)

---

## ⚠️ WICHTIGE HINWEISE

1. **Bestehende Struktur nutzen:**
   - Login & Navigation aus `servicebox_scraper_complete.py` wiederverwenden
   - Frame-Handling beibehalten
   - Credentials aus `config/credentials.json` laden

2. **Error-Handling:**
   - Nicht alle Bestellungen haben alle Felder
   - Manche Positionen könnten leer sein
   - Try-Except für jedes Feld

3. **Performance:**
   - 50 Bestellungen × ~3 Sekunden = ~150 Sekunden
   - Progress-Anzeige einbauen
   - Bei Fehler: Weiter mit nächster Bestellung

4. **Debugging:**
   - Screenshots bei jeder Detail-Seite
   - HTML-Dumps der ersten 3 Bestellungen
   - Ausführliches Logging

---

## 🚀 QUICK START FÜR CLAUDE

```bash
# 1. In Projekt-Verzeichnis wechseln
cd /opt/greiner-portal

# 2. Session Wrap-Up lesen
cat SESSION_WRAP_UP_TAG68.md

# 3. Letzte JSON-Daten prüfen
cat logs/servicebox_bestellungen.json

# 4. Bestehenden Scraper als Basis ansehen
cat tools/scrapers/servicebox_scraper_complete.py

# 5. Detail-Scraper entwickeln
# → Datei: tools/scrapers/servicebox_detail_scraper.py
```

---

## 🎯 DEFINITION OF DONE

- [ ] Scraper läuft durch alle 50 Bestellungen
- [ ] Alle Felder werden korrekt extrahiert
- [ ] JSON ist valide und strukturiert
- [ ] Error-Handling funktioniert
- [ ] Progress-Anzeige vorhanden
- [ ] Screenshots zur Validierung erstellt
- [ ] Dokumentation aktualisiert

---

**NÄCHSTE STEPS:**
1. Detail-Scraper entwickeln
2. Testen mit 3 Bestellungen
3. Auf alle 50 Bestellungen ausweiten
4. Validieren
5. Eventuell DB-Integration (später)

**Erstellt:** 2025-11-20 16:05  
**Für Session:** TAG69
