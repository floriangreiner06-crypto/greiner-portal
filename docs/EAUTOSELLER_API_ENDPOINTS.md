# eAutoseller API-Endpoints Dokumentation

**Datum:** 2025-12-29  
**Status:** ✅ Analyse abgeschlossen  
**Login:** fGreiner / fGreiner12 (txtLoginbereich: kfz)

---

## 🔍 ANALYSE-ERGEBNISSE

### Login erfolgreich
- ✅ Automatischer Login implementiert
- ✅ Wichtig: `txtLoginbereich` = "kfz" erforderlich
- ✅ Nach Login: `/administration/index.asp?ufilid=0`

### Website-Struktur
- **Frameset-basiert:**
  - `leftFrame`: `/administration/navi.asp?ufilid=`
  - `mainFrame`: `/administration/start.asp`

---

## 📋 GEFUNDENE API-ENDPOINTS

### 1. startdata.asp (Dashboard-Daten)
**URL:** `/administration/startdata.asp`  
**Method:** GET  
**Parameter:**
- `id`: Dashboard-Widget-ID (201, 202, 225, 226, 227, 228, 229, 230)
- `time`: Timestamp (z.B. 1926)

**Beispiel:**
```
GET /administration/startdata.asp?id=201&time=1926
```

**Response-Format:** Pipe-separated (`|`)  
**Hinweis:** Benötigt möglicherweise spezielles Cookie

**Status:** ⚠️ Gibt "NoWarnCookie Found" zurück (Cookie-Problem)

---

### 2. dataApi.asp (Fahrzeugdaten)
**URL:** `/administration/modules/carData/dataApi.asp`  
**Method:** GET  
**Parameter:**
- `AussSort`: Sortierung (z.B. 1)

**Beispiel:**
```
GET /administration/modules/carData/dataApi.asp?AussSort=1
```

**Response-Format:** HTML (nicht JSON/XML)  
**Size:** ~6KB

**Status:** ✅ Funktioniert, gibt HTML zurück

---

### 3. kfzuebersicht.asp (Fahrzeugübersicht)
**URL:** `/administration/kfzuebersicht.asp`  
**Method:** GET  
**Parameter:**
- `start`: 1
- `txtAktiv`: 1 (nur aktive Fahrzeuge)
- `txtOrder`: Sortierung (z.B. `kfz_preis ASC`)
- `txtMarke`, `txtModell`, `txtPreis`: Filter

**Beispiel:**
```
GET /administration/kfzuebersicht.asp?start=1&txtAktiv=1&txtOrder=kfz_preis%20ASC
```

**Response-Format:** HTML (große Seite, ~600KB)  
**Enthält:** Fahrzeugliste als HTML-Tabelle

**Status:** ✅ Funktioniert

---

### 4. Weitere ASP-Seiten

| Seite | URL | Beschreibung |
|-------|-----|--------------|
| `anfragenuebersicht.asp` | `/administration/anfragenuebersicht.asp` | Anfragen-Übersicht |
| `kontaktuebersicht.asp` | `/administration/kontaktuebersicht.asp` | Kontakt-Übersicht |
| `useruebersicht.asp` | `/administration/useruebersicht.asp` | User-Übersicht |
| `felgenuebersicht.asp` | `/administration/felgenuebersicht.asp` | Felgen-Übersicht |
| `kfzauss.asp` | `/administration/kfzauss.asp` | Fahrzeug-Ausschreibung |

**Status:** ✅ Alle funktionieren, geben HTML zurück

---

## 🔑 AUTHENTIFIZIERUNG

### Session-basiert
- Login über `/login.asp`
- Session-Cookie wird gesetzt
- Alle nachfolgenden Requests verwenden Session-Cookie

### Login-Daten:
```python
{
    'txtLoginbereich': 'kfz',  # WICHTIG!
    'txtUser': 'fGreiner',
    'txtpwd': 'fGreiner12',
    'usercook': '1',
    'txtUfilvorwahl': '1'
}
```

---

