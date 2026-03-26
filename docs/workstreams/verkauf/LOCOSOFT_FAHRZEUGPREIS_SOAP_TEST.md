# Locosoft Fahrzeugpreis-Update per SOAP – Testergebnis

**Workstream:** Verkauf  
**Datum:** 2026-03-11  
**Frage:** Können wir Fahrzeugpreise in Locosoft per SOAP oder PostgreSQL ändern? Test: VIN KMHKR81EFPU172712 von 37.980 € auf 37.000 €.

## Kurzfassung

- **PostgreSQL Locosoft (10.80.80.8):** Für DRIVE **read-only** – keine Preisänderung.
- **SOAP writeVehicleDetails:** Enthält **keine Preisfelder**. Der Typ `DMSServiceVehicle` bildet nur Fahrzeugstammdaten ab (brand, model, vin, mileage, holderNumber, …), nicht `dealer_vehicles.out_sale_price` oder vergleichbare Verkaufspreis-Felder.
- **Ergebnis:** Preisänderung über die bestehende SOAP-API **nicht möglich**. Preise weiter in der Locosoft-UI pflegen oder bei Loco-Soft nach einer API für Händlerfahrzeug-/Verkaufspreis-Änderung fragen.

## Durchgeführter Test

- Skript: `scripts/test_locosoft_fahrzeugpreis_update.py`
- VIN: KMHKR81EFPU172712  
- Aus Locosoft-PostgreSQL: `vehicle_number` 53161, `dealer_vehicle_number` 210834, `out_sale_price` 37.980 €, `out_invoice_date` NULL.
- SOAP `writeVehicleDetails` mit `number` + `outSalePrice` → Fehler: „unexpected keyword argument 'outSalePrice'“; Signatur von `DMSServiceVehicle` listet keine Preisfelder.

## Referenzen

- CONTEXT.md Verkauf: Vermerk „Fahrzeugpreise in Locosoft“
- Werkstatt: `docs/workstreams/werkstatt/Fahrzeuganlage/LOCOSOFT_ANLAGE_SOAP.md` (PostgreSQL read-only, Schreiben nur SOAP)
- Locosoft-Schema: `dealer_vehicles.out_sale_price`, `out_estimated_invoice_value` etc. in `docs/DB_SCHEMA_LOCOSOFT.md`
