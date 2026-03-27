# TODO FOR CLAUDE - SESSION START TAG138

**Erstellt:** 2024-12-24

---

## Offene Aufgaben

### 1. Buchhaltung klären: "Privat a reg"
- Absatzweg "Privat a reg" hat nur Einsatz-Konten (724201, 724202)
- Wo wird der Erlös gebucht? Vermutlich in 824200 "Privat reg"
- Frage an Buchhaltung: Sollen separate Erlös-Konten angelegt werden?

### 2. TEK v2 - Weitere Verbesserungen (optional)
- Hinweis bei Absatzwegen ohne Erlös-Gegenstück anzeigen?
- "Kein direktes Erlöskonto - Erlös in [xxx] enthalten"

---

## Technischer Stand

### Datenbanken
- **PostgreSQL** (10.80.80.8) - Hauptdatenbank für alles
- SQLite wird NICHT mehr verwendet (vollständig migriert)

### TEK v2 Features
- Drill-Down mit Einsatz | Erlös | DB1 | DB%
- Konto-Matching über letzte 5 Ziffern (NW + GW kompatibel)
- Modelle- und Absatzwege-Tab mit Konten-Details

---

## Wichtige Dateien

| Modul | Dateien |
|-------|---------|
| TEK v2 | `templates/controlling/tek_dashboard_v2.html`, `routes/controlling_routes.py` |
| BWA | `scripts/sync/bwa_berechnung.py` |

---

## Hinweise für nächste Session

1. **PostgreSQL nutzen** - Nicht SQLite!
2. **Template-Sync:** Nach Änderungen `cp /mnt/greiner-portal-sync/templates/... /opt/greiner-portal/templates/`
3. **Strg+F5** für Hard-Refresh im Browser nach Template-Änderungen
