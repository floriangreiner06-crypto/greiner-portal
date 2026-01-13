# GlobalCube Reverse Engineering Plan - TAG 182

**Datum:** 2026-01-12  
**Ziel:** Vollständige Reverse Engineering der GlobalCube BWA-Logik für 100%ige Übereinstimmung

---

## 🎯 PROBLEM

- **BWA Landau:** Differenz von -7.546,55 € (9%) verbleibt
- **Stückzahlen:** Stimmen nicht überein
- **Datenquelle:** Beide (DRIVE und GlobalCube) nutzen Locosoft PostgreSQL
- **Zeitraum:** Identisch (Sep-Dez 2025)

**Hypothese:** GlobalCube verwendet andere Filter-Logik oder Konten-Zuordnungen, die wir noch nicht identifiziert haben.

---

## 🔍 REVERSE ENGINEERING ANSÄTZE

### 1. GlobalCube Portal Scraping (IBM Cognos)

**Ziel:** BWA-Reports direkt aus dem Portal extrahieren

**Vorgehen:**
- ✅ Portal identifiziert: IBM Cognos BI (http://10.80.80.10:9300/bi/)
- ✅ Login-Credentials: Greiner Hawaii#22
- ⏳ Session-Management implementieren
- ⏳ BWA-Reports finden und navigieren
- ⏳ Report-Parameter extrahieren (Filter, Zeiträume)
- ⏳ Report-Daten scrapen (HTML-Tabellen oder Excel-Export)

**Tools:**
- `requests` + `BeautifulSoup` (falls installierbar)
- Session-Cookies für Authentifizierung
- JavaScript-Rendering (falls nötig: Selenium)

**Dateien:**
- `scripts/cognos_report_scraper.py` (erweitern)

---

### 2. GlobalCube Struktur-Dateien analysieren

**Ziel:** Filter-Logik aus XML/CSV-Dateien extrahieren

**Bekannte Dateien:**
- `/mnt/globalcube/GCStruct/Struktur_GuV.xml` - BWA-Hierarchie
- `/mnt/globalcube/GCStruct/Struktur_Controlling.xml` - Controlling-Struktur
- `/mnt/globalcube/GCStruct/config.xml` - Konfiguration
- `/mnt/globalcube/GCStruct/Kontenrahmen.csv` - Konten-Mapping

**Vorgehen:**
- ⏳ XML-Strukturen vollständig parsen
- ⏳ Filter-Regeln extrahieren (IF-THEN-Logik)
- ⏳ Konten-Zuordnungen validieren
- ⏳ Standort-Filter-Logik identifizieren

**Dateien:**
- `scripts/globalcube_explorer.py` (erweitern)

---

### 3. GlobalCube MDC-Dateien analysieren

**Ziel:** Rohdaten aus Materialized Data Cubes extrahieren

**Bekannte Dateien:**
- `/mnt/globalcube/Cubes/f_belege.mdc` - Buchungsdaten

**Vorgehen:**
- ⏳ MDC-Format reverse engineerieren (binär)
- ⏳ Datenstruktur identifizieren
- ⏳ Filter-Logik aus Daten ableiten
- ⏳ Vergleich mit Locosoft journal_accountings

**Herausforderung:** Proprietäres Format, möglicherweise verschlüsselt

---

### 4. Excel-Export-Analyse

**Ziel:** BWA-Werte aus Excel-Exports extrahieren und mit DRIVE vergleichen

**Vorgehen:**
- ⏳ Excel-Exports von GlobalCube sammeln (verschiedene Filter)
- ⏳ Werte extrahieren (Zell-Referenzen)
- ⏳ Mit DRIVE-Werten vergleichen
- ⏳ Differenzen analysieren
- ⏳ Filter-Logik ableiten

**Dateien:**
- `scripts/globalcube_explorer.py` (Excel-Parsing erweitern)

---

### 5. Cognos API/SDK

**Ziel:** Direkter Zugriff auf Cognos-Daten über API

**Vorgehen:**
- ⏳ Cognos REST API testen (ältere Version, gibt HTML zurück)
- ⏳ Cognos SDK evaluieren (Java-basiert)
- ⏳ Alternative: Cognos BI Server API

**Herausforderung:** Ältere Cognos-Version, möglicherweise keine moderne REST API

---

## 📋 KONKRETER AKTIONSPLAN

### Phase 1: Portal Scraping (Priorität: HOCH)

1. **Session-Management implementieren**
   ```python
   # Login zu Cognos Portal
   session = requests.Session()
   login_response = session.post('http://10.80.80.10:9300/bi/', 
                                  data={'username': 'Greiner', 
                                        'password': 'Hawaii#22'})
   ```

2. **BWA-Reports finden**
   - Portal-Navigation durchsuchen
   - Report-Links identifizieren
   - Report-Parameter extrahieren

3. **Report-Daten scrapen**
   - HTML-Tabellen parsen
   - Oder Excel-Export anfordern
   - Werte extrahieren

**Erwartetes Ergebnis:** Exakte BWA-Werte für alle Standorte/Marken

---

### Phase 2: Struktur-Dateien vollständig analysieren (Priorität: HOCH)

1. **XML-Strukturen parsen**
   - `Struktur_GuV.xml` vollständig analysieren
   - Filter-Regeln identifizieren
   - Konten-Zuordnungen extrahieren

2. **Filter-Logik dokumentieren**
   - IF-THEN-Regeln für Standorte
   - Konten-Bereiche und Ausschlüsse
   - KST-Zuordnungen

**Erwartetes Ergebnis:** Vollständige Filter-Logik-Dokumentation

---

### Phase 3: Vergleichs-Analyse (Priorität: MITTEL)

1. **Systematischer Vergleich**
   - Alle BWA-Positionen für alle Standorte/Marken
   - Monat vs. YTD
   - Stückzahlen

2. **Differenz-Analyse**
   - Identifiziere Muster in Differenzen
   - Ableitung von Filter-Regeln

**Erwartetes Ergebnis:** Liste aller Differenzen mit möglichen Ursachen

---

## 🛠️ TOOLS & SKRIPTE

### Zu erweitern:

1. **`scripts/cognos_report_scraper.py`**
   - Session-Management hinzufügen
   - Report-Navigation implementieren
   - Daten-Extraktion

2. **`scripts/globalcube_explorer.py`**
   - XML-Parsing erweitern
   - Filter-Logik-Extraktion
   - Excel-Parsing verbessern

3. **`scripts/vergleiche_bwa_globalcube.py`** (NEU)
   - Systematischer Vergleich aller Positionen
   - Differenz-Analyse
   - Report-Generierung

---

## 🎯 ERWARTETE ERGEBNISSE

### Nach Phase 1 (Portal Scraping):
- ✅ Exakte BWA-Werte für alle Standorte/Marken
- ✅ Validierung der DRIVE-Werte
- ✅ Identifikation von Differenzen

### Nach Phase 2 (Struktur-Analyse):
- ✅ Vollständige Filter-Logik-Dokumentation
- ✅ Konten-Zuordnungen validiert
- ✅ Standort-Filter-Logik verstanden

### Nach Phase 3 (Vergleichs-Analyse):
- ✅ Alle Differenzen identifiziert
- ✅ Ursachen dokumentiert
- ✅ Korrekturen implementiert

---

## 🚀 NÄCHSTE SCHRITTE

1. **Sofort:** Portal Scraping implementieren (Session-Management)
2. **Parallel:** XML-Strukturen vollständig analysieren
3. **Dann:** Systematischer Vergleich aller Positionen

**Priorität:** Portal Scraping, da es die schnellste Methode ist, exakte Werte zu erhalten.

---

## 📝 NOTIZEN

- GlobalCube nutzt IBM Cognos BI (ältere Version)
- Portal: http://10.80.80.10:9300/bi/
- Login: Greiner / Hawaii#22
- Datenquelle: Locosoft PostgreSQL (wie DRIVE)
- MDC-Format: Proprietär, möglicherweise verschlüsselt
