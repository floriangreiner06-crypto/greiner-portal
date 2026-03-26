# Mehr Inhalt für die Hilfe – Optionen

**Stand:** 2026-02-24

Die Seed-Artikel sind bewusst knapp (Schnellhilfe). Für **mehr Tiefe und bessere Beschreibungen** gibt es mehrere Wege.

---

## 1. Manuell aufschreiben

- **Wer:** Fachabteilungen (HR für Urlaub, Buchhaltung für Controlling, Verkauf für Auftragseingang usw.) oder eine zentrale Redaktion.
- **Wie:** In der **Hilfe-Verwaltung** (/hilfe/admin) Artikel bearbeiten, Absätze ergänzen, Beispiele (z. B. „Klicken Sie auf …“, „Feld X bedeutet …“) einfügen.
- **Vorteil:** Volle Kontrolle, firmenspezifische Formulierungen, echte Praxis.
- **Nachteil:** Zeitaufwand, oft fehlt die Kapazität.

---

## 2. KI nutzen (Empfehlung: Hybrid)

KI kann **nicht** die finale Verantwortung übernehmen, aber sehr gut **Rohfassungen** liefern, die Sie dann prüfen und anpassen.

### Was KI gut kann
- Aus **Stichpunkten** oder **kurzen Beschreibungen** einen vollständigen Artikel in gleicher Struktur (Kurz-Antwort, Schritt für Schritt, Hinweise) erzeugen.
- **Bestehende kurze Artikel** „erweitern“: gleichen Inhalt, mehr Erklärung, Beispiele, FAQ-ähnliche Absätze.
- **Einheitlichen Ton** („Sie“, sachlich, für Mitarbeiter) einhalten.

### Mögliche Wege

**A) Einmalig mit Cursor/Claude (ohne Code)**  
- Sie öffnen einen Hilfe-Artikel (oder die Liste der Titel) und bitten z. B.:  
  „Erweitere diesen Hilfe-Artikel für DRIVE-Mitarbeiter: Behalte die Struktur (Kurz-Antwort, Schritt für Schritt, Hinweise), füge konkrete Beispiele und 1–2 FAQ-Fragen hinzu. Markdown-Format.“  
- Das Ergebnis kopieren Sie in die Hilfe-Verwaltung und passen Links/Begriffe an.

**B) Optional: „KI erweitern“ im Admin (später)**  
- Im Hilfe-Modul ein Button **„Mit KI erweitern“** neben dem Artikel-Editor.
- Backend sendet Titel + aktuellen Inhalt an eine KI-API (z. B. AWS Bedrock, da ihr es schon für Fahrzeugschein-OCR nutzt).
- Prompt z. B.: „Erweitere den folgenden Hilfe-Artikel für ein internes Autohaus-Portal. Zielgruppe: Mitarbeiter. Behalte Markdown und die Abschnitte Kurz-Antwort, Schritt für Schritt, Hinweise. Füge wo sinnvoll Beispiele oder typische Fragen hinzu. Maximal 2x so lang.“
- Das **Ergebnis wird nur als Vorschlag** angezeigt; ein Mensch fügt es ein bzw. bearbeitet und speichert.

**C) Einmaliges Script**  
- Ein Python-Script liest alle `hilfe_artikel`, ruft für jeden (oder nur ausgewählte) eine KI-API auf, schreibt die erweiterten Texte in eine **neue Spalte** oder in Dateien.
- Redaktion vergleicht Alt/Neu und übernimmt manuell in die DB (z. B. über Admin).

---

## 3. Bestehende Quellen einbinden

- **Word/PDF-Anleitungen**, die es schon gibt (z. B. „Urlaubsplaner Anleitung.docx“), in Abschnitte zerlegen und als Hilfe-Artikel anlegen oder an bestehende Artikel anhängen.
- **Screenshots:** In Artikeln Verweise wie „Siehe Abbildung oben“ + Bild per Admin hochladen (falls ihr später eine Bild-Verwaltung für Hilfe einbaut) oder extern verlinken.
- **Links** auf Schulungsvideos oder Intranet-Seiten in den Hinweisen ergänzen.

---

## 4. Konkrete Empfehlung

1. **Kurzfristig (ohne Code):**  
   - Pro Kategorie 1–2 Artikel auswählen, die am wichtigsten sind.  
   - In Cursor/Claude (oder ChatGPT) den **bestehenden kurzen Text** einfügen und bitten: „Erweitere diesen Hilfe-Artikel …“ (wie oben).  
   - Ergebnis in der Hilfe-Verwaltung einfügen, prüfen, Links/Begriffe anpassen, speichern.

2. **Mittelfristig (wenn ihr mehr Artikel habt):**  
   - Optional Feature **„Mit KI erweitern“** im Hilfe-Admin: Button → API-Aufruf (Bedrock/OpenAI) → Vorschlag anzeigen → Mensch übernimmt.  
   - So müsst ihr nicht alles „von Hand“ aufschreiben, behaltet aber die Kontrolle.

3. **Inhalte pflegen:**  
   - Bei jedem größeren Release (z. B. neues Feature im Urlaubsplaner) einen kurzen Absatz in den passenden Hilfe-Artikel ergänzen – das bleibt Aufgabe von Menschen, KI kann nur Vorlagen liefern.

---

## Kurz: Müssen wir alles aufschreiben?

- **Nein.** Ihr könnt KI gezielt nutzen, um aus kurzen Texten oder Stichpunkten **Rohfassungen** zu erzeugen.
- **Ja, in dem Sinne:** Jeder veröffentlichte Inhalt sollte von einem Menschen **geprüft und freigegeben** werden (Richtigkeit, Tonalität, firmenspezifische Details).
- **Pragmatisch:** Einmalig 5–10 wichtige Artikel per KI erweitern (Copy-Paste oder kleines Script), dann schrittweise mit echten Nutzerfragen und Releases nachpflegen.

Wenn ihr euch für einen der Wege (z. B. „KI erweitern“-Button mit Bedrock) entscheidet, kann die konkrete Umsetzung im Hilfe-Modul als nächster Schritt geplant werden.
