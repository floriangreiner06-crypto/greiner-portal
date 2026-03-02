-- Fix: Fahrzeuganlage-Navi-Eintrag braucht requires_feature = 'fahrzeuganlage'
-- (Eintrag war teils ohne requires_feature; dann wird Eltern-Nachzug genutzt)

UPDATE navigation_items
SET requires_feature = 'fahrzeuganlage'
WHERE label = 'Fahrzeuganlage'
  AND (requires_feature IS NULL OR requires_feature = '');
