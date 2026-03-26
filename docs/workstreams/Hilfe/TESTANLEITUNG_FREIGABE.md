# Testanleitung: Freigabe-Prozess (Hilfe-Modul)

**Stand:** 2026-02-24

---

## Was wurde umgesetzt

- **Freigabe-Status** pro Artikel: `entwurf` (nur im Admin sichtbar) oder `freigegeben` (in der Hilfe sichtbar).
- In der **öffentlichen Hilfe** (/hilfe, Kategorien, Suche, Beliebt) erscheinen nur **freigegebene** Artikel.
- **Admin:** Alle Artikel sichtbar; Buttons **„Freigeben“** und **„Zurück auf Entwurf“**.

---

## So testen Sie

### 1. Voraussetzung

- Eingeloggt als **Admin** (oder User mit Admin-Rechten).
- Portal wurde nach der Umsetzung neu gestartet: `sudo systemctl restart greiner-portal` (falls noch nicht geschehen).

---

### 2. Öffentliche Hilfe prüfen

1. **Hilfe öffnen:** Menü **Hilfe** oder direkt **http://drive/hilfe**
2. **Erwartung:** Sie sehen alle Kategorien (Allgemein, Urlaubsplaner, Controlling, …) mit Artikelanzahl. Beim Klick auf eine Kategorie die zugehörigen Artikel.
3. **Suche:** Unter Hilfe „urlaub“ oder „login“ suchen – Treffer erscheinen.
4. **Einzelartikel:** Einen Artikel öffnen – Inhalt und Feedback-Buttons (👍/👎) sind da.

→ Alle bisherigen Seed-Artikel sind als **freigegeben** gesetzt und müssen sichtbar sein.

---

### 3. Admin: Artikel-Liste und Freigabe-Buttons

1. **Admin öffnen:** **http://drive/hilfe/admin**
2. **Erwartung:** Unter „Alle Artikel“ jede Zeile mit:
   - Badge **„Freigegeben“** (grün) oder **„Entwurf“** (gelb)
   - Bei **Freigegeben:** Button **„Zurück Entwurf“**
   - Bei **Entwurf:** Button **„Freigeben“**
   - Link **„Ansehen“** (öffnet den Artikel in der Hilfe, nur bei Freigegeben sinnvoll sichtbar)

**Test A – Auf Entwurf setzen**

1. Bei einem beliebigen Artikel auf **„Zurück Entwurf“** klicken.
2. Liste lädt neu; der Artikel hat jetzt Badge **„Entwurf“** und Button **„Freigeben“**.
3. **Hilfe-Seite** (http://drive/hilfe) im anderen Tab öffnen bzw. aktualisieren: Die **Kategorie** dieses Artikels zeigt **eine Artikelanzahl weniger** (oder die Kategorie verschwindet aus der Übersicht, wenn 0 Artikel freigegeben).
4. Den **Artikel direkt** aufrufen (z. B. /hilfe/artikel/1): **Nicht gefunden** oder Fehlermeldung (weil nur freigegebene Artikel ausgeliefert werden).

**Test B – Wieder freigeben**

1. In der Admin-Liste beim gleichen Artikel auf **„Freigeben“** klicken.
2. Liste lädt neu; Badge ist wieder **„Freigegeben“**.
3. Hilfe-Seite aktualisieren: Der Artikel erscheint wieder in der Kategorie und ist über Suche/Ansehen erreichbar.

---

### 4. Admin: Artikel bearbeiten – Status und Buttons

1. **Artikel bearbeiten:** In der Admin-Liste auf einen **Titel** klicken (z. B. „Wie logge ich mich im Portal ein?“) → **http://drive/hilfe/admin/bearbeiten/1**
2. **Erwartung:** Oberhalb des Formulars eine **Infobox**:
   - **Freigegeben:** grüne Box mit „Freigegeben am … von … Artikel ist in der Hilfe sichtbar.“
   - **Entwurf:** gelbe Box mit „Entwurf. Artikel ist nur hier sichtbar …“
3. Buttons neben **Speichern:**
   - Bei Freigegeben: **„Zurück auf Entwurf“**
   - Bei Entwurf: **„Freigeben“**

**Test C – Freigeben auf der Bearbeiten-Seite**

1. Einen Artikel, der **Entwurf** ist, in Bearbeitung öffnen.
2. Auf **„Freigeben“** klicken.
3. **Erwartung:** Infobox wechselt auf grün „Freigegeben …“, Button wechselt auf „Zurück auf Entwurf“. Kein Seiten-Reload nötig.
4. Hilfe-Seite prüfen: Artikel ist sichtbar.

**Test D – Zurück auf Entwurf auf der Bearbeiten-Seite**

1. Bei einem **freigegebenen** Artikel auf **„Zurück auf Entwurf“** klicken.
2. Infobox wechselt auf gelb „Entwurf …“, Button auf „Freigeben“.
3. Hilfe-Seite: Artikel nicht mehr sichtbar.

---

### 5. Neuer Artikel = immer Entwurf

1. **Neuer Artikel:** **http://drive/hilfe/admin/neu**
2. Kategorie wählen, Titel eintragen (z. B. „Test-Entwurf“), Inhalt minimal (z. B. „Test“), **Speichern**.
3. **Erwartung:** Sie landen auf der Bearbeiten-Seite des neuen Artikels; Infobox zeigt **Entwurf**, Button **„Freigeben“**.
4. **Hilfe** (http://drive/hilfe): Der neue Artikel erscheint **nicht** in Übersicht/Suche.
5. Nach Klick auf **„Freigeben“**: Artikel erscheint in der Hilfe.

---

## Kurz-Checkliste

- [ ] Hilfe-Übersicht zeigt Kategorien und Artikel (alle aktuell freigegeben).
- [ ] Admin-Liste zeigt bei jedem Artikel Entwurf- oder Freigegeben-Badge und passenden Button.
- [ ] „Zurück Entwurf“ → Artikel in der Hilfe nicht mehr sichtbar.
- [ ] „Freigeben“ → Artikel in der Hilfe wieder sichtbar.
- [ ] Auf der Bearbeiten-Seite: Infobox und Buttons passen zum Status; Freigeben/Entwurf wechseln sofort.
- [ ] Neu angelegter Artikel ist Entwurf und erscheint erst nach Freigeben in der Hilfe.

Wenn etwas davon nicht zutrifft: Browser-Konsole (F12) auf Fehler prüfen, ggf. Portal-Logs `sudo journalctl -u greiner-portal -n 50`.
