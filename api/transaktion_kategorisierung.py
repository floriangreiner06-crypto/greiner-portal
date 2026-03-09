"""
Transaktions-Kategorisierung (Bankenspiegel)
============================================
Regelbasierte Zuordnung + optional LM Studio für Unkategorisierte.

Kategorien werden in transaktionen.kategorie und transaktionen.unterkategorie gespeichert.
Reihenfolge der Regeln: erste Übereinstimmung gewinnt.
"""

from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# REGELN (erste Übereinstimmung gewinnt; Groß-/Kleinschreibung egal)
# =============================================================================
# Jede Regel: kategorie, unterkategorie (optional), begriffe (Liste; Treffer in einem Suchfeld)
# Suchfelder: verwendungszweck, buchungstext, gegenkonto_name (werden zu einem Suchtext zusammengefügt)
# Optional: nur_bei_betrag_positiv / nur_bei_betrag_negativ (Regel nur anwenden wenn Betrag passt)
# =============================================================================

TRANSAKTION_KATEGORIEN_REGELN = [
    # --- Intern (Umbuchungen etc.) ---
    {"kategorie": "Intern", "unterkategorie": "Umbuchung", "begriffe": ["Autohaus Greiner", "Umbuchung", "Einlage", "Rückzahlung Einlage"]},
    # --- Einkaufsfinanzierung (Tilgungen Autobanken) ---
    {"kategorie": "Einkaufsfinanzierung", "unterkategorie": "Stellantis", "begriffe": ["Stellantis", "Banque PSA", "PSA Bank"]},
    {"kategorie": "Einkaufsfinanzierung", "unterkategorie": "Santander", "begriffe": ["Santander", "Santander Consumer", "Tilgung Santander", "SANTANDER CONSUMER"]},
    {"kategorie": "Einkaufsfinanzierung", "unterkategorie": "Hyundai", "begriffe": ["Hyundai Finance", "Hyundai Motor Finance", "HMF", "Hyundai Capital", "Hyundai Capital Bank"]},
    {"kategorie": "Einkaufsfinanzierung", "unterkategorie": "Leasys", "begriffe": ["Leasys", "FCA Bank"]},
    {"kategorie": "Einkaufsfinanzierung", "unterkategorie": "Sonstige", "begriffe": ["Einkaufsfinanzierung", "Fahrzeugfinanzierung", "Händlerdarlehen", "Tilgung"]},
    # --- Gehalt / Personal ---
    {"kategorie": "Personal", "unterkategorie": "Gehalt", "begriffe": ["Gehalt", "Lohn", "Vergütung", "Lohnabrechnung", "Entgelt"]},
    {"kategorie": "Personal", "unterkategorie": "Sozialversicherung", "begriffe": ["Sozialversicherung", "Rentenversicherung", "Krankenkasse", "Arbeitsagentur", "Bundesagentur"]},
    {"kategorie": "Personal", "unterkategorie": "Steuer", "begriffe": ["Lohnsteuer", "LSt ", "SV-Beitrag"]},
    # --- Miete / Nebenkosten ---
    {"kategorie": "Miete & Nebenkosten", "unterkategorie": "Miete", "begriffe": ["Miete", "Mietzahlung", "Kaltmiete", "Warmmiete"]},
    {"kategorie": "Miete & Nebenkosten", "unterkategorie": "Nebenkosten", "begriffe": ["Nebenkosten", "Heizkosten", "Strom", "Stadtwerke", "Energie", "Gas "]},
    # --- Versicherung ---
    {"kategorie": "Versicherung", "unterkategorie": None, "begriffe": ["Versicherung", "Allianz", "Huk", "HUK", "AXA", "Zurich", "Provinzial", "Gothaer"]},
    # --- Steuern (ohne Lohnsteuer) ---
    {"kategorie": "Steuern", "unterkategorie": "Umsatzsteuer", "begriffe": ["Umsatzsteuer", "USt-Voranmeldung", "Finanzamt"]},
    {"kategorie": "Steuern", "unterkategorie": "Gewerbesteuer", "begriffe": ["Gewerbesteuer", "GewSt"]},
    {"kategorie": "Steuern", "unterkategorie": "Sonstige", "begriffe": ["Steuer", "FA ", "Finanzamt"]},
    # --- Kraftstoff / Energie (Betrieb) ---
    {"kategorie": "Betrieb", "unterkategorie": "Kraftstoff", "begriffe": ["Tankstelle", "Aral", "Shell", "Total ", "Esso", "Jet ", "Raiffeisen Tank"]},
    # --- Werbung / Marketing (Betrieb) ---
    {"kategorie": "Betrieb", "unterkategorie": "Werbung", "begriffe": ["Werbekostenbeitrag", "Werbekosten", "KS Partner-System", "KS Partner System"]},
    # --- Porto / Versand (Betrieb) ---
    {"kategorie": "Betrieb", "unterkategorie": "Versand", "begriffe": ["Deutsche Post", "POSTCARD", "Postcard", "DHL", "Porto", "Briefmarke"]},
    # --- Bank / Zinsen ---
    {"kategorie": "Bank & Zinsen", "unterkategorie": "Zinsen", "begriffe": ["Zinsen", "Sollzins", "Habenzins", "Kontoführung"]},
    {"kategorie": "Bank & Zinsen", "unterkategorie": "Gebühren", "begriffe": ["Kontogebühr", "Entgelt", "Bereitstellungsprovision"]},
    # --- Lieferanten / Verbindlichkeiten (nur Ausgaben) ---
    {"kategorie": "Lieferanten", "unterkategorie": "Fahrzeuge", "begriffe": ["Stellantis", "Opel", "Hyundai Motor", "Leapmotor", "Fahrzeuglieferung"]},
    {"kategorie": "Lieferanten", "unterkategorie": "Teile", "begriffe": ["Mobis", "MOBIS", "Teile", "Ersatzteil"]},
    {"kategorie": "Lieferanten", "unterkategorie": "Sonstige", "begriffe": ["PayPal", "Einkauf bei", "RE ", "Lieferant"], "nur_bei_betrag_negativ": True},
    {"kategorie": "Lieferanten", "unterkategorie": "Sonstige", "begriffe": ["Rechnung"], "nur_bei_betrag_negativ": True},
    # --- Einnahmen: Kunden (Rechnung bei Einnahmen = Zahlungseingang) ---
    {"kategorie": "Einnahmen", "unterkategorie": "Kunden", "begriffe": ["Überweisung", "Kunde", "Zahlungseingang"]},
    {"kategorie": "Einnahmen", "unterkategorie": "Sonstige", "begriffe": ["Rechnung"], "nur_bei_betrag_positiv": True},
    # --- Sonstige (Fallback für Ausgaben) ---
    {"kategorie": "Sonstige Ausgaben", "unterkategorie": None, "begriffe": []},  # wird nur bei betrag < 0 und kein Treffer gesetzt
    # --- Sonstige Einnahmen ---
    {"kategorie": "Sonstige Einnahmen", "unterkategorie": None, "begriffe": []},  # betrag > 0 und kein Treffer
]


