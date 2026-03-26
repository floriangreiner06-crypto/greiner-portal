-- Seed: Kategorien und Starter-Artikel für das Hilfe-Modul
-- Erstellt: 2026-02-24 | Workstream: Hilfe
-- Idempotent: WHERE NOT EXISTS / ON CONFLICT DO NOTHING

-- =============================================================================
-- KATEGORIEN (falls noch nicht vorhanden)
-- =============================================================================

INSERT INTO hilfe_kategorien (name, slug, beschreibung, icon, sort_order, modul_route, aktiv)
SELECT 'Allgemein', 'allgemein', 'Erste Schritte und allgemeine Fragen zum Portal', 'bi-house-door', 0, '/dashboard', true
WHERE NOT EXISTS (SELECT 1 FROM hilfe_kategorien WHERE slug = 'allgemein');

INSERT INTO hilfe_kategorien (name, slug, beschreibung, icon, sort_order, modul_route, aktiv)
SELECT 'Urlaubsplaner', 'urlaubsplaner', 'Urlaub beantragen, Genehmigung, Resturlaub', 'bi-calendar-check', 1, '/urlaubsplaner', true
WHERE NOT EXISTS (SELECT 1 FROM hilfe_kategorien WHERE slug = 'urlaubsplaner');

INSERT INTO hilfe_kategorien (name, slug, beschreibung, icon, sort_order, modul_route, aktiv)
SELECT 'Controlling & Finanzen', 'controlling', 'BWA, TEK, Bankenspiegel, OPOS, AfA', 'bi-graph-up-arrow', 2, '/controlling', true
WHERE NOT EXISTS (SELECT 1 FROM hilfe_kategorien WHERE slug = 'controlling');

INSERT INTO hilfe_kategorien (name, slug, beschreibung, icon, sort_order, modul_route, aktiv)
SELECT 'Verkauf', 'verkauf', 'Auftragseingang, Auslieferung, Zielplanung, Provision', 'bi-cart', 3, '/verkauf', true
WHERE NOT EXISTS (SELECT 1 FROM hilfe_kategorien WHERE slug = 'verkauf');

INSERT INTO hilfe_kategorien (name, slug, beschreibung, icon, sort_order, modul_route, aktiv)
SELECT 'Werkstatt & Service', 'werkstatt-service', 'Stempeluhr, Aufträge, Fahrzeuganlage, Teile', 'bi-wrench', 4, '/werkstatt', true
WHERE NOT EXISTS (SELECT 1 FROM hilfe_kategorien WHERE slug = 'werkstatt-service');

INSERT INTO hilfe_kategorien (name, slug, beschreibung, icon, sort_order, modul_route, aktiv)
SELECT 'Admin & Organisation', 'admin', 'Mitarbeiterverwaltung, Organigramm, Rechte', 'bi-gear', 5, '/admin/mitarbeiterverwaltung', true
WHERE NOT EXISTS (SELECT 1 FROM hilfe_kategorien WHERE slug = 'admin');

-- =============================================================================
-- ARTIKEL: Allgemein
-- =============================================================================

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Wie logge ich mich im Portal ein?', 'login',
'## Kurz-Antwort
Sie melden sich mit Ihrem Windows-Benutzernamen und -Passwort an (wie am PC).

## Schritt für Schritt
1. Rufen Sie die Portal-Adresse auf (z. B. http://drive).
2. Geben Sie Ihren **Benutzernamen** ein (ohne @auto-greiner.de).
3. Geben Sie Ihr **Windows-Passwort** ein.
4. Klicken Sie auf **Anmelden**.

## Hinweise
- Bei Problemen: Passwort zurücksetzen oder IT/Admin ansprechen.
- Die Session bleibt mehrere Stunden aktiv.',
'markdown', 'login, anmeldung, passwort', 0
FROM hilfe_kategorien k WHERE k.slug = 'allgemein'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'login');

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Wie ist das Portal aufgebaut? (Navigation)', 'navigation',
'## Kurz-Antwort
Oben in der Leiste sehen Sie die Hauptbereiche: Service, Teile & Zubehör, Verkauf, Controlling, Team Greiner, Admin. Je nach Ihrer Rolle werden nur die Bereiche angezeigt, auf die Sie Zugriff haben.

## Schritt für Schritt
1. **Menüleiste:** Klicken Sie auf einen Bereich (z. B. Verkauf) – es öffnet sich ein Dropdown mit Unterpunkten.
2. **Startseite:** Nach dem Login werden Sie je nach Rolle zur passenden Übersicht weitergeleitet (z. B. Auftragseingang für Verkauf).
3. **Hilfe:** Ganz rechts im Menü finden Sie „Hilfe“ – dort können Sie nach Themen suchen.

