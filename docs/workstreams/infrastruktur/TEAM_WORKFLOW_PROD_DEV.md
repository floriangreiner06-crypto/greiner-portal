# Team Workflow Prod vs Dev

## Ziel
Gleiche Tools und Regeln im Team, aber klare Trennung zwischen produktiven Hotfixes und Entwicklungsarbeit.

## Rollenmodell
- Florian: produktionsnahe Aenderungen und kleine Hotfixes.
- Vanessa: Entwicklung und Tests auf Dev-Umgebung.

## Branch-Regel
- `main`: produktionsnaher, stabiler Stand.
- `develop`: Integrationsbranch fuer laufende Entwicklung.
- `feature/*`: einzelne Umsetzungen von `develop` aus.

## Laufumgebungen
- Produktion: Portal ueber `http://drive` (Gunicorn/Apache, intern Port 5000).
- Entwicklung/Test: separate Instanz auf Port `5002` (eigener Service, eigene Logs).

## Tagesablauf (kurz)
1. Vanessa arbeitet auf `develop` bzw. `feature/*` und testet auf `:5002`.
2. PR nach `develop` mit Review.
3. Bei Releasefenster: `develop` -> PR nach `main`.
4. Florian deployed `main` nach Produktion.

## Guardrails
- Keine direkten Experimente auf Produktion.
- Keine force-pushes auf `main` oder `develop`.
- Migrationen und riskante Aenderungen zuerst in Dev pruefen.

## Minimaler Freigabe-Check vor Merge nach main
- PR ist mergebar und reviewed.
- Relevante Kernseite/Funktion in Dev geprueft.
- Bei Backend-Aenderung: geplanter Restart und kurzer Smoke-Check dokumentiert.
