# BWA Logik-Korrektur - TAG 182

**Datum:** 2026-01-12  
**Status:** ✅ Direkte Kosten korrigiert, Indirekte Kosten in Prüfung

---

## 🎯 PROBLEM

**GlobalCube vs. DRIVE (YTD Sep-Dez 2025):**
- Direkte Kosten: 33.698,81 € Differenz (DRIVE fehlen)
- Indirekte Kosten: 1.715,22 € Differenz (DRIVE fehlen)

---

## ✅ LÖSUNG: DIREKTE KOSTEN

### Korrekte Logik (Dezember 2025):

**411xxx + 410021 + 489xxx (KST 1-7) sollten ENTHALTEN sein in direkten Kosten**

**Änderung:**
- ❌ **ALT:** 410021, 411xxx, 489xxx komplett aus direkten Kosten ausgeschlossen
- ✅ **NEU:** Nur 489xxx (KST 0) aus direkten Kosten ausgeschlossen

**Ergebnis:**
- Direkte Kosten YTD: **659.228,98 €** ✅
- GlobalCube Referenz: **659.228,98 €** ✅
- **Differenz: 0,00 €** ✅

---

## ⏳ INDIREKTE KOSTEN (in Prüfung)

### Aktuelle Situation:

**DRIVE:** 851.318,27 €  
**GlobalCube:** 838.943,85 €  
**Differenz:** +12.374,42 € (DRIVE hat zu viel)

### Analyse:

- 489xxx KST 0: 1.708,92 €
- Erklärt nicht die Differenz von 12.374,42 €

### Mögliche Ursachen:

1. **489xxx komplett ausschließen?**
   - Aktuell: 489xxx (KST 0) in indirekten Kosten enthalten
   - Möglicherweise sollte 489xxx komplett ausgeschlossen werden?

2. **Andere Konten zu viel enthalten?**
   - Möglicherweise sind andere Konten in indirekten Kosten enthalten, die ausgeschlossen werden sollten?

3. **Zeitraum-abhängige Logik?**
   - Möglicherweise ist die Logik für indirekte Kosten auch zeitraum-abhängig?

---

## 📝 CODE-ÄNDERUNGEN

### Direkte Kosten:

```python
# ALT (TAG 177):
AND NOT (
    nominal_account_number = 410021
    OR nominal_account_number BETWEEN 411000 AND 411999
    OR nominal_account_number BETWEEN 489000 AND 489999
    ...
)

# NEU (TAG 182):
AND NOT (
    ...
    OR (nominal_account_number BETWEEN 489000 AND 489999
        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
    ...
)
```

### Indirekte Kosten:

```python
# Aktuell:
AND NOT (
    nominal_account_number = 410021
    OR nominal_account_number BETWEEN 411000 AND 411999
    OR nominal_account_number BETWEEN 489000 AND 489999
)
```

**Frage:** Sollte 489xxx komplett ausgeschlossen werden?

---

## 🚀 NÄCHSTE SCHRITTE

1. ⏳ **Indirekte Kosten analysieren**
   - Welche Konten sind zu viel enthalten?
   - Sollte 489xxx komplett ausgeschlossen werden?

2. ⏳ **Validierung**
   - Betriebsergebnis prüfen
   - Unternehmensergebnis prüfen

3. ⏳ **Zeitraum-Analyse**
   - Warum war TAG 177 Logik für August 2025 korrekt?
   - Warum ist sie für Dezember 2025 falsch?

---

## 📊 STATUS

- ✅ Direkte Kosten korrigiert (0,00 € Differenz)
- ⏳ Indirekte Kosten in Prüfung (+12.374,42 € Differenz)
- ⏳ Betriebsergebnis in Prüfung
- ⏳ Unternehmensergebnis in Prüfung

---

**Nächster Schritt:** Indirekte Kosten analysieren und korrigieren.
