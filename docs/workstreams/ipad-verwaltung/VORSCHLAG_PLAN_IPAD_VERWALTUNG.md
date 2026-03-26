# Vorschlag & Plan: Zentrale iPad-Verwaltung (Mechaniker)

**Stand:** 2026-03-18  
**Kontext:** 15 iPads im Werkstatt-Einsatz, bisher Einzeleinrichtung ohne zentrale Kontrolle. Ziel: zentrale Verwaltung, evtl. Integration in DRIVE.

---

## 1. Was ihr davon habt

- **Einheitliche Konfiguration:** Alle iPads gleiche Apps, Einstellungen, WLAN/Zertifikate
- **Kontrolle:** Wer hat welches Gerät, welcher iOS-Stand, welche Apps installiert
- **Sicherheit:** Remote-Sperre bei Verlust/Diebstahl, erzwungene Updates
- **Zeitersparnis:** Neue iPads oder Ersatzgeräte per „Zero Touch“ einrichten (über MDM)
- **Übersicht:** Eine Stelle (IT/Admin) sieht alle Geräte und kann eingreifen

---

## 2. Technische Basis: Apple Business Manager (ABM)

**Apple Business Manager** ist das **kostenlose** Portal von Apple für Firmen:

- **URL:** [business.apple.com](https://business.apple.com)
- **Kosten:** Keine
- **Funktionen (ohne MDM):**
  - Geräte per Seriennummer/Bestellung erfassen und zuweisen
  - Managed Apple IDs verwalten (optional)
  - Apps und Bücher zentral kaufen (VPP)
- **Wichtig:** Der **volle Nutzen** (Profile pushen, Remote-Befehle, automatische Einrichtung) kommt erst mit einem **MDM-Server** (Mobile Device Management). ABM ist aber die **Pflicht-Basis** für jede professionelle iPad-Verwaltung – auch für bestehende Geräte könnt ihr sie nachziehen (siehe „Bestehende Geräte“ unten).

**Bestehende Geräte in ABM aufnehmen:**  
Apple erlaubt das nachträgliche Hinzufügen mit **Apple Configurator** (App auf dem Mac): Gerät per USB verbinden, in Configurator „Zu Apple Business Manager hinzufügen“. Danach kann das Gerät einem MDM zugewiesen werden.

---

## 3. Optionen im Überblick

| | Option A: Nur ABM | Option B: ABM + Cloud-MDM | Option C: ABM + Self-Hosted MDM |
|--|-------------------|----------------------------|----------------------------------|
| **Kosten** | 0 € | Abo (z. B. 2–5 €/Gerät/Monat) | 0 € Lizenz, nur eigener Server |
| **Einrichtung** | Gering | Mittel | Hoch (SSL, APNS, Betrieb) |
| **Konfigurations-Profile** | Nein | Ja | Ja |
| **Remote-Sperre/-Wipe** | Nein | Ja | Ja |
| **App-Verteilung** | Manuell / VPP | Automatisch über MDM | Automatisch über MDM |
| **Zero-Touch Setup** | Eingeschränkt | Ja | Ja |
| **Betrieb** | Nur ABM-Web | Anbieter | Eigen (Updates, Backups) |

---

### Option A: Nur Apple Business Manager

- **Ideal für:** Erste Schritte, reine Übersicht und zentrale App-Käufe
- **Ihr macht:** ABM-Account anlegen, Geräte (Seriennummern) eintragen, ggf. Managed Apple IDs, App-Käufe über VPP
- **Ihr habt:** Keine automatischen Profile, kein Remote Lock/Wipe, keine echte „Fernsteuerung“
- **Aufwand:** Gering

---

### Option B: ABM + Cloud-MDM (Empfehlung für 15 iPads)

Ein **MDM-Dienst in der Cloud** übernimmt die Rolle des MDM-Servers. Ihr meldet euch im Browser an, ABM wird einmalig mit dem MDM verbunden, danach werden alle Geräte aus ABM im MDM angezeigt und verwaltet.

**Typische Anbieter (Beispiele):**

- **Jamf Now** — für kleine Teams (z. B. &lt; 25 Geräte), einfache Oberfläche, Apple-spezialisiert. Preise oft auf Anfrage (ca. 2–4 €/Gerät/Monat).
- **Mosyle** — günstige Einstiegsangebote, oft kostenlos bis 30 Geräte (Funktionen eingeschränkt), danach kostenpflichtig.
- **Scalefusion, ManageEngine MDM, Microsoft Intune** — weitere Optionen (Intune sinnvoll, wenn ihr schon Microsoft 365 stark nutzt).

**Vorteile:** Kein eigener Server, keine SSL/APNS-Einrichtung, Updates und Sicherheits-Patches vom Anbieter. Für **15 iPads** ist ein Cloud-MDM in der Regel die **pragmatischste Lösung**.

**Nachteile:** Laufende Kosten, Daten liegen beim Anbieter (Datenschutz ggf. prüfen).

---

### Option C: ABM + Self-Hosted MDM

**Beispiele:** MicroMDM (Open Source, für kleine Flotten), Nachfolger **NanoMDM**.

- **Vorteile:** Keine Lizenzkosten, volle Kontrolle über Daten und Infrastruktur.
- **Nachteile:** Ihr müsst selbst:
  - einen Server betreiben (z. B. auf 10.80.80.20 oder separatem Host),
  - SSL-Zertifikat und Apple Push Notification Service (APNS) einrichten,
  - das MDM warten und absichern.
- **Einschätzung:** Für 15 Geräte nur lohnenswert, wenn ihr ausdrücklich Self-Hosted wollt und die technische Betreuung (z. B. im Rahmen Infrastruktur-Workstream) übernehmen könnt. MicroMDM v1 ist bis Ende 2025 in Wartung; für Neuaufbau eher **NanoMDM** prüfen.

---

## 4. Was DRIVE konkret leisten kann

DRIVE ist ein **Flask-Portal** (ERP, Werkstatt, Controlling, …). Ein **eigenes, vollwertiges MDM** in DRIVE zu bauen ist **nicht sinnvoll** – MDM erfordert Apple-spezifische Protokolle, Zertifikate und Abnahmen. Stattdessen:

### 4.1 Sinnvolle DRIVE-Nutzung

1. **Zentraler Einstieg („iPad-Verwaltung“)**  
   - Neuer **Navi-Punkt** in DRIVE (z. B. unter Admin oder Werkstatt) mit:
     - **Link** zum Apple Business Manager und/oder zum gewählten MDM (Jamf, Mosyle, …)
     - **Kurze interne Anleitung:** „So verwaltet ihr die Mechaniker-iPads“ (PDF oder Doku-Seite)
   - Nutzer kommen wie gewohnt über DRIVE (LDAP-Login) und haben einen klaren Weg zur iPad-Verwaltung.

2. **Optionale Geräteliste in DRIVE**  
   - Einfache **Übersichtstabelle** im Portal: welches iPad (Seriennummer/Name) ist wem zugeordnet (z. B. Mitarbeiter aus `employees`), Status (z. B. „aktiv“, „in Reparatur“).
   - **Datenquelle:**  
     - Entweder **manuell** gepflegt (kleine Tabelle in PostgreSQL, z. B. `ipad_devices`: `id`, `device_name`, `serial`, `assigned_employee_id`, `notes`, `updated_at`).  
     - Oder später **per API** aus dem MDM (falls der gewählte MDM-Anbieter eine API anbietet und wir sie anbinden).
   - Das ersetzt **nicht** das MDM, gibt aber der Geschäftsleitung/Werkstatt einen schnellen Blick „Wer hat welches iPad“ ohne MDM-Login.

3. **Rechte**  
   - Zugriff auf den Navi-Punkt „iPad-Verwaltung“ nur für bestimmte Rollen (z. B. Admin, IT) über `requires_feature` / `role_restriction` in der DB-Navigation.

### 4.2 Was DRIVE nicht macht

- **Kein** Ersatz für ABM oder MDM (keine Profile, kein Remote Lock, keine App-Installation).
- **Kein** Anpassen eines externen MDM-Tools „in DRIVE“ – die Anpassung erfolgt im jeweiligen MDM; DRIVE verlinkt und kann optional eine Geräteliste anzeigen.

---

## 5. Empfehlung (Kurz)

- **Basis für alle:** **Apple Business Manager** sofort einrichten und bestehende iPads (per Apple Configurator) nachtragen.
- **Für 15 Mechaniker-iPads:** **Option B (ABM + Cloud-MDM)** wählen (z. B. Jamf Now oder Mosyle), um mit vertretbarem Aufwand volle Kontrolle zu bekommen.
- **DRIVE:** Navi-Punkt „iPad-Verwaltung“ mit Links zu ABM + MDM + interner Doku; optional einfache Geräteliste (manuell oder später per MDM-API).

Option C (Self-Hosted) nur, wenn ausdrücklich gewünscht und technisch abgesichert.

---

## 6. Phasenplan (Vorschlag)

| Phase | Inhalt | Dauer (grober Richtwert) |
|-------|--------|---------------------------|
| **1. Basis** | Apple Business Manager-Account anlegen, Rollen/Benutzer einrichten, Dokumentation (Wer macht was?) | 1–2 Tage |
| **2. Geräte** | Bestehende 15 iPads per Apple Configurator in ABM aufnehmen; neue Geräte künftig direkt über Händler/ABM registrieren | 1–2 Tage (je nach Anzahl gleichzeitig) |
| **3. MDM** | Cloud-MDM-Anbieter wählen (Jamf Now / Mosyle / …), ABM mit MDM verbinden, erste Geräte dem MDM zuweisen, Basis-Profile (WLAN, Sicherheit) erstellen | ca. 1 Woche (inkl. Tests) |
| **4. Rollout** | Alle 15 iPads ins MDM übernehmen, einheitliche Apps und Einstellungen ausrollen, Zero-Touch für Ersatzgeräte dokumentieren | 1–2 Wochen |
| **5. DRIVE** | Navi-Punkt „iPad-Verwaltung“ anlegen (Link zu ABM + MDM + Doku); optional Tabelle `ipad_devices` + einfache Übersichtsseite (Zuweisung Mechaniker ↔ iPad) | 1–2 Tage |

---

## 7. Nächste Schritte (Entscheidung)

1. **Entscheidung:** Option A, B oder C? (Empfehlung: B)
2. **Wenn B:** Welcher Anbieter? (Jamf Now, Mosyle, andere – ggf. Testphase nutzen)
3. **DRIVE:** Soll der Navi-Punkt „iPad-Verwaltung“ kommen? Soll eine einfache Geräteliste (Zuweisung iPad ↔ Mitarbeiter) im Portal gepflegt werden?
4. **Verantwortung:** Wer betreut ABM/MDM (IT/Admin)? Wer pflegt die Geräteliste in DRIVE (falls gewünscht)?

Sobald das geklärt ist, kann Phase 1 (ABM) starten und der Workstream **ipad-verwaltung** in den nächsten Sprints umgesetzt werden.
