# MDM-Kosten und Empfehlung für 15 Mechaniker-iPads

**Stand:** 2026-03-18  
**Ausgangslage:** 15 iPads, ABM eingerichtet, Wunsch nach Integration in DRIVE (ein Login, Geräteliste im Portal).

---

## 1. Kostenüberblick (ca. 15 Geräte)

| Tool | Kosten (15 iPads) | REST-API für DRIVE? | Zielgruppe |
|------|------------------|----------------------|------------|
| **Mosyle Business FREE** | **0 €** (bis 30 Geräte kostenlos) | **Ja** (businessapi.mosyle.com, JWT) | KMU, Schulen |
| **Jamf Now** | ca. 2–4 US$/Gerät/Monat → **ca. 30–60 €/Monat** (erste 3 Geräte oft gratis) | **Nein** | &lt; 25 Mitarbeiter |
| **Jamf Pro** | Auf Anfrage, deutlich teurer (meist größere Umgebungen) | **Ja** (umfangreich) | Enterprise |
| **Microsoft Intune** | Oft **in M365 Business Premium enthalten** (sonst ca. 6,90 €/User/Monat standalone) | **Ja** (Microsoft Graph) | M365-Kunden |
| **MicroMDM / NanoMDM** | 0 € (Open Source) | **Ja** | Self-Hosted, technisch versiert |

*Preise sind Richtwerte; bei Jamf/Intune bitte aktuelle Angebote einholen.*

---

## 2. Empfehlung für eure Zwecke

**Kriterien:** 15 iPads, möglichst geringe Kosten, Integration in DRIVE (Geräteliste ohne zweiten Account), einfache Verwaltung.

### Empfehlung: **Mosyle Business FREE**

| Kriterium | Mosyle Business FREE |
|-----------|----------------------|
| **Kosten** | **0 €** für bis zu 30 Geräte – ihr bleibt mit 15 iPads unter dem Limit. |
| **DRIVE-Integration** | **REST-API** (businessapi.mosyle.com) – Geräteliste, Gerätedetails, ggf. Aktionen in DRIVE abbildbar. |
| **Funktionen** | Vollwertiges MDM: Zero-Touch, ABM-Anbindung, Profile, App-Verteilung, Remote Lock/Wipe, Apple-fokussiert. |
| **Aufwand** | Account anlegen, ABM verbinden, Geräte zuweisen – vergleichbar mit Jamf Now. |
| **Nachteil** | Wenn ihr später &gt; 30 Geräte habt: kostenpflichtige Pläne (z. B. ab ca. 5,50–9 US$/Gerät/Jahr). |

Damit erfüllt ihr: **keine laufenden MDM-Kosten**, **API für DRIVE** (ein Login), **volles MDM** für 15 iPads.

---

### Alternative 1: **Microsoft Intune** (wenn ihr M365 Business nutzt)

- Intune ist in **Microsoft 365 Business Premium** (und einigen anderen Plänen) **bereits enthalten**.
- Dann: **0 € Zusatzkosten** für MDM, Verwaltung über Azure/Intune-Portal.
- **Microsoft Graph API** erlaubt Integration in DRIVE (Geräteliste, Status, Aktionen).
- **Nachteil:** Oberfläche und Konzepte sind eher Microsoft-zentriert; für reine Apple-Flotten ist Mosyle oft direkter.

**Sinnvoll,** wenn ihr ohnehin M365 Business Premium (oder vergleichbar) im Einsatz habt und ein einheitliches Microsoft-Ökosystem wollt.

---

### Alternative 2: **Jamf Now**

- **Kosten:** ca. 2–4 US$/Gerät/Monat → bei 15 Geräten grob **30–60 €/Monat**.
- **Keine öffentliche API** → in DRIVE nur **Link** auf Jamf-Weboberfläche, keine echte Geräteliste/Aktionen aus DRIVE.
- Einfache Bedienung, Apple-fokussiert, aber für euren Wunsch „alles in DRIVE“ weniger geeignet.

**Sinnvoll,** wenn ihr explizit Jamf wollt und auf die DRIVE-Integration verzichten könnt.

---

### Alternative 3: **Jamf Pro**

- Volle **REST-API**, sehr gute **DRIVE-Integration** möglich.
- **Kosten:** in der Regel deutlich höher als Jamf Now, oft für größere Umgebungen (z. B. 500+ Mitarbeiter) ausgelegt – für 15 iPads meist **überdimensioniert und teuer**.

**Sinnvoll** nur bei deutlich größerer Gerätezahl und Budget für Enterprise-MDM.

---

## 3. Kurzvergleich „besser für unsere Zwecke“

| Zweck | Besser geeignet |
|-------|------------------|
| **Geringe Kosten** | Mosyle Business FREE (0 €) oder Intune (wenn in M365 enthalten). |
| **Integration in DRIVE (ein Login, Geräteliste)** | Mosyle (API) oder Intune (Graph API); Jamf Now **nicht** (keine API). |
| **Einfache Einrichtung, reine Apple-Flotte** | Mosyle oder Jamf Now. |
| **Bereits M365 Business im Einsatz** | Intune prüfen (evtl. schon dabei). |

**Gesamt:** Für **15 iPads**, **Integration in DRIVE** und **minimale Kosten** ist **Mosyle Business FREE** die beste Wahl. Falls ihr **M365 Business Premium** nutzt, lohnt ein Blick auf **Intune** (kostenlos im Paket + Graph API).

---

## 4. Nächste Schritte bei Mosyle

1. **Account:** [business.mosyle.com](https://business.mosyle.com) → Mosyle Business FREE registrieren (bis 30 Geräte kostenlos).
2. **ABM anbinden:** In Mosyle Apple Business Manager verbinden (Organisations-ID, Token etc. wie in der Mosyle-Doku).
3. **Geräte:** Die 15 iPads in ABM dem Mosyle-MDM zuweisen, in Mosyle Profile anlegen.
4. **DRIVE:** API-Token in Mosyle erzeugen, in `config/credentials.json` hinterlegen; in DRIVE Modul für Geräteliste (und optional Aktionen) über Mosyle-API bauen – dann sehen Admins alles in DRIVE mit einem Login.

Details zur API: Mosyle TechDocs / Business API (REST, JWT-Auth). Die konkrete DRIVE-Integration (Endpoints, Credential-Struktur) kann nach der Mosyle-Einrichtung umgesetzt werden.
