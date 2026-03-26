# Einschätzung: Genehmiger-Logik vereinfachen – „alles unter einen Hut“

**Stand:** 2026-02  
**Kontext:** Margit kann Susannes Urlaub weiterhin nicht genehmigen; mehrere konfigurierbare Ebenen (LDAP, Organigramm, Vertretungen, Abteilungen) wirken vermeintlich zusammen, die tatsächliche Nutzung im Code ist uneinheitlich.

---

## 1. Wo wirkt was? (Ist-Zustand)

| Quelle / UI | Inhalt | Wo im Code genutzt? |
|-------------|--------|----------------------|
| **AD/LDAP** | Gruppen wie `GRP_Urlaub_Genehmiger_Disposition`; Manager-Hierarchie (manager-Attribut) | `vacation_approver_service`: `is_approver()`, `get_approvers_for_employee()`, `get_team_for_approver()` (AD-Manager + Abteilung aus Gruppen-Suffix) |
| **Organigramm → Tab „Genehmiger“** | Tabelle **vacation_approval_rules**: Gruppe (loco_grp_code), Standort, Genehmiger (LDAP), Prio | **Chef-Übersicht** (vacation_chef_api) – Anzeige „wer hat welche Gruppe“. **Nicht** für pending-approvals / approve / E-Mail-Empfänger. |
| **Organigramm → Tab „Vertretungen“** | Tabelle **substitution_rules**: Wer vertritt wen (Abwesenheit) | Urlaubsplaner: Konfliktprüfung „Vertreter darf nicht an denselben Tagen Urlaub haben wie Vertretener“. Kein Einfluss darauf, **wer** genehmigen darf. |
| **Organigramm → Abteilungen / Hierarchie** | Abteilungszuordnung, ggf. Manager | Nicht direkt für Urlaub-Genehmiger; AD-Manager ist die einzige Hierarchie-Quelle für „wer genehmigt wen“. |

Kernproblem: **Zwei getrennte „Wahrheiten“**

- **Genehmiger-Portal-Seite (Organigramm)** schreibt und liest **vacation_approval_rules** („Gruppe Disposition → Margit, Prio 1“).
- **Urlaubsplaner (pending, approve, E-Mails)** nutzt **nur** `vacation_approver_service` = **AD-Manager + LDAP-Gruppen**, liest **vacation_approval_rules nicht**.

Folge: Was in der Genehmiger-UI konfiguriert wird, steuert die Chef-Übersicht (Anzeige), aber **nicht**, wer im Urlaubsplaner „Zu genehmigen“ sieht und wer tatsächlich genehmigen darf. Das erklärt, warum Margit in der einen Ansicht als Genehmiger für Disposition steht, im Urlaubsplaner aber 0 Anträge sieht bzw. 401/403 beim Genehmigen bekommt.

**Warum 401/403 bei Margit konkret?** Der approve-Endpoint prüft: `booking_employee_id in team_ids`, wobei `team_ids` aus `get_team_for_approver(Margit)` kommt (AD-Reports + alle mit `department_name = "Disposition"`). Wenn Susannes `employees.department_name` nicht exakt „Disposition“ ist (z. B. „DIS“, Leerzeichen, anderer Locosoft-Code), ist sie nicht in `team_ids` → 403. Die Regeln aus dem Organigramm (Disposition → Margit) werden bei dieser Prüfung **gar nicht** gelesen.

---

## 2. Warum ist es so komplex?

- **Historisch gewachsen:** Zuerst AD + Gruppen; später Organigramm mit vacation_approval_rules und Chef-Übersicht dazu gebaut, ohne die bestehende Genehmiger-/Approval-Logik auf diese Regeln umzustellen.
- **Zwei Konzepte vermischt:**
  - **„Wer darf generell Anträge genehmigen?“** → aktuell: LDAP-Gruppen (`GRP_Urlaub_Genehmiger_*`, Admin).
  - **„Für wen ist Person X Genehmiger?“** → aktuell: AD-Manager („direkte Reports“) + heuristisch „alle aus Abteilung wie im Gruppen-Suffix“ (z. B. Disposition). Die **expliziten** Regeln aus vacation_approval_rules werden dabei **nicht** gelesen.
- **Viele Stellen:** E-Mails (`get_approvers_for_employee`), pending-approvals und approve (`get_team_for_approver`), Chef-Übersicht (vacation_approval_rules), Vertretungen (substitution_rules) – alles nebeneinander, ohne eine einzige „Genehmiger für Mitarbeiter X“-SSOT.

---

## 3. Vorschlag: Eine Quelle, eine Logik

### Option A: **vacation_approval_rules als SSOT (empfohlen)**

