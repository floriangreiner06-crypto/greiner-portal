# GlobalCube Portal Analyse - TAG 182

**Datum:** 2026-01-12  
**Status:** ⚠️ Portal ist Desktop-Client, nicht Web-basiert

---

## 🔍 ERGEBNISSE

### Portal-Zugriff

**URL:** http://10.80.80.10:9300  
**Login:** Greiner / Hawaii#22  
**Status:** ✅ Erreichbar (HTTP 200)

**Problem:** Portal ist sehr klein (731 Bytes), deutet auf Desktop-Client oder einfache Startseite hin.

**Erkenntnis:** GlobalCube ist ein **IBM Cognos Business Intelligence Portal** (redirectet zu `/bi/`).

**Portal-Typ:** IBM Cognos BI
**Haupt-URL:** http://10.80.80.10:9300/bi/

---

## 💡 ALTERNATIVE ANALYSE-STRATEGIE

Da das Portal nicht Web-basiert ist, müssen wir die **GlobalCube-Strukturen und Cubes direkt analysieren**:

### 1. Struktur-Dateien analysieren ✅

**Bereits durchgeführt:**
- ✅ `Struktur_GuV.xml` - BWA-Hierarchie identifiziert
- ✅ `Struktur_Controlling.xml` - Controlling-Struktur identifiziert
- ✅ Separate "Ausbildung"-Position (ID: 75) gefunden

### 2. Cube-Definitionen analysieren ⏳

**Nächste Schritte:**
- f_belege Cube analysieren (33 MB, könnte BWA-Daten enthalten)
- Nach Konto-Mappings in Cube-Dateien suchen
- Cube-Struktur verstehen

### 3. CSV/Excel-Exporte analysieren ⏳

**Vorhanden:**
- `/mnt/greiner-portal-sync/docs/F.03 BWA Vorjahres-Vergleich (7).xlsx`
- Könnte Filter-Logik durch Vergleich zeigen

### 4. Datenbank-Zugriff prüfen ⏳

**Hypothese:** GlobalCube könnte direkt auf Locosoft DB zugreifen
- Prüfe ob GlobalCube eigene Tabellen hat
- Prüfe ob GlobalCube Views/Materialized Views erstellt

---

## 🎯 EMPFEHLUNG

**Fokus auf Struktur-Analyse:**

1. **GuV-Struktur vollständig analysieren**
   - Welche Konten gehören zu welcher Struktur-ID?
   - Gibt es Filter-Regeln in der Struktur?

2. **f_belege Cube analysieren**
   - Könnte Konto-Mappings enthalten
   - Könnte Filter-Logik enthalten

3. **CSV/Excel-Exporte vergleichen**
   - Welche Werte zeigt GlobalCube?
   - Vergleich mit DRIVE-Berechnungen
   - Identifiziere Unterschiede

4. **Ausbildung-Position validieren**
   - Welche Konten sind in "Ausbildung" (ID: 75)?
   - Ist 411xxx dabei?

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ f_belege Cube analysieren (33 MB)
2. ⏳ CSV/Excel-Exporte mit DRIVE vergleichen
3. ⏳ Ausbildung-Position (411xxx) validieren
4. ⏳ Filter-Logik aus Strukturen extrahieren

---

**Status:** Portal-Analyse abgeschlossen, Fokus auf Struktur-Analyse
