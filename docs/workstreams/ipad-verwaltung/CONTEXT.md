# iPad-Verwaltung (Mechaniker-Tablets) — Arbeitskontext

## Status: Aktiv (ABM + Mosyle-Registrierung)
## Letzte Aktualisierung: 2026-03-18

## Beschreibung

Zentrale Verwaltung der **15 iPads** im Einsatz bei den Mechanikern. Bisher: Einzeleinrichtung, keine Kontrolle über Geräte, Apps und Updates. Ziel: Einheitliche Konfiguration, Übersicht über Geräte und Zuweisung, optional Integration in DRIVE als zentraler Einstieg.

## Ausgangslage

- 15 iPads im Werkstatt-Einsatz (Mechaniker)
- Einrichtung bisher manuell pro Gerät
- Keine zentrale Kontrolle (Updates, Apps, Zuweisung, Verlust/Diebstahl)
- Wunsch: Zentrale Verwaltung, evtl. Anbindung an DRIVE

## Dokumente

- **VORSCHLAG_PLAN_IPAD_VERWALTUNG.md** — Optionen, Tool-Empfehlung, Phasenplan, DRIVE-Anbindung
- **ANLEITUNG_APPLE_BUSINESS_MANAGER_ANLEGEN.md** — Schritt-für-Schritt ABM-Registrierung
- **ANLEITUNG_ABM_GERAETE_AUFNEHMEN.md** — iPads in ABM aufnehmen (Configurator 2 + manuell, Checkliste)
- **NACHSTES_NACH_ABM_EINRICHTUNG.md** — Nächste Schritte nach ABM (Geräte, MDM, DRIVE)
- **MDM_INTEGRATION_DRIVE_REST_API.md** — MDM in DRIVE integrieren (REST-API, welche Tools, „selber bauen“)
- **MDM_KOSTEN_UND_EMPFEHLUNG.md** — Kostenvergleich, Empfehlung Mosyle/Intune/Jamf für 15 iPads
- **MOSYLE_APPS_BOOKS_LOCOSOFT.md** — Apps-&-Bücher (VPP) in Mosyle verbinden, Token aus ABM, Locosoft mit ausrollen
- **SAMSUNG_VS_APPLE_VERWALTUNG.md** — Vergleich: Samsung Knox (APIs, offener) vs. Apple ABM

## Optionen (Kurz)

| Option | Beschreibung | Kosten | Aufwand |
|--------|--------------|--------|---------|
| **A** | Nur Apple Business Manager (ABM) | Kostenlos | Gering |
| **B** | ABM + Cloud-MDM (z. B. Jamf Now, Mosyle) | Abo pro Gerät | Mittel |
| **C** | ABM + Self-Hosted MDM (MicroMDM/NanoMDM) | Keine Lizenz | Hoch (technisch) |
| **DRIVE** | Navi-Punkt + Doku/Links; optional Geräteliste | — | Gering |

Empfehlung und Details siehe **VORSCHLAG_PLAN_IPAD_VERWALTUNG.md**.

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Workstream angelegt, Vorschlag & Plan dokumentiert
- ✅ Apple Business Manager (ABM) eingerichtet
- ✅ MDM-Entscheidung: Mosyle Business (kostenlos bis 30 Geräte, REST-API für DRIVE)
- 🔧 Mosyle-Registrierung eingereicht – **Account-Review durch Mosyle läuft** (Aktivierungs-Link per E-Mail folgt)
- ❌ Nach Freischaltung: Mosyle mit ABM verbinden, Geräte zuweisen; optional DRIVE-Integration (Geräteliste per API)

## Abhängigkeiten

- **Werkstatt:** iPads werden von Mechanikern genutzt; inhaltliche Anforderungen (welche Apps, welche Portale) ggf. mit Werkstatt abstimmen.
- **Infrastruktur:** Bei Self-Hosted MDM: Server, SSL, Apple Push (APNS); ansonsten nur Browser-Zugriff auf ABM/MDM-Cloud.
- **Auth:** DRIVE-Login (LDAP) kann für Zugriff auf „iPad-Verwaltung“-Seite genutzt werden; MDM-Login bleibt separat (ABM/MDM-Anbieter).

## Nächste Schritte (nach Freigabe)

1. Apple Business Manager einrichten (kostenlos, Basis für alle Optionen)
2. Bestehende iPads in ABM aufnehmen (Seriennummern / Apple Configurator)
3. MDM-Anbieter wählen und an ABM anbinden (bei Option B oder C)
4. In DRIVE: Navi-Punkt „iPad-Verwaltung“ (Link zu ABM/MDM + interne Doku)
5. Optional: Geräteliste in DRIVE (manuell oder per MDM-API) für Übersicht „Wer hat welches iPad“
