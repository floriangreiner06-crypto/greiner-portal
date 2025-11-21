-- ============================================
-- TAG 67: Konten-Kategorisierung erweitern
-- Datum: 2025-11-19
-- Zweck: Kontoinhaber & Verwendungszweck für Multi-Entity-Filtering
-- ============================================

-- 1. Neue Spalten hinzufügen
ALTER TABLE konten ADD COLUMN kontoinhaber TEXT;
ALTER TABLE konten ADD COLUMN verwendungszweck TEXT;
ALTER TABLE konten ADD COLUMN ist_operativ INTEGER DEFAULT 1;  -- 1=operativ, 0=nicht-operativ
ALTER TABLE konten ADD COLUMN anzeige_gruppe TEXT CHECK(anzeige_gruppe IN ('autohaus', 'gesellschafter', 'info'));

-- 2. Kommentare für Dokumentation
-- kontoinhaber: "Autohaus Greiner GmbH & Co. KG", "Greiner Immob.verw.GmbH & Co.KG", etc.
-- verwendungszweck: "Kontokorrent", "Festgeld", "Darlehen", etc.
-- ist_operativ: 1 = Sofort verfügbar (KK), 0 = Nicht operativ (Festgeld, Darlehen)
-- anzeige_gruppe:
--   'autohaus' = Dem Autohaus zugeordnet
--   'gesellschafter' = Gesellschafter-Konten (nur Info)
--   'info' = Darlehen etc. (nur zur Information)

-- 3. View aktualisieren (DROP & CREATE)
DROP VIEW IF EXISTS v_aktuelle_kontostaende;

CREATE VIEW v_aktuelle_kontostaende AS
SELECT 
    k.id,
    k.kontoname,
    k.iban,
    k.bank_id,
    k.kontotyp,
    k.kreditlinie,
    k.kontoinhaber,
    k.verwendungszweck,
    k.ist_operativ,
    k.anzeige_gruppe,
    b.name as bank_name,
    COALESCE(s.saldo, 0) as saldo,
    s.datum as letztes_update
FROM konten k
LEFT JOIN banken b ON k.bank_id = b.id
LEFT JOIN (
    SELECT 
        konto_id,
        saldo,
        datum
    FROM salden
    WHERE (konto_id, datum) IN (
        SELECT konto_id, MAX(datum)
        FROM salden
        GROUP BY konto_id
    )
) s ON k.id = s.konto_id
WHERE k.aktiv = 1
ORDER BY k.kontoname;

-- 4. Index für Performance
CREATE INDEX IF NOT EXISTS idx_konten_anzeige_gruppe ON konten(anzeige_gruppe);
CREATE INDEX IF NOT EXISTS idx_konten_ist_operativ ON konten(ist_operativ);

-- ============================================
-- Fertig! Nächster Schritt: Daten aktualisieren
-- Script: tag67_update_konten_daten.sql
-- ============================================
