# WhatsApp UI/Frontend - Plan

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 🎨 **UI/FRONTEND-PLAN**

---

## 🎯 AKTUELLER STAND

### **Bereits implementiert:**

✅ **Basis-UI:**
- `/whatsapp/messages` - Nachrichten-Liste (alle Nachrichten)
- `/whatsapp/contacts` - Kontakte verwalten
- Modal zum Senden von Nachrichten

✅ **Features:**
- Nachrichten anzeigen (chronologisch)
- Kontakte anzeigen (Liste)
- Nachricht senden (Modal)
- Status-Anzeige (gesendet, zugestellt, gelesen)

---

## 🎨 GEPLANTE UI-FEATURES

### **1. Chat-Interface (WhatsApp-ähnlich)** ⭐⭐⭐⭐ **EMPFOHLEN**

**Ziel:** WhatsApp-ähnliches Chat-Interface für Verkäufer

**Layout:**
```
┌─────────────────────────────────────────────┐
│  WhatsApp - Verkauf              [⚙️] [🔍] │
├──────────────┬──────────────────────────────┤
│ Kontakte     │ Chat-Fenster                │
│              │                              │
│ 🔴 [Kunde1]  │ ┌────────────────────────┐ │
│    Letzte... │ │ Kunde1                  │ │
│              │ │ +49 123 4567890         │ │
│ [Kunde2]     │ └────────────────────────┘ │
│    Hallo...  │                              │
│              │ ┌────────────────────────┐ │
│ [Kunde3]     │ │ Kunde1:                │ │
│              │ │ Hallo, ich interessiere │ │
│              │ │ mich für Fahrzeug XYZ   │ │
│              │ │ 10:30                   │ │
│              │ └────────────────────────┘ │
│              │                              │
│              │ ┌────────────────────────┐ │
│              │ │ Du:                    │ │
│              │ │ Gern, ich schicke...   │ │
│              │ │ ✓✓ 10:32               │ │
│              │ └────────────────────────┘ │
│              │                              │
│              │ ┌────────────────────────┐ │
│              │ │ [📎] [📷] Nachricht... │ │
│              │ │              [Senden]  │ │
│              │ └────────────────────────┘ │
└──────────────┴──────────────────────────────┘
```

**Features:**
- ✅ **Zwei-Spalten-Layout** (Kontakte links, Chat rechts)
- ✅ **Chat-Verlauf** (Nachrichten chronologisch, wie WhatsApp)
- ✅ **Eingabefeld** (Text, Bild-Upload, Emoji)
- ✅ **Status-Anzeige** (gesendet ✓, zugestellt ✓✓, gelesen ✓✓)
- ✅ **Timestamps** (relative Zeit: "vor 5 Min", "heute 10:30")
- ✅ **Ungelesene Badges** (rote Punkte bei unread_count > 0)
- ✅ **Bild-Vorschau** (Thumbnails für Bilder)
- ✅ **Responsive** (Mobile-optimiert)

---

### **2. Verkäufer-Dashboard**

**Ziel:** Übersicht für Verkäufer

**Layout:**
```
┌─────────────────────────────────────────────┐
│  WhatsApp Verkauf - Dashboard              │
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 🔴 5      │  │ 📞 12    │  │ ⏰ 3     │  │
│  │ Ungelesen │  │ Aktive   │  │ Heute   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│                                              │
│  Meine Chats:                                │
│  ┌────────────────────────────────────────┐ │
│  │ 🔴 Kunde1 - "Hallo, ich interessiere..."│ │
│  │    10:30                               │ │
│  ├────────────────────────────────────────┤ │
│  │ Kunde2 - "Vielen Dank für..."         │ │
│  │    09:15                               │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  Schnellzugriff:                             │
│  [Kunde A] [Kunde B] [Kunde C]              │
└──────────────────────────────────────────────┘
```

**Features:**
- ✅ **Statistik-Karten** (Ungelesen, Aktive Chats, Heute)
- ✅ **Meine Chats** (Liste der eigenen Chats)
- ✅ **Schnellzugriff** (häufige Kontakte)
- ✅ **Filter** (Ungelesen, Heute, Diese Woche)

---

### **3. Kontakt-Verwaltung (erweitert)**

**Ziel:** Kunden-Kontakte verwalten

**Features:**
- ✅ **Kunden hinzufügen** (Name, Telefonnummer, E-Mail)
- ✅ **Zuständigkeit** (Dropdown: Welcher Verkäufer)
- ✅ **Notizen** (Kunden-Info, Fahrzeug-Interesse, etc.)
- ✅ **Verknüpfung** (mit Fahrzeug-Bestand, Aufträgen)
- ✅ **Kontakt-Typ** (Workshop vs. Kunde)
- ✅ **Suchfunktion** (nach Name, Telefonnummer)

---

### **4. Echtzeit-Updates**

**Ziel:** Neue Nachrichten automatisch anzeigen

**Optionen:**
- **AJAX Polling** (alle 5 Sekunden prüfen)
- **WebSocket** (echte Echtzeit, komplexer)
- **Server-Sent Events** (SSE, einfacher als WebSocket)

**Empfehlung:** AJAX Polling (einfach, ausreichend)

---

### **5. Bild-Upload**

**Ziel:** Bilder direkt im Chat senden

**Features:**
- ✅ **Drag & Drop** (Bild in Chat-Fenster ziehen)
- ✅ **Datei-Auswahl** (Button zum Auswählen)
- ✅ **Vorschau** (Bild vor dem Senden anzeigen)
- ✅ **Upload-Progress** (Fortschrittsbalken)
- ✅ **Thumbnail** (Bilder als Thumbnails im Chat)

---

### **6. Mobile-Ansicht**

**Ziel:** Optimiert für Smartphones

