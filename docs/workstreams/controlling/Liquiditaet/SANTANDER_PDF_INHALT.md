# Santander-PDFs im Ordner Liquiditaet – Inhalt

**Stand:** 2026-03  
**Ordner:** `docs/workstreams/controlling/Liquiditaet/` (Sync: F:\Greiner Portal\...\Liquiditaet)

---

## 1. Allgemeinen_Bedingungen_Einkaufsfinanzierung_Mobilitaet.pdf (9 Seiten)

**Typ:** Allgemeine Geschäftsbedingungen (rechtlicher Rahmen)

**Inhalt (Auszug):**
- Santander Consumer Bank AG, Einkaufsfinanzierung (Mobilität)
- Gesamtrahmenkreditlinie, Unterkreditlinien, Verwendungszweck (Fahrzeuge, Ausschlüsse: Taxi/Fahrschule, nicht StVZO-konform, nicht inländisch)
- Einzelkreditverträge, Gesamtkredit, Kreditantrag über Anwendungssoftware
- Netting (Verrechnung bei Absatzfinanzierung)
- Sicherheiten: Sicherungsübereignung, Sicherungsabtretung (Miet-/Leasingforderungen, Kaufpreisforderungen)
- Keine konkreten Zahlen (keine Zinsfreiheit in Tagen, kein Zinssatz) – reine Rahmenbedingungen

**Für Modalitäten-DB:** Optional als Dokument erfassen; strukturierte **Zahlen** stehen in der Kreditrahmenvereinbarung.

---

## 2. Gebuehren_Leistungsverzeichnis_Haendlerfinanzierung.pdf

**Typ:** Gebühren- und Leistungsverzeichnis  
**Gültig ab:** 01.09.2025

**Inhalt (Auszug):**
- P@rtnerKonto-Firmenkonten: Kontoführung, SEPA (Überweisung/Lastschrift pro Transaktion 0,12 €), Auslandszahlung (SHARE 30 €, OUR 50 €), Kontoauszug 0,85 €, Onboarding 200 €
- Guthabenverzinsung 0,00 % p.a.; Sollzinssatz Überziehung laut Kreditvereinbarung
- Weitere Positionen (Daueraufträge, Schecks etc.)

**Für Modalitäten-DB:** Dokument anlegen; ggf. Einzelpositionen als Regeln (z. B. „SEPA Transaktion“ = 0,12 €), wenn für Liquiditätsplanung relevant.

---

## 3. Kreditrahmenvereinbarung_P@rtnerPlus_bestätigt.pdf (4 Seiten)

**Typ:** Konkrete Kreditrahmenvereinbarung (Vertrag)  
**Vertragsnummer:** EKF-2025-001747  
**Parteien:** Santander Consumer Bank AG / Auto Greiner GmbH & Co. KG + Autohaus Greiner GmbH & Co. KG (beide Deggendorf)

### 3.1 Kreditrahmen
- **Gesamt:** EUR 1.500.000 (P@rtnerPlus)
- **Mobilitätsfahrzeuge:** max. EUR 500.000
- Verwendung: Neufahrzeuge, Gebrauchtfahrzeuge, Mobilitätsfahrzeuge (max. 7 Jahre ab Erstzulassung; Rechnung/Ankaufschein max. 360 Tage alt)

### 3.2 Beleihung
- Basis: Händler-Einkaufs-Rechnungsbetrag netto (100 %)
- Gebrauchtfahrzeuge > 18 Monate: max. Eurotax-Schwacke HEP netto (differenzbesteuert: Bruttowert)
- Finanzierungsbetrag: min. 2.000 € (PKW) / 1.000 € (Motorräder), max. 120.000 €
- Lagerdauer > 360 Tage: Beleihung reduziert sich um 25 Prozentpunkte

### 3.3 Tilgung (Abschlagszahlung)
- **Neu- & Gebrauchtfahrzeuge:**  
  - 60. Tag: 10 %  
  - 120. Tag: 10 %  
  - 180. Tag: 10 %  
  - 360. Tag: Restsaldo  
  - Laufzeitverlängerung möglich: +10 % nach 360 Tagen, +10 % nach 540 Tagen, max. 720 Tage
- **Mobilitätsfahrzeuge:**  
  - monatlich 1,5 %  
  - 720. Tag: Restsaldo  
  - danach weiter monatlich 1,5 %

### 3.4 Zinskonditionen (Zinsaufschlag auf 6-Monats-Euribor; Mindestreferenz 0 Basispunkte)
- **Neu- & Gebrauchtfahrzeuge:**  
  - 1.–90. Tag: 2,00 %  
  - 91.–180. Tag: 3,50 %  
  - 181.–360. Tag: 4,00 %  
  - ab 361. Tag: 9,90 %
- **Mobilitätsfahrzeuge:**  
  - 1. Tag bis Laufzeitende: 3,50 %

### 3.5 Sonstiges
- Gebühren: aktuelles Gebühren- und Leistungsverzeichnis Händlerfinanzierung
- Bedingungswerke: AGB, Allgemeine Bedingungen Einkaufsfinanzierung (Mobilität), Gebühren- & Leistungsverzeichnis

---

## Nutzung für Modalitäten-DB

Die **Kreditrahmenvereinbarung** enthält die für Liquiditätsplanung und EK-Übersicht relevanten **Zahlen** (Tilgungstermine, Zinsaufschläge, Kreditrahmen). Diese können als strukturierte Regeln in `kredit_dokumente` + `kredit_ausfuehrungsbestimmungen` eingepflegt werden (z. B. regel_key `tilgung_60_tag` = 10 %, `zinsaufschlag_1_90_tag` = 2,00, `kreditrahmen_gesamt` = 1500000).  
Die **Allgemeinen Bedingungen** und das **Gebührenverzeichnis** können als Quelldokumente hinterlegt werden; konkrete Gebührenpositionen optional als weitere Regeln.
