# Mobis EDMOS Selenium-Analyse - Ergebnisse

**Datum:** 2026-01-09 (TAG 175)  
**Methode:** Selenium mit Chrome (headless) + Performance Logging

---

## ✅ ERFOLGREICH DURCHGEFÜHRT

### 1. Login-Prozess
- ✅ **Login erfolgreich!**
- ✅ **Login-Felder identifiziert:**
  - Username: `mainframe.VFrameSet.frameLogin.form.divLogin.form.div_login.form.edUserId:input`
  - Password: `mainframe.VFrameSet.frameLogin.form.divLogin.form.div_login.form.edPasswd:input`
- ✅ **Login-Methode:** JavaScript-Injection in Nexacro-Felder
- ✅ **Session:** JSESSIONID Cookie wird gesetzt

### 2. System-Struktur
- ✅ **Framework:** Nexacro Platform
- ✅ **Encoding:** euc-kr (koreanisch)
- ✅ **JavaScript-basiert:** Alle UI-Elemente werden dynamisch geladen

### 3. Network-Requests
- ✅ **208 Requests erfasst** während Login und Navigation
- ⚠️ **API-Endpunkte:** Nur 1 gefunden (Transaction.js)
- ⚠️ **Teilebezug-Endpunkte:** Keine in statischen Requests gefunden

---

## 🔍 ERKANNTE PROBLEME

### Problem 1: Nexacro API-Calls sind dynamisch
- Nexacro generiert API-Calls zur Laufzeit über JavaScript
- Performance-Logs erfassen nicht alle XHR/Fetch-Requests
- API-Calls werden möglicherweise über WebSocket oder andere Methoden gemacht

### Problem 2: Teilebezug-Navigation
- Elemente wurden gefunden ("Europe Distributor/Dealer Order System")
- Klicks waren erfolgreich
- Aber keine neuen API-Endpunkte wurden erfasst

### Problem 3: Request-Erfassung
- Chrome Performance-Logs erfassen nicht alle Requests
- Nexacro verwendet möglicherweise spezielle Kommunikationsmethoden

---

## 📋 GEFUNDENE INFORMATIONEN

### Login-Felder (Nexacro IDs)
```javascript
Username: mainframe.VFrameSet.frameLogin.form.divLogin.form.div_login.form.edUserId:input
Password: mainframe.VFrameSet.frameLogin.form.divLogin.form.div_login.form.edPasswd:input
```

### Login-Script (funktioniert)
```javascript
// Setze Username
document.getElementById('mainframe.VFrameSet.frameLogin.form.divLogin.form.div_login.form.edUserId:input').value = 'G2403Koe';

// Setze Password
document.getElementById('mainframe.VFrameSet.frameLogin.form.divLogin.form.div_login.form.edPasswd:input').value = 'Greiner3!';

// Submit
// (Form-Submit oder Enter-Taste)
```

### Gefundene Elemente
- "Europe Distributor/Dealer Order System" - Titel der Anwendung
- Menü-Struktur vorhanden, aber nicht vollständig analysiert

---

## 🎯 NÄCHSTE SCHRITTE

### Option 1: Manuelle Browser-Analyse (Empfohlen)
1. Browser öffnen (Chrome/Firefox)
2. DevTools → Network-Tab
3. In Mobis einloggen
4. Zu Teilebezug navigieren
5. HAR-Datei exportieren

### Option 2: Verbesserte Selenium-Analyse
- Chrome DevTools Protocol direkt verwenden
- Network-Domain aktivieren
- Alle Requests inkl. XHR/Fetch erfassen

### Option 3: Nexacro Transaction.js analysieren
- Transaction.js Datei herunterladen
- Nach API-Endpunkten suchen
- Request-Format verstehen

---

## 🔧 ERSTELLTE TOOLS

1. **`scripts/mobis_selenium_analysis.py`** - Selenium-basierte Analyse
   - ✅ Login funktioniert
   - ✅ Network-Requests werden erfasst
   - ⚠️ Nicht alle API-Calls werden erfasst

2. **Screenshots:**
   - `/tmp/mobis_login_page.png` - Login-Seite
   - `/tmp/mobis_teilebezug_*.png` - Nach Navigation

3. **Ergebnisse:**
   - `/tmp/mobis_selenium_analysis.json` - Alle erfassten Requests

---

## 📝 ERKENNTNISSE FÜR API-CLIENT

### Login-Implementierung
```python
# Login funktioniert mit:
POST https://edos.mobiseurope.com/EDMOSN/gen/login.do
Data: userid=G2403Koe&password=Greiner3!
Cookie: JSESSIONID (wird gesetzt)
```

### Session-Management
- JSESSIONID Cookie muss für alle Requests mitgeführt werden
- Session bleibt aktiv für mehrere Requests

### Request-Format (vermutet)
- Nexacro verwendet möglicherweise SSV-Format (Server Side Values)
- Oder JSON über XHR/Fetch
- Endpunkte enden auf `.do`

---

## ⚠️ LIMITIERUNGEN

1. **Dynamische API-Calls:** Nicht alle Requests werden erfasst
2. **Nexacro-spezifisch:** Benötigt spezielle Behandlung
3. **JavaScript-basiert:** Vollständige Analyse erfordert Browser

---

## 📞 EMPFEHLUNG

**Für vollständige API-Dokumentation:**
- Manuelle Browser-Analyse mit DevTools
- Oder HAR-Datei bereitstellen
- Dann kann ich den API-Client vollständig implementieren

**Aktuell möglich:**
- Login-Implementierung im API-Client
- Basis-Struktur für API-Calls
- Wartet auf API-Endpunkt-Dokumentation

---

**Status:** ✅ Login erfolgreich, ⏳ API-Endpunkte für Teilebezug benötigt
