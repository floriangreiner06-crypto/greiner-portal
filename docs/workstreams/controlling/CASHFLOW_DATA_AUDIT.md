# Cashflow Data Audit – DRIVE Portal

**Datum:** 2026-03-02  
**Status:** Erste Befunde (Schritte 1, 2, 7); Schritte 3–6 (Locosoft) und 8–9 bei Bedarf ergänzen.

---

## ✅ VORHANDEN & DIREKT NUTZBAR

| Kategorie | Quelle | Datenqualität | Anmerkung |
|-----------|--------|---------------|-----------|
| **Kontosalden** | View `v_aktuelle_kontostaende` (baut auf `konten` + `salden`) | Gut | Spalten: id (= Konto-ID), kontoname, iban, saldo, letztes_update, kreditlinie, bank_name. Gesamtsaldo und neuester Stand abfragbar. |
| **Transaktionen IST** | Tabelle `transaktionen` | Gut | 2021-01-27 bis 2026-03-02, ~19.060 Buchungen. Spalten: buchungsdatum, betrag, verwendungszweck, buchungstext, gegenkonto_name, auftraggeber_empfaenger, kategorie, unterkategorie. |
| **Kategorisierung** | `transaktionen.kategorie` | Teilweise | ~7.500 kategorisiert, ~11.560 unkategorisiert. Regeln + KI vorhanden (`api/transaktion_kategorisierung.py`). |
| **Tilgungen (geplant)** | Tabelle `tilgungen` | Gut | 110 zukünftige Positionen, Summe ~1,14 Mio €. Nutzbar für Ausgaben-Prognose. |
| **Einkaufsfinanzierung** | Tabelle `fahrzeugfinanzierungen` | Vorhanden | Spalten: finanzinstitut, finanzierungsbetrag, aktiv; Zins-Felder (zinsen_berechnet, zinsen_letzte_periode, zins_startdatum). Aktiv: Genobank 33, Santander 67, Stellantis 90, Hyundai 60 Fahrzeuge. |

---

## ⚠️ VORHANDEN, ABER AUFBEREITUNG NÖTIG

| Kategorie | Problem | Vorgeschlagene Lösung |
|-----------|---------|------------------------|
| **Unkategorisierte Transaktionen** | ~11.560 ohne Kategorie | Kategorisieren-Job (bereits API vorhanden) regelmäßig laufen lassen oder Batch mit KI; danach Auswertung „Einnahmen/Ausgaben nach Kategorie“ für Prognose nutzen. |
| **Geplante Zahlungen** | Keine Tabelle „wiederkehrende Positionen“ | Entweder Muster aus Transaktionen ableiten (z. B. gleicher gegenkonto_name, ähnlicher Betrag, monatlich) oder neue Tabelle `geplante_cashflow_positionen` (Datum, Betrag, Typ, Kategorie). |
| **Zinslast pro Monat (EK-Finanzierung)** | Spalte `zins_aktuell` existiert nicht; vorhanden: zinsen_berechnet, zinsen_letzte_periode | Zinslast aus vorhandenen Feldern oder aus `tilgungen` ableiten; ggf. kleines Aggregat in API. |

---

## ❌ NICHT AUTOMATISIERBAR – MANUELLE PFLEGE NÖTIG

| Kategorie | Warum nicht automatisch | Was konfigurieren |
|-----------|-------------------------|-------------------|
| **Hersteller-Abschläge (E4)** | Konten/Buchungstexte in FIBU müssen identifiziert werden | Nach Audit Schritt 4: Konten und ggf. Regeln in DRIVE hinterlegen (oder aus loco_journal_accountings per Konfig filterbar machen). |
| **Fixkosten (Miete, USt, Versicherung)** | Teilweise in Transaktionen erkennbar, aber nicht durchgängig | Regeln in transaktion_kategorisierung erweitern; wiederkehrende Beträge optional als „geplante Positionen“ einmalig anlegen. |

---

## ❓ UNGEKLÄRT – RÜCKFRAGEN AN FLORIAN/BUCHHALTUNG

- Unter welchem **Kontonamen/Buchungstext** tauchen die **Stellantis-Abschlagszahlungen** in der FIBU auf? (Audit Schritt 4 ausführen und Beispiele dokumentieren.)
- **Zahlungsdatum vs. Buchungsdatum:** An welchem Tag im Monat gehen Gehälter typischerweise raus (für Plan-Projektion)?
- Sollen **Mindestbestände** pro Konto oder global konfigurierbar sein für die Warnung?

---

## 📊 DATENQUALITÄTS-ZUSAMMENFASSUNG

| Kategorie | Quelle | Verfügbar | Qualität (1–5) | Anmerkung |
|-----------|--------|-----------+----------------|-----------|
| Kontosalden | v_aktuelle_kontostaende, salden | Ja | 5 | Tagesaktuell, View nutzt letzte Salden pro Konto. |
| Transaktionen IST | transaktionen | Ja | 5 | Langer Zeitraum, Kategorien teils gesetzt. |
| Kategorien | transaktionen.kategorie | Ja | 3 | Ca. 40 % kategorisiert; Rest nachziehen. |
| Tilgungen | tilgungen | Ja | 5 | 110 zukünftige, Summe klar. |
| EK-Finanzierung Bestand | fahrzeugfinanzierungen | Ja | 4 | Zins-Prognose aus vorhandenen Feldern ableitbar. |
| Personalkosten (FIBU) | loco_journal_accountings 74xxxx | Ja | 4 | Audit Schritt 3: monatliche Serie prüfen. |
| Hersteller-Abschläge | loco_journal_accountings | Unklar | 2 | Schritt 4: Konten/Buchungstexte identifizieren. |
| Geplante Fixkosten | transaktionen Muster / neue Tabelle | Teilweise | 2 | Muster oder manuelle Pflege. |

---

## 🗓️ EMPFOHLENE IMPLEMENTIERUNGS-REIHENFOLGE

- **Phase 1 (sofort umsetzbar):** Liquiditätsvorschau aus **IST-Daten**: Salden (v_aktuelle_kontostaende) + Transaktionen (bis Stichtag) + **Tilgungen** (tilgungen) als Zeitreihe (z. B. 30/60/90 Tage). Eine API-Funktion „projiziere_saldo(datum_start, datum_ende)“; Ausgabe: Liste pro Tag/Woche mit Saldo und erwarteten Bewegungen. Kein neues Datenmodell nötig.
- **Phase 2 (nach Konfiguration):** Geplante wiederkehrende Positionen (Gehalt, Miete, USt) abbilden – entweder aus Transaktions-Mustern oder Tabelle „geplante_cashflow_positionen“; in Projektion einrechnen.
- **Phase 3 (mittelfristig):** Hersteller-Abschläge (E4) und Fahrzeugeinkauf (A1) aus FIBU in Prognose; Mindestbestand-Warnung; optional E-Mail-Report.

---

## Technische Hinweise (aus Audit)

- **View v_aktuelle_kontostaende:** Spalte für Konto ist **`id`** (von konten), nicht `konto_id`. Join mit konten: `konten.id = v_aktuelle_kontostaende.id`.
- **transaktionen:** Enthält sowohl `auftraggeber_empfaenger` als auch `gegenkonto_name`; für Auswertungen beide nutzbar.
- **fahrzeugfinanzierungen:** Zins-Felder u. a. `zinsen_berechnet`, `zinsen_letzte_periode`, `zins_startdatum` (kein `zins_aktuell`).
