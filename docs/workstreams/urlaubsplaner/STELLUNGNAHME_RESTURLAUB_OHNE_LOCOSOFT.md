# Stellungnahme: Resturlaubsberechnung ohne Locosoft

**Datum:** 2026-02-24  
**Vereinbarung:** Keine Verbindung zu Locosoft mehr für die Urlaubsanspruchs- bzw. Resturlaubsberechnung.

---

## 1. Ausgangslage

- **Nutzerfeedback:** Resturlaub stimmt nicht (z. B. Jennifer Bielmeier: „20“ angezeigt, 2 Tage Mai offensichtlich nicht berücksichtigt).
- **Vereinbarung:** Die Berechnung von Anspruch und Resturlaub soll **ohne Locosoft** erfolgen – keine Locosoft-Connection für die Urlaubsanspruchsberechnung.

---

## 2. Aktueller Stand (ohne Änderung am Code)

Heute fließt Locosoft noch in die **Anzeige** des Resturlaubs ein:

- **View `v_vacation_balance_{Jahr}`** (Portal):  
  Berechnet aus `vacation_entitlements` und `vacation_bookings` (nur Urlaub, type_id=1)  
  → Anspruch, Verbraucht, Geplant, **Resturlaub (Portal)**.  
  Diese View verwendet **kein** Locosoft.

- **API** (`/balance`, `/my-balance`):  
  Liest den Rest aus der View und wendet danach eine **Locosoft-Kappe** an:  
  `Rest_Anzeige = min(Rest_Portal, Anspruch − Locosoft-Urlaub)`.  
  Dafür wird `get_absences_for_employee(s)` (Locosoft) aufgerufen.

**Beispiel Jennifer Bielmeier:**

- Portal (View): 28 Anspruch, 2 verbraucht (21./22.05.) → **Rest = 26**.
- Locosoft: 8 Urlaubstage (Url/BUr) für 2026 → Anzeige = min(26, 28−8) = **20**.

Die 2 Mai-Tage sind in der Portal-View berücksichtigt (daher 26). Die Anzeige „20“ kommt ausschließlich von der Locosoft-Kappe. Das widerspricht der Vereinbarung „keine Locosoft-Connection für Urlaubsanspruchsberechnung“.

---

## 3. Konsequenz

- **Resturlaub** (Anspruch, Verbraucht, Geplant, Rest) soll **nur aus Portal-Daten** kommen:  
  `vacation_entitlements` + `vacation_bookings` → View `v_vacation_balance_{Jahr}`.  
  **Kein** Abruf von Locosoft-Abwesenheiten für diese Berechnung, **keine** min()-Kappe mit Locosoft-Urlaub.

- Locosoft kann weiterhin für andere Zwecke genutzt werden (z. B. Anzeige „in Locosoft“, Kalender-Layer), **nicht** aber für die Zahl „Resturlaub“ oder die Logik „Anspruch − Verbraucht − Geplant“.

---

## 4. Was die Stellungnahme abdeckt

- **Feststellung:** Aktuell wird Locosoft noch für die Rest-Anzeige genutzt; das steht im Widerspruch zur Vereinbarung.
- **Zielbild:** Eine einzige Quelle für Resturlaub = View (Portal). Keine Locosoft-Connection für Urlaubsanspruchs-/Resturlaubsberechnung.
- **Kein Code:** Es wird hier **nichts** implementiert oder geändert – nur die Stellungnahme und das Zielbild festgehalten. Die konkrete Umsetzung (Entfernen der Locosoft-Aufrufe bzw. -Kappe in der Rest-Logik) erfolgt in einem separaten Schritt.

---

## 5. Relevante Stellen (für spätere Umsetzung)

- `api/vacation_api.py`:  
  - `_compute_rest_display(..., loco_urlaub)` – Locosoft-Parameter/Kappe.  
  - `get_all_balances` / `get_my_balance` – Aufruf von Locosoft und Übergabe von `loco_urlaub`.  
  - `_get_available_rest_days_for_validation` – gleiche Logik, eine Quelle.
- View `v_vacation_balance_{year}` – bleibt **einzige** Quelle für Rest (ohne Locosoft).

---

**Fazit:** Die Resturlaubsberechnung soll vereinbarungsgemäß **ohne Locosoft** erfolgen. Diese Stellungnahme hält das fest.

---

## 6. Umsetzung (2026-02)

- **Umgesetzt:** Resturlaub kommt nur noch aus DRIVE (View `v_vacation_balance_{Jahr}`). In `api/vacation_api.py`: `_compute_rest_display` ignoriert Locosoft; `get_my_balance`, `get_all_balances`, Team-Balance und `_get_available_rest_days_for_validation` nutzen keine Locosoft-Werte mehr für die Rest-Berechnung. Locosoft wird weiterhin optional für Anzeige (z. B. urlaub_locosoft, Kalender) abgefragt, aber nicht für Anspruch/Rest.
