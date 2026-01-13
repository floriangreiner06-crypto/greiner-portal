# Cognos Authentifizierung - Hilfe benötigt

**Datum:** 2026-01-12  
**Problem:** SOAP-Client kann nicht authentifizieren (Status 441)

---

## 🎯 ZIEL

BWA-Reports mit spezifischen Filtern aus Cognos abrufen:
- ✅ Einzelne Standorte (Landau, Deggendorf, Hyundai)
- ✅ Aufgedrillte Details
- ✅ Verschiedene Zeiträume

---

## 📋 OPTIONEN

### Option 1: Neue HAR-Datei (Empfohlen)

**Bitte erstelle eine neue HAR-Datei mit:**

1. **Landau einzeln:**
   - Filter: Nur Landau
   - Zeitraum: Dezember 2025
   - Aufgedrillt (wenn möglich)

2. **Deggendorf Opel einzeln:**
   - Filter: Nur Deggendorf (Opel)
   - Zeitraum: Dezember 2025
   - Aufgedrillt (wenn möglich)

3. **Deggendorf Hyundai einzeln:**
   - Filter: Nur Deggendorf HYU
   - Zeitraum: Dezember 2025
   - Aufgedrillt (wenn möglich)

**Vorgehen:**
1. Browser DevTools öffnen (F12)
2. Network-Tab aktivieren
3. HAR aufzeichnen
4. Report mit Filter aufrufen
5. HAR speichern

**Speichern als:**
- `f03_bwa_landau_dez2025.har`
- `f03_bwa_deggendorf_opel_dez2025.har`
- `f03_bwa_deggendorf_hyundai_dez2025.har`

---

### Option 2: Session-Daten teilen

**Wenn HAR nicht möglich, bitte teilen:**

1. **XSRF-Token** (aus Browser DevTools → Application → Cookies)
   - Name: `XSRF-TOKEN`
   - Wert: `...`

2. **Session-Cookies** (falls vorhanden)
   - Alle Cookies von `10.80.80.10:9300`

3. **Oder:** Aktuelle Browser-Session exportieren (z.B. als Cookie-JAR)

---

### Option 3: Selenium-Setup

**Falls Option 1 & 2 nicht möglich:**

Ich kann einen Selenium-basierten Scraper erstellen, der:
- Browser öffnet
- Automatisch einloggt
- Reports aufruft
- Daten extrahiert

**Benötigt:**
- Selenium installiert
- Chrome/Chromium Driver
- Login-Credentials

---

## 🚀 EMPFEHLUNG

**Option 1 (HAR-Datei) ist am einfachsten:**
- ✅ Keine Code-Änderungen nötig
- ✅ Funktioniert sofort
- ✅ Enthält alle benötigten Daten

**Bitte erstelle HAR-Dateien für:**
1. Landau (Dezember 2025)
2. Deggendorf Opel (Dezember 2025)
3. Deggendorf Hyundai (Dezember 2025)

---

## 📝 NÄCHSTE SCHRITTE

Sobald HAR-Dateien vorhanden:
1. ✅ HTML-Responses extrahieren
2. ✅ BWA-Werte parsen
3. ✅ Mit DRIVE vergleichen
4. ✅ Differenzen identifizieren
