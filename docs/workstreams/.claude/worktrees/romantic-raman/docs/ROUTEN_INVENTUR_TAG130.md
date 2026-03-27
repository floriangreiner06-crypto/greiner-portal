# Routen-Inventur TAG 130

**Erstellt:** 2025-12-20
**Zweck:** Portal aufräumen vor User-Onboarding

---

## Zusammenfassung

| Kategorie | Anzahl Routes | Status |
|-----------|---------------|--------|
| Auth & Core | 6 | Behalten |
| Bankenspiegel | 7 | Behalten |
| Controlling | 4 | Behalten |
| Verkauf | 5 | Behalten |
| Urlaubsplaner | 5 | Behalten |
| Werkstatt/Aftersales | 26 | **Prüfen - Duplikate!** |
| Teile | 3 | Behalten |
| Serviceberater | 2 | Behalten |
| Admin | 7 | Behalten |
| Jahresprämie | 5 | Behalten |
| **GESAMT** | **~70** | |

---

## 1. AUTH & CORE (app.py)

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/login` | Login-Page | `login.html` | OK |
| `/logout` | Logout | - | OK |
| `/` `/start` | Dynamische Startseite | Redirect | OK |
| `/dashboard` | Haupt-Dashboard | `dashboard.html` | OK |
| `/health` | Health-Check | JSON | OK |
| `/debug/user` | Debug User-Session | JSON | **Entfernen in Prod** |

---

## 2. BANKENSPIEGEL (/bankenspiegel/)

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/bankenspiegel` | Redirect → Dashboard | - | OK |
| `/bankenspiegel/dashboard` | Hauptseite | `bankenspiegel_dashboard.html` | OK |
| `/bankenspiegel/konten` | Kontenübersicht | `bankenspiegel_konten.html` | OK |
| `/bankenspiegel/transaktionen` | Transaktionsliste | `bankenspiegel_transaktionen.html` | OK |
| `/bankenspiegel/zinsen-analyse` | Zinsen Dashboard | `zinsen_analyse.html` | OK |
| `/bankenspiegel/einkaufsfinanzierung` | Redirect → Fahrzeugfin. | - | OK |
| `/bankenspiegel/fahrzeugfinanzierungen` | Fahrzeug-Finanzierungen | `einkaufsfinanzierung.html` | OK |
| `/bankenspiegel/konto/<id>` | Konto-Detail | `bankenspiegel_konto_detail.html` | OK |

---

## 3. CONTROLLING (/controlling/)

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/controlling/dashboard` | Controlling Dashboard | `controlling/dashboard.html` | OK |
| `/controlling/bwa` | BWA Ansicht | `controlling/bwa.html` | OK |
| `/controlling/tek` | Tägliche Erfolgskontrolle | `controlling/tek_dashboard.html` | OK |
| `/controlling/api/tek` | TEK API | JSON | OK |
| `/controlling/api/tek/detail` | TEK Drill-Down | JSON | OK |

---

## 4. VERKAUF (/verkauf/)

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/verkauf/auftragseingang` | Auftragseingang | `verkauf_auftragseingang.html` | OK |
| `/verkauf/auftragseingang/detail` | Detail-Ansicht | `verkauf_auftragseingang_detail.html` | OK |
| `/verkauf/auslieferung/detail` | Auslieferungen | `verkauf_auslieferung_detail.html` | OK |
| `/verkauf/leasys-kalkulator` | Leasys Kalkulator | `leasys_kalkulator.html` | OK |
| `/verkauf/leasys-programmfinder` | Leasys Programmfinder | `leasys_programmfinder.html` | OK |

---

