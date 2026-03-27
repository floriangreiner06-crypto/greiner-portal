# 📋 ANLEITUNG FÜR HR: LOCOSOFT DATENPFLEGE

**Erstellt:** 08.12.2025 (TAG 102)  
**Aktualisiert:** 08.12.2025 (Ergebnisse aus Datenqualitäts-Check)  
**Für:** Vanessa (HR)  
**Zweck:** Bessere Datenqualität für automatische Auswertungen im Greiner Portal DRIVE

---

## 🎯 ZIEL

Wir wollen im **Greiner Portal DRIVE** automatische Auswertungen ermöglichen:
- ✅ Überstunden-Übersicht (ohne manuelles Rechnen!)
- ✅ Urlaubsplanung & Resturlaub
- ✅ Kapazitätsplanung Werkstatt
- ✅ Arbeitszeitkonto-Saldo

---

## 📊 AKTUELLER STAND (08.12.2025)

### ✅ Was GUT funktioniert:

| Bereich | Status |
|---------|--------|
| Stempelzeiten | ✅ 187.549 Einträge - vollständig |
| Abwesenheiten | ✅ 15.077 Einträge - vollständig |
| Aktive Mitarbeiter | ✅ 69 (ohne System-User) |
| Arbeitszeiten | ✅ 95 MA haben Daten hinterlegt |
| Pausenzeiten | ✅ Grundsätzlich vorhanden |

### ⚠️ Was KORRIGIERT werden muss:

| Problem | Anzahl MA | Priorität | Auswirkung |
|---------|-----------|-----------|------------|
| **Pausen fehlen** | 15 | 🔴 HOCH | Falsche Überstunden! |
| **Arbeitszeiten unvollständig** | 9 | 🔴 HOCH | Soll-Zeit falsch |
| **Produktivitätsfaktor = 0** | 29 | 🟡 MITTEL | Kapazitätsplanung ungenau |
| **Keine Gruppe** | 1 | 🟢 NIEDRIG | Urlaubsanträge nicht möglich |

---

## 🔴 PRIORITÄT 1: PAUSEN NACHPFLEGEN (15 Mitarbeiter)

**Diese Mitarbeiter haben KEINE Pausen hinterlegt:**

| MA-Nr | Name | Arbeitstage | Pausen | Fehlen |
|-------|------|-------------|--------|--------|
| 1016 | Brendel, Sandra | 5 | 0 | 5 |
| 4003 | Egner, Edith | 5 | 0 | 5 |
| 1031 | Geiger, Daniela | 5 | 0 | 5 |
| 1027 | Geppert, Katrin | 5 | 0 | 5 |
| 1001 | Gruber, Cornelia | 5 | 0 | 5 |
| 1019 | Klein, Götz | 5 | 0 | 5 |
| 1029 | Kramhöller, Katrina | 5 | 0 | 5 |
| 1015 | Lackerbeck, Brigitte | 5 | 0 | 5 |
| 5005 | Scheingraber, Wolfgang | 5 | 0 | 5 |
| 1011 | Scheppach, Zuzana | 5 | 0 | 5 |
| 1009 | Eiglmaier, Silvia | 3 | 0 | 3 |
| 1013 | Erlmeier, Rosmarie | 5 | 2 | 3 |
| 1017 | Schimmer, Sandra | 3 | 0 | 3 |
| 1005 | Aichinger, Christian | 5 | 3 | 2 |
| 1032 | Greindl, Bianca | 2 | 0 | 2 |

### So geht's in Locosoft:

1. **Pr. 811** aufrufen
2. **F9** drücken → Mitarbeiter suchen (Name oder MA-Nr.)
3. Tab **"Arbeitszeitregelungen"** öffnen
4. Für **jeden Arbeitstag** (Mo-Fr) Pause eintragen:
   - **Pause 1 von:** `12:00`
   - **Pause 1 bis:** `12:44` (= 44 Minuten)
5. **Speichern**

**💡 Tipp:** Mit **F5** können Daten aus der Vorzeile übernommen werden!

