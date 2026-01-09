# Garantie-Dokumentation: GUDAT-Integration Analyse

**Erstellt:** 2026-01-09 (TAG 173)  
**Frage:** Können wir die Dokumentationspflichten von Hyundai erfüllen, indem wir die Texteingaben der Mechaniker aus GUDAT holen?

---

## 📋 HYUNDAI DOKUMENTATIONSPFLICHTEN

### Aus Garantie-Richtlinie 2025-09, Abschnitt 8.2:

**1. Kundenangabe (O-Ton)**
- ✅ **Pflicht:** Wörtliche Kundenangabe im Werkstattauftrag
- ✅ **Wann:** Zum Zeitpunkt der Kundenangabe
- ✅ **Wo:** Im DMS (Locosoft) eröffnen

**2. Diagnose/Veranlassung**
- ✅ **Pflicht:** Technischer Befund des Serviceberaters/Werkstattmeisters
- ✅ **Wann:** Nach Dialogannahme/Probefahrt
- ✅ **Inhalt:** 
  - Diagnose-Ergebnis
  - Fehlercodes (DTC)
  - Technischer Befund

**3. Arbeitskarte**
- ✅ **Pflicht:** Hinweise über die durchgeführte Reparatur
- ✅ **Inhalt:**
  - Reparaturmaßnahme (mit Unterschrift)
  - Verwendete Hyundai Original-Teile
  - Angewandte Arbeitszeit nach Monteur
  - Getrennt nach Arbeitsposition (TT-Zeiten zeitlich an/ab)
  - Angabe des schadenverursachenden Teiles
  - Eventuelle weitere Feststellungen (durch Meister)

**4. Stempelzeiten**
- ✅ **Pflicht:** TT-Zeiten müssen zeitlich (an/ab) separat ausgewiesen werden
- ✅ **Wichtig:** Muss im DMS abgebildet sein

**5. Garantieantrag (GWMS)**
- ✅ **Pflicht:** Einreichung innerhalb 21 Tage
- ✅ **Inhalt:**
  - Alle oben genannten Daten
  - DTC-Codes
  - Fehlerbeschreibung
  - Fotos (wenn nötig)

---

## 🔍 GUDAT: WAS WIRD DOKUMENTIERT?

### Aktuelle GUDAT-Integration

**GraphQL Query (aus `werkstatt_live_api.py`):**
```graphql
query GetWorkshopTasks {
  workshopTasks {
    data {
      id
      start_date
      work_load
      work_state
      description          # ← Mechaniker-Notizen?
      workshopService { id name }
      resource { id name }
      dossier {
        id
        vehicle { id license_plate }
        orders { id number }
      }
    }
  }
}
```

**Aktuell geholt:**
- ✅ `description` - Beschreibung des Tasks
- ✅ `work_load` - Vorgabe AW
- ✅ `start_date` - Startzeit
- ✅ `work_state` - Status
- ✅ Auftragsnummer (via `orders`)

**Frage:** Was genau steht in `description`?
- Ist das die Mechaniker-Notiz aus der Auftragskachel?
- Oder nur die ursprüngliche Beschreibung?

---

## ❓ OFFENE FRAGEN

### 1. GUDAT-Struktur prüfen
- **Was dokumentieren Mechaniker in GUDAT?**
  - In welchem Feld? (`description`? `notes`? `comments`?)
  - Wo genau in der Auftragskachel?
  - Wird das automatisch gespeichert?

### 2. GraphQL-Schema erweitern
- Gibt es weitere Felder für Notizen?
  - `notes`?
  - `comments`?
  - `internal_notes`?
  - `mechanic_notes`?
  - `diagnosis`?
  - `findings`?

### 3. Mapping zu Hyundai-Pflichten
- **Kundenangabe (O-Ton):** ❓ Wo in GUDAT?
- **Diagnose-Ergebnis:** ❓ `description`? Oder separates Feld?
- **Reparaturmaßnahme:** ❓ `description`? Oder separates Feld?
- **Stempelzeiten:** ✅ Aus Locosoft (nicht GUDAT)

---

## 🧪 TEST-PLAN

