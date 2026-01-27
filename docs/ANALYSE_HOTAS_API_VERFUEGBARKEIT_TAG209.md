# Analyse: H.O.T.A.S. API Verfügbarkeit

**Datum:** 2026-01-23  
**TAG:** 209  
**Status:** 📊 **ANALYSE & TEST-ERGEBNISSE**

---

## 🎯 FRAGESTELLUNG

**Gibt es eine H.O.T.A.S. API, die wir für DRIVE nutzen können?**

---

## 🔍 TEST-ERGEBNISSE

### **1. Website-Analyse**

**URL:** https://hotas.de/outside_login.php  
**Zugangsdaten:** greinerdeg / saturn

**Ergebnisse:**
- ✅ **Login funktioniert** (Status 200)
- ❌ **Keine API-Hinweise** im HTML gefunden
- ❌ **Keine API-Endpunkte** in JavaScript gefunden
- ❌ **Keine API-Dokumentation** Links gefunden
- ❌ **Keine REST/SOAP Endpunkte** gefunden

**Gefundene Keywords:**
- ✅ "schnittstelle" im HTML (aber nur in Text, nicht als API)
- ✅ "xml" im HTML (aber nur in HTML-Deklaration)

---

### **2. Locosoft-Dokumentation Analyse**

**Aus der PDF-Dokumentation:**

**Erkenntnis:**
- ✅ **WebService vorhanden** - "Die Bestellung wird anschließend direkt über den WebService übertragen"
- ⚠️ **Aber:** WebService wird von **Locosoft** aufgerufen, nicht direkt von uns
- ⚠️ **Keine öffentliche API** - Die Dokumentation beschreibt nur die Locosoft-Integration

**Architektur:**
```
DRIVE → Locosoft → H.O.T.A.S. WebService
```

**NICHT:**
```
DRIVE → H.O.T.A.S. API (direkt)
```

---

## 💡 ERKENNTNISSE

### **✅ Was wir wissen:**

1. **H.O.T.A.S. hat einen WebService**
   - Wird von Locosoft aufgerufen
   - Für Bestellungen verwendet
   - Nicht öffentlich dokumentiert

2. **Keine öffentliche API**
   - Keine REST API gefunden
   - Keine SOAP API gefunden
   - Keine API-Dokumentation verfügbar

3. **Integration nur über DMS**
   - "Die meisten DMS-Lieferanten bieten bereits Schnittstellen zu H.O.T.A.S. an"
   - Integration erfolgt über DMS (wie Locosoft)
   - Nicht direkt für externe Systeme

---

### **⚠️ Was unklar ist:**

1. **WebService-Details**
   - Welches Format? (SOAP, REST, XML-RPC?)
   - Welche Endpunkte?
   - Welche Authentifizierung?

2. **API für externe Systeme**
   - Gibt es eine API für externe Systeme?
   - Oder nur für DMS-Integration?

3. **Zugriffsmöglichkeiten**
   - Kann DRIVE direkt auf H.O.T.A.S. zugreifen?
   - Oder nur über Locosoft?

---

## 🎯 MÖGLICHE LÖSUNGSANSÄTZE

### **Option 1: Über Locosoft SOAP (muss erweitert werden)** ⭐⭐

**Frage:** Kann Locosoft SOAP um H.O.T.A.S.-Methoden erweitert werden?

**Vorteile:**
- ✅ Bereits vorhandene SOAP-Infrastruktur
- ✅ Einheitliche Schnittstelle
- ✅ Keine neue Authentifizierung

**Nachteile:**
- ❌ Möglicherweise nicht möglich
- ❌ Abhängigkeit von Locosoft-Entwicklung
- ❌ Wartezeit auf Implementierung

**Status:** ⏳ **Muss bei Locosoft angefragt werden**

---

### **Option 2: WebService Reverse Engineering** ⭐

**Frage:** Können wir den WebService analysieren, den Locosoft nutzt?

