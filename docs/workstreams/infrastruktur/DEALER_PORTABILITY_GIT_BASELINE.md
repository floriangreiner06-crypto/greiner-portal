# Dealer Portability Git Baseline

## Zielbild
DRIVE soll fuer weitere Haendler mit aehnlicher Infrastruktur reproduzierbar ausrollbar sein, ohne projektkritische Logik neu zu bauen.

## Baseline-Prinzipien
- Ein klarer `main`-Strang als produktionsnaher Referenzstand.
- Aenderungen in reviewbaren, thematischen PRs.
- Keine geheimen lokalen Abhaengigkeiten fuer Build und Betrieb.
- Dokumentierte Rollout- und Rückroll-Schritte.

## Empfohlener Branch-Flow
- `main`: stabil, deploybar.
- `feature/*`: thematische Umsetzung.
- Merge nur nach Review, Bugfixes und sauberem PR-Status.

## Portability-Checkliste
- Konfigurationen ueber Umgebungswerte und dokumentierte Credentials.
- Migrationen idempotent und ohne harte IDs/Passwoerter.
- API-Endpunkte fuer Frontend-Aufrufe liefern konsequent JSON.
- Teamweite Dev-Baseline ueber `.vscode/*` und Workstream-Doku.

## Uebergabe fuer neuen Haendler
- Infrastrukturparameter sammeln (DB, LDAP/AD, Mail, externe APIs).
- Mapping-Dokumente und Rollenmodell bereitstellen.
- Staged Rollout: Testsystem -> Pilot -> Produktion.
