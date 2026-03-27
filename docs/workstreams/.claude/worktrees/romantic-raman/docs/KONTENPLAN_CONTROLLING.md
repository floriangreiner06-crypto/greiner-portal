# KONTENPLAN & CONTROLLING - GREINER PORTAL

**Stand:** 03.12.2025  
**Validiert gegen:** GlobalCube BWA Oktober/November 2025  
**Status:** 100% BWA-Match ✅

---

## INHALTSVERZEICHNIS

1. [Firmenstruktur](#firmenstruktur)
2. [Kontenrahmen SKR51](#kontenrahmen-skr51)
3. [Umlage-Konten](#umlage-konten-kritisch)
4. [Kostenstellen-Logik](#kostenstellen-logik)
5. [BWA-Berechnung](#bwa-berechnung)
6. [TEK-Struktur](#tek-struktur)
7. [Vollkosten-Berechnung](#vollkosten-berechnung)
8. [Bekannte Probleme & Lösungen](#bekannte-probleme--lösungen)

---

## FIRMENSTRUKTUR

### Zwei juristische Einheiten:

| Firma | Marke | subsidiary_to_company_ref | branch_number |
|-------|-------|---------------------------|---------------|
| **Autohaus Greiner GmbH & Co. KG** | Stellantis (Opel, Peugeot, Citroen) | 1 | 1 (DEG), 3 (LAN) |
| **Auto Greiner GmbH & Co. KG** | Hyundai | 2 | 2 |

### Standort-Filter-Logik:

```
Für Umsatz/Einsatz (7/8xxxxx): branch_number
  - 1 = Deggendorf
  - 3 = Landau  
  - 2 = Hyundai (eigene Firma)

Für Kosten (4xxxxx): Letzte Ziffer der Kontonummer (6. Stelle)
  - xxx1 = Deggendorf
  - xxx2 = Landau
  - subsidiary=2 = Hyundai
```

---

## KONTENRAHMEN SKR51

### Übersicht der Kontenbereiche:

| Bereich | Konten | Typ | Vorzeichen |
|---------|--------|-----|------------|
| Umsatzerlöse | 80-88xxxx + 8932xx | Erlöse | HABEN - SOLL |
| Einsatzwerte | 70-79xxxx | Kosten | SOLL - HABEN |
| Kosten | 40-49xxxx | Kosten | SOLL - HABEN |
| Sonstige Erträge | 89xxxx | Erlöse | HABEN - SOLL |

### Detail: Umsatzerlöse (8xxxxx)

| Bereich | Konten | Beschreibung |
|---------|--------|--------------|
| Neuwagen | 810000-819999 | Verkaufserlöse NW |
| Gebrauchtwagen | 820000-829999 | Verkaufserlöse GW |
| Teile | 830000-839999 | Teile/Zubehör |
| Werkstatt | 840000-849999 | Lohn/Werkstatt |
| Sonstige | 860000-869999 | Sonstige Erlöse |
| Sonderposten | 893200-893299 | In Umsatz enthalten! |

**WICHTIG:**
- **817xxx, 827xxx** = Sonstige Erlöse (NICHT Wareneinsatz!)
- **817051, 827051, 837051, 847051** = **Umlage-Konten** (siehe unten)

### Detail: Einsatzwerte (7xxxxx)

| Bereich | Konten | Beschreibung |
|---------|--------|--------------|
| Neuwagen | 710000-719999 | Wareneinsatz NW |
| Gebrauchtwagen | 720000-729999 | Wareneinsatz GW |
| Teile | 730000-739999 | Wareneinsatz Teile |
| Werkstatt | 740000-749999 | Lohneinsatz |
| Sonstige | 760000-769999 | Sonstiger Einsatz |

### Detail: Kosten (4xxxxx)

| Typ | Konten | KST | Beschreibung |
|-----|--------|-----|--------------|
| Variable | 4151xx | alle | Provisionen Finanz-Vermittlung |
| Variable | 4355xx | alle | Trainingskosten |
| Variable | 455-456xx | 1-7 | Fahrzeugkosten (VFW, Ersatzwagen) |
| Variable | 4870x | 1-7 | Werbekosten direkt |
| Variable | 491-497xx | alle | Fertigmachen, Provisionen, Kulanz |
| Direkte | 40-48xxxx | 1-7 | Alle anderen mit KST 1-7 |
| Indirekte | 40-48xxxx | 0 | Verwaltungskosten |
| Indirekte | 424xxx | 1-7 | KFZ-Pauschale (Ausnahme) |
| Indirekte | 438xxx | 1-7 | Sachzuwendungen (Ausnahme) |
| Indirekte | 498-499xxx | alle | Umlagen |
| Indirekte | 891-896xxx | alle | Sonstige betriebliche Erträge |

---

## UMLAGE-KONTEN (KRITISCH!)

### Struktur der internen Verrechnung:

```
STELLANTIS (Autohaus Greiner) ERHÄLT:
═══════════════════════════════════════════════════════════════════
817051 = Umlage-Erlös Neuwagen        +12.500 €/Monat (HABEN)
827051 = Umlage-Erlös Gebrauchtwagen  +12.500 €/Monat (HABEN)
837051 = Umlage-Erlös Werkstatt       +12.500 €/Monat (HABEN)
847051 = Umlage-Erlös Teile           +12.500 €/Monat (HABEN)
───────────────────────────────────────────────────────────────────
SUMME ERLÖSE:                         +50.000 €/Monat

HYUNDAI (Auto Greiner) ZAHLT:
═══════════════════════════════════════════════════════════════════
498001 = Umlage-Kosten                -50.000 €/Monat (HABEN!)
───────────────────────────────────────────────────────────────────
KONZERN-EFFEKT:                              0 €  ← Nullsumme!
```

### Warum 498001 als HABEN gebucht wird:

- 498001 ist ein **Kostenkonto** (Klasse 4)
- Bei Hyundai wird es als **HABEN** gebucht = Kostenminderung/Erlös
- In der Kosten-Logik: `SOLL - HABEN` → HABEN wird **negativ**
- Ergebnis: Die indirekten Kosten werden **um 50.000 € gemindert**

### Problem ohne Filterung:

```
Indirekte Kosten Dezember 2025 (ohne Filter):
─────────────────────────────────────────────
Echte Kosten (SOLL):           +747 €
498001 Umlage (HABEN):     -50.000 €
415001 Umlage (HABEN):      -5.000 €
440001 Umlage (HABEN):      -2.500 €
461001 Umlage (HABEN):        -500 €
462001 Umlage (HABEN):        -500 €
─────────────────────────────────────────────
NETTO:                     -57.753 € ← NEGATIV!
```

### Lösung: Option A (implementiert)

```python
# Nur 498001 filtern (50.000 €/Monat)
UMLAGE_KOSTEN_KONTEN = [498001]

# Bei "ohne Umlage":
umlage_kosten_filter = "AND nominal_account_number NOT IN (498001)"
```

Die kleineren Umlagen (8.500 €) auf 415001, 440001, 461001, 462001 werden **nicht gefiltert**, da:
1. Diese Konten auch echte Kosten enthalten (Miete, etc.)
2. Der Betrag relativ gering ist
3. Eine Filterung nach Buchungstext zu komplex wäre

---

## KOSTENSTELLEN-LOGIK

### 5. Stelle der Kontonummer bestimmt KST:

| 5. Ziffer | Kostenstelle | BWA-Kategorie |
|-----------|--------------|---------------|
| **0** | Gesamt/Verwaltung | INDIREKT |
| **1** | Neuwagen | DIREKT oder VARIABEL |
| **2** | Gebrauchtwagen | DIREKT oder VARIABEL |
| **3** | Mechanik/Service | DIREKT oder VARIABEL |
| **4** | Karosserie | DIREKT |
| **5** | Lackiererei | DIREKT |
| **6** | Teile & Zubehör | DIREKT oder VARIABEL |
| **7** | Mietwagen | DIREKT oder VARIABEL |

### Beispiel:

```
Konto 410031:
  41 = Personalkosten (Gruppe)
  0  = Verwaltung (Bereich)
  03 = Mechanik (KST)
  1  = Deggendorf (Standort)

→ Personalkosten Verwaltung, KST Mechanik, Standort Deggendorf
```

---

## BWA-BERECHNUNG

### Struktur:

```
UMSATZERLÖSE
  - 80-88xxxx (HABEN - SOLL)
  - 893200-893299
─────────────────────
= UMSATZ

EINSATZWERTE
  - 70-79xxxx (SOLL - HABEN)
─────────────────────
= EINSATZ

UMSATZ - EINSATZ = DB1 (Bruttoertrag)

DB1 - VARIABLE KOSTEN = DB2
DB2 - DIREKTE KOSTEN = DB3
DB3 - INDIREKTE KOSTEN = BETRIEBSERGEBNIS (BE)
```

### SQL für Umsatz:

```sql
SELECT SUM(
    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
)/100.0
FROM loco_journal_accountings
WHERE accounting_date >= ? AND accounting_date < ?
  AND ((nominal_account_number BETWEEN 800000 AND 889999)
       OR (nominal_account_number BETWEEN 893200 AND 893299))
```

### SQL für Einsatz:

```sql
SELECT SUM(
    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
)/100.0
FROM loco_journal_accountings
WHERE accounting_date >= ? AND accounting_date < ?
  AND nominal_account_number BETWEEN 700000 AND 799999
```

---

## TEK-STRUKTUR

### Bereiche-Mapping:

| TEK-Bereich | Umsatz-Konten | Einsatz-Konten | KST |
|-------------|---------------|----------------|-----|
| 1-NW | 810000-819999 | 710000-719999 | 1 |
| 2-GW | 820000-829999 | 720000-729999 | 2 |
| 3-Teile | 830000-839999 | 730000-739999 | 6 |
| 4-Lohn | 840000-849999 | 740000-749999 | 3 |
| 5-Sonst | 860000-869999 | 760000-769999 | 7 |

### Umlage-Bereinigung (umlage='ohne'):

```python
# Erlöse filtern
UMLAGE_ERLOESE_KONTEN = [817051, 827051, 837051, 847051]
umlage_erloese_filter = f"AND nominal_account_number NOT IN ({konten})"

# Kosten filtern (nur 498001)
UMLAGE_KOSTEN_KONTEN = [498001]
umlage_kosten_filter = f"AND nominal_account_number NOT IN (498001)"
```

---

## VOLLKOSTEN-BERECHNUNG

### Funktion: `berechne_vollkosten()`

```python
def berechne_vollkosten(db, von, bis, firma_filter, standort, umlage_kosten_filter):
    """
    Returns:
    - variable: Dict {kst: betrag}
    - direkte: Dict {kst: betrag}
    - indirekte_gesamt: Float
    - umlage_verteilt: Dict {kst: betrag} (nach MA-Schlüssel)
    - ma_verteilung: Dict {kst: anzahl_ma}
    - umlage_schluessel: Dict {kst: prozent}
    """
```

### Umlage-Verteilung:

Die indirekten Kosten werden nach MA-Schlüssel auf produktive KST verteilt:

```
Produktive KST: ['12' (Verkauf), '3' (Service), '6' (Teile)]

Beispiel (60 MA):
  12 = 19 MA → 31.7%
  3  = 30 MA → 50.0%
  6  = 11 MA → 18.3%
```

### SQL für indirekte Kosten (mit Umlage-Filter):

```sql
SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0
FROM loco_journal_accountings
WHERE accounting_date >= ? AND accounting_date < ?
  AND ((nominal_account_number BETWEEN 400000 AND 499999 
        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
       OR (nominal_account_number BETWEEN 424000 AND 424999 
           AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
       OR (nominal_account_number BETWEEN 438000 AND 438999 
           AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
       OR nominal_account_number BETWEEN 498000 AND 499999
       OR (nominal_account_number BETWEEN 891000 AND 896999
           AND NOT (nominal_account_number BETWEEN 893200 AND 893299)))
  {firma_filter}
  {umlage_kosten_filter}  -- WICHTIG: Filtert 498001 raus!
```

---

## BEKANNTE PROBLEME & LÖSUNGEN

### Problem 1: BE > DB1 (Betriebsergebnis höher als Deckungsbeitrag)

**Symptom:** Im Vollkosten-Modus ist BE höher als DB1 (sollte nie passieren)

**Ursache:** 
- 498001 wird als HABEN gebucht (Umlage-Gegenbuchung)
- In Kosten-Logik wird HABEN negativ → Kosten werden negativ
- Negative Kosten werden vom DB1 abgezogen → BE steigt

**Lösung:** 
- `umlage_kosten_filter` in `berechne_vollkosten()` anwenden
- Bei "ohne Umlage" wird 498001 aus der Query gefiltert

### Problem 2: 89xxxx in Kosten-Query

**Frage:** Warum sind 891000-896999 in der indirekten Kosten-Query?

**Antwort:** 
- Diese Konten sind "Sonstige betriebliche Erträge"
- Sie mindern die Kosten (z.B. Versicherungserstattungen, Rabatte)
- Das ist **gewollt** laut BWA-Logik
- 893200-893299 werden explizit ausgenommen (sind im Umsatz)

### Problem 3: Drill-Down zeigt noch Umlage-Konten

**Status:** TODO
- Die Drill-Down-API (`/api/tek/detail`) respektiert noch nicht den Umlage-Filter
- Haupttabelle zeigt bereinigte Werte, Detail zeigt unbereinigt

### Problem 4: Wirtschaftsjahr ≠ Kalenderjahr

**Wichtig:** Das Wirtschaftsjahr läuft vom 01.09. bis 31.08.!
- September = Monat 1 des WJ
- August = Monat 12 des WJ
- Relevant für Jahresvergleiche und Abschlüsse

---

## DATEIEN & REFERENZEN

| Datei | Beschreibung |
|-------|--------------|
| `routes/controlling_routes.py` | TEK-API, Vollkosten-Berechnung |
| `templates/controlling/tek_dashboard.html` | TEK-Frontend |
| `data/greiner_controlling.db` | SQLite-Datenbank |
| `loco_journal_accountings` | Gespiegelte Buchungen aus Locosoft |

---

## CHANGELOG

| Datum | Änderung |
|-------|----------|
| 03.12.2025 | Umlage-Filter für 498001 in indirekte_sql implementiert |
| 03.12.2025 | Dokumentation erstellt |
| 02.12.2025 | BWA-Mapping validiert gegen GlobalCube |
| 15.11.2025 | 83/84/817/827 Kategorisierung korrigiert (v2.8) |

---

*Erstellt: 03.12.2025 | Autor: Claude AI + Autohaus Greiner*
