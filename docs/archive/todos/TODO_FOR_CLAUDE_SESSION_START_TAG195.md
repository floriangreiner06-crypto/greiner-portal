# TODO für Claude - Session Start TAG 195

**Erstellt:** 2026-01-16  
**Letzte Session:** TAG 194

---

## 🔴 PRIORITÄT 1: Testing & Feedback

### 1. Alarm-E-Mail-Testing (TAG 194 Fix)
- [ ] **WICHTIG:** Bitte Alarm-E-Mails testen
- [ ] Prüfen ob E-Mails jetzt korrekt gesendet werden
- [ ] Test-Szenarien:
  - Mechaniker hat heute bereits 50 Min abgeschlossen, stempelt neu an (20 Min aktuell), Vorgabe 60 Min → **KEINE** E-Mail (nur aktuelle Stempelung)
  - Mechaniker arbeitet 70 Min aktuell, Vorgabe 60 Min → **E-Mail** wird gesendet
  - Mechaniker arbeitet 25 Min aktuell, Vorgabe 20 Min → **KEINE** E-Mail (< 30 Min Schwelle)
  - Abgeschlossener Auftrag, überschreitet Vorgabe → **E-Mail** wird gesendet
- [ ] Feedback geben: Funktionieren die E-Mails jetzt korrekt?

---

## 🟡 PRIORITÄT 2: SSOT-Verletzungen (optional)

### 1. BETRIEB_NAMEN zentralisieren
- [ ] **Problem:** `BETRIEB_NAMEN` in verschiedenen Dateien definiert
  - `api/standort_utils.py` (SSOT) ✅
  - `api/werkstatt_data.py` (Duplikat) ❌
  - `api/werkstatt_live_api.py` (Duplikat) ❌
  - `utils/locosoft_helpers.py` (Duplikat) ❌
- [ ] **Lösung:** Alle Dateien auf `api/standort_utils.BETRIEB_NAMEN` umstellen
- [ ] **Status:** Nicht verschlimmert in TAG 194, aber sollte behoben werden

---

## 🟢 PRIORITÄT 3: Weitere Optimierungen (optional)

### 1. Alarm-E-Mail-Logik weiter optimieren
- [ ] Prüfen ob 30 Min Schwelle optimal ist (basierend auf User-Feedback)
- [ ] Prüfen ob weitere Filter nötig sind
- [ ] Performance-Optimierung (falls nötig)

### 2. Dokumentation
- [ ] `docs/ALARM_EMAIL_TRIGGER_DEFINITION_TAG193.md` aktualisieren (TAG 194 Fix dokumentieren)
- [ ] Beispiel-Szenarien erweitern

---

## 📋 Offene Aufgaben aus vorherigen Sessions

### Aus TAG 193
- [ ] Navigation-Testing (falls noch nicht abgeschlossen)
- [ ] Weitere Tests durchführen

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

### Alarm-E-Mails (TAG 194 Fix)
- **WICHTIG:** Prüfung basiert jetzt auf `heute_session_min` (nur aktuelle Stempelung)
- Alle aktiven Aufträge werden in `ueberschritten_map` aufgenommen
- Die Prüfung, ob überschritten, erfolgt in der E-Mail-Logik
- Mindestlaufzeit-Schwelle: 30 Minuten
- Dokumentation: `docs/ALARM_EMAIL_TRIGGER_DEFINITION_TAG193.md` (sollte aktualisiert werden)

### Testing
- **WICHTIG:** Alarm-E-Mails testen (User-Feedback abwarten)
- Prüfen ob E-Mails jetzt korrekt gesendet werden

### Git
- Commit: `186b0f4 - fix(TAG194): Alarm-E-Mail-Bug - Prüfung basiert jetzt auf heute_session_min statt fortschritt_prozent`
- Service: Neugestartet und aktiv

---

## 🚀 Nächste Schritte (je nach Feedback)

### Szenario 1: Alles funktioniert
- SSOT-Verletzungen beheben (optional)
- Dokumentation aktualisieren
- Weitere Optimierungen (optional)

### Szenario 2: Probleme gefunden
- Bugs beheben
- Weitere Tests durchführen
- Logik anpassen falls nötig

---

**Status:** Warte auf User-Feedback zu TAG 194 Fix
