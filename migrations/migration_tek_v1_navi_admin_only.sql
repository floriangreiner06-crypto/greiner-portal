-- TEK v1 nur noch für Admin in der Navigation anzeigen
-- Vorher: requires_feature = bankenspiegel → alle mit Bankenspiegel sahen den Eintrag (z. B. florian.pellkofer)
-- Nachher: nur portal_role admin (oder Nutzer mit Feature admin) sehen "TEK v1" unter Controlling → Archiv

UPDATE navigation_items
SET role_restriction = 'admin'
WHERE label = 'TEK v1'
  AND url = '/controlling/tek/archiv';
