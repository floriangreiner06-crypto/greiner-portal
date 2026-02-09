# Locosoft-Adressbuch-Anbindung

**TAG 211** – PostgreSQL-Kundendaten aus Locosoft als Adressbuch (z. B. für WhatsApp „Neuer Chat“).

---

## Übersicht

- **Read-only:** Es werden nur Lesezugriffe auf die Locosoft-Datenbank ausgeführt.
- **Quellen:** `customers_suppliers` (Stammdaten, Adresse) + `customer_com_numbers` (Telefon, E-Mail).
- **Nur Kunden:** Es werden nur Einträge mit `is_supplier = false` berücksichtigt.

---

## API

- **Modul:** `api/locosoft_addressbook_api.py`
- **Funktion:** `search_customers(q="", subsidiary=None, limit=100)`  
  Gibt eine Liste von Dicts zurück: `customer_number`, `display_name`, `first_name`, `family_name`, `phone`, `email`, `home_street`, `zip_code`, `home_city`, `subsidiary`.

**HTTP-Route (WhatsApp Verkauf):**

- `GET /whatsapp/verkauf/locosoft-addressbook?q=...&subsidiary=...&limit=50`
- Zugriff nur mit Berechtigung `whatsapp_verkauf`.
- Parameter:
  - `q`: Suchbegriff (Name, Kundennummer); optional.
  - `subsidiary`: Locosoft-Standort (1=DEG Opel, 2=HYU, 3=LAN); optional.
  - `limit`: Max. Treffer (Standard 50, max. 100).

---

## Nutzung im Portal

**Verkauf → WhatsApp Chat → Neuer Chat:**

- Bereich **„Aus Locosoft wählen“**: Suchfeld + Button **Suchen**.
- Trefferliste: Kunde anklicken → Telefonnummer und Name werden in die Felder **Telefonnummer** und **Name** übernommen.
- Danach wie gewohnt **Chat starten** oder **Senden**.

---

## Locosoft-Verbindung

- Verbindung wie im restlichen Portal über `api/db_utils.py` → `locosoft_session()` / `get_locosoft_connection()`.
- Konfiguration: `config/credentials.json` (Abschnitt `locosoft_postgresql`) bzw. Fallback auf Umgebungsvariablen (Host 10.80.80.8, DB `loco_auswertung_db`, User `loco_auswertung_benutzer`).

---

## Erweiterungen (optional)

- **Standort-Filter** im Modal (Dropdown „Standort“ vor der Locosoft-Suche).
- **Eigenes Menü „Adressbuch“** mit reiner Locosoft-Suche (ohne WhatsApp).
- **Sync in DRIVE-PostgreSQL:** periodischer Abgleich aus Locosoft in eine lokale Tabelle für schnellere Suche (bei Bedarf).
