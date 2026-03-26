-- Migration: Navigation-Eintrag "Hilfe" (Top-Level)
-- Erstellt: 2026-02-24 | Workstream: Hilfe
-- Sichtbar für alle eingeloggten User (requires_feature NULL)

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, category, active)
SELECT NULL, 'Hilfe', '/hilfe', 'bi-question-circle', 99, 'main', true
WHERE NOT EXISTS (SELECT 1 FROM navigation_items WHERE label = 'Hilfe' AND parent_id IS NULL);
