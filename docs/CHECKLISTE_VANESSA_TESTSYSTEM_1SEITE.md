# Vanessa Checkliste (1 Seite) - TESTSYSTEM

Ziel: Sicher im Test arbeiten, Produktion unberuehrt lassen.

## Start (vor jeder Session)

- [ ] SSH-Verbindung als `vanessa-dev` aktiv
- [ ] Arbeitsverzeichnis ist `/data/greiner-test`
- [ ] Browser-URL ist `http://drive/test`
- [ ] TESTSYSTEM-Badge ist sichtbar

## Arbeitsregeln

- [ ] Nur in Test arbeiten (nie auf `http://drive` ohne `/test`)
- [ ] Nur UI-Dateien anfassen: `templates/`, `static/css/`, `static/js/`
- [ ] Keine Aenderungen in `/opt/greiner-portal`
- [ ] Keine produktiven Restarts/Migrationen
- [ ] In kleinen Schritten arbeiten (aendern -> testen -> notieren)

## Schnelltest nach Aenderung

- [ ] Seite laedt ohne 500/504
- [ ] Keine JS-Fehler in Browser-Konsole
- [ ] Layout/Abstaende stimmen auf Desktop
- [ ] Rollen/Rechte-Sichtbarkeit bleibt korrekt
- [ ] Gewuenschter Mockup-Stand erreicht

## Uebergabe an Florian

- [ ] Was wurde geaendert? (1-3 Stichpunkte)
- [ ] Welche Dateien? (Pfade nennen)
- [ ] Wie getestet? (kurz)
- [ ] Offene Punkte/Fragen

## Stop-Signale (sofort pausieren)

- [ ] URL ohne `/test`
- [ ] TESTSYSTEM-Badge fehlt
- [ ] Unsicherheit, ob Produktion betroffen sein koennte
- [ ] Unerwartete Fehler bei Login/Rechten/Navigation

## Tool-Empfehlung fuer Vanessa

- Haupttool: **Claude Code Desktop** (mit SSH auf Testsystem)
- Optional: Claude Desktop/claude.ai fuer Ideen/Mockup-Texte
- UI-Feinschliff + Dateiedits: Cursor ist zusaetzlich hilfreich

