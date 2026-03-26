# Samsung vs. Apple: Offenheit der zentralen Geräteverwaltung

**Stand:** 2026-03-18  
**Frage:** Wäre die zentrale Verwaltung bei Samsung-Geräten „offener“ als bei Apple?

---

## Kurzantwort: Ja – Samsung ist API-offener und weniger „ein Portal“

- **Apple:** Geräte müssen über **Apple Business Manager** (ABM) laufen; Aufnahme bestehender Geräte nur per **Apple Configurator** (Mac/iPhone), **kein** Seriennummer-Feld in der Weboberfläche bei vielen Accounts. Integration in eigene Systeme (z. B. DRIVE) nur über **MDM-REST-API** (Jamf, Mosyle, Intune etc.) – ABM selbst hat keine offene API für Geräteaufnahme.
- **Samsung:** **Knox** bietet **REST-APIs** (OAuth2), **Knox Mobile Enrollment**, **Knox Deployment Program**, **Knox Configure** – Geräte können programmatisch registriert und verwaltet werden. Viele **Third-Party-MDMs** (z. B. Scalefusion, Intune, VMware) verwalten Samsung-Geräte direkt; kein zwingendes „Samsung Business Manager“-Portal wie bei Apple. Für eine **Integration in DRIVE** (eigenes Dashboard, Geräteliste, Aktionen) sind die Knox-APIs gut nutzbar.

---

## Vergleich (vereinfacht)

| Aspekt | Apple (iPad/iPhone) | Samsung (Knox) |
|--------|---------------------|----------------|
| **Geräte aufnehmen** | ABM + Configurator (kein Seriennummer-Formular in ABM bei vielen Accounts) | Knox Mobile Enrollment, Knox Deployment Program, oft über MDM oder API |
| **APIs für eigene Integration** | Nur über ein **MDM mit API** (Jamf, Mosyle, Intune) – ABM selbst keine offene API | **Knox REST-APIs** (OAuth2), Geräteliste, Konfiguration, Enrollment programmatisch |
| **„Ein Portal“** | ABM ist Pflicht für DEP/ADE und Apps & Bücher | Kein zwingendes Samsung-Portal; Third-Party-MDM oder eigene Anwendung möglich |
| **Lock-in** | Stark an Apple-Ökosystem (ABM, Configurator, App Store) gebunden | Knox ist Samsung-spezifisch, aber viele MDMs und APIs – wirbt Samsung als „systemoffen“ |

---

## Für euren Kontext (15 Mechaniker-iPads)

- Ihr seid bereits bei **Apple (iPad) + ABM + Mosyle**. Ein Wechsel zu Samsung-Tablets wäre eine **neue Geräte- und Lizenzentscheidung**, kein reines „öffnen“ der Verwaltung.
- **Wenn ihr künftig Samsung-Geräte** (Tablets/Phones) einführt: Zentrale Verwaltung ist **offener** – Knox-APIs und Third-Party-MDMs erlauben eine **Integration in DRIVE** (Geräteliste, Status, Aktionen) ohne Umweg über ein einziges Hersteller-Portal wie ABM. Die Aufnahme neuer Geräte (Zero Touch, Enrollment) ist oft dokumentiert und API-gestützt.

**Fazit:** Ja – bei Samsung ist die zentrale Verwaltung **API-offener** und weniger an ein einziges Portal gebunden als bei Apple. Für reine iPad-Flotten ändert das nichts an der aktuellen ABM/Configurator-Logik; für künftige Mischflotten oder Samsung-Tablets wäre eine DRIVE-Integration über Knox-APIs oder ein Knox-fähiges MDM gut machbar.
