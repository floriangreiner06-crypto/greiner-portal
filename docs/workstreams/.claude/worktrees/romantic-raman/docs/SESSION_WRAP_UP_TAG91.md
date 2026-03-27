# SESSION WRAP-UP TAG 91
**Datum:** 2025-12-04 (späte Session)
**Fokus:** Werkstatt-Leistungsübersicht - Produktivitäts-Kennzahl & Bugfixes

---

## ✅ ERLEDIGT

### 1. **Type 1 / Type 2 Korrektur in loco_times**
**Problem:** Falsche Annahme über Type-Bedeutung
- ❌ Vorher: Type 1 = Auftragszeit, Type 2 = Anwesenheit
- ✅ Jetzt:  Type 1 = **Anwesenheit** (Tages-Stempeluhr), Type 2 = **Auftragszeit** (produktive Arbeit)

**Beispiel vom 03.11.2025 (Mitarbeiter 5018):**
```
Type 1: 07:47 - 16:45 = 538 Min (EINE Zeile = Tages-Anwesenheit)
Type 2: Viele Zeilen mit order_number (Auftrags-Stempelungen, mit Duplikaten!)
```

**Geänderte Datei:** `scripts/sync/sync_werkstatt_zeiten.py`
```python
# Anwesenheit = Type 1 (nicht Type 2!)
WHERE type = 1
```

### 2. **Filter für echte Mechaniker**
**Problem:** Produktivität war 16.9% (viel zu niedrig)
- 55 "Mechaniker" angezeigt, aber viele ohne Stempelzeit (Büro, Verkauf, etc.)
- Diese zogen den Durchschnitt runter

**Lösung:** `AND stempelzeit_min > 0` in API-Query
- Jetzt nur noch 12 echte Mechaniker
- Produktivität: **84.7%** ✅ realistisch

**Geänderte Datei:** `api/werkstatt_api.py`

### 3. **Problemfälle-Tab: Duplikate & Auftragsnummer**
**Problem:** Gleicher Auftrag erschien 3x (JOIN mit loco_labours erzeugt Duplikate)

**Lösung:** 
- `SELECT DISTINCT` in der Query
- Neue Spalte "Auftrag" mit `auftrags_nr` hinzugefügt

**Geänderte Datei:** 
- `api/werkstatt_api.py` (DISTINCT)
- `templates/aftersales/werkstatt_uebersicht.html` (Spalte Auftrag)

---

## 📊 AKTUELLE WERTE (Vormonat November 2025)

| Kennzahl | Wert |
|----------|------|
| Mechaniker | 12 |
| Produktivität | 84.7% |
| Leistungsgrad | 86.1% |
| Aufträge | 1.303 |
| Stempelzeit | 95.822 Min |
| Anwesenheit | 113.180 Min |

**Top-Mechaniker (Produktivität):**
- Majer, Jan: 90.8%
- Smola, Walter: ~98%
- Ebner, Patrick: ~91%

---

## 📁 GEÄNDERTE DATEIEN

| Datei | Änderung |
|-------|----------|
| `scripts/sync/sync_werkstatt_zeiten.py` | Type 1 = Anwesenheit (nicht Type 2) |
| `api/werkstatt_api.py` | Filter stempelzeit > 0, DISTINCT für Problemfälle |
| `templates/aftersales/werkstatt_uebersicht.html` | Spalte "Auftrag" in Problemfälle-Tab |

---

## 🔧 DEPLOYMENT-STATUS

```bash
# Alle Dateien wurden deployed:
cp /mnt/greiner-portal-sync/scripts/sync/sync_werkstatt_zeiten.py /opt/greiner-portal/scripts/sync/
cp /mnt/greiner-portal-sync/api/werkstatt_api.py /opt/greiner-portal/api/
cp /mnt/greiner-portal-sync/templates/aftersales/werkstatt_uebersicht.html /opt/greiner-portal/templates/aftersales/

# Sync wurde ausgeführt
python3 scripts/sync/sync_werkstatt_zeiten.py

# Service wurde neugestartet
sudo systemctl restart greiner-portal
```

---

## 📧 EMAIL-INFRASTRUKTUR (für nächste Session)

Microsoft Graph API ist bereits implementiert:
```
/opt/greiner-portal/api/graph_mail_connector.py  ← Connector
/opt/greiner-portal/api/mail_api.py              ← Mail-API
/opt/greiner-portal/scripts/send_daily_auftragseingang.py  ← Beispiel
```

---

## 🔗 ERKENNTNISSE

### loco_times Type-Bedeutung:
| Type | Bedeutung | Zeilen pro Tag | order_number |
|------|-----------|----------------|--------------|
| 1 | Anwesenheit (Kommen/Gehen) | 1 | 0 oder NULL |
| 2 | Auftrags-Stempelung | Viele (mit Duplikaten!) | Auftragsnummer |

### Produktivitäts-Formel:
```
Produktivität = Stempelzeit (Type 2) / Anwesenheit (Type 1) × 100
```
- Zielwert: 70-90%
- < 60% = Unproduktiv (viel Leerlauf)
- > 95% = Sehr gut (kaum Nebenzeiten)

---

## ⏭️ NÄCHSTE SESSION: TAG 92

Siehe: `TODO_FOR_CLAUDE_SESSION_START_TAG92.md`
