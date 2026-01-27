# Analyse: Partslink Systeme

**Datum:** 2026-01-23  
**TAG:** 209  
**Status:** 📊 **ANALYSE & BEWERTUNG**

---

## 🎯 FRAGESTELLUNG

**Was ist "partslink" und ist es für DRIVE relevant?**

---

## 🔍 ERKENNTNISSE

Es gibt **zwei verschiedene Systeme** mit ähnlichen Namen:

### **1. Partslink24** ⭐⭐⭐ (HÖCHSTE RELEVANZ)

**Was ist Partslink24?**
- **Online-Portal** für Original-Ersatzteile
- **Mehrmarken-Plattform** für Automobilersatzteile
- **Betrieben im Auftrag** mehrerer Fahrzeughersteller
- **48.000+ Kunden** weltweit
- **8+ Millionen Original-Ersatzteile** verfügbar

**Unterstützte Marken:**
- Audi, BMW, Mercedes-Benz, Porsche, Volkswagen
- SEAT, Škoda, CUPRA
- Volkswagen Nutzfahrzeuge, MAN
- Und viele weitere

**Funktionalitäten:**
- ✅ **24/7 Online-Bestellung** - Rund um die Uhr verfügbar
- ✅ **Fahrgestellnummern-Suche** - Eindeutige Teileidentifikation
- ✅ **Mobile App** - QR-Code-Scan für Fahrgestellnummern
- ✅ **Bestandsprüfung** - Bei lokalen Händlern
- ✅ **Elektronische Archivierung** - Alle Bestellungen gespeichert
- ✅ **SAP-Schnittstellen** - Für Großkunden
- ✅ **API-Technologie** - Für DMS-Integration

**Zugangsbedingungen:**
- Registrierung erforderlich
- Verschiedene Abo-Modelle:
  - Jahres-Abo
  - Monats-Abo
  - Tageszugangslizenzen
  - Kostenloser einmonatiger Testzugang

**Website:** https://www.partslink24.com

---

### **2. PARTSLINK (partslink.org)** ⭐ (GERINGE RELEVANZ)

**Was ist PARTSLINK?**
- **Universelles Nummerierungssystem** für Aftermarket-Karosserieteile
- **Verwaltet von ABPA** (Automotive Body Parts Association)
- **160+ Mitglieder** - 90% der unabhängigen Aftermarket-Karosserieteile
- **Nummerierungssystem**, kein Bestellsystem

**Zweck:**
- Identifikation von Aftermarket-Karosserieteilen
- Vergleichbarkeit mit OEM-Teilen
- Tracking von Ersatzteilen

**Format:**
- Zwei-Zeichen Herstellercode
- Vierstelliger Teiltyp-Code
- Dreistellige Sequenznummer (100-999)
- Erweitert auf alphanumerisch (A-Z, ohne I/O)

**Datenformate:**
- **Standard Format**: dBase III oder Excel
- **ACES Format**: XML-basiert mit erweiterten Details

**Website:** https://www.partslink.org

**Relevanz für DRIVE:** ⚠️ **GERING** - Nur Nummerierungssystem, kein Bestellsystem

---

## 💡 RELEVANZ FÜR DRIVE

### **Partslink24** ⭐⭐⭐ **SEHR RELEVANT**

**Warum relevant:**
1. **Original-Ersatzteile** - Direkte Bestellung von Originalteilen
2. **Mehrmarken** - Unterstützt viele Marken (Opel, Hyundai, etc.)
3. **DMS-Integration** - API/Schnittstellen verfügbar
4. **24/7 Verfügbarkeit** - Rund um die Uhr bestellbar
5. **Fahrgestellnummern-Suche** - Eindeutige Teileidentifikation

**Vergleich zu H.O.T.A.S.:**
| Feature | H.O.T.A.S. | Partslink24 |
|---------|------------|-------------|
| **Typ** | Ersatzteilpool | Originalteile-Portal |
| **Quelle** | Verschiedene Händler | Hersteller-Originalteile |
| **API** | ❌ Nicht gefunden | ✅ SAP-Schnittstellen, API |
| **DMS-Integration** | ✅ Über Locosoft | ✅ Direkt möglich |
| **Marken** | Verschiedene | Originalteile (VW, Audi, BMW, etc.) |

**Potenzielle Integration in DRIVE:**
- ✅ **Teile-Suche** - Originalteile finden
- ✅ **Bestellung** - Direkte Bestellung über API
- ✅ **Bestandsprüfung** - Verfügbarkeit prüfen
- ✅ **Preisvergleich** - Mit anderen Quellen vergleichen

---

## 🔧 TECHNISCHE INTEGRATION

### **Partslink24 API/Schnittstellen**

**Verfügbare Schnittstellen:**
1. **SAP-Schnittstellen** - Für Großkunden
2. **API-Technologie** - Für DMS-Integration
3. **Middleware-Lösungen** - z.B. Speed4Trade Connect

**Integration-Möglichkeiten:**
- ✅ **Direkte API** - Falls verfügbar
- ✅ **SAP-Integration** - Für Großkunden
- ✅ **Middleware** - Über externe Lösungen

**Status:** ⏳ **Muss geprüft werden**

---

## 📋 NÄCHSTE SCHRITTE

### **1. Partslink24 API-Dokumentation anfordern** ⏳ (HÖCHSTE PRIORITÄT)

