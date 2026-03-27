# Quickstart (10 Minuten): Vanessa + Claude Code Desktop

Ziel: In 10 Minuten startklar im Testsystem, mit allen wichtigen Projektinfos im Claude-Setup.

---

## A) 10-Minuten-Setup

### 1) SSH kurz testen (Windows PowerShell)

```powershell
ssh vanessa-dev@10.80.80.20
```

Wenn das klappt: wieder beenden mit `exit`.

### 2) Claude Code Desktop starten

- Neues Remote/SSH-Projekt anlegen
- Host: `10.80.80.20`
- User: `vanessa-dev`
- Working Directory: `/data/greiner-test`

### 3) Browser fuer Test oeffnen

- `http://drive/test`
- TESTSYSTEM-Badge muss sichtbar sein

---

## B) Pflichtinfos ins Projekt bringen (wichtig)

Damit Claude im Projekt korrekt arbeitet, sollen diese Infos **immer** im Projektkontext sein:

1. `CLAUDE_VANESSA_TESTSYSTEM.md`
2. `CHECKLISTE_VANESSA_TESTSYSTEM_1SEITE.md`
3. `ANLEITUNG_VANESSA_CLAUDE_DESKTOP_SSH_TESTSYSTEM.md`
4. (optional) `CLAUDE.md` fuer Gesamtarchitektur

Empfohlener Ort im Projekt:
- direkt im Workspace/Sync ablegen (bereits erledigt)
- zusaetzlich als Projekt-Notiz/Instruktion in Claude Desktop hinterlegen

---

## C) Textbaustein fuer Projekt-Instruktion (copy/paste)

Diesen Block als feste Projektinstruktion in Claude Code Desktop einfuegen:

```text
Du arbeitest fuer DRIVE ausschliesslich im Testsystem.

Verbindliche Regeln:
1) Nur im Workspace /data/greiner-test arbeiten.
2) Browser-Tests nur ueber http://drive/test.
3) Wenn TESTSYSTEM-Badge fehlt: sofort stoppen und URL pruefen.
4) Keine Aenderungen an /opt/greiner-portal (Produktion).
5) Keine produktiven Restarts, Migrationen oder Deploys.
6) Fokus auf templates/, static/css/, static/js/ fuer Redesign.
7) In kleinen Schritten arbeiten: aendern -> testen -> kurz dokumentieren.
8) Bei Unsicherheit erst Rueckfrage stellen.
```

---

## D) Erster Prompt fuer Vanessa (copy/paste)

```text
Lies zuerst diese Dateien und arbeite strikt danach:
1) /mnt/greiner-portal-sync/CLAUDE_VANESSA_TESTSYSTEM.md
2) /mnt/greiner-portal-sync/docs/CHECKLISTE_VANESSA_TESTSYSTEM_1SEITE.md

Ziel fuer diese Session:
- nur UI-Anpassungen im Testsystem
- keine Produktivaenderungen

Bitte starte mit einer kurzen Zusammenfassung der Regeln und nenne dann den ersten kleinen Arbeitsschritt.
```

---

## E) Mini-Qualitaetscheck vor jedem "fertig"

- [ ] URL ist `http://drive/test`
- [ ] TESTSYSTEM-Badge sichtbar
- [ ] keine JS-Fehler in Browser-Konsole
- [ ] keine Aenderung an Produktivpfaden
- [ ] kurze Notiz: was wurde geaendert, welche Dateien

---

## F) Wenn etwas komisch wirkt

Sofort stoppen, wenn:
- URL ploetzlich `http://drive/...` ohne `/test` ist
- Badge fehlt
- unklar ist, ob Produktion betroffen ist

Dann Florian kurz informieren und erst nach Klaerung weiterarbeiten.

