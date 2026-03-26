# Resturlaub: Krankheitstage zählen nicht

## Problem (Vanessa, Stefan Geier)

Nach Eintrag von **Krankheitstagen** bis 23.03. wurde der **Resturlaub** neu berechnet und um 5 Tage reduziert (58 → 53). Krankheit darf den Resturlaub **nicht** mindern.

## Technischer Stand

- **View `v_vacation_balance_*`:** Zählt nur **Urlaub** (`vacation_type_id = 1`) in verbraucht/geplant/resturlaub. Krankheit (type_id 5) ist dort **nicht** enthalten. (TAG 198)
- **Locosoft-Korrektur:** Die Anzeige nutzt `min(View-Resturlaub, Anspruch − Locosoft-Urlaub)`. In Locosoft zählen nur **Url** und **BUr** als „Urlaub“; **Krn** (Krank) wird getrennt geführt.

## Mögliche Ursache

Wenn der Resturlaub trotzdem sinkt, sobald Krankheitstage eingetragen werden, kann **Locosoft** diese Tage fälschlich als **Urlaub (Url/BUr)** statt als **Krn** führen. Dann erhöht sich „Locosoft-Urlaub“, und die Anzeige wird nach unten begrenzt.

## Maßnahmen im Portal (Fix)

1. **Safeguard in der Anzeige:**  
   Wenn `(Anspruch − Locosoft-Urlaub)` mehr als 0,5 Tage **unter** dem View-Resturlaub liegt, wird **der View-Resturlaub** angezeigt. So wird verhindert, dass in Locosoft falsch erfasste Urlaubstage (z. B. eigentlich Krankheit) den angezeigten Rest künstlich drücken.
2. **Gleiche Logik** in `/balance`, `/my-balance` und in der Resturlaub-Validierung beim Buchen.

## Was ihr prüfen könnt

- **Locosoft:** Für Stefan Geier (und ggf. andere) prüfen, ob die Krankheitstage bis 23.03. in Locosoft als **Krn** und **nicht** als Url/BUr gebucht sind.
- Nach dem Fix sollte der Resturlaub für Stefan wieder **58** anzeigen, sofern die View 58 liefert und keine echten Urlaubstage in Locosoft dazukommen.
