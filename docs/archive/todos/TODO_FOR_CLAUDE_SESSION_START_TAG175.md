# TODO FÜR CLAUDE - SESSION START TAG 175

**Erstellt:** 2026-01-09 (nach TAG 174)  
**Status:** Bereit für nächste Session

---

## 📋 ÜBERBLICK

TAG 174 hat erfolgreich abgeschlossen:
- ✅ Separater Mount für Hyundai Garantie-Verzeichnis
- ✅ Erweiterte Anhänge-Funktion (alle Dokumente aus GUDAT)
- ✅ Unterschriftsprüfung (Locosoft APP)

---

## 🔍 ZU PRÜFEN BEI SESSION-START

1. **Mount-Status prüfen:**
   ```bash
   mount | grep -E "(hyundai-garantie|loco-bilder)"
   ```

2. **Test Garantieakte-Erstellung:**
   - Prüfe ob Auftrag 220542 noch korrekt funktioniert
   - Teste mit neuem Auftrag

3. **Unterschriftsprüfung:**
   - Prüfe ob bekannte Aufträge korrekt erkannt werden

---

## 🎯 MÖGLICHE NÄCHSTE AUFGABEN

### Option 1: Garantieakte-UI
- Dashboard/UI für Serviceberater zur Erstellung von Garantieakten
- Integration der Unterschriftsprüfung in UI
- Status-Anzeige (Unterschrift vorhanden/fehlt)

### Option 2: Automatisierung
- Automatische Garantieakte-Erstellung bei bestimmten Bedingungen
- Benachrichtigungen bei fehlenden Unterschriften

### Option 3: Weitere Features
- Terminblatt aus GUDAT holen (war geplant, noch nicht implementiert)
- PDF-Optimierung für große Dateien
- Batch-Verarbeitung mehrerer Aufträge

---

## 📝 WICHTIGE HINWEISE

- **Mounts:** Beide Mounts sind in `/etc/fstab` eingetragen und sollten nach Reboot automatisch gemountet werden
- **Credentials:** Verwenden `/root/.smbcredentials` (bereits vorhanden)
- **Test-Aufträge:** 
  - 220542: Hat Unterschrift in GUDAT (A220542.pdf), aber prüfe auch Locosoft BILDER
  - 220266: Keine Unterschrift gefunden (korrekt)
  - 209721: Hat Unterschrift in Locosoft BILDER

---

## 🔗 RELEVANTE DATEIEN

- `api/arbeitskarte_api.py` - Haupt-API für Arbeitskarte & Unterschriftsprüfung
- `api/garantieakte_workflow.py` - Workflow für Garantieakte-Erstellung
- `scripts/mount_hyundai_garantie.sh` - Mount-Script
- `docs/hyundai/MOUNT_HYUNDAI_GARANTIE.md` - Mount-Dokumentation

---

**Bereit für nächste Session! 🚀**
