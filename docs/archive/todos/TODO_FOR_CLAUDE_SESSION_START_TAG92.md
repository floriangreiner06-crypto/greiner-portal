# TODO FOR CLAUDE - SESSION START TAG 92
**Erstellt:** 2025-12-04
**Vorherige Session:** TAG 91 (Werkstatt Produktivität)

---

## 🎯 HAUPTTHEMA: Werkstatt LIVE Monitoring

### 1. **LIVE Monitoring von Aufträgen**
**Ziel:** Echtzeit-Überwachung laufender Werkstatt-Aufträge

**Machbarkeitsanalyse:**
- [ ] Welche Daten liefert Locosoft in Echtzeit? (loco_times, loco_orders?)
- [ ] Können wir offene Aufträge mit aktuellem Stempelzeit-Status sehen?
- [ ] Polling-Intervall bestimmen (alle 5 Min?)
- [ ] Dashboard-Konzept für offene Aufträge mit Ampel-Status

**Prüfen:**
```sql
-- Gibt es "offene" Aufträge in loco_orders?
SELECT * FROM loco_orders WHERE status = 'offen' LIMIT 10;

-- Aktuelle Stempelungen heute?
SELECT * FROM loco_times WHERE DATE(start_time) = DATE('now') AND end_time IS NULL;
```

---

### 2. **Warn-Email für SB & Serviceleiter**

**Infrastruktur vorhanden:** ✅
```
/opt/greiner-portal/api/graph_mail_connector.py
/opt/greiner-portal/api/mail_api.py
/opt/greiner-portal/scripts/send_daily_auftragseingang.py  ← Beispiel
```

**Trigger-Szenarien definieren:**
- [ ] Auftrag überschreitet Vorgabezeit um X% (z.B. 150%)?
- [ ] Auftrag steht seit X Stunden ohne Fortschritt?
- [ ] Leistungsgrad unter Schwellwert (z.B. < 50%)?

**Empfänger-Mapping klären:**
- [ ] Wie ist "zuständiger Serviceberater" zu einem Auftrag zugeordnet?
- [ ] Wer ist Serviceleiter (Eskalation)?
- [ ] Tabelle für Empfänger-Mapping erstellen?

---

### 3. **Abrechnungskontrolle**

**Anforderungen klären:**
- [ ] Was genau soll geprüft werden?
- [ ] Differenz Vorgabe vs. abgerechnete AW?
- [ ] Nachträglich geänderte Aufträge?
- [ ] Welche Tabellen sind relevant?

---

### 4. **"Das Digitale Autohaus" API Integration**

**Status:** HAR-Analyse wurde durchgeführt

**Fragen an User:**
- [ ] Wo liegt die HAR-Datei? (Server oder lokaler PC?)
- [ ] Welche Endpoints wurden identifiziert?
- [ ] Authentifizierung (Token, Cookie, API-Key)?
- [ ] Welche Daten wollen wir abrufen/synchronisieren?
- [ ] Gibt es offizielle API-Doku oder nur Reverse-Engineering?

**HAR-Datei suchen:**
```bash
find /opt/greiner-portal -name "*.har" 2>/dev/null
find /home -name "*.har" 2>/dev/null
```

---

## 📚 KONTEXT AUS TAG 91

### Werkstatt-Leistungsübersicht funktioniert:
- ✅ Dashboard mit 2 Tachos (Leistungsgrad + Produktivität)
- ✅ 5 Tabs (Ranking, Trend, Detail, Vergleich, Problemfälle)
- ✅ Filter: Zeitraum, Betrieb, Sortierung, "Inkl. Ehemalige"
- ✅ Sync-Job läuft täglich 19:15 Uhr

### loco_times Type-Bedeutung (WICHTIG!):
| Type | Bedeutung | Beispiel |
|------|-----------|----------|
| 1 | Anwesenheit (Tages-Stempeluhr) | 07:47 - 16:45 = 538 Min |
| 2 | Auftrags-Stempelung (produktiv) | Mit order_number, Duplikate möglich |

### Aktuelle Kennzahlen (November 2025):
- 12 aktive Mechaniker
- Produktivität: 84.7%
- Leistungsgrad: 86.1%

---

## 🔧 QUICK-START BEFEHLE

```bash
# Projekt-Status
cd /opt/greiner-portal
systemctl status greiner-portal

# Graph-Mail testen
python3 -c "from api.graph_mail_connector import GraphMailConnector; print('OK')"

# DB-Struktur prüfen (für Live-Monitoring)
sqlite3 data/greiner_controlling.db ".tables" | grep -i order
```

---

## 📁 RELEVANTE DATEIEN

| Datei | Zweck |
|-------|-------|
| `api/werkstatt_api.py` | Werkstatt-Leistungs-API |
| `api/graph_mail_connector.py` | Email via Microsoft Graph |
| `api/mail_api.py` | Mail-Endpunkte |
| `scripts/sync/sync_werkstatt_zeiten.py` | Täglicher Sync |
| `templates/aftersales/werkstatt_uebersicht.html` | Dashboard |

---

## ❓ OFFENE FRAGEN AN USER

1. **HAR-Datei:** Wo liegt sie? Server oder lokaler PC?
2. **Abrechnungskontrolle:** Was genau soll geprüft werden?
3. **Warn-Email Empfänger:** Wer ist zuständiger SB pro Auftrag? Gibt es ein Mapping?
4. **Eskalation:** Wer ist Serviceleiter? Eine Person oder pro Standort?

---

*Session-Start: Dieses Dokument lesen, dann mit User offene Fragen klären.*