## Hinweise
- Nicht alle Menüpunkte sind für alle Nutzer sichtbar; das hängt von Ihrer Rolle ab.',
'markdown', 'navigation, menü, bereiche', 1
FROM hilfe_kategorien k WHERE k.slug = 'allgemein'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'navigation');

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'An wen wende ich mich bei Problemen?', 'ansprechpartner',
'## Kurz-Antwort
Technische Probleme (Login, Zugriff, Fehlermeldungen): **IT / Systemadministration**.  
Fachliche Fragen zu einem Modul (z. B. Urlaub, Verkauf): **Ihr Vorgesetzter oder die zuständige Abteilung** (z. B. HR für Urlaub).

## Hinweise
- Bei Zugriffsverweigerung prüft die IT Ihre Berechtigungen (Rolle/AD-Gruppen).
- Für neue Berechtigungen ist in der Regel ein Antrag an die Geschäftsführung bzw. Admin nötig.',
'markdown', 'support, it, ansprechpartner', 2
FROM hilfe_kategorien k WHERE k.slug = 'allgemein'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'ansprechpartner');

-- =============================================================================
-- ARTIKEL: Urlaubsplaner
-- =============================================================================

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Wie beantrage ich Urlaub?', 'urlaub-beantragen',
'## Kurz-Antwort
Im Menü **Team Greiner → Urlaubsplaner** öffnen Sie den Kalender, wählen Ihre Urlaubstage und reichen den Antrag ein. Ihr Genehmiger erhält eine Benachrichtigung.

## Schritt für Schritt
1. **Urlaubsplaner** öffnen (Team Greiner → Urlaubsplaner).
2. Im Kalender die gewünschten **Tage anklicken** (grün = Urlaub).
3. Optional **Typ** wählen (Urlaub, Schulung, …).
4. Auf **Antrag stellen** klicken.
5. Der Genehmiger sieht den Antrag in seiner Übersicht und kann genehmigen oder ablehnen.

## Hinweise
- Resturlaub wird automatisch angezeigt; bei 0 Tagen Rest ist keine Buchung möglich.
- Vertretungsregeln: Wenn Sie jemanden vertreten, dürfen Sie in dessen Urlaubszeit keinen Urlaub buchen.',
'markdown', 'urlaub, beantragen, antrag', 0
FROM hilfe_kategorien k WHERE k.slug = 'urlaubsplaner'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'urlaub-beantragen');

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Wo sehe ich meinen Resturlaub?', 'resturlaub',
'## Kurz-Antwort
Im Urlaubsplaner steht neben Ihrem Namen in der Mitarbeiterliste Ihre **Resturlaub-Anzahl** (z. B. „27 Tage“). Oben links wird „Mein Rest“ angezeigt.

## Hinweise
- Die Anzeige berücksichtigt bereits genehmigte und gebuchte Urlaubstage sowie Abgleich mit Locosoft.
- Bei Abweichungen (z. B. Krankheit in Locosoft falsch gebucht) wenden Sie sich an HR/Buchhaltung.',
'markdown', 'resturlaub, guthaben, urlaub', 1
FROM hilfe_kategorien k WHERE k.slug = 'urlaubsplaner'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'resturlaub');

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Was bedeuten die Farben im Urlaubsplaner?', 'farben-urlaub',
'## Kurz-Antwort
- **Grün:** Urlaub (beantragt oder genehmigt)
- **Blau:** Schulung
- **Pink/Rosa:** Krankheit
- **Grau:** Urlaubssperre oder nicht buchbar
- **Blauer Punkt:** Tag ist in Locosoft erfasst (finale Buchung)

## Hinweise
- Genehmigte Tage erscheinen im Team-Kalender und (bei Konfiguration) im Outlook-Kalender.',
'markdown', 'urlaub, farben, kalender', 2
FROM hilfe_kategorien k WHERE k.slug = 'urlaubsplaner'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'farben-urlaub');

-- =============================================================================
-- ARTIKEL: Controlling
-- =============================================================================

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Was ist die TEK (Tägliche Erfolgskontrolle)?', 'tek',
'## Kurz-Antwort
Die TEK zeigt die **täglichen Kennzahlen** für Umsatz, Einsatz, DB1 (Deckungsbeitrag 1), Marge und eine Prognose (z. B. Breakeven). Sie ist unter Controlling → TEK zu finden.

## Wichtige Begriffe
- **Umsatz:** Tagesumsatz (z. B. Fahrzeugverkauf, Werkstatt).
- **Einsatz:** Kosten (u. a. 4-Lohn, rollierender Schnitt).
- **DB1:** Deckungsbeitrag 1 (Umsatz minus variable Kosten).
- **Breakeven:** Ab welchem Umsatz die Kosten gedeckt sind.',
'markdown', 'tek, erfolgskontrolle, kennzahlen', 0
FROM hilfe_kategorien k WHERE k.slug = 'controlling'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'tek');

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Wo finde ich den Bankenspiegel?', 'bankenspiegel',
'## Kurz-Antwort
Unter **Controlling → Bankenspiegel** sehen Sie Konten, Transaktionen und Zeitverläufe. Der Zugriff ist für Buchhaltung und berechtigte Rollen freigegeben.

