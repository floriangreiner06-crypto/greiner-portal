# 🗺️ GREINER DRIVE - ROADMAP Q1 2025

**Erstellt:** 2025-12-10 (TAG 111)  
**Gültig:** Dezember 2024 - März 2025  
**Status:** ✅ Freigegeben

---

## 📊 ÜBERSICHT

| Phase | Zeitraum | Fokus | Status |
|-------|----------|-------|--------|
| **Phase 1** | TAG 111-115 | Quick Wins | 🔲 Offen |
| **Phase 2** | TAG 116-130 | Verkauf Core | 🔲 Offen |
| **Phase 3** | TAG 131-145 | Controlling | 🔲 Offen |
| **Phase 4** | TAG 146-160 | Integration | 🔲 Offen |

---

## ⚡ PHASE 1: QUICK WINS (TAG 111-115)

*Hoher Nutzen, geringer Aufwand, sofort sichtbar*

### 1.1 TEK Überarbeitung + Forecast
**Aufwand:** 2-3 TAGs  
**Priorität:** 🔴 Kritisch

**Problem:**
- Aktueller Forecast berücksichtigt keine Werktage
- Keine Filterung nach Kostenstelle
- Abteilungsleiter haben keinen Überblick

**Lösung:**
- [ ] Werktage-Logik implementieren (Feiertage berücksichtigen)
- [ ] Forecast-Berechnung: `(IST / vergangene_Werktage) * Werktage_gesamt`
- [ ] Filter: Kostenstelle, Abteilung, Zeitraum
- [ ] Dashboard pro Abteilungsleiter

**Akzeptanzkriterien:**
- Forecast zeigt realistische Monatsend-Werte
- Jede Kostenstelle einzeln filterbar
- Abteilungsleiter sieht "sein" Team

---

### 1.2 LDAP-Rollen → Feature-Anpassung
**Aufwand:** 2-3 TAGs  
**Priorität:** 🟡 Hoch

**Problem:**
- Alle User sehen alle Features
- Keine Personalisierung nach Rolle
- Dashboards nicht angepasst

**Lösung:**
- [ ] Rollen-Mapping erweitern (LDAP-Gruppen → DRIVE-Rollen)
- [ ] Menü-Visibility nach Rolle
- [ ] Dashboard-Widgets nach Rolle
- [ ] Start-Seite nach Rolle (z.B. Verkäufer → Verkauf, Werkstatt → Aftersales)

**Rollen-Matrix:**

| Rolle | Bankenspiegel | Verkauf | Werkstatt | HR | Admin |
|-------|---------------|---------|-----------|-----|-------|
| Geschäftsleitung | ✅ | ✅ | ✅ | ✅ | ✅ |
| Verkaufsleiter | 🔲 | ✅ | 🔲 | 🔲 | 🔲 |
| Verkäufer | 🔲 | ✅ (eigene) | 🔲 | 🔲 | 🔲 |
| Werkstattleiter | 🔲 | 🔲 | ✅ | 🔲 | 🔲 |
| Buchhaltung | ✅ | 🔲 | 🔲 | 🔲 | 🔲 |
| HR | 🔲 | 🔲 | 🔲 | ✅ | 🔲 |

---

## 🚗 PHASE 2: VERKAUF CORE (TAG 116-130)

*Kritischer Workflow, täglich genutzt, HR-Entlastung*

### 2.1 Verkäufer-Provisionssystem
**Aufwand:** 8-10 TAGs  
**Priorität:** 🔴 Kritisch

**Aktueller Workflow (manuell):**
```
Locosoft → CSV Export → Excel (teilautomatisiert) → PDF → Verkäufer
```

**Neuer Workflow (DRIVE):**
```
┌─────────────────────────────────────────────────────────┐
│ 1. IMPORT                                               │
│    Locosoft CSV → DRIVE (automatisch via Celery)        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. VORLAUF                                              │
│    Verkäufer sieht seine Ablieferungen                  │
│    → Prüft Daten → Gibt frei ✓                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. FREIGABE                                             │
│    Verkaufsleiter sieht alle Vorlauf-Freigaben          │
│    → Prüft → Gibt frei ✓                                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 4. ABRECHNUNG                                           │
│    HR sieht freigegebene Abrechnungen                   │
│    → Rechnet ab → PDF generiert → Archiv                │
└─────────────────────────────────────────────────────────┘
```

**Technische Umsetzung:**
- [ ] DB-Schema: `provisionen`, `provision_positionen`, `provision_freigaben`
- [ ] Celery Job: Locosoft CSV Import
- [ ] API: `/api/provisionen/...`
- [ ] UI: Vorlauf-Ansicht (Verkäufer)
- [ ] UI: Freigabe-Ansicht (Verkaufsleiter)
- [ ] UI: Abrechnungs-Ansicht (HR)
- [ ] PDF-Generator (Abrechnungsbeleg)
- [ ] E-Mail-Benachrichtigungen (Workflow-Schritte)

**Provisionsregeln (zu klären):**
- Grundprovision pro Fahrzeug?
- Staffelung nach Marge/DB?
- Zusatzprovisionen (Finanzierung, Garantie, Zubehör)?
- Kulanz-Regelungen?

---

### 2.2 Verkäufer Dashboard
**Aufwand:** 4-5 TAGs  
**Priorität:** 🟡 Hoch