**Vorgehen:**
1. Locosoft-Netzwerk-Traffic analysieren
2. WebService-Calls identifizieren
3. API-Endpunkte extrahieren
4. Eigene Client-Implementierung

**Vorteile:**
- ✅ Direkter Zugriff möglich
- ✅ Keine Abhängigkeit von Locosoft

**Nachteile:**
- ❌ Rechtlich fragwürdig
- ❌ Technisch schwierig
- ❌ Wartungsaufwand hoch (bei Änderungen)
- ❌ Möglicherweise gegen AGB

**Status:** ❌ **NICHT empfohlen**

---

### **Option 3: H.O.T.A.S. Support kontaktieren** ⭐⭐⭐

**Frage:** Gibt es eine offizielle API für externe Systeme?

**Vorgehen:**
1. H.O.T.A.S. Support kontaktieren
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

### **Option 4: Über Locosoft PostgreSQL (Bestellungen)** ⭐⭐

**Frage:** Werden H.O.T.A.S.-Bestellungen in Locosoft gespeichert?

**Vorgehen:**
1. Locosoft PostgreSQL prüfen
2. Bestellungen mit H.O.T.A.S. Quelle finden
3. Bestellstatus abfragen

**Vorteile:**
- ✅ Direkter Zugriff auf Bestellungen
- ✅ Keine API nötig
- ✅ Schnelle Abfragen

**Nachteile:**
- ❌ Nur Bestellungen, keine Suche
- ❌ Keine Live-Abfrage möglich
- ❌ Abhängig von Locosoft-Datenstruktur

**Status:** ⏳ **Muss geprüft werden**

---

## 📋 NÄCHSTE SCHRITTE

### **1. H.O.T.A.S. Support kontaktieren** ⏳ (HÖCHSTE PRIORITÄT)

**Zu fragen:**
- [ ] Gibt es eine API für externe Systeme?
- [ ] Welches Format? (REST, SOAP, XML-RPC?)
- [ ] Welche Endpunkte sind verfügbar?
- [ ] Wie funktioniert die Authentifizierung?
- [ ] Gibt es API-Dokumentation?
- [ ] Was kostet die API-Nutzung?
- [ ] Gibt es Entwickler-Zugang?

**Kontakt:**
- Website: https://hotas.de
- Support kontaktieren
- API-Dokumentation anfordern

---

### **2. Locosoft Support kontaktieren** ⏳

**Zu fragen:**
- [ ] Kann Locosoft SOAP um H.O.T.A.S.-Methoden erweitert werden?
- [ ] Gibt es bereits H.O.T.A.S.-Methoden in SOAP?
- [ ] Wie funktioniert die H.O.T.A.S. Integration in Locosoft?
- [ ] Können wir auf den H.O.T.A.S. WebService zugreifen?

**Kontakt:**
- Locosoft Support
- H.O.T.A.S. SOAP-Integration anfragen

---

### **3. Locosoft PostgreSQL prüfen** ⏳

**SQL-Queries:**
```sql
-- Prüfen ob H.O.T.A.S. Bestellungen gespeichert werden
SELECT * FROM information_schema.tables 
WHERE table_name LIKE '%hotas%' OR table_name LIKE '%teilepool%';

-- Prüfen ob Bestellungen H.O.T.A.S. Quelle haben
SELECT * FROM parts_orders 
WHERE supplier_name LIKE '%HOTAS%' OR supplier_name LIKE '%H.O.T.A.S.%';

-- Prüfen ob es ein Feld für Teilepool-Quelle gibt
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'parts' 
AND (column_name LIKE '%pool%' OR column_name LIKE '%hotas%');
```

---

## 💡 WICHTIGE ERKENNTNISSE

### **✅ Was wir wissen:**
1. **H.O.T.A.S. hat einen WebService** - Wird von Locosoft genutzt
2. **Keine öffentliche API** - Keine REST/SOAP API gefunden
3. **Integration nur über DMS** - "Die meisten DMS-Lieferanten bieten bereits Schnittstellen an"

