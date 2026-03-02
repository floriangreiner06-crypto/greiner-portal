-- Controlling-Navi nur anzeigen, wenn User/Rolle berechtigt ist.
-- Top-Level "Controlling" und bisher freie Kinder (Divider) bekommen requires_feature.

UPDATE navigation_items
SET requires_feature = 'controlling'
WHERE id = 2;

UPDATE navigation_items
SET requires_feature = 'controlling'
WHERE parent_id = 2
  AND (requires_feature IS NULL OR requires_feature = '');
