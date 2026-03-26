# Fahrzeuganlage – Wo werden Daten geschrieben? Locosoft-Anlage per SOAP

**Stand:** 2026-02-20

## Klarstellung: Kein Schreiben in Locosoft-PostgreSQL

- **Locosoft PostgreSQL** (10.80.80.8, `loco_auswertung_db`) ist **read-only** für DRIVE (Spiegel/Mirror in `drive_portal`). Es wird **nicht** in die Locosoft-DB geschrieben.
- **DRIVE Portal PostgreSQL** (127.0.0.1, `drive_portal`): Hier speichern wir nur das **Scan-Archiv** in der Tabelle `fahrzeugschein_scans` (OCR-Ergebnis, Bildpfad, Halter/Fahrzeugdaten aus dem Schein). Das ist **keine** Stammdaten-Anlage von Kunde/Fahrzeug in Locosoft.
- Ein „Fahrzeug in unserer PostgreSQL anlegen“ im Sinne von **Locosoft-Stammdaten** machen wir **nicht** – weder in Locosoft-DB noch als Ersatz-Stamm in Portal. Die echte Anlage (Pr. 111/112) soll weiter in Locosoft erfolgen, idealerweise angebunden über **SOAP**.

## Phase 2: Anlage in Locosoft per SOAP

Zum **Schreiben** in Locosoft (Kunde/Fahrzeug anlegen) kommt nur die **Locosoft SOAP-API** in Frage (Schreibzugriff auf das DMS).

### Bereits im Projekt vorhanden

- **Config:** `config/locosoft_soap_config.py`  
  - Schreib-Operationen u. a.: `writeCustomerDetails`, `writeVehicleDetails` (V1, ohne zwingenden 2.2-Header).
- **Client:** `tools/locosoft_soap_client.py`  
  - `write_customer_details(customer: Dict)` → ruft `writeCustomerDetails` auf  
  - `write_vehicle_details(vehicle: Dict)` → ruft `writeVehicleDetails` auf  

Damit ist technisch die **Option „Anlage in Locosoft per SOAP“** gegeben.

### Was noch zu klären ist

1. **Neuanlage vs. Update**  
   - Ob `writeCustomerDetails` / `writeVehicleDetails` mit bestimmten Parametern (z. B. Nummer = 0 oder leer) eine **Neuanlage** erzeugen oder nur bestehende Datensätze aktualisieren, steht in der Locosoft-Doku bzw. WSDL. Das muss vor Phase-2-Implementierung geklärt werden.
2. **Feld-Mapping**  
   - Welche SOAP-Parameter (Kunde: Name, Adresse, …; Fahrzeug: FIN, Kennzeichen, HSN/TSN, Halter, …) für Neuanlage nötig sind und wie sie heißen, aus **WSDL** oder Locosoft-Dokumentation auslesen.
3. **Reihenfolge (verbindlich)**  
   - In Locosoft gilt: **Zuerst Kunde, dann Fahrzeug.**  
   - Umsetzung: Zuerst `writeCustomerDetails` ausführen → Kundennummer von Locosoft zurück; danach `writeVehicleDetails` mit Zuordnung zum angelegten Kunden. SOAP-Test muss diese Reihenfolge und die genauen Parameter prüfen.
4. **Betrieb/Standort**  
   - Welcher `subsidiary` / Betrieb (DEG/HYU/LAN) bei Anlage über SOAP gesetzt wird, muss definiert werden.

### Nächste Schritte

- **Kein** Schreiben in Locosoft-PostgreSQL.
- **Phase 1** (aktuell): Scan-Archiv nur in Portal-PostgreSQL; Dublettencheck nur **Lesen** aus `loco_vehicles`; Copy-to-Clipboard für manuelle Übernahme in Locosoft.
- **SOAP testen:** Vor Phase 2 ein Test-Script oder manuelle SOAP-Calls (z. B. mit `tools/locosoft_soap_client.py`): Neuanlage Kunde → Kundennummer → Neuanlage Fahrzeug (zu diesem Kunden). Reihenfolge: **erst Kunde, dann Fahrzeug** (wie in Locosoft).
- **Phase 2** (nach erfolgreichem Test): Button „In Locosoft anlegen“ im Modul Fahrzeuganlage; Aufruf `write_customer_details` → dann `write_vehicle_details` mit Kunden-Zuordnung; Feld-Mapping aus Scan/Maske gemäß WSDL.
