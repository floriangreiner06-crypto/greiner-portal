-- ============================================================================
-- ABTEILUNGSLEITER-PLANUNG TABELLE (TAG 165)
-- ============================================================================
-- Erstellt: TAG 165
-- Zweck: Bottom-Up Planung durch Abteilungsleiter (10 Fragen pro KST)
-- Workflow: Entwurf → Freigegeben → In kst_ziele geschrieben
-- ============================================================================

CREATE TABLE IF NOT EXISTS abteilungsleiter_planung (
    id SERIAL PRIMARY KEY,
    
    -- Zeitraum
    geschaeftsjahr TEXT NOT NULL,  -- z.B. '2025/26'
    monat INTEGER NOT NULL,         -- 1-12 (Kalendermonat: 1=Jan, 12=Dez)
    bereich TEXT NOT NULL,          -- 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
    standort INTEGER NOT NULL,      -- 1=DEG, 2=HYU, 3=LAN
    
    -- Status
    status TEXT DEFAULT 'entwurf',  -- 'entwurf', 'freigegeben', 'abgelehnt'
    erstellt_von VARCHAR(100),       -- LDAP-Username des Abteilungsleiters
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    freigegeben_von VARCHAR(100),    -- LDAP-Username der Geschäftsführung
    freigegeben_am TIMESTAMP,
    kommentar TEXT,                 -- Kommentar bei Freigabe/Ablehnung
    
    -- ========================================================================
    -- NEUWAGEN (NW) / GEBRAUCHTWAGEN (GW) - 10 Fragen
    -- ========================================================================
    -- 1. Stückzahl
    plan_stueck INTEGER,
    
    -- 2. Bruttoertrag pro Fahrzeug
    plan_bruttoertrag_pro_fzg NUMERIC(10,2),
    
    -- 3. Variable Kosten (%)
    plan_variable_kosten_prozent NUMERIC(5,2),
    
    -- 4. Durchschnittlicher Verkaufspreis
    plan_verkaufspreis NUMERIC(15,2),
    
    -- 5. Durchschnittliche Standzeit (Tage)
    plan_standzeit_tage INTEGER,
    
    -- 6. Fertigmachen-Kosten pro Fahrzeug
    plan_fertigmachen_pro_fzg NUMERIC(10,2),
    
    -- 7. Werbung & Marketing (Jahr)
    plan_werbung_jahr NUMERIC(12,2),
    
    -- 8. Kulanz & Garantie (Jahr)
    plan_kulanz_jahr NUMERIC(12,2),
    
    -- 9. Training & Schulung (Jahr) / EK-Preis (GW)
    plan_training_jahr NUMERIC(12,2),
    plan_ek_preis NUMERIC(15,2),  -- Nur für GW
    
    -- 10. Saisonalisierung (JSON: {"Sep": 8, "Okt": 9, ...})
    plan_saisonalisierung JSONB,
    
    -- ========================================================================
    -- WERKSTATT (ME) - 10 Fragen
    -- ========================================================================
    -- 1. Anzahl Serviceberater
    plan_anzahl_sb INTEGER,
    
    -- 2. Stundensatz
    plan_stundensatz NUMERIC(10,2),
    
    -- 3. Produktivität (%)
    plan_produktivitaet NUMERIC(5,2),
    
    -- 4. Leistungsgrad (%)
    plan_leistungsgrad NUMERIC(5,2),
    
    -- 5. Auslastung (%)
    plan_auslastung NUMERIC(5,2),
    
    -- 6. Verkaufte Stunden (automatisch berechnet)
    plan_stunden_verkauft NUMERIC(10,2),
    
    -- 7. DB1-Marge (%)
    plan_db1_marge NUMERIC(5,2),
    
    -- 8. Durchschnittliche AW pro Auftrag
    plan_aw_pro_auftrag NUMERIC(5,2),
    
    -- 9. Durchschnittliche Durchlaufzeit (Tage)
    plan_durchlaufzeit NUMERIC(5,2),
    
    -- 10. Wiederkehrrate (%)
    plan_wiederkehrrate NUMERIC(5,2),
    
    -- ========================================================================
    -- TEILE (TZ) - 10 Fragen
    -- ========================================================================
    -- 1. Umsatz (Jahr)
    plan_umsatz NUMERIC(15,2),
    
    -- 2. Marge (%)
    plan_marge_prozent NUMERIC(5,2),
    
    -- 3. Lagerumschlag (x pro Jahr)
    plan_lagerumschlag NUMERIC(5,2),
    
    -- 4. Durchschnittlicher Lagerwert (automatisch berechnet)
    plan_lagerwert NUMERIC(12,2),
    
    -- 5. Penner-Quote (%)
    plan_penner_quote NUMERIC(5,2),
    
    -- 6. Servicegrad (%)
    plan_servicegrad NUMERIC(5,2),
    
    -- 7. Durchschnittlicher EK-Preis pro Teil
    plan_ek_preis_teile NUMERIC(10,2),
    
    -- 8. Durchschnittlicher VK-Preis pro Teil
    plan_vk_preis_teile NUMERIC(10,2),
    
    -- 9. Zinskosten Lager (automatisch berechnet)
    plan_zinskosten_lager NUMERIC(12,2),
    
    -- 10. Direkte Kosten (Personal, Miete, etc.)
    plan_direkte_kosten NUMERIC(12,2),
    
    -- ========================================================================
    -- VORJAHRES-REFERENZ (für alle Bereiche)
    -- ========================================================================
    -- Vorjahres-Werte (automatisch geladen)
    vj_umsatz NUMERIC(15,2),
    vj_db1 NUMERIC(15,2),
    vj_db2 NUMERIC(15,2),
    vj_stueck INTEGER,
    vj_standzeit INTEGER,
    vj_produktivitaet NUMERIC(5,2),
    vj_leistungsgrad NUMERIC(5,2),
    vj_auslastung NUMERIC(5,2),
    vj_stundensatz NUMERIC(8,2),
    vj_lagerumschlag NUMERIC(5,2),
    vj_penner_quote NUMERIC(5,2),
    vj_servicegrad NUMERIC(5,2),
    vj_lagerwert NUMERIC(12,2),
    vj_zinskosten_lager NUMERIC(12,2),
    
    -- ========================================================================
    -- BERECHNETE ZIELE (nach Freigabe in kst_ziele geschrieben)
    -- ========================================================================
    -- Basis-Ziele (Bottom-Up aus Planung)
    umsatz_basis NUMERIC(15,2),
    db1_basis NUMERIC(15,2),
    db2_basis NUMERIC(15,2),
    
    -- Aufhol-Beitrag (Top-Down aus Gap-Analyse)
    aufhol_umsatz NUMERIC(15,2),
    aufhol_db1 NUMERIC(15,2),
    
    -- Gesamt-Ziele (Basis + Aufhol)
    umsatz_ziel NUMERIC(15,2),
    db1_ziel NUMERIC(15,2),
    db2_ziel NUMERIC(15,2),
    
    -- Metadaten
    geaendert_von VARCHAR(100),
    geaendert_am TIMESTAMP,
    
    -- Constraints
    UNIQUE(geschaeftsjahr, monat, bereich, standort),
    CHECK (monat >= 1 AND monat <= 12),
    CHECK (bereich IN ('NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige')),
    CHECK (standort >= 1 AND standort <= 3),
    CHECK (status IN ('entwurf', 'freigegeben', 'abgelehnt'))
);

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_abteilungsleiter_planung_gj_monat ON abteilungsleiter_planung(geschaeftsjahr, monat);
CREATE INDEX IF NOT EXISTS idx_abteilungsleiter_planung_bereich ON abteilungsleiter_planung(bereich);
CREATE INDEX IF NOT EXISTS idx_abteilungsleiter_planung_standort ON abteilungsleiter_planung(standort);
CREATE INDEX IF NOT EXISTS idx_abteilungsleiter_planung_status ON abteilungsleiter_planung(status);

