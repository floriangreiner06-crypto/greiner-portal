# TODO für Claude - Session Start TAG 193

**Erstellt:** 2026-01-15 (TAG 192)  
**Nächste Session:** TAG 193

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

### 1. Email-Benachrichtigungen (TAG 192)

**Korrekturen durchgeführt:**
- ✅ Aktive Aufträge: Nur Laufzeit des aktiven Mechanikers
- ✅ Abgeschlossene Aufträge: Nur heute/gestern

**Datei:** `celery_app/tasks.py`

**Status:** Funktioniert, sollte überwacht werden

**Nächste Schritte:**
- Monitoring ob weitere Probleme auftreten
- Eventuell zusätzliche Filter oder Cooldown

### 2. Locosoft Support-Anfrage

**Dokumente sind vorbereitet:**
- `docs/locosoft_support_anfrage_aw_anteil.md` (Hauptdokument)
- `docs/locosoft_aw_anteil_fragenkatalog.md` (Referenz)
- Alle Dokumente sind nach Windows synchronisiert

**Nächste Schritte:**
- Prüfen, ob Antwort von Locosoft eingegangen ist
- Falls ja: AW-Berechnung anpassen
- Falls nein: Nachfragen oder alternative Lösungsansätze prüfen

### 3. AW-Berechnung (TAG 191)

**Aktuelle Implementierung:**
- Formel: `AW-Ant. = time_units_Position × (Stempelzeit_Mechaniker / Gesamt-Stempelzeit_Auftrag)`
- Berechnung pro Position, dann Summierung
- Wenn nur ein Mechaniker: AW-Ant. = time_units_Position

**Datei:** `api/werkstatt_data.py` (CTE `aw_verrechnet`)

**Status:** Funktioniert, aber kleine Abweichung zu Locosoft bleibt

### 4. Leistungsgrad-Dokumentation

**Erstellt für Team:**
- `docs/leistungsgrad_berechnung_erklaerung.md` (Detaillierte Erklärung)
- `docs/leistungsgrad_fairness_analyse.md` (Fairness-Bewertung)

**Ergebnis:**
- ✅ DRIVE-Formel ist fair und valide
- ✅ Fairer für Team-Vergleiche
- ⚠️ Unterschiedliche Aussage als Standard-Formel (beide sind korrekt)

---

## Code-Änderungen (TAG 192)

### Geänderte Dateien

**Backend:**
- `celery_app/tasks.py`
  - Email-Logik korrigiert (2 Fixes)
  - Query für abgeschlossene Aufträge auf heute/gestern beschränkt
  - Map-Erstellung korrigiert (aktive Aufträge zuerst)

**Scripts:**
- `scripts/test_email_ueberschreitung.py` (NEU)
  - Test-Script für Email-Überschreitungs-Benachrichtigungen

---

## Git Status

**Nicht committet:**
- Alle Änderungen von TAG 192
- **Empfehlung:** Commit mit Message "TAG 192: Email-Benachrichtigungen korrigiert - aktive Aufträge und alte Aufträge"

---

## Server-Sync

**Synchronisiert:**
- ✅ Alle Änderungen sind auf Server

**Pfad:** `/opt/greiner-portal/`

---

## Session-Kontext

**TAG 192 Fokus:**
- Email-Benachrichtigungen bei Zeitüberschreitungen korrigiert
- 2 Bugs behoben: Aktive Aufträge und alte Aufträge
- Test-Script erstellt

**Ergebnis:**
- ✅ Aktive Aufträge: Korrekte Laufzeit (nur aktiver Mechaniker)
- ✅ Abgeschlossene Aufträge: Nur heute/gestern
- ✅ Alte Aufträge: Werden nicht mehr benachrichtigt
- ✅ Service getestet und funktioniert

**Nächste Session (TAG 193):**
- Monitoring ob weitere Probleme auftreten
- Auf Locosoft-Antwort warten (AW-Berechnung)
- Eventuell weitere Verbesserungen an Email-Logik
