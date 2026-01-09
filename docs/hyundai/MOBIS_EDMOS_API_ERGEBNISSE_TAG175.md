# Mobis EDMOS API Analyse - Ergebnisse

**Datum:** 2026-01-09 (TAG 175)  
**Status:** ⏳ Analyse läuft

---

## 🔍 ERKANNTE SYSTEM-STRUKTUR

### Framework
- **Nexacro Platform** - Enterprise Web Application Framework
- **Encoding:** euc-kr (koreanisch)
- **Session:** JSESSIONID Cookie

### Gefundene Endpunkte
1. **Login-Seite:** `https://edos.mobiseurope.com/EDMOSN/gen/index.jsp`
2. **Login-Endpunkt:** `https://edos.mobiseurope.com/EDMOSN/gen/login.do`
3. **App-Deskriptor:** `https://edos.mobiseurope.com/App_Desktop.xadl.js`

### JavaScript-Dateien (Nexacro)
- `nexacrolib/framework/Framework.js`
- `nexacrolib/component/Transaction.js` ← **Wichtig für API-Calls!**
- `nexacrolib/component/extPrototype/Transaction.js`
- `nexacrolib/component/ProjectLib/SL_Common.js`
- `nexacrolib/component/ProjectLib/SL100.js`

---

## 📋 LOGIN-PROZESS

### Erkannte Methoden

#### Methode 1: POST zu `/index.jsp`
- **Status:** 200 (keine Redirect)
- **Ergebnis:** Unklar

#### Methode 2: POST zu `/login.do`
- **Status:** 200
- **Content-Type:** `text/html; charset=euc-kr`
- **Ergebnis:** Möglicherweise korrekter Endpunkt

#### Methode 3: Nexacro Transaction (SSV-Format)
- **Status:** 200
- **Response:** "you request is Wrong!"
- **Ergebnis:** Falsches Format

---

## 🔧 NEXACRO KOMMUNIKATION

### Nexacro Transaction Format
Nexacro verwendet **SSV-Format** (Server Side Values):
```
SSV:utf-8\u001ekey1=value1\u001ekey2=value2\u001e
```

### Mögliche Endpunkte
- `/EDMOSN/gen/transaction.do` - Transaction-Endpunkt
- `/EDMOSN/gen/*.do` - Verschiedene Service-Endpunkte

---

## 🎯 NÄCHSTE SCHRITTE

### 1. Login-Prozess verstehen
- [ ] Browser DevTools öffnen (F12 → Network)
- [ ] Manuell in Mobis einloggen
- [ ] Alle Requests dokumentieren:
  - URL
  - Method (GET/POST)
  - Headers
  - Request Body
  - Response

### 2. Teilebezug-Funktion finden
- [ ] Nach Login: Navigation zu Teilebezug
- [ ] Network-Requests analysieren
- [ ] API-Endpunkte für Teilebezug identifizieren

### 3. API-Struktur dokumentieren
- [ ] Request-Format (SSV, JSON, XML?)
- [ ] Response-Format
- [ ] Authentifizierung (Session, Token?)

---

## 📝 HINWEISE

### Nexacro-spezifisch
- Nexacro verwendet oft **SSV-Format** für Datenübertragung
- Kommunikation läuft über `.do` Endpunkte
- Session-basierte Authentifizierung (JSESSIONID)

### Encoding
- **euc-kr** (koreanisch) - muss bei Requests/Responses beachtet werden

### Browser-basierte Analyse nötig
Da Nexacro eine komplexe JavaScript-Anwendung ist, ist eine **manuelle Browser-Analyse** mit DevTools am effektivsten:
1. Browser öffnen
2. DevTools → Network-Tab
3. In Mobis einloggen
4. Zu Teilebezug navigieren
5. Alle Requests exportieren (HAR-Datei)

---

## 🔗 RELEVANTE DATEIEN

- `scripts/analyse_mobis_website.py` - Website-Analyse-Script
- `scripts/mobis_login_test.py` - Login-Test-Script
- `api/mobis_edmos_api.py` - API-Client (TODO: anpassen)

---

**Status:** ⏳ Wartet auf manuelle Browser-Analyse für vollständige API-Dokumentation
