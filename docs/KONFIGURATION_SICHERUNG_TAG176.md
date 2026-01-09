# Konfigurations-Sicherung TAG 176

**Datum:** 2026-01-09  
**Grund:** Cursor-Installation abgestürzt - Konfigurationen sichern

---

## ✅ GESICHERTE DATEIEN

### 1. Claude Commands (`.claude/commands/`)
Alle 10 Command-Definitionen:
- `session-end.md` - **ERWEITERT** (Qualitätscheck)
- `session-start.md` - **ERWEITERT** (Standards)
- `commit.md`
- `db.md`
- `deploy.md`
- `feature.md`
- `fix.md`
- `logs.md`
- `status.md`
- `test.md`

**Pfad:** `/mnt/greiner-portal-sync/.claude/commands/`

### 2. Konfigurationsdateien
- `CLAUDE.md` - **AKTUALISIERT** (Qualitätscheck erwähnt)
- `.cursorrules` - Projekt-spezifische Regeln
- `.claude/COMMANDS.md` - Command-Übersicht

**Pfad:** `/mnt/greiner-portal-sync/`

### 3. Template
- `docs/QUALITAETSCHECK_TEMPLATE.md` - **NEU** (Qualitätscheck-Template)

**Pfad:** `/mnt/greiner-portal-sync/docs/`

---

## 📍 SYNC-VERZEICHNIS

**Windows:** `\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\`  
**Server:** `/mnt/greiner-portal-sync/`

---

## 🔄 WIEDERHERSTELLUNG

Falls Cursor erneut abstürzt, können die Dateien wiederhergestellt werden:

```bash
# Commands wiederherstellen
cp -r /mnt/greiner-portal-sync/.claude/commands/* /opt/greiner-portal/.claude/commands/

# Konfiguration wiederherstellen
cp /mnt/greiner-portal-sync/CLAUDE.md /opt/greiner-portal/
cp /mnt/greiner-portal-sync/.cursorrules /opt/greiner-portal/

# Template wiederherstellen
cp /mnt/greiner-portal-sync/docs/QUALITAETSCHECK_TEMPLATE.md /opt/greiner-portal/docs/
```

---

## 📝 HINWEISE

1. **Automatische Sync:** Dateien im Sync-Verzeichnis werden automatisch auf Windows synchronisiert
2. **Backup:** Alle Konfigurationen sind jetzt im Windows-Sync-Verzeichnis gesichert
3. **Versionierung:** Änderungen sollten auch in Git committet werden

---

**Status:** ✅ Alle Konfigurationsdateien gesichert!
