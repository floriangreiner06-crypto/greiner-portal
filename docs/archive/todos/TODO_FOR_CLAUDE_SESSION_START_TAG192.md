# TODO für Claude - Session Start TAG 192

**Erstellt:** 2026-01-14 (TAG 191)  
**Nächste Session:** TAG 192

---

## Offene Aufgaben

### 1. AW-Berechnung: Locosoft-Antwort abwarten ⏳

**Status:** Blockiert auf Locosoft Support
- **Support-Anfrage:** `docs/locosoft_support_anfrage_aw_anteil.md`
- **Fragenkatalog:** `docs/locosoft_aw_anteil_fragenkatalog.md`
- **Aktuell:** DRIVE: 9.6 AW vs. Locosoft: 10.0 AW (Differenz: 0.4 AW)

**Nächste Schritte:**
1. Auf Antwort von Locosoft warten
2. AW-Berechnung basierend auf Antwort anpassen
3. Exakte Übereinstimmung anstreben

**Dokumentation:**
- `docs/locosoft_support_anfrage_aw_anteil.md`
- `docs/aw_berechnung_differenzen_analyse.md`

### 2. Leistungsgrad: Abweichung klären ⏳

**Status:** Abhängig von AW-Berechnung
- **Aktuell:** DRIVE: 123.5% vs. Locosoft: 133.0% (Differenz: 9.5%)
- **Ursache:** Direkt abhängig von AW-Berechnung

**Nächste Schritte:**
1. Wird mit AW-Berechnung geklärt
2. Formel ggf. anpassen

**Dokumentation:**
- `docs/leistungsgrad_fairness_analyse.md`
- `docs/leistungsgrad_berechnung_erklaerung.md`

---

## Qualitätsprobleme (keine kritischen)

### ✅ Keine kritischen Qualitätsprobleme

**Status:** Alle Checks bestanden
- ✅ Keine Redundanzen
- ✅ SSOT-konform
- ✅ Konsistent
- ✅ Gut dokumentiert

---

## Wichtige Hinweise für nächste Session

### 1. Locosoft Support-Anfrage

**Dokumente sind vorbereitet:**
- `docs/locosoft_support_anfrage_aw_anteil.md` (Hauptdokument)
- `docs/locosoft_aw_anteil_fragenkatalog.md` (Referenz)
- Alle Dokumente sind nach Windows synchronisiert

**Nächste Schritte:**
- Prüfen, ob Antwort von Locosoft eingegangen ist
- Falls ja: AW-Berechnung anpassen
- Falls nein: Nachfragen oder alternative Lösungsansätze prüfen

### 2. AW-Berechnung (TAG 191)

**Aktuelle Implementierung:**
- Formel: `AW-Ant. = time_units_Position × (Stempelzeit_Mechaniker / Gesamt-Stempelzeit_Auftrag)`
- Berechnung pro Position, dann Summierung
- Wenn nur ein Mechaniker: AW-Ant. = time_units_Position

**Datei:** `api/werkstatt_data.py` (CTE `aw_verrechnet`)

**Status:** Funktioniert, aber kleine Abweichung zu Locosoft bleibt

### 3. Leistungsgrad-Dokumentation

**Erstellt für Team:**
- `docs/leistungsgrad_berechnung_erklaerung.md` (Detaillierte Erklärung)
- `docs/leistungsgrad_fairness_analyse.md` (Fairness-Bewertung)

**Ergebnis:**
- ✅ DRIVE-Formel ist fair und valide
- ✅ Fairer für Team-Vergleiche
- ⚠️ Unterschiedliche Aussage als Standard-Formel (beide sind korrekt)

### 4. Stempelungen-Analyse

**Ergebnis:**
- ✅ Stempelungen sind korrekt
- ✅ Duplikate werden automatisch korrigiert
- ✅ Keine Fehler an der Stempeluhr

**Dokumentation:** `docs/stempelungen_analyse_220471.md`

---

## Code-Änderungen (TAG 191)

### Geänderte Dateien

**Backend:**
- `api/werkstatt_data.py`
  - `aw_verrechnet` CTE komplett überarbeitet
  - AW-Berechnung basierend auf Chef-Erklärung
  - Pro-Position-Berechnung mit proportionaler Verteilung

**Dokumentation:**
- 6 neue Dokumentations-Dateien (siehe SESSION_WRAP_UP_TAG191.md)

---

## Git Status

**Nicht committet:**
- Alle Änderungen von TAG 191
- **Empfehlung:** Commit mit Message "TAG 191: AW-Berechnung optimiert, Locosoft Support vorbereitet"

---

## Server-Sync

**Synchronisiert:**
- ✅ Alle Locosoft Support-Dokumente
- ✅ Leistungsgrad-Dokumentation
- ✅ Stempelungen-Analyse

**Pfad:** `\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\docs\`

---

## Session-Kontext

**TAG 191 Fokus:**
- AW-Berechnung optimiert
- Locosoft Support-Anfrage vorbereitet
- Leistungsgrad-Dokumentation erstellt
- Fairness-Analyse durchgeführt

**Ergebnis:**
- ✅ AW-Berechnung sehr nahe an Locosoft (9.6 vs. 10.0 AW)
- ⚠️ Kleine Abweichung bleibt (wird mit Locosoft geklärt)
- ✅ Dokumentation vollständig

**Nächste Session (TAG 192):**
- Auf Locosoft-Antwort warten oder alternative Lösungsansätze prüfen
- AW-Berechnung ggf. anpassen
- Exakte Übereinstimmung anstreben
