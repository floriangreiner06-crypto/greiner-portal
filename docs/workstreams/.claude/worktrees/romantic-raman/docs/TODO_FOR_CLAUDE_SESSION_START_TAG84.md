# TODO FOR CLAUDE - SESSION START TAG84

**Datum:** 03. Dezember 2025  
**Vorherige Session:** TAG83 (Roadmap erstellt)

---

## 🎯 KONTEXT

TAG83 hat die **ROADMAP_DRIVE_2025.md** erstellt mit 5 neuen Features:
1. Lager: Renner & Penner Liste
2. eBay Kleinanzeigen Shop  
3. Serviceberater Rangliste (Contrasept)
4. Prämienmodell Aftersales
5. Leistungslohn Mechatroniker

---

## 📋 PRIORITÄTEN TAG84

### Prio 1: Locosoft-Analyse für neue Features

```bash
# Verbindung zu Locosoft PostgreSQL
psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db

# Tabellen für LAGER/TEILE suchen
\dt *part*
\dt *stock*
\dt *lager*
\dt *artikel*
\dt *inventory*

# Tabellen für WERKSTATT suchen
\dt *work*
\dt *order*
\dt *auftrag*
\dt *service*

# Spalten einer Tabelle anzeigen
\d tabellename
```

### Prio 2: User-Input abholen

1. **Prämienmodell-Excel:** Bitte in `User_input/` ablegen
2. **Contrasept-Artikelnummern:** Liste der Zusatzverkauf-Artikel
3. **Kleinanzeigen-Strategie:** Anzeigenchef oder CSV-Export?

### Prio 3: TAG83 offene Punkte

Aus SESSION_WRAP_UP_TAG82:
- [ ] Modellbezeichnung im Auftragseingang (zeigt Code statt Name)
- [ ] Bruttoertrag nach Faktura aktualisieren
- [ ] Werkstattaufträge zum Fahrzeug anzeigen
- [ ] Farben-Legende hinzufügen

---

## 📁 RELEVANTE DATEIEN

```
ROADMAP_DRIVE_2025.md                 # Neue Roadmap (heute erstellt)
LOCOSOFT_POSTGRESQL_DOKUMENTATION.md  # Locosoft-Struktur
api/verkauf_api.py                    # Version 2.2-vin
scripts/sync/sync_sales.py            # Verkaufsdaten-Sync
```

---

## 🔧 SCHNELLSTART

```bash
# Server-Verbindung
ssh ag-admin@10.80.80.20

# Ins Projektverzeichnis
cd /opt/greiner-portal
source venv/bin/activate

# Locosoft-Verbindung testen
python3 -c "
import psycopg2
import json
with open('config/credentials.json') as f:
    creds = json.load(f)['databases']['locosoft']
conn = psycopg2.connect(**creds)
cur = conn.cursor()
cur.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name\")
for row in cur.fetchall()[:20]:
    print(row[0])
"
```

---

## ✅ ERLEDIGTES TAG83

- [x] ROADMAP_DRIVE_2025.md erstellt
- [x] eBay Kleinanzeigen API-Status recherchiert (keine öffentliche API)
- [x] Feature-Priorisierung und Timeline definiert
- [x] Technische Anforderungen dokumentiert

---

*Erstellt: 03.12.2025*
*Von: Claude (TAG83)*
