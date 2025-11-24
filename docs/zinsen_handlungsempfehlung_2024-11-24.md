# 💰 ZINSEN-OPTIMIERUNG - HANDLUNGSEMPFEHLUNGEN

**Stand:** 24.11.2025  
**Erstellt für:** Buchhaltung / Plausi-Test  
**Potenzielle Ersparnis:** ~32.000 €/Jahr

---

## 📊 AKTUELLE ZINSKOSTEN (Monat/Jahr)

| Quelle | Monat | Jahr | Datenquelle |
|--------|-------|------|-------------|
| HVB Kontokorrent (Sollzinsen) | 528 € | 6.334 € | MT940 Import |
| Stellantis (7 Fz über Zinsfreiheit) | 1.805 € | 21.666 € | Stellantis ZIP/Excel |
| Santander (42 Fahrzeuge) | 1.894 € | 22.730 € | Santander CSV |
| Hyundai Finance (46 Fahrzeuge) | 2.702 € | 32.418 € | Hyundai CSV |
| **GESAMT** | **6.929 €** | **83.148 €** | |

---

## 🎯 HANDLUNGSEMPFEHLUNG 1: Konten-Umbuchung

**SOFORT UMSETZBAR**

| Von | Nach | Betrag | Ersparnis |
|-----|------|--------|-----------|
| 57908 KK (+193.511 €) | HVB KK (-100.547 €) | **100.547 €** | **528 €/Monat** |

**Buchungsart:** Bank an Bank (gleiche Firma: Autohaus Greiner)  
**Ersparnis/Jahr:** 6.334 €

**Warum?** HVB ist aktuell im Soll (-100.547 €) bei 6,30% Sollzins.  
Das 57908-Konto hat ausreichend Guthaben zum Ausgleich.

---

## 🎯 HANDLUNGSEMPFEHLUNG 2: Fahrzeug-Umfinanzierung

**7 FAHRZEUGE ÜBER ZINSFREIHEIT → SANTANDER**

| VIN | Modell | Saldo | Tage über Zinsfreiheit |
|-----|--------|-------|------------------------|
| SD152236 | C10 Design | 38.160 € | 36 Tage |
| S4194623 | - | 24.051 € | 19 Tage |
| S1042339 | - | 35.860 € | 14 Tage |
| SW061672 | - | 33.973 € | 13 Tage |
| S6043034 | - | 43.366 € | 13 Tage |
| SW063275 | - | 30.113 € | 13 Tage |
| S6044245 | - | 37.739 € | 12 Tage |
| **SUMME** | | **243.262 €** | |

**Zinsdifferenz:** Stellantis 9,03% → Santander ~4,5% = **4,53% Ersparnis**  
**Ersparnis:** 918 €/Monat = **11.020 €/Jahr**

**Santander Limit-Check:**
- Limit gesamt: 1.500.000 €
- Aktuell belegt: 929.271 €
- **Frei verfügbar: 570.729 €** ✅ (reicht für alle 7 Fahrzeuge)

**Ablauf Umfinanzierung:**
1. Ablösung bei Stellantis (Brief anfordern)
2. HVB wird belastet (~4 Tage Übergangszeit)
3. Santander zahlt an Genobank (57908 KK)

---

## 🎯 HANDLUNGSEMPFEHLUNG 3: Bald ablaufende Zinsfreiheit

**15 FAHRZEUGE MIT <14 TAGEN RESTLAUFZEIT**

| Priorität | VIN | Saldo | Tage verbleibend |
|-----------|-----|-------|------------------|
| Kritisch | SD157857 | 38.160 € | 0 Tage |
| Kritisch | SD157687 | 37.408 € | 0 Tage |
| Hoch | S4210342 | 24.051 € | 2 Tage |
| Hoch | S4236294 | 24.051 € | 4 Tage |
| ... | (11 weitere) | ... | 5-14 Tage |
| **SUMME** | | **415.898 €** | |

**Option A:** Umfinanzierung zu Santander (327.467 € noch frei nach Empfehlung 2)  
**Option B:** Verkauf priorisieren

**Potenzielle Zinsen ohne Aktion:** 3.130 €/Monat = 37.556 €/Jahr

---

## 📈 GESAMTERSPARNIS BEI UMSETZUNG

| Maßnahme | Ersparnis/Monat | Ersparnis/Jahr |
|----------|-----------------|----------------|
| 1. HVB ausgleichen | 528 € | 6.334 € |
| 2. 7 Stellantis umfinanzieren | 918 € | 11.020 € |
| 3. 15 bald ablaufend (wenn umfinanziert) | 1.236 € | 14.834 € |
| **GESAMT** | **2.682 €** | **32.188 €** |

---

## 📁 DATENQUELLEN

| Daten | Quelle | Import | Aktualisierung |
|-------|--------|--------|----------------|
| **Kontosalden** | MT940 Dateien (Banken) | `import_mt940.py` | Täglich 7-18 Uhr |
| **Stellantis Bestand** | ZIP von Stellantis Portal | `import_stellantis.py` | Täglich 7-18 Uhr |
| **Santander Bestand** | CSV Export | `import_santander_bestand.py` | Täglich 8:00 Uhr |
| **Hyundai Bestand** | CSV Export | `import_hyundai_finance.py` | Täglich 9:00 Uhr |
| **Zinssätze Konten** | Kontoaufstellung.xlsx (manuell) | Einmalig importiert | Bei Änderung |
| **EK-Finanzierung Limits** | Verträge (manuell) | Einmalig importiert | Bei Änderung |

### Zinssätze (aktuell hinterlegt):

| Institut/Konto | Zinssatz | Limit |
|----------------|----------|-------|
| HVB KK | 6,30% | 200.000 € |
| Sparkasse KK | 7,75% | 100.000 € |
| VR 57908 KK | 6,73% | 500.000 € |
| VR 1501500 HYU KK | 6,73% | 250.000 € |
| VR Landau KK | 11,75% | 0 € |
| Stellantis (über Zinsfreiheit) | 9,03% | 5.380.000 € |
| Santander | 4-5,5% (variabel) | 1.500.000 € |
| Hyundai Finance | 4,68% | 4.300.000 € |

---

## ⚠️ HINWEISE FÜR PLAUSI-TEST

1. **Prüfpunkt Kontosalden:** Stimmen die angezeigten Salden mit Kontoauszügen überein?
2. **Prüfpunkt Fahrzeugbestand:** Stimmt die Anzahl Fahrzeuge pro Institut?
3. **Prüfpunkt Zinsfreiheit:** Sind die "Tage über Zinsfreiheit" plausibel?
4. **Prüfpunkt Zinssätze:** Entsprechen die Zinssätze den aktuellen Konditionen?

**Portal-Link:** https://drive/bankenspiegel/zinsen-analyse

---

*Erstellt: 24.11.2025 | Greiner Portal TAG 80*
