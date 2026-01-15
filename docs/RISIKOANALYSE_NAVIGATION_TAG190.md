# Risikoanalyse: Navigation-Umsetzung TAG 190

**Datum:** 2026-01-14  
**Status:** ⚠️ Vor Aktivierung

---

## 🔴 Potenzielle Gefahren

### 1. **Template-Rendering: 2-stufige Dropdowns**
**Risiko:** ⚠️ MITTEL  
**Problem:** Bootstrap 5 unterstützt standardmäßig keine 2-stufigen Dropdowns (Sub-Dropdowns).  
**Aktueller Code:** `render_navigation_item()` rendert nur 1-stufige Dropdowns.

**Lösung erforderlich:**
- Custom JavaScript für Sub-Dropdowns (Hover/Click)
- Oder: Bootstrap-Dropdown erweitern
- Oder: Alternative UI (z.B. Mega-Menus)

**Test erforderlich:** ✅ Ja

---

### 2. **Feature-Zugriff funktioniert nicht**
**Risiko:** ⚠️ NIEDRIG  
**Problem:** Filterung nach `requires_feature` könnte fehlschlagen.  
**Aktueller Code:** `get_navigation_for_user()` filtert korrekt.

**Test erforderlich:** ✅ Ja (mit verschiedenen User-Rollen)

---

### 3. **Performance bei vielen Items**
**Risiko:** ⚠️ NIEDRIG  
**Problem:** 56 Items werden bei jedem Request geladen.  
**Aktueller Code:** Caching nicht implementiert.

**Lösung:** Optional: Redis-Cache für Navigation-Items

---

### 4. **Fallback funktioniert nicht**
**Risiko:** ⚠️ MITTEL  
**Problem:** Wenn DB-Navigation aktiviert ist, aber Fehler auftritt → keine Navigation sichtbar.  
**Aktueller Code:** Fallback auf hardcoded Navigation ist implementiert.

**Test erforderlich:** ✅ Ja (DB-Fehler simulieren)

---

### 5. **Sub-Dropdowns werden nicht angezeigt**
**Risiko:** 🔴 HOCH  
**Problem:** Aktuelles Template-Macro unterstützt keine 2-stufigen Dropdowns.  
**Aktueller Code:** `render_navigation_item()` rendert nur 1 Ebene.

**Lösung erforderlich:**
- Template-Macro erweitern für Sub-Dropdowns
- JavaScript für Bootstrap-Sub-Dropdowns hinzufügen
- CSS für Sub-Dropdown-Positionierung

**Test erforderlich:** ✅ KRITISCH

---

### 6. **URLs ändern sich nicht**
**Risiko:** ✅ KEIN RISIKO  
**Problem:** URLs bleiben gleich, nur Struktur ändert sich.  
**Status:** ✅ Keine Gefahr

---

### 7. **Rollback schwierig**
**Risiko:** ⚠️ NIEDRIG  
**Problem:** Wenn DB-Navigation aktiviert ist, muss `USE_DB_NAVIGATION=false` gesetzt werden.  
**Lösung:** Einfach Environment-Variable ändern + Service-Restart.

---

## ✅ Sichere Umsetzung

### **Phase 1: Template-Test (OHNE Aktivierung)**
1. Template-Macro für Sub-Dropdowns erweitern
2. JavaScript für Bootstrap-Sub-Dropdowns hinzufügen
3. Test-Seite erstellen (nicht in Produktion)
4. Manuell testen

### **Phase 2: Staging-Test (MIT Aktivierung, Test-User)**
1. `USE_DB_NAVIGATION=true` setzen
2. Nur für Test-User aktivieren (optional: Feature-Flag pro User)
3. Testen mit verschiedenen Rollen
4. Performance prüfen

### **Phase 3: Rollout (Produktion)**
1. `USE_DB_NAVIGATION=true` setzen
2. Service neu starten
3. Monitoring aktivieren
4. Rollback-Plan bereit haben

---

## 🛡️ Empfohlene Maßnahmen

### **VOR Aktivierung:**

1. ✅ **Template-Macro erweitern** für Sub-Dropdowns
2. ✅ **JavaScript hinzufügen** für Bootstrap-Sub-Dropdowns
3. ✅ **CSS anpassen** für Sub-Dropdown-Positionierung
4. ✅ **Test-Seite erstellen** (nicht in Produktion)
5. ✅ **Rollback-Plan dokumentieren**

### **NACH Aktivierung:**

1. ✅ **Monitoring:** Logs prüfen
2. ✅ **User-Feedback:** Erste Reaktionen sammeln
3. ✅ **Performance:** Response-Zeiten prüfen
4. ✅ **Rollback-Bereitschaft:** Falls Probleme auftreten

---

## 🚨 Kritische Punkte

### **MUSS vor Aktivierung behoben werden:**

1. ❌ **Sub-Dropdowns rendern** - Aktuell nicht implementiert!
2. ❌ **JavaScript für Bootstrap** - Fehlt noch!
3. ❌ **CSS für Positionierung** - Fehlt noch!

### **KANN nach Aktivierung optimiert werden:**

1. ⚠️ Performance (Caching)
2. ⚠️ UX-Verbesserungen
3. ⚠️ Weitere Anpassungen

---

## 📋 Checkliste vor Aktivierung

- [ ] Template-Macro erweitert (Sub-Dropdowns)
- [ ] JavaScript für Bootstrap-Sub-Dropdowns implementiert
- [ ] CSS für Sub-Dropdown-Positionierung hinzugefügt
- [ ] Test-Seite erstellt und getestet
- [ ] Rollback-Plan dokumentiert
- [ ] Monitoring vorbereitet
- [ ] User-Information vorbereitet (optional)

---

## 🔄 Rollback-Plan

**Falls Probleme auftreten:**

1. `USE_DB_NAVIGATION=false` in `.env` setzen
2. `sudo systemctl restart greiner-portal`
3. → Fallback auf hardcoded Navigation aktiv

**Dauer:** < 2 Minuten

---

## 💡 Empfehlung

**NICHT JETZT aktivieren!**

Zuerst:
1. Template-Macro für Sub-Dropdowns erweitern
2. JavaScript/CSS hinzufügen
3. Test-Seite erstellen
4. Dann aktivieren

**Geschätzter Aufwand:** 30-60 Minuten
