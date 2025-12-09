-- ============================================================================
-- MIGRATION 024: Urlaubs-Genehmiger System
-- ============================================================================
-- Erstellt: 2025-12-08 (TAG 103)
-- Zweck: Rollenbasierte Urlaubsgenehmigung basierend auf Locosoft grp_code
-- ============================================================================

-- 1. Haupttabelle: Genehmiger-Regeln
CREATE TABLE IF NOT EXISTS vacation_approval_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Welche Mitarbeiter betrifft diese Regel?
    loco_grp_code TEXT NOT NULL,              -- z.B. 'MON', 'VKB', 'SER'
    subsidiary INTEGER,                        -- 1=Deggendorf, 3=Landau, NULL=alle
    
    -- Wer genehmigt?
    approver_employee_id INTEGER NOT NULL,     -- FK zu employees.id
    approver_ldap_username TEXT NOT NULL,      -- z.B. 'w.scheingraber'
    
    -- Priorität (1=primär, 2=Stellvertreter)
    priority INTEGER DEFAULT 1,
    
    -- Aktiv?
    active INTEGER DEFAULT 1,
    
    -- Meta
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    notes TEXT,
    
    -- Constraints
    UNIQUE(loco_grp_code, subsidiary, approver_employee_id)
);

-- 2. Index für schnelle Lookups
CREATE INDEX IF NOT EXISTS idx_approval_rules_lookup 
ON vacation_approval_rules(loco_grp_code, subsidiary, active);

CREATE INDEX IF NOT EXISTS idx_approval_rules_approver 
ON vacation_approval_rules(approver_ldap_username, active);

-- 3. View: Mitarbeiter mit ihren Genehmigern
CREATE VIEW IF NOT EXISTS v_employee_approvers AS
SELECT 
    e.id as employee_id,
    e.first_name || ' ' || e.last_name as employee_name,
    lem.ldap_username as employee_ldap,
    gm.grp_code,
    le.subsidiary,
    CASE le.subsidiary 
        WHEN 1 THEN 'Deggendorf'
        WHEN 3 THEN 'Landau'
        ELSE 'Unbekannt'
    END as standort,
    ar.approver_ldap_username,
    ar.priority,
    ae.first_name || ' ' || ae.last_name as approver_name
FROM employees e
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
JOIN loco_employees le ON lem.locosoft_id = le.employee_number
JOIN loco_employees_group_mapping gm ON le.employee_number = gm.employee_number
LEFT JOIN vacation_approval_rules ar ON (
    ar.loco_grp_code = gm.grp_code 
    AND (ar.subsidiary IS NULL OR ar.subsidiary = le.subsidiary)
    AND ar.active = 1
)
LEFT JOIN ldap_employee_mapping alem ON ar.approver_ldap_username = alem.ldap_username
LEFT JOIN employees ae ON alem.employee_id = ae.id
WHERE e.aktiv = 1
ORDER BY e.last_name, e.first_name, ar.priority;

-- 4. View: Wer muss was genehmigen (für Genehmiger-Dashboard)
CREATE VIEW IF NOT EXISTS v_approver_teams AS
SELECT 
    ar.approver_ldap_username,
    ae.first_name || ' ' || ae.last_name as approver_name,
    ar.loco_grp_code,
    ar.subsidiary,
    CASE ar.subsidiary 
        WHEN 1 THEN 'Deggendorf'
        WHEN 3 THEN 'Landau'
        ELSE 'Alle Standorte'
    END as standort,
    ar.priority,
    COUNT(DISTINCT e.id) as team_size
FROM vacation_approval_rules ar
JOIN ldap_employee_mapping alem ON ar.approver_ldap_username = alem.ldap_username
JOIN employees ae ON alem.employee_id = ae.id
JOIN loco_employees_group_mapping gm ON ar.loco_grp_code = gm.grp_code
JOIN loco_employees le ON gm.employee_number = le.employee_number
    AND (ar.subsidiary IS NULL OR ar.subsidiary = le.subsidiary)
JOIN ldap_employee_mapping lem ON le.employee_number = lem.locosoft_id
JOIN employees e ON lem.employee_id = e.id AND e.aktiv = 1
WHERE ar.active = 1
GROUP BY ar.approver_ldap_username, ar.loco_grp_code, ar.subsidiary, ar.priority
ORDER BY ar.approver_ldap_username, ar.priority;

-- ============================================================================
-- INITIALE DATEN: Genehmiger-Regeln
-- ============================================================================

-- Verkauf (VKB) - Anton Süß für alle
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'VKB', NULL, e.id, 'anton.suess', 1, 'Verkaufsleitung - alle Standorte'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'anton.suess';

-- Monteure DEG - Wolfgang Scheingraber (Prio 1)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'MON', 1, e.id, 'w.scheingraber', 1, 'Werkstattleitung Deggendorf'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'w.scheingraber';

-- Monteure DEG - Matthias König (Prio 2 / Stellvertreter)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'MON', 1, e.id, 'matthias.koenig', 2, 'Serviceleiter (Stellvertreter)'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'matthias.koenig';

-- Monteure LAU - Rolf Sterr (Prio 1)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'MON', 3, e.id, 'rolf.sterr', 1, 'Filialleitung Landau'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'rolf.sterr';

