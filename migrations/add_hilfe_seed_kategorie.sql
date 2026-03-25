-- Seed: Eine Kategorie "Allgemein" für das Hilfe-Modul (optional)
INSERT INTO hilfe_kategorien (name, slug, beschreibung, icon, sort_order, aktiv)
SELECT 'Allgemein', 'allgemein', 'Erste Schritte und allgemeine Fragen zum Portal', 'bi-house-door', 0, true
WHERE NOT EXISTS (SELECT 1 FROM hilfe_kategorien WHERE slug = 'allgemein');
