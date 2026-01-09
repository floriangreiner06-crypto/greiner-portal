# Teilebezugsrechnung - Prüfung der Hyundai Unterlagen

**Datum:** 2026-01-09 (TAG 175)  
**Frage:** Muss beim Abrechnen/Einreichen eine Teilebezugsrechnung hochgeladen werden?

---

## 📋 ERGEBNIS DER PRÜFUNG

### ❌ **KEINE EXPLIZITE ERWÄHNUNG EINER "TEILEBEZUGSRECHNUNG"**

In den vorhandenen Hyundai-Unterlagen wurde **keine explizite Erwähnung** einer "Teilebezugsrechnung" gefunden, die beim Einreichen/Abrechnen hochgeladen werden muss.

---

## ✅ ABER: NACHWEIS DES TEILEBEZUGS IST PFLICHT

### Aus Garantie-Richtlinie 2025-09, Abschnitt 8.2 (Arbeitskarte):

**Pflichten:**
1. ✅ **Verwendete Hyundai Original-Teile dokumentieren**
2. ✅ **Angabe des schadenverursachenden Teiles (Teilenummer)**
3. ✅ **Nachweis des Teilebezugs aus Mobis (EDMOS)**

**Quelle:** `docs/hyundai/MOBIS_TEILEBEZUG_LOESUNG_TAG175.md`

---

## 📄 DOKUMENTATIONSPFLICHTEN (AUS UNTERLAGEN)

### 1. Arbeitskarte (Pflicht)
**Inhalt:**
- Reparaturmaßnahme (mit Unterschrift)
- **Verwendete Hyundai Original-Teile** ✅
- Angewandte Arbeitszeit nach Monteur
- Getrennt nach Arbeitsposition (TT-Zeiten zeitlich an/ab)
- **Angabe des schadenverursachenden Teiles** ✅
- Eventuelle weitere Feststellungen (durch Meister)

**Quelle:** `docs/hyundai/GARANTIE_DOKUMENTATION_GUDAT_ANALYSE_TAG173.md`

### 2. Garantieantrag (GWMS) - Einreichung
**Inhalt:**
- Alle oben genannten Daten
- DTC-Codes
- Fehlerbeschreibung
- Fotos (wenn nötig)
- **Keine explizite Erwähnung einer Teilebezugsrechnung**

**Quelle:** `docs/hyundai/GARANTIE_DOKUMENTATION_GUDAT_ANALYSE_TAG173.md`

---

## 🔍 WAS WIRD FÜR DEN TEILEBEZUG BENÖTIGT?

### Aus `MOBIS_TEILEBEZUG_LOESUNG_TAG175.md`:

**Benötigte Informationen:**
1. **Teile-Liste:**
   - Teilenummer
   - Beschreibung
   - Menge
   - Preis

2. **Bestell-Informationen:**
   - Bestellnummer
   - Lieferdatum

3. **Nachweis:**
   - Mobis Bestellnummer
   - Mobis Lieferschein
   - Bestätigung: Hyundai Original-Teil

**Aber:** Keine explizite Erwähnung einer "Rechnung" als separatem Dokument.

---

## 💡 INTERPRETATION

### Mögliche Interpretationen:

1. **Nachweis über Arbeitskarte:**
   - Die Teile-Informationen werden in der **Arbeitskarte** dokumentiert
   - Die Arbeitskarte enthält bereits:
     - Verwendete Hyundai Original-Teile
     - Angabe des schadenverursachenden Teiles
   - **→ Keine separate Rechnung nötig?**

2. **Nachweis über Mobis-Bestellung:**
   - Der "Nachweis des Teilebezugs aus Mobis (EDMOS)" könnte bedeuten:
     - Bestellnummer aus Mobis
     - Lieferschein aus Mobis
     - **→ Möglicherweise als Dokument/PDF?**

3. **Keine Rechnung erforderlich:**
   - Die Dokumentation der Teile in der Arbeitskarte reicht aus
   - Keine separate "Teilebezugsrechnung" nötig

---

## ❓ OFFENE FRAGEN

1. **Was genau bedeutet "Nachweis des Teilebezugs aus Mobis (EDMOS)"?**
   - Reicht die Bestellnummer/Lieferschein-Nummer?
   - Oder muss ein PDF-Dokument hochgeladen werden?

2. **Gibt es eine separate Anforderung für Teilebezugsrechnungen?**
   - In den vorhandenen Unterlagen nicht gefunden
   - Möglicherweise in anderen Dokumenten (z.B. GWMS-Handbuch)?

3. **Wie wird der Nachweis aktuell erbracht?**
   - Manuell in GWMS eingegeben?
   - Als PDF hochgeladen?
   - Oder reicht die Arbeitskarte?

---

## 🎯 EMPFEHLUNG

### 1. Prüfung der tatsächlichen GWMS-Anforderungen
- GWMS-Handbuch prüfen
- Aktuelle Einreichungsprozesse prüfen
- Bei Hyundai nachfragen (falls nötig)

### 2. Aktuelle Praxis prüfen
- Wie wird der Teilebezug aktuell nachgewiesen?
- Wird eine Rechnung hochgeladen?
- Oder reicht die Arbeitskarte?

### 3. Implementierung
- **Falls Rechnung erforderlich:**
  - Mobis-Bestellrechnung als PDF abrufen
  - In Garantieakte-Workflow integrieren
  - Als Anhang zur Garantieakte hinzufügen

- **Falls nur Nachweis erforderlich:**
  - Bestellnummer/Lieferschein in Arbeitskarte dokumentieren
  - Mobis-Teilebezug-API nutzen für Nachweis
  - In PDF einfügen

---

## 📊 ZUSAMMENFASSUNG

| Frage | Antwort |
|-------|---------|
| **Ist eine Teilebezugsrechnung explizit erwähnt?** | ❌ Nein |
| **Ist ein Nachweis des Teilebezugs erforderlich?** | ✅ Ja |
| **Wie wird der Nachweis erbracht?** | ❓ Unklar (Arbeitskarte oder separates Dokument?) |
| **Muss eine Rechnung hochgeladen werden?** | ❓ Nicht explizit in Unterlagen gefunden |

---

**Nächster Schritt:** Prüfung der tatsächlichen GWMS-Anforderungen oder aktuelle Praxis erfragen.
