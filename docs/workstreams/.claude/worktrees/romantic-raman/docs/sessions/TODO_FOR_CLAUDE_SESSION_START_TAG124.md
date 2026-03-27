# TODO für TAG 124

**Erstellt:** 17.12.2025
**Vorherige Session:** TAG 123

---

## Offene Punkte

### 1. Git-Commit auf Server
```bash
ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && git add -A && git commit -m 'feat(TAG123): Urlaubsplaner Locosoft-Integration, Scraper-Fix, AD-Sync'"
```

### 2. Mitarbeiter ohne AD prüfen
Folgende Mitarbeiter haben kein AD-Mapping:
- Paula Wieser (Elternzeit)
- Stefanie Bittner
- Rosmarie Erlmeier
- Cornelia Gruber
- Fabian Klammsteiner
- Luca-Emanuel Löw
- Andrea Pfeffer
- Vincent Pursch
- Andreas Karl Suttner
- Daniel Thammer
- Michael Ulrich
- Lena Wagner

**Frage:** Sind diese ausgeschieden/in Elternzeit oder fehlt das AD-Konto?

---

## Abgeschlossen in TAG 123

- [x] Preisradar Scraper Fix (ChromeDriver-Pfad)
- [x] Chef-Übersicht Team-Mitglieder
- [x] Admin-Übersicht AD-Abteilungen
- [x] Urlaubsplaner Locosoft-Abwesenheiten im Kalender
- [x] Mitarbeiter ohne AD-Mapping kennzeichnen
- [x] Zuzana Scheppach: Lager & Teile → T&Z
- [x] Aleyna Irep: AD-Mapping aktualisiert (Namensänderung)

---

## Kontext

### Geänderte Dateien in TAG 123
- `api/vacation_api.py`
- `api/vacation_chef_api.py`
- `api/vacation_admin_api.py`
- `tools/scrapers/schaeferbarthold_scraper_v3.py`
- `tools/scrapers/dello_scraper.py`

### Wichtige Erkenntnisse
- AD `department` = echte Abteilung (Buchhaltung, T&Z)
- Locosoft `grp_code` = Funktionsbeschreibung (LAG, MON)
- `employees.department_name` wird beim Login aus AD synchronisiert