## 5. URLAUBSPLANER

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/urlaubsplaner` | Redirect → V2 | - | OK |
| `/urlaubsplaner/v2` | Moderne UI | `urlaubsplaner_v2.html` | OK |
| `/urlaubsplaner/chef` | Chef-Übersicht | `urlaubsplaner_chef.html` | OK |
| `/urlaubsplaner/admin` | HR-Admin | `urlaubsplaner_admin.html` | OK |
| `/admin/organigramm` | Organigramm | `organigramm.html` | OK |

---

## 6. WERKSTATT / AFTERSALES

### 6.1 Doppelte Routes (app.py vs. werkstatt_routes.py)

Diese Routes sind **DOPPELT** definiert:

| Route | app.py | werkstatt_routes.py | Aktion |
|-------|--------|---------------------|--------|
| `/werkstatt` | ✓ (→ cockpit) | ✓ (→ uebersicht) | **KONFLIKT!** |
| `/werkstatt/cockpit` | ✓ | ✓ | Duplikat entfernen |
| `/werkstatt/live` | ✓ | ✓ | Duplikat entfernen |
| `/werkstatt/stempeluhr` | ✓ | ✓ | Duplikat entfernen |
| `/werkstatt/tagesbericht` | ✓ | ✓ | Duplikat entfernen |
| `/werkstatt/teile-status` | ✓ | ✓ | Duplikat entfernen |
| `/werkstatt/auftraege` | ✓ | ✓ | Duplikat entfernen |
| `/werkstatt/anwesenheit` | ✓ (deaktiviert) | ✓ | Duplikat entfernen |
| `/aftersales/kapazitaet` | ✓ | ✓ | Duplikat entfernen |

### 6.2 Nur in app.py

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/werkstatt/dashboard` | Werkstatt Dashboard | `aftersales/werkstatt_dashboard.html` | OK |
| `/werkstatt/uebersicht` | Legacy | `aftersales/werkstatt_uebersicht.html` | **Legacy?** |
| `/werkstatt/intelligence` | ML Dashboard | `werkstatt_intelligence.html` | OK |
| `/mein-bereich` | Serviceberater Start | `sb/mein_bereich.html` | OK |

### 6.3 Nur in werkstatt_routes.py

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/werkstatt/serviceberater` | SB Übersicht | `aftersales/serviceberater.html` | OK |
| `/werkstatt/teilebestellungen` | Teilebestellungen | `aftersales/teilebestellungen.html` | Duplikat mit Teile? |
| `/werkstatt/bestellung/<id>` | Detail | `aftersales/bestellung_detail.html` | OK |
| `/werkstatt/preisradar` | Preisradar | `aftersales/preisradar.html` | Duplikat mit Teile? |

### 6.4 DRIVE Module (werkstatt_routes.py)

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/werkstatt/drive/briefing` | Morgen-Briefing | `aftersales/drive_briefing.html` | OK |
| `/werkstatt/drive/kulanz` | Kulanz-Monitor | `aftersales/drive_kulanz.html` | OK |
| `/werkstatt/drive/kapazitaet` | ML-Kapazität | `aftersales/drive_kapazitaet.html` | OK |
| `/werkstatt/liveboard` | Live-Board | `aftersales/werkstatt_liveboard.html` | OK |
| `/werkstatt/liveboard/gantt` | Gantt-Ansicht | `aftersales/werkstatt_liveboard_gantt.html` | OK |
| `/werkstatt/reparaturpotenzial` | Upselling | `aftersales/werkstatt_reparaturpotenzial.html` | OK |

### 6.5 Monitor-Routes (ohne Login)

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/monitor/stempeluhr` | Monitor Stempeluhr | `aftersales/werkstatt_stempeluhr_monitor.html` | OK |
| `/monitor/liveboard` | Monitor Liveboard | `aftersales/werkstatt_liveboard.html` | OK |
| `/monitor/liveboard/gantt` | Monitor Gantt | `aftersales/werkstatt_liveboard_gantt.html` | OK |

---

## 7. TEILE (/aftersales/teile/)

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/aftersales/teile/bestellungen` | Bestellungen | `aftersales/teilebestellungen.html` | Duplikat? |
| `/aftersales/teile/bestellung/<nr>` | Detail | `aftersales/bestellung_detail.html` | OK |
| `/aftersales/teile/preisradar` | Preisradar | `aftersales/preisradar.html` | Duplikat? |

---

## 8. SERVICEBERATER (/aftersales/serviceberater/)

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/aftersales/serviceberater/` | Controlling | `aftersales/serviceberater.html` | OK |
| `/aftersales/serviceberater/controlling` | Controlling | `aftersales/serviceberater.html` | OK |

---

## 9. ADMIN

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/admin/system-status` | Redirect → Celery | - | OK |
| `/admin/celery/` | Task Manager | `admin/celery_tasks.html` | OK |
| `/admin/celery/start/<task>` | Task starten | JSON | OK |
| `/admin/celery/status/<id>` | Task-Status | JSON | OK |
| `/admin/celery/schedule/*` | Schedule-Verwaltung | JSON | OK |

