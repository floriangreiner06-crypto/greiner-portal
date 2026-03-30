# Kumulierte Zielprämie — Spec

## Ziel

Erweiterung der Zielprämie (I_neuwagen / Zielerfüllung) um eine kumulierte Betrachtung:
Der Verkäufer muss das **kumulierte Monatsziel** (Jan bis aktueller Monat) erreichen, damit eine Prämie ausgezahlt wird. Die Übererfüllung wird rein monatlich berechnet.

## Regeln

### Gate: Kumulierte Zielerreichung (Kalenderjahr)

```
Kumuliertes Ziel = Summe(Monatsziel Jan .. aktueller Monat)  — immer ab Januar des Kalenderjahres
Kumuliertes IST  = Summe(Monats-IST Jan .. aktueller Monat)

Gate bestanden: Kumuliertes IST >= Kumuliertes Ziel
```

### Prämienberechnung (nur wenn Gate bestanden)

```
Zielerreichung:  zielerreichung_betrag (z.B. 200 €)
Übererfüllung:   max(0, Monats-IST - Monats-Ziel) × stueck_praemie (z.B. 100 €/Stk.)
Stückprämie:     Zielerreichung + Übererfüllung
```

### Wenn Gate NICHT bestanden

Stückprämie = 0 € — unabhängig vom Einzelmonat.

### Keine Rückwirkung

Vergangene Monate werden nicht rückwirkend korrigiert. Nur der aktuelle Monat erhält die Prämie.

## Beispiele

### Beispiel 1: Gate nicht erreicht

| Monat | Ziel | IST | Kum. Ziel | Kum. IST | Gate | Zielerr. | Übererfüllung | Stückprämie |
|-------|------|-----|-----------|----------|------|----------|---------------|-------------|
| Jan   | 10   | 7   | 10        | 7        | ✗    | 0 €      | 0 €           | **0 €**     |
| Feb   | 10   | 12  | 20        | 19       | ✗    | 0 €      | 0 €           | **0 €**     |

### Beispiel 2: Gate knapp erreicht (kein Monats-Überschuss)

| Monat | Ziel | IST | Kum. Ziel | Kum. IST | Gate | Zielerr. | Übererfüllung | Stückprämie |
|-------|------|-----|-----------|----------|------|----------|---------------|-------------|
| Jan   | 10   | 7   | 10        | 7        | ✗    | 0 €      | 0 €           | **0 €**     |
| Feb   | 10   | 13  | 20        | 20       | ✓    | 200 €    | 3 × 100 €    | **500 €**   |

### Beispiel 3: Gate erreicht + Übererfüllung

| Monat | Ziel | IST | Kum. Ziel | Kum. IST | Gate | Zielerr. | Übererfüllung | Stückprämie |
|-------|------|-----|-----------|----------|------|----------|---------------|-------------|
| Jan   | 10   | 12  | 10        | 12       | ✓    | 200 €    | 2 × 100 €    | **400 €**   |
| Feb   | 10   | 11  | 20        | 23       | ✓    | 200 €    | 1 × 100 €    | **300 €**   |

### Beispiel 4: Gate erreicht, aber Monat unter Ziel

| Monat | Ziel | IST | Kum. Ziel | Kum. IST | Gate | Zielerr. | Übererfüllung | Stückprämie |
|-------|------|-----|-----------|----------|------|----------|---------------|-------------|
| Jan   | 10   | 15  | 10        | 15       | ✓    | 200 €    | 5 × 100 €    | **700 €**   |
| Feb   | 10   | 6   | 20        | 21       | ✓    | 200 €    | 0 €           | **200 €**   |

Feb: Gate bestanden (21 >= 20), aber monatlich unter Ziel (6 < 10) → keine Übererfüllung.

## Datenbank

### Neues Feld in provision_config

```sql
ALTER TABLE provision_config ADD COLUMN IF NOT EXISTS use_kumuliert BOOLEAN DEFAULT false;
```

Aktivierung nur für die bestehende Zeile `I_neuwagen / Zielerfüllung`. Alle anderen Provisionsarten bleiben `false`.

### Keine Änderung an provision_laeufe

Kumulierte Werte werden on-the-fly berechnet und als Rückgabewerte durchgereicht (nicht persistiert).

## Berechnung (provision_service.py)

### Neue Hilfsfunktion: get_kumulierte_zielpraemie_daten

