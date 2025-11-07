-- ============================================================================
-- MIGRATION 001: KONTOSTAND-HISTORIE
-- ============================================================================
-- Beschreibung: Historische Kontostände für Zeitreihen-Analysen
-- Priorität: KRITISCH (benötigt für Charts und Saldo-Entwicklung)
-- ============================================================================

CREATE TABLE IF NOT EXISTS kontostand_historie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    konto_id INTEGER NOT NULL,
    datum DATE NOT NULL,
    saldo REAL NOT NULL,
    waehrung TEXT DEFAULT 'EUR',
    quelle TEXT CHECK(quelle IN ('PDF_Import', 'Manuelle_Eingabe', 'Berechnet', 'API')),
    erfasst_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (konto_id) REFERENCES konten(id) ON DELETE CASCADE,
    UNIQUE(konto_id, datum)
);

CREATE INDEX IF NOT EXISTS idx_kontostand_konto ON kontostand_historie(konto_id);
CREATE INDEX IF NOT EXISTS idx_kontostand_datum ON kontostand_historie(datum);

-- ============================================================================
-- INITIALE DATEN AUS BESTEHENDEN TRANSAKTIONEN BERECHNEN
-- ============================================================================

-- Für jedes Konto den aktuellen Saldo aus der letzten Transaktion ermitteln
INSERT OR IGNORE INTO kontostand_historie (konto_id, datum, saldo, quelle)
SELECT 
    konto_id,
    DATE(buchungsdatum) as datum,
    saldo_nach_buchung as saldo,
    'Berechnet' as quelle
FROM (
    SELECT 
        konto_id,
        buchungsdatum,
        saldo_nach_buchung,
        ROW_NUMBER() OVER (PARTITION BY konto_id ORDER BY buchungsdatum DESC) as rn
    FROM transaktionen
    WHERE saldo_nach_buchung IS NOT NULL
)
WHERE rn = 1;

-- ============================================================================
-- VALIDIERUNG
-- ============================================================================

SELECT 
    'Migration 001 erfolgreich!' as Status,
    (SELECT COUNT(*) FROM kontostand_historie) as Einträge_kontostand_historie;
