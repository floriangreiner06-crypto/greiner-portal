-- ============================================================================
-- MIGRATION: WhatsApp Verkäufer-Support
-- ============================================================================
-- Erstellt: 2026-01-26 (TAG 211)
-- Zweck: Multi-User-Support für Verkäufer (8 Mitarbeiter)
-- ============================================================================

-- 1. User-Zuordnung für Nachrichten
ALTER TABLE whatsapp_messages 
ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- Index für schnelle User-Lookups
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_user 
ON whatsapp_messages(user_id);

-- 2. Channel-Typ (Teile vs. Verkauf)
ALTER TABLE whatsapp_messages 
ADD COLUMN IF NOT EXISTS channel_type VARCHAR(20) DEFAULT 'teile' 
CHECK (channel_type IN ('teile', 'verkauf'));

CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_channel_type 
ON whatsapp_messages(channel_type);

-- 3. Kontakt-Typ (Werkstatt vs. Kunde)
ALTER TABLE whatsapp_contacts 
ADD COLUMN IF NOT EXISTS contact_type VARCHAR(20) DEFAULT 'workshop' 
CHECK (contact_type IN ('workshop', 'customer'));

-- 4. Zuständiger Verkäufer (für Kunden-Kontakte)
ALTER TABLE whatsapp_contacts 
ADD COLUMN IF NOT EXISTS assigned_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_assigned_user 
ON whatsapp_contacts(assigned_user_id);

-- 5. Conversations-Tabelle (für Chat-Management)
CREATE TABLE IF NOT EXISTS whatsapp_conversations (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES whatsapp_contacts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    channel_type VARCHAR(20) NOT NULL DEFAULT 'verkauf' 
        CHECK (channel_type IN ('teile', 'verkauf')),
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_id INTEGER REFERENCES whatsapp_messages(id) ON DELETE SET NULL,
    unread_count INTEGER DEFAULT 0,
    is_archived BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contact_id, user_id, channel_type)
);

-- Index für schnelle Lookups
CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_user 
ON whatsapp_conversations(user_id);

CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_contact 
ON whatsapp_conversations(contact_id);

CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_channel_type 
ON whatsapp_conversations(channel_type);

CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_last_message 
ON whatsapp_conversations(last_message_at DESC);

-- 6. View: Verkäufer-Chats (nur eigene Chats)
CREATE OR REPLACE VIEW v_whatsapp_verkauf_chats AS
SELECT 
    c.id as conversation_id,
    c.contact_id,
    c.user_id,
    c.channel_type,
    c.last_message_at,
    c.unread_count,
    c.is_archived,
    cont.workshop_name as contact_name,
    cont.phone_number,
    cont.contact_name as contact_person,
    cont.contact_type,
    cont.assigned_user_id,
    m.content as last_message_preview,
    m.message_type as last_message_type,
    m.created_at as last_message_created_at
FROM whatsapp_conversations c
LEFT JOIN whatsapp_contacts cont ON c.contact_id = cont.id
LEFT JOIN whatsapp_messages m ON c.last_message_id = m.id
WHERE c.channel_type = 'verkauf'
ORDER BY c.last_message_at DESC;

-- 7. View: Verkäufer-Nachrichten (nur eigene Nachrichten)
CREATE OR REPLACE VIEW v_whatsapp_verkauf_messages AS
SELECT 
    m.*,
    c.workshop_name as contact_name,
    c.phone_number,
    c.contact_name as contact_person,
    c.contact_type,
    c.assigned_user_id,
    u.username,
    u.display_name
FROM whatsapp_messages m
LEFT JOIN whatsapp_contacts c ON m.contact_id = c.id
LEFT JOIN users u ON m.user_id = u.id
WHERE m.channel_type = 'verkauf'
ORDER BY m.created_at DESC;

-- 8. Funktion: Unread-Count aktualisieren
CREATE OR REPLACE FUNCTION update_conversation_unread_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE whatsapp_conversations
    SET 
        unread_count = (
            SELECT COUNT(*)
            FROM whatsapp_messages
            WHERE contact_id = NEW.contact_id
                AND direction = 'inbound'
                AND status != 'read'
                AND channel_type = NEW.channel_type
                AND (user_id = NEW.user_id OR user_id IS NULL)
        ),
        last_message_at = NEW.created_at,
        last_message_id = NEW.id,
        updated_at = CURRENT_TIMESTAMP
    WHERE contact_id = NEW.contact_id
        AND channel_type = NEW.channel_type
        AND (user_id = NEW.user_id OR (NEW.user_id IS NULL AND user_id IS NULL));
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Automatisch Unread-Count aktualisieren
DROP TRIGGER IF EXISTS trigger_update_conversation_unread ON whatsapp_messages;
CREATE TRIGGER trigger_update_conversation_unread
    AFTER INSERT ON whatsapp_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_unread_count();

-- ============================================================================
-- KONTROLLE
-- ============================================================================
-- Nach Migration ausführen:
-- SELECT * FROM whatsapp_conversations;
-- SELECT * FROM v_whatsapp_verkauf_chats;
-- SELECT * FROM v_whatsapp_verkauf_messages LIMIT 10;
