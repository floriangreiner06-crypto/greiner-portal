-- Top-Level "Dashboard" nur anzeigen, wenn Rolle das Feature "dashboard" hat.
-- Rolle "werkstatt" hat es standardmäßig nicht → Dashboard verschwindet für reine Werkstatt-User.

UPDATE navigation_items
SET requires_feature = 'dashboard'
WHERE id = 1 AND (requires_feature IS NULL OR requires_feature = '');
