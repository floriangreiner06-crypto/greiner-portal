# TODO für Claude - Session Start TAG 196

**Erstellt:** 2026-01-16  
**Letzte Session:** TAG 195 (Teil 2)

---

## ✅ ERFOLGREICH ABGESCHLOSSEN (TAG 195)

### 1. Fahrzeugbeschreibung-Generierung ✅
- **Status:** ✅ Implementiert
- **Endpoint:** `POST /api/ai/generiere/fahrzeugbeschreibung/<dealer_vehicle_number>`
- **Features:**
  - Automatische Beschreibung (150-200 Wörter)
  - Verkaufsargumente (3-5 Punkte)
  - SEO-Keywords (5-10 Begriffe)
  - Elektrofahrzeug-Erkennung
  - Typ-Mapping korrigiert (V = Vorführwagen, L = Leihgabe/Mietwagen)

### 2. Modell-Umstellung ✅
- **Status:** ✅ Umgestellt
- **Von:** `allenai/olmo-3-32b-think` (Think-Modell)
- **Zu:** `mistralai/magistral-small-2509` (bessere JSON-Ausgaben)
- **Alle Use Cases:** Verwenden jetzt mistralai

### 3. Modell-Vergleich & Testing ✅
- **Status:** ✅ Getestet
- **Ergebnis:** `qwen/qwen3-coder-30b` ist besser (41% schneller, detaillierter)
- **Empfehlung:** Optional für Fahrzeugbeschreibung umstellen

### 4. Dokumentation ✅
- **Status:** ✅ Vollständig dokumentiert
- **Dateien:** 6 neue Dokumentations-Dateien

---

## 🔴 PRIORITÄT 1: BWA-Fehleranalyse mit KI

### 1. BWA-Fehleranalyse Use Case ✅ NEU
- **Ziel:** Lokale KI verwenden um Fehler in DRIVE BWA im Vergleich zur Globalcube BWA zu identifizieren und beheben
- **Datenquellen:**
  - ✅ Umfassende Analysen vorhanden
  - ✅ Alle Excel-Dateien aus Globalcube verfügbar
  - ✅ Server-Laufwerkszugriff für Globalcube vorhanden
- **Anforderungen:**
  - KI soll Unterschiede zwischen DRIVE BWA und Globalcube BWA analysieren
  - Fehler identifizieren
  - Behebungsvorschläge generieren
- **Nächste Schritte:**
  1. [ ] Datenquellen analysieren (Excel-Dateien, Server-Zugriff)
  2. [ ] Use Case definieren (welche Fehler sollen analysiert werden?)
  3. [ ] API-Endpoint erstellen: `/api/ai/analysiere/bwa-fehler`
  4. [ ] Prompt-Engineering für BWA-Analyse
  5. [ ] Testing mit echten Daten
  6. [ ] Behebungsvorschläge implementieren

### 2. Datenquellen prüfen
- [ ] **WICHTIG:** Excel-Dateien aus Globalcube analysieren
- [ ] Struktur verstehen (welche Spalten, welche Daten?)
- [ ] Server-Laufwerkszugriff prüfen (Pfad, Format, Zugriffsrechte)
- [ ] DRIVE BWA-Daten strukturieren (welche Daten sind verfügbar?)

### 3. Fehlerkategorien definieren
- [ ] **WICHTIG:** Welche Fehler sollen analysiert werden?
- [ ] Mögliche Kategorien:
  - Abweichungen in Kontenwerten
  - Fehlende Buchungen
  - Falsche Zuordnungen
  - Zeitliche Abweichungen
  - Berechnungsfehler
- [ ] Prioritäten setzen (welche Fehler sind am kritischsten?)

---

## 🟡 PRIORITÄT 2: Modell-Optimierung (optional)

### 1. Fahrzeugbeschreibung Modell wechseln (optional)
- [ ] **Optional:** `qwen/qwen3-coder-30b` für Fahrzeugbeschreibung
- [ ] Vorteile: 41% schneller, detaillierter, reine DE
- [ ] Code-Änderung: `api/ai_api.py` Zeile 948