### 1. GUDAT GraphQL-Schema analysieren
```python
# Test: Alle verfügbaren Felder eines workshopTask prüfen
query = """
  query {
    __type(name: "WorkshopTask") {
      fields {
        name
        type { name kind }
      }
    }
  }
"""
```

### 2. Echten Auftrag prüfen
```python
# Test: Auftrag mit Mechaniker-Notizen holen
task = get_workshop_task_by_order_number(220345)
print(json.dumps(task, indent=2))
# Prüfen: Welche Felder enthalten Mechaniker-Notizen?
```

### 3. Mechaniker-Notizen identifizieren
- Wo schreiben Mechaniker ihre Notizen?
- Werden sie in GUDAT gespeichert?
- Können wir sie per GraphQL holen?

---

## ✅ MÖGLICHE LÖSUNG

### Variante 1: GUDAT `description` nutzen
**Wenn:** Mechaniker schreiben in `description`:
- ✅ Diagnose-Ergebnis
- ✅ Reparaturmaßnahme
- ✅ Befunde

**Dann können wir:**
1. `description` aus GUDAT holen
2. In Garantie-Checkliste anzeigen
3. Für GWMS-Antrag verwenden

### Variante 2: Locosoft `text_line` nutzen
**Wenn:** Mechaniker schreiben in Locosoft `labours.text_line`:
- ✅ Arbeitsbeschreibung
- ✅ Notizen pro Position

**Dann können wir:**
1. `text_line` aus Locosoft holen
2. Mit GUDAT-Daten kombinieren
3. Vollständige Dokumentation erstellen

### Variante 3: Kombination
**Best Practice:**
- GUDAT: Diagnose, Befunde, Notizen
- Locosoft: Arbeitspositionen, Stempelzeiten, Teile
- Kombiniert: Vollständige Dokumentation

---

## 📊 ABGLEICH: GUDAT vs. HYUNDAI-PFLICHTEN

| Hyundai-Pflicht | GUDAT | Locosoft | Status |
|----------------|-------|----------|--------|
| **Kundenangabe (O-Ton)** | ❓ | ✅ `orders.text` | ✅ Verfügbar |
| **Diagnose-Ergebnis** | ❓ `description`? | ❓ `labours.text_line`? | ⚠️ Prüfen |
| **Reparaturmaßnahme** | ❓ `description`? | ❓ `labours.text_line`? | ⚠️ Prüfen |
| **Stempelzeiten (an/ab)** | ❌ | ✅ `times` Tabelle | ✅ Verfügbar |
| **Arbeitspositionen** | ❌ | ✅ `labours` Tabelle | ✅ Verfügbar |
| **Fehlercodes (DTC)** | ❓ | ❓ | ⚠️ Prüfen |
| **Fotos** | ❓ | ❓ | ⚠️ Prüfen |

---

## 🚀 NÄCHSTE SCHRITTE

### 1. GUDAT-Struktur analysieren
```bash
# Test-Script erstellen
python3 scripts/test_gudat_dokumentation.py
```

**Ziele:**
- Alle verfügbaren Felder eines `workshopTask` finden
- Prüfen, wo Mechaniker-Notizen gespeichert werden
- GraphQL-Schema erweitern (falls nötig)

### 2. Locosoft-Struktur prüfen
```sql
-- Prüfen: Was steht in labours.text_line?
SELECT 
    order_number,
    text_line,
    description,
    operation_code
FROM labours
WHERE order_number = 220345
  AND text_line IS NOT NULL
  AND text_line != '';
```

### 3. Mapping erstellen
- GUDAT → Hyundai-Pflichten
- Locosoft → Hyundai-Pflichten
- Kombiniert → Vollständige Dokumentation

### 4. Dashboard erweitern
- GUDAT-Notizen anzeigen
- Locosoft-Notizen anzeigen
- Vollständigkeits-Check
- Auto-Füllen für GWMS

---

## 💡 ERWARTUNG

**Wahrscheinlich:**
- ✅ GUDAT `description` enthält Mechaniker-Notizen
- ✅ Locosoft `labours.text_line` enthält Arbeitsbeschreibungen
- ✅ Kombiniert reicht es für Hyundai-Dokumentationspflichten