-- Monteure LAU - Leonhard Keidl (Prio 2)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'MON', 3, e.id, 'leonhard.keidl', 2, 'Werkstattleiter Landau (Stellvertreter)'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'leonhard.keidl';

-- Serviceberater (SB) - Matthias König
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'SB', NULL, e.id, 'matthias.koenig', 1, 'Serviceleiter - alle Serviceberater'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'matthias.koenig';

-- Service DEG (SER) - Matthias König (Prio 1)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'SER', 1, e.id, 'matthias.koenig', 1, 'Serviceleiter Deggendorf'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'matthias.koenig';

-- Service DEG (SER) - Sandra Brendel (Prio 2)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'SER', 1, e.id, 'sandra.brendel', 2, 'Kundenzentrale (Stellvertreter)'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'sandra.brendel';

-- Service LAU (SER) - Rolf Sterr
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'SER', 3, e.id, 'rolf.sterr', 1, 'Filialleitung Landau'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'rolf.sterr';

-- Fahrzeugannahme (FA) - Matthias König
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'FA', NULL, e.id, 'matthias.koenig', 1, 'Serviceleiter'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'matthias.koenig';

-- Lager/Teile (LAG) - Bruno Wieland (Prio 1)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'LAG', NULL, e.id, 'bruno.wieland', 1, 'Teile & Zubehör Leitung'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'bruno.wieland';

-- Lager/Teile (LAG) - Matthias König (Prio 2)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'LAG', NULL, e.id, 'matthias.koenig', 2, 'Serviceleiter (Stellvertreter)'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'matthias.koenig';

-- Azubi Lager (A-L) - Bruno Wieland
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'A-L', NULL, e.id, 'bruno.wieland', 1, 'Teile & Zubehör Leitung'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'bruno.wieland';

-- Disposition (DIS) - Margit Loibl (Prio 1)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'DIS', NULL, e.id, 'margit.loibl', 1, 'Disposition Teamleitung'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'margit.loibl';

-- Disposition (DIS) - Jennifer Bielmeier (Prio 2)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'DIS', NULL, e.id, 'jennifer.bielmeier', 2, 'Disposition (Stellvertreter)'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'jennifer.bielmeier';

-- Callcenter/CRM (CC) - Brigitte Lackerbeck
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'CC', NULL, e.id, 'brigitte.lackerbeck', 1, 'Callcenter/CRM Teamleitung'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'brigitte.lackerbeck';

-- Marketing (MAR) - Brigitte Lackerbeck
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'MAR', NULL, e.id, 'brigitte.lackerbeck', 1, 'Marketing Teamleitung'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'brigitte.lackerbeck';

-- Verwaltung/Buchhaltung (VER) - Christian Aichinger (Prio 1)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'VER', NULL, e.id, 'christian.aichinger', 1, 'Buchhaltung Teamleitung'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'christian.aichinger';

-- Verwaltung/Buchhaltung (VER) - Vanessa Groll (Prio 2)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'VER', NULL, e.id, 'vanessa.groll', 2, 'Buchhaltung (Stellvertreter)'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'vanessa.groll';

-- Finanzen (FZ) - Christian Aichinger
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'FZ', NULL, e.id, 'christian.aichinger', 1, 'Buchhaltung Teamleitung'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'christian.aichinger';

-- Gewährleistung (G) - Matthias König
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'G', NULL, e.id, 'matthias.koenig', 1, 'Serviceleiter'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'matthias.koenig';

-- Hausmeister (HM) - Matthias König
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'HM', NULL, e.id, 'matthias.koenig', 1, 'Serviceleiter'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'matthias.koenig';

-- Azubi Werkstatt DEG (A-W) - Wolfgang Scheingraber
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'A-W', 1, e.id, 'w.scheingraber', 1, 'Werkstattleitung Deggendorf'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'w.scheingraber';

-- Azubi Werkstatt LAU (A-W) - Rolf Sterr
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'A-W', 3, e.id, 'rolf.sterr', 1, 'Filialleitung Landau'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'rolf.sterr';

-- Filialleitung (FL) - Florian Greiner (Prio 1)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'FL', NULL, e.id, 'florian.greiner', 1, 'Geschäftsleitung'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'florian.greiner';

-- Filialleitung (FL) - Peter Greiner (Prio 2)
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'FL', NULL, e.id, 'peter.greiner', 2, 'Geschäftsleitung (Stellvertreter)'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'peter.greiner';

-- Geschäftsleitung (GL) - gegenseitig
INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'GL', NULL, e.id, 'florian.greiner', 1, 'Geschäftsleitung gegenseitig'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'florian.greiner';

INSERT OR IGNORE INTO vacation_approval_rules 
(loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, notes)
SELECT 'GL', NULL, e.id, 'peter.greiner', 1, 'Geschäftsleitung gegenseitig'
FROM employees e 
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id 
WHERE lem.ldap_username = 'peter.greiner';

-- ============================================================================
-- KONTROLLE
-- ============================================================================
-- Nach Migration ausführen:
-- SELECT * FROM vacation_approval_rules ORDER BY loco_grp_code, subsidiary, priority;
-- SELECT * FROM v_approver_teams;
-- SELECT * FROM v_employee_approvers WHERE employee_name LIKE '%König%';
