# DRIVE BWA-Logik Nachbildung - Strategie

**Datum:** 2026-01-12  
**TAG:** 182  
**Ziel:** GlobalCube BWA-Logik vollständig in DRIVE nachbilden (unabhängig von Network Share)

---

## 🎯 AUSGANGSLAGE

### Problem
- GlobalCube Network Share könnte irgendwann wegfallen
- DRIVE muss unabhängig von GlobalCube funktionieren
- BWA-Logik muss 100% korrekt sein

### Aktuelle Situation
- ✅ DRIVE hat bereits große Teile der BWA-Logik implementiert
- ✅ HAR-Vergleiche zeigen < 1€ Differenz (sehr nah!)
- ⚠️ Einige Spezialfälle noch zu klären (z.B. 8910xx für Hyundai)

---

## 📊 VERGLEICH: DRIVE vs. GLOBALCUBE

### ✅ Was wir bereits haben

1. **Konten-Ranges**
   - Umsatz: 8xxxxx (800000-899999, außer 8932xx für Stellantis)
   - Einsatz: 7xxxxx (700000-799999)
   - Kosten: 4xxxxx (400000-499999)
   - Neutrales Ergebnis: 2xxxxx (200000-299999)

2. **Standort-Filter**
   - Deggendorf: `branch_number = 1` (Opel) oder `branch_number = 2` (Hyundai)
   - Landau: `branch_number = 3`
   - 6. Ziffer: Filialcode (1=DEG, 2=Landau)

3. **Firma/Marke-Filter**
   - Stellantis (Opel): `subsidiary_to_company_ref = 1`
   - Hyundai: `subsidiary_to_company_ref = 2`

4. **Kosten-Kategorisierung**
   - Variable Kosten: 4151xx, 4355xx, 455xxx, 487xxx, 491xxx-497899, 8910xx
   - Direkte Kosten: 4xxxxx (KST 1-7), exkl. Variable Kosten, exkl. 411xxx, 489xxx (KST 1-7)
   - Indirekte Kosten: 4xxxxx (KST 0), 424xxx, 438xxx, 498xxx, 891xxx (exkl. 8910xx, 8932xx), 489xxx (KST 0)

5. **G&V-Filter**
   - Abschlussbuchungen ausschließen (verfälschen BWA)

6. **YTD-Berechnung**
   - Wirtschaftsjahr: Sep-Aug
   - Kumulierte Werte vom WJ-Start

### ❓ Was wir von GlobalCube brauchen

1. **Vollständige Filter-Logik**
   - Alle Standorte/Marken-Kombinationen
   - Spezialfälle (z.B. Hyundai 89xxxx)

2. **Konten-Zuordnungen**
   - Welche Konten gehören zu welcher Kategorie?
   - Exclusions und Inclusions

3. **Validierung**
   - Vergleich mit GlobalCube-Werten
   - Automatische Tests

---

## 🔧 STRATEGIE: LOGIK NACHBILDEN

### 1. Statische Konfiguration (unabhängig von GlobalCube)

#### Konten-Ranges in DRIVE definieren
```python
# api/controlling_api.py
KONTO_RANGES = {
    'umsatz': (800000, 889999),
    'umsatz_sonder': (893200, 893299),  # Sonderumsatz
    'einsatz': (700000, 799999),
    'kosten': (400000, 499999),
    'neutral': (200000, 299999)
}
```

#### Filter-Logik in Python-Code implementieren
```python
def build_firma_standort_filter(firma: str, standort: str):
    """
    Baut Filter für Firma und Standort.
    Diese Logik ist statisch in DRIVE definiert.
    """
    # ... aktuelle Implementierung ...
```

#### Exclusions und Spezialfälle dokumentieren
```python
# Direkte Kosten Exclusions
DIRECT_COST_EXCLUSIONS = [
    410021,
    (411000, 411999),
    (415100, 415199),  # Variable Kosten
    # ... etc.
]
```

### 2. Validierung (gegen GlobalCube)

#### Vergleichs-Script
```python
# scripts/vergleiche_bwa_globalcube.py
# Vergleicht DRIVE vs. GlobalCube für alle Standorte/Marken
```

#### Automatische Tests
- HAR-Dateien als Referenz verwenden
- Alle Standorte/Marken testen
- Monat und YTD vergleichen

### 3. Dokumentation

#### Vollständiges Mapping-Dokument
- Alle Filter-Regeln
- Konten-Zuordnungen
- Spezialfälle

---

## ✅ VALIDIERUNG

### Aktuelle Validierung
- ✅ HAR-Vergleiche: < 1€ Differenz für Deggendorf Opel
- ✅ HAR-Vergleiche: < 1€ Differenz für Landau (nach Korrekturen)
- ⚠️ Hyundai: Noch 14.809€ Differenz im Unternehmensergebnis (8910xx Problem)

### Ziel-Validierung
- ✅ Alle Standorte/Marken: < 1€ Differenz
- ✅ Monat und YTD: < 1€ Differenz
- ✅ Alle BWA-Positionen: < 1€ Differenz

---

## 🎯 FAZIT

### Können wir die Logik nachbilden?
**✅ JA!** Wir sind bereits sehr nah dran.

### Sind wir dann valide und korrekt?
**✅ JA, wenn:**
1. Alle Spezialfälle geklärt sind (z.B. 8910xx für Hyundai)
2. Validierung gegen GlobalCube erfolgreich ist (< 1€ Differenz)
3. Alle Standorte/Marken getestet sind
4. Dokumentation vollständig ist

### Vorteile der Nachbildung
- ✅ Unabhängigkeit von GlobalCube Network Share
- ✅ Vollständige Kontrolle über die Logik
- ✅ Anpassbarkeit für zukünftige Anforderungen
- ✅ Validierung durch Vergleich möglich

### Nächste Schritte
1. ⏳ 8910xx Zuordnung für Hyundai klären
2. ⏳ Alle Spezialfälle dokumentieren
3. ⏳ Vollständige Validierung durchführen
4. ⏳ Mapping-Dokument finalisieren

---

## 📝 DOKUMENTATION

### Erstellte Dokumente
- `docs/BWA_LOGIK_FINAL_TAG182.md` - Aktuelle BWA-Logik
- `docs/GLOBALCUBE_BWA_VOLLSTAENDIGE_ANALYSE_TAG182.md` - GlobalCube Analyse
- `docs/globalcube_complete_documentation.json` - Vollständige Struktur-Daten

### Code-Referenzen
- `api/controlling_api.py` - BWA-Berechnung
- `scripts/vergleiche_bwa_globalcube_dez2025.py` - Vergleichs-Script
- `scripts/explore_har_complete.py` - HAR-Analyse
