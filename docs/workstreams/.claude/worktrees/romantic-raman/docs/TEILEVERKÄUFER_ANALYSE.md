# Teileverkäufer-Analyse

**Erstellt:** 2025-12-21
**Zweck:** Identifikation der Teileverkäufer im Serviceberater-Ranking

---

## Mitarbeiter mit MA-Nr 3xxx (Teile & Zubehör)

| MA-ID | Name | LDAP Abteilung | Standort | Im Ranking Dez? | Tatsächliche Rolle |
|-------|------|----------------|----------|-----------------|-------------------|
| 3000 | Georg Kandler | T&Z | Deggendorf | ❌ Nein | Teileverkäufer |
| 3001 | Bruno Wieland | T&Z | Deggendorf | ✅ 31 Rechnungen | **Teileverkäufer** |
| 3002 | Matthias Steinbauer | T&Z | Landau | ❌ Nein | Teileverkäufer |
| 3003 | Dennis Blüml | T&Z | Deggendorf | ✅ 165 Rechnungen | **Teileverkäufer** |
| 3004 | Thomas Stangl | T&Z | Deggendorf | ✅ 102 Rechnungen | **Teileverkäufer** |
| 3005 | Leurim Drmaku | - | Deggendorf | ❌ Nein | (nicht in LDAP) |
| 3006 | Stefan Geier | T&Z | Deggendorf | ❌ Nein | Teileverkäufer |
| 3007 | Matthias König | **Service** | Deggendorf | ✅ 77 Rechnungen | **Serviceleiter** |
| 3008 | Marcel Döring | - | Deggendorf | ❌ Nein | (nicht in LDAP) |
| 3009 | Fabian Klammsteiner | Verwaltung | Deggendorf | ❌ Nein | Verwaltung |
| 3010 | Stefanie Bittner | T&Z | Deggendorf | ❌ Nein | Teileverkäufer |

---

## Warum erscheinen Teileverkäufer im Ranking?

Teileverkäufer werden als `order_taking_employee_no` eingetragen, wenn sie:
- **Teile am Tresen verkaufen** (Theken-Verkauf)
- **Zubehör-Aufträge erstellen** (z.B. Anhängerkupplung, Dachbox)
- **Ersatzteil-Bestellungen** für Kunden aufgeben

---

## Unterscheidung: Locosoft-Flag

| Merkmal | Serviceberater | Teileverkäufer |
|---------|----------------|----------------|
| `is_customer_reception` | ✅ true | ❌ false |
| MA-Nummernbereich | 4xxx, 5xxx | 3xxx |
| LDAP Abteilung | Service | T&Z |
| Typische Aufträge | Wartung, Reparatur | Teileverkauf, Zubehör |

---

## Empfehlung: Filter für Ranking

### Aktuelle Implementierung (TAG133)

```python
# In serviceberater_api.py
ist_sb = row.get('is_customer_reception', False)
```

Mit dem `is_customer_reception` Flag werden jetzt nur echte Serviceberater im Ranking angezeigt:
- ✅ Herbert Huber (4000)
- ✅ Andreas Kraus (4005)
- ✅ Valentin Salmansberger (5009)
- ✅ Leonhard Keidl (4002)
- ✅ Edith Egner (4003)

Und diese werden **ausgeschlossen**:
- ❌ Dennis Blüml (3003) - Teileverkäufer
- ❌ Thomas Stangl (3004) - Teileverkäufer
- ❌ Bruno Wieland (3001) - Teileverkäufer
- ❌ Matthias König (3007) - Serviceleiter

---

## Sonderfall: Matthias König (3007)

- **MA-Nummer:** 3007 (3xxx-Bereich = T&Z)
- **LDAP-Abteilung:** Service
- **Locosoft is_customer_reception:** false
- **Rolle:** Serviceleiter

→ Matthias König ist **Serviceleiter**, nicht Serviceberater. Er erstellt manchmal selbst Aufträge, soll aber nicht im SB-Ranking erscheinen.

---

**Erstellt von:** Claude (DRIVE Portal Analyse)
**Tag:** 133