```
get_kumulierte_zielpraemie_daten(vkb, monat, config) -> dict:
    jahr, monat_int = parse(monat)

    kum_ziel = 0
    kum_ist = 0
    for m in range(1, monat_int + 1):
        ziel_m = get_nw_ziel_verkaeufer_monat(vkb, jahr, m)
        if ziel_m == 0 and config.get('zielpraemie_fallback_ziel'):
            ziel_m = int(config['zielpraemie_fallback_ziel'])
        kum_ziel += ziel_m
        kum_ist  += get_stueck_fuer_monat(vkb, jahr, m, basis)  # auslieferung/auftragseingang

    monats_ziel = get_nw_ziel_verkaeufer_monat(vkb, jahr, monat_int)
    monats_ist  = get_stueck_fuer_monat(vkb, jahr, monat_int, basis)

    gate = kum_ist >= kum_ziel
    monats_ueber = max(0, monats_ist - monats_ziel) if gate else 0

    return {
        kum_ziel, kum_ist, kum_erfuellt (bool),
        monats_ziel, monats_ist, monats_ueber,
        zielerreichung_betrag (€ oder 0),
        uebererfuellung_betrag (monats_ueber × stueck_praemie oder 0),
        stueckpraemie_gesamt
    }
```

### Anpassung berechne_live_provision

Im Zielprämie-Block (ca. Zeile 440-467):

```
if cfg_i.get('use_zielpraemie'):
    if cfg_i.get('use_kumuliert'):
        daten = get_kumulierte_zielpraemie_daten(vkb, monat, cfg_i)
        stueck_praemie_anteil = daten['stueckpraemie_gesamt']
        # daten wird ins Result übernommen für Detail/PDF
    else:
        # bestehende Einzel-Monats-Logik (unverändert)
```

### IST-Zählung pro Monat

Nutzt die bestehende Logik je nach `zielpraemie_basis`:
- `auslieferung`: Zählung über `out_invoice_date` in sales (bestehende Query)
- `auftragseingang`: Zählung über `get_nw_auftragseingang_stueck(vkb, monat_str)`

Neue Hilfsfunktion `get_stueck_fuer_monat(vkb, jahr, monat, basis)` kapselt dies für beliebige Monate.

## Rückgabewerte (Result-Dict)

`berechne_live_provision()` gibt bei `use_kumuliert` zusätzliche Felder zurück:

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `kum_ziel` | int | Kumuliertes Ziel (Jan..Monat) |
| `kum_ist` | int | Kumuliertes IST (Jan..Monat) |
| `kum_erfuellt` | bool | Gate bestanden? |
| `monats_ziel` | int | Ziel des aktuellen Monats |
| `monats_ist` | int | IST des aktuellen Monats |
| `monats_ueber` | int | Übererfüllungs-Stück (monatlich) |

Diese Felder werden von Detail-Seite und PDF genutzt.

## Detail-Seite (provision_detail.html)

Wenn `use_kumuliert` aktiv, wird im Stückprämie-Bereich ein Info-Block angezeigt:

**Bei Erfüllung:**
```
Kumulierte Zielerreichung (Jan–Mrz 2026)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Kum. Ziel: 30 Stk.    Kum. IST: 31 Stk.    ✓ Erfüllt
Monat Mrz: Ziel 10    IST 11                +1 Übererfüllung

Zielerreichung:    200,00 €
Übererfüllung:     100,00 € (1 × 100,00 €)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stückprämie:       300,00 €
```

**Bei Nicht-Erfüllung:**
```
Kumulierte Zielerreichung (Jan–Mrz 2026)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Kum. Ziel: 30 Stk.    Kum. IST: 28 Stk.    ✗ Nicht erfüllt
→ Keine Stückprämie in diesem Monat
```

## PDF (provision_pdf.py)

Gleiche Kumulierungs-Information im PDF:
- **Deckblatt:** Kompakte Zusammenfassungszeile mit Kum. Ziel/IST und Status
- **Detail-Abschnitt:** Eigener Block mit kumulierten Werten und Berechnung (wie Detail-Seite)

## Config-Modal (provision_api.py + Template)

Neuer Checkbox im Modal, untergeordnet zu "Zielprämie (NW)":

```
☑ Zielprämie (NW)
  ☑ Kumulierte Zielerreichung
    Monatsziel muss kumuliert (Jan bis aktueller Monat) erreicht sein.
```

Checkbox nur sichtbar/aktiv wenn "Zielprämie (NW)" aktiviert ist.

API-Endpoints POST/PUT `/api/provision/config` akzeptieren und speichern `use_kumuliert`.

## Scope

### Im Scope
- Neues DB-Feld `use_kumuliert`
- Berechnungslogik in `provision_service.py`
- Hilfsfunktion für IST-Zählung beliebiger Monate
- Anzeige in Detail-Seite
- Anzeige im PDF
- Config-Modal Checkbox
- API GET/POST/PUT für `use_kumuliert`

### Nicht im Scope
- Andere Kategorien als I_neuwagen
- Rückwirkende Korrektur vergangener Monate
- Persistierung kumulierter Werte in provision_laeufe
- GW-Zielprämie (nur NW)
