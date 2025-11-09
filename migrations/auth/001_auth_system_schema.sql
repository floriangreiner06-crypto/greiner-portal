-- ============================================================================
-- AUTH SYSTEM SCHEMA
-- Tabellen für User-Management, Rollen und Audit-Logging
-- ============================================================================

-- Users-Tabelle (erweitert)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    display_name TEXT,
    ou TEXT,
    department TEXT,
    title TEXT,
    is_active BOOLEAN DEFAULT 1,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rollen-Tabelle
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Rollen-Mapping
CREATE TABLE IF NOT EXISTS user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id),
    UNIQUE(user_id, role_id)
);

-- AD-Gruppen zu Rollen Mapping
CREATE TABLE IF NOT EXISTS ad_group_role_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_group_name TEXT UNIQUE NOT NULL,
    role_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- Audit-Log für Auth-Events
CREATE TABLE IF NOT EXISTS auth_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    event_type TEXT NOT NULL,
    success BOOLEAN,
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Standard-Rollen einfügen
INSERT OR IGNORE INTO roles (name, display_name, description) VALUES
    ('admin', 'Administrator', 'Voller Systemzugriff'),
    ('geschaeftsleitung', 'Geschäftsleitung', 'Vollzugriff auf alle Module'),
    ('buchhaltung', 'Buchhaltung', 'Zugriff auf Finanzen und Bankenspiegel'),
    ('verkauf', 'Verkauf', 'Zugriff auf Verkaufsmodule'),
    ('werkstatt', 'Werkstatt', 'Zugriff auf Werkstatt-Module'),
    ('user', 'Benutzer', 'Basis-Zugriffsrechte');

-- Indices für Performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_ou ON users(ou);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON auth_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON auth_audit_log(timestamp);

-- Views für einfache Abfragen
CREATE VIEW IF NOT EXISTS v_user_roles AS
SELECT 
    u.id as user_id,
    u.username,
    u.display_name,
    u.email,
    u.ou,
    r.name as role_name,
    r.display_name as role_display_name,
    ur.assigned_at
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.is_active = 1;
