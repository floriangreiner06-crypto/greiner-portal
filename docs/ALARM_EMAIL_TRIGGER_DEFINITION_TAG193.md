# Alarm-E-Mail Trigger - Definition (TAG 193)

**Datum:** 2026-01-16  
**Version:** Nach TAG 193 Fixes

---

## 📧 WANN WIRD EINE ALARM-E-MAIL GESENDET?

Eine Alarm-E-Mail wird gesendet, wenn **ALLE** folgenden Bedingungen erfüllt sind:

### ✅ Bedingung 1: Arbeitszeit
- **Wochentag:** Montag bis Freitag
- **Uhrzeit:** Zwischen 07:00 und 18:00 Uhr
- **Außerhalb dieser Zeiten:** Keine E-Mails

### ✅ Bedingung 2: Auftrag ist überschritten

#### Für AKTIVE Aufträge (Mechaniker arbeitet gerade):
1. **Aktuelle Stempelung ≥ 30 Minuten**
   - Der Mechaniker muss mindestens 30 Minuten am Auftrag arbeiten
   - Verhindert E-Mails bei sehr kurzen Stempelungen

2. **Aktuelle Stempelung > Vorgabe**
   - Nur die **aktuelle Stempelung heute** wird gezählt
   - **NICHT** die Gesamtlaufzeit des Auftrags
   - Formel: `heute_session_min > vorgabe_min`

3. **Überschreitung > 100%**
   - Die aktuelle Stempelung muss mehr als 100% der Vorgabe betragen
   - Beispiel: Vorgabe 60 Min, aktuelle Stempelung 65 Min → **KEINE** E-Mail (108%)
   - Beispiel: Vorgabe 60 Min, aktuelle Stempelung 70 Min → **E-Mail** (117%)

#### Für ABGESCHLOSSENE Aufträge (kein Mechaniker arbeitet mehr):
1. **Gesamtlaufzeit > Vorgabe**
   - Die **gesamte Laufzeit** des Auftrags wird gezählt
   - Summe aller Stempelungen von heute
   - Formel: `laufzeit_min > vorgabe_min`

2. **Überschreitung > 100%**
   - Die Gesamtlaufzeit muss mehr als 100% der Vorgabe betragen

### ✅ Bedingung 3: Auftrag hat noch offene Positionen
- Der Auftrag muss noch **nicht vollständig fakturiert** sein
- Abgeschlossene/fakturierte Aufträge bekommen **KEINE** E-Mail

### ✅ Bedingung 4: Keine E-Mail heute bereits gesendet
- Pro Auftrag und Empfänger wird **maximal 1 E-Mail pro Tag** gesendet
- Verhindert Spam bei dauerhaft überschrittenen Aufträgen

---

## 📊 BEISPIEL-SZENARIEN

### ✅ Beispiel 1: E-Mail wird GESENDET

**Auftrag 12345:**
- Vorgabe: 60 Minuten (10 AW)
- Mechaniker stempelt sich an (10:00 Uhr)
- Um 10:35 Uhr (35 Min später):
  - Aktuelle Stempelung: **35 Min** ✅ (≥ 30 Min)
  - Überschreitung: 35 / 60 = **58%** ❌ (< 100%)
  - **KEINE E-Mail** (noch nicht überschritten)

- Um 10:40 Uhr (40 Min später):
  - Aktuelle Stempelung: **40 Min** ✅ (≥ 30 Min)
  - Überschreitung: 40 / 60 = **67%** ❌ (< 100%)
  - **KEINE E-Mail** (noch nicht überschritten)

- Um 11:05 Uhr (65 Min später):
  - Aktuelle Stempelung: **65 Min** ✅ (≥ 30 Min)
  - Überschreitung: 65 / 60 = **108%** ✅ (> 100%)
  - **E-Mail wird GESENDET** ✅

### ❌ Beispiel 2: KEINE E-Mail (zu kurz gestempelt)

