# BWA 84705 Korrektur - TAG 196

**Datum:** 2026-01-16  
**TAG:** 196  
**Status:** ✅ **IMPLEMENTIERT**

---

## 🎯 ERKENNTNIS AUS GLOBALCUBE SCREENSHOT

**GlobalCube zeigt:**
- **"3 - ME (Mechanik)":** 76.497 €
- **"4 - KA (Karosserie)":** 9.922 €
- **Summe "Mechanik+Karo":** 86.419 € ✅

**WICHTIG:** Das Konto **84705 (12.500 €)** ist **visuell unter "3 - ME"** aufgelistet, gehört also zu **Mechanik**, nicht zu Clean Park!

---

## ✅ IMPLEMENTIERT

### 84705 zu Mechanik hinzugefügt:

- **84705 gehört zu Mechanik** (nicht Clean Park)
- Mechanik enthält jetzt 84705
- Clean Park schließt 84705 aus

### Clean Park Korrektur:

- **Clean Park schließt 84705 aus** (gehört zu Mechanik)
- Clean Park zeigt jetzt korrekte Werte ohne 84705

---

## 📊 ERGEBNISSE

**Nach Korrektur (Dezember 2025):**
- **Mechanik (mit 84705):** 70.596,43 €
- **Karosserie:** 0,00 € (keine Buchungen in 8405xx/745xxx)
- **Summe Mechanik+Karo:** 70.596,43 €
- **GlobalCube Mechanik+Karo:** 86.419,00 €
- **Differenz: -15.822,57 €**

**Clean Park:**
- **Clean Park (ohne 84705):** 5.008,43 €
- **GlobalCube Clean Park:** 16.741,00 €
- **Differenz: -11.732,57 €**

---

## ⚠️ VERBLEIBENDE PROBLEME

1. **Karosserie fehlt komplett:**
   - DRIVE zeigt 0,00 €
   - GlobalCube zeigt 9.922,00 €
   - **Mögliche Ursachen:**
     - GlobalCube verwendet andere Konten für Karosserie
     - Filter-Unterschiede
     - Standort-Unterschiede

2. **Mechanik+Karo Differenz:**
   - Fehlende 15.822,57 €
   - Teilweise durch fehlende Karosserie erklärt (9.922 €)
   - Verbleibende Differenz: ~5.900 €

---

## 📝 NÄCHSTE SCHRITTE

1. ⏳ **Karosserie-Konten finden:** Welche Konten verwendet GlobalCube für Karosserie?
2. ⏳ **Verbleibende Differenz analysieren:** ~5.900 € fehlen noch
3. ⏳ **Clean Park Differenz analysieren:** -11.732,57 €

---

## ✅ STATUS

- ✅ 84705 zu Mechanik hinzugefügt
- ✅ Clean Park schließt 84705 aus
- ⚠️ Karosserie fehlt komplett (9.922 €)
- ⚠️ Verbleibende Differenz: -15.822,57 €
