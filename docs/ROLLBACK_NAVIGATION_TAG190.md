# Rollback-Anleitung: DB-Navigation TAG 190

**Datum:** 2026-01-14  
**Status:** 🔄 Rollback-Plan

---

## 🚨 Schneller Rollback (falls buggy)

### **Schritt 1: DB-Navigation deaktivieren**

```bash
cd /opt/greiner-portal
sed -i 's/USE_DB_NAVIGATION=true/USE_DB_NAVIGATION=false/' .env
```

Oder manuell in `.env`:
```
USE_DB_NAVIGATION=false
```

### **Schritt 2: Service neu starten**

```bash
echo "OHL.greiner2025" | sudo -S systemctl restart greiner-portal
```

### **Schritt 3: Prüfen**

```bash
systemctl status greiner-portal --no-pager | head -5
```

**Dauer:** < 2 Minuten

---

## ✅ Nach Rollback

- ✅ Fallback auf hardcoded Navigation aktiv
- ✅ Alle URLs funktionieren weiterhin
- ✅ Keine Datenverluste
- ✅ Navigation-Items bleiben in DB (können später wieder aktiviert werden)

---

## 🔧 Falls Probleme auftreten

### **Problem: Navigation komplett weg**
→ Rollback durchführen (siehe oben)

### **Problem: Sub-Dropdowns funktionieren nicht**
→ CSS/JavaScript prüfen (bereits implementiert)
→ Browser-Cache leeren (Strg+F5)

### **Problem: Items fehlen**
→ Prüfen: `SELECT * FROM navigation_items WHERE active = true;`
→ Feature-Zugriff prüfen

---

## 📞 Support

Bei Problemen:
1. Rollback durchführen
2. Logs prüfen: `journalctl -u greiner-portal -n 50`
3. Browser-Konsole prüfen (F12)
