# WhatsApp Integration für Verkäufer - Plan

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 📋 **PLANUNG**

---

## 🎯 ANFORDERUNGEN

**Aktuell:**
- ✅ WhatsApp-Integration für **Teile-Handel** (externe Werkstätten)
- ✅ Basis-UI vorhanden (Nachrichten-Liste, Kontakte)

**Neu:**
- 🔄 WhatsApp für **Verkäufer** (8 Mitarbeiter)
- 🔄 **Chat-Interface** ähnlich WhatsApp
- 🔄 **Multi-User-Support** (jeder Verkäufer sieht seine Chats)
- 🔄 **Kunden-Kommunikation** (nicht nur Werkstätten)

---

## 💡 LÖSUNGSANSATZ

### **Option 1: Separate WhatsApp-Nummer für Verkäufer** ⭐⭐⭐⭐ **EMPFOHLEN**

**Vorgehen:**
- **Separate Twilio WhatsApp-Nummer** für Verkäufer
- **Separate Kontakte** (Kunden, nicht Werkstätten)
- **Separate Nachrichten** (Verkauf vs. Teile)

**Vorteile:**
- ✅ **Vollständig getrennt** - Teile und Verkauf unabhängig
- ✅ **Eigene Nummer** - Kunden wissen, dass es für Verkauf ist
- ✅ **Einfache Filterung** - Nach Nummer trennen

**Nachteile:**
- ⚠️ **Zusätzliche Kosten** - Zweite Nummer (~€1-15/Monat)
- ⚠️ **Zwei Nummern** - Zwei Nummern zu verwalten

---

### **Option 2: Gleiche Nummer, Filterung nach Kontakt-Typ** ⭐⭐⭐

**Vorgehen:**
- **Gleiche WhatsApp-Nummer** für Teile und Verkauf
- **Kontakt-Typ** in DB: `workshop` vs. `customer`
- **Filterung** in UI nach Typ

**Vorteile:**
- ✅ **Eine Nummer** - Einfacher zu verwalten
- ✅ **Keine zusätzlichen Kosten**

**Nachteile:**
- ⚠️ **Verwechslung möglich** - Nicht klar, ob Teile oder Verkauf
- ⚠️ **Komplexere Filterung** - Muss nach Typ unterscheiden

---

## 🎯 EMPFEHLUNG: OPTION 1 (SEPARATE NUMMER)

**Warum:**
- ✅ Klare Trennung (Teile vs. Verkauf)
- ✅ Professionell (eigene Nummer für Verkauf)
- ✅ Geringe Kosten (~€1-15/Monat)
- ✅ Einfache Implementierung

---

## 📊 DATENBANK-ERWEITERUNG

### **Migration: User-Zuordnung + Kontakt-Typ**

**Neue Felder:**

1. **whatsapp_messages:**
   - `user_id` INTEGER (wer hat Nachricht gesendet/empfangen)
   - `channel_type` VARCHAR(20) ('teile' oder 'verkauf')

2. **whatsapp_contacts:**
   - `contact_type` VARCHAR(20) ('workshop' oder 'customer')
   - `assigned_user_id` INTEGER (welcher Verkäufer ist zuständig)

3. **Neue Tabelle: whatsapp_conversations:**
   - `id` SERIAL PRIMARY KEY
   - `contact_id` INTEGER
   - `user_id` INTEGER (zuständiger Verkäufer)
   - `channel_type` VARCHAR(20)
   - `last_message_at` TIMESTAMP
   - `unread_count` INTEGER

---

## 🎨 UI/FRONTEND PLAN

### **Aktuell vorhanden:**

✅ **Basis-UI:**
- `/whatsapp/messages` - Nachrichten-Liste
- `/whatsapp/contacts` - Kontakte verwalten
- Modal zum Senden von Nachrichten

✅ **Features:**
- Nachrichten anzeigen
- Kontakte anzeigen
- Nachricht senden (Modal)

---

### **Geplant für Verkäufer:**

#### **1. Chat-Interface (WhatsApp-ähnlich)** ⭐⭐⭐⭐ **EMPFOHLEN**

