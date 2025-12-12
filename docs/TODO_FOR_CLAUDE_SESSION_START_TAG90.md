# TODO FÜR CLAUDE - SESSION START TAG 90

**Erstellt:** 2025-12-04 nach TAG 89  
**Priorität:** Script-Refactoring

---

## 🎯 HAUPTAUFGABE: Script-Umbenennung nach Funktion

### Warum?
- Scripts sind nach Lieferant/Bank benannt, nicht nach Funktion
- Schwer zu erkennen was ein Script macht
- Inkonsistente Namensgebung

### Vorgeschlagene Struktur:

```
scripts/imports/
├── banktransaktionen/
│   ├── import_mt940.py              # MT940 Format (Genobank, Sparkasse, VR)
│   └── import_pdf.py                # PDF Format (HypoVereinsbank)
│
├── einkaufsfinanzierung/
│   ├── import_stellantis.py         # Stellantis Bank (ZIP)
│   ├── import_hyundai.py            # Hyundai Finance
│   └── import_santander.py          # Santander
│
├── teile/
│   ├── import_lieferscheine.py      # Teile-Lieferscheine
│   └── import_bestellungen.py       # ServiceBox Bestellungen
│
└── stammdaten/
    ├── sync_employees.py            # Mitarbeiter aus LDAP
    ├── sync_fahrzeuge.py            # Fahrzeug-Stammdaten
    └── sync_sales.py                # Verkaufsdaten
```

### Mapping Alt → Neu:

| Aktuell | Neu |
|---------|-----|
| `import_stellantis.py` | `einkaufsfinanzierung/import_stellantis.py` |
| `import_hyundai_finance.py` | `einkaufsfinanzierung/import_hyundai.py` |
| `import_santander_bestand.py` | `einkaufsfinanzierung/import_santander.py` |
| `import_mt940.py` | `banktransaktionen/import_mt940.py` |
| `import_all_bank_pdfs.py` | `banktransaktionen/import_pdf.py` |

### Betroffene Dateien:
1. Scripts selbst (umbenennen/verschieben)
2. `scheduler/job_definitions.py` (Pfade anpassen)
3. `scheduler/routes.py` (JOB_FUNCTIONS Dict)
4. Symlinks in `scripts/sync/`
5. Dokumentation (CLAUDE.md)

### Vorgehensweise:
1. Backup der aktuellen Scripts
2. Neue Ordnerstruktur erstellen
3. Scripts kopieren (nicht verschieben!)
4. Job-Definitionen anpassen
5. Testen
6. Alte Scripts entfernen

---

## 📋 WEITERE OFFENE PUNKTE

### ServiceBox Scraper (Chrome-Problem)
```
Fehler: "Unsupported architecture:"
```
- Chrome/ChromeDriver funktioniert nicht auf dem Server
- Möglicherweise ARM vs x86 Problem?
- Prüfen: `uname -m` und Chrome-Version

### fstab Parse-Errors
```bash
cat -n /etc/fstab | tail -5
```
- Zeile 14-15 haben Syntax-Fehler
- Nicht kritisch, aber sollte gefixt werden

---

## 🔧 AKTUELLER STAND (nach TAG 89)

### Job-Scheduler
- ✅ Läuft als separater Service `greiner-scheduler`
- ✅ 30 Jobs aktiv
- ✅ Web-UI unter `/admin/jobs/`
- ✅ Manueller Job-Start funktioniert

### Services
```bash
sudo systemctl status greiner-portal      # Web-App
sudo systemctl status greiner-scheduler   # Job-Scheduler
```

### Wichtige Dateien
- `scheduler_standalone.py` - Scheduler-Prozess
- `config/greiner-scheduler.service` - Systemd-Service
- `scheduler/job_definitions.py` - Job-Definitionen
- `scheduler/routes.py` - Web-UI Routes

---

## 📖 KONTEXT LESEN

1. `CLAUDE.md` - Aktualisiert auf TAG 89
2. `SESSION_WRAP_UP_TAG89.md` - Diese Session

---

*Erstellt am Ende von TAG 89*
