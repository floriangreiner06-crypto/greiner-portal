-- ============================================================================
-- MIGRATION: WhatsApp-Integration für Teile-Handelsgeschäft
-- ============================================================================
-- Erstellt: 2026-01-26 (TAG 211)
-- Zweck: WhatsApp-Integration für Kommunikation mit externen Werkstätten
-- ============================================================================

-- 1. WhatsApp-Kontakte (externe Werkstätten)
CREATE TABLE IF NOT EXISTS whatsapp_contacts (
    id SERIAL PRIMARY KEY,
    workshop_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    notes TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index für schnelle Lookups
CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_phone 
ON whatsapp_contacts(phone_number);

CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_active 
ON whatsapp_contacts(active);

-- 2. WhatsApp-Nachrichten (Historie)
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES whatsapp_contacts(id) ON DELETE SET NULL,
    message_id VARCHAR(255) UNIQUE,  -- WhatsApp Message ID (WAMID)
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('text', 'image', 'document', 'audio', 'video')),
    content TEXT,
    media_url TEXT,
    media_id VARCHAR(255),  -- WhatsApp Media ID
    caption TEXT,  -- Für Bilder/Dokumente
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'read', 'failed', 'pending')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index für schnelle Lookups
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_contact 
ON whatsapp_messages(contact_id);

CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_message_id 
ON whatsapp_messages(message_id);

CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_direction 
ON whatsapp_messages(direction);

CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_created 
ON whatsapp_messages(created_at DESC);

-- 3. WhatsApp-Nachrichten ↔ Teile-Anfragen (Verknüpfung)
CREATE TABLE IF NOT EXISTS whatsapp_parts_requests (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES whatsapp_messages(id) ON DELETE CASCADE,
    part_number VARCHAR(100),
    part_name VARCHAR(255),
    quantity INTEGER DEFAULT 1,
    vehicle_info TEXT,  -- Fahrzeuginfo (z.B. VIN, Marke, Modell)
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'quoted', 'ordered', 'delivered', 'cancelled')),
    quote_price DECIMAL(10, 2),
    quote_currency VARCHAR(3) DEFAULT 'EUR',
    quote_valid_until DATE,
    order_date DATE,
    delivery_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index für schnelle Lookups
CREATE INDEX IF NOT EXISTS idx_whatsapp_parts_requests_message 
ON whatsapp_parts_requests(message_id);

CREATE INDEX IF NOT EXISTS idx_whatsapp_parts_requests_status 
ON whatsapp_parts_requests(status);

CREATE INDEX IF NOT EXISTS idx_whatsapp_parts_requests_part_number 
ON whatsapp_parts_requests(part_number);

-- 4. View: WhatsApp-Nachrichten mit Kontakt-Info
CREATE OR REPLACE VIEW v_whatsapp_messages_with_contact AS
SELECT 
    m.id,
    m.message_id,
    m.contact_id,
    c.workshop_name,
    c.phone_number,
    c.contact_name,
    m.direction,
    m.message_type,
    m.content,
    m.media_url,
    m.caption,
    m.status,
    m.error_message,
    m.created_at,
    m.updated_at
FROM whatsapp_messages m
LEFT JOIN whatsapp_contacts c ON m.contact_id = c.id
ORDER BY m.created_at DESC;

-- 5. View: Teile-Anfragen mit Nachrichten-Info
CREATE OR REPLACE VIEW v_whatsapp_parts_requests_full AS
SELECT 
    pr.id,
    pr.message_id,
    m.message_id as whatsapp_message_id,
    m.direction,
    m.created_at as message_created_at,
    c.workshop_name,
    c.phone_number,
    c.contact_name,
    pr.part_number,
    pr.part_name,
    pr.quantity,
    pr.vehicle_info,
    pr.status,
    pr.quote_price,
    pr.quote_currency,
    pr.quote_valid_until,
    pr.order_date,
    pr.delivery_date,
    pr.notes,
    pr.created_at,
    pr.updated_at
FROM whatsapp_parts_requests pr
LEFT JOIN whatsapp_messages m ON pr.message_id = m.id
LEFT JOIN whatsapp_contacts c ON m.contact_id = c.id
ORDER BY pr.created_at DESC;

-- ============================================================================
-- INITIALE DATEN (optional - Beispiel-Kontakt)
-- ============================================================================
-- Kann später über UI hinzugefügt werden

-- ============================================================================
-- KONTROLLE
-- ============================================================================
-- Nach Migration ausführen:
-- SELECT * FROM whatsapp_contacts;
-- SELECT * FROM whatsapp_messages ORDER BY created_at DESC LIMIT 10;
-- SELECT * FROM v_whatsapp_messages_with_contact LIMIT 10;
-- SELECT * FROM v_whatsapp_parts_requests_full LIMIT 10;
