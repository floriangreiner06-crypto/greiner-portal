-- Spalte kennzeichen in fahrzeugfinanzierungen (für Sync aus Locosoft vehicles.license_plate)
-- Wird von scripts/sync/sync_stammdaten.py und sync_fahrzeug_stammdaten.py befüllt.

ALTER TABLE fahrzeugfinanzierungen
ADD COLUMN IF NOT EXISTS kennzeichen VARCHAR(20);

COMMENT ON COLUMN fahrzeugfinanzierungen.kennzeichen IS 'Amtliches Kfz-Kennzeichen, aus Locosoft vehicles.license_plate synchronisiert';