---

## 10. JAHRESPRÄMIE (/jahrespraemie/)

| Route | Funktion | Template | Status |
|-------|----------|----------|--------|
| `/jahrespraemie/` | Übersicht | `jahrespraemie/index.html` | OK |
| `/jahrespraemie/neu` | Neue Berechnung | `jahrespraemie/neu.html` | OK |
| `/jahrespraemie/<id>` | Berechnung | `jahrespraemie/berechnung.html` | OK |
| `/jahrespraemie/<id>/mitarbeiter` | Mitarbeiter | `jahrespraemie/mitarbeiter.html` | OK |
| `/jahrespraemie/<id>/kulanz` | Kulanz | `jahrespraemie/kulanz.html` | OK |
| `/jahrespraemie/<id>/export` | Export | `jahrespraemie/export.html` | OK |

---

## PROBLEME & HANDLUNGSBEDARF

### 1. Doppelte Werkstatt-Routes (KRITISCH)

`app.py` und `werkstatt_routes.py` definieren **dieselben Routes**!

**Problem:** Flask nimmt die zuerst registrierte Route.

**Lösung:**
- Alle Werkstatt-Routes in `werkstatt_routes.py` zentralisieren
- Aus `app.py` entfernen

### 2. Doppelte Teile-Routes

| Route | Ort 1 | Ort 2 |
|-------|-------|-------|
| Teilebestellungen | `/werkstatt/teilebestellungen` | `/aftersales/teile/bestellungen` |
| Preisradar | `/werkstatt/preisradar` | `/aftersales/teile/preisradar` |

**Lösung:** Einen Pfad wählen, andere als Redirect

### 3. Legacy-Routes

- `/werkstatt/uebersicht` - Alte Ansicht, durch Dashboard ersetzt?
- `/werkstatt/anwesenheit` - Bereits deaktiviert (Type 1 Problem)

### 4. Debug-Route in Production

- `/debug/user` - Sollte in Production deaktiviert sein

---

## EMPFEHLUNG: Konsolidierte Struktur

```
/                           → Dynamische Startseite
├── /dashboard              → Allgemeines Dashboard
├── /mein-bereich           → Serviceberater Startseite
│
├── /bankenspiegel/         → Finanzen
│   ├── dashboard
│   ├── konten
│   ├── transaktionen
│   ├── zinsen-analyse
│   └── fahrzeugfinanzierungen
│
├── /controlling/           → BWA & TEK
│   ├── dashboard
│   ├── bwa
│   └── tek
│
├── /verkauf/               → Verkauf
│   ├── auftragseingang
│   ├── auslieferung
│   ├── leasys-kalkulator
│   └── leasys-programmfinder
│
├── /werkstatt/             → Aftersales (KONSOLIDIERT)
│   ├── dashboard           → Hauptseite Werkstatt
│   ├── cockpit             → Ampel-System
│   ├── liveboard           → Wer arbeitet woran
│   ├── stempeluhr          → Stempelungen
│   ├── teile-status        → Fehlende Teile
│   ├── tagesbericht        → Kontrolle
│   ├── reparaturpotenzial  → Upselling
│   └── drive/              → ML-Features
│       ├── briefing
│       ├── kulanz
│       └── kapazitaet
│
├── /teile/                 → Teile (statt /aftersales/teile/)
│   ├── bestellungen
│   ├── preisradar
│   └── bestellung/<id>
│
├── /serviceberater/        → Serviceberater-Controlling
│   └── controlling
│
├── /urlaubsplaner/         → Urlaub
│   ├── v2
│   ├── chef
│   └── admin
│
├── /jahrespraemie/         → Jahresprämie
│   └── ...
│
├── /admin/                 → Administration
│   ├── celery/
│   └── organigramm
│
└── /monitor/               → Monitor ohne Login
    ├── stempeluhr
    └── liveboard
```

---

## Nächste Schritte

1. [ ] Doppelte Werkstatt-Routes bereinigen
2. [ ] Teile-Routes konsolidieren
3. [ ] Legacy-Routes entfernen oder redirecten
4. [ ] Navigation (base.html) aktualisieren
5. [ ] Debug-Route für Production deaktivieren
