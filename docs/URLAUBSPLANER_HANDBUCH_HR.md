# 📋 GREINER PORTAL DRIVE - Urlaubsplaner Handbuch

## Für HR & Führungskräfte

**Version:** 1.0  
**Datum:** 09.12.2025  
**Autor:** IT Autohaus Greiner

---

# 📖 Inhaltsverzeichnis

1. [Was ist DRIVE?](#1-was-ist-drive)
2. [Anmeldung](#2-anmeldung)
3. [Rollen im Urlaubsplaner](#3-rollen-im-urlaubsplaner)
4. [Workflows für Mitarbeiter](#4-workflows-für-mitarbeiter)
5. [Workflows für Vorgesetzte](#5-workflows-für-vorgesetzte)
6. [Workflows für HR/Admin](#6-workflows-für-hradmin)
7. [Active Directory Pflege](#7-active-directory-pflege)
8. [Testanleitung](#8-testanleitung)
9. [Häufige Fragen (FAQ)](#9-häufige-fragen-faq)
10. [Hilfe & Support](#10-hilfe--support)

---

# 1. Was ist DRIVE?

**DRIVE** (Digital Resources & Information for Vehicle Enterprises) ist das interne Portal des Autohaus Greiner. Es bietet verschiedene Module:

- 🏖️ **Urlaubsplaner** - Urlaub beantragen und genehmigen
- 📊 **Bankenspiegel** - Finanz-Controlling (nur für Buchhaltung)
- 🚗 **Verkauf** - Auftragseingang & Auslieferungen

**Zugang:** https://drive.auto-greiner.de (nur im Firmennetzwerk oder VPN)

---

# 2. Anmeldung

## 2.1 Login

1. Öffnen Sie **https://drive.auto-greiner.de** im Browser
2. Geben Sie Ihre **Windows-Anmeldedaten** ein:
   - **Benutzername:** Ihr Windows-Benutzername (z.B. `max.mustermann`)
   - **Passwort:** Ihr Windows-Passwort
3. Klicken Sie auf **"Anmelden"**

> ⚠️ **Wichtig:** Es sind dieselben Zugangsdaten wie für Ihren Windows-PC!

## 2.2 Erster Login

Beim ersten Login werden Ihre Daten automatisch mit Locosoft verknüpft. Dies kann einige Sekunden dauern.

Falls Probleme auftreten, wenden Sie sich an die IT.

---

# 3. Rollen im Urlaubsplaner

Je nach Ihrer Position haben Sie unterschiedliche Rechte:

| Rolle | Beschreibung | Rechte |
|-------|--------------|--------|
| **Mitarbeiter** | Jeder Angestellte | Eigenen Urlaub beantragen & einsehen |
| **Vorgesetzter** | Abteilungsleiter, Teamleiter | Team-Urlaub einsehen & genehmigen |
| **HR/Admin** | Sandra Brendel, Florian Greiner | Alle Mitarbeiter verwalten, Urlaubskontingente pflegen |

## 3.1 Woher kommen die Rollen?

Die Rollen werden aus dem **Active Directory (AD)** gelesen:

- **Vorgesetzter:** Wer im AD als `manager` eines Mitarbeiters eingetragen ist
- **Genehmiger:** Wer in einer `GRP_Urlaub_Genehmiger_*` Gruppe ist
- **Admin:** Wer in der Gruppe `GRP_Urlaub_Admin` ist

> 💡 Die Pflege erfolgt in der **Active Directory Benutzer und Computer** Konsole (siehe Kapitel 7).

---

# 4. Workflows für Mitarbeiter

## 4.1 Urlaub beantragen

**Schritt-für-Schritt:**

1. Melden Sie sich bei DRIVE an
2. Klicken Sie im Menü auf **"Urlaubsplaner"**
3. Sie sehen Ihr **Urlaubskonto**:
   - Jahresanspruch
   - Bereits genommen
   - Noch verfügbar
4. Klicken Sie auf **"Neuer Antrag"** (oder das + Symbol)
5. Füllen Sie das Formular aus:
   - **Von:** Erster Urlaubstag
   - **Bis:** Letzter Urlaubstag
   - **Art:** Urlaub, Zeitausgleich, Sonderurlaub, etc.
   - **Bemerkung:** (optional) z.B. "Familienfeier"
6. Klicken Sie auf **"Absenden"**

**Was passiert dann?**
- Ihr Vorgesetzter erhält automatisch eine **E-Mail-Benachrichtigung**
- Der Antrag erscheint in Ihrer Liste als **"Ausstehend"** (gelb)
- Nach Genehmigung ändert sich der Status auf **"Genehmigt"** (grün)

## 4.2 Antrag stornieren

Solange ein Antrag noch **nicht genehmigt** wurde:

1. Gehen Sie zu **"Meine Anträge"**
2. Klicken Sie auf den Antrag
3. Klicken Sie auf **"Stornieren"**
4. Bestätigen Sie die Stornierung

> ⚠️ Bereits genehmigte Anträge können nur vom Vorgesetzten oder HR storniert werden!

## 4.3 Urlaubsübersicht einsehen

1. Klicken Sie auf **"Kalender"** im Urlaubsplaner
2. Sie sehen:
   - Ihre eigenen Urlaubstage (farbig markiert)
   - Feiertage (grau)
   - Optional: Urlaub Ihrer Kollegen (wenn freigegeben)

---

# 5. Workflows für Vorgesetzte

## 5.1 Team-Übersicht

Als Vorgesetzter sehen Sie automatisch **alle Mitarbeiter, die Ihnen im AD zugeordnet sind**.

1. Melden Sie sich bei DRIVE an
2. Gehen Sie zum **Urlaubsplaner**
3. Sie sehen oben einen Tab **"Mein Team"**
4. Hier sehen Sie:
   - Alle Ihre Teammitglieder
   - Deren Urlaubskontingente
   - Anstehende Urlaube

> 💡 Wer in Ihrem Team erscheint, hängt davon ab, bei welchen Mitarbeitern SIE als `manager` im AD eingetragen sind!

## 5.2 Urlaubsantrag genehmigen

**Bei Eingang eines Antrags:**
- Sie erhalten eine **E-Mail** mit den Details
- Im Betreff steht: "Urlaubsantrag von [Name]"

**Genehmigung in DRIVE:**

1. Klicken Sie auf den Link in der E-Mail **ODER**
2. Gehen Sie zu DRIVE → Urlaubsplaner → **"Offene Anträge"**
3. Sie sehen alle ausstehenden Anträge Ihres Teams
4. Klicken Sie auf einen Antrag
5. Prüfen Sie:
   - Zeitraum
   - Verbleibendes Kontingent des Mitarbeiters
   - Überschneidungen mit anderen Teammitgliedern
6. Klicken Sie auf:
   - ✅ **"Genehmigen"** - Der Mitarbeiter wird benachrichtigt
   - ❌ **"Ablehnen"** - Geben Sie einen Grund an

## 5.3 Antrag ablehnen

1. Klicken Sie auf den Antrag
2. Klicken Sie auf **"Ablehnen"**
3. Geben Sie einen **Grund** ein (Pflichtfeld), z.B.:
   - "Zu viele Kollegen gleichzeitig im Urlaub"
   - "Wichtiger Termin in diesem Zeitraum"
4. Klicken Sie auf **"Absenden"**

Der Mitarbeiter erhält eine E-Mail mit dem Ablehnungsgrund.

## 5.4 Team-Kalender

1. Gehen Sie zu **"Team-Kalender"**
2. Sie sehen alle Urlaube Ihres Teams auf einen Blick
3. Rot markiert = Überschneidungen / potenzielle Konflikte

---

# 6. Workflows für HR/Admin

## 6.1 Übersicht

Als Admin (Gruppe `GRP_Urlaub_Admin`) haben Sie Zugriff auf:
- **Alle** Mitarbeiter (standortübergreifend)
- Urlaubskontingente verwalten
- Anträge für andere stellen/stornieren
- Auswertungen & Berichte

## 6.2 Urlaubskontingent anpassen

**Wann nötig?**
- Neuer Mitarbeiter (anteiliger Anspruch)
- Beförderung (mehr Urlaubstage)
- Korrektur von Fehlern

**Vorgehen:**

1. Gehen Sie zu **Urlaubsplaner → Verwaltung → Kontingente**
2. Suchen Sie den Mitarbeiter
3. Klicken Sie auf **"Bearbeiten"**
4. Passen Sie an:
   - **Jahresanspruch:** Anzahl Tage
   - **Resturlaub Vorjahr:** Übertragene Tage
   - **Sonderurlaub:** Falls gewährt
5. Klicken Sie auf **"Speichern"**
6. **Grund angeben** (wird protokolliert)

## 6.3 Urlaub für Mitarbeiter eintragen

**Wann nötig?**
- Nachträgliche Erfassung
- Mitarbeiter hat keinen PC-Zugang

**Vorgehen:**

1. Gehen Sie zu **Urlaubsplaner → Verwaltung → Neuer Eintrag**
2. Wählen Sie den **Mitarbeiter** aus
3. Füllen Sie das Formular aus (wie bei normalem Antrag)
4. Wählen Sie Status:
   - **Genehmigt** - Direkt eintragen ohne Workflow
   - **Ausstehend** - Normaler Genehmigungsprozess
5. Klicken Sie auf **"Speichern"**

## 6.4 Krankmeldung erfassen

> 📝 Krankmeldungen werden primär in **Locosoft** erfasst und nachts synchronisiert.

Falls eine manuelle Erfassung in DRIVE nötig ist:

1. **Urlaubsplaner → Verwaltung → Neuer Eintrag**
2. Mitarbeiter wählen
3. Art: **"Krank"** oder **"Krank mit AU"**
4. Zeitraum eingeben
5. Status auf **"Genehmigt"** setzen
6. Speichern

## 6.5 Auswertungen erstellen

1. Gehen Sie zu **Urlaubsplaner → Berichte**
2. Wählen Sie den Berichtstyp:
   - **Jahresübersicht** - Alle Urlaube eines Jahres
   - **Abteilungsbericht** - Urlaube pro Abteilung
   - **Resturlaub** - Wer hat noch wie viel?
3. Wählen Sie Filter (Jahr, Abteilung, Standort)
4. Klicken Sie auf **"Erstellen"**
5. Export möglich als **Excel** oder **PDF**

## 6.6 Protokoll / Audit-Log

Alle Änderungen werden protokolliert:

1. Gehen Sie zu **Urlaubsplaner → Verwaltung → Protokoll**
2. Sie sehen:
   - Wer hat wann was geändert
   - Alte und neue Werte
   - IP-Adresse und Zeitstempel

---

# 7. Active Directory Pflege

## 7.1 Warum ist das wichtig?

DRIVE liest folgende Informationen aus dem Active Directory:
- **manager** → Wer ist der Vorgesetzte?
- **department** → Welche Abteilung?
- **company** → Welcher Standort?

**Wenn diese Felder nicht gepflegt sind:**
- ❌ Mitarbeiter erscheinen nicht im Team des Vorgesetzten
- ❌ Genehmigungen gehen an die falsche Person
- ❌ Auswertungen nach Abteilung funktionieren nicht

## 7.2 AD-Attribute pflegen

**Benötigte Berechtigung:** Domain Admin oder delegierte OU-Verwaltung

**Vorgehen:**

1. Öffnen Sie **Active Directory Benutzer und Computer** (dsa.msc)
2. Navigieren Sie zu: `AUTO-GREINER → Abteilungen → [Abteilung]`
3. Doppelklicken Sie auf den Benutzer
4. Reiter **"Organisation"**:

| Feld | Bedeutung | Beispiel |
|------|-----------|----------|
| **Vorgesetzter** | Direkter Manager | König, Matthias |
| **Abteilung** | Abteilungsname | Werkstatt |
| **Firma** | Standort | Autohaus Greiner - Deggendorf |

5. Klicken Sie auf **"OK"**

> ⚠️ **Wichtig bei Firma/Standort:**
> - `Autohaus Greiner - Deggendorf` → Standort Deggendorf
> - `Autohaus Greiner - Landau` → Standort Landau
> 
> Die Schreibweise muss exakt stimmen!

## 7.3 Genehmiger-Gruppen

Damit jemand Urlaub genehmigen kann, muss er in einer Genehmiger-Gruppe sein:

| AD-Gruppe | Beschreibung |
|-----------|--------------|
| `GRP_Urlaub_Admin` | Vollzugriff (HR, Geschäftsleitung) |
| `GRP_Urlaub_Genehmiger_GL` | Geschäftsleitung |
| `GRP_Urlaub_Genehmiger_Verkauf` | Verkaufsleitung |
| `GRP_Urlaub_Genehmiger_Service_DEG` | Serviceleitung Deggendorf |
| `GRP_Urlaub_Genehmiger_Werkstatt_DEG` | Werkstattleitung Deggendorf |
| `GRP_Urlaub_Genehmiger_Werkstatt_LAU` | Werkstattleitung Landau |
| `GRP_Urlaub_Genehmiger_Teile` | Teileleitung |
| `GRP_Urlaub_Genehmiger_Buchhaltung` | Buchhaltungsleitung |

**Gruppe zuweisen:**

1. AD Benutzer und Computer öffnen
2. Benutzer suchen
3. Rechtsklick → **"Zu einer Gruppe hinzufügen"**
4. Gruppenname eingeben (z.B. `GRP_Urlaub_Genehmiger_Werkstatt_DEG`)
5. OK

> 💡 Die Änderung wird bei der nächsten Anmeldung des Benutzers wirksam!

## 7.4 Prüfbericht

Jeden Montag um 7:00 Uhr erhalten Sie automatisch einen **LDAP-Locosoft Matching Report** per E-Mail.

Dieser zeigt:
- ❌ Mitarbeiter ohne LDAP-Mapping (können sich nicht einloggen)
- ⚠️ Fehlende Vorgesetzte im AD
- ⚠️ Fehlende Abteilung im AD
- ⚠️ Fehlender Standort (company) im AD
- 🔴 Standort-Unterschiede zwischen AD und Locosoft

**Bitte diese Probleme zeitnah im AD korrigieren!**

---

# 8. Testanleitung

## 8.1 Test als Mitarbeiter

**Testszenario:** Urlaubsantrag stellen

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| 1 | Login als normaler Mitarbeiter | Dashboard erscheint |
| 2 | Urlaubsplaner öffnen | Eigenes Kontingent wird angezeigt |
| 3 | "Neuer Antrag" klicken | Formular öffnet sich |
| 4 | Datum auswählen (z.B. nächste Woche Mo-Fr) | Tage werden berechnet |
| 5 | Art: "Urlaub" wählen | - |
| 6 | Absenden | Erfolgsmeldung, Status "Ausstehend" |
| 7 | Prüfen: Vorgesetzter hat E-Mail erhalten | E-Mail mit Antrag-Details |

## 8.2 Test als Vorgesetzter

**Voraussetzung:** Sie sind im AD als `manager` von mindestens einem Mitarbeiter eingetragen UND in einer `GRP_Urlaub_Genehmiger_*` Gruppe.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| 1 | Login als Vorgesetzter | Dashboard mit "Offene Anträge" Badge |
| 2 | Urlaubsplaner öffnen | Tab "Mein Team" sichtbar |
| 3 | "Mein Team" klicken | Liste aller Untergebenen |
| 4 | "Offene Anträge" klicken | Antrag aus Test 8.1 sichtbar |
| 5 | Antrag anklicken | Details werden angezeigt |
| 6 | "Genehmigen" klicken | Erfolgsmeldung |
| 7 | Prüfen: Mitarbeiter hat E-Mail erhalten | E-Mail "Ihr Urlaub wurde genehmigt" |

## 8.3 Test als Admin

**Voraussetzung:** Sie sind in der Gruppe `GRP_Urlaub_Admin`.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| 1 | Login als Admin | Dashboard erscheint |
| 2 | Urlaubsplaner öffnen | "Mein Team" zeigt ALLE Mitarbeiter |
| 3 | Team-Größe prüfen | ca. 60+ Mitarbeiter |
| 4 | "Verwaltung" Menü sichtbar | Ja |
| 5 | Kontingent eines MA öffnen | Bearbeiten möglich |
| 6 | Änderung speichern | Erfolgsmeldung |
| 7 | Protokoll prüfen | Änderung ist geloggt |

## 8.4 Test der AD-Integration

**Ziel:** Prüfen ob Manager-Zuordnung funktioniert

```
Testfall: Christian Raith (Werkstatt DEG)
- Im AD: manager = Matthias König
- Erwartung: Christian erscheint im Team von Matthias König
```

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| 1 | Login als `matthias.koenig` | - |
| 2 | Urlaubsplaner → Mein Team | Christian Raith in der Liste |
| 3 | Login als `christian.raith` | - |
| 4 | Urlaubsantrag stellen | - |
| 5 | Prüfen: matthias.koenig erhält E-Mail | ✅ |

## 8.5 Fehlersuche

**Problem: Mitarbeiter erscheint nicht im Team**

1. AD prüfen: Hat der Mitarbeiter einen `manager` eingetragen?
2. AD prüfen: Ist der Manager korrekt geschrieben?
3. Hat sich der Mitarbeiter schon mal bei DRIVE angemeldet?
4. Hat sich der Manager schon mal bei DRIVE angemeldet?

**Problem: Vorgesetzter kann nicht genehmigen**

1. AD prüfen: Ist der Vorgesetzte in einer `GRP_Urlaub_Genehmiger_*` Gruppe?
2. Hat sich der Vorgesetzte seit Gruppenänderung neu angemeldet?

**Problem: Falscher Genehmiger wird benachrichtigt**

1. AD prüfen: Wer ist als `manager` eingetragen?
2. Matching-Report prüfen (E-Mail vom Montag)

---

# 9. Häufige Fragen (FAQ)

## Allgemein

**F: Kann ich DRIVE von zuhause nutzen?**
A: Ja, über VPN. Verbinden Sie sich erst mit dem VPN, dann öffnen Sie DRIVE.

**F: Mein Passwort funktioniert nicht.**
A: Es ist dasselbe Passwort wie für Windows. Falls Sie es geändert haben, nutzen Sie das neue. Bei Problemen: IT kontaktieren.

**F: Ich sehe den Urlaubsplaner nicht.**
A: Melden Sie sich einmal ab und wieder an. Falls es dann noch nicht geht: IT kontaktieren.

## Für Mitarbeiter

**F: Wie viel Urlaub habe ich noch?**
A: Urlaubsplaner öffnen → oben wird Ihr Kontingent angezeigt.

**F: Kann ich halbe Tage Urlaub nehmen?**
A: Das hängt von der Unternehmensregelung ab. Fragen Sie Ihren Vorgesetzten oder HR.

**F: Mein Antrag wurde abgelehnt - was nun?**
A: In der Ablehnungs-E-Mail steht der Grund. Sprechen Sie mit Ihrem Vorgesetzten und stellen Sie ggf. einen neuen Antrag für einen anderen Zeitraum.

## Für Vorgesetzte

**F: Ich sehe mein Team nicht.**
A: Prüfen Sie mit HR/IT, ob Sie im AD korrekt als Vorgesetzter eingetragen sind.

**F: Ich kann Anträge nicht genehmigen.**
A: Sie müssen in einer `GRP_Urlaub_Genehmiger_*` Gruppe sein. Kontaktieren Sie IT.

**F: Ein Mitarbeiter erscheint nicht in meinem Team.**
A: Der Mitarbeiter muss sich einmal bei DRIVE anmelden. Zusätzlich muss er/sie im AD Ihnen als Vorgesetzter zugeordnet sein.

## Für HR/Admin

**F: Wie übertrage ich Resturlaub ins neue Jahr?**
A: Verwaltung → Kontingente → Mitarbeiter bearbeiten → "Resturlaub Vorjahr" anpassen.

**F: Ein neuer Mitarbeiter kann sich nicht anmelden.**
A: 1) Ist er im AD angelegt? 2) Ist er in Locosoft angelegt? 3) Sind AD und Locosoft korrekt verknüpft (Matching-Report)?

---

# 10. Hilfe & Support

## Ansprechpartner

| Thema | Ansprechpartner | Kontakt |
|-------|-----------------|---------|
| DRIVE allgemein | IT | it@auto-greiner.de |
| Urlaubskontingente | Sandra Brendel | sandra.brendel@auto-greiner.de |
| AD-Pflege | IT | it@auto-greiner.de |
| Locosoft-Daten | Buchhaltung | buchhaltung@auto-greiner.de |

## Probleme melden

Bei technischen Problemen:

1. **Screenshot** des Fehlers machen
2. Beschreiben: **Was wollten Sie tun? Was ist passiert?**
3. E-Mail an **it@auto-greiner.de** mit:
   - Ihrem Benutzernamen
   - Zeitpunkt des Fehlers
   - Screenshot
   - Fehlerbeschreibung

---

# 📎 Anhang

## A. Übersicht der Abwesenheitsarten

| Art | Kürzel | Wird vom Kontingent abgezogen? |
|-----|--------|-------------------------------|
| Urlaub | URL | ✅ Ja |
| Zeitausgleich | ZA | ❌ Nein (separates Konto) |
| Krank ohne AU | KoA | ❌ Nein |
| Krank mit AU | KmA | ❌ Nein |
| Sonderurlaub | SU | ❌ Nein |
| Unbezahlter Urlaub | UU | ❌ Nein |
| Fortbildung | FB | ❌ Nein |
| Mutterschutz | MU | ❌ Nein |
| Elternzeit | EZ | ❌ Nein |

## B. Status-Übersicht

| Status | Farbe | Bedeutung |
|--------|-------|-----------|
| Ausstehend | 🟡 Gelb | Wartet auf Genehmigung |
| Genehmigt | 🟢 Grün | Genehmigt, eingetragen |
| Abgelehnt | 🔴 Rot | Vom Vorgesetzten abgelehnt |
| Storniert | ⚫ Grau | Vom MA oder Vorgesetzten storniert |

## C. Genehmiger-Hierarchie

```
                    ┌─────────────────────┐
                    │  GRP_Urlaub_Admin   │
                    │  (Sandra, Florian)  │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
    ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
    │   Verkauf   │    │   Service   │    │  Werkstatt  │
    │ (Anton Süß) │    │ (M. König)  │    │ (W. Lipp)   │
    └─────────────┘    └─────────────┘    └─────────────┘
```

Bei Eskalation (z.B. Abteilungsleiter selbst) geht der Antrag automatisch an GL/Admin.

---

**Ende des Dokuments**

*Bei Fragen oder Anmerkungen zu diesem Handbuch wenden Sie sich bitte an die IT.*
