# Bugfix: PDF-Generierung - 'NoneType' object has no attribute 'split'

**TAG:** 192  
**Datum:** 2026-01-15  
**Problem:** Fehler beim Erstellen der Garantieakte-PDF

---

## 🔴 Problem

**Fehler:**
```
AttributeError: 'NoneType' object has no attribute 'split'
```

**Ursache:**
- `Paragraph()` von reportlab erhält `None` statt String
- Passiert wenn Datenfelder `None` sind (z.B. `kunde.get('name')` = None)
- Reportlab versucht `.split()` auf None aufzurufen

**Betroffene Stellen:**
- `kunde.get('name')` → None
- `kunde.get('adresse')` → None
- `fahrzeug.get('marke_modell')` → None
- `auftrag.get('serviceberater')` → None
- `job_beschreibung` → None
- `beschreibung` (Teile) → None
- `description` (GUDAT) → None

---

## ✅ Lösung

### 1. Safe-Paragraph-Funktion
- **Neu:** `safe_paragraph(text, style)` Funktion
- **Logik:** Prüft ob text None ist, gibt '' zurück falls ja
- **Code:**
```python
def safe_paragraph(text, style):
    """Erstellt Paragraph nur wenn text nicht None ist"""
    if text is None:
        return ''
    return Paragraph(str(text), style)
```

### 2. None-Checks überall
- **Alle Paragraph-Aufrufe:** Verwenden `safe_paragraph()` oder `or ''`
- **Betroffene Stellen:**
  - Kunde-Name, Adresse, E-Mail
  - Fahrzeug-Marke/Modell
  - Serviceberater
  - Job-Beschreibung
  - Teile-Beschreibung
  - GUDAT-Description

### Code-Änderungen:
```python
# Vorher:
Paragraph(kunde.get('name', ''), normal_style)  # Wenn name=None, wird '' verwendet, aber könnte trotzdem None sein

# Nachher:
safe_paragraph(kunde.get('name'), normal_style)  # Expliziter None-Check
```

---

## 📊 Erwartete Verbesserung

- **Vorher:** Fehler wenn Datenfeld None ist
- **Nachher:** Leerer String wird verwendet, PDF wird erstellt

---

## 🧪 Testing

**Bitte testen:**
1. Garantieauftrag mit fehlenden Daten öffnen
2. "Garantieakte erstellen" klicken
3. PDF sollte jetzt erstellt werden (ohne Fehler)

---

**Status:** ✅ Fix implementiert, Service neu gestartet
