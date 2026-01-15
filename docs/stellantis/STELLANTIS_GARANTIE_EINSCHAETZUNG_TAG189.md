# Stellantis Garantie-Feature - Einschätzung und Implementierungsplan

**Erstellt:** 2026-01-14 (TAG 189)  
**Status:** 📋 Einschätzung  
**Referenz:** Hyundai Garantie-Feature (TAG 173)

---

## 📋 ZUSAMMENFASSUNG

**Frage:** Wie können wir für Stellantis (Opel) Garantieaufträge automatisiert einen Dokumentationsordner erstellen, ähnlich wie bei Hyundai?

**Antwort:** ✅ **JA, sehr gut möglich!** Die Hyundai-Implementierung kann als Basis verwendet werden. Es gibt einige Unterschiede, die berücksichtigt werden müssen.

---

## 🔍 AKTUELLER STAND: HYUNDAI GARANTIE-FEATURE

### Implementierte Funktionalität (TAG 173)

**API-Endpoint:**
- `POST /api/arbeitskarte/<order_number>/speichern`

**Funktionalität:**
1. ✅ Erstellt Ordner: `{kunde}_{Auftragsnummer}`
2. ✅ Speichert Arbeitskarte-PDF (ohne Bilder)
3. ✅ Lädt und speichert alle Bilder einzeln (nummeriert: `01_`, `02_`, ...)
4. ✅ Speichert Terminblatt (falls vorhanden)
5. ✅ Speichert Metadaten (Ersteller, Datum)

**Ordnerstruktur:**
```
\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie\
  └── {kunde}_{Auftragsnummer}\
      ├── Arbeitskarte_{Auftragsnummer}.pdf
      ├── 01_{Bildname}.jpg
      ├── 02_{Bildname}.jpg
      ├── ...
      └── Terminblatt_{name}.pdf (falls vorhanden)
```

**Speicherort:**
- **Server:** `/mnt/hyundai-garantie/` (Mount: `\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie`)
- **Fallback:** `/mnt/greiner-portal-sync/Hyundai_Garantie/`

**Garantie-Erkennung:**
- `charge_type = 60` ODER
- `labour_type IN ('G', 'GS')` ODER
- `invoice_type = 6`

**Standort-Filter:**
- Hyundai = `subsidiary = 2` (Betrieb 2)

---

## 🆚 VERGLEICH: HYUNDAI vs. STELLANTIS

### Gemeinsamkeiten ✅

| Aspekt | Hyundai | Stellantis | Status |
|--------|---------|------------|--------|
| **Garantie-Erkennung** | `charge_type=60` ODER `labour_type IN ('G','GS')` ODER `invoice_type=6` | **GLEICH** | ✅ Identisch |
| **Datenquelle** | Locosoft (orders, labours, invoices) | **GLEICH** | ✅ Identisch |
| **GUDAT-Integration** | Bilder/Anhänge aus GUDAT | **GLEICH** | ✅ Identisch |
| **Arbeitskarte-PDF** | Generierung aus Locosoft-Daten | **GLEICH** | ✅ Identisch |
| **Ordnerstruktur** | `{kunde}_{Auftragsnummer}` | **GLEICH** | ✅ Identisch |
| **Dateien** | Arbeitskarte-PDF, Bilder, Terminblatt | **GLEICH** | ✅ Identisch |

### Unterschiede ⚠️

