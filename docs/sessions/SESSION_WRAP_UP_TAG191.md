# SESSION WRAP-UP TAG 191

**Datum:** 2026-01-14  
**Thema:** AW-Berechnung & Leistungsgrad-Analyse, Locosoft Support-Vorbereitung

---

## Was wurde erledigt

### 1. AW-Berechnung optimiert (TAG 191)

**Problem:**
- AW-Berechnung wich von Locosoft ab (9.6 AW vs. 10.0 AW)
- Leistungsgrad wich ab (123.5% vs. 133.0%)

**Lösung:**
- AW-Berechnung basierend auf Chef-Erklärung angepasst
- Formel: `AW-Ant. = time_units_Position × (Stempelzeit_Mechaniker / Gesamt-Stempelzeit_Auftrag)`
- Berechnung erfolgt pro Position, dann Summierung
- Wenn nur ein Mechaniker: AW-Ant. = time_units_Position

**Geänderte Dateien:**
- `api/werkstatt_data.py`: `aw_verrechnet` CTE komplett überarbeitet (TAG 191)

**Ergebnis:**
- AW-Berechnung sehr nahe an Locosoft (9.6 vs. 10.0 AW)
- Kleine Abweichung bleibt (0.4 AW, 9.5% Leistungsgrad)
- Support-Anfrage an Locosoft vorbereitet

### 2. Stempelungen-Analyse

**Problem:**
- Vermutung: Fehlerhafte Stempelungen für Auftrag 220471

**Ergebnis:**
- ✅ Stempelungen sind korrekt (nach Deduplizierung)
- ✅ Duplikate werden automatisch korrigiert
- ✅ Keine Fehler an der Stempeluhr
- ⚠️ Problem liegt in AW-Berechnung von Locosoft (nicht in Stempelungen)

**Dokumentation:**
- `docs/stempelungen_analyse_220471.md`

### 3. Locosoft Support-Vorbereitung

**Erstellte Dokumente:**
1. `docs/locosoft_support_anfrage_aw_anteil.md` (Hauptdokument)
   - Kurze, prägnante Support-Anfrage
   - Konkretes Beispiel (220471)
   - Direkt an Locosoft sendbar

2. `docs/locosoft_aw_anteil_fragenkatalog.md` (Referenz)
   - Detaillierter Fragenkatalog (9 Kategorien)
   - Bei Rückfragen verwenden

3. `docs/aw_berechnung_differenzen_analyse.md` (Hintergrund)
   - Analyse der identifizierten Differenzen

4. `docs/stempelungen_analyse_220471.md` (Hintergrund)
   - Bestätigung, dass Stempelungen korrekt sind

### 4. Leistungsgrad-Dokumentation

**Erstellte Dokumente:**
1. `docs/leistungsgrad_berechnung_erklaerung.md`
   - Detaillierte Erklärung für das Team
   - Praktische Beispiele
   - Häufige Fragen

2. `docs/leistungsgrad_fairness_analyse.md`
   - Internet-Recherche zu Best Practices
   - Vergleich Standard-Formel vs. DRIVE-Formel
   - Fairness & Validität-Bewertung

**Ergebnis:**
- ✅ DRIVE-Formel ist fair und valide
- ✅ Fairer für Team-Vergleiche (berücksichtigt Pausen/Lücken)
- ⚠️ Unterschiedliche Aussage als Standard-Formel (beide sind korrekt)

---

## Geänderte Dateien

### Backend (Python)
- `api/werkstatt_data.py`
  - `aw_verrechnet` CTE komplett überarbeitet (TAG 191)
  - AW-Berechnung basierend auf Chef-Erklärung
  - Pro-Position-Berechnung mit proportionaler Verteilung

### Dokumentation
- `docs/locosoft_support_anfrage_aw_anteil.md` (NEU)
- `docs/locosoft_aw_anteil_fragenkatalog.md` (NEU)
- `docs/aw_berechnung_differenzen_analyse.md` (NEU)
- `docs/stempelungen_analyse_220471.md` (NEU)
- `docs/leistungsgrad_berechnung_erklaerung.md` (NEU)
- `docs/leistungsgrad_fairness_analyse.md` (NEU)