**Features:**
- ✅ **Responsive Design** (Bootstrap 5)
- ✅ **Touch-optimiert** (große Buttons, Swipe-Gesten)
- ✅ **Vollbild-Chat** (Chat nimmt ganzen Bildschirm)
- ✅ **Bottom-Navigation** (Kontakte, Chats, Einstellungen)

---

## 📊 IMPLEMENTIERUNGS-PLAN

### **Phase 1: Basis-Chat-Interface** (4-6 Stunden)

**Aufgaben:**
1. **Template erstellen:** `templates/whatsapp/verkauf_chat.html`
2. **Zwei-Spalten-Layout** (Bootstrap Grid)
3. **Chat-Verlauf anzeigen** (Nachrichten chronologisch)
4. **Eingabefeld** (Text, Senden-Button)
5. **Status-Anzeige** (gesendet, zugestellt, gelesen)

**Dateien:**
- `templates/whatsapp/verkauf_chat.html` (neu)
- `routes/whatsapp_routes.py` (Route hinzufügen)
- `api/whatsapp_api.py` (API-Endpoints)

---

### **Phase 2: Echtzeit-Updates** (2-3 Stunden)

**Aufgaben:**
1. **AJAX Polling** implementieren
2. **Neue Nachrichten** automatisch laden
3. **Unread-Count** aktualisieren
4. **Scroll zu neuer Nachricht** (automatisch)

**JavaScript:**
```javascript
// Polling alle 5 Sekunden
setInterval(function() {
    fetch('/whatsapp/verkauf/updates?last_message_id=' + lastMessageId)
        .then(response => response.json())
        .then(data => {
            if (data.new_messages.length > 0) {
                // Neue Nachrichten anzeigen
                appendMessages(data.new_messages);
            }
        });
}, 5000);
```

---

### **Phase 3: Bild-Upload** (2-3 Stunden)

**Aufgaben:**
1. **File-Input** hinzufügen
2. **Drag & Drop** implementieren
3. **Upload-Endpoint** erstellen
4. **Vorschau** anzeigen
5. **Thumbnail** im Chat anzeigen

---

### **Phase 4: Verkäufer-Dashboard** (2-3 Stunden)

**Aufgaben:**
1. **Template erstellen:** `templates/whatsapp/verkauf_dashboard.html`
2. **Statistik-Karten** (Ungelesen, Aktive Chats)
3. **Chat-Liste** (Meine Chats)
4. **Schnellzugriff** (häufige Kontakte)

---

### **Phase 5: Mobile-Ansicht** (2-3 Stunden)

**Aufgaben:**
1. **Responsive Design** optimieren
2. **Touch-Gesten** (Swipe, etc.)
3. **Vollbild-Chat** (Mobile)
4. **Bottom-Navigation** (Mobile)

---

## 📋 GESAMTAUFWAND

| Phase | Aufwand | Priorität |
|-------|---------|-----------|
| **Basis-Chat-Interface** | 4-6h | ⭐⭐⭐⭐ Hoch |
| **Echtzeit-Updates** | 2-3h | ⭐⭐⭐⭐ Hoch |
| **Bild-Upload** | 2-3h | ⭐⭐⭐ Mittel |
| **Verkäufer-Dashboard** | 2-3h | ⭐⭐⭐ Mittel |
| **Mobile-Ansicht** | 2-3h | ⭐⭐ Niedrig |
| **Testing** | 2-3h | ⭐⭐⭐⭐ Hoch |
| **Gesamt** | **~14-21h** | |

---

## 🎨 UI-KOMPONENTEN

### **Chat-Message-Komponente:**

```html
<div class="message message-inbound">
    <div class="message-header">
        <span class="message-sender">Kunde1</span>
        <span class="message-time">10:30</span>
    </div>
    <div class="message-content">
        Hallo, ich interessiere mich für Fahrzeug XYZ
    </div>
</div>

<div class="message message-outbound">
    <div class="message-header">
        <span class="message-sender">Du</span>
        <span class="message-time">10:32</span>
        <span class="message-status">✓✓</span>
    </div>
    <div class="message-content">
        Gern, ich schicke Ihnen gerne weitere Informationen.
    </div>
</div>
```

---

### **Kontakt-Liste:**

```html
<div class="contact-item unread">
    <div class="contact-avatar">K</div>
    <div class="contact-info">
        <div class="contact-name">Kunde1</div>
        <div class="contact-preview">Hallo, ich interessiere...</div>
    </div>
    <div class="contact-meta">
        <span class="contact-time">10:30</span>
        <span class="unread-badge">5</span>
    </div>
</div>
```

---

## 🔐 BERECHTIGUNGEN

### **Feature-Zugriff:**

**In `config/roles_config.py`:**
```python
FEATURE_ACCESS = {
    'whatsapp_teile': ['admin', 'lager', 'werkstatt_leitung'],
    'whatsapp_verkauf': ['admin', 'verkauf_leitung', 'verkauf'],
}
```

**Zugriff:**
- **Verkäufer:** Nur eigene Chats
- **Verkaufsleitung:** Alle Verkaufs-Chats
- **Admin:** Alle Chats (Teile + Verkauf)

---

## 📋 CHECKLISTE

### **UI-Implementierung:**

- [ ] Chat-Interface erstellen
- [ ] Verkäufer-Dashboard erstellen
- [ ] Echtzeit-Updates implementieren
- [ ] Bild-Upload implementieren
- [ ] Mobile-Ansicht optimieren
- [ ] Testing durchführen

---

**Status:** 🎨 UI/Frontend-Plan abgeschlossen  
**Empfehlung:** Schrittweise Implementierung (Phase 1 → 2 → 3)  
**Aufwand:** ~14-21 Stunden für vollständige UI
