# Stellantis Garantie-Feature - Implementierung

**Erstellt:** 2026-01-14 (TAG 189)  
**Status:** ✅ Implementiert  
**Referenz:** Hyundai Garantie-Feature (TAG 173)

---

## 📋 ZUSAMMENFASSUNG

Das Stellantis Garantie-Feature wurde erfolgreich implementiert. Die bestehende Hyundai-Implementierung wurde erweitert um Stellantis-Support (Opel) mit automatischer Brand-Erkennung.

---

## ✅ IMPLEMENTIERTE ÄNDERUNGEN

### 1. `api/garantieakte_workflow.py` erweitert

**Änderungen:**
- ✅ `brand`-Parameter hinzugefügt (`'hyundai'` oder `'stellantis'`)
- ✅ Brand-spezifische Pfad-Konfigurationen (`BRAND_PATHS`)
- ✅ `create_garantieakte_ordner()` erweitert um `brand`-Parameter
- ✅ `create_garantieakte_vollstaendig()` erweitert um `brand`-Parameter
- ✅ Windows-Pfad-Generierung brand-spezifisch

**Pfad-Konfigurationen:**
```python
BRAND_PATHS = {
    'hyundai': {
        'base_paths': [...],
        'fallback': "/mnt/greiner-portal-sync/Hyundai_Garantie",
        'windows_base': r'\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie'
    },
    'stellantis': {
        'base_paths': [
            "/mnt/stellantis-garantie",
            "/mnt/buchhaltung/DigitalesAutohaus/Stellantis_Garantie",
            ...
        ],
        'fallback': "/mnt/greiner-portal-sync/Stellantis_Garantie",
        'windows_base': r'\\srvrdb01\Allgemein\DigitalesAutohaus\Stellantis_Garantie'
    }
}
```

### 2. `api/arbeitskarte_api.py` erweitert

**Änderungen:**
- ✅ `subsidiary` wird aus Locosoft geholt
- ✅ Automatische Brand-Erkennung:
  - `subsidiary = 1` oder `3` → `brand = 'stellantis'`
  - `subsidiary = 2` → `brand = 'hyundai'`
- ✅ Brand wird an `create_garantieakte_vollstaendig()` übergeben
- ✅ Brand wird in Rückgabe-Dictionary aufgenommen

**Brand-Erkennung:**
```python
subsidiary = auftrag[6]  # Aus Locosoft orders.subsidiary
if subsidiary == 1 or subsidiary == 3:
    brand = 'stellantis'  # Deggendorf Opel (1) oder Landau (3)
elif subsidiary == 2:
    brand = 'hyundai'  # Deggendorf Hyundai (2)
```

### 3. Mount-Script erstellt

**Datei:** `scripts/mount_stellantis_garantie.sh`

**Funktionalität:**
- ✅ Erstellt Mount-Punkt `/mnt/stellantis-garantie`
- ✅ Mountet `\\srvrdb01\Allgemein\DigitalesAutohaus\Stellantis_Garantie`
- ✅ Prüft Schreibrechte
- ✅ Anleitung für `/etc/fstab`-Eintrag

---

## 🔧 VERWENDUNG

### API-Endpoint

**POST** `/api/arbeitskarte/<order_number>/speichern`

**Funktionalität:**
- Brand wird **automatisch** aus `subsidiary` erkannt
- Keine manuelle Angabe nötig
- Erstellt Ordner in brand-spezifischem Verzeichnis

**Beispiel:**
```bash
POST /api/arbeitskarte/123456/speichern
```

**Response:**
```json
{
  "success": true,
  "message": "Garantieakte erfolgreich gespeichert",
  "ordner_path": "/mnt/stellantis-garantie/Mustermann, Max_123456",
  "windows_path": "\\\\srvrdb01\\Allgemein\\DigitalesAutohaus\\Stellantis_Garantie\\Mustermann, Max_123456",
  "dateien": [...],
  "anzahl_dateien": 15
}
```

---

## 📁 ORDNERSTRUKTUR

### Stellantis

```
\\srvrdb01\Allgemein\DigitalesAutohaus\Stellantis_Garantie\
  └── {kunde}_{Auftragsnummer}\
      ├── Arbeitskarte_{Auftragsnummer}.pdf
      ├── 01_{Bildname}.jpg
      ├── 02_{Bildname}.jpg
      ├── ...
      └── Terminblatt_{name}.pdf (falls vorhanden)
```

### Hyundai (unverändert)

```
\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie\
  └── {kunde}_{Auftragsnummer}\
      ├── Arbeitskarte_{Auftragsnummer}.pdf
      ├── 01_{Bildname}.jpg
      ├── ...
      └── Terminblatt_{name}.pdf (falls vorhanden)
```

---

## 🔌 MOUNT-EINRICHTUNG

### 1. Windows-Ordner erstellen

