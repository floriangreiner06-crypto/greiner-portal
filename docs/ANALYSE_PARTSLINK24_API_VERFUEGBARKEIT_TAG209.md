# Analyse: Partslink24 API Verfügbarkeit

**Datum:** 2026-01-23  
**TAG:** 209  
**Status:** 📊 **ANALYSE & TEST-ERGEBNISSE**

---

## 🎯 FRAGESTELLUNG

**Gibt es eine Partslink24 API, die wir für DRIVE nutzen können?**

---

## 🔍 TEST-ERGEBNISSE

### **1. Website-Analyse**

**URL:** https://www.partslink24.com/partslink24/user/login.do  
**Zugangsdaten:** 
- Firmenkennung: de-801571
- Benutzer: admin
- Passwort: Greiner1

**Ergebnisse:**
- ✅ **Login-Seite erreichbar** (Status 200)
- ⚠️ **Login-Status unklar** - URL bleibt gleich nach Login
- ❌ **Keine API-Hinweise** im HTML gefunden
- ❌ **Keine API-Endpunkte** in JavaScript gefunden
- ❌ **Keine API-Dokumentation** Links gefunden
- ❌ **Keine REST/SOAP Endpunkte** gefunden

**Technologie:**
- **Apache Struts** - Java-basiertes Framework
- **Form-basierter Login** - POST zu `/partslink24/user/login.do`
- **CSRF-Token** - `org.apache.struts.taglib.html.TOKEN`

**Login-Felder:**
- `accountLogin` - Text (Firmenkennung?)
- `userLogin` - Text (Benutzername)
- `loginBean.password` - Password
- `code2f` - Text (2FA?)
- `org.apache.struts.taglib.html.TOKEN` - Hidden (CSRF-Token)

---

### **2. Web-Recherche**

**Erkenntnisse:**
- ✅ **pl24connect** - Software für DMS-Integration
- ✅ **SAP-Schnittstellen** - Für Großkunden verfügbar
- ✅ **API-Technologie** - Erwähnt, aber nicht öffentlich dokumentiert
- ⚠️ **Keine öffentliche API-Dokumentation** gefunden

**pl24connect:**
- **Software-Lösung** für Händler
- **DMS-Integration** möglich
- **Bestellverarbeitung** aus partslink24
- **24/7 System** mit COMbox als zentrale Hub
- **Netzwerk-Ordner** für Bestellformulare
- **DMS-Verbindung** erforderlich

---

## 💡 ERKENNTNISSE

### **✅ Was wir wissen:**

1. **Partslink24 hat Integration-Möglichkeiten**
   - pl24connect für DMS-Integration
   - SAP-Schnittstellen für Großkunden
   - API-Technologie erwähnt

2. **Keine öffentliche API**
   - Keine REST API gefunden
   - Keine SOAP API gefunden
   - Keine API-Dokumentation verfügbar

3. **Integration über pl24connect**
   - Software-basierte Integration
   - DMS-Verbindung erforderlich
   - Netzwerk-Ordner für Datenübertragung

---

### **⚠️ Was unklar ist:**

1. **API-Details**
   - Welches Format? (REST, SOAP, XML-RPC?)
   - Welche Endpunkte?
   - Welche Authentifizierung?

2. **pl24connect Details**
   - Wie funktioniert die Integration?
   - Welche DMS-Systeme werden unterstützt?
   - Gibt es Locosoft-Integration?

3. **Zugriffsmöglichkeiten**
   - Kann DRIVE direkt auf Partslink24 zugreifen?
   - Oder nur über pl24connect?
   - Oder nur über Locosoft?

---

## 🎯 MÖGLICHE LÖSUNGSANSÄTZE

### **Option 1: pl24connect nutzen** ⭐⭐⭐

**Frage:** Gibt es pl24connect für Locosoft?

**Vorgehen:**
1. Partslink24 Support kontaktieren
2. pl24connect für Locosoft anfragen
3. Installation und Konfiguration

**Vorteile:**
- ✅ Offizielle Lösung
- ✅ DMS-Integration
- ✅ Unterstützt

**Nachteile:**
- ⚠️ Möglicherweise kostenpflichtig
- ⚠️ Software-Installation nötig
- ⚠️ Abhängigkeit von pl24connect

**Status:** ⏳ **Muss bei Partslink24 angefragt werden**

---

### **Option 2: SAP-Schnittstellen nutzen** ⭐⭐

**Frage:** Haben wir SAP-Schnittstellen-Zugang?