## 📊 API-FORMATE

### Aktuell gefunden:
- **HTML:** Die meisten Endpoints geben HTML zurück
- **Pipe-separated:** `startdata.asp` (benötigt Cookie)
- **JSON:** ❌ Nicht gefunden (möglicherweise mit anderen Parametern)
- **XML:** ❌ Nicht gefunden (möglicherweise mit anderen Parametern)

### Bekannte eAutoseller APIs (aus Recherche):
1. **flashXML API** - `/eaxml` oder `/flashxml`
   - Benötigt AuthCode
   - XML-Format
   - Dokumentation: https://www.eautoseller.de/hp/eaxml.asp

2. **Upload API** - `/api/upload`
   - CSV-Format
   - Dokumentation: https://www.eautoseller.de/hp/api.asp

---

## 💡 ERKENNTNISSE

### 1. HTML-basierte APIs
- Die meisten Endpoints geben HTML zurück
- Daten können aus HTML geparst werden
- Keine direkten JSON/XML-Endpoints gefunden

### 2. JavaScript-basierte Datenabfrage
- `startdata.asp` wird via XMLHttpRequest aufgerufen
- Verschiedene IDs für verschiedene Dashboard-Widgets
- Benötigt möglicherweise spezielle Cookies

### 3. Frameset-Struktur
- Website verwendet Framesets
- Navigation in `navi.asp`
- Hauptinhalt in `start.asp`

---

## 🎯 NÄCHSTE SCHRITTE

### PRIO 1: Browser-Analyse ⭐⭐⭐
**Warum:** APIs werden dynamisch via JavaScript geladen

**Vorgehen:**
1. Browser öffnen (F12 → Network-Tab)
2. Login auf eAutoseller
3. Aktionen durchführen:
   - Fahrzeugliste öffnen
   - Fahrzeug öffnen
   - Dashboard-Widgets laden
4. API-Calls im Network-Tab dokumentieren

### PRIO 2: flashXML API testen ⭐⭐
- AuthCode von eAutoseller Support anfordern
- flashXML API mit AuthCode testen
- Beispiel-Requests dokumentieren

### PRIO 3: HTML-Parsing ⭐
- HTML-Responses parsen
- Fahrzeugdaten extrahieren
- Python-Client entwickeln

---

## 📝 CODE-BEISPIELE

### Login:
```python
import requests

session = requests.Session()
session.verify = False

# Login
resp = session.get('https://greiner.eautoseller.de/')
# ... Login-Daten extrahieren und senden
session.post('https://greiner.eautoseller.de/login.asp', data=login_data)

# API-Call
resp = session.get('https://greiner.eautoseller.de/administration/kfzuebersicht.asp?start=1&txtAktiv=1')
# HTML parsen für Fahrzeugdaten
```

### startdata.asp:
```python
# Benötigt möglicherweise spezielles Cookie
resp = session.get('https://greiner.eautoseller.de/administration/startdata.asp?id=201&time=1926')
# Response: Pipe-separated Daten
```

---

## ⚠️ HINWEISE

1. **Cookie-Problem:** `startdata.asp` gibt "NoWarnCookie Found" zurück
   - Möglicherweise zusätzliches Cookie erforderlich
   - Oder JavaScript setzt Cookie vor API-Call

2. **HTML-Parsing:** Die meisten APIs geben HTML zurück
   - BeautifulSoup für Parsing verwenden
   - Tabellen-Struktur analysieren

3. **Dynamisches Laden:** Viele APIs werden erst bei Aktionen geladen
   - Browser-Analyse zeigt echte API-Calls
   - Network-Tab ist wichtig

---

## 📚 LINKS

- **eAutoseller Homepage:** https://www.eautoseller.de
- **flashXML Dokumentation:** https://www.eautoseller.de/hp/eaxml.asp
- **Upload API Dokumentation:** https://www.eautoseller.de/hp/api.asp

---

**Status:** ✅ Analyse abgeschlossen, ⏳ Browser-Analyse empfohlen für dynamische APIs

