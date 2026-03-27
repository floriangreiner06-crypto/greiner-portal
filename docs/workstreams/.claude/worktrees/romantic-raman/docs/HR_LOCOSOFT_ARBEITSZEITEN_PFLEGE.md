# 📋 LOCOSOFT ARBEITSZEITEN - PFLEGEHINWEISE FÜR HR

**Erstellt:** 2025-12-05 (TAG 94)  
**Hintergrund:** Analyse der Arbeitszeiten-Daten für Kapazitätsplanung

---

## ⚠️ PROBLEM GEFUNDEN

Bei der Analyse der Locosoft-Datenbank wurde festgestellt:

| Feld | Soll | Ist |
|------|------|-----|
| `employees_worktimes.is_latest_record` | `true` für aktuellen Eintrag | **IMMER NULL** |

**Auswirkung:** Die Kennzeichnung "aktueller Datensatz" fehlt. Das Portal kann die Daten trotzdem nutzen (über Datum-Sortierung), aber es ist nicht sauber gepflegt.

---

## 📊 AKTUELLE DATENLAGE

### Positiv ✅
- **487 Arbeitszeit-Einträge** vorhanden
- **Alle 17 Mechaniker** (5000-5999) haben Arbeitszeiten gepflegt
- Daten enthalten: Wochentag, Start, Ende, Dauer

### Beispiel aus der Datenbank:
```
MA 5003 | Smola,Walter  | Tag 4 (Fr) | Dauer: 8.0h | Von: 07:00 | Bis: 16:00
MA 5004 | Dederer,Andreas | Tag 4 (Fr) | Dauer: 8.0h | Von: 07:00 | Bis: 16:00
```

---

## 🔧 EMPFEHLUNG: LOCOSOFT RICHTIG PFLEGEN

### 1. Arbeitszeiten-Modul in Locosoft

**Pfad:** Stammdaten → Mitarbeiter → [Mitarbeiter wählen] → Reiter "Arbeitszeiten"

### 2. Pflege-Checkliste pro Mitarbeiter

- [ ] **Gültig ab-Datum** setzen (bei Änderungen neuen Eintrag mit aktuellem Datum)
- [ ] **Für jeden Arbeitstag** (Mo-Fr, ggf. Sa):
  - Arbeitszeit-Start (z.B. 07:00)
  - Arbeitszeit-Ende (z.B. 16:00)  
  - Arbeitsdauer in Stunden (z.B. 8.0)
- [ ] **Pausenzeiten** korrekt abziehen (Dauer = Ende - Start - Pause)

### 3. Bei Arbeitszeitänderungen

**NICHT** den alten Eintrag überschreiben, sondern:

1. Neuen Eintrag mit **aktuellem "Gültig ab"-Datum** anlegen
2. Alte Einträge bleiben für Historie erhalten
3. Das System nimmt automatisch den neuesten Eintrag

### 4. Produktivitätsfaktor (optional)

In `employees_history` gibt es das Feld `productivity_factor`:
- **1.0** = Vollzeit-Mechaniker (100% produktiv)
- **0.8** = 80% produktiv (z.B. Teilzeit oder Auszubildende)
- **0.0** = Nicht produktiv (z.B. Meister mit Verwaltungsaufgaben)

**Aktuell:** Fast alle Mechaniker haben `productivity_factor = 0.0` - das sollte korrigiert werden!

---

## 📈 NUTZEN FÜR KAPAZITÄTSPLANUNG

Mit korrekten Daten kann das Portal berechnen:

| Kennzahl | Berechnung |
|----------|------------|
| **Tageskapazität** | Summe(Arbeitszeit) aller anwesenden Mechaniker × 6 AW/h |
| **Verfügbar** | Tageskapazität - Abwesende (Urlaub, Krank) |
| **Auslastung** | Geplante Aufträge (AW) / Verfügbare Kapazität |

### Beispiel heute (05.12.2025):
```
Verfügbar:       13 Mechaniker × 8h × 6 AW = 624 AW
Geplante Arbeit: 123 AW (10 Termine)
Auslastung:      ~20% (nur Termine - offene Aufträge zusätzlich!)
```

---

## 🎯 KONKRETE AUFGABEN FÜR HR

### Sofort:
1. **Produktivitätsfaktor** für alle Mechaniker auf 1.0 setzen (außer Azubis/Meister)

### Bei nächster Gelegenheit:
2. **Arbeitszeiten prüfen** - stimmen die Einträge noch?
3. **Neue Mitarbeiter** - Arbeitszeiten direkt bei Anlage pflegen

### Langfristig:
4. Bei Locosoft-Support nachfragen warum `is_latest_record` nicht gepflegt wird

---

## 📞 KONTAKT

Bei Fragen zur Kapazitätsplanung im Portal:
- Portal-Entwicklung: [Claude-Projekt TAG 94]
- Datenbank: Locosoft PostgreSQL (`employees_worktimes`, `employees_history`)

---

*Diese Dokumentation ist Teil des Greiner Portal Projekts.*
