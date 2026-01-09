# Analyse: Urlaubsplaner Bugs nach Refactoring (TAG 176)

**Datum:** 2026-01-09  
**Quelle:** User Testing Dokument "Verbesserung Urlaubsplaner.docx"  
**Kontext:** Viele Bugs entstanden nach Refactoring

---

## 🚨 KRITISCHE BUGS (Funktionalität kaputt)

### 1. **Genehmigungsfunktion funktioniert NICHT** ❌ KRITISCH

**Problem:**
- "Beantragte Urlaubstage können nicht genehmigt werden. Beispiel Edith Egner"
- "Aber bei Edith Egner kommt das Feld für die Auswahl, aber keine Genehmigung"
- "Die Admin bzw. Genehmigerrollen funktionieren auch nicht"
- "Christian Aichinger kann den Urlaub von Vanessa nicht genehmigen"
- "Vanessa kann auch von anderen keinen Urlaub genehmigen"
- "Vermutlich fehlt die Funktion genehmigen komplett"

**Impact:**
- ❌ **Urlaubsplaner ist nicht nutzbar**
- ❌ **Keine Genehmigungen möglich**
- ❌ **E-Mail-Funktion kann nicht getestet werden**

**Vermutete Ursache:**
- API-Endpunkt `/approve` funktioniert nicht
- Berechtigungsprüfung schlägt fehl
- Team-Ermittlung funktioniert nicht

---

### 2. **Falsche Tage werden markiert** ❌ KRITISCH

**Problem:**
- "Außerdem werden die falschen Tage markiert, wenn man z.B bei Edith Egner genehmigen möchte"
- "Hier werden die Tage bei Christian Aichinger blau markiert…"

**Impact:**
- ❌ **Genehmigung für falsche Person**
- ❌ **Verwirrung bei Genehmigern**

**Vermutete Ursache:**
- Frontend-JavaScript verwendet falsche Employee-ID
- API gibt falsche Daten zurück
- Session-Management-Problem

---

### 3. **Resturlaubstage werden falsch berechnet** ❌ KRITISCH

**Problem:**
- "Die Resturlaubstage werden nicht richtig angezeigt"
- "z.B. Bianca Greindl hat 41 Resturlaubstage für 2026 das kann nicht stimmen!!"
- "Herbert Huber hat 27 Tage Resturlaub, obwohl er bereits alle Urlaubstage für 2026 verplant hat…"
- "Vanessa Groll hat Urlaub im Juni 2026 beantragt, diese 5 Tage werden aber nicht vom Urlaubsanspruch abgezogen"

**Impact:**
- ❌ **Falsche Anzeige von Resturlaub**
- ❌ **Urlaub wird nicht vom Anspruch abgezogen**
- ❌ **Verwirrung bei Mitarbeitern**

