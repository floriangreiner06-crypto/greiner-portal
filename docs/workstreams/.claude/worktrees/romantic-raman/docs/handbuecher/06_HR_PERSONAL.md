# DRIVE Handbuch - HR & Personal

**Zielgruppe:** HR/Personalabteilung, Abteilungsleiter (Genehmiger), alle Mitarbeiter
**Rollen im System:** admin, hr, abteilungsleiter, mitarbeiter
**Stand:** Dezember 2025

---

## Module im Überblick

| Modul | URL | Zielgruppe | Funktion |
|-------|-----|------------|----------|
| Urlaubsplaner | /urlaubsplaner/v2 | Alle | Urlaub beantragen/einsehen |
| Chef-Ansicht | /urlaubsplaner/chef | Abteilungsleiter | Genehmigungen |
| Admin-Panel | /urlaubsplaner/admin | HR/Admin | Kontingente, Regeln |
| Anwesenheit | /werkstatt/anwesenheit | Werkstatt-Leitung | Stempelzeiten-Report |

---

## 1. Urlaubsplaner (für alle Mitarbeiter)

**URL:** https://drive.auto-greiner.de/urlaubsplaner/v2

### Übersicht
Nach dem Login sehen Sie:
- **Ihr Urlaubskonto:** Anspruch, genommen, Rest
- **Ihre Buchungen:** Alle beantragten Tage
- **Team-Kalender:** Wer ist wann abwesend?

### Urlaub beantragen

#### Schritt für Schritt
1. **Kalender öffnen:** Auf den Kalender klicken
2. **Tage auswählen:** Ersten und letzten Tag anklicken
3. **Art wählen:** Urlaub, Gleittag, Sonderurlaub
4. **Absenden:** Button "Urlaub beantragen"

#### Buchungsarten
| Art | Beschreibung | Genehmigung |
|-----|--------------|-------------|
| Urlaub | Regulärer Erholungsurlaub | Ja |
| Gleittag | Zeitausgleich | Ja |
| Sonderurlaub | Hochzeit, Geburt, Todesfall | Ja + HR |
| Krankheit | Krankmeldung | Nur HR/Admin |

### Status-Anzeige
| Status | Bedeutung | Farbe |
|--------|-----------|-------|
| Beantragt | Wartet auf Genehmigung | Gelb |
| Genehmigt | Urlaub bestätigt | Grün |
| Abgelehnt | Nicht genehmigt | Rot |
| Storniert | Zurückgezogen | Grau |

### Urlaub stornieren
1. Buchung in der Liste finden
2. "Stornieren" klicken
3. Grund eingeben (optional)
4. Bestätigen

**Hinweis:** Bereits genehmigte Buchungen können nicht mehr selbst storniert werden. Bitte HR kontaktieren.

### Team-Kalender
- Zeigt alle Teammitglieder
- Farbcodiert nach Abwesenheitsart
- Hilft bei der Planung (Vertretungen)

---

## 2. Chef-Ansicht (Abteilungsleiter/Genehmiger)

**URL:** https://drive.auto-greiner.de/urlaubsplaner/chef

### Zugang
Nur für Mitarbeiter mit Genehmiger-Rolle (in LDAP hinterlegt).

### Offene Anträge
Dashboard zeigt:
- Anzahl offener Anträge
- Nach Priorität sortiert (Datum, Dauer)
- Klick öffnet Details

### Genehmigen/Ablehnen

#### Genehmigen
1. Antrag auswählen
2. "Genehmigen" klicken
3. Optional: Bemerkung hinzufügen
4. **Automatisch:** E-Mail an Mitarbeiter + HR + Kalendereintrag

#### Ablehnen
1. Antrag auswählen
2. "Ablehnen" klicken
3. **Pflicht:** Begründung eingeben
4. **Automatisch:** E-Mail an Mitarbeiter

### Team-Übersicht
- Alle Mitarbeiter Ihrer Abteilung
- Aktueller Urlaubsstand pro Person
- Geplante Abwesenheiten

### Vertretungsregeln
Wenn Sie selbst abwesend sind:
- Stellvertreter wird automatisch benachrichtigt
- Stellvertreter kann genehmigen
- Einrichtung durch HR/Admin

---

## 3. Admin-Panel (HR/Personalabteilung)

**URL:** https://drive.auto-greiner.de/urlaubsplaner/admin

### Urlaubskontingente verwalten

#### Mitarbeiter bearbeiten
1. Mitarbeiter in Liste suchen
2. Auf Name klicken
3. Kontingent anpassen:
   - Jahresanspruch
   - Resturlaub Vorjahr
   - Sonderurlaub-Kontingent
4. Speichern

#### Massen-Import
Für Jahreswechsel:
1. Excel-Vorlage herunterladen
2. Neue Kontingente eintragen
3. Hochladen

### Genehmiger-Regeln

#### Regel anlegen
1. "Neue Regel" klicken
2. Mitarbeiter auswählen (wer wird genehmigt?)
3. Genehmiger auswählen (wer genehmigt?)
4. Reihenfolge festlegen (1 = Erst-Genehmiger)
5. Speichern

#### Stellvertreter-Regeln
Für Abwesenheit des Genehmigers:
1. "Vertretungsregel" anlegen
2. Originaler Genehmiger auswählen
3. Stellvertreter auswählen
4. Zeitraum festlegen (optional)

