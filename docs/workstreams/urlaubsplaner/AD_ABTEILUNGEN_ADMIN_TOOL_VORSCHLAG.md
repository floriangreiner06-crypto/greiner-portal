# Admin-Tool: Abteilungen im AD pflegen / Mitarbeiter zuweisen

**Stand:** 2026-02-27  
**Kontext:** Vanessa soll Abteilungen (z. B. „Fahrzeuge“) an der richtigen Stelle anlegen und Mitarbeiter in Abteilungen zuweisen können – sicher und über die DRIVE-Admin-Oberfläche.  
**Abteilung „Fahrzeuge“** existiert im AD derzeit noch nicht (als Wert im User-Attribut).

---

## 1. Wie „Abteilung“ im AD funktioniert

Im Active Directory ist **Abteilung** kein eigenes Objekt (kein Container, keine OU), sondern ein **Attribut am Benutzerobjekt**:

- **Attributname:** `department` (Standard-AD-Attribut)
- **Typ:** Zeichenkette (z. B. „Disposition“, „Service“, „Fahrzeuge“, „Kundenzentrale“)
- **Pro User:** Jeder User hat genau einen Wert in `department` (oder keinen).

Das Portal liest diesen Wert bereits beim Sync:  
`auth/ldap_connector.py` → `get_user_details()` holt u. a. `department` und der Sync schreibt ihn nach `employees.department_name`.

**Folge:**  
„Abteilung Fahrzeuge anlegen“ bedeutet **nicht**, im AD einen neuen Ordner/OU anzulegen, sondern:  
Bei den gewünschten Benutzern (z. B. Stephan Wittmann, Götz Klein, Sandra Schimmer) das Attribut **`department`** auf den Wert **„Fahrzeuge“** setzen. Sobald das gesetzt ist und ein Sync läuft, erscheint „Fahrzeuge“ im Organigramm und überall, wo `department_name` aus der Portal-DB kommt.

---

## 2. Zwei Wege für ein sicheres Tool

### Option A: Nur Portal (ohne AD-Schreibzugriff)

- **Tool in Admin:**  
  - Abteilungsliste aus der DB (z. B. alle vorkommenden `department_name` + Möglichkeit, **neue Abteilung** z. B. „Fahrzeuge“ hinzuzufügen).  
  - Pro Mitarbeiter: Abteilung auswählen (Dropdown) und speichern → nur **`employees.department_name`** wird in der Portal-DB aktualisiert.
- **Vorteil:** Keine AD-Rechte nötig, sofort nutzbar, keine Änderung am AD.
- **Nachteil:** Beim nächsten Sync „von AD mit Überschreiben“ würde der AD-Wert wieder reinkopiert und die Portal-Änderung ggf. überschrieben (wenn AD weiterhin alten/leeren Wert hat).  
  → Sinnvoll nur, wenn ihr entweder **ohne Überschreiben** syncet oder das Sync-Verhalten so anpasst, dass `department_name` bei „Portal-Management“ nicht überschrieben wird.

### Option B: Portal + AD (AD als Quelle, einheitlich)

- **Voraussetzung:** Der Portal-Service-Account (z. B. `svc_portal@auto-greiner.de`) oder ein eigener „HR-Sync“-Account hat im AD **Schreibrechte** auf Benutzerobjekte (mindestens Attribut `department`).
- **Tool in Admin:**  
  - Wie Option A: Abteilungen verwalten (inkl. „Fahrzeuge“), Mitarbeiter einer Abteilung zuweisen.  
  - Beim Speichern:  
    1. **Portal:** `employees.department_name` setzen.  
    2. **AD:** Bei vorhandenem `ldap_username` (sAMAccountName) das Attribut **`department`** des entsprechenden AD-Users auf den gewählten Wert setzen (LDAP MODIFY).
- **Vorteil:** AD bleibt die eine Quelle; Sync kann unverändert mit „Überschreiben“ laufen; Organigramm und alle Auswertungen bleiben konsistent mit dem AD.
- **Nachteil:** Erfordert AD-Konfiguration (Rechte) und eine kleine Erweiterung im LDAP-Connector (z. B. `update_user_department(ldap_username, department)`).

**Empfehlung:** Wenn ihr die Abteilungen dauerhaft im AD führen wollt (wie besprochen), **Option B** umsetzen und dafür die AD-Rechte für das Setzen von `department` bereitstellen.

---

## 3. Konkreter Vorschlag für die Admin-Oberfläche (sicher)

