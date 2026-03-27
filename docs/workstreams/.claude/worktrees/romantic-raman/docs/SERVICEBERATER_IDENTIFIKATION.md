# Serviceberater-Identifikation

**Erstellt:** 2025-12-21
**Zweck:** Unterscheidung echte Serviceberater vs. andere MA im Ranking

---

## Datenquellen

| Quelle | Feld | Bedeutung |
|--------|------|-----------|
| **Locosoft** | `is_customer_reception = true` | Kundenannahme/Serviceberater |
| **LDAP/SQLite** | `department_name = 'Service'` | Abteilung Service |

---

## Ergebnis: Echte Serviceberater

| MA-ID | Name | Standort | Locosoft (is_customer_reception) | LDAP (department) | **Status** |
|-------|------|----------|----------------------------------|-------------------|------------|
| 4000 | Herbert Huber | Deggendorf | ✅ true | Service | ✅ **SERVICEBERATER** |
| 4005 | Andreas Kraus | Deggendorf | ✅ true | Service | ✅ **SERVICEBERATER** |
| 5009 | Valentin Salmansberger | Deggendorf | ✅ true | Service | ✅ **SERVICEBERATER** |
| 4002 | Leonhard Keidl | Landau | ✅ true + Meister | Werkstatt | ✅ **SERVICEBERATER** |
| 4003 | Edith Egner | Landau | ✅ true | Kundenzentrale | ✅ **SERVICEBERATER** |

---

## Keine Serviceberater (aber im Ranking)

| MA-ID | Name | Locosoft | LDAP (department) | **Tatsächliche Rolle** |
|-------|------|----------|-------------------|------------------------|
| 3003 | Dennis Blüml | ❌ false | T&Z | **Teileverkäufer** |
| 3001 | Bruno Wieland | ❌ false | T&Z | **Teile & Zubehör** |
| 3004 | Thomas Stangl | ❌ false | T&Z | **Teile & Zubehör** |
| 3007 | Matthias König | ❌ false | Service | **Serviceleiter** (nicht SB) |
| 1025 | Aleyna Irep | ❌ false | Kundenzentrale | **Unfallschaden/Faktura** |
| 1014 | Christian Meyer | ❌ false (mechanic) | Werkstatt | **Werkstattleiter/Mechaniker** |
| 1008 | Jennifer Bielmeier | ❌ false | Disposition | **Disposition** |
| 1016 | Sandra Brendel | ❌ false | Kundenzentrale | **Kundenzentrale** |
| 1006 | Stephan Metzner | ❌ false | Kundenzentrale | **Kundenzentrale Landau** |
| 1036 | Doris Egginger | ❌ false | Kundenzentrale | **Kundenzentrale** |
| 1003 | Rolf Sterr | ❌ false (salesman) | Verkauf | **Verkäufer** (GL) |
| 1023 | Margit Schreder | ❌ false | Kundenzentrale | **Kundenzentrale Landau** |

---

## Warum erscheinen sie im Ranking?

Diese MA erscheinen, weil sie als `order_taking_employee_no` in Aufträgen eingetragen sind:

- **Teileverkäufer (3xxx):** Erstellen Teileverkäufe am Tresen
- **Faktura/Kundenzentrale:** Erstellen Rechnungen für Unfallschäden, Garantie
- **Serviceleiter:** Erstellt manchmal selbst Aufträge

---

## Empfehlung: Filter für Ranking

### Option A: Locosoft-Flag nutzen (empfohlen)

```sql
WHERE e.is_customer_reception = true
```

**Vorteil:** Direkt in Locosoft gepflegt, immer aktuell

### Option B: MA-Nummern-Bereich

```python
SERVICEBERATER_IDS = [4000, 4002, 4003, 4005, 5009]
```

**Nachteil:** Manuell pflegen

### Option C: LDAP-Abteilung

```sql
WHERE department_name = 'Service' AND role != 'serviceleiter'
```

**Nachteil:** Nicht alle SBs haben department='Service'

---

## Aktuelle Konfiguration in serviceberater_api.py

```python
SERVICEBERATER_CONFIG = {
    # Deggendorf
    4000: {'name': 'Herbert Huber', 'standort': 'deggendorf'},
    4005: {'name': 'Andreas Kraus', 'standort': 'deggendorf'},
    5009: {'name': 'Valentin Salmansberger', 'standort': 'deggendorf'},
    # Landau
    4002: {'name': 'Leonhard Keidl', 'standort': 'landau'},
    4003: {'name': 'Edith Egner', 'standort': 'landau'},
}
```

**Status:** ✅ Korrekt konfiguriert

---

## Fehlende Serviceberater?

| MA-ID | Name | Standort | Notiz |
|-------|------|----------|-------|
| 5003 | Walter Smola | Landau | In Config, aber keine Rechnungen Dez? |
| 1006 | Stephan Metzner | Landau | In Config als Vertretung |

→ Prüfen ob noch aktiv / Vertretung

---

**Erstellt von:** Claude (DRIVE Portal Analyse)
**Tag:** 133
