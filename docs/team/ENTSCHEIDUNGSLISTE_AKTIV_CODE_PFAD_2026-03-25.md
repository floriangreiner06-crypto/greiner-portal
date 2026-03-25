# Entscheidungsliste AKTIV_CODE_PFAD (2026-03-25)

Ziel: Die 33 untracked Dateien im App-Code-Pfad in klare Entscheidungen ueberfuehren.

Legende:
- **BEHALTEN** = Datei fachlich sinnvoll, im Repo verbleiben
- **INTEGRIEREN** = Datei ist sinnvoll, aber mit TODO (z. B. Navigation/Rechte/Tests/Verkabelung)
- **VERWERFEN** = entfernen/archivieren (aktuell keine Kandidaten mit hoher Sicherheit)

## 1) Hilfe-Modul (klar aktiv)

- `api/hilfe_api.py` -> **INTEGRIEREN** (API ist vorhanden und wird in Templates/Routes genutzt)
- `routes/hilfe_routes.py` -> **INTEGRIEREN** (rendert Hilfe-Templates, fachlich konsistent)
- `templates/hilfe/hilfe_uebersicht.html` -> **INTEGRIEREN**
- `templates/hilfe/hilfe_suche.html` -> **INTEGRIEREN**
- `templates/hilfe/hilfe_artikel.html` -> **INTEGRIEREN**
- `templates/hilfe/hilfe_kategorie.html` -> **INTEGRIEREN**
- `templates/hilfe/hilfe_admin.html` -> **INTEGRIEREN**
- `templates/hilfe/hilfe_admin_artikel.html` -> **INTEGRIEREN**
- `static/css/hilfe.css` -> **INTEGRIEREN**

Begruendung: Route-/Template- und API-Referenzen sind vorhanden; Modul ist dokumentiert im Workstream `Hilfe`.

## 2) Verkauf Dashboard / Motocost / Zielauswertung (klar aktiv)

- `api/verkauf_vkl_dashboard_service.py` -> **INTEGRIEREN**
- `templates/verkauf_dashboard.html` -> **INTEGRIEREN**
- `templates/verkauf_motocost.html` -> **INTEGRIEREN**
- `templates/verkauf_zielauswertung.html` -> **INTEGRIEREN**
- `static/js/verkauf_dashboard.js` -> **INTEGRIEREN**
- `static/js/verkauf_motocost.js` -> **INTEGRIEREN**
- `static/js/verkauf_zielauswertung.js` -> **INTEGRIEREN**

Begruendung: Referenzen in `routes/verkauf_routes.py` und bestehender Feature-Logik (`verkauf_dashboard`) sind sichtbar.

## 3) Fahrzeuganlage / Scanner (klar aktiv)

- `api/fahrzeuganlage_api.py` -> **INTEGRIEREN**
- `api/fahrzeugschein_scanner.py` -> **INTEGRIEREN**
- `templates/fahrzeuganlage.html` -> **INTEGRIEREN**

Begruendung: Route in `routes/werkstatt_routes.py` und API-Endpunkte sind vorhanden; Workstream-Doku beschreibt die Implementierung.

## 4) Garantie / Gudat / Dokumente (fachlich aktiv, Integrationspruefung)

- `api/garantie_precheck_service.py` -> **INTEGRIEREN**
- `api/garantie_pruefung.py` -> **INTEGRIEREN**
- `api/gudat_da_client.py` -> **INTEGRIEREN**
- `api/doc_to_pdf.py` -> **INTEGRIEREN**

Begruendung: Fachnahe Service-/Integrationsdateien; vor Abschluss kurze Querpruefung gegen bestehende SSOT-Module notwendig.

## 5) WhatsApp / Inbound (teilaktiv)

- `api/whatsapp_inbound.py` -> **BEHALTEN**

Begruendung: Wird aus `celery_app/tasks.py` und `routes/whatsapp_routes.py` verwendet.

## 6) Admin-/Konfig-UI (kandidaten fuer Integration)

- `templates/admin/konfiguration.html` -> **INTEGRIEREN**
- `templates/admin/konten_verwaltung.html` -> **INTEGRIEREN**
- `templates/admin/modalitaeten_verwaltung.html` -> **INTEGRIEREN**
- `routes/provision_routes.py` -> **INTEGRIEREN**
- `templates/ki_assistent.html` -> **INTEGRIEREN**

Begruendung: Fachlich passend zu laufenden Workstreams; vor finaler Entscheidung kurz auf Route-Registration und Navi-Verkabelung pruefen.

## 7) Weitere API-/Template-Kandidaten

- `api/cashflow_erwartung_ausgaben.py` -> **INTEGRIEREN**
- `api/cashflow_erwartung_locosoft.py` -> **INTEGRIEREN**
- `templates/verkauf_landau_90_tage_test.html` -> **BEHALTEN** (explizit als Test/Analyse-Template benannt, nicht loeschen)

Begruendung: Controlling/Verkauf-Kontext vorhanden; fuer produktive Aktivierung ggf. Route/Navi/Feature-Check.

## 8) Tests

- `tests/__init__.py` -> **BEHALTEN**

Begruendung: neutral, risikoarm, Teststruktur-Baustein.

## Kurzfazit

- **BEHALTEN:** 3
- **INTEGRIEREN:** 30
- **VERWERFEN:** 0 (kein sicherer Kandidat ohne Fachcheck)

## Naechster konkreter Schritt

1. Die 30 `INTEGRIEREN`-Dateien in 3 technische Pakete aufteilen: `hilfe`, `verkauf`, `fahrzeuganlage+rest`.
2. Pro Paket nur:
   - Registrierung/Verkabelung pruefen (Blueprint/Route/Navi/Feature),
   - minimale Smoke-Checks dokumentieren,
   - danach erst Commit-Vorschlag.

