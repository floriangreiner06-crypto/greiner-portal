# Cognos Authentifizierung - Status TAG 182

**Datum:** 2026-01-12  
**Problem:** SOAP-Requests schlagen mit Status 441 (Unauthorized) fehl

---

## 🔍 VERSUCHTE ANSÄTZE

### ✅ Funktioniert:
- **Basic Auth** für Hauptseite (`/bi/`)
- **Basic Auth** für Report-App (`/bi/pat/rsapp.htm`)
- **XSRF-Token** wird extrahiert
- **Cookies** werden gesetzt

### ❌ Funktioniert nicht:
- **SOAP-Requests** (`POST /bi/v1/reports`) → Status 441
- Auch mit Basic Auth + XSRF-Token

---

## 💡 HYPOTHESE

Cognos benötigt für SOAP-Requests eine **aktive Browser-Session**, nicht nur Basic Auth + XSRF-Token.

Mögliche Gründe:
1. **Session-Cookie** fehlt (nicht nur XSRF-Token)
2. **Authenticity-Token** im SOAP-Header muss gültig sein
3. **Context-ID** muss mit aktiver Session verknüpft sein
4. **JavaScript-basierte Authentifizierung** wird benötigt

---

## 🚀 LÖSUNGSANSÄTZE

### Option 1: Selenium (Empfohlen)
**Browser-Automation:**
- Öffnet echten Browser
- Loggt sich ein
- Ruft Reports auf
- Extrahiert Daten

**Vorteile:**
- ✅ Funktioniert garantiert
- ✅ Nutzt echte Browser-Session
- ✅ Kann JavaScript ausführen

**Nachteile:**
- ⚠️ Benötigt Browser + Driver
- ⚠️ Langsamer als direkte Requests

---

### Option 2: Session-Cookies aus Browser
**Manuell:**
- Browser DevTools öffnen
- Cookies exportieren
- In Script verwenden

**Vorteile:**
- ✅ Schnell
- ✅ Keine zusätzlichen Tools

**Nachteile:**
- ⚠️ Cookies laufen ab
- ⚠️ Muss regelmäßig erneuert werden

---

### Option 3: HAR-Dateien (Aktuell)
**Bereits vorhanden:**
- HTML-Responses extrahieren
- BWA-Werte parsen

**Vorteile:**
- ✅ Funktioniert sofort
- ✅ Keine Authentifizierung nötig

**Nachteile:**
- ⚠️ Nur für bereits aufgerufene Reports
- ⚠️ Keine neuen Filter möglich

---

## 📋 EMPFEHLUNG

**Für sofortige Nutzung:**
- ✅ HAR-Dateien verwenden (bereits vorhanden)
- ✅ HTML-Responses extrahieren
- ✅ BWA-Werte parsen

**Für langfristige Lösung:**
- ✅ Selenium-Scraper implementieren
- ✅ Automatisch Reports mit verschiedenen Filtern aufrufen
- ✅ Daten extrahieren

---

## 🎯 NÄCHSTE SCHRITTE

1. **Sofort:** HTML aus HAR extrahieren und BWA-Werte parsen
2. **Parallel:** Selenium-Setup vorbereiten
3. **Dann:** Selenium-Scraper implementieren
