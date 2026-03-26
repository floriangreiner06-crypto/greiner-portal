-- ============================================================================
-- Merge Duplikat-User (gleicher LOWER(username), verschiedene Schreibweise)
-- Datum: 2026-03-12
-- Grund: Doppelte Einträge durch case-sensitiven Login; eine Person = ein User.
-- Nach Merge: Urlaub-Genehmigungs-Mail (Fallback E-Mail aus users) trifft eindeutig.
-- Behalten: je Gruppe der User mit neuestem last_login (72, 73, 41).
-- Löschen: 46 (Christian alt), 39 (Katrina alt), 71 (Katrin G alt).
-- ============================================================================

BEGIN;

-- 1) user_roles: Rollen vom Duplikat auf Haupt-User übertragen (wo noch nicht vorhanden), dann Duplikat-Rollen löschen
-- Christian: 46 → 72
INSERT INTO user_roles (user_id, role_id, assigned_at)
SELECT 72, ur.role_id, ur.assigned_at
FROM user_roles ur
WHERE ur.user_id = 46
  AND NOT EXISTS (SELECT 1 FROM user_roles u2 WHERE u2.user_id = 72 AND u2.role_id = ur.role_id);
DELETE FROM user_roles WHERE user_id = 46;

-- Katrina: 39 → 73 (nur user_dashboard_config, keine user_roles für 39)
-- Katrin G: 71 → 41
INSERT INTO user_roles (user_id, role_id, assigned_at)
SELECT 41, ur.role_id, ur.assigned_at
FROM user_roles ur
WHERE ur.user_id = 71
  AND NOT EXISTS (SELECT 1 FROM user_roles u2 WHERE u2.user_id = 41 AND u2.role_id = ur.role_id);
DELETE FROM user_roles WHERE user_id = 71;

-- 2) user_dashboard_config: Haupt-User hat bereits eine Zeile (UNIQUE user_id) – nur Duplikat-Zeilen löschen
DELETE FROM user_dashboard_config WHERE user_id IN (39, 46, 71);

-- 3) auth_audit_log: Alte user_id auf Haupt-User umbiegen (Historie bleibt zuordenbar)
UPDATE auth_audit_log SET user_id = 72 WHERE user_id = 46;
UPDATE auth_audit_log SET user_id = 73 WHERE user_id = 39;
UPDATE auth_audit_log SET user_id = 41 WHERE user_id = 71;

-- 4) vacation_bookings.approved_by falls jemand mit Duplikat genehmigt hat
UPDATE vacation_bookings SET approved_by = 72 WHERE approved_by = 46;
UPDATE vacation_bookings SET approved_by = 73 WHERE approved_by = 39;
UPDATE vacation_bookings SET approved_by = 41 WHERE approved_by = 71;

-- 5) Verbleibende user_roles der Duplikate löschen, dann User löschen
DELETE FROM user_roles WHERE user_id = 39;
DELETE FROM users WHERE id IN (39, 46, 71);

COMMIT;

-- Verifikation: Keine Duplikate mehr pro LOWER(username)
-- SELECT LOWER(TRIM(username)), COUNT(*) FROM users GROUP BY LOWER(TRIM(username)) HAVING COUNT(*) > 1;
