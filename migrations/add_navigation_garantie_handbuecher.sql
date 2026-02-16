-- Garantie: Handbücher & Richtlinien in DB-Navigation (Phase 1 Wissensbasis)
-- Zeigt den neuen Navi-Punkt unter Service → Garantie, wenn DB-Navigation aktiv ist.
-- parent_id = gleicher Garantie-Bereich wie Garantieaufträge (parent von Garantieaufträge)

INSERT INTO navigation_items (
    parent_id,
    label,
    url,
    icon,
    order_index,
    requires_feature,
    is_header,
    is_divider,
    category,
    active
)
SELECT
    g.parent_id,
    'Handbücher & Richtlinien',
    '/aftersales/garantie/handbuecher',
    'bi-journal-bookmark',
    7,
    'aftersales',
    false,
    false,
    'dropdown',
    true
FROM navigation_items g
WHERE g.label = 'Garantieaufträge' AND g.url = '/aftersales/garantie/auftraege'
  AND NOT EXISTS (
    SELECT 1 FROM navigation_items c
    WHERE c.label = 'Handbücher & Richtlinien' AND c.url = '/aftersales/garantie/handbuecher'
  );
