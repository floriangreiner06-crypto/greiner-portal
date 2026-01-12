# Quick Start: Test der Neuerungen - TAG 179

**Datum:** 2026-01-10

---

## 🚀 SCHNELLSTART

### 1. Service-Neustart (ERFORDERLICH)

```bash
# Sudo-Passwort: OHL.greiner2025
echo 'OHL.greiner2025' | sudo -S systemctl restart greiner-portal
```

**Prüfen:**
```bash
echo 'OHL.greiner2025' | sudo -S systemctl status greiner-portal
```

---

### 2. Frontend-Test

**URL öffnen:**
```
http://10.80.80.20:5000/controlling/finanzreporting
```

**Schnelltest:**
1. ✅ Seite lädt ohne Fehler
2. ✅ Dropdowns sind befüllt (Standorte, Konto-Ebenen)
3. ✅ Filter setzen (z.B. Zeitraum: 2024-09-01 bis 2024-10-31, Konto-Ebene: 800)
4. ✅ "Daten laden" klicken
5. ✅ Daten werden angezeigt (KPI-Karten, Chart, Tabelle)
6. ✅ Export-Buttons sind aktiviert (grün)
7. ✅ "CSV exportieren" klicken → Download startet
8. ✅ "Excel exportieren" klicken → Download startet

---

### 3. API-Test (Optional)

**Metadaten-Endpunkt:**
```bash
curl http://10.80.80.20:5000/api/finanzreporting/cube/metadata | python3 -m json.tool
```

**Export-Endpunkt (CSV):**
```bash
curl "http://10.80.80.20:5000/api/finanzreporting/cube/export?format=csv&dimensionen=zeit&measures=betrag&von=2024-09-01&bis=2024-09-30" -o test.csv
```

---

## 📋 VOLLSTÄNDIGE ANLEITUNG

Siehe: `docs/TEST_ANLEITUNG_FINANZREPORTING_TAG179.md`

---

**Viel Erfolg! 🎉**
