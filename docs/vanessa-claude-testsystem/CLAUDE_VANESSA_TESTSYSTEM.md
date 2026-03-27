# CLAUDE.md (Vanessa - Testsystem / Develop)

## Ziel

- Redesign sicher im Testsystem entwickeln
- Produktion nicht beruehren

## Verbindliche Regeln

1. Nur in `/data/greiner-test` arbeiten.
2. Browser nur ueber `http://drive/test`.
3. Keine Aenderungen in `/opt/greiner-portal`.
4. Keine produktiven Restarts, Migrationen oder Deploys.
5. Fokus auf `templates/`, `static/css/`, `static/js/`.

## Arbeitsablauf

1. Aufgabe klar formulieren
2. Kleine UI-Aenderung umsetzen
3. Sofort im Test pruefen
4. Kurz dokumentieren (was, wo, warum)

## Stop-Signale

- URL ohne `/test`
- TESTSYSTEM-Badge fehlt
- Unsicherheit bzgl. Produktion
