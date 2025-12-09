# PROMPT FÜR TAG 97 - Kopieren und in neuen Chat einfügen

---

## START-PROMPT:

```
Weiter mit TAG 97 - ML Werkstatt Intelligence Verbesserungen.

Kontext:
- TAG 96 abgeschlossen (ML-Modell + API + Dashboard live)
- Server: 10.80.80.20, User: ag-admin, PuTTY-Session
- Sync-Verzeichnis: \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\

Bitte lies zuerst:
1. /mnt/project/CLAUDE.md (Projekt-Anweisungen)
2. docs/SESSION_WRAP_UP_TAG96.md (Was wurde gemacht)
3. docs/TODO_TAG97.md (Was ist zu tun)

Dann starten wir mit den Dashboard-Verbesserungen:
- Mechaniker-Namen statt Nummern
- Ranking-Filter fixen
- Menü-Link hinzufügen

Arbeitsweise: Du schreibst Dateien im Sync-Verzeichnis, ich kopiere einzelne Dateien auf den Server und teste.
```

---

## WICHTIGE REGELN FÜR CLAUDE:

1. **Sync-Verzeichnis nutzen:**
   - SCHREIBEN: `\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\`
   - NIEMALS: Direkt auf Server oder rsync komplett

2. **Einzelne Dateien kopieren lassen:**
   ```bash
   cp /mnt/greiner-portal-sync/[pfad] /opt/greiner-portal/[pfad]
   ```

3. **Nach Änderungen neustarten:**
   ```bash
   sudo systemctl restart greiner-portal
   ```

4. **Locosoft-Abfragen:**
   ```bash
   PGPASSWORD="loco" psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db -c "..."
   ```

5. **SQLite-Abfragen:**
   ```bash
   sqlite3 /opt/greiner-portal/data/greiner_controlling.db "..."
   ```

6. **Git-Workflow:**
   ```bash
   cd /opt/greiner-portal
   git add [dateien]
   git commit -m "TAG 97: [Beschreibung]"
   git push origin feature/tag82-onwards
   ```

---

## PROJEKT-KONTEXT (falls Claude fragt):

- **Stack:** Flask + SQLite + PostgreSQL (Locosoft) + LDAP
- **ML-Modell:** RandomForest, R²=0.749, MAE=21.6min
- **ML-API:** /api/ml/auftragsdauer, /mechaniker-ranking, /statistik
- **Dashboard:** /werkstatt/intelligence
- **Trainingsdaten:** 143.510 gefilterte Aufträge

---

## OFFENE FRAGEN FÜR TAG 97:

1. TecDoc/TecRMI Zugang vorhanden? → Mit Florian klären
2. HR informiert wegen Samstags-Stunden in Locosoft?
3. Weitere ML-Use-Cases priorisieren?
