-- Samstagsdienst (VKL): Reine Info – Samstage markieren, an denen Verkäufer nicht im Haus ist.
-- Keine Auswirkung auf Arbeitszeit oder Urlaubskonto. 2026-03
INSERT INTO vacation_types (id, name, color, available_for_user, available_for_approver, available_for_admin, deduct_from_contingent, needs_approval)
VALUES (13, 'Samstagsdienst', '#9E9E9E', false, true, true, 0, 0)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  color = EXCLUDED.color,
  available_for_approver = EXCLUDED.available_for_approver,
  available_for_admin = EXCLUDED.available_for_admin,
  deduct_from_contingent = EXCLUDED.deduct_from_contingent,
  needs_approval = EXCLUDED.needs_approval;
