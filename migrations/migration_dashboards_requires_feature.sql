-- Startseiten: requires_feature setzen, damit nur für Rolle sichtbare Startseiten angeboten werden
-- (Rechteverwaltung: User mit Rolle "Verkauf" darf z.B. nicht "Bankenspiegel" als Startseite zugewiesen bekommen)

UPDATE available_dashboards SET requires_feature = 'bankenspiegel'    WHERE dashboard_key = 'bankenspiegel';
UPDATE available_dashboards SET requires_feature = 'controlling'      WHERE dashboard_key = 'controlling';
UPDATE available_dashboards SET requires_feature = 'auftragseingang' WHERE dashboard_key = 'verkauf_auftragseingang';
UPDATE available_dashboards SET requires_feature = 'werkstatt_live'   WHERE dashboard_key = 'werkstatt_dashboard';
UPDATE available_dashboards SET requires_feature = 'werkstatt_live'  WHERE dashboard_key = 'werkstatt_live';
UPDATE available_dashboards SET requires_feature = 'urlaubsplaner'   WHERE dashboard_key = 'urlaubsplaner';
UPDATE available_dashboards SET requires_feature = 'sb_dashboard'    WHERE dashboard_key = 'aftersales_serviceberater';
UPDATE available_dashboards SET requires_feature = 'aftersales'      WHERE dashboard_key = 'aftersales_garantie';
-- mein_bereich, dashboard (Allgemeines Dashboard): bleibt NULL = für alle wählbar