**Aber:**
- ⚠️ Muss getestet werden
- ⚠️ GraphQL-Schema könnte erweitert werden müssen
- ⚠️ Mapping könnte angepasst werden müssen

---

## ✅ TEST-ERGEBNISSE (2026-01-09)

### GUDAT-Analyse durchgeführt

**Statistik (50 Tasks heute):**
- ✅ 23 Tasks (46%) haben `description` gefüllt
- ⚠️ 27 Tasks (54%) haben `description = null`
- ✅ `orders.note` Feld existiert, aber meist `null`

**Beispiele für `description`:**
- "3.Inspektion+ eCall Batterie wechseln"
- "1. Inspektion bzw. Öl- und Filterwechsel+Fehlerspeicher auslesen"
- "9,90" (Preis?)

**Erkenntnis:**
- `description` enthält **Arbeitsbeschreibungen**, nicht unbedingt Mechaniker-Notizen während der Arbeit
- `orders.note` könnte Mechaniker-Notizen enthalten, ist aber meist leer
- **Fazit:** GUDAT `description` ist verfügbar, aber möglicherweise nicht ausreichend für vollständige Dokumentation

### Locosoft-Analyse durchgeführt

**Prüfung von `labours.text_line` für Hyundai Garantieaufträge:**

**Beispiele gefunden:**
- ✅ **Kundenangabe (O-Ton):** "Kunde gibt an: Tankdeckel öffnet sporadisch nicht"
- ✅ **Diagnose-Notiz:** "GDS-Grundprüfung: -> fehlt"
- ✅ **Fehlercodes (DTC):** "Verbesserte AGR-Regellogik (DTC P0404, P049D, P0471"
- ✅ **Reparaturmaßnahme:** "40DC18 - NX4e_NX4e_P/HEV_ECU UPDATE"
- ✅ **Arbeitsbeschreibung:** "HEIZUNGS-& LUFTUNGSSTEUERUNG", "Tankklappe instandsetzen"

**Erkenntnis:**
- ✅ Locosoft `text_line` enthält **genau die Informationen**, die Hyundai benötigt!
- ✅ Kundenangaben (O-Ton) sind dokumentiert
- ✅ Diagnose-Ergebnisse sind dokumentiert
- ✅ Fehlercodes (DTC) sind dokumentiert
- ✅ Reparaturmaßnahmen sind dokumentiert

---

## ✅ FAZIT: KÖNNEN WIR DIE DOKUMENTATIONSPFLICHTEN ERFÜLLEN?

### JA! ✅ Kombination aus GUDAT + Locosoft

| Hyundai-Pflicht | GUDAT | Locosoft | Status |
|----------------|-------|----------|--------|
| **Kundenangabe (O-Ton)** | ❌ | ✅ `labours.text_line` | ✅ **Verfügbar** |
| **Diagnose-Ergebnis** | ⚠️ `description` (begrenzt) | ✅ `labours.text_line` | ✅ **Verfügbar** |
| **Reparaturmaßnahme** | ⚠️ `description` (begrenzt) | ✅ `labours.text_line` | ✅ **Verfügbar** |
| **Fehlercodes (DTC)** | ❌ | ✅ `labours.text_line` | ✅ **Verfügbar** |
| **Stempelzeiten (an/ab)** | ❌ | ✅ `times` Tabelle | ✅ **Verfügbar** |
| **Arbeitspositionen** | ❌ | ✅ `labours` Tabelle | ✅ **Verfügbar** |

### Empfehlung

**Primär: Locosoft `labours.text_line`**
- ✅ Enthält alle benötigten Informationen
- ✅ Kundenangaben (O-Ton) sind dokumentiert
- ✅ Diagnose, Fehlercodes, Reparaturmaßnahmen sind dokumentiert

**Sekundär: GUDAT `description`**
- ⚠️ Enthält Arbeitsbeschreibungen, aber nicht immer vollständig
- ✅ Kann als Ergänzung dienen