**Vorgehen:**
1. Partslink24 Support kontaktieren
2. SAP-Schnittstellen-Zugang beantragen
3. Integration planen

**Vorteile:**
- ✅ Offizielle Lösung
- ✅ Für Großkunden verfügbar
- ✅ Standardisiert

**Nachteile:**
- ❌ Nur für Großkunden
- ❌ Möglicherweise kostenpflichtig
- ❌ SAP-Infrastruktur nötig

**Status:** ⏳ **Muss bei Partslink24 angefragt werden**

---

### **Option 3: Partslink24 Support kontaktieren** ⭐⭐⭐

**Frage:** Gibt es eine API für externe Systeme?

**Vorgehen:**
1. Partslink24 Support kontaktieren
2. API-Dokumentation anfordern
3. Entwickler-Zugang beantragen

**Vorteile:**
- ✅ Offizielle Lösung
- ✅ Dokumentiert
- ✅ Unterstützt

**Nachteile:**
- ⚠️ Möglicherweise nicht verfügbar
- ⚠️ Möglicherweise kostenpflichtig

**Status:** ✅ **EMPFOHLEN - Als erstes versuchen**

---

### **Option 4: Über Locosoft Integration** ⭐⭐⭐

**Frage:** Gibt es Partslink24-Integration in Locosoft?

**Vorgehen:**
1. Locosoft Support kontaktieren
2. Partslink24-Integration prüfen
3. Konfiguration anfragen

**Vorteile:**
- ✅ Bereits vorhandene Infrastruktur
- ✅ Einheitliche Schnittstelle
- ✅ Keine neue Authentifizierung

**Nachteile:**
- ⚠️ Möglicherweise nicht verfügbar
- ⚠️ Abhängigkeit von Locosoft

**Status:** ⏳ **Muss bei Locosoft angefragt werden**

---

## 📋 NÄCHSTE SCHRITTE

### **1. Partslink24 Support kontaktieren** ⏳ (HÖCHSTE PRIORITÄT)

**Zu fragen:**
- [ ] Gibt es eine API für externe Systeme?
- [ ] Welches Format? (REST, SOAP, XML-RPC?)
- [ ] Welche Endpunkte sind verfügbar?
- [ ] Wie funktioniert die Authentifizierung?
- [ ] Gibt es API-Dokumentation?
- [ ] Was kostet die API-Nutzung?
- [ ] Gibt es pl24connect für Locosoft?
- [ ] Wie funktioniert pl24connect?
- [ ] Gibt es SAP-Schnittstellen-Zugang?

**Kontakt:**
- Website: https://www.partslink24.com
- Support kontaktieren
- API-Dokumentation anfordern

---

### **2. Locosoft Support kontaktieren** ⏳

**Zu fragen:**
- [ ] Gibt es Partslink24-Integration in Locosoft?
- [ ] Wie funktioniert die Integration?
- [ ] Welche Funktionen sind verfügbar?
- [ ] Was kostet die Integration?
- [ ] Gibt es pl24connect-Integration?

---

### **3. pl24connect prüfen** ⏳

**Fragen:**
- [ ] Gibt es pl24connect für Locosoft?
- [ ] Wie funktioniert die Installation?
- [ ] Welche Konfiguration ist nötig?
- [ ] Was kostet pl24connect?

---

## 💡 WICHTIGE ERKENNTNISSE

### **✅ Was wir wissen:**
1. **Partslink24 hat Integration-Möglichkeiten** - pl24connect, SAP-Schnittstellen
2. **Keine öffentliche API** - Keine REST/SOAP API gefunden
3. **Integration über pl24connect** - Software-basierte Integration

### **⚠️ Was unklar ist:**
1. **API für externe Systeme** - Gibt es eine?
2. **pl24connect Details** - Wie funktioniert es?
3. **Locosoft-Integration** - Gibt es eine?

### **❌ Was nicht möglich ist:**
1. **Direkte API-Nutzung** - Keine öffentliche API gefunden
2. **Reverse Engineering** - Rechtlich & technisch problematisch

---

## 🎯 EMPFEHLUNG

### **Phase 1: Partslink24 Support kontaktieren** ✅ (EMPFOHLEN)

**Priorität:** ⭐⭐⭐ **Höchste Priorität**

**Fragen:**
1. Gibt es eine API für externe Systeme?
2. Welches Format? (REST, SOAP, XML-RPC?)
3. Welche Endpunkte?
4. Wie funktioniert die Authentifizierung?
5. Gibt es API-Dokumentation?
6. Was kostet die API-Nutzung?
7. Gibt es pl24connect für Locosoft?
8. Wie funktioniert pl24connect?

