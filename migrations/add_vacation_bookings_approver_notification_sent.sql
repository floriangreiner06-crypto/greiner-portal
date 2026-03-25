-- Urlaubsplaner: Eine E-Mail pro Zeitraum an Genehmiger (nicht pro Tag)
-- Spalte um zu markieren, dass für diese Buchung bereits eine Genehmiger-Benachrichtigung
-- (ggf. gebündelt mit anderen Tagen) gesendet wurde.
ALTER TABLE vacation_bookings
ADD COLUMN IF NOT EXISTS approver_notification_sent_at TIMESTAMP;

COMMENT ON COLUMN vacation_bookings.approver_notification_sent_at IS 'Zeitpunkt, zu dem die Genehmiger-E-Mail für diesen Antrag (ggf. gebündelt mit anderen Tagen) gesendet wurde.';