## Schritt für Schritt
1. Menü **Controlling** öffnen.
2. **Bankenspiegel** (oder Bankenspiegel/Konten) wählen.
3. Konto auswählen oder Zeitraum anpassen.',
'markdown', 'bankenspiegel, konten, controlling', 1
FROM hilfe_kategorien k WHERE k.slug = 'controlling'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'bankenspiegel');

-- =============================================================================
-- ARTIKEL: Verkauf
-- =============================================================================

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Wo finde ich den Auftragseingang?', 'auftragseingang',
'## Kurz-Antwort
**Verkauf → Auftragseingang.** Dort sehen Sie eingehende Aufträge, aufgeschlüsselt nach Verkäufer und Modell. Sie können nach Standort filtern.

## Hinweise
- Die Daten stammen aus Locosoft bzw. der Verkaufsabwicklung.
- Für Auslieferungen und Detailansichten nutzen Sie die verlinkten Unterpunkte im Verkauf-Menü.',
'markdown', 'auftragseingang, verkauf, umsatz', 0
FROM hilfe_kategorien k WHERE k.slug = 'verkauf'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'auftragseingang');

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Was ist die Verkäufer-Zielplanung?', 'zielplanung',
'## Kurz-Antwort
Die **Verkäufer-Zielplanung** dient der Planung von Stückzahlen und Zielen pro Verkäufer (Kalenderjahr, ggf. NW/GW). Sie ist über das Verkauf-Menü oder einen eigenen Navi-Punkt erreichbar.

## Hinweise
- Ziele und Freigaben werden dort gepflegt und mit der Provisionslogik verknüpft.',
'markdown', 'zielplanung, verkauf, ziele', 1
FROM hilfe_kategorien k WHERE k.slug = 'verkauf'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'zielplanung');

-- =============================================================================
-- ARTIKEL: Werkstatt & Service
-- =============================================================================

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Wo sehe ich die Stempeluhr / Anwesenheit?', 'stempeluhr',
'## Kurz-Antwort
Unter **Service → Werkstatt** (bzw. Aftersales) finden Sie **Stempeluhr**, **Stempeluhr-Monitor** und **Anwesenheit**. Je nach Rolle sehen Sie Ihren Bereich oder die Gesamtübersicht.

## Hinweise
- Daten kommen aus der Zeiterfassung (Gudat/Locosoft). Bei Abweichungen die zuständige Stelle ansprechen.',
'markdown', 'stempeluhr, anwesenheit, werkstatt', 0
FROM hilfe_kategorien k WHERE k.slug = 'werkstatt-service'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'stempeluhr');

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Was ist die Fahrzeuganlage?', 'fahrzeuganlage',
'## Kurz-Antwort
Die **Fahrzeuganlage** unterstützt die Erfassung von Fahrzeugen (z. B. über Fahrzeugschein-OCR). Sie ist unter Service/Werkstatt zu finden und für berechtigte Rollen (Werkstatt, Service, Disposition) sichtbar.

## Hinweise
- Bei technischen Fragen (OCR, Anbindung) wenden Sie sich an die IT.',
'markdown', 'fahrzeuganlage, werkstatt, ocr', 1
FROM hilfe_kategorien k WHERE k.slug = 'werkstatt-service'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'fahrzeuganlage');

-- =============================================================================
-- ARTIKEL: Admin & Organisation
-- =============================================================================

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Was ist die Mitarbeiterverwaltung?', 'mitarbeiterverwaltung',
'## Kurz-Antwort
Unter **Admin → Mitarbeiterverwaltung** pflegen HR/Buchhaltung die **digitalen Personalakten**: Stammdaten, Vertrag, Arbeitszeitmodell, Urlaubseinstellungen. Die Daten werden u. a. vom Urlaubsplaner genutzt.

## Hinweise
- Zugriff nur für Admin und berechtigte Rollen. Änderungen an Urlaubsansprüchen wirken sich im Urlaubsplaner aus.',
'markdown', 'mitarbeiterverwaltung, admin, personal', 0
FROM hilfe_kategorien k WHERE k.slug = 'admin'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'mitarbeiterverwaltung');

INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order)
SELECT k.id, 'Was ist das Organigramm?', 'organigramm',
'## Kurz-Antwort
Das **Organigramm** (Admin → Organigramm) zeigt die Struktur mit **Vertretungsregeln** und **Abwesenheitsgrenzen**. Genehmiger und Vertreter werden dort zugeordnet; die Regeln gelten z. B. im Urlaubsplaner („Vertreter darf in der Urlaubszeit der vertretenen Person keinen Urlaub buchen“).

## Hinweise
- Pflege durch Admin/Buchhaltung. Änderungen wirken sofort auf Genehmigungen und Vertretungsprüfungen.',
'markdown', 'organigramm, vertretung, admin', 1
FROM hilfe_kategorien k WHERE k.slug = 'admin'
AND NOT EXISTS (SELECT 1 FROM hilfe_artikel a WHERE a.kategorie_id = k.id AND a.slug = 'organigramm');
