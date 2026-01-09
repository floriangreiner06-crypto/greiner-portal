# Mobis EDMOS API-Analyse - Zusammenfassung

**Datum:** 2026-01-09 (TAG 175)  
**Status:** ⚠️ Automatische Analyse limitiert - Browser-basierte Analyse empfohlen

---

## 🔍 DURCHGEFÜHRTE ANALYSEN

### 1. Website-Struktur
- ✅ **Framework:** Nexacro Platform (Enterprise Web Application)
- ✅ **Login-Endpunkt:** `/EDMOSN/gen/login.do`
- ✅ **Session:** JSESSIONID Cookie
- ✅ **Encoding:** euc-kr (koreanisch)

### 2. Login-Prozess
- ✅ **Methode:** POST zu `/EDMOSN/gen/login.do`
- ✅ **Parameter:** `userid`, `password`
- ✅ **Status:** Login funktioniert (Status 200)

### 3. App-Struktur
- ⚠️ **App-Deskriptor:** `App_Desktop.xadl.js` (nur 92 Zeichen - möglicherweise Redirect)
- ✅ **JavaScript-Libraries:** Nexacro Framework-Dateien gefunden
- ⚠️ **API-Endpunkte:** Nicht in statischen Dateien gefunden (dynamisch generiert)

---

## ⚠️ LIMITIERUNGEN DER AUTOMATISCHEN ANALYSE

### Problem
Nexacro ist eine **dynamische JavaScript-Anwendung**, die API-Calls zur Laufzeit generiert. Die Endpunkte sind nicht in statischen HTML/JS-Dateien sichtbar.

### Lösung
**Browser-basierte Analyse mit DevTools** ist erforderlich:
1. Browser öffnen (Chrome/Firefox)
2. DevTools → Network-Tab öffnen
3. In Mobis einloggen
4. Zu Teilebezug-Funktion navigieren
5. Network-Requests analysieren

---

## 📋 EMPFOHLENE NÄCHSTE SCHRITTE

### Option 1: Manuelle Browser-Analyse (Empfohlen)
1. **Browser öffnen:** Chrome oder Firefox
2. **DevTools öffnen:** F12 → Network-Tab
3. **Filter setzen:** "XHR" oder "Fetch" aktivieren
4. **Login durchführen:**
   - URL: https://edos.mobiseurope.com/EDMOSN/gen/index.jsp
   - User: G2403Koe
   - Pass: Greiner3!
5. **Zu Teilebezug navigieren:**
   - Im Menü nach "Teile", "Parts", "Bestellung", "Order" suchen
   - Funktion öffnen
6. **Requests dokumentieren:**
   - Alle Requests im Network-Tab kopieren
   - HAR-Datei exportieren (Rechtsklick → "Save all as HAR")
   - Oder Screenshots der Requests machen

### Option 2: Selenium-basierte Analyse
- Automatisiertes Browser-Script mit Selenium
- Kann Login durchführen und Navigation automatisieren
- Erfordert Selenium-Installation

### Option 3: HAR-Datei-Analyse
- Wenn HAR-Datei vorhanden, kann ich diese analysieren
- Enthält alle Network-Requests mit Details

---

## 🔧 ERSTELLTE TOOLS

1. **`scripts/analyse_mobis_website.py`** - Website-Struktur-Analyse
2. **`scripts/mobis_login_test.py`** - Login-Test
3. **`scripts/mobis_full_analysis.py`** - Vollständige Analyse
4. **`scripts/mobis_deep_analysis.py`** - Tiefen-Analyse der Nexacro-App

---

## 📝 ERWARTETE API-STRUKTUR (basierend auf Nexacro)

### Nexacro Transaction-Format
```
POST /EDMOSN/gen/transaction.do
Content-Type: application/x-www-form-urlencoded

SSV:utf-8\u001eservice=TeilebezugService\u001emethod=getPartsForOrder\u001eorder_number=220542\u001e
```

### Mögliche Endpunkte (zu verifizieren)
- `/EDMOSN/gen/transaction.do` - Haupt-Transaction-Endpunkt
- `/EDMOSN/gen/parts.do` - Teilebezug (wenn vorhanden)
- `/EDMOSN/gen/order.do` - Bestellungen (wenn vorhanden)

---

## 🎯 FÜR TEILEBEZUG BENÖTIGTE INFORMATIONEN

1. **API-Endpunkt:**
   - URL für Teilebezug-Abfrage
   - Request-Methode (GET/POST)
   - Request-Format (SSV, JSON, XML, Form-Data)

2. **Request-Parameter:**
   - Wie wird Auftragsnummer übergeben?
   - Welche weiteren Parameter sind nötig?
   - Session/Token-Handling?

3. **Response-Format:**
   - JSON, XML, SSV?
   - Datenstruktur der Teile-Informationen
   - Felder: Teilenummer, Beschreibung, Bestellnummer, Lieferdatum, etc.

---

## 📞 NÄCHSTE AKTION

**Bitte eine der folgenden Optionen:**
1. HAR-Datei von Browser-Analyse bereitstellen
2. Screenshots der Network-Requests senden
3. Selenium-Script erstellen lassen (für automatisierte Analyse)
4. Manuell die API-Details dokumentieren und teilen

---

**Status:** ⏳ Wartet auf Browser-Analyse oder HAR-Datei für vollständige API-Dokumentation
