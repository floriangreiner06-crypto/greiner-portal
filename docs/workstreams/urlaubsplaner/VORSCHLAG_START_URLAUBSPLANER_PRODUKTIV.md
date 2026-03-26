# Vorschlag: Urlaubsplaner produktiv starten – Vorgehensweise

**Ausgangslage:**  
Tage werden in DRIVE im Kalender angezeigt (z. B. aus Locosoft/Import), aber die **Resturlaubsberechnung** basiert nur auf Einträgen in `vacation_bookings` (type_id = 1). Dadurch: Anzeige (viele Tage) und Rest-Zahl (z. B. 26) passen nicht zusammen – zwei Quellen, keine klare Führung. So ist ein produktiver Start nicht sinnvoll.

**Ziel:**  
Eine klare, einfache Führung: **DRIVE = einzige Quelle** für Anspruch und gebuchten/geplanten Urlaub. Kein „teils Locosoft, teils DRIVE“ in der Logik.

---

## Option A: Mit „leerer“ Planung starten (Reset Buchungen)

**Idee:**  
Alle Urlaubsbuchungen in DRIVE für das relevante Jahr (z. B. 2026) **löschen** – Start mit **0 gebuchten/geplanten Tagen** im System. Rest = Anspruch (aus Mitarbeiterverwaltung).

**Vorteile:**  
- Sofort konsistent: Rest = Anspruch für alle.  
- Keine Mischung aus Alt-Import und Neu-Buchungen.  
- Einfache Regel: „Ab Stichtag gilt nur, was in DRIVE gebucht wird.“

**Nachteile / Aufwand:**  
- Kalender ist leer; bisher angezeigte (importierte) Tage verschwinden.  
- Fachlich: Mitarbeiter haben „real“ schon Urlaub genommen/geplant. Der Anspruch in DRIVE stimmt, aber „verbraucht“ startet bei 0.  
- Entweder: Alle akzeptieren „wir starten mit Rest = Anspruch“ (real verbrauchte Tage werden nicht rückerfasst). Oder: Man trägt die **bereits real verplanten** Tage nach dem Reset manuell in DRIVE nach (einmalig), dann stimmt Rest.

**Wann sinnvoll:**  
Wenn ihr bewusst einen **Stichtag** setzt („ab heute nur noch DRIVE“) und entweder (a) Rest = Anspruch für alle akzeptiert oder (b) die schon verplanten Tage einmalig in DRIVE nachbucht.

---

## Option B: Import bereinigen und vereinheitlichen (kein Total-Löschung)

**Idee:**  
Nicht alles löschen, sondern **nur doppelte/ungereinigte oder falsche Einträge** bereinigen. Was in DRIVE als „Urlaub“ (type_id = 1) zählen soll, bleibt; der Rest (z. B. falscher Typ, Duplikate, Locosoft-Import mit falscher Zuordnung) wird bereinigt oder korrigiert.

**Vorteile:**  
- Kein komplett leerer Kalender.  
- Theoretisch eine saubere Basis, wenn die Datenqualität stimmt.

**Nachteile:**  
- Aufwendig: Man muss pro Mitarbeiter/Jahr prüfen, was „richtig“ ist (DRIVE vs. Locosoft vs. Realität).  
- Risiko: Weiterhin Unstimmigkeiten, wenn Import-Logik und View-Logik nicht 1:1 übereinstimmen.

**Wann sinnvoll:**  
Nur wenn ihr wenige Mitarbeiter habt und die Zeit für eine manuelle Bereinigung (und klare Regeln „was zählt als Urlaub“) habt.

---

## Option C: Stichtag mit „leerer“ Planung + optionale Nachbuchung (Empfehlung)

**Idee (pragmatischer Mix):**

1. **Stichtag festlegen** (z. B. 1. März 2026 oder Start nächster Monat): Ab dann ist **DRIVE die einzige Quelle** für Buchungen und Rest.
2. **Reset Buchungen für das laufende Jahr:**  
   Für das Jahr, in dem ihr startet (z. B. 2026), alle Einträge in `vacation_bookings` für **Urlaub (type_id = 1)** löschen – optional nur für bestimmte Abteilungen/Standorte, wenn ihr schrittweise rollt.  
   Andere Typen (Ausgleichstag, Krankheit, Schulung etc.) könnt ihr beibehalten oder ebenfalls löschen, je nach Entscheidung.
3. **Ergebnis:**  
   Rest = Anspruch (aus Mitarbeiterverwaltung) für alle. Kalender für Urlaub (type_id = 1) ist leer.
4. **Optionale Nachbuchung:**  
   Wo ihr **wisst**, dass schon Urlaub fix verplant ist (z. B. „diese 10 Tage sind genehmigt“), bucht ihr diese **einmalig** in DRIVE nach (genehmigt). Dann stimmt Rest = Anspruch − diese Tage.  
   Wo ihr nicht nachbucht, bleibt Rest = Anspruch bis zur ersten Buchung in DRIVE.

**Vorteile:**  
- Klare Regel: Eine Quelle (DRIVE), keine Locosoft-Logik mehr in der Berechnung.  
- Entweder „sauber leer“ (Rest = Anspruch) oder „gezielt nachgebucht“ (nur wo nötig).  
- Kein dauerhafter Mischbetrieb „Anzeige von woanders, Rest aus DRIVE“.

**Nachteile:**  
- Einmaliger Aufwand: Entscheidung, ob und wo nachgebucht wird; ggf. Lösch-Script und ggf. manuelle Nachbuchung.

---

## Empfehlung (kurz)

- **Nicht** so weiterlaufen lassen (Anzeige voll, Rest falsch) – das blockiert Produktivbetrieb.  
- **Pragmatisch:** **Option C** – Stichtag, Buchungen für das Start-Jahr (nur Urlaub type_id = 1) zurücksetzen, dann entweder Rest = Anspruch für alle oder gezielte Nachbuchung der bereits verplanten Tage.  
- **Kommunikation:** Intern klar sagen: „Ab [Datum] gilt nur, was im Urlaubsplaner DRIVE gebucht und genehmigt ist. Vorherige Planung haben wir [nicht übernommen / nur wo vereinbart nachgebucht].“

---

## Nächste Schritte (ohne Code, nur Planung)

1. **Entscheidung:** Option A (komplett leer), B (Bereinigung) oder C (Stichtag + Reset + optional Nachbuchung).  
2. **Stichtag** und **Jahr** festlegen (z. B. 2026, ab 1.3.).  
3. **Scope:** Nur type_id = 1 (Urlaub) löschen oder alle Typen für das Jahr? Nur bestimmte Abteilungen?  
4. **Nachbuchung:** Ja/Nein; wenn ja, wer trägt die „bereits verplanten“ Tage ein (HR, Abteilungsleiter) und bis wann?  
5. **Erst danach:** Technisch umsetzen (Löschung, ggf. Script; keine Logik-Änderung an der Berechnung nötig, die bleibt wie jetzt).

Wenn ihr euch für eine Option entschieden habt, kann die konkrete technische Umsetzung (z. B. welches SQL, welche Sicherung) separat geplant werden.