### 2. Few-Shot Learning implementieren
- [ ] Beispiel-Datenbank erstellen (`fahrzeug_beschreibung_beispiele`)
- [ ] 10-20 Beispiele sammeln
- [ ] API erweitern mit Beispiel-Auswahl
- [ ] Prompt erweitern mit Beispielen

---

## 🟢 PRIORITÄT 3: Weitere KI-Use Cases (optional)

### 1. Arbeitskarten-Dokumentationsprüfung Frontend
- [ ] **Optional:** Frontend-Integration für Arbeitskarten-Prüfung
- [ ] Button in Arbeitskarte-Ansicht
- [ ] Modal mit Prüfungsergebnissen

### 2. Garantie-Dokumentationsprüfung
- [ ] **Optional:** Endpoint implementieren
- [ ] Integration in Garantie-Workflow
- [ ] Frontend-Integration

---

## 📋 Offene Aufgaben aus vorherigen Sessions

### Aus TAG 195
- [x] Fahrzeugbeschreibung-Generierung ✅
- [x] Modell-Umstellung ✅
- [x] Modell-Vergleich ✅
- [ ] Few-Shot Learning ⏳
- [ ] RAG-Integration ⏳

### Aus TAG 195 (Teil 1)
- [ ] TT-Zeit-Analyse Testing ⏳
- [ ] Feedback sammeln ⏳

---

## 🔍 Qualitätsprobleme die behoben werden sollten

### 1. SSOT-Verletzungen (nicht neu)
- [ ] `BETRIEB_NAMEN` zentralisieren
- [ ] Weitere SSOT-Verletzungen prüfen

### 2. Code-Duplikate (nicht neu)
- [ ] Prüfen ob weitere Code-Duplikate existieren
- [ ] Gemeinsame Patterns in Utilities verschieben

---

## 📝 Wichtige Hinweise für nächste Session

### BWA-Fehleranalyse (NEU - PRIORITÄT 1)
- **WICHTIG:** Neuer Use Case für KI-gestützte BWA-Fehleranalyse
- **Datenquellen:**
  - Excel-Dateien aus Globalcube verfügbar
  - Server-Laufwerkszugriff für Globalcube vorhanden
  - Umfassende Analysen bereits durchgeführt
- **Ziel:** Fehler identifizieren und beheben
- **Status:** ⏳ Zu implementieren

### Modell-Optimierung (TAG 195)
- **WICHTIG:** `qwen/qwen3-coder-30b` ist besser für Fahrzeugbeschreibung
- Empfehlung: Optional umstellen (41% schneller, detaillierter)
- **Status:** ✅ Getestet, optional umzustellen

### Modell-Umstellung (TAG 195)
- **WICHTIG:** Alle Use Cases verwenden jetzt `mistralai/magistral-small-2509`
- Default-Modell geändert (bessere JSON-Ausgaben)
- **Status:** ✅ Umgestellt

### Server-Neustart (TAG 195)
- **WICHTIG:** Server-Neustart erforderlich nach `api/ai_api.py` Änderungen
- Empfehlung: `sudo systemctl restart greiner-portal`
- **Status:** ⏳ Wartet auf Neustart

### Dokumentation (TAG 195)
- **WICHTIG:** Umfangreiche Dokumentation erstellt
- 6 neue Dokumentations-Dateien
- **Status:** ✅ Vollständig dokumentiert

---

## 🚀 Nächste Schritte (je nach Priorität)

### Szenario 1: BWA-Fehleranalyse (PRIORITÄT 1)
1. Datenquellen analysieren
2. Use Case definieren
3. API-Endpoint erstellen
4. Testing mit echten Daten
5. Behebungsvorschläge implementieren

### Szenario 2: Modell-Optimierung (optional)
1. Fahrzeugbeschreibung auf `qwen3-coder` umstellen
2. Few-Shot Learning implementieren
3. Weitere Tests durchführen

### Szenario 3: Weitere Use Cases (optional)
1. Arbeitskarten-Prüfung Frontend
2. Garantie-Dokumentationsprüfung
3. Weitere KI-Use Cases

---

**Status:** BWA-Fehleranalyse Use Case definiert, wartet auf Implementierung ⏳
