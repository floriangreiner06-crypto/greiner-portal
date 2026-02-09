-- Migration: Alarm E-Mail Report-Subscriber Tracking (TAG 206)
-- Ermöglicht Tracking von Empfängern per E-Mail (report_subscriptions) zusätzlich zu employee_locosoft_id.
-- Nach Migration: Celery-Task kann Report-Subscriber in Admin konfigurierbar versenden und 1x pro Tag tracken.

-- 1. Spalte für E-Mail-Empfänger (z.B. aus Report-Subscriptions)
ALTER TABLE email_notifications_sent
ADD COLUMN IF NOT EXISTS recipient_email TEXT DEFAULT NULL;

-- 2. Alten UNIQUE-Constraint entfernen (Name kann je nach DB variieren)
DO $$
DECLARE
    conname text;
BEGIN
    SELECT c.conname INTO conname
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    WHERE t.relname = 'email_notifications_sent' AND c.contype = 'u'
    LIMIT 1;
    IF conname IS NOT NULL THEN
        EXECUTE format('ALTER TABLE email_notifications_sent DROP CONSTRAINT %I', conname);
    END IF;
END $$;

-- 3. Neuer eindeutiger Index: ein Eintrag pro Auftrag/Tag pro Empfänger (Locosoft-ID oder E-Mail)
CREATE UNIQUE INDEX IF NOT EXISTS idx_email_notifications_sent_recipient
ON email_notifications_sent (auftrag_nr, notification_type, sent_date,
    COALESCE(recipient_email, employee_locosoft_id::text));

COMMENT ON COLUMN email_notifications_sent.recipient_email IS 'E-Mail-Adresse bei Report-Subscriber (employee_locosoft_id dann -1)';
