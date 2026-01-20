# Urlaubsplaner User-Test Ergebnisse (TAG 198)

**Datum:** 08.01.2026  
**Quelle:** "Verbesserung Urlaubsplaner.docx" (User Testing)  
**TAG:** 198

---

## 🚨 KRITISCHE BUGS (Funktionalität kaputt)

### 1. **Genehmigungsfunktion funktioniert NICHT** ❌ KRITISCH

**Problem:**
- "Beantragte Urlaubstage können nicht genehmigt werden. Beispiel Edith Egner"
- "Aber bei Edith Egner kommt das Feld für die Auswahl, aber keine Genehmigung"
- "Vermutlich fehlt die Funktion genehmigen komplett"

**Impact:**
- ❌ **Urlaubsplaner ist nicht nutzbar**
- ❌ **Keine Genehmigungen möglich**
- ❌ **E-Mail-Funktion kann nicht getestet werden**

**Beispiele:**
- Edith Egner: Feld für Auswahl vorhanden, aber keine Genehmigung möglich
- Christian Aichinger kann den Urlaub von Vanessa nicht genehmigen
- Vanessa kann auch von anderen keinen Urlaub genehmigen

---

### 2. **Admin/Genehmigerrollen funktionieren nicht** ❌ KRITISCH

**Problem:**
- "Die Admin bzw. Genehmigerrollen funktionieren auch nicht"
- "Christian Aichinger kann den Urlaub von Vanessa nicht genehmigen"
- "Vanessa kann auch von anderen keinen Urlaub genehmigen"

**Impact:**
- ❌ **Berechtigungssystem defekt**
- ❌ **Genehmigungs-Workflow nicht nutzbar**

---

### 3. **Falsche Tage werden markiert** ❌ KRITISCH

**Problem:**
- "Außerdem werden die falschen Tage markiert, wenn man z.B bei Edith Egner genehmigen möchte"
- "Hier werden die Tage bei Christian Aichinger blau markiert…"

**Impact:**
- ❌ **Genehmigung für falsche Person**
- ❌ **Verwirrung bei Genehmigern**
- ❌ **Falsche Daten werden angezeigt**

---

### 4. **Resturlaubstage werden falsch berechnet** ❌ KRITISCH

**Problem:**
- "Die Resturlaubstage werden nicht richtig angezeigt"
- "z.B. Bianca Greindl hat 41 Resturlaubstage für 2026 das kann nicht stimmen!!"
- "Herbert Huber hat 27 Tage Resturlaub, obwohl er bereits alle Urlaubstage für 2026 verplant hat…"

**Impact:**
- ❌ **Falsche Anzeige von Resturlaub**
- ❌ **Fehlentscheidungen bei Urlaubsplanung**

---

### 5. **Urlaubstage werden nicht vom Anspruch abgezogen** ❌ KRITISCH

**Problem:**
- "Vanessa Groll hat Urlaub im Juni 2026 beantragt, diese 5 Tage werden aber nicht vom Urlaubsanspruch abgezogen"

**Impact:**
- ❌ **Urlaubsanspruch wird nicht korrekt aktualisiert**
- ❌ **Doppelte Buchung möglich**

---

### 6. **Urlaubstage werden im Januar 2027 nicht zurückgesetzt** ❌ KRITISCH

**Problem:**
- "Die Urlaubstage werden im Januar 2027 nicht richtig angepasst, dort stehen die gleichen Tage wie 2026"
- "Hier sollte eine Regelung her, dass die Urlaubstage immer zurückgesetzt werden auf die Standard 27 Tage, falls jemand schon im Voraus Urlaubstage verplant"

**Impact:**
- ❌ **Falsche Anzeige im neuen Jahr**
- ❌ **Urlaubsanspruch wird nicht zurückgesetzt**

---

## ⚠️ BUGS (Falsche Darstellung)

### 7. **Falsche Darstellung - Krankheit als Schulung**

**Problem:**
- "Es wurden z.B. von Stefan Geier Krankheitstage eingetragen, hier wird es aber als Schulung angezeigt"

**Impact:**
- ⚠️ **Falsche Kategorisierung**
- ⚠️ **Verwirrung bei Anzeige**

---

### 8. **Falsche Darstellung bei Vanessa**

**Problem:**
- "Vanessa hat keinen Urlaub im Juni hinterlegt, sie hat dann eine Woche eingetragen"
- "Bei Christian Aichinger zeigt es aber schon die beiden Wochen an"

**Impact:**
- ⚠️ **Inkonsistente Anzeige**
- ⚠️ **Verwirrung bei Genehmigern**

---

## 🎯 NEUE FEATURES (Gewünscht)

### 1. **Urlaubssperren pro Abteilung**

**Anforderung:**
- "Admins sollen noch die Möglichkeit haben, dass man Urlaubssperren pro Abteilung eingeben kann"
- "Dies bitte mit einem roten Strich im Kästchen darstellen"

