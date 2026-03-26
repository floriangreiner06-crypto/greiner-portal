# Outlook „Team: Florian Greiner“ vs. DRIVE-Kalender – Klärung

**Stand:** 2026-02  
**Frage:** Kommt die Konfiguration des Team-Kalenders in Outlook („Team: Florian Greiner“ mit Anton Süß, Brigitte Lackerbeck, Christian Aichinger, Matthias König, Rolf Sterr) aus DRIVE?

---

## Kurzantwort: **Nein**

Die **„Team: Florian Greiner“-Kalendergruppe** in Outlook (mit den einzelnen Personen-Kalendern nebeneinander) wird **nicht** von DRIVE/Portal erzeugt oder konfiguriert. Sie kommt aus **Outlook bzw. Microsoft 365 / Azure AD**.

---

## Was DRIVE mit Microsoft Graph macht

| Aktion | Quelle | Ziel |
|--------|--------|------|
| Kalender-**Schreiben** | `api/vacation_calendar_service.py` | **Eine** Shared Mailbox: `drive@auto-greiner.de` |
| E-Mail-Versand | `api/graph_mail_connector.py` | Office 365 (Mail.Send) |

- **Konfiguration in DRIVE:** Nur `CALENDAR_MAILBOX` (default: `drive@auto-greiner.de`) in `config/.env`; ggf. Graph-Credentials (`GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`).
- **Kein** Aufruf der Graph-API zum Anlegen von Kalendergruppen, zum Hinzufügen von Benutzern zu „Team: …“ oder zum Setzen von Berechtigungen auf **Personen-Kalendern**.

Der Kalender von **drive@** erscheint in Outlook, wenn man ihn manuell hinzufügt („Andere Kalender“ / „Kalender hinzufügen“) – im Screenshot z. B. als **„Autohaus Greiner“** (orange). Das ist derselbe Kalender, in den DRIVE bei genehmigtem Urlaub schreibt.

---

## Woher kommt „Team: Florian Greiner“?

Die **Kalendergruppe** „Team: Florian Greiner“ mit den einzelnen Personen (Anton Süß, Brigitte Lackerbeck, …) stammt aus dem **Outlook-Client / M365**:

1. **Manuell in Outlook:**  
   Kalendergruppe anlegen (z. B. „Neue Kalendergruppe“) und die gewünschten Personen-Kalender hinzufügen. Die Gruppe wird im Postfach/Profil des Benutzers (Florian) gespeichert.

2. **Organisationsstruktur (Azure AD / M365):**  
   Wenn Florian in Azure AD als **Manager** der genannten Benutzer eingetragen ist, kann Outlook „Mein Team“ / direkte Berichte anbieten und daraus eine Team-Ansicht bilden. Das würde in **Azure AD / Microsoft 365 Admin** konfiguriert, nicht in DRIVE.

---

## Zusammenfassung

| Was | Kommt aus DRIVE? |
|-----|------------------|
| Shared-Kalender **drive@** („Autohaus Greiner“) mit Urlaubseinträgen | ✅ Ja – DRIVE schreibt per Graph in diesen Kalender; Mailbox/Konfiguration (drive@) ist die einzige „Kalender-Konfiguration“ aus DRIVE. |
| **„Team: Florian Greiner“** mit Personen-Kalendern (Anton, Brigitte, …) | ❌ Nein – kommt aus Outlook / M365 / Azure AD, nicht aus dem Portal. |

Wenn die Team-Ansicht „jetzt auf einmal“ angezeigt wird, liegt das an einer Änderung in Outlook (z. B. Kalendergruppe angelegt), an M365/Exchange (z. B. Manager-Zuordnung) oder an einem Update des Outlook-Clients – **nicht** an einer Änderung im DRIVE-Code oder an einer neuen Konfiguration aus dem Portal.

---

## Referenzen

- `api/vacation_calendar_service.py` – nur `drive@`-Kalender, nur Schreiben von Events
- `docs/archive/sessions/SESSION_WRAP_UP_TAG104.md` – ursprüngliche Kalender-Integration (Shared Mailbox drive@)
- `docs/workstreams/urlaubsplaner/CONTEXT.md` – Abschnitt Outlook-Kalender