- **Regel:** „Wer darf was genehmigen?“ und „Für wen ist wer Genehmiger?“ kommen **nur noch** aus **vacation_approval_rules** (das, was im Organigramm unter „Genehmiger“ gepflegt wird).
- **Konkret:**
  - **Team eines Genehmigers** = alle Mitarbeiter, deren Abteilung/Standort zu einer Regel mit diesem Genehmiger passen (bereits in vacation_chef_api ähnlich umgesetzt: Gruppe + Standort → Mitarbeiter).
  - **pending-approvals** und **approve** nutzen diese Team-Definition statt `get_team_for_approver()` (AD + Gruppen-Suffix).
  - **E-Mail „Antrag eingereicht“** Empfänger = Genehmiger aus den Regeln, die auf den Mitarbeiter zutreffen (statt nur aus `get_approvers_for_employee()` mit AD-Manager).
- **LDAP/AD:** Nur noch für **Login / Identität** und ggf. „ist User überhaupt in einer Rolle, die irgendwo als Genehmiger vorkommt?“ (Performance/Optimierung). Nicht mehr für die **fachliche** Zuordnung „Genehmiger für Abteilung X“.

**Vorteile:** Eine Konfigurationsstelle (Organigramm → Genehmiger). Was dort steht, gilt auch im Urlaubsplaner. Weniger Überraschungen, weniger „im Kreis drehen“.

**Aufwand:** Mittel. vacation_approver_service (oder ein neues Modul) liest vacation_approval_rules; get_team_for_approver und die Stelle „wer sind die Genehmiger für employee_id?“ werden auf diese Quelle umgestellt; AD-Manager-Logik und Gruppen-Suffix-Heuristik können schrittweise entfernt oder nur noch als Fallback (z. B. wenn keine Regel existiert) genutzt werden.

---

### Option B: **AD + Gruppen als SSOT, Organigramm nur Anzeige**

- Alle fachlichen Entscheidungen bleiben bei AD (Manager + `GRP_Urlaub_Genehmiger_*`).
- vacation_approval_rules und Chef-Übersicht werden **nur noch Anzeige** („so ungefähr sieht es in AD aus“) oder werden abgeschaltet; Konfiguration von „Wer genehmigt für Disposition?“ erfolgt nur noch über AD (Gruppen + Manager).

**Vorteile:** Keine zweite Konfiguration; eine Quelle (AD).  
**Nachteile:** Änderungen nur über AD/IT; Organigramm-Genehmiger-Tab wird irreführend, wenn er nicht die echte Logik abbildet. Passt schlecht zu „wir wollen Komplexität raus und eine klare Hut-Logik“.

---

### Option C: **Hybrid mit klarer Priorität**

- **Primär:** vacation_approval_rules (Organigramm). Wenn für Abteilung/Standort ein Genehmiger eingetragen ist, gilt nur der.
- **Fallback:** Wenn **keine** Regel existiert (z. B. neue Abteilung), einmalig AD-Manager + Gruppen nutzen, bis Regeln gepflegt sind.

**Vorteile:** Eine Hauptquelle, trotzdem robust bei fehlenden Regeln.  
**Nachteile:** Noch zwei Wege im Code; Fallback muss klar dokumentiert und getestet werden.

---

## 4. Empfehlung und nächste Schritte

- **Empfehlung:** **Option A** – vacation_approval_rules als **einzige** fachliche Quelle für „Wer genehmigt für wen?“ nutzen und Urlaubsplaner (pending, approve, E-Mails) sowie Chef-Übersicht darauf ausrichten. LDAP nur noch für Identität und ggf. grobe Rolle.
- **Komplexitätsabbau im Code:**
  - Eine zentrale Funktion(en), z. B. `get_approvers_for_employee(employee_id)` und `get_team_for_approver(ldap_username)`, die **nur** aus vacation_approval_rules (+ employees Abteilung/Standort) ableiten.
  - vacation_approver_service von AD-Manager und Gruppen-Suffix-Logik entlasten oder entfernen.
  - Keine doppelte „Team“-Definition mehr (einmal AD + Suffix, einmal Regeln).
- **Vertretungen** bewusst getrennt lassen: substitution_rules = „wer vertritt wen in Abwesenheit“, **nicht** „wer genehmigt“. Dann bleibt die Regel einfach: Genehmiger = nur vacation_approval_rules (bzw. eine daraus abgeleitete SSOT).

Wenn du dich für Option A entscheidest, kann als nächster Schritt ein kurzer **Umsetzungsplan** (welche APIs/Stellen umgestellt werden, Migration/Feature-Flag) erstellt werden – weiterhin ohne sofortigen Code, bis du die Richtung bestätigst.
