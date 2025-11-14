# AKTUELLER DATENBANK-STAND

## Wichtige Geschäftslogik:
- Autohaus Greiner GmbH & Co. KG (Hauptfirma)
- Auto Greiner GmbH & Co. KG (Schwester)
- Greiner Immobilien Verwaltungs GmbH (NICHT Autohaus, nur Vermieter)

## Interne Transaktionen:
- Zwischen den beiden Autohaus-Firmen = INTERN
- Mit Immobilien GmbH = EXTERN (ist Vermieter)

## Parser-Regeln:
- Kontoauszug ist die WAHRHEIT
- KEINE Salden berechnen
- Salden aus PDF übernehmen
- kontostand_historie Tabelle nutzen

## Import-Stand:
- Oktober: KOMPLETT (~3000 Transaktionen)
- November: TODO (243 Transaktionen aus 40 PDFs)

## Bekannte Konten:
- Sparkasse KK (IBAN: DE63741500000760036467)
- 57908 KK (IBAN: DE27741900000000057908)
- 22225 Immo KK (IBAN: DE64741900000000022225)
- 20057908 Darlehen (IBAN: DE94741900000020057908)
- 1700057908 Festgeld (IBAN: DE96741900001700057908)
- Hypovereinsbank KK (IBAN: DE22741200710006407420)
- 303585 VR Landau KK (IBAN: DE76741910000000303585)
- 1501500 HYU KK (IBAN: DE68741900000001501500)
- 4700057908 Darlehen (IBAN: DE58741900004700057908)
- KfW 120057908 (IBAN: DE41741900000120057908)
Stand: Thu Nov 13 01:27:01 PM CET 2025