**Erwartetes Ergebnis:**
- ✅ API-Dokumentation erhalten
- ✅ Test-Zugang beantragen
- ✅ Integration planen

---

### **Phase 2: Locosoft Support kontaktieren** ⏳

**Priorität:** ⭐⭐ **Mittlere Priorität**

**Fragen:**
1. Gibt es Partslink24-Integration in Locosoft?
2. Wie funktioniert die Integration?
3. Welche Funktionen sind verfügbar?
4. Was kostet die Integration?

**Erwartetes Ergebnis:**
- ✅ Integration möglich oder nicht
- ✅ Kosten erfahren
- ✅ Zeitplan erhalten

---

### **Phase 3: pl24connect prüfen** ⏳

**Priorität:** ⭐⭐ **Mittlere Priorität**

**Fragen:**
1. Gibt es pl24connect für Locosoft?
2. Wie funktioniert die Installation?
3. Welche Konfiguration ist nötig?
4. Was kostet pl24connect?

**Erwartetes Ergebnis:**
- ✅ Installation möglich oder nicht
- ✅ Kosten erfahren
- ✅ Konfiguration planen

---

## 📊 ZUSAMMENFASSUNG

| Option | Status | Empfehlung |
|--------|--------|------------|
| **Partslink24 API (direkt)** | ❌ Nicht gefunden | ⏳ **Support kontaktieren** |
| **pl24connect** | ⚠️ Unbekannt | ⏳ **Partslink24 anfragen** |
| **SAP-Schnittstellen** | ⚠️ Unbekannt | ⏳ **Partslink24 anfragen** |
| **Locosoft Integration** | ⚠️ Unbekannt | ⏳ **Locosoft anfragen** |
| **Reverse Engineering** | ❌ Nicht empfohlen | ❌ **NICHT durchführen** |

---

## 🎯 FAZIT

**Partslink24 API Status:**

- ❌ **Keine öffentliche API gefunden**
- ✅ **pl24connect verfügbar** (aber Details unklar)
- ✅ **SAP-Schnittstellen verfügbar** (aber nur für Großkunden)
- ⚠️ **Unklar:** Gibt es eine API für externe Systeme?

**Empfehlung:**
1. ✅ **Partslink24 Support kontaktieren** - API-Dokumentation anfordern
2. ⏳ **Locosoft Support kontaktieren** - Integration prüfen
3. ⏳ **pl24connect prüfen** - Installation anfragen

**Nächster Schritt:**
- Partslink24 Support kontaktieren
- API-Dokumentation anfordern
- pl24connect für Locosoft anfragen

---

**Vergleich zu H.O.T.A.S.:**
- Partslink24 hat **pl24connect** (H.O.T.A.S. = Keine API gefunden)
- Partslink24 hat **SAP-Schnittstellen** (H.O.T.A.S. = Keine API gefunden)
- Partslink24 bietet **Originalteile** (H.O.T.A.S. = Ersatzteilpool)

**Status:** 📊 Analyse abgeschlossen  
**Nächster Schritt:** Partslink24 Support kontaktieren für API-Dokumentation und pl24connect

---

## 🔍 ERWEITERTE ANALYSE (Nach Login)

**Login-Status:** ✅ **Erfolgreich eingeloggt**

**Gefundene Hinweise:**
- ✅ **ETKA Interface** - JavaScript-Dateien gefunden (`etka-interface.js`, `etka-catalog-interface.js`)
- ✅ **Hilfe-Funktion** - `showHelp()` JavaScript-Funktion
- ✅ **Kontakt-Seite** - `/partslink24/contact-extern.action`
- ⚠️ **Keine direkten API-Links** im eingeloggten Bereich gefunden

**Technologie:**
- **Apache Struts** - Java-basiertes Framework
- **ETKA Integration** - Möglicherweise für DMS-Integration
- **JavaScript-basierte Navigation** - `navigateSecure()` Funktion

**Nächste Schritte:**
1. ✅ **Hilfe-Seite prüfen** - Möglicherweise API-Dokumentation
2. ✅ **Kontakt-Seite prüfen** - Support kontaktieren
3. ⏳ **ETKA Interface analysieren** - Möglicherweise API-Endpunkte
4. ⏳ **JavaScript-Dateien analysieren** - Suche nach API-Calls
