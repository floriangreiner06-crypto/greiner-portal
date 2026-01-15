-- Migration TAG 190: Initial-Daten für Navigation-Items
-- Erstellt: 2026-01-14
-- Zweck: Migriert bestehende Navigation aus base.html

-- Dashboard (Top-Level, immer sichtbar)
INSERT INTO navigation_items (label, url, icon, order_index, category, active) VALUES
('Dashboard', '/', 'bi-house-door', 1, 'main', true)
ON CONFLICT DO NOTHING;

-- Controlling Dropdown (Top-Level)
INSERT INTO navigation_items (label, url, icon, order_index, requires_feature, is_dropdown, category, active) VALUES
('Controlling', NULL, 'bi-graph-up-arrow', 2, NULL, true, 'main', true)
ON CONFLICT DO NOTHING;

-- Controlling Dropdown-Items
-- Note: requires_feature wird später gesetzt, da Controlling-Dropdown sichtbar ist wenn bankenspiegel ODER zinsen ODER einkaufsfinanzierung
-- Für einzelne Items setzen wir die spezifischen Features

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, is_header, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Übersichten',
    NULL,
    NULL,
    1,
    'bankenspiegel',
    true,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Dashboard',
    '/controlling/dashboard',
    'bi-speedometer2',
    2,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'BWA',
    '/controlling/bwa',
    'bi-graph-up',
    3,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'TEK (Tägliche Erfolgskontrolle)',
    '/controlling/tek',
    'bi-bar-chart-line',
    4,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Kontenmapping',
    '/controlling/kontenmapping',
    'bi-table',
    5,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Auswertung Zeiterfassung',
    '/controlling/auswertung-zeiterfassung',
    'bi-clock-history',
    6,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

-- Divider
WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, is_divider, order_index, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    '',
    true,
    7,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

-- Zielplanung Header
WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, is_header, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Zielplanung',
    NULL,
    NULL,
    8,
    'bankenspiegel',
    true,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    '1%-Ziel (Unternehmensplan)',
    '/controlling/unternehmensplan',
    'bi-bullseye',
    9,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'KST-Ziele (Tagesstatus)',
    '/controlling/kst-ziele',
    'bi-bar-chart',
    10,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

-- Divider
WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, is_divider, order_index, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    '',
    true,
    11,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

-- Abteilungsleiter-Planung (für alle mit Controlling-Zugriff)
WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Abteilungsleiter-Planung',
    '/planung/abteilungsleiter',
    'bi-clipboard-check',
    12,
    'controlling',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

-- Analysen Header
WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, is_header, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Analysen',
    NULL,
    NULL,
    13,
    NULL,  -- Sichtbar wenn zinsen ODER einkaufsfinanzierung ODER bankenspiegel
    true,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Zinsen-Analyse',
    '/bankenspiegel/zinsen-analyse',
    'bi-percent',
    14,
    'zinsen',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Einkaufsfinanzierung',
    '/bankenspiegel/einkaufsfinanzierung',
    'bi-truck',
    15,
    'einkaufsfinanzierung',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Jahresprämie',
    '/jahrespraemie/',
    'bi-gift',
    16,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

-- Divider
WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, is_divider, order_index, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    '',
    true,
    17,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

-- Bankenspiegel Header
WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, is_header, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Bankenspiegel',
    NULL,
    NULL,
    18,
    'bankenspiegel',
    true,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Dashboard',
    '/bankenspiegel/dashboard',
    'bi-bank2',
    19,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Kontenübersicht',
    '/bankenspiegel/konten',
    'bi-wallet2',
    20,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Transaktionen',
    '/bankenspiegel/transaktionen',
    'bi-receipt',
    21,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Fahrzeugfinanzierungen',
    '/bankenspiegel/fahrzeugfinanzierungen',
    'bi-car-front',
    22,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

-- Divider
WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, is_divider, order_index, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    '',
    true,
    23,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

-- Archiv Header
WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, is_header, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'Archiv',
    NULL,
    NULL,
    24,
    'bankenspiegel',
    true,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

