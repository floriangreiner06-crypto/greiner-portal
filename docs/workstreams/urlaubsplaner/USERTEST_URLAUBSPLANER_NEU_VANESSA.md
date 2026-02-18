# Usertest „Urlaubsplaner neu“ (Vanessa)

**Quelle:** `Urlaubsplaner neu.docx` (F:\Buchhaltung\VG\DRIVE\ bzw. docs/workstreams/urlaubsplaner/)  
**Stand:** 2026-02-16 (Inhalt ins Repo übernommen)

---

## Punkte aus dem Dokument

### Urlaubsplaner

1. **Spezifische Mitarbeiter-Auswahl bei Masseneingabe nicht möglich**  
   → Gewünscht: Bei Masseneingabe gezielt einzelne Mitarbeiter auswählen können.

2. **Urlaubssperre auch für Admins ohne Masseneingabe (Landau und Deggendorf sind nicht getrennt)**  
   → Urlaubssperren sollen auch für Admins gelten (kein Umgehen via Masseneingabe). Außerdem: Landau und Deggendorf getrennt abbilden/sperren.

3. **Urlaubssperre kann nicht gelöscht werden, bitte beheben!**  
   → Bug: Urlaubssperren lassen sich nicht löschen.

4. **Schulung und Krankheitstage evtl. farblich unterschiedlicher machen**  
   → Schulung evtl. blau (wie bisher), Krankheit anders, damit besser unterscheidbar.

5. **Meine Anträge auf der rechten Seite stören evtl. entfernen**  
   → Rechtsleiste „Meine Anträge“ wirkt unübersichtlich; ggf. entfernen oder reduzieren.

6. **Monatsauswahl wäre super, wenn man mit Pfeilen einen Monat nach vorne und zurück springen könnte**  
   → Zusätzlich zu Monat/Jahr-Dropdown: Pfeile für Vor/Zurück (wie früher?).

7. **Mitarbeiter sind noch z.T. ohne AD!**  
   → Hinweis: Einige Mitarbeiter ohne AD-Zuordnung (bereits als „kein AD“ im Planer sichtbar).

### Mitarbeiterverwaltung

8. **„Neuen Mitarbeiter anlegen“, „Anwendungen“ und „Reporte“ ohne Funktion**  
   → Diese Buttons/Bereiche haben derzeit keine Funktion.

9. **„Anwendungen“ benötigt man in diesem Fall nicht mehr**  
   → Kann entfallen oder ausgeblendet werden.

10. **„Reporte“**  
    Hier soll eine Liste mit allen Mitarbeitern mit Übersicht:  
    - wie viel Urlaubsanspruch sie haben,  
    - wie viel Urlaubstage bereits genommen,  
    - wie viele noch offen sind.  
    Urlaubstage auch **nach Monaten aufzuteilen**.  
    **Wichtig für Jahresabschluss, Rückstellung im August!**

---

## Zuordnung (kurz) – Stand Umsetzung

| Nr | Thema | Typ | Status |
|----|--------|-----|--------|
| 1 | Masseneingabe: Mitarbeiter-Auswahl | Wunsch | ✅ Umgesetzt: Option „Spezifische Mitarbeiter“, Multi-Select; Standard beim Öffnen |
| 2 | Urlaubssperre für Admins, Standorte getrennt | Wunsch/Bug | ✅ Masseneingabe prüft jetzt Sperren (kein Admin-Bypass). Landau/Deggendorf getrennt: offen (Schema location in vacation_blocks) |
| 3 | Urlaubssperre löschen | Bug | ✅ Umgesetzt: Urlaubsplaner-Admin-Seite zeigt Sperren mit Button „Löschen“ |
| 4 | Farben Schulung/Krankheit | UX | ✅ Schulung blau (#5C6BC0), Krankheit (#E91E63) |
| 5 | „Meine Anträge“ Seitenleiste | UX | ✅ Ein-/ausklappbar, standardmäßig eingeklappt |
| 6 | Monats-Pfeile | UX | ✅ Pfeile „Vorheriger“ / „Nächster Monat“ neben Dropdowns |
| 7 | Mitarbeiter ohne AD | Hinweis | Anzeige vorhanden („kein AD“) |
| 8–9 | Anwendungen/Reporte | MV | ✅ „Anwendungen“ entfernt. „Reporte“ öffnet Modal mit Urlaubs-Report (Name, Anspruch, Genommen, Offen) |
| 10 | Report: Urlaubsübersicht + nach Monaten | Anforderung | ✅ Report mit Jahr-Auswahl, Tabelle aller MA (Anspruch/Genommen/Offen). Nach Monaten: ggf. Erweiterung |

---

**Referenz:** Word-Datei liegt im Sync unter  
`docs/workstreams/urlaubsplaner/Urlaubsplaner neu.docx` (auf Server ggf. unter `/mnt/greiner-portal-sync/...`).