def _suchtext(verwendungszweck: Optional[str], buchungstext: Optional[str], gegenkonto_name: Optional[str]) -> str:
    """Baut einen einheitlichen Suchtext aus den Transaktionsfeldern."""
    parts = [
        (verwendungszweck or "").strip(),
        (buchungstext or "").strip(),
        (gegenkonto_name or "").strip(),
    ]
    return " ".join(p for p in parts if p).lower()


def apply_rules(
    verwendungszweck: Optional[str] = None,
    buchungstext: Optional[str] = None,
    gegenkonto_name: Optional[str] = None,
    betrag: Optional[float] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Wendet die regelbasierte Kategorisierung an.

    Returns:
        (kategorie, unterkategorie) oder (None, None) wenn keine Regel passt.
    """
    text = _suchtext(verwendungszweck, buchungstext, gegenkonto_name)
    if not text and not any(b for r in TRANSAKTION_KATEGORIEN_REGELN for b in r["begriffe"]):
        # Nur Sonstige-Regeln haben leere begriffe
        if betrag is not None:
            if betrag < 0:
                return ("Sonstige Ausgaben", None)
            if betrag > 0:
                return ("Sonstige Einnahmen", None)
        return (None, None)

    for regel in TRANSAKTION_KATEGORIEN_REGELN:
        # Optional: Regel nur bei positivem oder negativem Betrag
        if regel.get("nur_bei_betrag_positiv"):
            if betrag is None or betrag <= 0:
                continue
        if regel.get("nur_bei_betrag_negativ"):
            if betrag is None or betrag >= 0:
                continue

        begriffe = regel.get("begriffe") or []
        if not begriffe:
            # Sonstige-Regel: nur anwenden wenn betrag bekannt
            if betrag is not None:
                if regel["kategorie"] == "Sonstige Ausgaben" and betrag < 0:
                    return (regel["kategorie"], regel["unterkategorie"])
                if regel["kategorie"] == "Sonstige Einnahmen" and betrag > 0:
                    return (regel["kategorie"], regel["unterkategorie"])
            continue
        for begriff in begriffe:
            if begriff.lower() in text:
                return (regel["kategorie"], regel["unterkategorie"])

    # Kein Treffer -> nach Vorzeichen
    if betrag is not None:
        if betrag < 0:
            return ("Sonstige Ausgaben", None)
        if betrag > 0:
            return ("Sonstige Einnahmen", None)
    return (None, None)


def get_kategorien_liste() -> List[Dict[str, Any]]:
    """Gibt die Liste der verwendeten Kategorien/Unterkategorien aus den Regeln zurück (für API/Dashboard)."""
    seen = set()
    out = []
    for r in TRANSAKTION_KATEGORIEN_REGELN:
        k = r["kategorie"]
        u = r.get("unterkategorie")
        key = (k, u)
        if key not in seen and k not in ("Sonstige Ausgaben", "Sonstige Einnahmen"):
            seen.add(key)
            out.append({"kategorie": k, "unterkategorie": u})
    out.append({"kategorie": "Sonstige Ausgaben", "unterkategorie": None})
    out.append({"kategorie": "Sonstige Einnahmen", "unterkategorie": None})
    return out


def kategorisiere_transaktion_in_db(
    conn,
    trans_id: int,
    kategorie: Optional[str] = None,
    unterkategorie: Optional[str] = None,
    overwrite: bool = False,
) -> bool:
    """
    Setzt Kategorie für eine Transaktion in der DB (per Regel oder explizit).

    Wenn kategorie/unterkategorie None sind, werden die Regeln auf die bestehende Zeile angewendet.
    overwrite=True überschreibt auch bestehende Kategorie.
    """
    from api.db_connection import sql_placeholder, convert_placeholders

    ph = sql_placeholder()
    cursor = conn.cursor()

    # Explizit gesetzt (manuell oder KI-Vorschlag) – immer verwenden wenn übergeben, auch bei overwrite=True
    if kategorie is not None:
        cursor.execute(
            convert_placeholders("""
                UPDATE transaktionen SET kategorie = """ + ph + """, unterkategorie = """ + ph + """
                WHERE id = """ + ph
            ),
            (kategorie, unterkategorie, trans_id),
        )
        return cursor.rowcount > 0

    # Aus DB lesen und Regeln anwenden (nur wenn keine explizite Kategorie übergeben wurde)
    cursor.execute(
        convert_placeholders("""
            SELECT id, verwendungszweck, buchungstext, gegenkonto_name, betrag, kategorie
            FROM transaktionen WHERE id = """ + ph
        ),
        (trans_id,),
    )
    row = cursor.fetchone()
    if not row:
        return False

    # HybridRow oder dict
    vw = row.get("verwendungszweck") if hasattr(row, "get") else (row[1] if len(row) > 1 else None)
    bt = row.get("buchungstext") if hasattr(row, "get") else (row[2] if len(row) > 2 else None)
    gk = row.get("gegenkonto_name") if hasattr(row, "get") else (row[3] if len(row) > 3 else None)
    betrag = row.get("betrag") if hasattr(row, "get") else (row[4] if len(row) > 4 else None)
    bestehend = row.get("kategorie") if hasattr(row, "get") else (row[5] if len(row) > 5 else None)

    if not overwrite and bestehend:
        return True  # bereits kategorisiert, nichts tun

    kat, unterkat = apply_rules(verwendungszweck=vw, buchungstext=bt, gegenkonto_name=gk, betrag=betrag)
    if kat is None:
        return False

    cursor.execute(
        convert_placeholders("""
            UPDATE transaktionen SET kategorie = """ + ph + """, unterkategorie = """ + ph + """
            WHERE id = """ + ph
        ),
        (kat, unterkat, trans_id),
    )
    return cursor.rowcount > 0


def kategorisiere_batch(
    conn,
    limit: int = 500,
    nur_unkategorisiert: bool = True,
    overwrite: bool = False,
    nur_sonstige_ausgaben: bool = False,
) -> Dict[str, Any]:
    """
    Kategorisiert mehrere Transaktionen per Regeln.

    Bei nur_sonstige_ausgaben=True: nur Zeilen mit kategorie = 'Sonstige Ausgaben' laden
    und mit overwrite=True neu prüfen (z. B. nach erweiterten Regeln).

    Returns:
        { "aktualisiert": int, "übersprungen": int, "fehler": int, "beispiele": [...] }
    """
    from api.db_connection import sql_placeholder, convert_placeholders

    ph = sql_placeholder()
    cursor = conn.cursor()

    if nur_sonstige_ausgaben:
        where = " AND kategorie = 'Sonstige Ausgaben'"
        overwrite = True
    else:
        where = " AND (kategorie IS NULL OR kategorie = '')" if nur_unkategorisiert else ""
    cursor.execute(
        convert_placeholders("""
            SELECT id, verwendungszweck, buchungstext, gegenkonto_name, betrag
            FROM transaktionen
            WHERE 1=1 """ + where + """
            ORDER BY buchungsdatum DESC, id DESC
            LIMIT """ + str(int(limit))
        ),
    )
    rows = cursor.fetchall()

    aktualisiert = 0
    uebersprungen = 0
    fehler = 0
    beispiele = []

    for row in rows:
        rid = row.get("id") if hasattr(row, "get") else row[0]
        vw = row.get("verwendungszweck") if hasattr(row, "get") else (row[1] if len(row) > 1 else None)
        bt = row.get("buchungstext") if hasattr(row, "get") else (row[2] if len(row) > 2 else None)
        gk = row.get("gegenkonto_name") if hasattr(row, "get") else (row[3] if len(row) > 3 else None)
        betrag = row.get("betrag") if hasattr(row, "get") else (row[4] if len(row) > 4 else None)

        kat, unterkat = apply_rules(verwendungszweck=vw, buchungstext=bt, gegenkonto_name=gk, betrag=betrag)
        if kat is None:
            uebersprungen += 1
            continue
        try:
            cursor.execute(
                convert_placeholders("""
                    UPDATE transaktionen SET kategorie = """ + ph + """, unterkategorie = """ + ph + """
                    WHERE id = """ + ph
                ),
                (kat, unterkat, rid),
            )
            if cursor.rowcount > 0:
                aktualisiert += 1
                if len(beispiele) < 5:
                    beispiele.append({"id": rid, "kategorie": kat, "unterkategorie": unterkat})
        except Exception as e:
            logger.warning("Kategorisierung Transaktion %s: %s", rid, e)
            fehler += 1

    try:
        conn.commit()
    except Exception:
        pass

    return {
        "aktualisiert": aktualisiert,
        "uebersprungen": uebersprungen,
        "fehler": fehler,
        "beispiele": beispiele,
    }