**Layout:**
```
┌─────────────────────────────────────┐
│  WhatsApp - Verkauf                │
├──────────┬──────────────────────────┤
│ Kontakte │ Chat-Fenster            │
│          │                          │
│ [Kunde1] │ [Kunde1]                 │
│ [Kunde2] │ Hallo, ich interessiere  │
│ [Kunde3] │ mich für...              │
│          │                          │
│          │ [Antwort]                │
│          │                          │
│          │ ┌──────────────────────┐ │
│          │ │ Nachricht eingeben...│ │
│          │ │ [📎] [📷] [Senden]  │ │
│          │ └──────────────────────┘ │
└──────────┴──────────────────────────┘
```

**Features:**
- ✅ **Zwei-Spalten-Layout** (Kontakte links, Chat rechts)
- ✅ **Echtzeit-Updates** (neue Nachrichten automatisch)
- ✅ **Bild-Upload** (Drag & Drop)
- ✅ **Status-Anzeige** (gesendet, zugestellt, gelesen)
- ✅ **Unread-Badges** (ungelesene Nachrichten)

---

#### **2. Verkäufer-Dashboard**

**Features:**
- ✅ **Meine Chats** (nur Chats des Verkäufers)
- ✅ **Ungelesene Nachrichten** (Badge mit Anzahl)
- ✅ **Neue Kontakte** (potenzielle Kunden)
- ✅ **Schnellzugriff** (häufige Kontakte)

---

#### **3. Kontakt-Verwaltung**

**Features:**
- ✅ **Kunden hinzufügen** (Name, Telefonnummer)
- ✅ **Zuständigkeit** (welcher Verkäufer)
- ✅ **Notizen** (Kunden-Info, Fahrzeug-Interesse)
- ✅ **Verknüpfung** (mit Fahrzeug-Bestand, Aufträgen)

---

#### **4. Mobile-Ansicht**

**Features:**
- ✅ **Responsive Design** (Smartphone-optimiert)
- ✅ **Touch-optimiert** (große Buttons)
- ✅ **Push-Benachrichtigungen** (neue Nachrichten)

---

## 🔧 TECHNISCHE UMSETZUNG

### **Phase 1: DB-Erweiterung**

**Migration:**
```sql
-- User-Zuordnung
ALTER TABLE whatsapp_messages 
ADD COLUMN user_id INTEGER REFERENCES users(id);

-- Kontakt-Typ
ALTER TABLE whatsapp_contacts 
ADD COLUMN contact_type VARCHAR(20) DEFAULT 'workshop' 
CHECK (contact_type IN ('workshop', 'customer'));

ALTER TABLE whatsapp_contacts 
ADD COLUMN assigned_user_id INTEGER REFERENCES users(id);

-- Conversations-Tabelle
CREATE TABLE whatsapp_conversations (...);
```

**Aufwand:** ~1 Stunde

---

### **Phase 2: API-Erweiterung**

**Neue Endpoints:**
- `GET /whatsapp/verkauf/chats` - Meine Chats (nur Verkäufer)
- `GET /whatsapp/verkauf/chat/{contact_id}` - Chat-Verlauf
- `POST /whatsapp/verkauf/send` - Nachricht senden (mit user_id)
- `GET /whatsapp/verkauf/unread` - Ungelesene Nachrichten

**Aufwand:** ~2-3 Stunden

---

### **Phase 3: UI-Implementierung**

**Neue Templates:**
- `templates/whatsapp/verkauf_chat.html` - Chat-Interface
- `templates/whatsapp/verkauf_dashboard.html` - Verkäufer-Dashboard

**Features:**
- Chat-Interface (Zwei-Spalten)
- Echtzeit-Updates (AJAX Polling oder WebSocket)
- Bild-Upload
- Mobile-Ansicht

**Aufwand:** ~4-6 Stunden

---

### **Phase 4: Multi-User-Support**

**Features:**
- User-Filterung (nur eigene Chats)
- Zuständigkeit (Kontakt zu Verkäufer zuordnen)
- Übergabe (Chat an anderen Verkäufer)

**Aufwand:** ~2-3 Stunden