**Vermutete Ursache:**
- Berechnung verwendet falsche Daten
- Buchungen werden nicht korrekt gezählt
- Jahr-Problem (siehe Bug #4)

---

### 4. **Jahr-Übergang funktioniert nicht** ❌ KRITISCH

**Problem:**
- "Die Urlaubstage werden im Januar 2027 nicht richtig angepasst, dort stehen die gleichen Tage wie 2026"
- "Hier sollte eine Regelung her, dass die Urlaubstage immer zurückgesetzt werden auf die Standard 27 Tage, falls jemand schon im Voraus Urlaubstage verplant"

**Impact:**
- ❌ **2027 zeigt falsche Daten**
- ❌ **Urlaubstage werden nicht zurückgesetzt**

**Vermutete Ursache:**
- **Hardcoded `2025` in API-Version!** (siehe Analyse doppelte Dateien)
- Root-Version hat `datetime.now().year` - wird aber nicht verwendet
- API verwendet veraltete Version mit hardcoded Jahr

---

### 5. **Falsche Darstellung von Urlaubstypen** ❌

**Problem:**
- "Es wurden z.B. von Stefan Geier Krankheitstage eingetragen, hier wird es aber als Schulung angezeigt"

**Impact:**
- ❌ **Falsche Anzeige von Urlaubstypen**
- ❌ **Verwirrung bei Genehmigern**

**Vermutete Ursache:**
- `vacation_type_id` wird falsch gemappt
- Frontend verwendet falsche Icons/Farben
- Datenbank-Mapping-Problem

---

### 6. **Falsche Darstellung im Kalender** ❌

**Problem:**
- "Vanessa hat keinen Urlaub im Juni hinterlegt, sie hat dann eine Woche eingetragen"
- "Bei Christian Aichinger zeigt es aber schon die beiden Wochen an"
- "Darstellung Christian Aichinger" vs "Darstellung Vanessa" - unterschiedlich

**Impact:**
- ❌ **Inkonsistente Anzeige**
- ❌ **Verwirrung bei Genehmigern**

**Vermutete Ursache:**
- Frontend-Caching-Problem
- API gibt unterschiedliche Daten zurück
- Session-Problem

---

## ⚠️ WICHTIGE FEATURES (Fehlen)

### 7. **Urlaubssperren pro Abteilung** (Feature Request)

**Anforderung:**
- "Admins sollen noch die Möglichkeit haben, dass man Urlaubssperren pro Abteilung eingeben kann"
- "Dies bitte mit einem roten Strich im Kästchen darstellen"

**Status:** ❌ Nicht implementiert

---

### 8. **Masseneingaben** (Feature Request)

**Anforderung:**
- "Admins sollen noch Masseneingaben für Urlaubstage pro Abteilung bzw. für alle Mitarbeiter eintragen können"
- "Hier müssten dann einfach alle Abteilungen bzw. Mitarbeiter zum anhaken sein"

**Status:** ❌ Nicht implementiert

---

### 9. **Report am Geschäftsjahresende** (Feature Request)

**Anforderung:**
- "Report erstellen, der am Geschäftsjahresende die jeweiligen bereits genommenen und noch übrigen Urlaubstage pro Mitarbeiter anzeigt (wichtig für Rückstellungen)"

**Status:** ❌ Nicht implementiert

---

### 10. **Freie Tage manuell hinterlegen** (Feature Request)

**Anforderung:**
- "Man sollte auch die freien Tage der Mitarbeiter manuell hinterlegen können"
- "Diese sollten dann im Planer ausgegraut werden"
- "Der Urlaubsanspruch müsste dann auch dementsprechend angepasst werden"

**Status:** ❌ Nicht implementiert

---

## 🎨 UI/UX VERBESSERUNGEN

### 11. **Aktueller Tag markieren**

**Anforderung:**
- "Evtl. könnte man den aktuellen Tag farblich markieren, also die ganze Spalte von allen Mitarbeitern"
- "Die blaue 7 fällt hier kaum auf… am besten die ganze Spalte mit einer hellen Farbe markieren…"

**Status:** ⚠️ Teilweise implementiert (nur Zahl, nicht ganze Spalte)

---

## 👥 ORGANISATORISCHE PROBLEME

### 12. **Mitarbeiter in falschen Abteilungen**

**Problem:**
- "Silvia Eiglmaier sollte unter 'Disposition' laufen"
- "Sandra Schimmer, Stephan Wittmann und Götz Klein sollen bei 'Fahrzeuge' stehen"
- "Daniel Thammer soll unter 'Werkstatt' laufen"
- "Edith Egner soll unter 'Service' laufen"
- "Werkstatt kein AD: noch zuordnen"

**Status:** ⚠️ Datenproblem, nicht Code-Problem

---

## 🔍 VERBINDUNG ZU REFACTORING-PROBLEMEN

### Zusammenhang mit doppelten Dateien:

**Kritisch:** `vacation_api.py` Problem!

1. **API verwendet veraltete Version:**
   - `app.py` importiert: `from api.vacation_api import vacation_api`
   - API-Version: `2025-12-29` (alt)
   - Root-Version: `2026-01-07` (neu, hat Fixes)

2. **Hardcoded Jahr:**
   - API-Version: `year = request.args.get('year', 2025, type=int)` ❌
   - Root-Version: `year = request.args.get('year', datetime.now().year, type=int)` ✅
   - **→ Erklärt Bug #4 (Jahr-Übergang funktioniert nicht)!**

3. **Fehlendes Logging:**
   - API-Version: Keine Debug-Logs
   - Root-Version: Umfangreiches Logging für Genehmigungsprozess
   - **→ Erklärt warum Genehmigungsprobleme schwer zu debuggen sind!**

---

## 📊 PRIORISIERUNG

### Priorität 1 (KRITISCH - Sofort fixen):
1. ✅ **Genehmigungsfunktion** - Urlaubsplaner nicht nutzbar
2. ✅ **Jahr-Problem** - Hardcoded 2025 → `datetime.now().year`
3. ✅ **Resturlaubstage-Berechnung** - Falsche Anzeige
4. ✅ **Falsche Tage markiert** - Genehmigung für falsche Person

### Priorität 2 (WICHTIG):
5. ✅ **Urlaubstyp-Darstellung** - Krankheit als Schulung
6. ✅ **Kalender-Darstellung** - Inkonsistente Anzeige

### Priorität 3 (FEATURES):
7. ⚠️ Urlaubssperren pro Abteilung
8. ⚠️ Masseneingaben
9. ⚠️ Report am Geschäftsjahresende
10. ⚠️ Freie Tage manuell hinterlegen

### Priorität 4 (UI/UX):
11. ⚠️ Aktueller Tag markieren (ganze Spalte)

### Priorität 5 (Daten):
12. ⚠️ Mitarbeiter in falschen Abteilungen

---

## 🎯 SOFORT-MASSNAHMEN

### 1. vacation_api.py fixen (KRITISCH)

**Problem:** API verwendet veraltete Version mit hardcoded `2025`

**Lösung:**
```bash
# Root-Version nach API kopieren (hat datetime.now().year)
cp vacation_api.py api/vacation_api.py

# Service neu starten
sudo systemctl restart greiner-portal
```

**Erwartetes Ergebnis:**
- ✅ Jahr-Problem behoben (2026/2027 funktionieren)
- ✅ Debug-Logging verfügbar
- ✅ Bessere Fehlerbehandlung

---

### 2. Genehmigungsfunktion debuggen

**Vermutete Ursachen:**
- Team-Ermittlung funktioniert nicht
- Berechtigungsprüfung schlägt fehl
- API-Endpunkt `/approve` hat Bug

**Aktionen:**
1. Logs prüfen: `journalctl -u greiner-portal -f`
2. API-Endpunkt `/api/vacation/pending-approvals` testen
3. API-Endpunkt `/api/vacation/approve` testen
4. Team-Ermittlung prüfen (AD-Manager-Struktur)

---

### 3. Resturlaubstage-Berechnung prüfen

**Vermutete Ursachen:**
- Buchungen werden nicht korrekt gezählt
- Jahr-Problem (siehe #1)
- Berechnung verwendet falsche Daten

**Aktionen:**
1. API-Endpunkt `/api/vacation/my-balance` prüfen
2. Datenbank-Query für Resturlaub prüfen
3. Buchungen pro Mitarbeiter zählen

---

## 📋 NÄCHSTE SCHRITTE

1. ✅ **Sofort:** `vacation_api.py` Root-Version nach API kopieren
2. ✅ **Dann:** Genehmigungsfunktion debuggen
3. ✅ **Dann:** Resturlaubstage-Berechnung prüfen
4. ✅ **Dann:** Urlaubstyp-Darstellung fixen
5. ✅ **Dann:** Kalender-Darstellung fixen

---

**Status:** ✅ Analyse abgeschlossen - Kritische Bugs identifiziert und mit Refactoring-Problemen verknüpft
