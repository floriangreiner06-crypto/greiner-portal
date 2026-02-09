# Twilio WhatsApp Sandbox – Handy verbinden

**TAG:** 211  
**Ziel:** Dein Handy mit der Twilio-Sandbox verbinden, damit du Nachrichten senden und empfangen kannst.

---

## Schritt 1: Join-Code in Twilio holen

1. Im Browser: **https://console.twilio.com** öffnen und einloggen.
2. Links: **Messaging** → **Try it out** → **Send a WhatsApp message** (oder **Explore** → **Messaging** → **Try it out**).
3. Dort siehst du z.B.:
   - **Sandbox-Nummer:** z.B. `+1 415 523 8886`
   - **Join-Code:** z.B. `join blau-gras` oder `join gruen-himmel`  
   → **Diesen Code (z.B. „blau-gras“) merken oder notieren.**

---

## Schritt 2: WhatsApp auf dem Handy öffnen

1. **WhatsApp** auf deinem Smartphone öffnen.
2. **Neuen Chat** starten (z.B. „Neuer Chat“ / Stift-Symbol).

---

## Schritt 3: Sandbox-Nummer als Kontakt anlegen (optional)

1. Die **Sandbox-Nummer** in deine Kontakte eintragen, z.B.:
   - **+1 415 523 8886** (ohne Leerzeichen).
   - Name z.B. „Twilio Sandbox“.
2. Oder: In WhatsApp beim „Neuen Chat“ die Nummer direkt eingeben: **+14155238886** (mit Ländervorwahl +1 für USA).

---

## Schritt 4: Join-Nachricht senden

1. In WhatsApp einen **neuen Chat** mit der Sandbox-Nummer starten (z.B. +1 415 523 8886).
2. **Genau diese Nachricht** schreiben (Join-Code aus Schritt 1 verwenden):
   ```text
   join blau-gras
   ```
   (Statt „blau-gras“ deinen echten Code aus der Twilio-Console eintragen – nur Kleinbuchstaben, Leerzeichen wie angezeigt.)
3. **Senden** tippen.

---

## Schritt 5: Bestätigung

- Twilio antwortet in der Regel mit etwas wie: **„You're all set! …“** oder **„Sie sind bereit! …“**  
- Ab dann:
  - Du kannst **an diese Sandbox-Nummer** schreiben → Nachrichten kommen in DRIVE an (wenn Webhook steht).
  - Von DRIVE **an deine Handynummer** gesendete Nachrichten erscheinen in deinem WhatsApp.

---

## Wichtig

- **Nur dieses eine Handy** (bzw. diese Nummer) ist mit der Sandbox verbunden.  
- **Trial-Account:** Es können nur Nachrichten an **verifizierte Nummern** gehen – deine Nummer ist nach dem „join“ verifiziert.  
- **Sandbox-Nummer:** Immer die Nummer aus der Twilio-Console verwenden (z.B. +1 415 523 8886), nicht deine eigene.

---

## Kurz-Checkliste

- [ ] In Twilio: **Messaging** → **Try it out** → **Send a WhatsApp message**.
- [ ] **Sandbox-Nummer** und **Join-Code** (z.B. `join blau-gras`) notieren.
- [ ] WhatsApp öffnen → Neuer Chat mit **Sandbox-Nummer** (z.B. +14155238886).
- [ ] Nachricht **„join &lt;dein-code&gt;“** senden.
- [ ] Bestätigung von Twilio abwarten → dann ist das Handy verbunden.

---

**Danach:** In DRIVE (z.B. **Verkauf → WhatsApp Chat**) eine Nachricht an deine eigene Nummer senden – sie sollte auf dem Handy in WhatsApp ankommen (sobald alles konfiguriert ist).
