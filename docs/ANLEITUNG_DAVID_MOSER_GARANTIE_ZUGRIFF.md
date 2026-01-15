# Anleitung: David Moser - Garantie-Zugriff einrichten

**Datum:** 2026-01-14  
**User:** David Moser (ID: 27)  
**Ziel:** Zugriff auf `/aftersales/garantie/auftraege`

---

## ✅ STATUS

### Bereits erledigt:
1. ✅ Title-Mapping erweitert: "Gewährleistung und Auftragsvorbereitung" → Rolle "service"
2. ✅ Rolle "service" hat Zugriff auf:
   - `aftersales` Feature ✅
   - `teilebestellungen` Feature ✅

### Aktueller Stand:
- **DB-Rolle:** werkstatt (hat bereits Zugriff!)
- **Title-basierte Rolle:** service (nach nächstem Login)
- **Beide Rollen haben Zugriff auf Garantie!**

---

## 🔧 OPTIONEN

### Option 1: Nichts tun (empfohlen)
David Moser hat bereits Zugriff, weil:
- Seine DB-Rolle "werkstatt" hat Zugriff auf `aftersales` ✅
- Nach nächstem Login wird er automatisch Rolle "service" bekommen (auch mit Zugriff) ✅

**Aktion:** Einfach testen ob es funktioniert!

### Option 2: DB-Rolle anpassen (optional)
Falls du willst, dass David die Rolle "service" in der DB hat (statt "werkstatt"):

```sql
-- Alte Rolle entfernen
DELETE FROM user_roles 
WHERE user_id = 27 AND role_id = (SELECT id FROM roles WHERE name = 'werkstatt');

-- Neue Rolle hinzufügen
INSERT INTO user_roles (user_id, role_id, assigned_at)
SELECT 27, id, NOW()
FROM roles
WHERE name = 'service'
ON CONFLICT DO NOTHING;
```

**Aber:** Beide Rollen haben Zugriff, also nicht nötig!

---

## 🧪 TESTEN

1. **Als David Moser einloggen:**
   - Username: `david.moser@auto-greiner.de`
   - URL testen: `http://10.80.80.20:5000/aftersales/garantie/auftraege`

2. **Navigation prüfen:**
   - Nach Login sollte "After Sales" im Menü sichtbar sein
   - "Garantieaufträge" sollte klickbar sein

3. **Falls nicht sichtbar:**
   - Service-Neustart: `sudo systemctl restart greiner-portal`
   - User ausloggen und neu einloggen (damit neue Rolle geladen wird)

---

## 📊 AKTUELLE ZUGRIFFE

### David Moser (ID: 27):
- **DB-Rolle:** werkstatt
- **Title-basierte Rolle:** service (nach Login)
- **Beide haben Zugriff auf:**
  - ✅ `aftersales` → `/aftersales/garantie/auftraege`
  - ✅ `teilebestellungen` → Navigation "After Sales"

### Feature-Zugriffe (aus DB):
```sql
-- Prüfen welche Features David hat
SELECT DISTINCT fa.feature_name
FROM feature_access fa
JOIN user_roles ur ON fa.role_name = (SELECT name FROM roles WHERE id = ur.role_id)
WHERE ur.user_id = 27;
```

---

## ✅ FAZIT

**David Moser sollte bereits Zugriff haben!**

- Falls nicht: Service-Neustart + User neu einloggen
- Falls immer noch nicht: DB-Rolle prüfen (sollte "werkstatt" oder "service" sein)

---

*Erstellt: TAG 190 | Autor: Claude AI*
