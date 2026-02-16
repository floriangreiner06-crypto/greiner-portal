# AfA Buchhaltungs-Excel – Auswertung 2026-02-16

## Dateien

| Datei | Inhalt | Fz.-Art | Jw-Kz (Spalte) | Zeilen (Daten) |
|-------|--------|---------|----------------|----------------|
| mietwagendeg.xlsx | Mietwagen Deggendorf | G | **M** | 31 |
| mietwagenlandau.xlsx | Mietwagen Landau | G | **M** | 15 |
| vfwopeldeg.xlsx | VFW Opel Deggendorf | V | leer | 16 |
| vfwopellandau.xlsx | VFW Opel Landau | V | leer | 2 |
| vfwhyundai.xlsx | VFW Hyundai | V | leer | 42 |
| vfwleapmotor.xlsx | VFW Leapmotor | V | leer | 5 |
| Scan_20260216130905.pdf | DATEV Vorführwagen | — | — | (Scan) |

## Spalten (Excel)

- **Fz.-Art:** Fahrzeugart (V = Vorführwagen, G = Gebrauchtwagen/Mietwagen)
- **Kom.Nr.:** Kommissionsnummer (Locosoft dealer_vehicle_number)
- **Jw-Kz:** Jahreswagenkennzeichen (pre_owned_car_code); bei Mietwagen-Listen = **M**, bei VFW oft leer
- **Fabrikat, Modell-Code, Modell-Bez., Fahrgestellnr. (VIN), Buchwert, Erstzulassung, Fzg.-Eingang/-Ausgang** usw.

## Folgerungen für DRIVE

1. **Mietwagen-Filter:** Neben „X“ (eigene, Locosoft) wird **„M“** (Jw-Kz aus Buchhaltung) akzeptiert: `pre_owned_car_code IN ('X', 'M')` sowie Kennzeichen enthält „X“. So decken sich Kandidaten in DRIVE mit den Buchhaltungs-Mietwagen-Listen.
2. **VFW:** Filter `dealer_vehicle_type = 'V'` bleibt; entspricht Fz.-Art V in den Listen.
3. **Nutzungsdauer:** In Excel keine Spalte gefunden; Modul-Default **72 Monate** beibehalten.

## Abgleich durchführen

Script: `scripts/afa_vergleiche_buchhaltung_excel.py`  
Ausführung: `python scripts/afa_vergleiche_buchhaltung_excel.py`

Optional: VIN/Kom.Nr. aus Excel mit Locosoft-Kandidaten (API `GET /api/afa/locosoft-kandidaten`) abgleichen, um Abweichungen zu prüfen.
