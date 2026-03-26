# Masterplan Entwicklung - DRIVE steuert Prozesse, Locosoft als Fallback (Wildmosers + Greiner)

**Version:** 1.0  
**Datum:** 2026-03-23  
**Zielbild:** DRIVE ist prozessfuehrend fuer Termin, Auftrag, Werkstatt-Dispo, Teile-Dispo und Mietwagen. Locosoft bleibt ERP/Fallback und wird aus DRIVE heraus befuellt.

---

## 1) Scope und Zielprozesse

### In Scope (MVP + Rollout)
- Terminanlage, Terminverschiebung, Terminabsage
- Auftragseroeffnung und Auftragsstatus
- Werkstatt-Disposition (Ressourcen-/Slot-Zuweisung)
- Teile-Disposition (Bedarf, Verfuegbarkeit, Bestellung, ETA)
- Mietwagen-Disposition (Reservierung, Uebergabe, Ruecknahme, Verlaengerung)
- Rueckschreiben in Locosoft als Fallback-/Spiegelsystem

### Out of Scope (Phase spaeter)
- Vollstaendige Faktura-Logik in DRIVE
- Kompletter Ersatz aller Spezialmasken in Locosoft

---

## 2) Architekturprinzipien (verbindlich)

- **DRIVE-first UI:** Alle Fachanwender arbeiten primaer in DRIVE.
- **Locosoft-write-back:** Jede kritische Aktion wird in Locosoft gespiegelt.
- **Idempotenz:** Keine Doppelbuchungen bei Retry oder Timeout.
- **Asynchrones Sync-Modell:** UI schnell halten, Sync robust ueber Queue/Worker.
- **Transparenz:** Jeder Sync-Status ist sichtbar (`PENDING_SYNC`, `SYNCED`, `SYNC_FAILED`).
- **Auditierbarkeit:** Jede Aktion hat Correlation-ID und Event-Historie.

---

## 3) Technisches Kernmodell

## 3.1 Integrationsmodule
- `LocosoftWriteService` (zentraler Adapter fuer Termin/Auftrag/Dispo/Teile/Mietwagen)
- `SyncOutbox` (persistente Event-Queue in drive_portal)
- `SyncWorker` (Celery, Retry mit Backoff, Dead-Letter)
- `ReconciliationService` (Abgleich DRIVE vs Locosoft)

## 3.2 Standard-Ablauf je Schreibvorgang
1. Benutzer fuehrt Aktion in DRIVE aus.
2. DRIVE speichert Fachzustand lokal + Outbox-Event.
3. Worker schreibt nach Locosoft.
4. Ergebnis wird rueckgespiegelt:
   - Erfolg -> `SYNCED`
   - Fehler -> `SYNC_FAILED` + Fehlercode + Retry-Strategie
5. Reconciliation prueft taeglich Konsistenz.

---

## 4) Phasenplan

## Phase 0 - Discovery und Freigaben (1-2 Wochen)
- Prozessworkshops mit Wildmosers (Ist/Soll je Prozess)
- Feldmapping DRIVE <-> Locosoft finalisieren
- Write-Endpunkte/Mechanismen pro Prozess validieren
- Testdaten und Pilotstandort festlegen

**Deliverables**
- Integrationsmatrix je Prozess
- Feldmapping-Dokument (SSOT)
- Risiko- und Fallback-Konzept

## Phase 1 - Integrationskern (2-4 Wochen)
- Outbox-Tabellen und Sync-Status im Backend
- Zentraler `LocosoftWriteService`
- Basis-Retry, Fehlerklassifikation, Audit-Log
- Monitoring-Ansicht "Sync Gesundheit"

**Abnahme**
- Mindestens 95 Prozent Sync-Erfolg in Test
- Kein Datenverlust bei simuliertem Locosoft-Ausfall

## Phase 2 - Prozessmodule (4-6 Wochen)

