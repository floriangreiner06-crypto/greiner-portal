# Analyse: MessengerPeople API-Einstellung & Migration zu Sinch

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** ⚠️ **KRITISCH - Service-Einstellung angekündigt**

---

## 🚨 WICHTIGE MITTEILUNG VON MESSENGERPEOPLE

**Kernpunkte:**
1. **Service-Ende:** `messengerpeople.dev` API wird am **31.12.2026** eingestellt
2. **Neue Channels:** **Keine neuen Channels** können nach **31.01.2026** hinzugefügt werden
3. **Alternative:** Sinch Conversation API wird empfohlen
4. **Support:** Neue Support-Form ab sofort

---

## 📊 AUSWIRKUNGEN AUF UNSERE PLANUNG

### **Kritische Punkte:**

#### **1. Neuer Teile-Channel** ⚠️ **ZEITKRITISCH**

**Problem:**
- Wir wollten einen **neuen Channel für Teile-Bereich** erstellen
- **Deadline:** 31.01.2026 (nur noch wenige Tage!)
- **Nach diesem Datum:** Keine neuen Channels mehr möglich

**Status:**
- ✅ **Noch möglich** (wenn vor 31.01.2026)
- ❌ **Nicht mehr möglich** (wenn nach 31.01.2026)

#### **2. Langfristige Nutzung** ⚠️ **MIGRATION NÖTIG**

**Problem:**
- Bestehender Kunden-Channel läuft bis **31.12.2026**
- **Danach:** Service wird eingestellt
- **Migration nötig:** Spätestens bis Ende 2026

**Status:**
- ✅ **Bis 31.12.2026:** Bestehende Channels funktionieren
- ⚠️ **Ab 2027:** Migration zu Sinch erforderlich

---

## 💡 HANDLUNGSOPTIONEN

### **Option 1: Schnell neuen Channel erstellen** ⚠️ **ZEITKRITISCH**

**Wenn wir VOR 31.01.2026 sind:**
1. ✅ **Sofort neuen Teile-Channel erstellen** (noch möglich)
2. ✅ **Bis 31.12.2026 nutzen** (fast 1 Jahr)
3. ⚠️ **2026 Migration zu Sinch planen**

**Vorteile:**
- ✅ Sofortige Lösung
- ✅ Fast 1 Jahr Nutzung möglich
- ✅ Zeit für Migration

**Nachteile:**
- ⚠️ Migration trotzdem nötig (2026)
- ⚠️ Zwei Migrations-Schritte (jetzt MessengerPeople, später Sinch)

---

### **Option 2: Direkt auf Sinch migrieren** ⭐⭐⭐ **EMPFOHLEN**

**Strategie:**
1. ✅ **Sofort Sinch Conversation API evaluieren**
2. ✅ **Direkt Sinch für Teile-Channel nutzen**
3. ✅ **Bestehenden Kunden-Channel später migrieren** (bis 31.12.2026)

**Vorteile:**
- ✅ **Zukunftssicher** - Keine erneute Migration nötig
- ✅ **Einheitliche Lösung** - Beide Channels auf Sinch
- ✅ **Moderne API** - Aktuellste Features
- ✅ **Längerfristige Planung** - Keine Deadline 2026

**Nachteile:**
- ⚠️ **Mehr Aufwand** - Code muss für Sinch angepasst werden
- ⚠️ **Zwei Systeme temporär** - MessengerPeople (Kunden) + Sinch (Teile)

---

### **Option 3: Bestehenden Channel teilen** ⭐ **NICHT EMPFOHLEN**

**Strategie:**
1. ❌ **Bestehenden Kunden-Channel auch für Teile nutzen**
2. ❌ **Filterung über Nachrichteninhalt**

**Nachteile:**
- ❌ **Keine separate Nummer** - Gleiche Nummer für Kunden und Teile
- ❌ **Fehleranfällig** - Falsche Zuordnung möglich
- ❌ **Nicht gewünscht** - User wollte separate Lösung

**Nicht empfohlen!**

---

## 🔍 SINCH CONVERSATION API ANALYSE

### **Was ist Sinch Conversation API?**

- **Nachfolger** von MessengerPeople API
- **Gleicher Anbieter** (Sinch hat MessengerPeople gekauft)
- **Ähnliche Funktionalität** - WhatsApp Business API
- **Moderne API** - Aktuellste Features

### **Vergleich: MessengerPeople vs. Sinch**

| Feature | MessengerPeople | Sinch Conversation API |
|---------|----------------|------------------------|
| **Service-Ende** | 31.12.2026 | ✅ Langfristig verfügbar |
| **Neue Channels** | ❌ Nur bis 31.01.2026 | ✅ Unbegrenzt |
| **API-Struktur** | REST API v17 | REST API (moderner) |
| **Multi-Channel** | ✅ Ja | ✅ Ja |
| **Support** | ⚠️ Eingeschränkt | ✅ Vollständig |
| **Migration** | ❌ Nicht nötig | ⚠️ Von MessengerPeople |

### **API-Unterschiede (vorläufig):**