### Abwesenheitsarten verwalten
- Neue Arten anlegen
- Farben zuweisen
- Genehmigungspflicht definieren
- Kontingent-Abzug (ja/nein)

### Krankheitsbuchungen
Nur HR/Admin kann Krankheit eintragen:
1. Mitarbeiter auswählen
2. "Krankheit buchen"
3. Zeitraum eingeben
4. Speichern (keine Genehmigung nötig)

### Reports

#### Urlaubsübersicht
- Export aller Mitarbeiter mit Kontingenten
- Genommen/Geplant/Rest
- Filter nach Abteilung

#### Abwesenheitskalender
- Monats-/Jahresübersicht
- Export als PDF/Excel
- Für Aushang/Dokumentation

---

## 4. Anwesenheits-Report (Werkstatt)

**URL:** https://drive.auto-greiner.de/werkstatt/anwesenheit

### Funktion
Zeigt Stempelzeiten der Werkstattmitarbeiter basierend auf Locosoft-Daten.

### Ansichten
- **Tagesansicht:** Alle Stempelungen heute
- **Wochenansicht:** Wochenzusammenfassung
- **Monatsansicht:** Monatlicher Übersicht

### Spalten
| Spalte | Beschreibung |
|--------|--------------|
| Mitarbeiter | Name |
| Datum | Arbeitstag |
| Kommen | Erste Stempelung |
| Gehen | Letzte Stempelung |
| Pause | Abgezogene Pausenzeit |
| Anwesend | Netto-Arbeitszeit |
| Soll | Vertragsarbeitszeit |
| Differenz | Über-/Unterzeit |

### Export
CSV-Export für Lohnbuchhaltung.

---

## Arbeitsabläufe

### Urlaubsplanung (Mitarbeiter)
1. **Januar:** Jahresplanung - Haupturlaub eintragen
2. **Laufend:** Einzelne Tage bei Bedarf
3. **Vor Urlaub:** Status prüfen (genehmigt?)
4. **Nach Urlaub:** Kontingent prüfen

### Genehmigungsworkflow (Abteilungsleiter)
1. **Täglich:** E-Mail-Benachrichtigung prüfen
2. **Im Portal:** Offene Anträge bearbeiten
3. **Bei Konflikt:** Mit Mitarbeiter sprechen
4. **Dokumentation:** System protokolliert alles

### Jahreswechsel (HR)
1. **November:** Resturlaub-Übersicht erstellen
2. **Dezember:** Mitarbeiter informieren (Verfall?)
3. **Januar:** Neue Kontingente importieren
4. **Januar:** Übertrag Resturlaub buchen

---

## E-Mail-Benachrichtigungen

### Automatische E-Mails
| Ereignis | Empfänger | Inhalt |
|----------|-----------|--------|
| Antrag gestellt | Genehmiger | Link zum Antrag |
| Antrag genehmigt | Mitarbeiter + HR | Bestätigung + Details |
| Antrag abgelehnt | Mitarbeiter | Begründung |
| Storno durch MA | Genehmiger | Info |
| Storno durch Admin | Mitarbeiter | Info + Grund |

### Kalender-Integration
Bei Genehmigung wird automatisch:
- Outlook-Termin erstellt
- Team-Kalender aktualisiert
- Locosoft-Eintrag angelegt

---

## Berechtigungen

### Rollen-Übersicht
| Rolle | Sehen | Buchen | Genehmigen | Verwalten |
|-------|-------|--------|------------|-----------|
| Mitarbeiter | Eigene + Team | Eigene | - | - |
| Genehmiger | Team | Eigene | Team | - |
| HR | Alle | Alle | Alle | Kontingente |
| Admin | Alle | Alle | Alle | Alles |

### LDAP-Gruppen
Die Berechtigung wird automatisch aus dem Active Directory übernommen:
- **GRP_Urlaub_Admin:** HR/Admin-Zugriff
- **GRP_Urlaub_Genehmiger:** Chef-Ansicht
- **Alle anderen:** Mitarbeiter-Ansicht

---

## Häufige Fragen

**Q: Mein Resturlaub ist falsch?**
A: HR kontaktieren. Kontingente werden aus Locosoft synchronisiert.

**Q: Wer ist mein Genehmiger?**
A: Im Urlaubsplaner unter "Meine Genehmiger" sichtbar. Bei Unklarheit: HR fragen.

**Q: Kann ich halbe Tage buchen?**
A: Ja, bei der Buchung "halber Tag" auswählen.

**Q: Genehmiger ist selbst im Urlaub?**
A: Stellvertreter wird automatisch benachrichtigt (falls eingerichtet).

**Q: Wie lange muss ich auf Genehmigung warten?**
A: Genehmiger erhalten sofort E-Mail. Bei Dringlichkeit direkt ansprechen.

**Q: Urlaub wird nicht im Outlook-Kalender angezeigt?**
A: Nur genehmigte Buchungen erscheinen im Kalender. Status prüfen!

---

## Kontakt

| Thema | Ansprechpartner |
|-------|-----------------|
| Kontingent-Fragen | HR-Abteilung |
| Technische Probleme | IT-Abteilung |
| Genehmiger-Änderung | HR-Abteilung |
| Locosoft-Abgleich | HR + IT |

---

*Letzte Aktualisierung: TAG 143 - Dezember 2025*
