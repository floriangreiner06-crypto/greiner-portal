# TODO für nächste Session — 2026-03-27

## Offene Aufgaben

### Priorität 1: Git aufräumen
- [ ] feature/tag112-onwards in main mergen (3 Commits)
- [ ] Tote Branches löschen: cleanup/drive-sane, feature/sane-drive-* (6), backup/main-sane-drive-*, feature/tag82-onwards, feature/bankenspiegel-komplett, feature/controlling-*, feature/november-import-*, feature/verkauf-dashboard, show-current
- [ ] Stash droppen wenn alles stabil (stash@{0} und stash@{1})

### Priorität 2: Develop-Workflow validieren
- [ ] Vanessa testen lassen auf drive:5002
- [ ] Ersten Develop→Produktion Merge durchspielen
- [ ] develop-Branch auf GitHub pushen

### Priorität 3: Offene Feature-Arbeit
- [ ] Urlaubsplaner: Resturlaub-Formel zentralisieren (_compute_rest_display) — optional
- [ ] Verkauf: Auftragseingang Perioden-Buttons vereinheitlichen (Stash hat "Dieses Jahr/GJ", Auslieferungen hat "Kalenderjahr/Geschäftsjahr")

## Hinweise für nächste Session
- sudo OHNE Passwort: `sudo -n /usr/bin/systemctl restart greiner-portal`
- NIEMALS Passwort im Chat verwenden
- Produktion: /opt/greiner-portal/ (feature/tag112-onwards)
- Develop: /opt/greiner-test/ (develop)
- Session-Doku jetzt mit Datum statt TAG-Nummer
