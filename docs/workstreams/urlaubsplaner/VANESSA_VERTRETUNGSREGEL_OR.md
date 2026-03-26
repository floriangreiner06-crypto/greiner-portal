# Vanessa: Vertretungsregel – entweder Margit oder Ilayda

**Quelle:** Anmerkung Vanessa (Workstream/Windows-Verzeichnis), 2026-02

## Wunsch

Vertretungsregel so bauen, dass **entweder Margit oder Ilayda** da sein müssen. Bei Jennifer sind beide als Vertretung hinterlegt. Jennifer hatte am 02.01. Ausgleichstag, Ilayda Urlaub – Urlaub von Ilayda konnte nicht eingetragen werden, weil die Vertretungsregel griff. Dasselbe bei Margit: Fehlermeldung beim Urlaubseintrag.

## Umsetzung

- **Neu:** Blockierung nur, wenn die vertretene Person abwesend ist **und** an demselben Tag **keine andere** Vertretung anwesend ist (mindestens eine Vertretung muss da sein).
- **Datei:** `api/vacation_api.py` – `_check_substitute_vacation_conflict()`.
- **CONTEXT.md:** Eintrag unter „Vertretungsregel + Resturlaub nach Eingabe“.
