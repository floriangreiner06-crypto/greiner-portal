# TODO für Claude - Session Start TAG 194

**Erstellt:** 2026-01-16  
**Letzte Session:** TAG 193

---

## 🔴 PRIORITÄT 1: Testing & Feedback

### 1. Alarm-E-Mail-Testing
- [ ] **WICHTIG:** Bitte Alarm-E-Mails testen
- [ ] Prüfen ob E-Mails jetzt korrekt gesendet werden
- [ ] Test-Szenarien:
  - Mechaniker stempelt an, Auftrag bereits überschritten → **KEINE** E-Mail (nur aktuelle Stempelung)
  - Mechaniker arbeitet 35 Min, überschreitet Vorgabe → **E-Mail** wird gesendet
  - Abgeschlossener Auftrag, überschreitet Vorgabe → **E-Mail** wird gesendet
- [ ] Feedback geben: Funktionieren die E-Mails jetzt korrekt?

### 2. Navigation-Testing
- [ ] **WICHTIG:** Navigation vollständig testen
- [ ] Prüfen ob alle Links funktionieren
- [ ] Prüfen ob Sub-Dropdowns korrekt öffnen/schließen
- [ ] Prüfen ob keine Überlappungen mehr auftreten
- [ ] Feedback geben: Funktioniert die Navigation jetzt korrekt?

---

## 🟡 PRIORITÄT 2: SSOT-Verletzungen (optional)

### 1. BETRIEB_NAMEN zentralisieren
- [ ] **Problem:** `BETRIEB_NAMEN` in verschiedenen Dateien definiert
  - `api/standort_utils.py` (SSOT) ✅
  - `api/werkstatt_data.py` (Duplikat) ❌
  - `api/werkstatt_live_api.py` (Duplikat) ❌
  - `utils/locosoft_helpers.py` (Duplikat) ❌
- [ ] **Lösung:** Alle Dateien auf `api/standort_utils.BETRIEB_NAMEN` umstellen
- [ ] **Status:** Nicht verschlimmert in TAG 193, aber sollte behoben werden

---

## 🟢 PRIORITÄT 3: Weitere Optimierungen (optional)

### 1. Alarm-E-Mail-Logik weiter optimieren
- [ ] Prüfen ob 30 Min Schwelle optimal ist
- [ ] Prüfen ob weitere Filter nötig sind
- [ ] Performance-Optimierung (falls nötig)

### 2. Navigation weiter verbessern
- [ ] Prüfen ob weitere Verbesserungen nötig sind
- [ ] Mobile-Ansicht prüfen
- [ ] Accessibility prüfen

---

## 📋 Offene Aufgaben aus vorherigen Sessions

### Aus TAG 192
- [ ] Performance-Feedback (wurde bereits gegeben - besser ohne QA-Feature)
- [ ] QA-Dateien aufräumen (Entscheidung: Löschen oder aufbewahren?)

---

## 🔍 Qualitätsprobleme die behoben werden sollten

### 1. SSOT-Verletzungen
- [ ] `BETRIEB_NAMEN` zentralisieren (siehe oben)
- [ ] Weitere SSOT-Verletzungen prüfen

### 2. Code-Duplikate
- [ ] Prüfen ob weitere Code-Duplikate existieren
- [ ] Gemeinsame Patterns in Utilities verschieben

---

## 📝 Wichtige Hinweise für nächste Session

### Navigation
- Hover deaktiviert, nur Click-basiert
- Z-Index korrigiert (1100 für Sub-Dropdowns)
- `data-bs-toggle` von Sub-Dropdowns entfernt
- STATIC_VERSION: `20260116140000`

### Alarm-E-Mails
- Verwendet `heute_session_min` für aktive Aufträge
- Mindestlaufzeit-Schwelle: 30 Minuten
- Datums-Filter für `laufzeit_min` hinzugefügt
- Dokumentation: `docs/ALARM_EMAIL_TRIGGER_DEFINITION_TAG193.md`

### Testing
- **WICHTIG:** Alarm-E-Mails testen
- **WICHTIG:** Navigation vollständig testen

---

## 🚀 Nächste Schritte (je nach Feedback)

### Szenario 1: Alles funktioniert
- SSOT-Verletzungen beheben (optional)
- Weitere Optimierungen (optional)

### Szenario 2: Probleme gefunden
- Bugs beheben
- Weitere Tests durchführen

---

**Status:** Warte auf Test-Feedback