**Priorität:** Hoch

---

### 2. **Masseneingaben für Urlaubstage**

**Anforderung:**
- "Außerdem sollen Admins noch Masseneingaben für Urlaubstage pro Abteilung bzw. für alle Mitarbeiter eintragen können"
- "Hier müssten dann einfach alle Abteilungen bzw. Mitarbeiter zum anhaken sein, damit man hier den Urlaub in einem bestimmten Zeitraum für alle eingeben kann"

**Priorität:** Mittel

---

### 3. **Report für Geschäftsjahresende**

**Anforderung:**
- "Außerdem wäre es noch super, wenn man einen Report erstellen kann, der am Geschäftsjahresende die jeweiligen bereits genommenen und noch übrigen Urlaubstage pro Mitarbeiter anzeigt (wichtig für Rückstellungen)"

**Priorität:** Mittel

---

### 4. **Freie Tage manuell hinterlegen**

**Anforderung:**
- "Man sollte auch die freien Tage der Mitarbeiter manuell hinterlegen können, diese sollten dann im Planer ausgegraut werden, damit jeder weiß, dass derjenige z.b. mittwochs immer frei hat"
- "Somit wäre der Planer einfach übersichtlicher, der Urlaubsanspruch müsste dann auch dementsprechend angepasst werden!"
- "In Loco-Soft werden die freien Tage nicht gekennzeichnet, daher keine Übertragung möglich bzw. müsste manuell erledigt werden"

**Priorität:** Mittel

---

## 🎨 UI-VERBESSERUNGEN

### 1. **Aktueller Tag farblich markieren**

**Anforderung:**
- "Evtl. könnte man den aktuellen Tag farblich markieren, also die ganze Spalte von allen Mitarbeitern"
- "Einfachere Darstellung und für HR besser"
- "Die blaue 7 fällt hier kaum auf… am besten die ganze Spalte mit einer hellen Farbe markieren…"

**Priorität:** Niedrig

---

## 👥 MITARBEITER-ZUORDNUNGEN (Korrigieren)

**Problem:** Mitarbeiter sind in falschen Abteilungen

**Korrekturen:**
- **Silvia Eiglmaier** → sollte unter "Disposition" laufen
- **Sandra Schimmer, Stephan Wittmann, Götz Klein** → sollen bei "Fahrzeuge" stehen
- **Daniel Thammer** → soll unter "Werkstatt" laufen
- **Edith Egner** → soll unter "Service" laufen
- **Werkstatt kein AD** → noch zuordnen

**Priorität:** Mittel

---

## 📋 PRIORITÄTEN

### Sofort (KRITISCH):
1. ✅ Genehmigungsfunktion reparieren
2. ✅ Admin/Genehmigerrollen reparieren
3. ✅ Falsche Tage-Markierung beheben
4. ✅ Resturlaubstage-Berechnung korrigieren
5. ✅ Urlaubstage-Abzug vom Anspruch implementieren
6. ✅ Jahreswechsel-Logik (Januar 2027) implementieren

### Kurzfristig:
7. ✅ Krankheit/Schulung-Darstellung korrigieren
8. ✅ Mitarbeiter-Zuordnungen korrigieren

### Mittelfristig (Neue Features):
9. ⚠️ Urlaubssperren pro Abteilung
10. ⚠️ Masseneingaben für Urlaubstage
11. ⚠️ Report für Geschäftsjahresende
12. ⚠️ Freie Tage manuell hinterlegen

### Langfristig (UI):
13. ⚠️ Aktueller Tag farblich markieren

---

## 🔍 ANALYSE-BEDARF

### Zu prüfen:
1. **Genehmigungs-API:** `/approve` Endpunkt funktioniert?
2. **Berechtigungsprüfung:** `current_user.can_access_feature()` funktioniert?
3. **Team-Ermittlung:** Wie werden Genehmiger-Teams ermittelt?
4. **Frontend-JavaScript:** Verwendet falsche Employee-ID?
5. **Resturlaub-Berechnung:** Formel prüfen
6. **Urlaubstage-Abzug:** Wann wird der Anspruch aktualisiert?
7. **Jahreswechsel:** Automatisches Reset implementiert?

---

## 📝 NÄCHSTE SCHRITTE

1. **Code-Analyse:** Genehmigungsfunktion in `api/vacation_api.py` prüfen
2. **Berechtigungsprüfung:** `auth/auth_manager.py` prüfen
3. **Frontend:** JavaScript für Genehmigung prüfen
4. **Resturlaub-Berechnung:** Formel in `api/vacation_api.py` prüfen
5. **Jahreswechsel:** Logik für automatisches Reset implementieren

---

**Status:** 🔴 **KRITISCH - Urlaubsplaner ist aktuell nicht vollständig nutzbar**
