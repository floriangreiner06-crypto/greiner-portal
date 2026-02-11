# TODO für Session Start TAG 199

**Erstellt:** TAG 198  
**Datum:** 2026-01-XX

---

## Offene Aufgaben

### 1. Locosoft-Support-Antwort abwarten (aus TAG 197)
- **Status:** Frage wurde erstellt (`docs/LOCOSOFT_SUPPORT_FRAGE_AW_ANTEIL.md`)
- **Nächster Schritt:** Support kontaktieren und Antwort abwarten
- **Priorität:** Hoch

### 2. AW-Anteil-Berechnung korrigieren (aus TAG 197)
- **Status:** Aktuell -27.0% Abweichung (verbessert von -49.5%)
- **Nächster Schritt:** Basierend auf Locosoft-Support-Antwort implementieren
- **Ziel:** < 1% Abweichung zu Locosoft
- **Priorität:** Hoch

### 3. Weitere Tests durchführen (aus TAG 197)
- **Status:** Nur Tobias (5007) für Dezember getestet
- **Nächster Schritt:** 
  - Weitere Mechaniker testen
  - Weitere Zeiträume testen (Januar, etc.)
  - Christian Raith (5002) für Dezember testen
- **Priorität:** Mittel

### 4. Garantie SOAP API testen
- **Status:** API-Endpunkte vorhanden, muss getestet werden
- **Nächster Schritt:** Vollständige Implementierung testen
- **Priorität:** Mittel

---

## Qualitätsprobleme (optional)

### 1. Analyse-Scripts aufräumen
- **Problem:** Viele temporäre Analyse-Scripts mit ähnlicher Logik
- **Lösung:** 
  - Gemeinsame Funktionen (parse_zeit, parse_prozent) in Utility-Modul auslagern
  - Alte Scripts in `scripts/archive/` verschieben
- **Priorität:** Niedrig

---

## Wichtige Hinweise für nächste Session

### 1. AW-Anteil-Berechnung
- **Aktuelle Implementierung:** ALLE Positionen von Aufträgen mit Stempelung
- **Ergebnis:** 621.5 AW (3729 Min) vs. Locosoft 851 AW (5106 Min)
- **Faktor:** 1.369 würde passen, aber wahrscheinlich andere Logik
- **Warten auf:** Locosoft-Support-Antwort

### 2. Stmp.Anteil-Berechnung
- **Status:** ✅ **Korrekt implementiert** (75% der Gesamt-Dauer)
- **Abweichung:** -0.1% (sehr gut!)
- **Keine Änderungen nötig**

### 3. Leistungsgrad-Formel
- **Formel:** `Leistungsgrad = (AW-Anteil / Stmp.Anteil) × 100`
- **Status:** ✅ **Korrekt implementiert**
- **Problem:** Nur AW-Anteil ist falsch, nicht die Formel

### 4. Dokumentation (TAG 198)
- **Erstellt:**
  - `docs/DRIVE_FEATURES_BETRIEBSVERSAMMLUNG_22_01_2026.md` - Feature-Übersicht
  - `docs/DRIVE_PORTAL_GESAMTDOKUMENTATION_TAG198.md` - Gesamtdokumentation
- **Gesynct:** Alle relevanten Dokumentationsdateien für Claude verfügbar

---

## Kontext aus TAG 198

- **Hauptfokus:** Dokumentation für Betriebsversammlung & Gesamtdokumentation
- **Ergebnis:** 
  - Feature-Übersicht erstellt
  - Gesamtdokumentation mit Stand, Aufwand, Erfolgen erstellt
  - Bestehende Dokumentation für Claude gesynct
- **Keine Code-Änderungen:** Nur Dokumentation

---

## Kontext aus TAG 197

- **Hauptproblem:** AW-Anteil-Berechnung weicht um -27.0% ab
- **Lösungsansatz:** 7 Hypothesen getestet, beste gefunden und implementiert
- **Ergebnis:** Verbesserung von -49.5% auf -27.0%, aber noch nicht perfekt
- **Nächster Schritt:** Locosoft-Support kontaktieren

---

## Server-Sync

**Wichtig:** Nach Git-Commit auf Server syncen:
```bash
# Auf Windows (Srvrdb01):
# Dateien werden automatisch gesynct via \\Srvrdb01\Allgemein\Greiner Portal\...

# Auf Server (10.80.80.20):
cd /opt/greiner-portal
git pull
sudo systemctl restart greiner-portal  # Nur wenn Python-Code geändert wurde
```

**Hinweis:** TAG 198 hatte **keine Code-Änderungen** → **Kein Restart nötig!**

---

## Dokumentation für Betriebsversammlung

**Erstellt in TAG 198:**
- `docs/DRIVE_FEATURES_BETRIEBSVERSAMMLUNG_22_01_2026.md` - Feature-Übersicht
- `docs/DRIVE_PORTAL_GESAMTDOKUMENTATION_TAG198.md` - Gesamtdokumentation

**Verfügbar für Claude:**
- Alle relevanten Dokumentationsdateien wurden nach Windows gesynct
- Verfügbar unter: `\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\docs\`

---

## Nächste Prioritäten

1. **Locosoft-Support kontaktieren** (Hoch)
2. **AW-Anteil-Berechnung korrigieren** (Hoch)
3. **Weitere Tests durchführen** (Mittel)
4. **Garantie SOAP API testen** (Mittel)

---

**Erstellt:** TAG 198  
**Nächste Session:** TAG 199
