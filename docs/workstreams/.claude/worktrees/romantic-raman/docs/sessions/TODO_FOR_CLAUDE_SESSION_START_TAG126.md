# TODO FOR CLAUDE - SESSION START TAG126

**Erstellt:** 2025-12-18
**Vorherige Session:** TAG125

---

## Kontext

Das Werkstatt Live-Board wurde in TAG125 neu implementiert mit:
- Karten-basierter UI für Mechaniker-Übersicht
- Gudat-Integration für disponierte Aufträge
- Auftrag-Detail-Modal bei Klick
- Auto-Refresh alle 30 Sekunden

---

## Offene Punkte aus TAG125

### 1. Live-Board Verbesserungen (Optional)
- [ ] Gudat-Aufträge: Echte Start-/Endzeiten aus Disposition statt geschätzter Zeiten
- [ ] Sound-Benachrichtigung bei Status-Änderungen
- [ ] Mobile/Tablet-Optimierung für Werkstatt-Nutzung
- [ ] Drag & Drop für Auftrags-Umplanung (falls gewünscht)

### 2. Git Push ausstehend
Der lokale Commit `f5de7cb` muss noch gepusht werden:
```bash
git push origin feature/tag82-onwards
```

---

## Wichtige Dateien TAG125

| Datei | Beschreibung |
|-------|--------------|
| `api/werkstatt_live_api.py` | Live-Board API mit Gudat-Integration |
| `templates/aftersales/werkstatt_liveboard.html` | Karten-UI mit Modal |
| `routes/werkstatt_routes.py` | Route `/werkstatt/liveboard` |

---

## Sync-Befehle (falls nicht bereits synchronisiert)

```bash
# API + Template + Routes syncen
cp /mnt/greiner-portal-sync/api/werkstatt_live_api.py /opt/greiner-portal/api/
cp /mnt/greiner-portal-sync/templates/aftersales/werkstatt_liveboard.html /opt/greiner-portal/templates/aftersales/
cp /mnt/greiner-portal-sync/routes/werkstatt_routes.py /opt/greiner-portal/routes/

# Neustart
sudo systemctl restart greiner-portal
```

---

## Notizen

- Live-Board URL: `/werkstatt/liveboard` oder `/werkstatt/drive/liveboard`
- API-Endpoint für Auftragsdetails: `/api/werkstatt/live/auftrag/<nr>`
- Gudat-Client: `tools/gudat_client.py`

---

*Bereit für TAG126*