**MessengerPeople:**
```
POST https://rest.messengerpeople.com/api/v17/messages
{
  "sender": "channel-id",
  "recipient": "491234567890",
  "payload": {"type": "text", "text": "..."}
}
```

**Sinch Conversation API (vermutlich ähnlich):**
```
POST https://conversation.api.sinch.com/v1/messages
{
  "channel": "whatsapp",
  "to": "491234567890",
  "message": {"text": "..."}
}
```

**Hinweis:** Exakte API-Struktur muss geprüft werden!

---

## 🎯 EMPFEHLUNG

### **Kurzfristig (sofort):**

**Wenn wir VOR 31.01.2026 sind:**
1. ✅ **Sofort neuen Teile-Channel in MessengerPeople erstellen**
2. ✅ **Bis Ende 2026 nutzen**
3. ✅ **Migration zu Sinch für 2026 planen**

**Wenn wir NACH 31.01.2026 sind:**
1. ✅ **Direkt Sinch Conversation API evaluieren**
2. ✅ **Sinch für Teile-Channel nutzen**
3. ✅ **Bestehenden Kunden-Channel später migrieren**

### **Langfristig (2026):**

1. ✅ **Migration zu Sinch planen**
2. ✅ **Beide Channels auf Sinch migrieren**
3. ✅ **Code für Sinch API anpassen**

---

## 📋 MIGRATIONSPLAN

### **Phase 1: Sofort (Januar 2026)**

**Option A: MessengerPeople (wenn noch möglich)**
- [ ] Neuen Teile-Channel erstellen (vor 31.01.2026)
- [ ] DRIVE-Integration fertigstellen
- [ ] Testen

**Option B: Sinch (wenn nicht mehr möglich)**
- [ ] Sinch Account erstellen
- [ ] Sinch Conversation API evaluieren
- [ ] Code für Sinch anpassen
- [ ] Teile-Channel in Sinch erstellen

### **Phase 2: 2026 (Migration)**

- [ ] Sinch Conversation API dokumentieren
- [ ] Code-Migration planen
- [ ] Bestehenden Kunden-Channel migrieren
- [ ] Teile-Channel migrieren (falls MessengerPeople)
- [ ] Testen und Go-Live

### **Phase 3: Ab 2027**

- [ ] Alle Channels auf Sinch
- [ ] MessengerPeople komplett abgelöst
- [ ] Langfristige Wartung

---

## ⚠️ KRITISCHE ENTSCHEIDUNG

### **Heute (26.01.2026):**

**Status:** ⚠️ **Nur noch 5 Tage bis 31.01.2026!**

**Entscheidung nötig:**
1. **Schnell neuen Channel in MessengerPeople erstellen?** (noch möglich)
2. **Oder direkt Sinch evaluieren?** (zukunftssicherer)

### **Empfehlung:**

**Wenn möglich (vor 31.01.2026):**
- ✅ **Sofort neuen Channel erstellen** (5 Tage Zeit!)
- ✅ **Bis Ende 2026 nutzen**
- ✅ **Migration für 2026 planen**

**Wenn nicht möglich (nach 31.01.2026):**
- ✅ **Direkt Sinch nutzen**
- ✅ **Zukunftssichere Lösung**

---

## 📚 NÄCHSTE SCHRITTE

### **Sofort (heute):**

1. **Prüfen:** Sind wir noch vor 31.01.2026? ✅ **JA (26.01.2026)**
2. **Entscheiden:** MessengerPeople oder Sinch?
3. **Handeln:** Entweder Channel erstellen ODER Sinch evaluieren

### **Diese Woche:**

1. **MessengerPeople:**
   - [ ] Neuen Teile-Channel erstellen
   - [ ] Channel-ID notieren
   - [ ] DRIVE-Integration abschließen

2. **ODER Sinch:**
   - [ ] Sinch Account erstellen
   - [ ] API-Dokumentation prüfen
   - [ ] Code-Anpassung planen

### **2026 (Migration):**

1. [ ] Sinch Conversation API evaluieren
2. [ ] Migrationsplan erstellen
3. [ ] Code anpassen
4. [ ] Beide Channels migrieren

---

## 🎯 FAZIT

**Situation:**
- ⚠️ **MessengerPeople wird eingestellt** (31.12.2026)
- ⚠️ **Neue Channels nur bis 31.01.2026** (nur noch 5 Tage!)
- ✅ **Sinch Conversation API als Alternative**

**Empfehlung:**
1. **Kurzfristig:** Neuen Channel in MessengerPeople erstellen (wenn noch möglich)
2. **Langfristig:** Migration zu Sinch planen (2026)

**Kritisch:**
- ⏰ **Nur noch 5 Tage** bis Deadline für neue Channels!
- ⚠️ **Schnelle Entscheidung nötig**

---

**Status:** ⚠️ **KRITISCH - Sofortige Entscheidung nötig**  
**Deadline:** 31.01.2026 (nur noch 5 Tage!)  
**Empfehlung:** Schnell Channel erstellen ODER direkt Sinch evaluieren