Unabhängig von A oder B kann die Oberfläche so aussehen:

1. **Bereich:** Admin → z. B. „Abteilungen verwalten“ oder Erweiterung **Rechteverwaltung / Organigramm** (Tab „Abteilungen“).
2. **Berechtigung:** Nur für Rollen mit Rechten für Organigramm/HR (z. B. Admin, HR, Vanessa) – z. B. `can_access_feature('admin')` oder eigenes Feature `organigramm_edit` / `department_manage`.
3. **Funktionen:**  
   - **Abteilungsliste:** Alle aktuell in der Portal-DB vorkommenden Abteilungen (DISTINCT `department_name`) anzeigen.  
   - **Neue Abteilung anlegen:** Freitext (z. B. „Fahrzeuge“) – wird nur als erlaubter Wert geführt; beim ersten Zuweisen eines Mitarbeiters erscheint sie im Organigramm.  
   - **Mitarbeiter zuweisen:**  
     - Mitarbeiterliste (aus Portal, ggf. gefiltert nach Standort/aktiv).  
     - Pro Mitarbeiter: Dropdown „Abteilung“ (bestehende + neu angelegte) und „Speichern“.  
     - Optional: Mehrfachauswahl (z. B. Stephan Wittmann, Götz Klein, Sandra Schimmer → Abteilung „Fahrzeuge“ → einmal speichern).
4. **Sicherheit / Sauberkeit:**  
   - Bestätigung vor Speichern („Abteilung für X Mitarbeiter auf ‚Fahrzeuge‘ setzen?“).  
   - Optional: **Audit-Log** (wer hat wann welche Abteilung für wen geändert).  
   - Optional: Feste Liste „erlaubte Abteilungen“ (Whitelist), um Tippfehler zu vermeiden – dann „Fahrzeuge“ einmal anlegen und nur aus Liste wählbar.

Wenn **Option B** gewählt wird:

5. **Backend:**  
   - Neuer Aufruf im LDAP-Connector, z. B. `update_user_department(ldap_username: str, department: str) -> (bool, Optional[str])`.  
   - Implementierung: LDAP MODIFY am User-Objekt (DN aus Suche nach `sAMAccountName`), Attribut `department` ersetzen.  
   - Nur ausführen, wenn der Service-Account verbunden ist und Schreibrechte hat; bei Fehler (z. B. 50 „Insufficient Rights“) klare Meldung und nur Portal-Update durchführen bzw. Meldung „AD-Update fehlgeschlagen, bitte IT kontaktieren“.

---

## 4. Technische Kurzfassung

| Thema | Inhalt |
|-------|--------|
| **AD-Struktur** | `department` = User-Attribut (String), kein separates „Abteilungs-Objekt“. „Fahrzeuge anlegen“ = bei Usern `department = "Fahrzeuge"` setzen. |
| **Portal heute** | Organigramm liest `employees.department_name` (aus Sync von AD oder manuell). |
| **Sicherer Weg** | Tool nur für berechtigte Rollen; Abteilung optional als Whitelist; Bestätigung + optional Audit; bei Option B: AD-Update nur mit klarer Fehlerbehandlung. |
| **Nächster Schritt** | Entscheidung: Option A (nur Portal) oder Option B (Portal + AD). Bei B: AD-Rechte für `department` für Service-Account prüfen/anlegen, danach LDAP-Connector erweitern und Admin-UI bauen. |

---

## 5. Für Vanessa / Herr Greiner

- **Abteilung „Fahrzeuge“:** Wird im AD nicht als eigener Ordner angelegt, sondern als **Wert** beim jeweiligen Benutzer (Feld „Abteilung“). Den können wir z. B. in einem Admin-Tool setzen – entweder nur im Portal (Option A) oder direkt im AD (Option B), wenn die Rechte dafür da sind.
- **Sicher:** Nur bestimmte Rollen (z. B. Admin/HR) können das Tool nutzen; Änderungen können protokolliert und mit Bestätigung versehen werden.
- **An der richtigen Stelle:** Im AD ist die „richtige Stelle“ das Benutzerattribut `department`; in der Oberfläche wäre die „richtige Stelle“ ein eigener Bereich unter Admin (oder Rechteverwaltung), in dem Abteilungen angelegt und Mitarbeiter zugewiesen werden.

Wenn ihr euch für Option A oder B entschieden habt, kann die konkrete Implementierung (Routen, API, LDAP-Methode, Template) darauf aufbauen.
