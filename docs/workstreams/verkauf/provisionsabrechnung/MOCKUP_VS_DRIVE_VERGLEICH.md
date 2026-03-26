# Provisions-Mockup vs. DRIVE – Vergleich

**Stand:** 2026-02  
**Mockup:** `provision_mockup.jsx` (React, im gleichen Ordner)  
**DRIVE:** Routes `/provision/dashboard`, `/provision/detail/<lauf_id>`, `/provision/meine` + API + `provision_service.py`

---

## 1. Was das Mockup zeigt

### 1.1 Layout
- **Sidebar:** DRIVE-Logo, Navigation (Controlling: Dashboard, Bankenspiegel, BWA; Verkauf: Auftragseingang, Auslieferungen, **Provisionen** mit Badge; Personal: Urlaub, Zeiterfassung; System: Einstellungen), User „Anton Süß, Verkaufsleiter“.
- **Top Bar:** Titel „Provisionsabrechnung“, Monat-Badge, **Monats-Dropdown** (Januar 2026, Dezember 2025, …).
- **Hauptbereich:** je nach View Dashboard oder Detail.

### 1.2 Dashboard
- **4 KPI-Karten:** Provisionen Gesamt (€), Fahrzeuge (ausgeliefert), Abgeschlossen (Anzahl Endläufe), Offen (noch zu bearbeiten).
- **Tabelle Verkäufer:** Spalten Verkäufer | VKB-Nr | **Fahrzeuge** | Provision | **Status** | Aktionen.
- **Status-Badges:** ENTWURF (grau), VORLAUF (orange), PRUEFUNG (blau), ENDLAUF (grün), LOHNBUCH (lila).
- **Header-Buttons:** „▶ Alle Vorläufe erstellen“, „⬇ Sammel-Export“.
- **Aktionen pro Zeile:** je nach Status „Vorlauf“, „→ Prüfung“, „✓ Endlauf“, „Details“; immer „Details“.
- **Fußzeile:** GESAMT (Fahrzeuge, Provision).
- Zeile klickbar → wechselt in Detail-Ansicht für diesen Verkäufer.

### 1.3 Detail (Provisionsabrechnung eines Verkäufers)
- **Header:** „← Zurück“, „Provisionsabrechnung: [Name]“, Status-Badge, Monat.
- **4 KPI-Karten:** I. Neuwagen (€ inkl. Stückprämie, Sub: „x Fzg. inkl. y € Stückpr.“), II. VFW/Testwagen, III. Gebrauchtwagen, IV. GW Bestand (jeweils € + Anzahl Fzg.).
- **Blöcke als Cards:**
  - **I. Neuwagen:** Tabelle Nr | Auslieferung | Marke | Typ | Käufer | DB | Provision; Fuß: Summe DB, Summe Provision, Zeile „Stückprämie: x × 50 €“.
  - **II. Vorführ-/Testwagen:** Nr | Auslieferung | Marke | Typ | Käufer | **Rg.Netto** | Provision (Titel: „1% auf Rg.Netto (min 103€, max **500€**)“).
  - **III. Gebrauchtwagen:** gleiche Struktur wie II (1% Rg.Netto, min 103€, max 500€).
  - **IV. GW aus Bestand:** Nr | Auslief. | Marke | Typ | Käufer | **DB** | **Kosten** | **Basis** | Provision (Titel: „12% auf (DB − Kosten)“).
- **Zusammenfassung & Jahresübersicht:** Card mit Monatssumme (Zeilen I–IV + Stückprämie, PROVISION fett) und **Jahresübersicht 2026** (Tabelle Monat | Fzg. | Gesamt, Jahressumme, „Davon abgerechnet / Noch offen“).
- **Buttons:** „📄 PDF Vorlauf“, „✓ Endlauf freigeben“.

---

## 2. Was DRIVE heute hat

### 2.1 Dashboard (`/provision/dashboard`)
- Monat: **input type=month** (YYYY-MM).
- **Eine Tabelle „Läufe“:** Verkäufer | Status | Summe | Aktionen (Detail-Link, bei VORLAUF: Löschen).
- **Zweite Tabelle „Verkäufer (Vorlauf erstellen)“:** VKB | Name | Button „Vorlauf“ (wenn noch kein Lauf).
- Keine KPIs, keine Fahrzeuganzahl, keine Status-Badges, keine Buttons „Alle Vorläufe“ / „Sammel-Export“, keine GESAMT-Zeile.

