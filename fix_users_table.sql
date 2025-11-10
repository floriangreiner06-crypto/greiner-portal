-- ============================================================================
-- FIX USERS-TABELLE: ALTE TABELLE ERSETZEN MIT AUTH-STRUKTUR
-- ============================================================================
-- Datum: 2025-11-09
-- Zweck: Ersetzt alte users-Tabelle (4 Spalten) mit neuer Auth-Tabelle (17 Spalten)
-- ============================================================================

BEGIN TRANSACTION;

-- 1. Alte Tabelle sichern
ALTER TABLE users RENAME TO users_old_backup_20251109_0148;

-- 2. Neue users-Tabelle erstellen
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    upn TEXT,
    display_name TEXT NOT NULL,
    email TEXT,
    ad_dn TEXT,
    ad_groups TEXT,
    ou TEXT,
    department TEXT,
    title TEXT,
    is_active BOOLEAN DEFAULT 1,
    is_locked BOOLEAN DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    last_login TIMESTAMP,
    last_ad_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Indices erstellen
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_upn ON users(upn);
CREATE INDEX idx_users_last_login ON users(last_login);
CREATE INDEX idx_users_is_active ON users(is_active);

-- 4. Trigger für updated_at
CREATE TRIGGER update_users_updated_at 
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

COMMIT;

-- 5. Verifikation
SELECT '=== ALTE TABELLE (BACKUP) ===' AS info;
PRAGMA table_info(users_old_backup_20251109_0148);

SELECT '=== NEUE TABELLE ===' AS info;
PRAGMA table_info(users);

SELECT 'SUCCESS: users-Tabelle wurde erfolgreich ersetzt!' AS status;
