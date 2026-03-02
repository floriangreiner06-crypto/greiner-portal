-- Admin- und Team-Greiner-Navi rechtsbeschränkt (Parent-Kind-Konsistenz).
-- Admin: Top-Level braucht Feature "admin", Kinder erben in navigation_utils.
-- Team Greiner: "Mein Urlaub" und zugehöriger Divider brauchen "urlaubsplaner".

UPDATE navigation_items
SET requires_feature = 'admin'
WHERE id = 6;

UPDATE navigation_items
SET requires_feature = 'urlaubsplaner'
WHERE id IN (44, 45)
  AND (requires_feature IS NULL OR requires_feature = '');