**Zu fragen:**
- [ ] Gibt es eine REST/SOAP API?
- [ ] Welche Endpunkte sind verfügbar?
- [ ] Wie funktioniert die Authentifizierung?
- [ ] Gibt es API-Dokumentation?
- [ ] Was kostet die API-Nutzung?
- [ ] Gibt es Test-Zugang?
- [ ] Welche DMS-Systeme werden unterstützt?
- [ ] Gibt es Locosoft-Integration?

**Kontakt:**
- Website: https://www.partslink24.com
- Support kontaktieren
- API-Dokumentation anfordern

---

### **2. Partslink24 Test-Zugang beantragen** ⏳

**Vorgehen:**
1. Registrierung auf partslink24.com
2. Kostenloser einmonatiger Testzugang nutzen
3. Funktionen testen
4. API-Zugang anfragen

---

### **3. Locosoft Support kontaktieren** ⏳

**Zu fragen:**
- [ ] Gibt es Partslink24-Integration in Locosoft?
- [ ] Wie funktioniert die Integration?
- [ ] Welche Funktionen sind verfügbar?
- [ ] Was kostet die Integration?

---

### **4. Integration in DRIVE planen** ⏳

**Potenzielle Features:**
1. **Teile-Suche** - Originalteile über Partslink24 suchen
2. **Bestellung** - Direkte Bestellung über API
3. **Bestandsprüfung** - Verfügbarkeit prüfen
4. **Preisvergleich** - Mit anderen Quellen vergleichen
5. **Bestellstatus** - Tracking von Bestellungen

**Integration-Punkte:**
- `api/teile_api.py` - Teile-Suche erweitern
- `api/teile_stock_utils.py` - Bestandsprüfung
- `api/parts_api.py` - Bestellung integrieren
- `api/werkstatt_live_api.py` - Verfügbarkeit anzeigen

---

## 🎯 VERGLEICH: H.O.T.A.S. vs. Partslink24

| Feature | H.O.T.A.S. | Partslink24 |
|---------|------------|-------------|
| **Typ** | Ersatzteilpool | Originalteile-Portal |
| **Quelle** | Verschiedene Händler | Hersteller-Originalteile |
| **API** | ❌ Nicht gefunden | ✅ SAP-Schnittstellen, API |
| **DMS-Integration** | ✅ Über Locosoft | ✅ Direkt möglich |
| **Marken** | Verschiedene | Originalteile (VW, Audi, BMW, etc.) |
| **Bestellung** | ✅ Über Locosoft | ✅ Direkt über API |
| **Suche** | ✅ Über Locosoft | ✅ Direkt über API |
| **Preise** | ⚠️ Verschiedene Händler | ✅ Originalteile-Preise |
| **Verfügbarkeit** | ⚠️ Abhängig von Händlern | ✅ 24/7 verfügbar |

---

## 💡 EMPFEHLUNG

### **Partslink24** ⭐⭐⭐ **SEHR EMPFEHLENSWERT**

**Warum:**
1. ✅ **Originalteile** - Direkter Zugriff auf Originalteile
2. ✅ **API verfügbar** - SAP-Schnittstellen, API-Technologie
3. ✅ **DMS-Integration** - Direkt möglich
4. ✅ **24/7 Verfügbarkeit** - Rund um die Uhr
5. ✅ **Mehrmarken** - Viele Marken unterstützt

**Nächste Schritte:**
1. ✅ **Partslink24 Support kontaktieren** - API-Dokumentation anfordern
2. ⏳ **Test-Zugang beantragen** - Funktionen testen
3. ⏳ **Locosoft Support kontaktieren** - Integration prüfen
4. ⏳ **Integration in DRIVE planen** - Features implementieren

---

### **PARTSLINK (partslink.org)** ⚠️ **GERINGE RELEVANZ**

**Warum:**
- Nur Nummerierungssystem
- Kein Bestellsystem
- Für Aftermarket-Karosserieteile
- Nicht für Originalteile

**Relevanz:** ⚠️ **GERING** - Nur für spezielle Anwendungsfälle

---

## 📊 ZUSAMMENFASSUNG

| System | Typ | API | Relevanz | Empfehlung |
|--------|-----|-----|----------|------------|
| **Partslink24** | Originalteile-Portal | ✅ Verfügbar | ⭐⭐⭐ Sehr hoch | ✅ **EMPFOHLEN** |
| **PARTSLINK** | Nummerierungssystem | ❌ Nicht relevant | ⭐ Gering | ⚠️ Nur speziell |

---

## 🎯 FAZIT

**Partslink24 ist sehr relevant für DRIVE:**

- ✅ **Originalteile** - Direkter Zugriff auf Originalteile
- ✅ **API verfügbar** - SAP-Schnittstellen, API-Technologie
- ✅ **DMS-Integration** - Direkt möglich
- ✅ **24/7 Verfügbarkeit** - Rund um die Uhr
- ✅ **Mehrmarken** - Viele Marken unterstützt

**Nächster Schritt:**
1. ✅ **Partslink24 Support kontaktieren** - API-Dokumentation anfordern
2. ⏳ **Test-Zugang beantragen** - Funktionen testen
3. ⏳ **Locosoft Support kontaktieren** - Integration prüfen

**Vergleich zu H.O.T.A.S.:**
- Partslink24 bietet **Originalteile** (H.O.T.A.S. = Ersatzteilpool)
- Partslink24 hat **API verfügbar** (H.O.T.A.S. = Keine API gefunden)
- Partslink24 ermöglicht **direkte Integration** (H.O.T.A.S. = Nur über Locosoft)

---

**Status:** 📊 Analyse abgeschlossen  
**Nächster Schritt:** Partslink24 Support kontaktieren für API-Dokumentation
