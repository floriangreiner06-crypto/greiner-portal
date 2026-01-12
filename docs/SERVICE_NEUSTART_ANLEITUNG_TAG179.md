# Service-Neustart Anleitung - TAG 179

**Datum:** 2026-01-10  
**Grund:** Neue API-Endpunkte (Metadaten, Export) aktivieren

---

## 🔄 SERVICE-NEUSTART

### Schritt 1: Service-Neustart durchführen

**Auf dem Server (10.80.80.20):**

```bash
# Sudo-Passwort: OHL.greiner2025
echo 'OHL.greiner2025' | sudo -S systemctl restart greiner-portal
```

**Oder interaktiv:**
```bash
sudo systemctl restart greiner-portal
# Passwort: OHL.greiner2025
```

### Schritt 2: Service-Status prüfen

```bash
# Sudo-Passwort: OHL.greiner2025
echo 'OHL.greiner2025' | sudo -S systemctl status greiner-portal
```

**Oder interaktiv:**
```bash
sudo systemctl status greiner-portal
# Passwort: OHL.greiner2025
```

**Erwartetes Ergebnis:**
```
● greiner-portal.service - Greiner Portal Flask Application
   Loaded: loaded (/etc/systemd/system/greiner-portal.service; enabled; vendor preset: enabled)
   Active: active (running) since ...
```

### Schritt 3: Logs prüfen

```bash
# Sudo-Passwort: OHL.greiner2025
echo 'OHL.greiner2025' | sudo -S journalctl -u greiner-portal -n 50 --no-pager
```

**Oder interaktiv:**
```bash
sudo journalctl -u greiner-portal -n 50 --no-pager
# Passwort: OHL.greiner2025
```

**Prüfen:**
- ✅ "Finanzreporting API registriert: /api/finanzreporting/"
- ✅ Keine Fehler beim Start

---

## ✅ VERIFIZIERUNG

### Test 1: Metadaten-Endpunkt

```bash
curl http://localhost:5000/api/finanzreporting/cube/metadata | python3 -m json.tool
```

**Erwartetes Ergebnis:**
```json
{
    "dimensionen": [...],
    "measures": [...],
    "standorte": [...],
    "kostenstellen": [...],
    "konto_ebenen": [...]
}
```

### Test 2: Export-Endpunkt (CSV)

```bash
curl -I "http://localhost:5000/api/finanzreporting/cube/export?format=csv&dimensionen=zeit&measures=betrag&von=2024-09-01&bis=2024-09-30"
```

**Erwartetes Ergebnis:**
```
Content-Type: text/csv; charset=utf-8-sig
Content-Disposition: attachment; filename=finanzreporting_cube_...
```

---

## 📋 VOLLSTÄNDIGE TEST-ANLEITUNG

Siehe: `docs/TEST_ANLEITUNG_FINANZREPORTING_TAG179.md`

---

**Nach Neustart:** Alle neuen Endpunkte sollten verfügbar sein! 🚀