**Features:**
- [ ] **Zielerfüllung:** IST vs. SOLL (Stück + Umsatz)
- [ ] **Forecast:** Hochrechnung Monatsende (mit Werktagen)
- [ ] **Leasingausläufer:** Potenziale aus auslaufenden Verträgen
- [ ] **Provision-Preview:** Voraussichtliche Provision aktueller Monat
- [ ] **Pipeline:** Offene Angebote, Bestellungen
- [ ] **Vergleich:** Eigene Performance vs. Team-Durchschnitt

**Datenquellen:**
- Locosoft: Verkäufe, Aufträge, Angebote
- eAutoSeller (Phase 4): Leasingausläufer
- Provisionssystem (2.1): Provision-Daten

---

## 📊 PHASE 3: CONTROLLING (TAG 131-145)

*Management-Value, Planung, Transparenz*

### 3.1 Budget-Planung (BWA-basiert)
**Aufwand:** 5-7 TAGs  
**Priorität:** 🟡 Hoch

**Features:**
- [ ] **PLAN-Erfassung:** Budget pro Kostenstelle/Monat
- [ ] **IST-Abgleich:** Automatisch aus FIBU (549k Buchungen)
- [ ] **Abweichungsanalyse:** PLAN vs. IST (€ + %)
- [ ] **Ampelsystem:** Grün (<5%), Gelb (5-15%), Rot (>15%)
- [ ] **Zeitreihe:** Monat/Quartal/Jahr
- [ ] **Drill-Down:** Kostenstelle → Konten → Buchungen

**DB-Schema:**
```sql
budget_plan (
    id, kostenstelle, konto_bereich, 
    jahr, monat, plan_betrag,
    created_by, created_at
)

v_budget_vergleich (View)
    → JOIN budget_plan + fibu_buchungen
    → Berechnet IST, Abweichung, Status
```

---

### 3.2 EcoDMS Integration (Rechnungsfreigabe)
**Aufwand:** 4-5 TAGs  
**Priorität:** 🟡 Hoch

**Voraussetzungen:**
- ✅ EcoDMS API bereits getestet (Bankenspiegel)
- [ ] API-Credentials für Produktiv

**Workflow:**
```
EcoDMS                         DRIVE
────────                       ─────
Rechnung eingescannt    →      
                        ←      Polling: Neue Rechnungen?
Rechnung abrufen        →      
                               Zur Freigabe anzeigen
                               Abteilungsleiter gibt frei ✓
                        ←      Status: Freigegeben
Rechnung als "freigegeben" markieren
```

**Umsetzung:**
- [ ] Celery Job: EcoDMS Polling (alle 15 Min)
- [ ] DB: `ecodms_rechnungen` (Cache + Status)
- [ ] API: `/api/rechnungen/...`
- [ ] UI: Freigabe-Liste (filtert nach Kostenstelle/User)
- [ ] EcoDMS API: Status-Update bei Freigabe

---

## 🔗 PHASE 4: INTEGRATION (TAG 146-160)

*Externe Systeme, höherer Aufwand*

### 4.1 eAutoSeller API
**Aufwand:** 6-8 TAGs  
**Priorität:** 🟡 Mittel

**Ziel:** Verkaufsleiter Dashboard mit externen Daten

**Features:**
- [ ] Fahrzeugbestand synchronisieren
- [ ] Leasingausläufer-Potenziale
- [ ] Standzeiten-Analyse
- [ ] Preisempfehlungen

**Voraussetzungen:**
- [ ] API-Zugang beantragen
- [ ] API-Dokumentation beschaffen
- [ ] Test-Account einrichten

---

### 4.2 WhatsApp-Anbindung
**Aufwand:** 8-10 TAGs  
**Priorität:** 🟢 Nice-to-have

**Offene Fragen:**
- [ ] Catch-Integration analysieren (nur Empfang oder auch Versand?)
- [ ] WhatsApp Business API Kosten klären
- [ ] DSGVO: Opt-In Prozess definieren
- [ ] Use Cases definieren (Terminbestätigung? Service-Erinnerung?)

**Erst starten wenn:**
- Compliance-Fragen geklärt
- Kosten akzeptiert
- Catch-API verstanden

---

## 📝 TRACKING

### Fortschritt

| Phase | Geplant | Erledigt | Status |
|-------|---------|----------|--------|
| Phase 1 | 5 TAGs | 0 | 🔲 0% |
| Phase 2 | 15 TAGs | 0 | 🔲 0% |
| Phase 3 | 12 TAGs | 0 | 🔲 0% |
| Phase 4 | 18 TAGs | 0 | 🔲 0% |
| **Gesamt** | **50 TAGs** | **0** | **🔲 0%** |

### Meilensteine

| Meilenstein | Ziel-TAG | Status |
|-------------|----------|--------|
| TEK Forecast live | TAG 113 | 🔲 |
| LDAP-Rollen aktiv | TAG 115 | 🔲 |
| Provisionssystem MVP | TAG 125 | 🔲 |
| Verkäufer Dashboard live | TAG 130 | 🔲 |
| Budget-Planung live | TAG 140 | 🔲 |
| EcoDMS Integration | TAG 145 | 🔲 |

---

## 📚 REFERENZEN

- `docs/BWA_KONTEN_MAPPING_FINAL.md` - BWA-Struktur für Budget-Planung
- `docs/KONZEPT_ZINSEN_FINAL.md` - Kostenstellen-Logik
- `docs/SESSION_WRAP_UP_TAG110.md` - Celery Migration

---

**Nächster Schritt:** TAG 111 - TEK Forecast starten

---

*Erstellt: 2025-12-10 | Autor: Claude | Version: 1.0*