### 2.2 Detail (`/provision/detail/<lauf_id>`)
- Verkäufer, Monat, Status, Summe (eine Zeile).
- **Kategorie-Summen:** I–V + Gesamt + Kumulierte Summen (I, I+II, I+II+III, …).
- **Eine gemeinsame Positionen-Tabelle:** Kat. | Verkäufer | Einkäufer | Käufer | Modell | Rg.Nr. | Provision.
- Links: „← Dashboard“, bei Vorlauf „Vorlauf löschen“.
- Keine KPI-Cards, keine **getrennten Blöcke** (I / II / III / IV) mit eigenen Tabellen, keine Spalten Auslieferung/Marke/Typ, bei IV keine Spalten DB/Kosten/Basis, keine **Jahresübersicht**, keine Buttons „PDF Vorlauf“ / „Endlauf freigeben“.

### 2.3 Meine Provision (`/provision/meine`)
- Live-Berechnung eigener Provision (aktueller Monat), ohne Lauf – im Mockup nicht abgebildet (Verkäufer-Sicht).

### 2.4 Fachlogik (Backend)
- Berechnung I–IV + Stückprämie/Zielprämie wie in PROVISIONSREGELN_SYSTEM.md; IV mit J60/J61; Einkäufer/DB2 abgebildet. **Daten für die erweiterte Darstellung (DB, Kosten, Basis, Rg.Netto pro Position) liefert die API bereits** (`positionen_i/ii/iii/iv` mit `deckungsbeitrag`, `rg_netto`, etc. im Live-Ergebnis; im Lauf-Detail kommen Positionen aus DB mit `deckungsbeitrag`, `rg_netto`, `provision_final`).

---

## 3. Gegenüberstellung: Mockup vs. DRIVE

| Aspekt | Mockup | DRIVE |
|--------|--------|--------|
| **Sidebar / Gesamtlayout** | Sidebar mit DRIVE-Nav, Provisionen hervorgehoben | Standard base.html, keine eigene Sidebar für Provisionen |
| **Monatsauswahl** | Dropdown in Top Bar | Dashboard: input type=month; Detail: nur über Dashboard |
| **Dashboard KPIs** | 4 Karten (Gesamt €, Fahrzeuge, Abgeschlossen, Offen) | Fehlt |
| **Dashboard Tabelle** | Verkäufer, VKB, **Fahrzeuge**, Provision, **Status**, Aktionen | Läufe: Verkäufer, Status, Summe, Aktionen; separate Tabelle „Verkäufer“ für Vorlauf |
| **Status-Darstellung** | Badges (ENTWURF, VORLAUF, PRUEFUNG, ENDLAUF, LOHNBUCH) | Text |
| **„Alle Vorläufe erstellen“** | Button | Fehlt |
| **„Sammel-Export“** | Button | Fehlt |
| **GESAMT-Zeile Dashboard** | Fahrzeuge + Provision | Fehlt |
| **Detail: KPI-Cards** | I–IV mit € und Fzg.-Anzahl | Nur Summen-Tabelle (I–V + Gesamt + Kumuliert) |
| **Detail: Blöcke I–IV** | Pro Kategorie eigene Card + Tabelle (mit Ausl., Marke, Typ, Käufer, DB/Netto, Provision; IV: DB, Kosten, Basis) | Eine flache Positionen-Tabelle (Kat, Verkäufer, Einkäufer, Käufer, Modell, Rg.Nr., Provision) |
| **Detail: IV Spalten** | DB, Kosten, Basis, Provision | In API vorhanden; in UI keine Spalten Kosten/Basis, keine Aufteilung nach Blöcken |
| **Jahresübersicht** | Tabelle Monat | Fzg. | Gesamt + Jahressumme | Fehlt |
| **PDF Vorlauf / Endlauf freigeben** | Buttons | Fehlt |
| **II. VFW Max** | 500 € (im Mockup-Titel) | Config 300 € (laut PROVISIONSREGELN_SYSTEM) |

---

## 4. Kurzbewertung

- **Berechnung:** DRIVE deckt die Regeln I–IV inkl. DB2/Einkäufer und J60/J61 ab; Mockup zeigt dieselbe Struktur (I–IV, Stückprämie, IV mit DB/Kosten/Basis).
- **UX/Layout:** Mockup ist deutlich reicher: KPIs, Status-Badges, getrennte Blöcke pro Kategorie, Jahresübersicht, Sammel-Export, „Alle Vorläufe“, PDF/Endlauf-Buttons.
- **Daten:** Die nötigen Felder (DB, Rg.Netto, Kosten/Basis für IV, Auslieferungsdatum, Modell) sind in der API/Struktur vorhanden; Detail-View müsste sie nur pro Block ausgeben und optional Jahresübersicht aus weiteren API-Daten füllen.

**Empfehlung:** Schrittweise das Dashboard um KPIs, Status-Badges, Fahrzeuganzahl und GESAMT-Zeile erweitern; Detail-View in **Blöcke I–IV** mit je eigener Tabelle (inkl. IV: DB, Kosten, Basis) und optional Jahresübersicht + Buttons (PDF, Endlauf) an das Mockup annähern. Sidebar-Option später, wenn ein einheitliches DRIVE-Layout gewünscht ist.
