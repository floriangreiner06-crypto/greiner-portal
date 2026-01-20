# Testanleitung: Fahrzeugfinanzierungen Dashboard

**Zielgruppe:** Verkaufsleitung & Buchhaltung  
**Datum:** 2026-01-20  
**Version:** 1.0  
**Feature:** Fahrzeugfinanzierungen & Zinsen-Analyse

---

## 📋 Inhaltsverzeichnis

1. [Feature-Übersicht](#feature-übersicht)
2. [Zugriff & Navigation](#zugriff--navigation)
3. [Datenquellen & Erläuterung](#datenquellen--erläuterung)
4. [Testanleitung für Verkaufsleitung](#testanleitung-für-verkaufsleitung)
5. [Testanleitung für Buchhaltung](#testanleitung-für-buchhaltung)
6. [Häufige Fragen (FAQ)](#häufige-fragen-faq)

---

## 🎯 Feature-Übersicht

Das **Fahrzeugfinanzierungen Dashboard** bietet eine konsolidierte Übersicht über alle Fahrzeugfinanzierungen der Autohaus-Gruppe. Es kombiniert Daten aus verschiedenen Finanzierungsquellen und ermöglicht eine detaillierte Analyse der Zinskosten.

### Hauptfunktionen:

1. **Finanzierungsübersicht**
   - Gesamtanzahl finanzierter Fahrzeuge
   - Gesamtfinanzierungssumme
   - Abbezahlte Beträge (Tilgung)
   - Durchschnittliche Finanzierung pro Fahrzeug

2. **Institut-spezifische Ansichten**
   - **Stellantis Bank**: Neuwagen-Finanzierungen (Opel/Hyundai, Leapmotor)
   - **Santander Bank**: Gebrauchtwagen-Finanzierungen
   - **Hyundai Finance**: Hyundai-spezifische Finanzierungen
   - **Genobank**: Fahrzeuge mit Genobank-Finanzierung (Konto 4700057908)

3. **Marken-Analyse**
   - Aufschlüsselung nach Fahrzeugmarken pro Institut
   - Klickbare Badges für detaillierte Fahrzeuglisten

4. **Zinskosten-Tracking**
   - Fahrzeuge mit laufenden Zinsen
   - Monatliche und jährliche Zinskosten
   - Zinsfreiheits-Warnungen (< 30 Tage übrig)

5. **Detaillierte Fahrzeugansichten**
   - Modal mit Fahrzeugliste nach Marke
   - Einzelfahrzeug-Details aus Locosoft
   - Zinskosten pro Fahrzeug

---

## 🔗 Zugriff & Navigation

### URL:
```
http://10.80.80.20:5000/bankenspiegel/fahrzeugfinanzierungen
```

### Navigation im Portal:
1. Hauptmenü → **Bankenspiegel**
2. Untermenü → **Fahrzeugfinanzierungen**

### Berechtigungen:
- **Verkaufsleitung**: Vollzugriff (alle Institute)
- **Buchhaltung**: Vollzugriff (alle Institute)
- **Controlling**: Vollzugriff (alle Institute)

---

## 📊 Datenquellen & Erläuterung

### 1. **fahrzeugfinanzierungen** (DRIVE Portal DB)

**Tabelle:** `fahrzeugfinanzierungen` (PostgreSQL)

**Hauptfelder:**
- `finanzinstitut`: Stellantis, Santander, Hyundai Finance, Genobank
- `vin`: Fahrgestellnummer (VIN)
- `modell`: Fahrzeugmodell
- `hersteller` / `rrdi`: Marke (hersteller für Genobank, rrdi für andere)
- `aktueller_saldo`: Aktueller Finanzierungssaldo
- `original_betrag`: Ursprünglicher Finanzierungsbetrag
- `alter_tage`: Tage seit Finanzierungsbeginn
- `zinsfreiheit_tage`: Verbleibende zinsfreie Tage
- `zinsen_gesamt`: Bereits angefallene Zinsen
- `zinsen_letzte_periode`: Monatliche Zinskosten
- `zins_startdatum`: Datum ab dem Zinsen anfallen

**Datenquelle:**
- **Stellantis**: Import aus Excel/CSV (Import-Script: `scripts/imports/import_stellantis.py`)
- **Santander**: Import aus Excel/CSV (Import-Script: `scripts/imports/import_santander.py`)
- **Hyundai Finance**: Import aus CSV (Import-Script: `scripts/imports/import_hyundai_finance.py`)
- **Genobank**: Import aus Locosoft (Import-Script: `scripts/imports/import_genobank_finanzierungen.py`)

**Aktualisierung:**
- Manuelle Imports über Scripts
- Zinsen werden automatisch berechnet (bei Stellantis: 9,03% p.a.)

---

### 2. **Locosoft** (Externe PostgreSQL DB)

**Verbindung:** Read-only Zugriff auf Locosoft-Datenbank

**Verwendete Tabellen:**
- `vehicles`: Fahrzeug-Stammdaten (VIN, Modell, EZ, KM-Stand)
- `dealer_vehicles`: Händlerfahrzeuge (Bestand, Kalkulation, Standort)
- `makes`: Marken (Opel, Hyundai, etc.)
- `models`: Modell-Details
- `subsidiaries`: Standorte (Deggendorf, Landau)

**Verwendung:**
- **Fahrzeugdetails**: Wenn VIN im Modal angeklickt wird
- **Modell-Erkennung**: Falls Modell in `fahrzeugfinanzierungen` leer ist
- **Marken-Erkennung**: Falls Marke in `fahrzeugfinanzierungen` leer ist (Genobank)

**Besonderheit:**
- VIN-Suche unterstützt gekürzte VINs (z.B. "T6004025" findet "VXKKAHPY3T6004025")

---

### 3. **konten & salden** (DRIVE Portal DB)

**Tabellen:** `konten`, `salden` (PostgreSQL)

**Verwendung:**
- **Genobank-Konto**: Konto 4700057908 (IBAN mit 4700057908)
- `sollzins`: Zinssatz für Genobank-Finanzierungen (aus MT940)
- `saldo`: Aktueller Kontostand (für Genobank-Badge, falls keine Fahrzeuge)

**Datenquelle:**
- MT940-Import über Bankenspiegel-Feature
- Automatische Aktualisierung bei MT940-Import

---

### 4. **ek_finanzierung_konditionen** (DRIVE Portal DB)

**Tabelle:** `ek_finanzierung_konditionen` (PostgreSQL)

**Verwendung:**
- Fallback-Zinssätze für Genobank (falls nicht in `konten.sollzins` vorhanden)
- Standard: 5,5% p.a.

---

## 🧪 Testanleitung für Verkaufsleitung

### Test 1: Übersichtsdashboard

**Ziel:** Gesamtübersicht über alle Finanzierungen prüfen

**Schritte:**
1. Öffne `/bankenspiegel/fahrzeugfinanzierungen`
2. Prüfe die **Gesamt-KPIs** oben:
   - Anzahl Fahrzeuge
   - Gesamtfinanzierung
   - Abbezahlt (Betrag & Prozent)
3. Prüfe die **Institut-Karten**:
   - Stellantis Bank
   - Santander Bank
   - Hyundai Finance
   - Genobank

**Erwartetes Ergebnis:**
- Alle Institute werden angezeigt
- Zahlen sind plausibel (keine negativen Werte)
- Genobank erscheint auch wenn keine Fahrzeuge vorhanden (zeigt Konto-Saldo)

---

### Test 2: Marken-Analyse

**Ziel:** Markenverteilung pro Institut prüfen

**Schritte:**
1. Öffne ein Institut (z.B. "Stellantis Bank")
2. Prüfe die **Marken-Badges**:
   - Opel/Hyundai: Anzahl Fahrzeuge
   - Leapmotor: Anzahl Fahrzeuge
   - Unbekannt: Sollte möglichst leer sein
3. Klicke auf einen Marken-Badge (z.B. "Opel/Hyundai")

**Erwartetes Ergebnis:**
- Modal öffnet sich mit Fahrzeugliste
- Fahrzeuge sind nach Standzeit sortiert (älteste zuerst)
- Spalten: VIN, Modell, Marke, Saldo, Original, Alter, Zinsen, Abbezahlt

---

### Test 3: Fahrzeugdetails aus Locosoft

**Ziel:** Einzelfahrzeug-Details prüfen

**Schritte:**
1. Öffne ein Marken-Modal (z.B. "Genobank - Opel")
2. Klicke auf eine **VIN** (blau, unterstrichen)
3. Prüfe das **Fahrzeugdetail-Modal**:
   - Fahrzeugdaten: VIN, Typ, Marke/Modell, EZ, KM-Stand, Kennzeichen
   - Bestandsdaten: Eingang, Standzeit, Standort, Lagerort, Kommissionsnummer, Status
   - Finanzierungsdaten: Finanzinstitut, Saldo, Original, Zinsen Gesamt, Zinsen/Monat, Zinsfreiheit

**Erwartetes Ergebnis:**
- Alle Felder sind korrekt befüllt
- Modell wird korrekt erkannt (nicht "Unbekannt")
- Marke wird korrekt erkannt (nicht "Unbekannt")
- Zinskosten werden angezeigt (falls vorhanden)

---

### Test 4: Zinskosten-Tracking

**Ziel:** Fahrzeuge mit laufenden Zinsen prüfen

**Schritte:**
1. Scrolle zum Abschnitt **"Fahrzeuge mit laufenden Zinsen"**
2. Prüfe die **Zinsen-KPIs**:
   - Anzahl Fahrzeuge mit Zinsen
   - Finanzierung unter Zinsen
   - Zinsen Gesamt
   - Zinsen/Monat Ø
3. Prüfe die **Zinsen-Tabelle**:
   - Fahrzeuge mit höchsten Zinskosten zuerst
   - Spalten: Institut, VIN, Modell, Saldo, Zinsen Gesamt, Zinsen/Monat

**Erwartetes Ergebnis:**
- Nur Fahrzeuge mit tatsächlich laufenden Zinsen werden angezeigt
- Zinskosten sind korrekt berechnet
- Monatliche Zinskosten sind plausibel

---

### Test 5: Genobank-spezifische Tests

**Ziel:** Genobank-Finanzierungen prüfen

**Schritte:**
1. Öffne "Genobank Bank" Karte
2. Prüfe:
   - Anzahl Fahrzeuge
   - Marken-Badges (Opel, Leapmotor, etc.)
   - Keine "Unbekannt"-Marken (oder möglichst wenige)
3. Öffne ein Marken-Modal (z.B. "Genobank - Opel")
4. Prüfe:
   - Alle Fahrzeuge haben Modell (nicht "Unbekannt")
   - Alle Fahrzeuge haben Marke (nicht "Unbekannt")
   - Zinskosten werden angezeigt

**Erwartetes Ergebnis:**
- Genobank-Badge erscheint auch wenn keine Fahrzeuge vorhanden (zeigt Konto-Saldo)
- Marken werden korrekt erkannt (aus Locosoft)
- Modelle werden korrekt erkannt (aus Locosoft)
- Zinskosten basieren auf `sollzins` aus Konto 4700057908

---

## 💰 Testanleitung für Buchhaltung

### Test 1: Finanzierungssummen validieren

**Ziel:** Gesamtfinanzierungssummen mit Buchhaltungssystem abgleichen

**Schritte:**
1. Öffne `/bankenspiegel/fahrzeugfinanzierungen`
2. Notiere die **Gesamtfinanzierung** aus den KPIs
3. Vergleiche mit:
   - Stellantis: Finanzierungsübersicht aus Excel/CSV
   - Santander: Finanzierungsübersicht aus Excel/CSV
   - Hyundai Finance: Finanzierungsübersicht aus CSV
   - Genobank: Konto-Saldo 4700057908 (aus Buchhaltungssystem)

**Erwartetes Ergebnis:**
- Summen stimmen überein (Toleranz: ±0,01 €)
- Abweichungen dokumentieren

---

### Test 2: Zinskosten validieren

**Ziel:** Zinskosten mit Buchhaltungssystem abgleichen

**Schritte:**
1. Öffne den Abschnitt **"Zinsen-Analyse"**
2. Notiere:
   - Zinskosten / Monat (Gesamt)
   - Zinskosten / Jahr (Gesamt)
   - Aufschlüsselung nach Institut
3. Vergleiche mit:
   - Buchhaltungssystem: Zinskosten pro Monat
   - Kontoauszüge: Zinsbuchungen

**Erwartetes Ergebnis:**
- Zinskosten sind plausibel
- Monatliche Zinskosten entsprechen den Buchungen
- Genobank-Zinsen sind in "Konten Sollzinsen" enthalten (keine Doppelzählung)

---

### Test 3: Genobank-Konto validieren

**Ziel:** Genobank-Konto 4700057908 prüfen

**Schritte:**
1. Öffne "Genobank Bank" Karte
2. Prüfe:
   - Finanzierungssumme entspricht Konto-Saldo 4700057908
   - Zinssatz (`sollzins`) ist korrekt (aus MT940)
3. Öffne ein Fahrzeugdetail-Modal für Genobank-Fahrzeug
4. Prüfe:
   - Zinskosten werden korrekt berechnet
   - Zinssatz entspricht `sollzins` aus Konto

**Erwartetes Ergebnis:**
- Konto-Saldo stimmt mit Finanzierungssumme überein
- Zinssatz ist aktuell (aus letztem MT940-Import)
- Zinskosten-Berechnung ist korrekt: `Saldo × Zinssatz × Tage / 365`

---

### Test 4: Abbezahlte Beträge validieren

**Ziel:** Tilgungsbeträge prüfen

**Schritte:**
1. Öffne `/bankenspiegel/fahrzeugfinanzierungen`
2. Prüfe die **Gesamt-KPIs**:
   - Abbezahlt (Betrag)
   - Abbezahlt (%)
3. Berechne manuell:
   - `Abbezahlt = Originalbetrag - Aktueller Saldo`
   - `Abbezahlt % = (Abbezahlt / Originalbetrag) × 100`
4. Öffne ein Marken-Modal
5. Prüfe die **Gesamt-Summen** in der Fußzeile:
   - Abbezahlt entspricht Summe der Einzelfahrzeuge

**Erwartetes Ergebnis:**
- Abbezahlte Beträge sind korrekt
- Prozentwerte sind korrekt
- Summen stimmen überein

---

### Test 5: Datenaktualität prüfen

**Ziel:** Prüfen ob Daten aktuell sind

**Schritte:**
1. Öffne `/bankenspiegel/fahrzeugfinanzierungen`
2. Prüfe die **Datenstand-Anzeige** (falls vorhanden)
3. Öffne ein Fahrzeugdetail-Modal
4. Prüfe:
   - Standzeit entspricht aktueller Datum
   - Zinskosten sind aktuell berechnet
5. Vergleiche mit:
   - Letzter Import-Stand (aus Import-Scripts)
   - Letzter MT940-Import (für Genobank)

**Erwartetes Ergebnis:**
- Daten sind aktuell (max. 1-2 Tage alt)
- Zinskosten werden täglich neu berechnet
- Standzeiten werden täglich aktualisiert

---

## ❓ Häufige Fragen (FAQ)

### Q1: Warum werden manche Fahrzeuge als "Unbekannt" angezeigt?

**A:** Die Marke/Modell-Erkennung erfolgt automatisch aus Locosoft. Falls ein Fahrzeug nicht in Locosoft gefunden wird oder die VIN unvollständig ist, wird "Unbekannt" angezeigt. Dies sollte nach dem nächsten Import korrigiert werden.

**Lösung:** VIN im Import-Script prüfen oder manuell in Locosoft nachtragen.

---

### Q2: Warum werden Genobank-Zinsen doppelt gezählt?

**A:** Genobank-Zinsen werden über das Konto 4700057908 erfasst (MT940). Diese sind bereits in "Konten Sollzinsen" enthalten. Im Dashboard werden sie separat angezeigt, aber nicht doppelt gezählt.

**Prüfung:** In der Zinsen-Analyse sollte "Konten Sollzinsen" die Genobank-Zinsen enthalten.

---

### Q3: Wie werden Zinskosten für Genobank berechnet?

**A:** 
- Zinssatz: Aus `konten.sollzins` (Konto 4700057908) - wird über MT940 aktualisiert
- Fallback: 5,5% p.a. (falls `sollzins` nicht vorhanden)
- Berechnung: `Saldo × Zinssatz × Tage seit Zinsstart / 365`
- Monatlich: `Saldo × Zinssatz × 30 / 365`

---

### Q4: Warum erscheint Genobank auch wenn keine Fahrzeuge vorhanden sind?

**A:** Genobank wird angezeigt, wenn das Konto 4700057908 existiert und aktiv ist. In diesem Fall wird der Konto-Saldo als Finanzierungssumme angezeigt.

**Zweck:** Buchhaltung kann den Konto-Saldo auch ohne verknüpfte Fahrzeuge sehen.

---

### Q5: Wie aktualisiere ich die Finanzierungsdaten?

**A:** 
- **Stellantis/Santander/Hyundai Finance**: Import-Scripts ausführen (siehe `scripts/imports/`)
- **Genobank**: Import-Script ausführen (`scripts/imports/import_genobank_finanzierungen.py`)
- **Zinssätze**: Automatisch über MT940-Import (Bankenspiegel)

**Hinweis:** Imports sollten regelmäßig durchgeführt werden (z.B. wöchentlich).

---

### Q6: Was bedeutet "Zinsfreiheit" in den Fahrzeugdetails?

**A:** 
- **Positive Zahl**: Verbleibende zinsfreie Tage
- **0 oder negativ**: Zinsen laufen bereits
- **Leer**: Keine Zinsfreiheit definiert (Zinsen laufen sofort)

**Beispiel:** "30 Tage übrig" = Fahrzeug hat noch 30 zinsfreie Tage, danach fallen Zinsen an.

---

## 📞 Support & Kontakt

Bei Fragen oder Problemen:

1. **Technische Probleme**: IT-Support kontaktieren
2. **Datenprobleme**: Controlling kontaktieren
3. **Berechtigungen**: Systemadministrator kontaktieren

**Dokumentation:**
- Code-Dokumentation: `/opt/greiner-portal/docs/`
- Session-Logs: `/opt/greiner-portal/docs/sessions/`

---

## 📝 Changelog

**Version 1.0 (2026-01-20)**
- Initiale Testanleitung
- Feature: Fahrzeugfinanzierungen Dashboard
- Feature: Zinskosten-Tracking
- Feature: Genobank-Integration
- Feature: Locosoft-Integration für Fahrzeugdetails

---

**Ende der Testanleitung**
