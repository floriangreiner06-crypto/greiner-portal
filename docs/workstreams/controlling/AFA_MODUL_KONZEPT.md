# AfA-Modul Vorführwagen / Mietwagen — Konzept

**Stand:** 2026-02-16  
**Workstream:** Controlling

## Ziel

Automatische Berechnung der **monatlichen Abschreibung (AfA)** für Vorführwagen (VFW) und Mietwagen im Anlagevermögen. Bisher manuell in DATEV/Locosoft; DRIVE stellt die Berechnung und eine Buchungsliste für die Einbuchung bereit.

## Fachliche Regeln

- **Einordnung:** Anlagevermögen (nicht Umlaufvermögen).
- **Nutzungsdauer:** 72 Monate (6 Jahre), konfigurierbar; auch bei kurzer Nutzungsdauer als VFW/Mietwagen (BFH VIII R 64/06).
- **Methode:** Lineare Abschreibung (§ 7 Abs. 1 EStG). Degressive AfA (ab 01.07.2025) als spätere Erweicherung vorgesehen (Feld `afa_methode`).
- **Bemessungsgrundlage:** Netto-Anschaffungskosten (EK netto inkl. Sonderausstattung, Überführung, Zulassung).
- **Monatliche AfA:** `Anschaffungskosten_netto / 72` (bzw. konfigurierbare Nutzungsdauer).
- **Monatsgenau:** Anschaffungsmonat und Abgangsmonat zählen voll.
- **Abgang:** Bei Verkauf/Umbuchung Restbuchwert und Buchgewinn/-verlust erfassbar.

## Technische Umsetzung

| Komponente | Beschreibung |
|------------|--------------|
| **DB** | `afa_anlagevermoegen` (Stammdaten), `afa_buchungen` (monatliche Buchungen). Migration: `docs/migrations/migration_afa_modul.sql` |
| **API** | `api/afa_api.py` — Dashboard, Fahrzeuge, Detail, Monatsberechnung, Buchungsliste, CRUD, Abgang, Health |
| **Frontend** | `routes/afa_routes.py` → `templates/controlling/afa_dashboard.html` (KPI-Karten, Tabelle mit Filter, Monatsübersicht, CSV-Export, Detail-Modal mit Chart) |
| **Navigation** | Controlling → AfA Vorführwagen/Mietwagen (Berechtigung: controlling oder admin) |
| **Celery** | Task `afa_monatsberechnung`: Monatliche AfA für alle aktiven Fahrzeuge in `afa_buchungen` schreiben (z. B. am 1. des Monats für Vormonat) |

## Discovery & Datenquellen

- **DRIVE:** Keine bestehende SSOT für VFW/Mietwagen-Liste → neue Tabelle.
- **Locosoft:** `dealer_vehicle_type`, `is_rental_or_school_vehicle` vorhanden; optional später Anreicherung/Import.
- **FIBU:** Buchhaltung bucht Monatsende: **450001/450002** an **090301/090302** (Mietwagen) bzw. **090401/090402** (VFW). Abgang: 090xxx an Bestandskonto. Details: **`AFA_BUCHHALTUNG_FEEDBACK.md`**.

Details Discovery: **`AFA_DISCOVERY.md`**.

## Nächste Schritte (optional)

1. RedBeat/Celery Beat: `afa_monatsberechnung` am 1. jeden Monats (für Vormonat) planen.
2. Formular „Neues Fahrzeug anlegen“ im Dashboard (derzeit nur API POST).
3. Degressive AfA (ab 01.07.2025) ergänzen, wenn gewünscht.
