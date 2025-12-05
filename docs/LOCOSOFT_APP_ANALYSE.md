# 📱 LOCOSOFT "MEIN-AUTOHAUS" APP - FEATURE-ANALYSE

**Analysiert:** 2025-12-02  
**Aktuelle Version:** V2.16.179 (iOS) / V2.15.177 (Android)  
**Quelle:** https://www.mein-autohaus.app + Update-Logs

---

## 🎯 KERNFEATURES DER APP

### 1. 👥 KUNDEN & FAHRZEUGE
- Kundensuche (erweitert: Name, Straße, Tel, E-Mail, PLZ, Ansprechpartner)
- Fahrzeugsuche (Kennzeichen, Modell, Schlüsselkasten-Nr, Käufer)
- Kundenakte einsehen und bearbeiten
- Fahrzeugakte mit allen Details
- **Kontakteinträge** anlegen, bearbeiten, schließen
- Medien (Bilder, Videos, Audio) zu Kunden/Fahrzeugen hochladen

### 2. 🚗 HÄNDLERFAHRZEUGE
- Bestand und Vorlauf einsehen
- Motorisierung, Farbe, Zubehör anzeigen
- **Standort-Tracking via QR-Code oder NFC-Chip**
- Kilometerstand aktualisieren
- Tankfüllung/Sauberkeit pflegen
- "Muss gereinigt werden" / "Muss in Werkstatt" markieren
- **Loco-Location-Chips (LLC)** für Fahrzeug-Tracking
- Schlüsselkasten-Nummer anzeigen
- Position per WhatsApp/E-Mail teilen

### 3. 📋 AUFTRÄGE
- Aufträge anlegen und bearbeiten
- Arbeiten und Ersatzteile hinzufügen
- km-Stand im Auftrag anpassen
- **Auftragspositionen stempeln**
- Bilder/Videos/Audio zum Auftrag hinzufügen
- Werkstattauftrag unterschreiben lassen
- Per E-Mail an Kunden senden
- Auftragsbestätigung drucken

### 4. ✅ CHECKLISTEN (Dialogannahme)
Kategorien:
- Allgemein
- Annahmecheckliste  
- Arbeitsdurchführung
- Schlussabnahme
- Verkauf

Features:
- Checkboxen (OK / Nicht OK / Unklar)
- Fahrzeugskizze für Schadensmarkierung
- Drop-Down Menüs
- Freitext-Eingaben
- Pflichtfelder definierbar
- Bremswerterfassung
- **Kunde + Mitarbeiter Unterschrift**
- PDF-Export in Auftrag

### 5. 🔔 IBN (Inner-Betriebliche-Nachrichten)
- Nachrichten lesen und schreiben
- Weltweit verfügbar
- Prioritäten (wichtig/normal)
- Suche mit Highlighting
- URL/E-Mail/Telefon direkt aufrufbar

### 6. 📅 TERMINKALENDER
- Tagesansicht
- Termine aller Mitarbeiter einsehen
- **Termine erfassen, bearbeiten, löschen**
- Start-/Endzeit
- **Werkstatt-Termine aus Pr. 266!**
- Urlaub und Abwesenheiten sichtbar
- IBN-Erinnerung bei Terminen

### 7. ⏱️ ZEITERFASSUNG
- Kommt/Geht stempeln
- Pausen stempeln
- Anwesenheit Kollegen sehen
- **GPS-Position bei Stempelung**
- Monatliche Arbeitszeit-Übersicht
- Nach Mitarbeitergruppen filtern

### 8. 🔧 ERSATZTEILE
- Teilesuche (auch per Barcode)
- Lagerbestand prüfen
- Teile-Medien hinterlegen
- Bilder zu Ersatzteilen

### 9. 🛞 RÄDER/REIFEN (Pr. 541)
- Reifeneinlagerung verwalten
- Ein-/Auslagerung mit/ohne Montage
- Profiltiefe, DOT, Reifendruck erfassen
- **Reifenetiketten drucken**
- Lagerort suchen
- Bis zu 99 Bilder pro Vorgang
- Temporäre Lagerorte

### 10. 📊 STATISTIKEN (Pr. 272/273)
- Jahres-/Monats-/Tagesumsätze
- 3-Jahres-Vergleich grafisch
- Einzelrechnungen
- Betriebsstätten-Filter
- Kundenrechnungen in Kundenakte

### 11. 📦 INVENTUR
- Teile per Barcode scannen
- Manuelle Auswahl aus Liste
- Nach Lager sortiert
- **OFFLINE-Modus!**