---

## 📊 GESAMTAUFWAND

| Phase | Aufwand | Priorität |
|-------|---------|-----------|
| **DB-Erweiterung** | ~1h | ⭐⭐⭐⭐ Hoch |
| **API-Erweiterung** | ~2-3h | ⭐⭐⭐⭐ Hoch |
| **UI-Implementierung** | ~4-6h | ⭐⭐⭐⭐ Hoch |
| **Multi-User-Support** | ~2-3h | ⭐⭐⭐ Mittel |
| **Testing** | ~2-3h | ⭐⭐⭐⭐ Hoch |
| **Gesamt** | **~11-16h** | |

---

## 🎨 UI-MOCKUP

### **Chat-Interface:**

**Linke Spalte (Kontakte):**
- Liste aller Kunden-Kontakte
- Ungelesene Nachrichten (Badge)
- Letzte Nachricht (Vorschau)
- Sortierung: Zuletzt aktiv

**Rechte Spalte (Chat):**
- Chat-Verlauf (Nachrichten chronologisch)
- Eingabefeld (Text, Bild-Upload)
- Status-Anzeige (gesendet, zugestellt, gelesen)
- Timestamps

---

### **Verkäufer-Dashboard:**

**Karten:**
- **Ungelesene Nachrichten:** Anzahl + Liste
- **Neue Kontakte:** Heute hinzugefügt
- **Aktive Chats:** Letzte 24h
- **Schnellzugriff:** Häufige Kontakte

---

## 🔐 BERECHTIGUNGEN

### **Feature-Zugriff:**

**In `config/roles_config.py`:**
```python
FEATURE_ACCESS = {
    'whatsapp_teile': ['admin', 'lager', 'werkstatt_leitung'],  # Teile-Handel
    'whatsapp_verkauf': ['admin', 'verkauf_leitung', 'verkauf'],  # Verkauf
}
```

**Zugriff:**
- **Verkäufer:** Nur eigene Chats
- **Verkaufsleitung:** Alle Verkaufs-Chats
- **Admin:** Alle Chats (Teile + Verkauf)

---

## 📋 CHECKLISTE

### **DB-Erweiterung:**

- [ ] Migration erstellen (user_id, contact_type, conversations)
- [ ] Migration ausführen
- [ ] Views aktualisieren

### **API-Erweiterung:**

- [ ] User-Filterung implementieren
- [ ] Neue Endpoints erstellen
- [ ] Zuständigkeit (assigned_user_id) implementieren

### **UI-Implementierung:**

- [ ] Chat-Interface erstellen
- [ ] Verkäufer-Dashboard erstellen
- [ ] Echtzeit-Updates implementieren
- [ ] Mobile-Ansicht optimieren

### **Testing:**

- [ ] Multi-User testen
- [ ] Chat-Funktionalität testen
- [ ] Bild-Upload testen
- [ ] Mobile-Ansicht testen

---

## 💡 ERWEITERUNGS-MÖGLICHKEITEN

### **Kurzfristig:**

- ✅ **Fahrzeug-Verknüpfung** (Chat mit Fahrzeug-Bestand verknüpfen)
- ✅ **Automatische Antworten** (z.B. "Vielen Dank für Ihre Anfrage")
- ✅ **Vorlagen** (häufige Antworten als Vorlagen)

### **Mittelfristig:**

- 🔄 **E-Mail-Integration** (WhatsApp-Nachrichten als E-Mail weiterleiten)
- 🔄 **CRM-Verknüpfung** (Kontakte mit CRM synchronisieren)
- 🔄 **Analytics** (Chat-Statistiken, Response-Zeiten)

### **Langfristig:**

- 🔮 **KI-Unterstützung** (Automatische Antwort-Vorschläge)
- 🔮 **Chatbot** (Automatische Antworten auf häufige Fragen)
- 🔮 **Video-Chat** (über WhatsApp Video)

---

**Status:** 📋 Planung abgeschlossen  
**Empfehlung:** Separate WhatsApp-Nummer für Verkäufer  
**Aufwand:** ~11-16 Stunden für vollständige Implementierung
