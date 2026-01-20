# Kapazitätsplanung - Frontend-Überarbeitung

**Datum:** 2026-01-20  
**TAG:** 200  
**Datei:** `templates/aftersales/kapazitaetsplanung.html`

---

## ✅ DURCHGEFÜHRTE ÄNDERUNGEN

### 1. Wochen-Übersicht (`renderGudatWeek()`)

**Verbesserungen:**
- ✅ **Samstag-Erkennung:** Werkstatt geschlossen wird korrekt angezeigt
- ✅ **Sonntag-Erkennung:** Auch Sonntage werden als geschlossen markiert
- ✅ **Datum-Anzeige:** Datum wird zusätzlich zum Wochentag angezeigt
- ✅ **Negative AW:** Überbuchung wird als "X AW überbucht" angezeigt (rot)
- ✅ **Kapazität:** Gesamtkapazität wird pro Tag angezeigt
- ✅ **Bessere Fehlerbehandlung:** Prüft ob Container existiert und Daten vorhanden sind

**Neue Features:**
```javascript
// Samstag/Sonntag erkennen
const dayOfWeek = dateObj.getDay(); // 0=Sonntag, 6=Samstag
const isClosed = dayOfWeek === 6 || dayOfWeek === 0;

// Geschlossene Tage anzeigen
if (isClosed) {
    statusText = 'GESCHLOSSEN';
    freeText = '-';
}
```

**CSS-Anpassungen:**
- `.gudat-week-day.closed` - Grauer Hintergrund für geschlossene Tage
- `.day-date` - Datum-Anzeige
- `.day-capacity` - Kapazität-Anzeige

---

### 2. Teams-Anzeige (`renderGudatTeams()`)

**Verbesserungen:**
- ✅ **Negative AW:** Überbuchung wird als "X AW überbucht" angezeigt (rot, fett)
- ✅ **Tooltip:** Erklärung bei Überbuchung: "Überbuchung: Geplante Arbeit übersteigt verfügbare Kapazität (Abwesenheiten berücksichtigt)"
- ✅ **Abwesenheiten:** Abwesende AW werden angezeigt (falls vorhanden)
- ✅ **Bessere Formatierung:** Kapazität und freie AW klar getrennt

**Neue Features:**
```javascript
// Freie AW korrekt anzeigen
if (free < 0) {
    freeText = `${Math.abs(free)} AW überbucht`;
    freeClass = 'text-danger fw-bold';
} else {
    freeText = `${Math.round(free)} AW frei`;
}

// Tooltip für Überbuchung
const tooltip = free < 0 ? 
    'title="Überbuchung: Geplante Arbeit übersteigt verfügbare Kapazität (Abwesenheiten berücksichtigt)"' : 
    '';
```

---

### 3. KPIs-Anzeige (`renderGudatWidget()`)

**Verbesserungen:**
- ✅ **Negative AW:** Überbuchung wird in den KPIs oben korrekt angezeigt
- ✅ **Visuelle Hervorhebung:** Überbuchung in rot und fett
- ✅ **Tooltip:** Erklärung bei Überbuchung

**Code:**
```javascript
const free = data.frei || 0;
if (free < 0) {
    freeElement.textContent = Math.abs(Math.round(free)) + ' AW überbucht';
    freeElement.className = 'text-danger fw-bold';
    freeElement.title = 'Überbuchung: Geplante Arbeit übersteigt verfügbare Kapazität (Abwesenheiten berücksichtigt)';
}
```

---

## 📊 VISUELLE VERBESSERUNGEN

### Vorher:
- Samstag: Zeigte 0% (verwirrend)
- Negative AW: "-69 AW frei" (unverständlich)
- Keine Erklärung für Überbuchung

### Nachher:
- Samstag: "GESCHLOSSEN" (klar)
- Negative AW: "69 AW überbucht" (verständlich, rot)
- Tooltip erklärt Überbuchung
- Datum wird angezeigt
- Kapazität wird pro Tag angezeigt

---

## 🎯 ERGEBNIS

**Alle Probleme behoben:**
- ✅ Samstage werden als geschlossen angezeigt
- ✅ Negative AW wird als Überbuchung angezeigt
- ✅ Tooltips erklären Überbuchung
- ✅ Bessere Fehlerbehandlung
- ✅ Zusätzliche Informationen (Datum, Kapazität)

**Frontend ist jetzt benutzerfreundlicher und zeigt alle Informationen korrekt an!**

---

**Erstellt von:** Claude AI  
**Datum:** 2026-01-20  
**TAG:** 200