WITH controlling_id AS (SELECT id FROM navigation_items WHERE label = 'Controlling' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM controlling_id),
    'TEK v1',
    '/controlling/tek/archiv',
    'bi-archive',
    25,
    'bankenspiegel',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM controlling_id)
ON CONFLICT DO NOTHING;

-- Verkauf Dropdown (Top-Level)
INSERT INTO navigation_items (label, url, icon, order_index, requires_feature, is_dropdown, category, active) VALUES
('Verkauf', NULL, 'bi-cart3', 3, 'auftragseingang', true, 'main', true)
ON CONFLICT DO NOTHING;

-- Verkauf Dropdown-Items
WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    'Auftragseingang',
    '/verkauf/auftragseingang',
    'bi-clipboard-data',
    1,
    'auftragseingang',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    'Auslieferungen',
    '/verkauf/auslieferung/detail',
    'bi-truck',
    2,
    'auslieferungen',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    'eAutoseller Bestand',
    '/verkauf/eautoseller-bestand',
    'bi-car-front',
    3,
    'auftragseingang',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    'GW-Standzeit',
    '/verkauf/gw-bestand',
    'bi-clock-history',
    4,
    'auftragseingang',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

-- Divider
WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, is_divider, order_index, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    '',
    true,
    5,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

-- Planung Header (nur für admin/geschaeftsleitung/verkauf_leitung)
WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, is_header, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    'Planung',
    NULL,
    NULL,
    6,
    'admin',  -- Oder verkauf_leitung - wird im Frontend geprüft
    true,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    'Budget-Planung',
    '/verkauf/budget',
    'bi-bullseye',
    7,
    'admin',  -- Oder verkauf_leitung
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    'Lieferforecast',
    '/verkauf/lieferforecast',
    'bi-calendar-week',
    8,
    'admin',  -- Oder verkauf_leitung
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

-- Divider
WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, is_divider, order_index, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    '',
    true,
    9,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

-- Tools Header
WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, is_header, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    'Tools',
    NULL,
    NULL,
    10,
    'auftragseingang',
    true,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    'Leasys Programmfinder',
    '/verkauf/leasys-programmfinder',
    'bi-search-heart',
    11,
    'auftragseingang',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

WITH verkauf_id AS (SELECT id FROM navigation_items WHERE label = 'Verkauf' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM verkauf_id),
    'Leasys Kalkulator',
    '/verkauf/leasys-kalkulator',
    'bi-calculator',
    12,
    'auftragseingang',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM verkauf_id)
ON CONFLICT DO NOTHING;

-- Urlaubsplaner (Top-Level, immer sichtbar)
INSERT INTO navigation_items (label, url, icon, order_index, is_dropdown, category, active) VALUES
('Urlaubsplaner', NULL, 'bi-calendar-check', 4, true, 'main', true)
ON CONFLICT DO NOTHING;

WITH urlaub_id AS (SELECT id FROM navigation_items WHERE label = 'Urlaubsplaner' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, category, active)
SELECT 
    (SELECT id FROM urlaub_id),
    'Mein Urlaub',
    '/urlaubsplaner/v2',
    'bi-calendar-plus',
    1,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM urlaub_id)
ON CONFLICT DO NOTHING;

-- Divider
WITH urlaub_id AS (SELECT id FROM navigation_items WHERE label = 'Urlaubsplaner' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, is_divider, order_index, category, active)
SELECT 
    (SELECT id FROM urlaub_id),
    '',
    true,
    2,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM urlaub_id)
ON CONFLICT DO NOTHING;

-- Team-Übersicht (nur für Leitungen)
WITH urlaub_id AS (SELECT id FROM navigation_items WHERE label = 'Urlaubsplaner' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM urlaub_id),
    'Team-Übersicht',
    '/urlaubsplaner/chef',
    'bi-diagram-3',
    3,
    'urlaub_genehmigen',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM urlaub_id)
ON CONFLICT DO NOTHING;