**Kombination:**
- ✅ Locosoft `text_line` für vollständige Dokumentation
- ✅ GUDAT `description` als zusätzliche Quelle
- ✅ Locosoft `times` für Stempelzeiten
- ✅ Locosoft `labours` für Arbeitspositionen

---

## 🚀 NÄCHSTE SCHRITTE

1. ✅ **GUDAT geprüft** → `description` verfügbar, aber begrenzt
2. ✅ **Locosoft geprüft** → `text_line` enthält alle benötigten Informationen!
3. ⏳ **Dashboard erweitern** → Locosoft `text_line` in Garantie-Checkliste anzeigen
4. ⏳ **Auto-Füllen** → `text_line` für GWMS-Antrag nutzen

---

---

## 🔍 UPDATE: "ANMERKUNG"-FELD GEFUNDEN (Screenshot-Analyse)

**Aus Screenshot identifiziert:**
- ✅ Feldname: **"Anmerkung"** (Notes/Comments)
- ✅ Enthält Mechaniker-Notizen:
  - "T.R."
  - "-Fehlerspeicher ausgelesen, DTC C162078 im Front Radar aktiv abgespeichert."
  - "-Einstellwinkel des Radarmoduls vorne überprüft → Dazu"
- ✅ Auftrag: 220542 (Locosoft (Hyundai))

**Nächster Schritt:**
- ⏳ HAR-Datei analysieren, um GraphQL-Feldnamen zu identifizieren
- ⏳ Test-Query erstellen, um "Anmerkung"-Daten zu holen

**Analyse-Script erstellt:**
- `/opt/greiner-portal/scripts/analyse_gudat_har.py`
- Wartet auf HAR-Datei in Sync-Ordner

---

---

## ✅ ERFOLG: "ANMERKUNG"-FELD GEFUNDEN! (HAR-Datei-Analyse)

**Datum:** 2026-01-09  
**Auftrag getestet:** 220542

### Ergebnis

**Die "Anmerkung" ist in `workshopTasks.description`!**

**Query gefunden:**
```graphql
query GetDossierDrawerData($id: ID!) {
  dossier(id: $id) {
    id
    note
    workshopTasks {
      id
      description  # ← HIER IST DIE ANMERKUNG!
      work_load
      work_state
    }
  }
}
```

**Beispiel (Auftrag 220542, Task 84082):**
```
T.R.
-Fehlerspeicher ausgelesen, DTC C162078 im Front Radar aktiv abgespeichert.
-Einstellwinkel des Radarmoduls vorne überprüft → Dazu GDS Statische Kalibrierung durchgeführt
-Stoßstange vorne A+E, Vertikalwinkel des Radarmoduls auf -1,3° angepasst
-Statische kalibrierung nicht möglich.
-Dynamische kalibrierung durchgeführt → OK, Kalibrierung erfolgreich durchgelaufen → NOK Fehler C162078 immer noch vorhanden.
=> Radarmodul vorne lässt sich nicht kalibrieren
→ Vorderes Radarmodul erneuern + Kalibrieren
```

### Wichtige Erkenntnisse

1. **`workshopTasks.description`** enthält die Mechaniker-Notizen
2. **Nicht alle Tasks haben eine `description`** (kann `null` sein)
3. **Pro Task eine Anmerkung** (nicht pro Dossier)
4. **Die Query `GetDossierDrawerData` holt bereits alle `workshopTasks` mit `description`**

### Nächste Schritte

1. ✅ **Feld identifiziert:** `workshopTasks.description`
2. ✅ **Query gefunden:** `GetDossierDrawerData`
3. ⏳ **Integration:** In Garantie-Dashboard einbauen
4. ⏳ **API-Endpoint:** Erstellen, um Anmerkungen für Auftrag zu holen

---

*Analyse erstellt: 2026-01-09 (TAG 173)*  
*GUDAT-Test durchgeführt: 2026-01-09*  
*Locosoft-Test durchgeführt: 2026-01-09*  
*Screenshot-Analyse: 2026-01-09*  
*HAR-Datei-Analyse: 2026-01-09*  
*✅ Anmerkung-Feld gefunden: workshopTasks.description*
