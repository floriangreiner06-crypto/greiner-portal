# 📋 ANLEITUNG FÜR HR: LOCOSOFT DATENPFLEGE VERBESSERN

**Erstellt:** 08.12.2025 (TAG 102)  
**Für:** Vanessa (HR)  
**Zweck:** Bessere Datenqualität für automatische Auswertungen im Greiner Portal

---

## 🎯 WARUM IST DAS WICHTIG?

Wir entwickeln im **Greiner Portal DRIVE** automatische Auswertungen für:
- ✅ Überstunden-Übersicht (ohne manuelles Zusammenrechnen!)
- ✅ Urlaubsplanung & Resturlaub
- ✅ Kapazitätsplanung Werkstatt
- ✅ Arbeitszeitkonto-Saldo

**Problem:** Die Daten in Locosoft sind teilweise unvollständig oder nicht gepflegt. Dadurch müsst ihr vieles manuell machen, was eigentlich automatisch gehen könnte!

---

## 🔍 WAS WIR GEFUNDEN HABEN (Analyse 08.12.2025)

### ✅ Was GUT gepflegt ist:
| Bereich | Status | Bemerkung |
|---------|--------|-----------|
| Stempelzeiten | ✅ | 187.549 Einträge vorhanden |
| Abwesenheiten (Urlaub, Krank) | ✅ | 15.077 Einträge |
| Mitarbeiter-Stammdaten | ✅ | 71 aktive MA |
| Arbeitszeiten (Soll pro Tag) | ✅ | Für die meisten MA gepflegt |

### ⚠️ Was FEHLT oder UNVOLLSTÄNDIG ist:

| Bereich | Problem | Auswirkung |
|---------|---------|------------|
| **Pausen** | Nur für Di/Mi/Do gepflegt, Mo/Fr fehlen! | Überstunden falsch berechnet |
| **Urlaubsanspruch** | NICHT in Locosoft! | Muss manuell nachgehalten werden |
| **Produktivitätsfaktor** | Bei 116 von 117 MA = 0.0 | Kapazitätsplanung funktioniert nicht |
| **Arbeitszeitkonto-Saldo** | Nicht in DB exportiert | Keine automatische Übersicht möglich |
| **Montag-Arbeitszeit** | Bei vielen MA fehlt Montag! | Soll-Ist-Vergleich unvollständig |

---

## 📝 KONKRETE AUFGABEN FÜR LOCOSOFT

### 1️⃣ PAUSEN VOLLSTÄNDIG PFLEGEN (PRIORITÄT HOCH!)

**Wo:** Stammdaten → Mitarbeiter → [MA wählen] → Reiter "Pausenzeiten"

**Problem gefunden bei MA 1005 (Aichinger):**
```
Aktuell gepflegt:     Di, Mi, Do = 44 Min Pause
FEHLT:                Mo, Fr = KEINE Pause eingetragen!
```

**Aber:** Im Monatsabschluss werden Fr +45min manuell korrigiert!

**Aufgabe:**
- [ ] Für ALLE Mitarbeiter prüfen: Sind Mo-Fr Pausen eingetragen?
- [ ] Standard-Pause (45 Min, 12:00-12:45) für alle Wochentage eintragen
- [ ] Bei Teilzeit-MA: Angepasste Pausen eintragen

**Frage an Locosoft-Support:**
> "Wie können wir die Pausenzeiten für alle Mitarbeiter auf einmal prüfen/aktualisieren? Gibt es einen Sammel-Import oder eine Übersicht?"

---

### 2️⃣ ARBEITSZEITEN MONTAG NACHTRAGEN (PRIORITÄT HOCH!)

**Wo:** Stammdaten → Mitarbeiter → [MA wählen] → Reiter "Arbeitszeiten"

**Problem:** Bei vielen MA fehlt der Montag komplett!

**Beispiel MA 1005:**
```
Aktuell:  Di=8h, Mi=8h, Do=8h, Fr=8h, Sa=8h
FEHLT:    Mo = NICHT EINGETRAGEN!
```

**Aufgabe:**
- [ ] Für alle MA prüfen: Ist Montag eingetragen?
- [ ] Fehlende Montage nachtragen (Standard: 8:00h, 08:00-16:44)

**Frage an Locosoft-Support:**
> "Können Sie uns eine Liste aller Mitarbeiter geben, bei denen Arbeitszeiten für bestimmte Wochentage fehlen?"

---

### 3️⃣ PRODUKTIVITÄTSFAKTOR SETZEN (PRIORITÄT MITTEL)

**Wo:** Stammdaten → Mitarbeiter → [MA wählen] → Reiter "Allgemein" oder "Werkstatt"

**Problem:** 116 von 117 Mitarbeitern haben `productivity_factor = 0.0`

**Was bedeutet das?**
- **1.0** = Vollzeit-Mechaniker (100% produktiv)
- **0.8** = 80% produktiv (z.B. Azubi im 3. Lehrjahr)
- **0.5** = 50% produktiv (z.B. Azubi im 1. Lehrjahr)
- **0.0** = Nicht produktiv (Verwaltung, Verkauf)

