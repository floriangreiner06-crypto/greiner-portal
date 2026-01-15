# Migration TAG 190: Feature-Zugriffsverwaltung

**Datum:** 2026-01-14  
**Status:** Implementiert, Migration erforderlich

---

## 📋 ÜBERSICHT

Phase 1 der Feature-Zugriffsverwaltung ist implementiert. Die Feature-Zugriffe können jetzt über die UI bearbeitet werden und werden in der Datenbank gespeichert.

---

## ✅ IMPLEMENTIERTE ÄNDERUNGEN

### 1. Datenbank-Schema
- **Tabelle:** `feature_access`
- **Migration-Script:** `migrations/migration_tag190_feature_access.sql`
- **Zweck:** Speichert Feature-Rollen-Zuordnungen

### 2. API-Endpoints
- `GET /api/admin/feature-access` - Lädt Feature-Zugriffe (DB + Config-Fallback)
- `POST /api/admin/feature-access/<feature>/role/<role>` - Fügt Rolle zu Feature hinzu
- `DELETE /api/admin/feature-access/<feature>/role/<role>` - Entfernt Rolle von Feature
- `POST /api/admin/feature-access/<feature>` - Aktualisiert alle Rollen für ein Feature

### 3. Utility-Funktionen
- `get_feature_access_from_db()` - Lädt aus DB mit Fallback auf Config
- `has_feature_access_db()` - Prüft Feature-Zugriff (DB-basiert)

### 4. Frontend
- Feature-Cards sind jetzt editierbar
- "Bearbeiten"-Button pro Feature
- Modal zum Bearbeiten von Rollen
- Speichern-Funktionalität

---

## 🚀 MIGRATION DURCHFÜHREN

### Schritt 1: Migration-Script ausführen

```bash
# Auf Server einloggen
ssh ag-admin@10.80.80.20

# Migration ausführen
cd /opt/greiner-portal
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/migration_tag190_feature_access.sql
```

**Erwartete Ausgabe:**
```
CREATE TABLE
CREATE INDEX
CREATE INDEX
INSERT 0 75  (oder ähnlich)
COMMENT
```

### Schritt 2: Service-Neustart

```bash
# Service neustarten (nach Code-Änderungen)
sudo systemctl restart greiner-portal

# Logs prüfen
journalctl -u greiner-portal -f
```

### Schritt 3: Testing

1. **Admin-Seite öffnen:**
   - http://10.80.80.20:5000/admin/rechte
   - Tab "Feature-Zugriff" öffnen

2. **Feature bearbeiten:**
   - Auf "Bearbeiten"-Button klicken (Stift-Icon)
   - Modal öffnet sich
   - Rollen per Klick hinzufügen/entfernen
   - "Speichern" klicken

3. **Prüfen:**
   - Änderungen sollten sofort sichtbar sein
   - Seite neu laden → Änderungen bleiben erhalten

---

## 🔍 VERIFIZIERUNG

### Datenbank prüfen:

```sql
-- Prüfe ob Tabelle existiert
SELECT COUNT(*) FROM feature_access;

-- Prüfe Beispiel-Daten
SELECT feature_name, role_name, created_by 
FROM feature_access 
WHERE feature_name = 'bankenspiegel'
ORDER BY role_name;
```

**Erwartet:** ~75 Zeilen (je nach Anzahl Features × Rollen)

### API testen:

```bash
# Feature-Zugriffe laden
curl http://10.80.80.20:5000/api/admin/feature-access

# Sollte JSON mit feature_access und title_to_role zurückgeben
```

---

## ⚠️ WICHTIGE HINWEISE

### Rückwärtskompatibilität
- ✅ Bestehende `FEATURE_ACCESS` in `config/roles_config.py` bleibt erhalten
- ✅ DB-Werte haben Priorität, Config als Fallback
- ✅ Keine Breaking Changes

### Berechtigungen
- Nur User mit `admin`-Feature-Zugriff können Feature-Zugriffe bearbeiten
- API-Endpoints prüfen `current_user.can_access_feature('admin')`

### Fallback-Verhalten
- Wenn DB leer ist → verwendet `FEATURE_ACCESS` aus Config
- Wenn DB Daten hat → DB hat Priorität
- Migration füllt DB mit Initial-Daten aus Config

---

## 🐛 BEKANNTE ISSUES

**Keine bekannt** - Implementierung ist neu

---

## 📝 NÄCHSTE SCHRITTE

Nach erfolgreicher Migration:
1. ✅ Feature-Zugriffe können über UI bearbeitet werden
2. ⏳ Phase 2: Individuelle Startseite (optional)

---

*Erstellt: TAG 190 | Autor: Claude AI*
