-- Genobank Konto 4700057908: Sollzins hinzufügen
-- Der Zinssatz sollte aus der Kontoaufstellung oder MT940-Daten kommen
-- Falls nicht vorhanden, wird ein Default-Wert verwendet

-- Prüfe ob Konto existiert
SELECT id, kontoname, sollzins 
FROM konten 
WHERE kontonummer = '4700057908' OR iban LIKE '%4700057908%';

-- Falls sollzins NULL ist, setze einen Default-Wert
-- TODO: Zinssatz aus aktueller Kontoaufstellung oder MT940-Daten ermitteln
UPDATE konten 
SET sollzins = 5.5  -- Default, sollte durch Kontoaufstellung-Import aktualisiert werden
WHERE (kontonummer = '4700057908' OR iban LIKE '%4700057908%')
  AND sollzins IS NULL;

-- Prüfe Ergebnis
SELECT id, kontoname, sollzins, 
       (SELECT saldo FROM salden WHERE konto_id = konten.id ORDER BY datum DESC LIMIT 1) as aktueller_saldo
FROM konten 
WHERE kontonummer = '4700057908' OR iban LIKE '%4700057908%';