| Aspekt | Hyundai | Stellantis | Anpassung nötig? |
|--------|---------|------------|------------------|
| **Standort** | `subsidiary = 2` (Betrieb 2) | `subsidiary = 1` (Betrieb 1 + 3) | ✅ **JA** - Filter anpassen |
| **Speicherort** | `Hyundai_Garantie/` | `Stellantis_Garantie/` | ✅ **JA** - Neuer Ordner |
| **Mount-Punkt** | `/mnt/hyundai-garantie` | `/mnt/stellantis-garantie` (neu) | ✅ **JA** - Neuer Mount |
| **Windows-Pfad** | `\\srvrdb01\...\Hyundai_Garantie\` | `\\srvrdb01\...\Stellantis_Garantie\` | ✅ **JA** - Neuer Pfad |
| **Handbuch-Anforderungen** | Hyundai Garantie-Richtlinie | Stellantis WAM V2 NSC | ⚠️ **PRÜFEN** - Mögliche Unterschiede |

---

## 📊 STELLANTIS STANDORT-MAPPING

### Standorte

| Standort-ID | Name | subsidiary | Betrieb |
|-------------|------|------------|---------|
| **1** | Deggendorf Opel | 1 | 1 |
| **3** | Landau Opel | 1 | 3 |

**Wichtig:**
- Beide Standorte gehören zu **Stellantis** (`subsidiary = 1`)
- Filter muss beide Standorte berücksichtigen: `subsidiary = 1 AND (subsidiary_location = 1 OR subsidiary_location = 3)`
- Oder einfacher: `subsidiary = 1` (beide Standorte)

---

## 🎯 IMPLEMENTIERUNGSSTRATEGIE

### Option 1: Erweiterte Hyundai-Funktion (EMPFOHLEN) ✅

**Vorteile:**
- ✅ Wiederverwendung der bestehenden Logik
- ✅ Einheitliche Code-Basis
- ✅ Einfache Wartung
- ✅ SSOT-Prinzip (Single Source of Truth)

**Ansatz:**
1. `garantieakte_workflow.py` erweitern um `brand`-Parameter
2. Dynamische Pfad-Auswahl basierend auf `brand` ('hyundai' oder 'stellantis')
3. API-Endpoint erweitern: `POST /api/arbeitskarte/<order_number>/speichern?brand=stellantis`

**Code-Struktur:**
```python
def create_garantieakte_ordner(
    kunde_name: str,
    auftragsnummer: int,
    brand: str = 'hyundai',  # 'hyundai' oder 'stellantis'
    base_path: str = None
) -> str:
    # Brand-spezifische Pfade
    if brand == 'stellantis':
        BASE_PATH_OPTIONS = [
            "/mnt/stellantis-garantie",
            "/mnt/buchhaltung/DigitalesAutohaus/Stellantis_Garantie",
            # ... Fallbacks
        ]
    else:  # hyundai
        BASE_PATH_OPTIONS = [
            "/mnt/hyundai-garantie",
            # ... bestehende Pfade
        ]
```

### Option 2: Separate Stellantis-Funktion

**Vorteile:**
- ✅ Klare Trennung
- ✅ Unabhängige Entwicklung

**Nachteile:**
- ❌ Code-Duplikation
- ❌ Wartungsaufwand
- ❌ Verletzung SSOT-Prinzip

**Bewertung:** ❌ **NICHT EMPFOHLEN** (Code-Duplikation)

---

## 🔧 IMPLEMENTIERUNGSSCHRITTE

### Phase 1: Vorbereitung

1. **Stellantis-Handbuch analysieren** 📄
   - [ ] PDF lesen: `docs/Stellantis/de_DE-AT_Stellantis_WAM_V2_NSC.pdf`
   - [ ] Anforderungen identifizieren
   - [ ] Unterschiede zu Hyundai dokumentieren

2. **Windows-Ordner erstellen** 📁
   - [ ] `\\srvrdb01\Allgemein\DigitalesAutohaus\Stellantis_Garantie\` erstellen
   - [ ] Berechtigungen prüfen (Schreibrechte für Server)

3. **Mount-Punkt einrichten** 🔌
   - [ ] `/mnt/stellantis-garantie` erstellen
   - [ ] Mount-Script: `scripts/mount_stellantis_garantie.sh`
   - [ ] `/etc/fstab` Eintrag hinzufügen
   - [ ] Testen: Schreibrechte prüfen

### Phase 2: Code-Anpassungen

1. **`api/garantieakte_workflow.py` erweitern** 🔧
   - [ ] `brand`-Parameter hinzufügen
   - [ ] Brand-spezifische Pfade konfigurieren
   - [ ] Windows-Pfad-Generierung anpassen

2. **`api/arbeitskarte_api.py` erweitern** 🔧
   - [ ] API-Endpoint: `brand`-Parameter unterstützen
   - [ ] Brand-Erkennung: Automatisch aus `subsidiary` ableiten
   - [ ] Oder: Query-Parameter `?brand=stellantis`

3. **Garantie-Erkennung erweitern** 🔍
   - [ ] Filter für Stellantis: `subsidiary = 1`
   - [ ] Optional: Standort-Filter (Deggendorf oder Landau)

### Phase 3: Testing

1. **Test-Aufträge** 🧪
   - [ ] Stellantis Garantieauftrag finden (Deggendorf)
   - [ ] Stellantis Garantieauftrag finden (Landau)
   - [ ] Ordner-Erstellung testen
   - [ ] Dateien speichern testen
   - [ ] Windows-Pfad prüfen

2. **Integrationstest** 🔗
   - [ ] API-Endpoint testen
   - [ ] Frontend-Integration (falls vorhanden)
   - [ ] Fehlerbehandlung testen

---

## 📁 DATEI-STRUKTUR (Vorschlag)

### Neue/Geänderte Dateien

```
api/
  ├── garantieakte_workflow.py          # ERWEITERN: brand-Parameter
  ├── arbeitskarte_api.py               # ERWEITERN: brand-Erkennung
  └── garantie_auftraege_api.py        # ERWEITERN: Stellantis-Filter

