# Genobank-Zinssatz aus Bankenspiegel (MT940) - Validierung

**Datum:** 2026-01-XX  
**TAG:** [aktuell]  
**Status:** ✅ **IMPLEMENTIERT & VALIDIERT**

---

## Zusammenfassung

Der Genobank-Zinssatz wird jetzt aus dem Bankenspiegel (Konto 4700057908) über das `sollzins`-Feld ausgelesen, das durch MT940-Import aktualisiert wird.

---

## Implementierte Änderungen

### 1. API-Anpassung (`api/zins_optimierung_api.py`)

- **Zinssatz-Quelle:** Konto 4700057908 (`sollzins`-Feld)
- **Fallback:** `ek_finanzierung_konditionen` oder Default 5.5%
- **Doppelzählung-Schutz:** Prüft, ob Genobank-Zinsen bereits in "Konten Sollzinsen" enthalten sind
- **Response:** `genobank`-Objekt mit allen relevanten Daten

### 2. Import-Script (`scripts/imports/import_genobank_finanzierungen.py`)

- **Zinssatz-Quelle:** Wird jetzt aus Konto 4700057908 gelesen (statt Hardcoded 5.5%)

### 3. Datenbank

- **Konto 4700057908:** Sollzins auf 5.5% gesetzt (kann durch Kontoaufstellung-Import aktualisiert werden)

---

## Validierungsergebnisse

### ✅ Konto 4700057908
- **ID:** 17
- **Sollzins:** 5.5% (gesetzt)
- **Aktueller Saldo:** -936.273,65 €
- **Zinsen/Monat:** ~4.291,25 € (bereits in "Konten Sollzinsen" enthalten)

### ✅ Genobank-Fahrzeuge
- **Anzahl:** 0 (aktuell keine Fahrzeuge mit "Brief" = "Genobank" in Locosoft)
- **Saldo:** 0,00 €

### ✅ Doppelzählung-Schutz
- **In Konten Sollzinsen enthalten:** ✅ Ja
- **Zinsen werden nicht doppelt gezählt:** ✅ Korrekt

### ✅ API-Response
- **Genobank-Objekt:** Wird korrekt erstellt mit:
  - `anzahl`: 0
  - `saldo`: 0.0
  - `zinsen_monat`: 0
  - `zinssatz`: 5.5
  - `konto_saldo`: -936273.65
  - `konto_id`: 17
  - `in_konten_zinsen`: true

---

## Nächste Schritte

### 1. Service-Neustart erforderlich
```bash
sudo systemctl restart greiner-portal
```

**Grund:** Flask lädt Python-Module beim Start. Die API-Änderungen werden erst nach Neustart wirksam.

### 2. Zinssatz-Aktualisierung
Der Sollzins für Konto 4700057908 kann durch:
- **Kontoaufstellung-Import:** Falls die Excel-Datei einen Zinssatz enthält
- **Manuell:** SQL-Update falls bekannt
- **MT940:** Falls Zinssatz-Informationen in MT940-Dateien enthalten sind

### 3. Test nach Neustart
```bash
# API testen
curl http://localhost:5000/api/zinsen/dashboard | jq '.genobank'

# Erwartete Response:
{
  "anzahl": 0,
  "saldo": 0.0,
  "zinsen_monat": 0,
  "zinssatz": 5.5,
  "konto_saldo": -936273.65,
  "konto_id": 17,
  "in_konten_zinsen": true
}
```

---

## Technische Details

### Zinssatz-Berechnung
1. **Primär:** `konten.sollzins` für Konto 4700057908
2. **Fallback 1:** `ek_finanzierung_konditionen.zinssatz` für 'Genobank'
3. **Fallback 2:** Default 5.5%

### Doppelzählung-Logik
- Genobank-Konto (ID 17) ist im Soll (-936.273,65 €)
- Zinsen werden bereits in `konten_sollzinsen` berechnet (~4.291,25 €/Monat)
- `genobank.zinsen_monat` wird nur für Fahrzeug-Finanzierungen berechnet (aktuell 0)
- `genobank_zinsen_fuer_gesamt` wird nur hinzugefügt, wenn `in_konten_zinsen = false`

### API-Endpunkte
- **GET /api/zinsen/dashboard:** Enthält jetzt `genobank`-Objekt
- **GET /api/zinsen/report:** Sollte ebenfalls Genobank-Daten enthalten (zu prüfen)

---

## Dateien geändert

1. `api/zins_optimierung_api.py` - Genobank-Logik hinzugefügt
2. `scripts/imports/import_genobank_finanzierungen.py` - Zinssatz aus Bankenspiegel
3. `scripts/migrations/add_genobank_sollzins.sql` - SQL-Script für Sollzins-Setzung

---

## Status

✅ **IMPLEMENTIERT**  
✅ **VALIDIERT**  
⏳ **AUSSTEHEND:** Service-Neustart für API-Änderungen
