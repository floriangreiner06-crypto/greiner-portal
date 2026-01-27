# Separate WhatsApp-Channel für Teile-Bereich

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 📊 **LÖSUNGSVORSCHLAG**

---

## 🎯 ANFORDERUNGEN

**Aktuelle Situation:**
- ✅ MessengerPeople bereits auf Homepage integriert (www.auto-greiner.de)
- ✅ WhatsApp-Nachrichten werden an CRM-System weitergeleitet (Leads)
- ✅ Funktioniert für Kunden-Kommunikation

**Neue Anforderung:**
- 🔄 **Separate WhatsApp-Nummer** für Teile-Bereich
- 🔄 **Eigener WhatsApp-Button** auf Homepage (nur für Teile)
- ⚠️ **Bestehende Lösung darf NICHT kompromittiert werden**

---

## 💡 LÖSUNGSANSATZ

### **Option 1: Separater MessengerPeople Channel** ⭐⭐⭐ **EMPFOHLEN**

**Wie es funktioniert:**
1. **Neuer Channel in MessengerPeople** - Separate WhatsApp-Nummer für Teile
2. **Separater Webhook-Endpoint** - Eigener Webhook für Teile-Channel
3. **Filterung im Webhook** - Nur Nachrichten vom Teile-Channel verarbeiten
4. **Separater Button auf Homepage** - Verlinkt auf Teile-Channel

**Vorteile:**
- ✅ **Vollständig getrennt** - Keine Beeinträchtigung der bestehenden Lösung
- ✅ **Eigene Nummer** - Separate WhatsApp-Nummer für Teile
- ✅ **Eigener Webhook** - Unabhängige Verarbeitung
- ✅ **Einfache Konfiguration** - In MessengerPeople Dashboard

**Nachteile:**
- ⚠️ **Zusätzliche Kosten** - Zweite Nummer/Channel
- ⚠️ **Zwei Webhooks** - Zwei Endpoints zu verwalten

---

### **Option 2: Channel-Filterung im Webhook** ⭐⭐ **ALTERNATIVE**

**Wie es funktioniert:**
1. **Gleicher Channel** - Nutzt bestehenden Channel
2. **Filterung im Webhook** - Prüft Nachrichteninhalt oder Absender
3. **Routing** - Leitet an CRM oder DRIVE weiter

**Vorteile:**
- ✅ **Keine zusätzlichen Kosten** - Nutzt bestehenden Channel
- ✅ **Ein Webhook** - Ein Endpoint

**Nachteile:**
- ❌ **Komplexere Filterung** - Muss Nachrichten unterscheiden
- ❌ **Fehleranfällig** - Falsche Zuordnung möglich
- ❌ **Gleiche Nummer** - Keine separate Nummer

**Nicht empfohlen** - Zu fehleranfällig!

---

## 🚀 EMPFOHLENE LÖSUNG: Separater Channel

### **Schritt 1: Neuer Channel in MessengerPeople**

1. **MessengerPeople Dashboard** → Channels
2. **Neuen WhatsApp-Channel erstellen**
3. **Separate WhatsApp-Nummer zuweisen**
4. **Channel-ID notieren** (für DRIVE-Konfiguration)

### **Schritt 2: Separater Webhook für DRIVE**

**Neuer Webhook-Endpoint:**
- **URL:** `https://auto-greiner.de/whatsapp/teile/webhook`
- **Channel:** Nur Teile-Channel
- **Events:** `message`, `status`

**Bestehender Webhook (unverändert):**
- **URL:** `https://auto-greiner.de/whatsapp/webhook` (oder bestehender CRM-Webhook)
- **Channel:** Bestehender Kunden-Channel
- **Events:** `message`, `status`

### **Schritt 3: Code-Anpassung in DRIVE**

**Neue Route für Teile-Webhook:**
```python
@whatsapp_bp.route('/teile/webhook', methods=['GET', 'POST'])
def teile_webhook():
    """Separater Webhook für Teile-Channel"""
    # Nur Nachrichten vom Teile-Channel verarbeiten
    # Filterung über channel_id im Webhook-Event
```

**Konfiguration:**
```bash
# Bestehende Konfiguration (unverändert)
MESSENGERPEOPLE_API_KEY=...
MESSENGERPEOPLE_CHANNEL_ID=...  # Kunden-Channel

# Neue Konfiguration für Teile
MESSENGERPEOPLE_TEILE_CHANNEL_ID=...  # Teile-Channel
MESSENGERPEOPLE_TEILE_WEBHOOK_TOKEN=...
```

### **Schritt 4: Homepage-Integration**

**Bestehender Button (unverändert):**
- Verlinkt auf bestehenden Kunden-Channel
- Weiterleitung an CRM

**Neuer Button für Teile:**
```html
<!-- Neuer WhatsApp-Button für Teile -->
<a href="https://wa.me/DEINE_TEILE_NUMMER" 
   class="whatsapp-button-teile"
   target="_blank">
    <i class="whatsapp-icon"></i>
    WhatsApp Teile-Service
</a>
```

**Oder über MessengerPeople Widget:**
- Separates Widget für Teile-Channel
- Eigener Button auf Homepage

---

## 📋 IMPLEMENTIERUNG

### **1. Code-Anpassung: Separater Webhook**

**Neue Route in `routes/whatsapp_routes.py`:**

