-- Granulare Rechteverwaltung: Portal-Rolle pro User überschreibbar (Admin-UI)
-- Wenn gesetzt, bestimmt portal_role_override die wirksame Rolle (Navi + Features); sonst LDAP-Title.
-- PostgreSQL (drive_portal)

ALTER TABLE users ADD COLUMN IF NOT EXISTS portal_role_override VARCHAR(50) DEFAULT NULL;
COMMENT ON COLUMN users.portal_role_override IS 'Portal-Rolle gesetzt durch Admin (Rechteverwaltung). NULL = aus LDAP title ableiten.';
