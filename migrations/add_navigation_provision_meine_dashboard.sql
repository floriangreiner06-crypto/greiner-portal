-- Migration: Provisionsmodul in DB-Navigation sichtbar machen
-- Zweck: "Meine Provision" und "Provisions-Dashboard" unter Verkauf UND unter Admin,
--        damit das Modul sichtbar ist (insb. wenn USE_DB_NAVIGATION=true).
-- Referenz: base.html Verkauf-Dropdown (hardcoded) hatte diese Links; in navigation_items fehlten sie.

BEGIN;

-- 1) Unter Verkauf: Meine Provision (für alle mit auftragseingang)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT 
    v.id,
    'Meine Provision',
    '/provision/meine',
    'bi-cash-coin',
    13,
    'auftragseingang',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Verkauf' AND parent_id IS NULL LIMIT 1) v
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = v.id AND n.label = 'Meine Provision'
);

-- 2) Unter Verkauf: Provisions-Dashboard (VKL) – nur admin/geschaeftsleitung/verkauf_leitung
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    v.id,
    'Provisions-Dashboard (VKL)',
    '/provision/dashboard',
    'bi-cash-stack',
    14,
    'admin,geschaeftsleitung,verkauf_leitung',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Verkauf' AND parent_id IS NULL LIMIT 1) v
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = v.id AND n.label = 'Provisions-Dashboard (VKL)'
);

-- 3) Unter Admin: Meine Provision + Provisions-Dashboard (direkter Zugriff für Admins)
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    a.id,
    'Meine Provision',
    '/provision/meine',
    'bi-cash-coin',
    9,
    'admin',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1) a
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = a.id AND n.label = 'Meine Provision' AND n.url = '/provision/meine'
);

INSERT INTO navigation_items (parent_id, label, url, icon, order_index, role_restriction, category, active)
SELECT 
    a.id,
    'Provisions-Dashboard (VKL)',
    '/provision/dashboard',
    'bi-cash-stack',
    10,
    'admin',
    'dropdown',
    true
FROM (SELECT id FROM navigation_items WHERE label = 'Admin' AND parent_id IS NULL LIMIT 1) a
WHERE NOT EXISTS (
    SELECT 1 FROM navigation_items n
    WHERE n.parent_id = a.id AND n.label = 'Provisions-Dashboard (VKL)' AND n.url = '/provision/dashboard'
);

COMMIT;
