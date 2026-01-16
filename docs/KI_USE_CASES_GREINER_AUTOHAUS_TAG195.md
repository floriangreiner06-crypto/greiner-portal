# KI Use Cases für Greiner Autohaus - TAG 195

**Erstellt:** 2026-01-16  
**Basis:** LM Studio Server Integration (http://46.229.10.1:4433)  
**Status:** ✅ Implementiert - Bereit für Use Cases

---

## 📋 ÜBERBLICK

Konkrete, umsetzbare Use Cases für die lokale KI-Integration im DRIVE-System. Fokus auf **praktische, sofort umsetzbare** Anwendungen mit hohem ROI.

---

## 🎯 PRIORITÄT 1: WERKSTATT & GARANTIE (Höchster ROI)

### 1.1 Arbeitskarten-Dokumentationsprüfung ⭐⭐⭐ ✅ IMPLEMENTIERT

**Status:** ✅ Bereits implementiert (`/api/ai/pruefe/arbeitskarte/<auftrag_id>`)

**Problem:**
- Arbeitskarten müssen vollständig dokumentiert sein (Hyundai/Stellantis-Richtlinie)
- Manuelle Prüfung auf Vollständigkeit: **5-10 Min pro Auftrag**
- Fehlende Dokumentation → Garantie-Ablehnungen → **Geldverlust**

**KI-Lösung:**
- ✅ Automatische Vollständigkeitsprüfung
- ✅ Qualitätsbewertung (0-100%)
- ✅ Fehlende Elemente identifizieren
- ✅ Empfehlungen geben

**ROI:** ~24.000€/Jahr (50 Aufträge/Tag × 5 Min × 20 Tage × 12 Monate)

**Nächste Schritte:**
- [ ] Frontend-Integration (Button in Arbeitskarte-Ansicht)
- [ ] Automatische Warnung bei unvollständiger Dokumentation
- [ ] Dashboard-Widget: "Aufträge mit unvollständiger Dokumentation"

---

### 1.2 Garantie-Dokumentationsprüfung vor GWMS-Einreichung ⭐⭐⭐

**Problem:**
- Garantieanträge müssen vollständig sein (21-Tage-Frist)
- Fehlende Dokumentation → Ablehnungen → **Geldverlust**
- Manuelle Prüfung: **10-15 Min pro Antrag**

**KI-Lösung:**
- Automatische Prüfung vor GWMS-Einreichung:
  - ✅ Alle erforderlichen Felder vorhanden?
  - ✅ DTC-Codes dokumentiert?
  - ✅ Arbeitskarte vollständig?
  - ✅ TT-Zeiten erfasst?
  - ✅ Fotos vorhanden (wenn nötig)?
- Risikobewertung: Erfolgswahrscheinlichkeit (niedrig/mittel/hoch)
- Automatische Checkliste: Was fehlt noch?

**Datenquellen:**
- `garantie_akte` (DRIVE) - Garantie-Dokumentation
- `orders` (Locosoft) - Auftragsdaten
- `gudat` (GUDAT) - Diagnose-Daten
- GWMS-API - Einreichungsstatus

**ROI:** ~1.200€/Jahr (10 Anträge/Monat × 12 Min × 12 Monate)

**Integration:**
- Endpoint: `POST /api/ai/pruefe/garantie/<auftrag_id>`
- Integration in `api/garantie_soap_api.py` (vor GWMS-Einreichung)
- Frontend: Warnung bei unvollständiger Dokumentation

---

### 1.3 Automatische Fehlerklassifikation aus Mechaniker-Notizen ⭐⭐

**Problem:**
- Mechaniker-Notizen sind unstrukturiert (GUDAT `description`)
- Fehler müssen manuell kategorisiert werden
- Keine automatische Priorisierung

**KI-Lösung:**
- Automatische Klassifikation:
  - **Fehlertyp:** Motor, Elektrik, Karosserie, Klima, Getriebe, etc.
  - **Dringlichkeit:** Kritisch, Normal, Niedrig
  - **Komplexität:** Einfach, Mittel, Komplex
- Vorschläge für Diagnose-Schritte
- Automatische Zuordnung zu Spezialisten

**Datenquellen:**
- `gudat.description` - Mechaniker-Notizen
- `orders.order_text` - Kundenangabe
- `labours` - Arbeitspositionen

**ROI:** ~1.500€/Jahr (Effizienzsteigerung bei Auftragsverteilung)

**Integration:**
- Endpoint: `POST /api/ai/klassifiziere/fehler`
- Integration in Werkstatt-Live-Ansicht
- Automatische Tags/Badges in Auftragsliste

---

### 1.4 TT-Zeit-Optimierung für Garantieaufträge ⭐⭐

**Problem:**
- TT-Zeiten werden oft nicht optimal genutzt (siehe `docs/hyundai/HYUNDAI_DIAGNOSE_VERGUETUNG_ANALYSE_TAG173.md`)
- Bis 0,9 Stunden (9 AW) = **75,87€ zusätzliche Vergütung** pro Auftrag
- Viele Serviceberater wissen nicht, wann TT-Zeit sinnvoll ist

**KI-Lösung:**
- Automatische Analyse:
  - Diagnosezeit vs. Standardarbeitszeit vergleichen
  - Empfehlung: TT-Zeit erfassen? (Ja/Nein)
  - Begründung: Warum lohnt es sich?
- Automatische Warnung: "TT-Zeit möglich: +75€ Vergütung"

**Datenquellen:**
- `labours` - Arbeitspositionen, AW
- `stempelzeiten` - Tatsächliche Arbeitszeit
- `orders` - Auftragsdaten

**ROI:** **Sehr hoch!** (75€ pro Auftrag × 10 Aufträge/Monat = 750€/Monat = 9.000€/Jahr)

**Integration:**
- Endpoint: `POST /api/ai/analysiere/tt-zeit/<auftrag_id>`
- Integration in Arbeitskarte-Ansicht
- Automatische Empfehlung bei Garantieaufträgen

---

## 🎯 PRIORITÄT 2: REKLAMATIONEN & KUNDENBEZIEHUNGEN

### 2.1 Reklamationsbewertung (Rechtliche Prüfung) ⭐⭐⭐

**Problem:**
- Reklamationen müssen rechtlich bewertet werden
- Manuelle Bewertung: **20-30 Min pro Reklamation**
- Komplexe Rechtslage (Gewährleistung, Beweislastumkehr, etc.)
- Beispiel: `docs/reklamationen/kunde_3008334_steinschlag_bewertung.md`

**KI-Lösung:**
- Automatische rechtliche Bewertung:
  - ✅ Gewährleistungsfrist prüfen (2 Jahre)
  - ✅ Beweislastumkehr prüfen (6 Monate)
  - ✅ Mangelbegriff prüfen
  - ✅ Risikobewertung (niedrig/mittel/hoch)
- Automatische Empfehlungen:
  - Gewährleistung annehmen/ablehnen?
  - Kulanzlösung empfehlen?
  - Versicherung empfehlen?

**Datenquellen:**
- Reklamationsdaten (DRIVE)
- Verkaufsdaten (Locosoft) - Verkaufsdatum, Preis
- Auftragshistorie (Locosoft) - Wartungen, Reparaturen

**ROI:** ~1.200€/Jahr (10 Reklamationen/Monat × 25 Min × 12 Monate)

**Integration:**
- Endpoint: `POST /api/ai/bewerte/reklamation`
- Integration in Reklamations-Workflow
- Automatische Bewertung bei Reklamationserstellung

---

### 2.2 Kundenanfragen-Kategorisierung & Priorisierung ⭐

**Problem:**
- Kundenanfragen (E-Mail, Telefon, etc.) müssen manuell kategorisiert werden
- Keine automatische Priorisierung
- Wichtige Anfragen werden übersehen

**KI-Lösung:**
- Automatische Kategorisierung:
  - **Thema:** Rechnung, Termin, Reklamation, Garantie, Wartung, etc.
  - **Dringlichkeit:** Hoch, Normal, Niedrig
  - **Zugehöriger Auftrag/Fahrzeug** (aus Text extrahieren)
- Automatische Antwortvorschläge (optional)

**ROI:** ~500€/Jahr (Effizienzsteigerung)

**Integration:**
- Endpoint: `POST /api/ai/kategorisiere/anfrage`
- Integration in Kundenkommunikation-System (falls vorhanden)

---

## 🎯 PRIORITÄT 3: BANKENSPIEGEL & FINANZEN

### 3.1 Transaktions-Kategorisierung ⭐⭐

**Problem:**
- Transaktionen müssen manuell kategorisiert werden
- `kategorie`-Feld in `transaktionen`-Tabelle
- Zeitaufwendig bei vielen Transaktionen: **2-5 Min pro Transaktion**

**KI-Lösung:**
- Automatische Kategorisierung basierend auf:
  - `buchungstext`
  - `verwendungszweck`
  - Betrag
  - Konto
- Vorschläge für Kategorien:
  - Materialaufwand
  - Personalkosten
  - Miete
  - Versicherung
  - Steuern
  - Sonstiges

**Datenquellen:**
- `transaktionen` (DRIVE) - Banktransaktionen
- `konten` (DRIVE) - Kontoinformationen

**ROI:** ~7.500€/Jahr (500 Transaktionen/Monat × 3 Min × 12 Monate)

**Integration:**
- Endpoint: `POST /api/ai/kategorisiere/transaktion`
- Integration in Bankenspiegel-Import
- Automatische Kategorisierung bei Import

---

### 3.2 Anomalie-Erkennung bei Transaktionen ⭐

**Problem:**
- Ungewöhnliche Transaktionen müssen manuell erkannt werden
- Fehlerhafte Buchungen werden spät entdeckt

**KI-Lösung:**
- Automatische Anomalie-Erkennung:
  - Ungewöhnliche Beträge
  - Ungewöhnliche Kategorien
  - Ungewöhnliche Zeitpunkte
  - Ungewöhnliche Verwendungszwecke
- Automatische Warnungen bei verdächtigen Transaktionen

**ROI:** Schwer quantifizierbar, aber wichtig für Qualität

**Integration:**
- Endpoint: `POST /api/ai/erkenne/anomalie`
- Integration in Bankenspiegel-Dashboard
- Automatische Warnungen

---

### 3.3 Automatische Kontenzuordnung für Buchungen ⭐

**Problem:**
- Buchungen müssen manuell Konten zugeordnet werden
- Fehlerhafte Zuordnungen → falsche BWA-Werte

**KI-Lösung:**
- Automatische Kontenzuordnung basierend auf:
  - Buchungstext
  - Verwendungszweck
  - Betrag
  - Historie
- Vorschläge für Konten (SKR51-Kontenrahmen)

**ROI:** ~1.000€/Jahr (Effizienzsteigerung)

**Integration:**
- Endpoint: `POST /api/ai/zuordne/konto`
- Integration in Controlling/BWA-Workflow

---

## 🎯 PRIORITÄT 4: VERKAUF & FAHRZEUGVERWALTUNG

### 4.1 Fahrzeugbeschreibung-Generierung ⭐

**Problem:**
- Fahrzeugbeschreibungen müssen manuell geschrieben werden
- Zeitaufwendig für Verkaufsplattformen: **10-15 Min pro Fahrzeug**

**KI-Lösung:**
- Automatische Generierung von Fahrzeugbeschreibungen:
  - Basierend auf Fahrzeugdaten (Marke, Modell, Ausstattung, etc.)
  - Marktgerechte Formulierung
  - SEO-optimiert
- Vorschläge für Verkaufsargumente

**Datenquellen:**
- `fahrzeuge` (Locosoft) - Fahrzeugdaten
- Verkaufsdaten (Locosoft)

**ROI:** ~1.500€/Jahr (10 Fahrzeuge/Monat × 12 Min × 12 Monate)

**Integration:**
- Endpoint: `POST /api/ai/generiere/fahrzeugbeschreibung`
- Integration in Verkaufs-Workflow

---

### 4.2 Standzeit-Analyse & Empfehlungen ⭐

**Problem:**
- Fahrzeuge mit langer Standzeit müssen identifiziert werden
- Manuelle Analyse erforderlich

**KI-Lösung:**
- Automatische Analyse der Standzeit:
  - Gründe für lange Standzeit identifizieren
  - Empfehlungen für Preisreduktion
  - Empfehlungen für Marketing-Maßnahmen

**ROI:** Schwer quantifizierbar, aber wichtig für Umsatz

**Integration:**
- Endpoint: `POST /api/ai/analysiere/standzeit`
- Integration in Fahrzeugverwaltung

---

## 📊 ZUSAMMENFASSUNG: TOP 10 USE CASES

| Priorität | Use Case | Zeitersparnis | ROI/Jahr | Komplexität | Status |
|-----------|----------|---------------|----------|-------------|--------|
| 1 | **Arbeitskarten-Dokumentationsprüfung** | 5-10 Min/Auftrag | ~24.000€ | Mittel | ✅ Implementiert |
| 2 | **TT-Zeit-Optimierung** | 2-3 Min/Auftrag | ~9.000€ | Niedrig | ⏳ Geplant |
| 3 | **Garantie-Dokumentationsprüfung** | 10-15 Min/Antrag | ~1.200€ | Mittel | ⏳ Geplant |
| 4 | **Transaktions-Kategorisierung** | 2-5 Min/Transaktion | ~7.500€ | Niedrig | ⏳ Geplant |
| 5 | **Reklamationsbewertung** | 20-30 Min/Reklamation | ~1.200€ | Hoch | ⏳ Geplant |
| 6 | **Fehlerklassifikation** | 3-5 Min/Auftrag | ~1.500€ | Mittel | ⏳ Geplant |
| 7 | **Kontenzuordnung** | 3-5 Min/Buchung | ~1.000€ | Niedrig | ⏳ Geplant |
| 8 | **Fahrzeugbeschreibung** | 10-15 Min/Fahrzeug | ~1.500€ | Niedrig | ⏳ Geplant |
| 9 | **Anomalie-Erkennung** | - | Qualität | Mittel | ⏳ Geplant |
| 10 | **Kundenanfragen-Kategorisierung** | 2-3 Min/Anfrage | ~500€ | Niedrig | ⏳ Geplant |

**Gesamt-ROI:** ~47.400€/Jahr + Qualitätsverbesserung

---

## 🚀 IMPLEMENTIERUNGS-ROADMAP

### Phase 1: Sofort umsetzbar (TAG 195-196)
1. ✅ Arbeitskarten-Dokumentationsprüfung (bereits implementiert)
2. [ ] Frontend-Integration für Arbeitskarten-Prüfung
3. [ ] TT-Zeit-Optimierung (hoher ROI, niedrige Komplexität)

### Phase 2: Kurzfristig (TAG 197-198)
4. [ ] Garantie-Dokumentationsprüfung
5. [ ] Transaktions-Kategorisierung
6. [ ] Fehlerklassifikation

### Phase 3: Mittelfristig (TAG 199+)
7. [ ] Reklamationsbewertung
8. [ ] Kontenzuordnung
9. [ ] Fahrzeugbeschreibung
10. [ ] Anomalie-Erkennung

---

## 💡 SPEZIELLE USE CASES FÜR GREINER AUTOHAUS

### Multi-Brand-Unterstützung
- **Hyundai:** Spezifische Garantie-Anforderungen
- **Stellantis (Opel):** Spezifische Garantie-Anforderungen
- **KI erkennt automatisch:** Brand basierend auf `subsidiary` und prüft entsprechend

### 3-Standort-Unterstützung
- **DEG (Deggendorf Opel):** `subsidiary = 1`
- **HYU (Deggendorf Hyundai):** `subsidiary = 2`
- **LAN (Landau):** `subsidiary = 3`
- **KI berücksichtigt:** Standort-spezifische Anforderungen

### GUDAT-Integration
- **Mechaniker-Notizen:** Aus GUDAT `description` extrahieren
- **Diagnose-Daten:** Aus GUDAT Tasks analysieren
- **KI nutzt:** GUDAT-Daten für bessere Dokumentationsprüfung

---

## 🔧 TECHNISCHE UMSETZUNG

### API-Struktur (bereits vorhanden)
- `api/ai_api.py` - LM Studio Client
- Endpoints: `/api/ai/*`
- Konfiguration: `config/credentials.json`

### Integration-Pattern
```python
from api.ai_api import lm_studio_client

# Beispiel: Arbeitskarten-Prüfung
result = lm_studio_client.chat_completion(
    messages=[
        {"role": "system", "content": "Du bist ein Experte für Autohaus-Dokumentation."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=500,
    temperature=0.3
)
```

---

## 📝 NÄCHSTE SCHRITTE

1. **Frontend-Integration** für Arbeitskarten-Prüfung
2. **TT-Zeit-Optimierung** implementieren (hoher ROI!)
3. **Garantie-Dokumentationsprüfung** implementieren
4. **Testing** mit echten Daten
5. **Feedback** sammeln und optimieren

---

**Erstellt:** TAG 195  
**Status:** Use Cases identifiziert, bereit für Implementierung
