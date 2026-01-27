# TEK E-Mail Report Verbesserungsvorschlag V2 - TAG 204

**Datum:** 2026-01-21  
**Anlass:** Nutzer-Feedback - E-Mail-Struktur gefällt nicht, PDF ist OK

---

## 📋 Aktuelle Probleme

### 1. Bereichs-E-Mail (z.B. "TEK Teile")
- ❌ Zeigt "Status: Ziel erreicht" basierend auf Marge (32.6% vs. Ziel 32%)
- ❌ Zu fokussiert auf einen Bereich, keine Gesamtübersicht
- ❌ "Ziel-Marge" wird angezeigt - Nutzer möchte das entfernen

### 2. Gesamt-E-Mail
- ❌ Zu komplex mit großer Tabelle (10 Spalten)
- ❌ Schwer auf mobilen Geräten lesbar
- ❌ Zu viele Details auf einmal

---

## 🔍 Recherche: Best Practices für tägliche Erlös- und Erfolgsberichte

### Typische Struktur erfolgreicher Daily Reports:

1. **Executive Summary** (Top-Level KPIs)
   - Gesamt-Erlös (heute + Monat kumuliert)
   - Gesamt-DB1 (heute + Monat kumuliert)
   - Trend-Indikatoren (↑/↓ vs. Vortag/Vormonat)

2. **Abteilungsübersicht** (kompakt, visuell)
   - Karten/Boxen statt großer Tabellen
   - Farbcodierung (Grün/Gelb/Rot) für schnelle Orientierung
   - Nur die wichtigsten KPIs pro Abteilung

3. **Drill-Down** (optional, im PDF)
   - Detaillierte Tabellen
   - Absatzwege, Modelle, etc.

### Beispiele aus der Praxis:

**Struktur 1: KPI-Cards (moderne Dashboards)**
```
┌─────────────┬─────────────┬─────────────┐
│ Heute Erlös │ Monat Erlös │ DB1 Monat   │
│ 45.000 €    │ 850.000 €   │ 125.000 €   │
│ ↑ +12%      │ ↑ +8%       │ ↑ +15%      │
└─────────────┴─────────────┴─────────────┘

┌─────────────────────────────────────────┐
│ Abteilungen (heute)                     │
├─────────────────────────────────────────┤
│ 🚗 Neuwagen     12.500 €  [🟢 +5%]     │
│ 🚙 Gebrauchtw.   8.200 €  [🟡 -2%]     │
│ 🔧 Service      15.300 €  [🟢 +10%]    │
│ 📦 Teile         9.000 €  [🟢 +3%]     │
└─────────────────────────────────────────┘
```

**Struktur 2: Kompakte Tabelle (2-Zeilen-Header)**
```
┌──────────┬──────────┬──────────┬──────────┐
│          │  HEUTE   │  MONAT   │          │
│ Abteilung│ Erlös DB1│ Erlös DB1│ Trend    │
├──────────┼──────────┼──────────┼──────────┤
│ Neuwagen │ 12.5k 2k│ 250k 45k│ ↑ +5%    │
│ Gebrauch.│  8.2k 1k│ 180k 30k│ ↓ -2%    │
│ Service  │ 15.3k 3k│ 320k 65k│ ↑ +10%   │
│ Teile    │  9.0k 2k│ 200k 55k│ ↑ +3%    │
└──────────┴──────────┴──────────┴──────────┘
```

**Struktur 3: Hierarchisch (Gesamt → Abteilungen)**
```
📊 GESAMT
   Erlös heute: 45.000 € | Monat: 850.000 €
   DB1 heute: 8.000 € | Monat: 125.000 €
   Marge: 14,7%

📋 ABTEILUNGEN
   Neuwagen:     12.500 € / 2.000 € (heute) | 250.000 € / 45.000 € (Monat)
   Gebrauchtw.:   8.200 € / 1.000 € (heute) | 180.000 € / 30.000 € (Monat)
   Service:      15.300 € / 3.000 € (heute) | 320.000 € / 65.000 € (Monat)
   Teile:         9.000 € / 2.000 € (heute) | 200.000 € / 55.000 € (Monat)
```

