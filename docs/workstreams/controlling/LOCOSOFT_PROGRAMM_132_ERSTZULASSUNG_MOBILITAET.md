# Locosoft Programm 132 – Erstzulassung und Santander-Mobilität

## Hintergrund

Im **Locosoft Programm 132** (Fahrzeugstamm / dealer_vehicles) wird der Fahrzeugtyp über `dealer_vehicle_type` geführt (N, T, V, D, G, L …). Die **Erstzulassung** steht in der Tabelle **`vehicles`** in der Spalte **`first_registration_date`**.

**Problem:** Stellantis-Fahrzeuge in EK-Finanzierung können in Locosoft weiterhin als „Neuwagen“ (dealer_vehicle_type = 'N') geführt werden, obwohl sie bereits **zugelassen** sind (first_registration_date gesetzt). Für **Santander** zählen solche Fahrzeuge nur unter dem **Mobilitäts-Rahmen** (z. B. 500.000 €), nicht unter dem Neuwagen-/Gebrauchtwagen-Rahmen. Wird die Erstzulassung nicht ausgewertet, erscheinen sie im Portal fälschlich als „Mobilität: Nein“ und die Umfinanzierungsempfehlung kann den verfügbaren Mobilität-Rahmen überschreiten.

## Relevante Locosoft-Daten (Programm 132)

| Quelle | Spalte | Bedeutung |
|--------|--------|-----------|
| `dealer_vehicles` | `dealer_vehicle_type` | N=Neuwagen, T=Tageszulassung, V=Vorführer, D=Demo, G=Gebraucht, L=Leihfahrzeug |
| `dealer_vehicles` | `is_rental_or_school_vehicle` | Mietwagen/Schulungsfahrzeug |
| `dealer_vehicles` | `pre_owned_car_code` | z. B. 'M' = Mietwagen (Buchhaltung) |
| **`vehicles`** | **`first_registration_date`** | **Erstzulassungsdatum** – wenn gesetzt, ist das Fahrzeug bereits zugelassen |

## DRIVE-Logik: Santander „Mobilität“

**Modul:** `api/zins_optimierung_api.py` → `_locosoft_fahrzeuge_fuer_vins()`.

Ein Fahrzeug gilt für Santander als **Mobilität**, wenn mindestens eine der folgenden Bedingungen zutrifft:

1. **Vorführer/Demo:** `dealer_vehicle_type` IN ('V', 'D')
2. **Tageszulassung:** `dealer_vehicle_type` = 'T'
3. **Neuwagen mit Erstzulassung:** `dealer_vehicle_type` = 'N' **und** `vehicles.first_registration_date IS NOT NULL` (bereits zugelassen → bei Santander Mobilität)
4. **Mietwagen:** `is_rental_or_school_vehicle` = true
5. **GW-Mietwagen (Buchhaltung):** `dealer_vehicle_type` = 'G' und `pre_owned_car_code` = 'M'

Die Abfrage nutzt **vehicles** (Erstzulassung) und **dealer_vehicles** (Typ, Mietwagen-Kennzeichen) aus der Locosoft-PostgreSQL-DB. So werden auch Stellantis-Fahrzeuge, die in Programm 132 noch als „N“ geführt werden, aber bereits eine Erstzulassung haben, korrekt als Mobilität gezählt und die Umfinanzierungsempfehlung bleibt innerhalb des Mobilität-Rahmens.

## Prüfung in Locosoft

- In **Programm 132** prüfen: Ist bei betroffenen Stellantis-Fahrzeugen die **Erstzulassung** (first_registration_date / EZ) gepflegt, sobald das Fahrzeug zugelassen ist?
- Optional: Soll der **Fahrzeugtyp** von N auf T (Tageszulassung) umgestellt werden, sobald zugelassen? Dann würde die Anzeige auch ohne Auswertung der Erstzulassung stimmen; DRIVE wertet beides aus (Typ T oder N mit EZ).

## Siehe auch

- `docs/DB_SCHEMA_LOCOSOFT.md` – Tabellen `vehicles`, `dealer_vehicles`
- Zins-Optimierung / EK-Finanzierung: Bankenspiegel → Fahrzeugfinanzierungen, Modal „Stellantis → Santander“
