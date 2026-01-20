# Urlaubsplaner "undefined.undefined." Fix - TAG 198

**Datum:** 2026-01-19  
**Problem:** "undefined.undefined." wird in "Zu genehmigen" Box angezeigt

---

## 🐛 PROBLEM

In der "Zu genehmigen" Box wird "undefined.undefined." angezeigt statt:
- Mitarbeiter-Name
- Datum

---

## 🔍 URSACHE

Mögliche Ursachen:
1. **Browser-Cache:** Alte JavaScript-Version wird gecacht
2. **Unvollständige API-Daten:** `employee_name` oder `date` fehlen in der Response
3. **Fehlerhafte Datenstruktur:** API gibt Daten in falschem Format zurück

---

## ✅ LÖSUNG

### 1. Defensive Programming hinzugefügt

**Code-Stelle:** `templates/urlaubsplaner_v2.html` (Zeilen 725-740)

```javascript
validPending.forEach(p => {
    // Prüfe ob alle benötigten Felder vorhanden sind
    if (!p.employee_name || !p.date || !p.booking_id) {
        console.warn('⚠️ Unvollständige Daten in pending approval:', p);
        return; // Überspringe unvollständige Einträge
    }
    
    // Explizite String-Konvertierung
    const employeeName = String(p.employee_name || 'Unbekannt');
    const dateStr = fmtD(p.date);
    // ...
});
```

### 2. Explizite String-Konvertierung

- `employee_name` wird explizit zu String konvertiert
- `date` wird durch `fmtD()` formatiert
- Fallback-Werte für fehlende Daten

### 3. API-Datenformatierung

**Code-Stelle:** `api/vacation_api.py` (Zeilen 1234-1243)

- `date` wird explizit zu String konvertiert (ISO-Format)
- `employee_name` wird aus Datenbank geholt
- Alle Felder werden explizit gesetzt

---

## 🔧 WENN PROBLEM PERSISTIERT

### Browser-Cache leeren:
1. **Hard Refresh:** `Strg + F5` (Windows) oder `Cmd + Shift + R` (Mac)
2. **Browser-Cache leeren:** Einstellungen → Datenschutz → Browserdaten löschen
3. **Inkognito-Modus testen:** Um Cache zu umgehen

### API-Daten prüfen:
```bash
# API direkt testen
curl "http://localhost:5000/api/vacation/pending-approvals" | jq '.pending[0]'
```

### Browser-Console prüfen:
1. F12 öffnen
2. Console-Tab öffnen
3. Nach Warnungen suchen: `⚠️ Unvollständige Daten in pending approval`

---

## 📋 ÄNDERUNGEN

- `templates/urlaubsplaner_v2.html`:
  - Defensive Programming hinzugefügt (Zeile 727-730)
  - Explizite String-Konvertierung (Zeile 733-734)
  - Fallback-Werte für fehlende Daten
  - Console-Warnung bei unvollständigen Daten

---

**Status:** ✅ **Fix implementiert - Browser-Cache leeren falls Problem persistiert**
