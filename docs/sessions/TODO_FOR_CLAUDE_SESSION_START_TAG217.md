# TODO für Session-Start TAG 217

**Stand:** 2026-02-24 (Session-Ende TAG 216)

---

## Kontext

- **Urlaubsplaner:** Rollout für Abteilung Disposition; Vanessa schult. Rest = min(Portal-Rest, Anspruch − Locosoft-Urlaub); Anspruch aus Mitarbeiterverwaltung; kein pauschaler Weihnachten/Silvester-Abzug.
- **Session Wrap-Up:** `docs/sessions/SESSION_WRAP_UP_TAG216.md`

---

## Offene Aufgaben (nach Priorität)

1. **Urlaubsplaner (optional):** Rest-Berechnung in **eine** zentrale Hilfsfunktion auslagern (`_compute_rest_display` o. ä.), um Duplikate in get_all_balances, get_my_balance, _get_available_rest_days_for_validation, get_my_team zu reduzieren (siehe ANALYSE_RESTURLAUB_FEHLERQUELLEN.md).

2. **Markdown ins Windows-Sync:** Nach Bearbeitung von .md in `docs/` ggf. nach `/mnt/greiner-portal-sync/docs/` kopieren (gleicher Unterpfad), damit unter Windows sichtbar.

---

## Nächste Schritte (fachlich)

- Rollout Disposition begleiten (Vanessa Schulung).
- Bei Feedback zu Rest-Anzeige oder Locosoft-Abweichungen: CONTEXT.md Urlaubsplaner prüfen, ggf. Safeguard (Krankheit in Locosoft als Url) wieder diskutieren.

---

## Qualitätsprobleme (optional beheben)

- Resturlaub-Formel an 4+ Stellen dupliziert; Auslagerung in eine Funktion würde SSOT und Wartung verbessern.

---

## Wichtige Hinweise für nächste Session

- **CLAUDE.md** und **docs/workstreams/urlaubsplaner/CONTEXT.md** lesen.
- Urlaubsplaner: Anspruch = Mitarbeiterverwaltung (vacation_entitlements); Rest = min(View-Rest, Anspruch − Locosoft-Urlaub). Kalender = Portal + Locosoft.
- Migration `fix_margit_loibl_urlaubsanspruch_2026.sql` wurde ausgeführt (Margit Loibl 2026 = 27 Tage).
