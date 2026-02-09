-- Migration TAG 211: WhatsApp-Menüpunkte in DB-Navigation
-- Erstellt: 2026-01-26
-- Zweck: WhatsApp Chat (Verkauf) und WhatsApp Teile (After Sales) in navigation_items

-- 1. WhatsApp Chat unter Verkauf (nur wenn noch nicht vorhanden)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT v.id, 'WhatsApp Chat', '/whatsapp/verkauf/chat', 'bi-whatsapp text-success', 99, 'whatsapp_verkauf', 'dropdown', true
FROM navigation_items v
WHERE v.label = 'Verkauf' AND v.parent_id IS NULL
AND NOT EXISTS (SELECT 1 FROM navigation_items c WHERE c.parent_id = v.id AND c.label = 'WhatsApp Chat')
LIMIT 1;

-- 2. WhatsApp Teile unter Teile & Zubehör (nur wenn noch nicht vorhanden)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT t.id, 'WhatsApp Teile', '/whatsapp/messages', 'bi-whatsapp text-success', 99, 'whatsapp_teile', 'dropdown', true
FROM navigation_items t
WHERE t.label = 'Teile & Zubehör' AND t.parent_id IS NULL
AND NOT EXISTS (SELECT 1 FROM navigation_items c WHERE c.parent_id = t.id AND c.label = 'WhatsApp Teile')
LIMIT 1;