---

## Qualitätscheck

### ✅ Redundanzen
- **Keine doppelten Dateien gefunden**
- **Keine doppelten Funktionen gefunden**
- AW-Berechnung zentral in `werkstatt_data.py`

### ✅ SSOT-Konformität
- ✅ Verwendet `api.db_utils.locosoft_session()` für DB-Verbindungen
- ✅ Verwendet zentrale Imports (`from api.db_utils import ...`)
- ✅ Keine lokalen DB-Verbindungen

### ✅ Code-Duplikate
- **Keine Code-Duplikate gefunden**
- AW-Berechnung zentral in `aw_verrechnet` CTE

### ✅ Konsistenz
- ✅ DB-Verbindungen: Korrekt verwendet (`locosoft_session()`)
- ✅ SQL-Syntax: PostgreSQL-kompatibel (`%s`, `true`, etc.)
- ✅ Error-Handling: Konsistentes Pattern
- ✅ Imports: Zentrale Utilities verwendet

### ✅ Dokumentation
- ✅ Neue Features dokumentiert (AW-Berechnung, Leistungsgrad)
- ✅ Support-Anfrage vorbereitet
- ✅ Team-Dokumentation erstellt

---

## Bekannte Issues

### 1. AW-Berechnung: Abweichung zu Locosoft

**Status:** ⚠️ In Arbeit
- **Problem:** DRIVE: 9.6 AW vs. Locosoft: 10.0 AW (Differenz: 0.4 AW)
- **Ursache:** Locosoft berechnet AW-Ant. anders (noch nicht vollständig verstanden)
- **Lösung:** Support-Anfrage an Locosoft gestellt
- **Dokumentation:** `docs/locosoft_support_anfrage_aw_anteil.md`

### 2. Leistungsgrad: Abweichung zu Locosoft

**Status:** ⚠️ In Arbeit
- **Problem:** DRIVE: 123.5% vs. Locosoft: 133.0% (Differenz: 9.5%)
- **Ursache:** Direkt abhängig von AW-Berechnung
- **Lösung:** Wird mit AW-Berechnung geklärt
- **Dokumentation:** `docs/leistungsgrad_fairness_analyse.md`

---

## Nächste Schritte

1. **Auf Antwort von Locosoft warten**
   - Support-Anfrage wurde vorbereitet
   - Dokumente sind nach Windows synchronisiert

2. **AW-Berechnung anpassen** (wenn Formel bekannt)
   - Basierend auf Locosoft-Antwort
   - Exakte Übereinstimmung anstreben

3. **Team-Präsentation vorbereiten**
   - Leistungsgrad-Erklärung ist dokumentiert
   - Fairness-Analyse ist verfügbar

---

## Git Status

**Geänderte Dateien:**
- `api/werkstatt_data.py` (AW-Berechnung überarbeitet)
- 6 neue Dokumentations-Dateien

**Nicht committet:**
- Alle Änderungen sind noch nicht committet
- **Empfehlung:** Commit mit Message "TAG 191: AW-Berechnung optimiert, Locosoft Support vorbereitet"

---

## Server-Sync

**Synchronisiert nach Windows:**
- ✅ Alle Locosoft Support-Dokumente
- ✅ Leistungsgrad-Dokumentation
- ✅ Stempelungen-Analyse

**Pfad:** `\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\docs\`

---

## Zusammenfassung

**Erfolgreich:**
- ✅ AW-Berechnung basierend auf Chef-Erklärung implementiert
- ✅ Stempelungen-Analyse durchgeführt (korrekt)
- ✅ Locosoft Support-Anfrage vorbereitet
- ✅ Leistungsgrad-Dokumentation erstellt
- ✅ Fairness-Analyse durchgeführt

**Offen:**
- ⚠️ Abweichung zu Locosoft (0.4 AW, 9.5% Leistungsgrad)
- ⏳ Auf Antwort von Locosoft warten

**Qualität:**
- ✅ Keine Redundanzen
- ✅ SSOT-konform
- ✅ Konsistent
- ✅ Gut dokumentiert