```python
@whatsapp_bp.route('/teile/webhook', methods=['GET', 'POST'])
def teile_webhook():
    """
    Separater Webhook für Teile-Channel.
    Verarbeitet nur Nachrichten vom Teile-Channel.
    """
    config = get_whatsapp_config()
    teile_channel_id = os.getenv('MESSENGERPEOPLE_TEILE_CHANNEL_ID', '')
    verify_token = config.get('webhook_token', '')
    
    if request.method == 'GET':
        # Webhook-Verifizierung
        token = request.args.get('token')
        challenge = request.args.get('challenge')
        
        if token == verify_token:
            logger.info("MessengerPeople Teile-Webhook erfolgreich verifiziert")
            return challenge or 'ok', 200
        return 'Verification failed', 403
    
    elif request.method == 'POST':
        # Eingehende Nachricht - nur vom Teile-Channel verarbeiten
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'status': 'ok'}), 200
            
            # Prüfe ob Nachricht vom Teile-Channel kommt
            sender = data.get('sender') or data.get('channel_id')
            if sender != teile_channel_id:
                logger.debug(f"Nachricht nicht vom Teile-Channel: {sender}")
                return jsonify({'status': 'ok'}), 200  # Ignorieren, nicht verarbeiten
            
            # Verarbeite nur Nachrichten vom Teile-Channel
            if data.get('type') == 'message':
                _handle_incoming_message_mp(data)
            elif data.get('type') == 'status':
                _handle_status_update_mp(data)
            
            return jsonify({'status': 'ok'}), 200
            
        except Exception as e:
            logger.error(f"Fehler im Teile-Webhook: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
```

### **2. Separater Client für Teile**

**Neue Klasse in `api/whatsapp_api.py`:**

```python
class WhatsAppTeileClient(WhatsAppClient):
    """
    Client für Teile-Channel (separater Channel).
    """
    
    def __init__(self):
        super().__init__()
        # Überschreibe Channel ID mit Teile-Channel
        self.channel_id = os.getenv('MESSENGERPEOPLE_TEILE_CHANNEL_ID', '')
        
        if not self.channel_id:
            logger.warning("Teile-Channel-ID nicht konfiguriert")
```

### **3. Konfiguration**

**`.env` erweitern:**

```bash
# Bestehende Konfiguration (Kunden-Channel) - UNVERÄNDERT
MESSENGERPEOPLE_API_URL=https://rest.messengerpeople.com/api/v17
MESSENGERPEOPLE_API_KEY=DEIN_API_KEY
MESSENGERPEOPLE_CHANNEL_ID=KUNDEN_CHANNEL_ID  # Bestehend, unverändert
MESSENGERPEOPLE_WEBHOOK_URL=https://auto-greiner.de/whatsapp/webhook  # Bestehend

# Neue Konfiguration für Teile-Channel
MESSENGERPEOPLE_TEILE_CHANNEL_ID=TEILE_CHANNEL_ID  # NEU
MESSENGERPEOPLE_TEILE_WEBHOOK_TOKEN=teile_webhook_token
MESSENGERPEOPLE_TEILE_WEBHOOK_URL=https://auto-greiner.de/whatsapp/teile/webhook
```

---

## ✅ SICHERHEIT & ISOLATION

### **Garantierte Trennung:**

1. **Separate Channels** - Physikalisch getrennt
2. **Separate Webhooks** - Unterschiedliche Endpoints
3. **Channel-Filterung** - Webhook prüft Channel-ID
4. **Separate Konfiguration** - Eigene Channel-IDs

### **Bestehende Lösung bleibt unverändert:**

- ✅ Bestehender Webhook bleibt unverändert
- ✅ Bestehender Channel bleibt unverändert
- ✅ CRM-Integration bleibt unverändert
- ✅ Homepage-Button bleibt unverändert

---

## 📊 ARCHITEKTUR-ÜBERSICHT

```
┌─────────────────────────────────────────────────────────┐
│                    Homepage                               │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │ WhatsApp Button  │      │ WhatsApp Button  │        │
│  │   (Kunden)       │      │   (Teile)       │        │
│  └────────┬─────────┘      └────────┬─────────┘        │
└───────────┼──────────────────────────┼──────────────────┘
            │                          │
            │                          │
┌───────────▼──────────────────────────▼──────────────────┐
│              MessengerPeople                            │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │ Kunden-Channel   │      │ Teile-Channel    │        │
│  │ (bestehend)      │      │ (NEU)            │        │
│  └────────┬─────────┘      └────────┬─────────┘        │
└───────────┼──────────────────────────┼──────────────────┘
            │                          │
            │                          │
┌───────────▼──────────┐      ┌────────▼──────────────────┐
│   CRM-System         │      │   DRIVE Portal            │
│   (bestehend)        │      │   /whatsapp/teile/webhook│
│   /whatsapp/webhook  │      │   (NEU)                   │
└──────────────────────┘      └───────────────────────────┘
```

---

## 🎯 FAZIT

**Ja, das geht!** ✅

**Lösung:**
- Separater MessengerPeople Channel für Teile
- Separater Webhook-Endpoint in DRIVE
- Channel-Filterung im Webhook
- Bestehende Lösung bleibt unverändert

**Vorteile:**
- ✅ Vollständige Trennung
- ✅ Eigene WhatsApp-Nummer
- ✅ Keine Beeinträchtigung der bestehenden Lösung
- ✅ Einfache Konfiguration

**Nächste Schritte:**
1. Neuen Channel in MessengerPeople erstellen
2. Separaten Webhook-Endpoint implementieren
3. Konfiguration erweitern
4. Homepage-Button hinzufügen

---

**Status:** 📊 Lösungsvorschlag erstellt  
**Empfehlung:** Separater Channel (Option 1)
