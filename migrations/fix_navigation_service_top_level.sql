-- Service als Top-Level-Navi immer sichtbar (Unterpunkte bleiben feature-geprüft)
-- Vorher: requires_feature = 'teilebestellungen' → nur mit Teile-Feature sichtbar
-- Nachher: requires_feature = NULL → Service-Dropdown für alle, Untermenüs (Werkstatt, Garantie, …) weiterhin nach Feature

UPDATE navigation_items
SET requires_feature = NULL
WHERE label = 'Service' AND parent_id IS NULL;