### **⚠️ Was unklar ist:**
1. **API für externe Systeme** - Gibt es eine?
2. **WebService-Details** - Format, Endpunkte, Authentifizierung
3. **Zugriffsmöglichkeiten** - Direkt oder nur über Locosoft?

### **❌ Was nicht möglich ist:**
1. **Direkte API-Nutzung** - Keine öffentliche API gefunden
2. **Reverse Engineering** - Rechtlich & technisch problematisch

---

## 🎯 EMPFEHLUNG

### **Phase 1: H.O.T.A.S. Support kontaktieren** ✅ (EMPFOHLEN)

**Priorität:** ⭐⭐⭐ **Höchste Priorität**

**Fragen:**
1. Gibt es eine API für externe Systeme?
2. Welches Format? (REST, SOAP, XML-RPC?)
3. Welche Endpunkte?
4. Wie funktioniert die Authentifizierung?
5. Gibt es API-Dokumentation?
6. Was kostet die API-Nutzung?

**Erwartetes Ergebnis:**
- ✅ API-Dokumentation erhalten
- ✅ Test-Zugang beantragen
- ✅ Integration planen

---

### **Phase 2: Locosoft Support kontaktieren** ⏳

**Priorität:** ⭐⭐ **Mittlere Priorität**

**Fragen:**
1. Kann Locosoft SOAP um H.O.T.A.S.-Methoden erweitert werden?
2. Gibt es bereits H.O.T.A.S.-Methoden in SOAP?
3. Wie funktioniert die H.O.T.A.S. Integration?

**Erwartetes Ergebnis:**
- ✅ SOAP-Erweiterung möglich oder nicht
- ✅ Kosten erfahren
- ✅ Zeitplan erhalten

---

### **Phase 3: Locosoft PostgreSQL prüfen** ⏳

**Priorität:** ⭐⭐ **Mittlere Priorität**

**Fragen:**
1. Werden H.O.T.A.S.-Bestellungen gespeichert?
2. In welcher Tabelle?
3. Welche Felder sind verfügbar?

**Erwartetes Ergebnis:**
- ✅ Bestellungen können abgefragt werden
- ✅ Bestellstatus kann getrackt werden
- ⚠️ Aber: Keine Suche möglich

---

## 📊 ZUSAMMENFASSUNG

| Option | Status | Empfehlung |
|--------|--------|------------|
| **H.O.T.A.S. API (direkt)** | ❌ Nicht gefunden | ⏳ **Support kontaktieren** |
| **Locosoft SOAP erweitern** | ⚠️ Unbekannt | ⏳ **Locosoft anfragen** |
| **Locosoft PostgreSQL** | ⏳ Muss geprüft werden | ⏳ **SQL-Queries prüfen** |
| **Reverse Engineering** | ❌ Nicht empfohlen | ❌ **NICHT durchführen** |

---

## 🎯 FAZIT

**H.O.T.A.S. API Status:**

- ❌ **Keine öffentliche API gefunden**
- ✅ **WebService vorhanden** (aber nur für DMS-Integration)
- ⚠️ **Unklar:** Gibt es eine API für externe Systeme?

**Empfehlung:**
1. ✅ **H.O.T.A.S. Support kontaktieren** - API-Dokumentation anfordern
2. ⏳ **Locosoft Support kontaktieren** - SOAP-Erweiterung anfragen
3. ⏳ **Locosoft PostgreSQL prüfen** - Bestellungen abfragen

**Nächster Schritt:**
- H.O.T.A.S. Support kontaktieren
- API-Dokumentation anfordern
- Test-Zugang beantragen

---

**Status:** 📊 Analyse abgeschlossen  
**Nächster Schritt:** H.O.T.A.S. Support kontaktieren für API-Dokumentation