**⚠️ WICHTIG:** Fehlende Pausen bedeuten, dass die Überstunden-Berechnung um ca. 7 Stunden pro Monat FALSCH ist!

---

## 🔴 PRIORITÄT 2: ARBEITSZEITEN VERVOLLSTÄNDIGEN (9 Mitarbeiter)

**Diese Mitarbeiter haben unvollständige Arbeitszeiten:**

| MA-Nr | Name | Vorhandene Tage | Fehlen |
|-------|------|-----------------|--------|
| 1007 | Wieser, Paula | KEINE | Mo-Fr |
| 1010 | Aufschläger, Ramona | Mo | Di-Fr |
| 3000 | Kandler, Georg | Di | Mo, Mi-Fr |
| 1032 | Greindl, Bianca | Do, Fr | Mo-Mi |
| 1023 | Schreder, Margit | Di, Do | Mo, Mi, Fr |
| 1009 | Eiglmaier, Silvia | Mo, Di, Do | Mi, Fr |
| 1037 | Kerscher, Susanne | Di, Mi, Do | Mo, Fr |
| 1017 | Schimmer, Sandra | Mi, Do, Fr | Mo, Di |
| 1004 | Loibl, Margit | Mo, Di, Do, Fr | Mi |

### So geht's in Locosoft:

1. **Pr. 811** aufrufen
2. **F9** drücken → Mitarbeiter suchen
3. Tab **"Arbeitszeitregelungen"** öffnen
4. Im Bereich **"Arbeitszeithinterlegung"** für jeden fehlenden Tag:
   - **Arbeitszeit von:** z.B. `07:00`
   - **Arbeitszeit bis:** z.B. `16:59` (**NICHT** 17:00!)
   - **Pause 1 von:** `12:00`
   - **Pause 1 bis:** `12:44`
5. **Speichern**

**💡 Tipp:** Mit **F9** (Daten von Mitarbeiter holen) können Einstellungen eines anderen MA übernommen werden!

**⚠️ WICHTIG aus Locosoft-Handbuch:**
> "Umgangssprachlich: 'Ich arbeite von 9 - 17 Uhr' ist FALSCH, richtig ist 9 - 16.59 Uhr!"

---

## 🟡 PRIORITÄT 3: PRODUKTIVITÄTSFAKTOR SETZEN (29 Mitarbeiter)

**Diese PRODUKTIVEN Mitarbeiter (schedule_index=100) haben Leistungsfaktor = 0:**

| MA-Nr | Name | Monteur-Nr | Gruppe |
|-------|------|------------|--------|
| 5016 | Berger, Sascha | 5016 | MON |
| 5004 | Dederer, Andreas | 5004 | MON |
| 5024 | Ebner, Marius | 5024 | MON |
| 5008 | Ebner, Patrick | 5008 | MON |
| 5020 | Hoffmann, Lucas | 5020 | MON |
| 5014 | Litwin, Jaroslaw | 5014 | MON |
| 5018 | Majer, Jan | 5018 | MON |
| 5007 | Reitmeier, Tobias | 5007 | MON |
| 5005 | Scheingraber, Wolfgang | 5005 | MON |
| 5003 | Smola, Walter | 5003 | MON |
| 5027 | Löw, Luca-Emanuel | 5027 | A-W, MON |
| 5030 | Pursch, Vincent | 5030 | A-W |
| 5029 | Rolof, Angelo | 5029 | A-W |
| 5026 | Suttner, Andreas Karl | 5056 | A-W |
| 5028 | Thammer, Daniel | 5028 | A-W |
| 5025 | Wagner, Lena | 5025 | A-W |
| 5017 | Kreulinger, Luca | 5017 | MON, SB |
| 4000 | Huber, Herbert | 4000 | SB |
| 4002 | Keidl, Leonhard | 4002 | SER |
| 4005 | Kraus, Andreas | 4005 | SB |
| 5009 | Salmansberger, Valentin | 5009 | SB, SER |
| 3009 | Klammsteiner, Fabian | 3009 | A-L |
| 3007 | König, Matthias | 3007 | LAG |
| 1011 | Scheppach, Zuzana | 1011 | LAG |
| 1013 | Erlmeier, Rosmarie | 1013 | FA |
| 1019 | Klein, Götz | 1019 | FA |
| 1014 | Meyer, Christian | 1014 | FA |
| 1017 | Schimmer, Sandra | 1017 | FA |