**Auftrag 12345:**
- Vorgabe: 60 Minuten (10 AW)
- Mechaniker stempelt sich an (10:00 Uhr)
- Um 10:10 Uhr (10 Min später):
  - Aktuelle Stempelung: **10 Min** ❌ (< 30 Min Schwelle)
  - **KEINE E-Mail** (zu kurz gestempelt, auch wenn theoretisch überschritten)

### ❌ Beispiel 3: KEINE E-Mail (Auftrag bereits gestern überschritten)

**Auftrag 12345:**
- Vorgabe: 60 Minuten (10 AW)
- Gestern bereits 100 Min gestempelt (von anderen Mechanikern)
- Heute stempelt neuer Mechaniker sich an (10:00 Uhr)
- Um 10:05 Uhr (5 Min später):
  - Aktuelle Stempelung heute: **5 Min** ❌ (< 30 Min)
  - **KEINE E-Mail** (nur aktuelle Stempelung zählt, nicht gestern)

### ✅ Beispiel 4: E-Mail für abgeschlossenen Auftrag

**Auftrag 12345:**
- Vorgabe: 60 Minuten (10 AW)
- Auftrag wurde heute abgeschlossen (kein Mechaniker arbeitet mehr)
- Gesamtlaufzeit heute: **90 Min**
- Überschreitung: 90 / 60 = **150%** ✅ (> 100%)
- **E-Mail wird GESENDET** ✅

---

## 🔍 TECHNISCHE DETAILS

### Berechnung für aktive Aufträge:
```python
# Nur aktuelle Stempelung heute
laufzeit_min = heute_session_min  # z.B. 35 Min

# Mindestlaufzeit-Schwelle
if laufzeit_min < 30:
    return  # KEINE E-Mail

# Überschreitung berechnen
diff_prozent = (laufzeit_min / vorgabe_min * 100)  # z.B. 35/60 = 58%

# Nur wenn > 100%
if diff_prozent <= 100:
    return  # KEINE E-Mail

# E-Mail senden
send_email()
```

### Berechnung für abgeschlossene Aufträge:
```python
# Gesamtlaufzeit heute (alle Stempelungen)
laufzeit_min = sum(alle_stempelungen_heute)  # z.B. 90 Min

# Überschreitung berechnen
diff_prozent = (laufzeit_min / vorgabe_min * 100)  # z.B. 90/60 = 150%

# Nur wenn > 100%
if diff_prozent <= 100:
    return  # KEINE E-Mail

# E-Mail senden
send_email()
```

---

## 📋 ZUSAMMENFASSUNG

**E-Mail wird gesendet, wenn:**
1. ✅ Arbeitszeit (Mo-Fr, 7-18 Uhr)
2. ✅ Auftrag überschreitet Vorgabe (> 100%)
3. ✅ Für aktive Aufträge: Mindestens 30 Min aktuell gestempelt
4. ✅ Auftrag hat noch offene Positionen
5. ✅ Keine E-Mail heute bereits gesendet

**E-Mail wird NICHT gesendet, wenn:**
- ❌ Außerhalb Arbeitszeit
- ❌ Aktuelle Stempelung < 30 Min (aktive Aufträge)
- ❌ Überschreitung ≤ 100%
- ❌ Auftrag bereits vollständig fakturiert
- ❌ E-Mail heute bereits gesendet

---

## 🎯 WICHTIGE ÄNDERUNGEN (TAG 193)

### Vorher (Bug):
- E-Mail wurde gesendet, wenn Gesamtlaufzeit (alle Tage) > Vorgabe
- Problem: Mechaniker stempelt an → sofort E-Mail (weil gestern bereits überschritten)

### Nachher (Fix):
- E-Mail wird nur gesendet, wenn **aktuelle Stempelung heute** > Vorgabe
- Mindestlaufzeit-Schwelle: 30 Minuten
- Verhindert falsche Alarme bei kurz angestempelten Mechanikern

---

**Status:** ✅ Implementiert und aktiv