### 2.1 Termin
- DRIVE Terminboard als Fuehrungsmaske
- Create/Update/Cancel -> Write-back nach Locosoft-Terminplaner
- Konfliktcheck (Doppelbelegung, Ressourcenkollision)

### 2.2 Auftrag
- Auftragsanlage aus DRIVE
- Statusfluss: neu -> geplant -> in Arbeit -> fertig -> fakturierbar
- Kernstatus in Locosoft spiegeln

### 2.3 Werkstatt-Dispo
- Dispo-Board (Mechaniker/Slots/Arbeitspakete)
- Priorisierung/Drag-and-Drop Logik
- Spiegelung relevanter Dispofelder in Locosoft

### 2.4 Teile-Dispo
- Teilebedarf aus Auftragspositionen
- Verfuegbarkeit, Reservierung, Bestellung, ETA
- Rueckmeldungen in Auftrag/Dispo integrieren

### 2.5 Mietwagen
- Reservierung aus Termin/Auftrag
- Verfuegbarkeitspruefung und Konfliktschutz
- Uebergabe, Ruecknahme, Verlaengerung, No-Show
- Synchron in Locosoft-Mietwagenmodul spiegeln

**Abnahme**
- End-to-End ohne Medienbruch fuer 5 Pilotfaelle pro Prozess

## Phase 3 - Pilot und Rollout (2-3 Wochen)
- Pilotbetrieb mit Key-Usern
- Hypercare (taegliche Reviewrunde)
- Rollout pro Bereich/Standort

**Abnahme**
- Key-User-Freigabe
- Stabile Sync-Quote > 98 Prozent im Pilot
- Keine kritischen offenen P1-Fehler

---

## 5) Daten- und Tabellenvorschlag (drive_portal)

- `integration_sync_outbox` (event_id, entity_type, action, payload, status, retries, correlation_id)
- `integration_sync_result` (event_id, target_system, success, error_code, response_meta, synced_at)
- `locosoft_entity_mapping` (drive_entity, drive_id, locosoft_id, source_of_truth)
- `dispo_resource_mapping` (drive_resource_id, locosoft_resource_ref, standort)
- `mietwagen_booking_link` (drive_booking_id, locosoft_booking_id, status)

---

## 6) Rollen und Verantwortlichkeiten

- **Greiner Produkt/Tech:** Architektur, Integrationskern, Betriebskonzept
- **Wildmosers Fachseite:** Prozessfreigabe, Fachtests, Priorisierung
- **Greiner + Wildmosers Key-User:** UAT je Prozess, KPI-Validierung
- **IT Infrastruktur:** Netzwerk, Credentials, Monitoring, Backup

---

## 7) Risiken und Gegenmassnahmen

- **Unklare Write-Moeglichkeiten in Locosoft:** Frueher API/Mechanismus-PoC je Prozess
- **Parallelpflege in zwei UIs:** Betriebsregel "DRIVE-first", Rollen absichern
- **Ueberbuchung bei Termin/Mietwagen:** Optimistisches Locking + harte Konfliktregeln
- **Sync-Stoerung:** Queue + Retry + Dead-Letter + manuelle Freigabeansicht

---

## 8) Go-Live Kriterien

- Termin, Auftrag, Werkstatt-Dispo, Teile-Dispo, Mietwagen lauffaehig im Pilot
- Fallback-Spiegelung in Locosoft im Soll
- Monitoring, Alerting und Notfallprozess aktiv
- Schulung abgeschlossen (Serviceassistenz, Dispo, Teile, Werkstattleitung)

---

## 9) Empfohlene Reihenfolge fuer Umsetzung

1. Termin  
2. Auftrag  
3. Werkstatt-Dispo  
4. Teile-Dispo  
5. Mietwagen  
6. Reconciliation-Haertung und Rollout

Diese Reihenfolge minimiert Risiko und bringt frueh sichtbaren Nutzen.