scripts/
  └── mount_stellantis_garantie.sh      # NEU: Mount-Script

docs/
  └── stellantis/
      ├── STELLANTIS_GARANTIE_EINSCHAETZUNG_TAG189.md  # Diese Datei
      ├── STELLANTIS_GARANTIE_HANDBUCH_ANALYSE.md      # Handbuch-Analyse
      └── MOUNT_STELLANTIS_GARANTIE.md                 # Mount-Doku
```

---

## ⚠️ OFFENE FRAGEN

### 1. Stellantis-Handbuch-Anforderungen

**Frage:** Gibt es spezielle Anforderungen im Stellantis-Handbuch, die sich von Hyundai unterscheiden?

**Aktion:** 
- [ ] PDF analysieren
- [ ] Anforderungen dokumentieren
- [ ] Unterschiede identifizieren

### 2. Automatische Brand-Erkennung

**Frage:** Soll die Brand-Erkennung automatisch erfolgen (aus `subsidiary`) oder manuell (Query-Parameter)?

**Empfehlung:** ✅ **Automatisch** aus `subsidiary` ableiten
- `subsidiary = 1` → Stellantis
- `subsidiary = 2` → Hyundai

### 3. Standort-Filter

**Frage:** Sollen Stellantis-Garantieaufträge nach Standort gefiltert werden (Deggendorf vs. Landau)?

**Empfehlung:** ✅ **JA, optional**
- Standard: Beide Standorte (Deggendorf + Landau)
- Optional: Filter nach Standort

### 4. Frontend-Integration

**Frage:** Gibt es bereits ein Frontend für die Garantieakte-Erstellung?

**Aktion:**
- [ ] Prüfen ob Frontend existiert
- [ ] Falls ja: Stellantis-Option hinzufügen
- [ ] Falls nein: Optional für später

---

## 📊 AUFWAND-SCHÄTZUNG

| Phase | Aufgabe | Aufwand | Priorität |
|-------|---------|---------|-----------|
| **1** | Handbuch analysieren | 1-2h | Hoch |
| **1** | Windows-Ordner + Mount | 0.5h | Hoch |
| **2** | Code-Anpassungen | 2-3h | Hoch |
| **3** | Testing | 1-2h | Hoch |
| **Gesamt** | | **4.5-7.5h** | |

---

## ✅ NÄCHSTE SCHRITTE

1. **Stellantis-Handbuch analysieren** 📄
   - PDF lesen und Anforderungen extrahieren
   - Unterschiede zu Hyundai dokumentieren

2. **Mount-Punkt einrichten** 🔌
   - Windows-Ordner erstellen
   - Mount-Script erstellen
   - Testen

3. **Code-Implementierung** 💻
   - `garantieakte_workflow.py` erweitern
   - API-Endpoint anpassen
   - Testing

---

## 💡 ERKENNTNISSE

1. **Hyundai-Implementierung ist sehr gut wiederverwendbar** ✅
   - 90% der Logik kann übernommen werden
   - Nur Pfade und Filter müssen angepasst werden

2. **Garantie-Erkennung ist identisch** ✅
   - `charge_type=60`, `labour_type IN ('G','GS')`, `invoice_type=6`
   - Keine Anpassung nötig

3. **Hauptunterschied: Speicherort** ⚠️
   - Hyundai: `Hyundai_Garantie/`
   - Stellantis: `Stellantis_Garantie/`
   - Separate Mount-Punkte nötig

4. **Brand-Parameter macht Code flexibel** 💡
   - Einheitliche Code-Basis
   - Einfache Erweiterung für weitere Marken (z.B. Leapmotor)

---

## 📝 NOTIZEN

- **Stellantis = Opel** (subsidiary=1)
- **Standorte:** Deggendorf (1) + Landau (3)
- **Handbuch:** `de_DE-AT_Stellantis_WAM_V2_NSC.pdf` (126 Seiten)
- **Referenz:** Hyundai Garantie-Feature (TAG 173)

---

*Erstellt: TAG 189 | Autor: Claude AI*