**Aufgabe:**
- [ ] Für alle MECHANIKER (5000-5999): Produktivitätsfaktor auf **1.0** setzen
- [ ] Für Azubis: Je nach Lehrjahr 0.5-0.8
- [ ] Meister/Serviceberater: 0.3-0.5 (teils produktiv)

**Aktuell korrekt:** Nur MA 5002 (Raith, Christian) hat 1.0

**Frage an Locosoft-Support:**
> "Wo genau wird der Produktivitätsfaktor gepflegt? Können wir das für mehrere MA gleichzeitig ändern?"

---

### 4️⃣ URLAUBSANSPRUCH IN LOCOSOFT (PRIORITÄT HOCH!)

**Problem:** Der Urlaubsanspruch pro Mitarbeiter ist NICHT in der Locosoft-Datenbank!

**Aktuell im PDF sichtbar:**
```
MA 1005: Urlaubsanspruch = 27 Tage
```

**Aber:** Diese Information ist nicht in den Tabellen, die wir auslesen können!

**Fragen an Locosoft-Support:**
> 1. "Wo wird der Urlaubsanspruch pro Mitarbeiter gepflegt?"
> 2. "Wird der Anspruch in einer Tabelle gespeichert, die wir per SQL auslesen können?"
> 3. "Gibt es eine Tabelle für Urlaubsansprüche pro Jahr?"

**Falls nicht in Locosoft möglich:**
→ Wir pflegen den Urlaubsanspruch dann im Greiner Portal (haben wir schon vorbereitet!)

---

### 5️⃣ ARBEITSZEITKONTO-SALDO EXPORTIEREN (PRIORITÄT MITTEL)

**Problem:** Der Saldo (z.B. 318:55h bei MA 1005) ist nicht in der Datenbank!

**Aktuell:** Der Saldo wird nur beim Monatsabschluss im PDF angezeigt, aber nicht gespeichert.

**Fragen an Locosoft-Support:**
> 1. "Gibt es eine Möglichkeit, den Arbeitszeitkonto-Saldo pro MA in eine Tabelle zu exportieren?"
> 2. "Können wir einen automatischen Export nach dem Monatsabschluss einrichten?"
> 3. "Gibt es eine Schnittstelle (API, CSV-Export) für Zeitkonto-Daten?"

**Alternative:** Wir berechnen den Saldo selbst aus den Stempelzeiten (aber dann brauchen wir einen Startwert!)

---

### 6️⃣ `is_latest_record` FLAG SETZEN (PRIORITÄT NIEDRIG)

**Wo:** Technische Einstellung in Locosoft

**Problem:** In den Tabellen `employees_history`, `employees_worktimes`, `employees_breaktimes` ist das Feld `is_latest_record` IMMER NULL.

**Sollte sein:** `true` für den aktuellsten Datensatz pro MA

**Frage an Locosoft-Support:**
> "Das Feld `is_latest_record` in den Mitarbeiter-Tabellen ist nie gesetzt. Ist das ein Konfigurationsproblem? Wie können wir das aktivieren?"

---

## 📊 ÜBERSICHT: WAS BRINGT DAS?

| Wenn gepflegt... | ...dann automatisch möglich: |
|------------------|------------------------------|
| Pausen vollständig | ✅ Korrekte Überstunden-Berechnung |
| Arbeitszeiten Mo-Fr | ✅ Soll-Ist-Vergleich pro Woche |
| Produktivitätsfaktor | ✅ Werkstatt-Kapazitätsplanung |
| Urlaubsanspruch | ✅ Resturlaub-Übersicht im Portal |
| Saldo-Export | ✅ Arbeitszeitkonto ohne manuelles Rechnen |

**Ergebnis:** Weniger manuelle Arbeit beim Monatsabschluss! 🎉

---

## 📞 KONTAKT LOCOSOFT-SUPPORT

**Hotline:** [Locosoft Support-Nummer eintragen]

**Themen für den Anruf:**
1. Pausenzeiten-Pflege (Sammel-Funktion?)
2. Arbeitszeiten-Übersicht (fehlende Wochentage finden)
3. Produktivitätsfaktor-Pflege
4. Urlaubsanspruch - wo gespeichert?
5. Arbeitszeitkonto-Export
6. `is_latest_record` Flag

---

## 📋 CHECKLISTE FÜR VANESSA

### Sofort (diese Woche):
- [ ] Locosoft-Support kontaktieren mit obigen Fragen
- [ ] Pausen für 5-10 Test-MA vollständig pflegen
- [ ] Rückmeldung an Florian, was möglich ist

### Kurzfristig (bis Ende Dezember):
- [ ] Pausen für ALLE MA vervollständigen
- [ ] Montag-Arbeitszeiten nachtragen
- [ ] Produktivitätsfaktor für Mechaniker setzen

### Mittelfristig (Q1 2026):
- [ ] Urlaubsanspruch-Lösung klären (Locosoft oder Portal?)
- [ ] Saldo-Export einrichten (falls möglich)

---

## ❓ FRAGEN?

Bei Unklarheiten:
- **Florian Greiner** (Portal-Entwicklung)
- **Claude/AI** (technische Analyse)

---

*Dieses Dokument ist Teil des Greiner Portal DRIVE Projekts.*  
*Erstellt auf Basis der Datenanalyse vom 08.12.2025*
