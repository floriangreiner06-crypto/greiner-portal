# Locosoft Memo „P1“ – Aushebelung NW-Provision (1% Rg.Netto)

**Stand:** 2026-03-02  
**Quelle:** Dispo/HR: Bei Fakturierung wird im Loco-Soft unter **Pr. 132**, Reiter **„Verkauf“**, Zeile **„Memo“** ein **„P1“** eingetragen. Dann tauchen die Provisionen automatisch bei **VFW/TW** auf. Berechnung: **1 % von Rechnungsbetrag netto**.

---

## 1. Identifikation in der Datenbank

### Locosoft (PostgreSQL, Read-Only)

| Datenbank   | Tabelle           | Spalte | Typ               | Bedeutung |
|------------|-------------------|--------|-------------------|-----------|
| loco_auswertung_db | **dealer_vehicles** | **memo** | character varying | Pr. 132 Reiter Verkauf, Zeile „Memo“. **P1** = dieser Verkauf soll nicht als Neuwagen (DB/Zielprämie), sondern wie VFW/TW (1 % Rg.Netto) provisioniert werden. |

- **Pr. 132** = Programm/Maske 132 in Locosoft (Fahrzeug-Detail, Reiter Verkauf).
- In Locosoft sind ca. **1.200+** verkaufte Fahrzeuge mit `memo = 'P1'` vorhanden (Stand Abfrage 2026-03-02).

### DRIVE Portal (PostgreSQL)

| Tabelle | Spalte | Herkunft | Bedeutung |
|---------|--------|----------|-----------|
| **sales** | **memo** | Sync aus `dealer_vehicles.memo` (Script `scripts/sync/sync_sales.py`) | Entspricht Locosoft. **P1** (nach Trim, case-insensitive) steuert in der Provisionsberechnung die Zuordnung. |

- Migration: `migrations/add_sales_memo.sql` (Spalte `sales.memo` + Kommentar).

---

## 2. Logik in DRIVE

- **Provisions-SSOT:** `api/provision_service.py` (Funktion `berechne_live_provision`).
- **Regel:**  
  - Wenn ein Verkauf nach `out_sale_type` in **Block I (Neuwagen)** fällt (F/N/D) **und** `sales.memo` (getrimmt, Großschreibung) **= „P1“** ist:  
    → Position wird **nicht** in Kat. I (Neuwagen) gezählt, sondern in **Kat. II (Testwagen/VFW)** verbucht.  
  - Berechnung: **1 % von Rechnungsbetrag netto** (Rg.Netto), inkl. Min/Max der Konfiguration für **II_testwagen** (provision_config: min_betrag 103 €, max_betrag 300 €).
- **Stück-/Zielprämie Neuwagen:** P1-Positionen zählen **nicht** zur Neuwagen-Stückzahl und **nicht** zur DB-Summe für die NW-Provision (DB/Zielprämie).

---

## 3. provision-config (http://drive/admin/provision-config)

- **Kat. I Neuwagen:** Unverändert (Bemessungsgrundlage db oder rg_netto, Zielprämie etc.). Nur Verkäufe **ohne** Memo P1 zählen hier.
- **Kat. II Testwagen/VFW:** Enthält zusätzlich alle **Neuwagen mit Memo P1**; Satz und Min/Max wie bisher (1 %, 103 € / 300 €). Keine Änderung an den Konfigurationsfeldern nötig – die **Daten** (memo) steuern die Zuordnung.

---

## 4. Sync

- **sync_sales.py** liest `TRIM(dv.memo) AS memo` aus `dealer_vehicles` und schreibt in `sales.memo`.
- Nach Deployment: Einmal **Verkauf-Sync** ausführen (oder nächsten geplanten Lauf abwarten), damit bestehende Verkäufe im Portal mit `memo` gefüllt werden.
- Neue Fakturierungen mit P1 in Locosoft werden beim nächsten Sync automatisch mit `memo = 'P1'` in `sales` übernommen.

---

## 5. Kurzfassung für Dispo/HR

- **Locosoft:** Pr. 132 → Reiter Verkauf → Zeile **Memo** → **P1** eintragen.
- **DRIVE:** Liest `memo` aus Locosoft, bucht diese Verkäufe bei der Provision in **VFW/TW** (1 % Rg.Netto, Min/Max wie VFW), nicht als Neuwagen.