### 12. 🗺️ KUNDENRADAR
- Kunden auf Landkarte anzeigen
- Nach Kundencode filtern
- Codes ein-/ausschließen
- Zoom-Funktion

---

## 💡 BESONDERS INTERESSANT FÜR WERKSTATTPLANUNG

| Feature | Relevanz | In App vorhanden |
|---------|----------|------------------|
| **Werkstatt-Termine aus Pr. 266** | ⭐⭐⭐ | ✅ JA! |
| Mitarbeiter-Kalender | ⭐⭐⭐ | ✅ |
| Aufträge anlegen/bearbeiten | ⭐⭐⭐ | ✅ |
| Checklisten/Dialogannahme | ⭐⭐⭐ | ✅ |
| Zeiterfassung/Stempeln | ⭐⭐ | ✅ |
| Anwesenheits-Übersicht | ⭐⭐ | ✅ |
| Ersatzteil-Verfügbarkeit | ⭐⭐ | ✅ |
| Offline-Modus | ⭐⭐ | ✅ (nur Inventur) |

---

## 🔌 TECHNISCHE DETAILS

### Verbindung zu Locosoft:
- **App-Server-Dienst** in Pr. 987 erforderlich
- QR-Code für Mitarbeiter-Freischaltung
- Server-Ruhezeiten konfigurierbar
- JWT-Token-Authentifizierung

### Berechtigungen:
- Steuerung über **Pr. 983** (Zugriff-Schlüssel)
- Vertrauenszugriff in **Pr. 984**
- Mitarbeiter-Berechtigung pro Programm

### Programme die relevant sind:
- **Pr. 266** - Werkstattplanung/Termine
- Pr. 211 - Aufträge
- Pr. 111 - Kundenakte
- Pr. 112 - Fahrzeugakte
- Pr. 132 - Händlerfahrzeuge
- Pr. 541 - Rädereinlagerung
- Pr. 281 - Zeiterfassung
- Pr. 818 - Terminkalender
- Pr. 812 - Abwesenheiten/Urlaub

---

## 📱 APP-BEWERTUNGEN (App Store)

**Kritik:**
- "Bilder nicht direkt in Auftrag hochladbar" (ohne komplette Einlagerung)
- "Signaturfunktion nicht kundenfreundlich"
- "Keine Bilder in Checklisten"
- "Server nicht erreichbar" Probleme
- "Scanner funktioniert nicht immer"

**Positiv:**
- Umfangreiche Features
- Gute Locosoft-Integration
- Ständige Updates

---

## 🎯 ERKENNTNISSE FÜR GREINER PORTAL

### Was die App KANN (und wir nutzen könnten):
1. ✅ **Werkstatt-Termine aus Pr. 266** - die Daten sind also da!
2. ✅ Mitarbeiter-Kalender mit Terminen
3. ✅ Abwesenheiten/Urlaub integriert
4. ✅ Aufträge mobil bearbeiten

### Was die App NICHT gut kann (unsere Chance!):
1. ❌ Übersichtliche Werkstatt-Plantafel
2. ❌ Kapazitätsplanung visuell
3. ❌ Einfacher Workflow für Serviceberater
4. ❌ Desktop-optimierte Ansicht

### Datenquellen bestätigt:
```
Locosoft Pr. 266 = Werkstattplanung
  → Hat Termine!
  → Wird in App angezeigt
  → Muss in PostgreSQL sein (times? orders? workshop_orders?)
```

---

## 🚀 NÄCHSTE SCHRITTE

1. **Locosoft PostgreSQL analysieren:**
   - `orders` Tabelle → Aufträge
   - `times` Tabelle → Zeiterfassung
   - Suchen nach Pr. 266 Daten

2. **Herausfinden:**
   - Wo sind die Werkstatt-Termine in PostgreSQL?
   - Wie sind Mechaniker den Terminen zugeordnet?
   - Gibt es eine `appointments` oder `schedule` Tabelle?

3. **MVP definieren:**
   - Desktop-Plantafel (was App nicht hat)
   - Einfacher als DA
   - Besser als Locosoft 266

---

## 📋 ZUSAMMENFASSUNG

Die "Mein-Autohaus" App zeigt:
- **Locosoft HAT die Werkstattplanungs-Daten** (Pr. 266)
- Die Daten sind über App-Server zugänglich
- Die App ist MOBIL-optimiert, nicht DESKTOP
- **Unsere Chance:** Desktop-Plantafel mit besserem UX

**Empfehlung:** Die Werkstatt-Daten sind definitiv in Locosoft vorhanden. 
Wir müssen nur herausfinden, in welcher PostgreSQL-Tabelle!

---

*Erstellt von Claude - TAG 88*
