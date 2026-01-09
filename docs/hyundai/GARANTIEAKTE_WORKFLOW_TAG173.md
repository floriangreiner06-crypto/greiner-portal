# Garantieakte Workflow - Vollständige Implementierung

**Erstellt:** 2026-01-09 (TAG 173)  
**Status:** ✅ Implementiert und getestet

---

## 📋 WORKFLOW

### Ordnerstruktur
```
\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie\
  └── {kunde}_{Auftragsnummer}\
      ├── Arbeitskarte_{Auftragsnummer}.pdf
      ├── 01_{Bildname}.jpg
      ├── 02_{Bildname}.jpg
      ├── ...
      └── Terminblatt_{name}.pdf (falls vorhanden)
```

### Beispiel: Auftrag 220542
```
Kopra-Schäfer, Dr. Monika_220542\
  ├── Arbeitskarte_220542.pdf (7.7 KB)
  ├── 01_IMG_5510.jpg (538 KB)
  ├── 02_IMG_5513.jpg (837 KB)
  ├── 03_IMG_5511.jpg (960 KB)
  ├── 04_IMG_5512.jpg (1007 KB)
  ├── 05_IMG_5508.jpg (959 KB)
  ├── 06_IMG_5515.jpg (1.1 MB)
  ├── 07_IMG_5509.jpg (978 KB)
  ├── 08_IMG_5516.jpg (1.3 MB)
  ├── 09_IMG_5514.jpg (1.2 MB)
  ├── 10_IMG_5507.jpg (1.3 MB)
  ├── 11_Image_20260107_132327.png (189 KB)
  ├── 12_Hyundai Antwort Schäfer.png (31 KB)
  └── 13_Altteil.jpg (858 KB)
```

---

## 🚀 API-ENDPOINT

### POST `/api/arbeitskarte/<order_number>/speichern`

**Funktion:**
- Erstellt Ordner `{kunde}_{Auftragsnummer}`
- Speichert Arbeitskarte-PDF (ohne Bilder)
- Lädt und speichert alle Bilder einzeln
- Speichert Terminblatt (falls vorhanden)

**Response:**
```json
{
  "success": true,
  "message": "Garantieakte erfolgreich gespeichert",
  "ordner_path": "/mnt/.../Kopra-Schäfer, Dr. Monika_220542",
  "windows_path": "\\\\srvrdb01\\Allgemein\\DigitalesAutohaus\\Hyundai_Garantie\\...",
  "dateien": [
    {
      "typ": "Arbeitskarte",
      "pfad": "...",
      "groesse_kb": 7.7
    },
    {
      "typ": "Bild",
      "pfad": "...",
      "groesse_kb": 538.0,
      "name": "IMG_5510.jpeg"
    }
  ],
  "anzahl_dateien": 14
}
```

---

## 📁 SPEICHERORTE

### Primär (Ziel)
- **Server:** `/mnt/buchhaltung/DigitalesAutohaus/Hyundai_Garantie/`
- **Windows:** `\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie\`

### Fallback (aktuell verwendet)
- **Server:** `/mnt/greiner-portal-sync/Hyundai_Garantie/`
- **Windows:** `\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\Hyundai_Garantie\`

**Hinweis:** Der primäre Pfad benötigt Schreibrechte. Aktuell wird der Fallback-Pfad verwendet, der bereits funktioniert.

---

## ✅ GETESTET

**Auftrag 220542:**
- ✅ Ordner erstellt: `Kopra-Schäfer, Dr. Monika_220542`
- ✅ 14 Dateien gespeichert:
  - 1 Arbeitskarte-PDF
  - 13 Bilder (einzeln, nummeriert)
- ✅ Gesamtgröße: ~11 MB
- ✅ Alle Dateien einzeln (nicht im PDF integriert)

---

## 🔧 NÄCHSTE SCHRITTE

1. **Berechtigungen prüfen:**
   - Ordner `/mnt/buchhaltung/DigitalesAutohaus/Hyundai_Garantie` gehört `root`
   - Benötigt Schreibrechte für `ag-admin` oder Flask-User

2. **Mount prüfen:**
   - Falls `\\srvrdb01\Allgemein\DigitalesAutohaus` nicht gemountet ist, muss es gemountet werden

3. **Terminblatt-Download:**
   - Aktuell wird Terminblatt-Daten geholt, aber PDF-Download noch nicht implementiert
   - Ähnlich wie Bilder: `download_image()` für PDFs erweitern

---

## 💡 HINWEISE

- **Bilder werden NICHT im PDF integriert** - sie werden einzeln gespeichert
- **Dateinamen werden bereinigt** - ungültige Windows-Zeichen werden ersetzt
- **Bilder werden nummeriert** - für bessere Sortierung (01_, 02_, ...)
- **Original-Dateinamen werden beibehalten** - soweit möglich