---

## 🎯 Verbesserungsvorschlag für TEK E-Mails

### Option A: KPI-Cards Design (empfohlen)

**Vorteile:**
- ✅ Sehr übersichtlich, mobile-friendly
- ✅ Schnelle Orientierung durch Farben
- ✅ Moderne Optik

**Struktur:**
1. **Header:** TEK - Tägliche Erfolgskontrolle | Datum
2. **Gesamt-KPIs (4 Cards):**
   - Heute Erlöse
   - Heute DB1
   - Monat Erlöse (kumuliert)
   - Monat DB1 (kumuliert)
3. **Abteilungen (kompakt):**
   - Pro Abteilung: Name, Heute (Erlöse/DB1), Monat (Erlöse/DB1), Trend-Icon
   - Farbcodierung: Grün (gut), Gelb (ok), Rot (kritisch)
4. **Footer:** Link zu DRIVE, PDF-Hinweis

### Option B: Kompakte 2-Level-Tabelle

**Vorteile:**
- ✅ Alle Daten auf einen Blick
- ✅ Kompakter als aktuelle Version
- ✅ Gut lesbar

**Struktur:**
1. **Header:** TEK - Tägliche Erfolgskontrolle | Datum
2. **Gesamt-Zeile:** GESAMT | Heute (Erlöse/DB1) | Monat (Erlöse/DB1) | Marge
3. **Abteilungen-Tabelle:**
   - KST | Abteilung | Stück | Heute (Erlöse | DB1) | Monat (Erlöse | DB1 | DB1/Stk)
   - Max. 7 Spalten statt 10
4. **Footer:** Link zu DRIVE, PDF-Hinweis

### Option C: Hierarchisch-Textuell

**Vorteile:**
- ✅ Sehr einfach zu lesen
- ✅ Funktioniert in jedem E-Mail-Client
- ✅ Keine Tabellen-Probleme

**Struktur:**
1. **Header:** TEK - Tägliche Erfolgskontrolle | Datum
2. **Gesamt-Block:**
   ```
   📊 GESAMT
   Erlös heute: 45.000 € | Monat kumuliert: 850.000 €
   DB1 heute: 8.000 € | Monat kumuliert: 125.000 €
   Marge: 14,7% | Prognose: 380.000 €
   ```
3. **Abteilungen (pro Abteilung ein Block):**
   ```
   🚗 Neuwagen (KST 1)
   Heute: 12.500 € Erlöse | 2.000 € DB1
   Monat: 250.000 € Erlöse | 45.000 € DB1 | 3.750 €/Stk
   Stück: 12 (Monat)
   ```
4. **Footer:** Link zu DRIVE, PDF-Hinweis

---

## ✅ Sofort-Maßnahmen (wie gewünscht)

1. **"Ziel erreicht" / Status entfernen** aus Bereichs-E-Mails
   - Entferne Spalte "Status" aus `build_bereich_email_html()`
   - Entferne "Ziel-Marge" Zeile
   - Zeige nur: DB1, Marge, Umsatz, Einsatz

2. **Gesamt-E-Mail vereinfachen**
   - Reduziere Spaltenanzahl (von 10 auf 7-8)
   - Entferne "Ziel/Erfüllung" Spalten (vorerst)
   - Bessere mobile Darstellung

---

## 🎨 Empfehlung

**Für Gesamt-E-Mail:** Option B (Kompakte 2-Level-Tabelle)
- Alle wichtigen Daten sichtbar
- Nicht zu komplex
- Gut lesbar

**Für Bereichs-E-Mail:** Option C (Hierarchisch-Textuell)
- Einfach und klar
- Fokus auf den einen Bereich
- Keine unnötigen Status-Anzeigen

---

## 📝 Nächste Schritte

1. ✅ "Ziel erreicht" / Status aus Bereichs-E-Mails entfernen
2. ✅ Gesamt-E-Mail vereinfachen (Option B)
3. ✅ Bereichs-E-Mail vereinfachen (Option C)
4. ⏳ Testen und Feedback einholen
