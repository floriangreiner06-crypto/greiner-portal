# WhatsApp - Vorarbeiten bis DMZ-Einrichtung

**Datum:** 2026-01-26  
**Status:** 📋 **VORARBEITEN**

---

## ✅ WAS KÖNNEN WIR BIS ZUR DMZ-EINRICHTUNG MACHEN?

### **1. Datenbank-Migration ausführen** ⭐⭐⭐⭐ **HOCH**

**Status:** ✅ Migration bereits erstellt  
**Datei:** `migrations/add_whatsapp_verkauf_support_tag211.sql`

**Aufgaben:**
- [ ] Migration auf lokaler/Test-DB ausführen
- [ ] Views testen (`v_whatsapp_verkauf_chats`, `v_whatsapp_verkauf_messages`)
- [ ] Trigger testen (Unread-Count automatisch aktualisieren)
- [ ] Daten-Validierung (Kontakte, Nachrichten)

**Vorteil:**
- ✅ DB-Struktur ist fertig, wenn DMZ steht
- ✅ Kann lokal getestet werden
- ✅ Keine Abhängigkeit von öffentlicher URL

**Aufwand:** ~30 Minuten

---

### **2. Lokales Webhook-Testing (Ngrok/Tunnelmole)** ⭐⭐⭐⭐ **HOCH**

**Status:** ⏳ Noch nicht getestet

**Aufgaben:**
- [ ] Ngrok oder Tunnelmole installieren
- [ ] Lokalen Tunnel starten (`ngrok http 5000`)
- [ ] Twilio Sandbox mit Tunnel-URL konfigurieren
- [ ] Webhook-Endpoint testen (Signatur-Validierung)
- [ ] Eingehende Nachrichten testen
- [ ] Status-Updates testen

**Vorteil:**
- ✅ Webhook funktioniert, bevor DMZ steht
- ✅ Sicherheitsmaßnahmen können getestet werden
- ✅ Twilio-Setup kann abgeschlossen werden

**Aufwand:** ~1-2 Stunden

**Anleitung:** Siehe `docs/TWILIO_WEBHOOK_URL_LOESUNG_TAG211.md`

---

### **3. Chat-Interface Template erstellen** ⭐⭐⭐ **MITTEL**

**Status:** ⏳ Noch nicht implementiert

**Aufgaben:**
- [ ] Template erstellen: `templates/whatsapp/verkauf_chat.html`
- [ ] Zwei-Spalten-Layout (Kontakte links, Chat rechts)
- [ ] Chat-Nachrichten anzeigen (chronologisch)
- [ ] Eingabefeld für Nachrichten
- [ ] Status-Anzeige (gesendet, zugestellt, gelesen)
- [ ] Ungelesene Badges (rote Punkte)

**Vorteil:**
- ✅ UI ist fertig, wenn DMZ steht
- ✅ Kann lokal getestet werden (mit Mock-Daten)
- ✅ Keine Abhängigkeit von Twilio

**Aufwand:** ~4-6 Stunden

**Referenz:** Siehe `docs/WHATSAPP_UI_FRONTEND_PLAN_TAG211.md`

---

### **4. API-Endpoints für Verkäufer erweitern** ⭐⭐⭐ **MITTEL**

**Status:** ⏳ Noch nicht implementiert

**Aufgaben:**
- [ ] Route: `/whatsapp/verkauf/chats` - Liste der Chats
- [ ] Route: `/whatsapp/verkauf/messages/<contact_id>` - Chat-Verlauf
- [ ] Route: `/whatsapp/verkauf/send` - Nachricht senden
- [ ] Route: `/whatsapp/verkauf/updates` - Neue Nachrichten (AJAX)
- [ ] User-Filterung (nur eigene Chats)
- [ ] Channel-Filterung (nur 'verkauf')

**Vorteil:**
- ✅ API ist fertig, wenn DMZ steht
- ✅ Kann lokal getestet werden (mit Mock-Daten)
- ✅ Frontend kann sofort verwendet werden

**Aufwand:** ~2-3 Stunden

**Referenz:** Siehe `docs/WHATSAPP_VERKAEUFER_INTEGRATION_TAG211.md`

---

### **5. Verkäufer-Dashboard Template** ⭐⭐ **NIEDRIG**

**Status:** ⏳ Noch nicht implementiert

**Aufgaben:**
- [ ] Template erstellen: `templates/whatsapp/verkauf_dashboard.html`
- [ ] Statistik-Karten (Ungelesen, Aktive Chats, Heute)
- [ ] Chat-Liste (Meine Chats)
- [ ] Schnellzugriff (häufige Kontakte)

**Vorteil:**
- ✅ Dashboard ist fertig, wenn DMZ steht
- ✅ Kann lokal getestet werden

**Aufwand:** ~2-3 Stunden

---

### **6. Twilio-Setup abschließen** ⭐⭐⭐⭐ **HOCH**

**Status:** ⏳ Teilweise erledigt (Sandbox verbunden)

