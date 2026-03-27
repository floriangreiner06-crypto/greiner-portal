# TODO FOR CLAUDE SESSION START - TAG88

**Erstellt:** 2025-12-01  
**Vorgänger:** TAG87

---

## 📋 KONTEXT

TAG87 hat das **Jahresprämie-Modul** implementiert:
- DB-Schema, API, Frontend komplett
- Upload + Berechnung funktioniert
- Validierung mit Lohnbuchhaltung steht aus

---

## 🎯 PRIORITÄTEN TAG88

### 1. Validierung Jahresprämie (falls Feedback vom User)
- Kategorisierung (VZ/TZ/MJ/Azubi) korrekt?
- Berechtigungslogik passt?
- Berechnungsergebnisse stimmen?
- Ggf. Anpassungen an `api/jahrespraemie_api.py`

### 2. Mögliche Erweiterungen
- Excel-Export (openpyxl)
- PDF-Belege für einzelne MA
- Eigene Berechtigung `jahrespraemie`

---

## 📁 WICHTIGE DATEIEN

```
/opt/greiner-portal/
├── api/jahrespraemie_api.py          # API-Logik
├── routes/jahrespraemie_routes.py    # Routes
├── templates/jahrespraemie/          # Templates
├── migrations/add_jahrespraemie_tables.sql
└── CLAUDE.md                         # Projekt-Kontext (LESEN!)
```

---

## 🔧 SYNC-WORKFLOW (aus CLAUDE.md)

```bash
# Mount-Pfad (KORREKT!):
/mnt/greiner-portal-sync/

# Server → Windows (nach Änderungen auf Server)
rsync -av --progress \
  --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='logs/*.log' --exclude='data/*.db' --exclude='.git' \
  /opt/greiner-portal/ /mnt/greiner-portal-sync/

# Windows → Server (nach Claude-Änderungen)
rsync -av --progress --exclude='.git' --exclude='*.tar.gz' \
  /mnt/greiner-portal-sync/ /opt/greiner-portal/
```

---

## ✅ CHECKLISTE SESSION-START

- [ ] CLAUDE.md lesen
- [ ] SESSION_WRAP_UP_TAG87.md lesen
- [ ] User-Feedback zu Jahresprämie?
- [ ] Git-Status prüfen

---

*Erstellt: 2025-12-01*
