-- GW-Bestand (IV): Operatoren konfigurierbar (Stelle: zwischen DB und Abzug; zwischen Anteil und Pauschale)
ALTER TABLE provision_config
  ADD COLUMN IF NOT EXISTS gw_bestand_operator_abzug TEXT DEFAULT 'minus',
  ADD COLUMN IF NOT EXISTS gw_bestand_operator_komponenten TEXT DEFAULT 'plus';

COMMENT ON COLUMN provision_config.gw_bestand_operator_abzug IS 'Operator an Stelle: zwischen Deckungsbeitrag und Abzug. minus = DB2 = DB - Abzug, plus = DB + Abzug.';
COMMENT ON COLUMN provision_config.gw_bestand_operator_komponenten IS 'Operator an Stelle: zwischen GW-Umsatzprovision-Anteil und Verkaufskostenpauschale. plus = Abzug = (DB×Anteil)+Pauschale, minus = (DB×Anteil)-Pauschale.';