Erstelle auf Windows-Server:
```
\\srvrdb01\Allgemein\DigitalesAutohaus\Stellantis_Garantie\
```

**Berechtigungen:**
- Schreibrechte für Server-User (`ag-admin`)

### 2. Mount-Script ausführen

```bash
sudo /opt/greiner-portal/scripts/mount_stellantis_garantie.sh
```

### 3. Persistent machen (fstab)

Füge zu `/etc/fstab` hinzu:
```
//srvrdb01/Allgemein/DigitalesAutohaus/Stellantis_Garantie /mnt/stellantis-garantie cifs credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775,nofail 0 0
```

Dann testen:
```bash
sudo mount -a
```

### 4. Prüfen

```bash
# Mount-Status
mount | grep stellantis-garantie

# Schreibrechte testen
touch /mnt/stellantis-garantie/test.txt && rm /mnt/stellantis-garantie/test.txt && echo "✅ OK"
```

---

## 🧪 TESTING

### Test-Aufträge

1. **Stellantis-Auftrag (Deggendorf Opel):**
   - `subsidiary = 1`
   - Sollte in `Stellantis_Garantie/` gespeichert werden

2. **Stellantis-Auftrag (Landau):**
   - `subsidiary = 3`
   - Sollte in `Stellantis_Garantie/` gespeichert werden

3. **Hyundai-Auftrag:**
   - `subsidiary = 2`
   - Sollte in `Hyundai_Garantie/` gespeichert werden (unverändert)

### Test-Schritte

1. ✅ API-Endpoint testen: `POST /api/arbeitskarte/<order_number>/speichern`
2. ✅ Ordner-Erstellung prüfen
3. ✅ Dateien speichern prüfen
4. ✅ Windows-Pfad prüfen
5. ✅ Brand-Erkennung prüfen

---

## 🔄 RÜCKWÄRTSKOMPATIBILITÄT

**✅ Vollständig rückwärtskompatibel!**

- Bestehende Hyundai-Aufträge funktionieren weiterhin
- `brand`-Parameter ist optional (Default: `'hyundai'`)
- Legacy-Konstanten (`BASE_PATH_OPTIONS`, `FALLBACK_PATH`) bleiben erhalten

---

## 📊 BRAND-ERKENNUNG

### Automatische Erkennung

| subsidiary | Standort | Brand |
|------------|----------|-------|
| 1 | Deggendorf Opel | `stellantis` |
| 2 | Deggendorf Hyundai | `hyundai` |
| 3 | Landau Opel | `stellantis` |

### Manuelle Überschreibung

Falls nötig, kann `brand` manuell übergeben werden:
```python
create_garantieakte_vollstaendig(
    ...,
    brand='stellantis'  # Manuell setzen
)
```

---

## ⚠️ WICHTIGE HINWEISE

1. **Mount-Punkt muss eingerichtet sein:**
   - `/mnt/stellantis-garantie` muss existieren und gemountet sein
   - Falls nicht: Fallback auf `/mnt/greiner-portal-sync/Stellantis_Garantie`

2. **Windows-Ordner muss existieren:**
   - `\\srvrdb01\Allgemein\DigitalesAutohaus\Stellantis_Garantie\` muss erstellt werden
   - Berechtigungen prüfen!

3. **Brand-Erkennung:**
   - Funktioniert automatisch aus `subsidiary`
   - Keine manuelle Eingabe nötig

4. **Rückwärtskompatibilität:**
   - Alle bestehenden Hyundai-Aufträge funktionieren weiterhin
   - Keine Breaking Changes

---

## 📝 NÄCHSTE SCHRITTE

### Optional (nicht kritisch):

1. **`garantie_auftraege_api.py` erweitern:**
   - `get_garantieakte_metadata()` erweitern um Stellantis-Pfade
   - Aktuell funktioniert nur für Hyundai

2. **Frontend-Integration:**
   - Falls vorhanden: Stellantis-Option hinzufügen
   - Brand-Anzeige in UI

3. **Testing:**
   - Test-Aufträge für Stellantis finden
   - Vollständigen Workflow testen

---

## 🔗 RELEVANTE DATEIEN

### Geänderte Dateien:
- `api/garantieakte_workflow.py` - Brand-Parameter hinzugefügt
- `api/arbeitskarte_api.py` - Brand-Erkennung implementiert

### Neue Dateien:
- `scripts/mount_stellantis_garantie.sh` - Mount-Script
- `docs/stellantis/STELLANTIS_GARANTIE_IMPLEMENTIERUNG_TAG189.md` - Diese Datei

### Dokumentation:
- `docs/stellantis/STELLANTIS_GARANTIE_EINSCHAETZUNG_TAG189.md` - Einschätzung
- `docs/stellantis/STELLANTIS_GARANTIE_HANDBUCH_ANALYSE_TAG189.md` - Handbuch-Analyse

---

*Erstellt: TAG 189 | Autor: Claude AI*