-- After Sales Dropdown (Top-Level)
INSERT INTO navigation_items (label, url, icon, order_index, requires_feature, is_dropdown, category, active) VALUES
('After Sales', NULL, 'bi-tools', 5, 'teilebestellungen', true, 'main', true)
ON CONFLICT DO NOTHING;

-- After Sales Items (vereinfacht - wichtigste Items)
-- Controlling Header
WITH aftersales_id AS (SELECT id FROM navigation_items WHERE label = 'After Sales' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, is_header, category, active)
SELECT 
    (SELECT id FROM aftersales_id),
    'Controlling',
    NULL,
    NULL,
    1,
    'teilebestellungen',
    true,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM aftersales_id)
ON CONFLICT DO NOTHING;

WITH aftersales_id AS (SELECT id FROM navigation_items WHERE label = 'After Sales' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM aftersales_id),
    'Serviceberater Übersicht',
    '/aftersales/serviceberater/uebersicht',
    'bi-people',
    2,
    'teilebestellungen',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM aftersales_id)
ON CONFLICT DO NOTHING;

WITH aftersales_id AS (SELECT id FROM navigation_items WHERE label = 'After Sales' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM aftersales_id),
    'Serviceberater Controlling',
    '/aftersales/serviceberater/',
    'bi-person-badge',
    3,
    'teilebestellungen',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM aftersales_id)
ON CONFLICT DO NOTHING;

-- Divider
WITH aftersales_id AS (SELECT id FROM navigation_items WHERE label = 'After Sales' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, is_divider, order_index, category, active)
SELECT 
    (SELECT id FROM aftersales_id),
    '',
    true,
    4,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM aftersales_id)
ON CONFLICT DO NOTHING;

-- Garantie Header
WITH aftersales_id AS (SELECT id FROM navigation_items WHERE label = 'After Sales' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, is_header, category, active)
SELECT 
    (SELECT id FROM aftersales_id),
    'Garantie',
    NULL,
    NULL,
    5,
    'aftersales',
    true,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM aftersales_id)
ON CONFLICT DO NOTHING;

WITH aftersales_id AS (SELECT id FROM navigation_items WHERE label = 'After Sales' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    (SELECT id FROM aftersales_id),
    'Garantieaufträge',
    '/aftersales/garantie/auftraege',
    'bi-shield-check',
    6,
    'aftersales',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM aftersales_id)
ON CONFLICT DO NOTHING;

-- Admin Dropdown (Top-Level, nur für admin)
INSERT INTO navigation_items (label, url, icon, order_index, role_restriction, is_dropdown, category, active) VALUES
('Admin', NULL, 'bi-shield-lock', 6, 'admin', true, 'main', true)
ON CONFLICT DO NOTHING;

WITH admin_id AS (SELECT id FROM navigation_items WHERE label = 'Admin' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, is_header, category, active)
SELECT 
    (SELECT id FROM admin_id),
    'System',
    NULL,
    NULL,
    1,
    'admin',
    true,
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM admin_id)
ON CONFLICT DO NOTHING;

WITH admin_id AS (SELECT id FROM navigation_items WHERE label = 'Admin' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    (SELECT id FROM admin_id),
    'Task Manager',
    '/admin/celery/',
    'bi-list-task',
    2,
    'admin',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM admin_id)
ON CONFLICT DO NOTHING;

WITH admin_id AS (SELECT id FROM navigation_items WHERE label = 'Admin' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    (SELECT id FROM admin_id),
    'Flower Dashboard',
    'http://10.80.80.20:5555',
    'bi-flower1',
    3,
    'admin',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM admin_id)
ON CONFLICT DO NOTHING;

WITH admin_id AS (SELECT id FROM navigation_items WHERE label = 'Admin' LIMIT 1)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    (SELECT id FROM admin_id),
    'Rechteverwaltung',
    '/admin/rechte',
    'bi-person-lock',
    4,
    'admin',
    'dropdown',
    true
WHERE EXISTS (SELECT 1 FROM admin_id)
ON CONFLICT DO NOTHING;
