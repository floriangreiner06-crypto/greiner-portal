-- Garantie-Dokumente: Tabelle für dynamische Liste + Upload (Serviceleiter)
-- Workstream: werkstatt
-- Nutzung: Handbücher, Richtlinien, Rundschreiben; Dateien in data/uploads/garantie/

CREATE TABLE IF NOT EXISTS garantie_dokumente (
    id SERIAL PRIMARY KEY,
    dateiname VARCHAR(255) NOT NULL,
    titel VARCHAR(500) NOT NULL,
    marke VARCHAR(100),
    stand VARCHAR(100),
    typ VARCHAR(50) NOT NULL DEFAULT 'handbuch',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by VARCHAR(255),
    UNIQUE(dateiname)
);

COMMENT ON TABLE garantie_dokumente IS 'Garantie-Handbücher, Richtlinien, Rundschreiben; PDFs in data/uploads/garantie/';
COMMENT ON COLUMN garantie_dokumente.typ IS 'handbuch | richtlinie | rundschreiben';

-- Seed: bekannte Handbücher (Dateien können per Upload ergänzt werden)
INSERT INTO garantie_dokumente (dateiname, titel, marke, stand, typ)
VALUES
    ('Garantie-Richtlinie Stand 01-2026.pdf', 'Garantie-Richtlinie', 'Übergreifend', '01/2026', 'richtlinie'),
    ('Garantie-Richtlinie Hyundai Stand 02-2024.pdf', 'Garantie-Richtlinie Hyundai', 'Hyundai', '02/2024', 'richtlinie'),
    ('Garantie-Handbuch Opel Stand Mai 2025.pdf', 'Garantie-Handbuch Opel', 'Opel / Stellantis', 'Mai 2025', 'handbuch'),
    ('Garantiehandbuch Leapmotor.pdf', 'Garantiehandbuch Leapmotor', 'Leapmotor', '', 'handbuch')
ON CONFLICT (dateiname) DO NOTHING;

-- Feature: Garantie-Dokumente hochladen (Serviceleiter / Admin)
INSERT INTO feature_access (feature_name, role_name, created_by, created_at)
VALUES
    ('garantie_dokumente_upload', 'admin', 'migration', NOW()),
    ('garantie_dokumente_upload', 'werkstatt', 'migration', NOW())
ON CONFLICT (feature_name, role_name) DO NOTHING;
