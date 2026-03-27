# TODO FÜR CLAUDE - SESSION START TAG 176

**Erstellt:** 2026-01-09 (nach TAG 175)  
**Status:** Bereit für nächste Session

---

## 📋 ÜBERBLICK

TAG 175 hat abgeschlossen:
- ✅ Hyundai Garantie-Modul Stand geprüft
- ✅ Teilebezugsrechnung-Anforderung geprüft
- ✅ Mobis EDMOS API analysiert (Ansatz verworfen)
- ✅ Hyundai Workshop Automation HAR analysiert

**Entscheidung:** Mobis EDMOS Ansatz verworfen → ecodms API als Alternative

---

## 🔍 ZU PRÜFEN BEI SESSION-START

1. **Aktueller Stand:**
   - Prüfe `docs/hyundai/HYUNDAI_GARANTIE_MODUL_STAND_TAG175.md`
   - Prüfe `docs/hyundai/TEILEBEZUGSRECHNUNG_PRUEFUNG_TAG175.md`

2. **ecodms API:**
   - Prüfe ob ecodms API verfügbar ist
   - Dokumentation prüfen (falls vorhanden)
   - Endpunkte für Rechnungen finden

---

## 🎯 MÖGLICHE NÄCHSTE AUFGABEN

### Priorität 1: ecodms API Integration

**Ziel:** Rechnungen aus eigenem Archiv (ecodms) über API holen

**Schritte:**
1. [ ] ecodms API analysieren
   - API-Dokumentation prüfen
   - Endpunkte identifizieren
   - Authentifizierung prüfen

2. [ ] API-Client erstellen
   - `api/ecodms_api.py` erstellen
   - Endpunkt für Rechnungen implementieren
   - Fehlerbehandlung

3. [ ] In Garantieakte-Workflow integrieren
   - Rechnung zu Garantieakte hinzufügen
   - Als PDF-Anhang speichern

---

### Priorität 2: Live-Dashboard API

**Ziel:** Echte Daten aus Locosoft für Live-Dashboard

**Schritte:**
1. [ ] Daten aus Locosoft holen
   - Auftragsdaten
   - Arbeitspositionen
   - Stempelzeiten

2. [ ] Empfehlungen berechnen
   - BASICA00 prüfen
   - TT-Zeit berechnen
   - RQ0 prüfen

3. [ ] API-Endpunkt implementieren
   - `/aftersales/garantie/api/live-dashboard/<order_number>`
   - Echte Daten zurückgeben

---

### Priorität 3: Teilebezug-Integration

**Ziel:** Teilebezug in Garantieakte-Workflow integrieren

**Schritte:**
1. [ ] Mobis Teilebezug API prüfen (falls noch nötig)
   - `api/mobis_teilebezug_api.py` ist bereits erstellt
   - Testen mit echten Daten

2. [ ] Teilebezug-Liste in PDF einfügen
   - In Arbeitskarte-PDF integrieren
   - Hyundai Original-Nachweis

---

## 📝 WICHTIGE HINWEISE

- **Mobis EDMOS:** Ansatz verworfen, Dokumentation bleibt für Referenz
- **ecodms API:** Wird für Rechnungen verwendet (später)
- **Teilebezug:** Nachweis ist Pflicht, Format noch unklar

---

## 🔗 RELEVANTE DATEIEN

### Dokumentation:
- `docs/hyundai/HYUNDAI_GARANTIE_MODUL_STAND_TAG175.md` - Aktueller Stand
- `docs/hyundai/TEILEBEZUGSRECHNUNG_PRUEFUNG_TAG175.md` - Teilebezugsrechnung-Prüfung
- `docs/hyundai/MOBIS_EDMOS_DOKUMENTE_ENDPUNKTE_TAG175.md` - Mobis Analyse (Referenz)

### APIs:
- `api/arbeitskarte_api.py` - Arbeitskarte & Unterschriftsprüfung
- `api/garantieakte_workflow.py` - Garantieakte-Erstellung
- `api/mobis_teilebezug_api.py` - Mobis Teilebezug (bereit, aber nicht verwendet)

---

**Bereit für nächste Session! 🚀**
