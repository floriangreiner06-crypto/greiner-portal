# Garantie Live-Dashboard Mockup - TAG 173

**Erstellt:** 2026-01-09  
**Zweck:** Live-Handlungsempfehlungen für Serviceberater während der Auftragsbearbeitung

---

## 🎯 Zielsetzung

Ein Live-Dashboard für Serviceberater, das während der Bearbeitung eines Garantieauftrags durch den Mechaniker:
- ✅ Live-Status anzeigt
- ✅ Handlungsempfehlungen gibt
- ✅ Dokumentations-Checkliste führt
- ✅ Vergütungs-Optimierung zeigt
- ✅ Automatisch aktualisiert wird

---

## 📋 Features des Mockups

### 1. Auftrag-Info Box
- Auftragsnummer, Fahrzeug, Kunde
- Serviceberater, Mechaniker
- Vorgabe vs. Gestempelt
- Aktueller Status (In Bearbeitung/Wartend/Fertig)

### 2. Vergütungs-Übersicht
- Aktuelle Vergütung
- Potenzial (was möglich wäre)
- Optimierte Vergütung (mit allen Empfehlungen)

### 3. Handlungsempfehlungen
- **Kritisch** (rot): Wichtige Maßnahmen, die Geld bringen
- **Wichtig** (gelb): Empfohlene Maßnahmen
- **Info** (blau): Zusätzliche Möglichkeiten

Jede Empfehlung zeigt:
- Titel und Beschreibung
- Aktionen (Buttons)
- Wert in Euro

### 4. Dokumentations-Checkliste
- Fortschrittsbalken
- Pflichtfelder vs. Optionale Felder
- Automatische Aktualisierung

### 5. Mechaniker-Status
- Wer arbeitet gerade?
- Wie lange schon?
- Vorgabe vs. Ist-Zeit

---

## 🚀 Verwendung

### Mockup ansehen:
```
http://10.80.80.20:5000/aftersales/garantie-live-dashboard-mockup/
```

**Hinweis:** Route muss noch erstellt werden!

### Direkt öffnen:
```bash
# Auf Server
firefox /opt/greiner-portal/templates/aftersales/garantie_live_dashboard_mockup.html
```

---

## 📊 Beispiel-Daten im Mockup

**Auftrag:** #220345
- Hyundai IONIQ 5
- Serviceberater: Salmansberger, Valentin
- Mechaniker: Müller, Thomas
- Vorgabe: 3.0 AW
- Gestempelt: 3.8 AW (23 Min)
- Aktuell: 27.80 €
- Potenzial: +15.17 €

**Empfehlungen:**
1. BASICA00 fehlt → +8.43 €
2. TT-Zeit möglich (0.8 AW) → +6.74 €
3. RQ0 möglich (wenn Fehlercodes) → +25.29 €

---

## 🔧 Nächste Schritte (nach Bewertung)

### 1. API-Endpoint erstellen
```python
@bp.route('/api/garantie/live-dashboard/<int:order_number>')
def get_garantie_live_dashboard(order_number):
    # Daten aus Locosoft holen
    # Empfehlungen berechnen
    # Status prüfen
    return jsonify({...})
```

### 2. Auto-Refresh implementieren
- Alle 30 Sekunden aktualisieren
- WebSocket für Echtzeit-Updates (optional)

### 3. Aktionen implementieren
- BASICA00 hinzufügen
- TT-Zeit berechnen und hinzufügen
- Checkliste aktualisieren

### 4. Integration
- In bestehendes Werkstatt-Cockpit integrieren
- Oder als separates Feature

---

## 💡 Design-Entscheidungen

### Farben:
- **Rot (Kritisch):** Wichtige Maßnahmen, die Geld bringen
- **Gelb (Wichtig):** Empfohlene Maßnahmen
- **Blau (Info):** Zusätzliche Möglichkeiten
- **Grün (Erledigt):** Bereits umgesetzt

### Layout:
- Responsive Design (Mobile + Desktop)
- Klare Hierarchie
- Fokus auf Handlungsempfehlungen

### UX:
- Live-Indikator zeigt, dass Daten aktuell sind
- Buttons für direkte Aktionen
- Fortschrittsbalken für Checkliste
- Hover-Effekte für Interaktivität

---

## 📝 Feedback sammeln

**Fragen für die Bewertung:**
1. Ist die Übersicht klar und verständlich?
2. Sind die Handlungsempfehlungen hilfreich?
3. Fehlt etwas Wichtiges?
4. Ist die Checkliste vollständig?
5. Sollte etwas anders dargestellt werden?

---

*Mockup erstellt: 2026-01-09 (TAG 173)*
