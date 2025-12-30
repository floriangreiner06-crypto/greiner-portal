# eAutoseller Bestand - Navigation

**Datum:** 2025-12-29  
**Status:** ✅ Im Menü verlinkt

---

## 📍 ZUGRIFF

### Im DRIVE Portal:

1. **Navigation:** Oben im Menü → **Verkauf** → **eAutoseller Bestand**
2. **Direkte URL:** `https://drive.auto-greiner.de/verkauf/eautoseller-bestand`

---

## 🎯 BEREchtIGUNGEN

**Zugriff:** Alle Benutzer mit `auftragseingang` Feature-Zugriff
- Admin
- Geschäftsleitung
- Verkaufsleitung
- Verkäufer
- Disposition

---

## 📋 MENÜ-STRUKTUR

```
Verkauf
├── Auftragseingang
├── Auslieferungen
├── eAutoseller Bestand  ← NEU
├── ────────────────────
├── Planung (nur GF + VK-Leitung)
│   ├── Budget-Planung
│   └── Lieferforecast
└── Tools
    ├── Leasys Programmfinder
    └── Leasys Kalkulator
```

---

## ✅ IMPLEMENTIERT

- ✅ Route erstellt: `/verkauf/eautoseller-bestand`
- ✅ Template erstellt: `verkauf_eautoseller_bestand.html`
- ✅ Im Menü verlinkt: `templates/base.html`
- ✅ KPIs werden angezeigt
- ✅ Fahrzeugliste (wird noch verfeinert)

---

**Status:** ✅ Navigation implementiert