**Aufgaben:**
- [ ] Twilio Sandbox testen (Nachrichten senden/empfangen)
- [ ] Produktions-Nummer beantragen (falls gewünscht)
- [ ] `.env` Datei finalisieren (Credentials)
- [ ] Webhook-URL in Twilio konfigurieren (später: DMZ-URL)

**Vorteil:**
- ✅ Twilio ist fertig, wenn DMZ steht
- ✅ Kann mit Sandbox getestet werden

**Aufwand:** ~1-2 Stunden

**Referenz:** Siehe `docs/TWILIO_SETUP_ANLEITUNG_TAG211.md`

---

### **7. Feature-Zugriff konfigurieren** ⭐⭐⭐ **MITTEL**

**Status:** ⏳ Noch nicht konfiguriert

**Aufgaben:**
- [ ] `config/roles_config.py` erweitern:
  - `whatsapp_teile` - Für Teile-Handel
  - `whatsapp_verkauf` - Für Verkäufer
- [ ] Rollen zuordnen (Verkäufer → `whatsapp_verkauf`)
- [ ] Navigation erweitern (WhatsApp-Menü)

**Vorteil:**
- ✅ Berechtigungen sind fertig, wenn DMZ steht
- ✅ Kann lokal getestet werden

**Aufwand:** ~30 Minuten

---

## 📋 PRIORISIERUNG

### **Sofort (vor DMZ):**

1. **DB-Migration ausführen** ⭐⭐⭐⭐
   - ✅ Keine Abhängigkeiten
   - ✅ Kann sofort gemacht werden
   - ✅ Basis für alles weitere

2. **Lokales Webhook-Testing** ⭐⭐⭐⭐
   - ✅ Twilio-Setup abschließen
   - ✅ Sicherheitsmaßnahmen testen
   - ✅ Webhook funktioniert, bevor DMZ steht

3. **Twilio-Setup abschließen** ⭐⭐⭐⭐
   - ✅ Sandbox testen
   - ✅ Credentials finalisieren

---

### **Parallel (während DMZ-Einrichtung):**

4. **Chat-Interface Template** ⭐⭐⭐
   - ✅ UI ist fertig, wenn DMZ steht
   - ✅ Kann mit Mock-Daten getestet werden

5. **API-Endpoints erweitern** ⭐⭐⭐
   - ✅ Backend ist fertig, wenn DMZ steht
   - ✅ Kann mit Mock-Daten getestet werden

6. **Feature-Zugriff konfigurieren** ⭐⭐⭐
   - ✅ Berechtigungen sind fertig
   - ✅ Navigation erweitert

---

### **Später (nach DMZ):**

7. **Verkäufer-Dashboard** ⭐⭐
   - ✅ Nice-to-have
   - ✅ Kann später implementiert werden

---

## 🎯 EMPFOHLENE REIHENFOLGE

### **Phase 1: Basis (Sofort)**

1. ✅ DB-Migration ausführen (~30 Min)
2. ✅ Twilio-Setup abschließen (~1-2 Std)
3. ✅ Lokales Webhook-Testing (~1-2 Std)

**Ergebnis:** Webhook funktioniert lokal, Twilio ist fertig

---

### **Phase 2: Frontend/Backend (Parallel zu DMZ)**

4. ✅ Chat-Interface Template (~4-6 Std)
5. ✅ API-Endpoints erweitern (~2-3 Std)
6. ✅ Feature-Zugriff konfigurieren (~30 Min)

**Ergebnis:** UI und API sind fertig, wenn DMZ steht

---

### **Phase 3: Finalisierung (Nach DMZ)**

7. ✅ Webhook-URL in Twilio auf DMZ-URL ändern
8. ✅ Produktions-Testing
9. ✅ Verkäufer-Dashboard (optional)

**Ergebnis:** Vollständig funktionsfähig

---

## 📊 GESAMTAUFWAND

| Phase | Aufgaben | Aufwand |
|-------|----------|---------|
| **Phase 1** | DB-Migration, Twilio, Webhook-Testing | ~3-5 Stunden |
| **Phase 2** | Chat-Interface, API-Endpoints, Feature-Zugriff | ~7-10 Stunden |
| **Phase 3** | DMZ-Integration, Testing, Dashboard | ~2-3 Stunden |
| **Gesamt** | | **~12-18 Stunden** |

---

## ✅ CHECKLISTE

### **Sofort (vor DMZ):**

- [ ] DB-Migration ausführen
- [ ] Twilio Sandbox testen
- [ ] Lokales Webhook-Testing (Ngrok/Tunnelmole)
- [ ] `.env` Datei finalisieren

### **Parallel (während DMZ):**

- [ ] Chat-Interface Template erstellen
- [ ] API-Endpoints für Verkäufer erweitern
- [ ] Feature-Zugriff konfigurieren
- [ ] Navigation erweitern

### **Nach DMZ:**

- [ ] Webhook-URL in Twilio auf DMZ-URL ändern
- [ ] Produktions-Testing
- [ ] Verkäufer-Dashboard (optional)

---

**Status:** 📋 Vorarbeiten geplant  
**Nächster Schritt:** DB-Migration ausführen und Twilio-Setup abschließen