### So geht's in Locosoft:

1. **Pr. 811** aufrufen
2. **F9** → Mitarbeiter suchen
3. Tab **"Kennzahlen/Indizes"** öffnen
4. Feld **"Leistungsfaktor"** ausfüllen:

| Mitarbeiter-Typ | Leistungsfaktor |
|-----------------|-----------------|
| Vollzeit-Mechaniker | **1.0** |
| Meister | **1.0 - 1.1** |
| Azubi 3. Lehrjahr | **0.8** |
| Azubi 2. Lehrjahr | **0.5** |
| Azubi 1. Lehrjahr | **0.3** |
| Verwaltung (nicht produktiv) | **0.0** (korrekt!) |

5. **Speichern**

**ℹ️ Hinweis:** Serviceberater (SER) mit schedule_index=0 können Leistungsfaktor=0 behalten, wenn sie nicht selbst produktiv arbeiten.

---

## 🟢 PRIORITÄT 4: GRUPPEN-ZUORDNUNG (1 Mitarbeiter)

| MA-Nr | Name |
|-------|------|
| 3000 | Kandler, Georg |

### So geht's in Locosoft:

1. **Pr. 811** aufrufen
2. **F9** → Mitarbeiter suchen
3. Tab **"Gruppen/Profile"** öffnen
4. Passende Gruppe zuweisen (z.B. LAG, VER, DIS)
5. **Speichern**

**⚠️ WICHTIG:** Ohne Gruppe sind keine Urlaubsanträge in Pr. 813 möglich!

---

## ✅ CHECKLISTE FÜR VANESSA

### Diese Woche (Priorität HOCH):
- [ ] **Pausen nachpflegen** für die 15 betroffenen MA
- [ ] **Arbeitszeiten vervollständigen** für die 9 betroffenen MA
- [ ] Datenqualitäts-Check erneut ausführen zur Kontrolle

### Bis Ende Dezember:
- [ ] **Produktivitätsfaktor** bei den 29 produktiven MA setzen
- [ ] **Gruppe zuweisen** für Kandler, Georg

### Bei Bedarf:
- [ ] Feiertage 2026 in Pr. 819 anlegen

---

## 🔧 DATENQUALITÄTS-CHECK SELBST AUSFÜHREN

Du kannst den Check jederzeit selbst auf dem Server ausführen:

```bash
# Per Putty auf 10.80.80.20 verbinden, dann:
cd /opt/greiner-portal
source venv/bin/activate
python3 scripts/hr_datenqualitaet_check.py
```

Das Script zeigt dir immer den aktuellen Stand der Datenqualität.

---

## 📞 KONTAKT

**Bei Fragen zur Datenpflege:**
- Florian Greiner

**Bei Fragen zu Locosoft:**
- Locosoft-Support (Hotline)

---

## 📊 GRUPPEN-ÜBERSICHT

Diese Gruppen sind bei Greiner angelegt:

| Code | Bedeutung | Anzahl MA |
|------|-----------|-----------|
| MON | Monteur/Werkstatt | 13 |
| SER | Service | 10 |
| VKB | Verkauf | 8 |
| LAG | Lager | 7 |
| A-W | Azubi Werkstatt | 6 |
| DIS | Disposition | 6 |
| FA | Fahrzeugannahme | 5 |
| CC | Call-Center | 5 |
| SB | Serviceberater | 4 |
| VER | Verwaltung | 4 |
| GL | Geschäftsleitung | 2 |
| FL | Filialleiter | 2 |
| A-L | Azubi Lager | 2 |
| MAR | Marketing | 2 |

---

*Erstellt am 08.12.2025 - Greiner Portal DRIVE TAG 102*
