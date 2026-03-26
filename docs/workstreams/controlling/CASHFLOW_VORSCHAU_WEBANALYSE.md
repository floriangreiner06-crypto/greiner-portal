# Cashflow-Vorschau / Liquiditätsplanung – Webanalyse fertige Tools

**Workstream:** Controlling  
**Stand:** 2026-03-02  
**Zweck:** Prüfung, ob sich bestehende Open-Source- oder Standard-Tools für eine Cashflow-Vorschau im DRIVE adaptieren lassen.

---

## Ergebnis Kurzfassung

- **Fertige „Cashflow-Vorschau“-Produkte** (pycashflow, liquidity_planning, Cashflowy etc.) sind **nicht 1:1 übernehmbar**: andere Tech-Stacks (ERPNext, eigenes Auth), andere Datenquellen (kein MT940/Locosoft), andere Zielgruppe (Privatanwender/SME generisch).
- **Sinnvoll:** Konzepte und Logik (Projektion, Kategorien, Laufzeiten) als Inspiration nutzen und **im DRIVE bauen** – auf Basis **Bankenspiegel** (`transaktionen`, `konten`, Kategorisierung), **Locosoft** (OPOS, FIBU), **tilgungen** und ggf. geplanten Zahlungsläufen.
- **Bibliotheken:** MT940-Parsing (z. B. `wolph/mt940` Python) kann bei Bedarf ergänzend genutzt werden; DRIVE hat bereits MT940-Import und Transaktionen in PostgreSQL.

---

## Analysierte Tools (Auswahl)

### 1. PyCashFlow (whahn1983/pycashflow)

- **Stack:** Python, Flask, SQLAlchemy, Plotly, Pandas; SQLite/PostgreSQL; GPL-3.0.
- **Features:** 12-Monate-Cashflow-Projektion, wiederkehrende Transaktionen (Monatlich/Wöchentlich/etc.), Laufende Salden, Mindestbestand-Warnung, E-Mail-IMAP für Salden-Updates, Multi-User/Rollen.
- **Daten:** Eigenes Modell (Schedules, Balances); **kein** MT940, keine Anbindung an Buchhaltung/Bankenspiegel.
- **Bewertung:** Logik (Projektion, Frequenzen, Business Days) gut übertragbar. **Nicht** als Fremdsystem integrieren (eigenes Auth, eigenes Datenmodell); Ideen für **eigene** DRIVE-Funktion „geplante Zahlungen + IST-Transaktionen → Vorschau“ nutzbar.

### 2. Liquidity Planning (alyf-de/liquidity_planning)

- **Stack:** ERPNext App (Frappe), Python; GPL-3.0.
- **Features:** Report „Cash Flow Forecast“ aus Sales Orders, Purchase Orders, Invoices, Gehälter (CTC), Expense Claims; Filter Firma, Zeitraum, Periodizität, Währung.
- **Daten:** Vollständig aus ERPNext (kein MT940, keine Bankkonten wie im DRIVE).
- **Bewertung:** Konzept „Einnahmen/Ausgaben aus bestehenden Modulen aggregieren“ passt zu DRIVE (Locosoft FIBU, OPOS, Bankenspiegel). **Nicht** als App übernehmbar (ERPNext-spezifisch); **Methodik** (Zeiträume, Kategorien, Netto-Cashflow) für DRIVE-Liquiditätsmodul nutzbar.

### 3. Cashflowy (asyncauto/cashflowy)

- **Stack:** Apache-2.0; API-Ordner im Repo.
- **Bewertung:** Wenig Doku; API-Ansatz prinzipiell interessant. Keine direkte Passung zu DRIVE-Daten (MT940, Locosoft, Bankenspiegel).

### 4. MT940 / Bankdaten

- **wolph/mt940 (Python):** MT940 parsen → Python-Strukturen; nützlich wenn man Parsing auslagern will. DRIVE hat bereits **eigenen** MT940-Import und speichert in `transaktionen`.
- **Oracle Banking Cash Management API, Open Banking APIs:** REST-Cashflow-Projektion; Ziel Großbanken/Enterprise, nicht ohne Weiteres für DRIVE-Stack und On-Prem-Banken nutzbar.

---

## Passung zum DRIVE (Controlling Workstream)

| DRIVE-Baustein | Relevanz für Cashflow-Vorschau |
|----------------|--------------------------------|
| **Bankenspiegel** | `konten`, `transaktionen`, `daily_balances`; Kategorisierung (regelbasiert + KI) bereits umgesetzt. **IST-Daten** und kategorisierte Verläufe als Basis. |
| **MT940/PDF-Import** | Kontobewegungen laufend in `transaktionen`; kein zusätzliches Tool nötig. |
| **Kategorien** | `transaktionen.kategorie` / `unterkategorie`; Dashboard nach Kategorien; Grundlage für „Einnahmen/Ausgaben nach Kategorie“ in Vorschau. |
| **tilgungen** | Geplante Tilgungen (Hyundai); Erweiterung um Stellantis/Santander wenn Daten verfügbar. |
| **Locosoft** | FIBU, OPOS; für „erwartete“ Umsätze/Debitoren optional; SSOT-Regel beachten. |
| **PLAN_LIQUIDITAET_KATEGORISIERUNG_TILGUNGEN.md** | Kategorisierung ✅; Tilgungsmuster und nächster Schritt „Vorschau“ beschrieben. |

---

## Empfehlung

- **Kein** fremdes Cashflow-Produkt 1:1 integrieren oder ersetzen.
- **Cashflow-Vorschau im DRIVE neu bauen:**
  - **IST:** Salden und Transaktionen aus Bankenspiegel (bereits vorhanden).
  - **Plan:** (1) Wiederkehrende/geplante Zahlungen (neu oder aus `tilgungen`), (2) optional erwartete Einnahmen/Ausgaben aus Kategorien-Mittelwerten oder einfachen Regeln.
  - **Ausgabe:** Zeitreihe (täglich/wöchentlich/monatlich) „Saldo heute + erwartete Bewegungen“; Darstellung z. B. Chart + Tabelle; Mindestbestand-Warnung optional.
- Konzepte aus **PyCashFlow** (Projektionslogik, Frequenzen, Laufende Salden) und **Liquidity Planning** (Aggregation Einnahmen/Ausgaben, Periodizität) in der Doku/Implementierung referenzieren.

---

## Nächste Schritte (nach Projektentscheid)

1. Anforderung „Cashflow-Vorschau“ im Controlling-Workstream verankern (CONTEXT.md, ggf. eigenes Konzept-Doc).
2. Datenmodell klären: nur Bankenspiegel + `tilgungen` oder zusätzlich „geplante Zahlungen“ (neue Tabelle/Config).
3. SSOT: Eine Stelle für Projektionslogik (analog TEK in `api/controlling_data.py`); API unter `api/` (z. B. `bankenspiegel_api.py` oder neues Modul), Routes/Templates unter Controlling.