-- Kommentare
COMMENT ON TABLE abteilungsleiter_planung IS 'Abteilungsleiter-Planung (Bottom-Up) - 10 Fragen pro KST (TAG 165)';
COMMENT ON COLUMN abteilungsleiter_planung.status IS 'Status: entwurf, freigegeben, abgelehnt';
COMMENT ON COLUMN abteilungsleiter_planung.plan_saisonalisierung IS 'JSON: {"Sep": 8, "Okt": 9, ...} - Prozentuale Verteilung pro Monat';
COMMENT ON COLUMN abteilungsleiter_planung.umsatz_basis IS 'Basis-Umsatz-Ziel (Bottom-Up aus Planung)';
COMMENT ON COLUMN abteilungsleiter_planung.aufhol_umsatz IS 'Aufhol-Beitrag Umsatz (Top-Down aus Gap-Analyse)';
COMMENT ON COLUMN abteilungsleiter_planung.umsatz_ziel IS 'Gesamt-Umsatz-Ziel (Basis + Aufhol)';

-- ============================================================================
-- KST-ZIELE ERWEITERN (für Abteilungsleiter-Planung)
-- ============================================================================

ALTER TABLE kst_ziele
ADD COLUMN IF NOT EXISTS plan_abteilungsleiter VARCHAR(100),
ADD COLUMN IF NOT EXISTS plan_freigegeben_von VARCHAR(100),
ADD COLUMN IF NOT EXISTS plan_freigegeben_am TIMESTAMP;

COMMENT ON COLUMN kst_ziele.plan_abteilungsleiter IS 'Wer hat geplant? (aus abteilungsleiter_planung)';
COMMENT ON COLUMN kst_ziele.plan_freigegeben_von IS 'Wer hat freigegeben? (aus abteilungsleiter_planung)';
COMMENT ON COLUMN kst_ziele.plan_freigegeben_am IS 'Wann freigegeben? (aus abteilungsleiter_planung)';

-- ============================================================================



