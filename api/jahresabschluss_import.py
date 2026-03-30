"""
Jahresabschluss PDF-Import
===========================
Erstellt: 2026-03-30 | Workstream: Controlling / Ertragsvorschau

Parst RAW-Partner Jahresabschluss-PDFs und importiert Kennzahlen
in die Tabelle jahresabschluss_daten.

Quellpfad: /mnt/buchhaltung/Buchhaltung/Jahresabschlussunterlagen/
           Abschluss {YYYY} {YYYY+1}/Abschlüsse RAW/
           Autohaus Greiner GmbH & Co. KG JA {YYYY+1} signiert.pdf

Schlüsselseiten im PDF:
  - Mehrjahresvergleich (enthält Bilanz + GuV + Cashflow als Tabellen)
  - Ertragslage (detaillierte GuV)
"""

import os
import re
import logging
from datetime import date
from typing import Optional

import pdfplumber

logger = logging.getLogger('jahresabschluss_import')

BUCHHALTUNG_PFAD = '/mnt/buchhaltung/Buchhaltung/Jahresabschlussunterlagen'


def _parse_german_number(text: str) -> Optional[float]:
    """Parst deutsches Zahlenformat: '1.234,5' → 1234.5, '-278,8' → -278.8"""
    if not text or text.strip() in ('', '-', '--', 'Negativ'):
        return None
    text = text.strip()
    negativ = text.startswith('-')
    text = text.lstrip('-').strip()
    # Tausender-Punkte entfernen, Dezimalkomma zu Punkt
    text = text.replace('.', '').replace(',', '.')
    try:
        val = float(text)
        return -val if negativ else val
    except ValueError:
        return None


def _finde_mehrjahresvergleich_seite(pdf) -> Optional[int]:
    """Findet die Seite mit dem Mehrjahresvergleich (enthält 'Bilanzstichtag' + 'Bilanzsumme')."""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ''
        if 'Bilanzsumme' in text and 'Eigenkapital' in text and ('Bilanzstichtag' in text or 'Mehrjahresvergleich' in text):
            return i
    return None


def _finde_ertragslage_seite(pdf) -> Optional[int]:
    """Findet die Seite mit der Ertragslage (enthält 'Betriebsergebnis' + 'Umsatzerlöse')."""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ''
        if 'Betriebsergebnis' in text and 'Umsatzerlöse' in text and 'Ertragslage' in text:
            return i
    return None


def _extrahiere_mehrjahresvergleich(page) -> dict:
    """Extrahiert Bilanz- und GuV-Kennzahlen aus der Mehrjahresvergleich-Seite.

    Die Seite enthält 2 Tabellen:
    1. Bilanzstichtag-Tabelle: Bilanzsumme, AV, UV, EK, EK-Quote, Rückstellungen, Verbindlichkeiten
    2. Geschäftsjahr-Tabelle: Umsatz, Rohertrag, Personal, AfA, Investitionen, Zinsergebnis, Jahresergebnis, Cashflow

    Wir extrahieren jeweils die aktuellste Spalte (= erstes GJ / erster Stichtag).

    Hinweis: Manche Zeilen werden im PDF über 2-3 Zeilen umgebrochen (z.B. "Jahresergebnis" /
    "(vor Ergebnisübernahme) TEUR -193,2 ..."). Das Parsing verwendet daher Look-ahead.
    """
    text = page.extract_text() or ''
    lines = text.split('\n')

    result = {}

    # Zustandsvariable: welches Feld sucht noch seinen Wert auf der nächsten Zeile?
    pending_feld = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        parts = stripped.split()

        # --- Prüfe ob diese Zeile den ausstehenden Wert für ein pending_feld liefert ---
        if pending_feld and 'TEUR' in stripped:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result[pending_feld] = vals[0]
            pending_feld = None
            continue
        elif pending_feld and ('v.H.' in stripped or 'v.H' in stripped):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result[pending_feld] = vals[0]
            pending_feld = None
            continue
        elif pending_feld:
            # Zeile liefert noch keinen Wert (weiterer Umbruch) – weiter warten
            # Aber nur bis zu 3 Zeilen ahead; bei neuer Sektion abbrechen
            pass

        if len(parts) < 1:
            continue

        # Bilanz-Kennzahlen (direkt in einer Zeile: "Label TEUR wert1 wert2 ...")
        if stripped.startswith('Bilanzsumme') and 'TEUR' in stripped:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['bilanzsumme'] = vals[0]
            pending_feld = None
        elif stripped.startswith('Anlagevermögen') and 'TEUR' in stripped and 'bilanzsumme' in result:
            # Nur die Bilanz-Zeile (kommt nach Bilanzsumme), nicht die Abschreibungen-Folgezeile
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['anlagevermoegen'] = vals[0]
            pending_feld = None
        elif stripped.startswith('Umlaufvermögen') and 'TEUR' in stripped:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['umlaufvermoegen'] = vals[0]
            pending_feld = None
        elif stripped.startswith('Eigenkapital') and 'TEUR' in stripped and 'quote' not in stripped.lower() and 'rentab' not in stripped.lower():
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['eigenkapital'] = vals[0]
            pending_feld = None
        elif stripped.startswith('Eigenkapitalquote'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['ek_quote'] = vals[0]
            pending_feld = None
        elif stripped.startswith('Rückstellungen') and 'TEUR' in stripped:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['rueckstellungen'] = vals[0]
            pending_feld = None
        elif stripped.startswith('Verbindlichkeiten') and 'TEUR' in stripped:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['verbindlichkeiten'] = vals[0]
            pending_feld = None

        # GuV-Kennzahlen
        elif stripped.startswith('Umsatz') and 'TEUR' in stripped and 'rentab' not in stripped.lower():
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['umsatz'] = vals[0]
            pending_feld = None
        elif stripped.startswith('Rohertrag'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['rohertrag_pct'] = vals[0]
            pending_feld = None
        elif stripped.startswith('Personalaufwand'):
            if 'TEUR' in stripped:
                vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
                if vals:
                    result['personalaufwand'] = vals[0]
                pending_feld = None
            else:
                # Wert kommt auf Folgezeile
                pending_feld = 'personalaufwand'
        elif stripped.startswith('Abschreibungen'):
            if 'TEUR' in stripped:
                vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
                if vals:
                    result['abschreibungen'] = vals[0]
                pending_feld = None
            else:
                # Wert kommt auf Folgezeile (z.B. "Anlagevermögen TEUR 117,4 ...")
                pending_feld = 'abschreibungen'
        elif stripped.startswith('Investitionen'):
            if 'TEUR' in stripped:
                vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
                if vals:
                    result['investitionen'] = vals[0]
                pending_feld = None
            else:
                # Wert kommt auf Folgezeile (kann mehrere Zeilen sein: "Vorführfahrzeuge) TEUR 50,6")
                pending_feld = 'investitionen'
        elif stripped.startswith('Zinsergebnis'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['zinsergebnis'] = vals[0]
            pending_feld = None
        elif stripped.startswith('Jahresergebnis'):
            if 'TEUR' in stripped:
                vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
                if vals:
                    result['jahresergebnis'] = vals[0]
                pending_feld = None
            else:
                # Wert kommt auf Folgezeile: "(vor Ergebnisübernahme) TEUR -193,2 ..."
                pending_feld = 'jahresergebnis'

        # Cashflow
        elif 'Geschäftstätigkeit' in stripped and 'TEUR' in stripped:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['cashflow_geschaeft'] = vals[0]
            pending_feld = None
        elif 'Investitionstätigkeit' in stripped and 'TEUR' in stripped:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['cashflow_invest'] = vals[0]
            pending_feld = None
        elif 'Finanzierungstätigkeit' in stripped and 'TEUR' in stripped:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['cashflow_finanz'] = vals[0]
            pending_feld = None
        elif 'Jahresende' in stripped and 'TEUR' in stripped:
            # "Jahresende TEUR 190,3 134,8 ..." (Folgezeile nach "Finanzmittelbestand am")
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['finanzmittel_jahresende'] = vals[0]
            pending_feld = None

    return result


def _extrahiere_ertragslage(page) -> dict:
    """Extrahiert Betriebsergebnis, Finanzergebnis, Neutrales Ergebnis aus Ertragslage-Seite."""
    text = page.extract_text() or ''
    lines = text.split('\n')

    result = {}

    for line in lines:
        parts = line.strip().split()
        if len(parts) < 2:
            continue

        if line.strip().startswith('Betriebsergebnis'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['betriebsergebnis'] = vals[0]
        elif line.strip().startswith('Finanzergebnis'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['finanzergebnis'] = vals[0]
        elif line.strip().startswith('Neutrales Ergebnis'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['neutrales_ergebnis'] = vals[0]

    return result


def _extrahiere_aus_anlagen(pdf) -> dict:
    """Extrahiert Kennzahlen aus Bilanz (Anlage 1) und GuV (Anlage 2).

    Fallback-Parser für PDFs ohne Mehrjahresvergleich (z.B. Auto Greiner).
    Werte werden in EUR extrahiert und in TEUR umgerechnet.
    """
    result = {}
    ganzer_text = '\n'.join(page.extract_text() or '' for page in pdf.pages)

    # --- Bilanz-Werte (aus "Bilanz zum 31. August") ---
    # Bilanzsumme: die letzte Zahl in der Bilanz-Zeile die mit der Seitensumme übereinstimmt
    # Format: "3.568.219,03 3.728.115,49" (aktuell, Vorjahr)
    bilanz_match = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})\s+(\d{1,3}(?:\.\d{3})*,\d{2})\s*$',
                               ganzer_text, re.MULTILINE)

    # Eigenkapital aus "Eigenkapital" Zeile mit Kapitalanteile-Summe
    # Suche nach dem Muster: Kapitalanteile-Summe (z.B. "1.348.786,76 1.322.610,57")
    ek_matches = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})\s+(\d{1,3}(?:\.\d{3})*,\d{2})', ganzer_text)

    # --- GuV-Werte (aus "Gewinn- und Verlustrechnung") ---
    for page in pdf.pages:
        text = page.extract_text() or ''
        if 'Gewinn- und Verlustrechnung' not in text and 'Verlustrechnung' not in text:
            continue
        if 'Anlage' not in text:
            continue

        lines = text.split('\n')
        for line in lines:
            # Zahlen extrahieren: Format "1.234.567,89" oder "-1.234.567,89"
            zahlen = re.findall(r'-?\d{1,3}(?:\.\d{3})*,\d{2}', line)
            if not zahlen:
                continue
            # Erste Zahl = aktuelles GJ
            aktuelle = _parse_german_number(zahlen[0])

            # Umsatzerlöse (Zeile 1)
            if re.match(r'^\d+\.\s*U', line) or 'Umsatzerlöse' in line or ('U' in line[:5] and aktuelle and aktuelle > 1000000):
                if aktuelle and aktuelle > 100000:
                    result['umsatz'] = round(aktuelle / 1000, 1)

            # Materialaufwand
            elif 'Materialaufwand' in line or ('aterial' in line and aktuelle and aktuelle < -100000):
                if aktuelle and aktuelle < 0:
                    result['_materialaufwand'] = aktuelle

            # Abschreibungen
            elif 'Abschreibungen' in line or 'bschreibung' in line:
                if aktuelle and aktuelle < 0:
                    result['abschreibungen'] = round(abs(aktuelle) / 1000, 1)

            # Sonstige betriebliche Aufwendungen
            elif 'Sonstige betriebliche Aufwendungen' in line or 'onstige betrieblic' in line:
                if aktuelle and aktuelle < 0:
                    result['_sonst_aufw'] = aktuelle

            # Zinsaufwendungen
            elif 'Zins' in line and 'Aufwendungen' in line:
                if aktuelle and aktuelle < 0:
                    result['zinsergebnis'] = round(aktuelle / 1000, 1)

            # Ergebnis nach Steuern / Jahresüberschuss
            elif 'Ergebnis nach Steuern' in line:
                if aktuelle is not None:
                    result['jahresergebnis'] = round(aktuelle / 1000, 1)
            elif ('schuss' in line or 'fehlbetrag' in line) and re.match(r'^\d+\.', line.strip()):
                if aktuelle is not None and 'jahresergebnis' not in result:
                    result['jahresergebnis'] = round(aktuelle / 1000, 1)

    # --- Bilanz-Seite: Bilanzsumme und EK ---
    for page in pdf.pages:
        text = page.extract_text() or ''
        if 'Bilanz zum' not in text:
            continue
        if 'Anlage' not in text and 'A K T I V A' not in text:
            continue

        lines = text.split('\n')
        for line in lines:
            zahlen = re.findall(r'-?\d{1,3}(?:\.\d{3})*,\d{2}', line)
            if not zahlen:
                continue
            aktuelle = _parse_german_number(zahlen[0])

            # Bilanzsumme: letzte Zeile der Bilanz (enthält Gesamtsumme)
            # Beide Seiten (Aktiva + Passiva) enden mit derselben Zahl
            if aktuelle and aktuelle > 1000000:
                result['bilanzsumme'] = round(aktuelle / 1000, 1)  # wird überschrieben bis zur letzten Zeile

            # Eigenkapital: Zeile mit Kapitalanteile-Summe
            if ('1.348' in line or '1.322' in line) and 'Kommandit' not in line:
                # Suche spezifisch nach der EK-Summenzeile
                pass

        # Eigenkapital: suche die Zeile mit 2 großen Zahlen nach "Kapitalanteile"/"Eigenkapital"
        ek_found = False
        for i, line in enumerate(lines):
            if ek_found:
                break
            if 'Kapitalanteile' in line or ('Eigenkapital' in line and 'quote' not in line.lower()):
                # Die nächsten Zeilen nach Eigenkapital durchsuchen
                for j in range(i, min(i+8, len(lines))):
                    subline = lines[j]
                    zahlen = re.findall(r'-?\d{1,3}(?:\.\d{3})*,\d{2}', subline)
                    if len(zahlen) >= 2:
                        v1 = _parse_german_number(zahlen[0])
                        v2 = _parse_german_number(zahlen[1])
                        # EK-Summenzeile: zwei ähnlich große Zahlen > 50.000
                        if v1 and v2 and abs(v1) > 50000 and abs(v2) > 50000:
                            result['eigenkapital'] = round(v1 / 1000, 1)
                            ek_found = True
                            break

    # Rohertrag berechnen wenn möglich
    if result.get('umsatz') and result.get('_materialaufwand'):
        rohertrag = result['umsatz'] * 1000 + result['_materialaufwand']
        result['rohertrag_pct'] = round(rohertrag / (result['umsatz'] * 1000) * 100, 1)

    # EK-Quote berechnen
    if result.get('eigenkapital') and result.get('bilanzsumme') and result['bilanzsumme'] > 0:
        result['ek_quote'] = round(result['eigenkapital'] / result['bilanzsumme'] * 100, 1)

    # Betriebsergebnis berechnen
    if all(k in result for k in ['umsatz', '_materialaufwand', 'abschreibungen', '_sonst_aufw']):
        be = (result['umsatz'] * 1000 + result['_materialaufwand']
              - result['abschreibungen'] * 1000 + result['_sonst_aufw'])
        result['betriebsergebnis'] = round(be / 1000, 1)

    # Temp-Felder entfernen
    result.pop('_materialaufwand', None)
    result.pop('_sonst_aufw', None)

    return result


def _gj_aus_dateiname(dateiname: str) -> Optional[str]:
    """Extrahiert das Geschäftsjahr aus dem Dateinamen.

    'Autohaus Greiner GmbH & Co. KG JA 2025 signiert.pdf' → '2024/25'
    'Autohaus Greiner GmbH & Co. KG JA 31.08.2024.pdf' → '2023/24'
    'AH Greiner GmbH & Co. KG JA 2022.pdf' → '2021/22'
    Die Jahreszahl im Dateinamen ist das END-Jahr des GJ.
    """
    # Format "JA 31.08.2024" (Datumsformat)
    match = re.search(r'JA\s+\d{2}\.\d{2}\.(\d{4})', dateiname)
    if match:
        end_jahr = int(match.group(1))
        start_jahr = end_jahr - 1
        return f"{start_jahr}/{str(end_jahr)[-2:]}"

    # Format "JA 2025" (Jahreszahl)
    match = re.search(r'JA\s+(\d{4})', dateiname)
    if not match:
        return None
    end_jahr = int(match.group(1))
    start_jahr = end_jahr - 1
    return f"{start_jahr}/{str(end_jahr)[-2:]}"


def _gj_aus_zusammenfuehrung(dateiname: str) -> Optional[str]:
    """Extrahiert das Geschäftsjahr aus einem Zusammenführung-Dateinamen.

    'Zusammenführung 2021.pdf'                           → '2020/21'
    'Zusammenführung 2022.pdf'                           → '2021/22'
    'Zusammenführung AH Greiner und Auto Greiner 2023.pdf' → '2022/23'
    'Zusammenführung Vermögensgegenstände 2025.pdf'      → '2024/25'
    'Zusammenführung der Vermögensgegenstände 31.08.2024.pdf' → '2023/24'
    """
    # Format mit Datum "31.08.2024"
    match = re.search(r'\d{2}\.\d{2}\.(\d{4})', dateiname)
    if match:
        end_jahr = int(match.group(1))
        start_jahr = end_jahr - 1
        return f"{start_jahr}/{str(end_jahr)[-2:]}"

    # Format mit Jahreszahl am Ende (z.B. "... 2025.pdf", "... 2023 signiert.pdf")
    match = re.search(r'(\d{4})', dateiname)
    if match:
        end_jahr = int(match.group(1))
        start_jahr = end_jahr - 1
        return f"{start_jahr}/{str(end_jahr)[-2:]}"

    return None


def _stichtag_aus_gj(gj: str) -> date:
    """Berechnet den Bilanzstichtag (31.08.) aus dem GJ.

    '2024/25' → 2025-08-31
    """
    teile = gj.split('/')
    start_jahr = int(teile[0])
    return date(start_jahr + 1, 8, 31)


def import_jahresabschluss(dateipfad: str, gesellschaft: str = 'autohaus', importiert_von: str = 'system') -> dict:
    """Importiert einen Jahresabschluss aus einem RAW-Partner PDF.

    Returns: Dict mit importierten Werten + Zusammenfassung.
    """
    if not os.path.exists(dateipfad):
        return {'error': f'Datei nicht gefunden: {dateipfad}'}

    dateiname = os.path.basename(dateipfad)
    if gesellschaft == 'gruppe':
        gj = _gj_aus_zusammenfuehrung(dateiname)
    else:
        gj = _gj_aus_dateiname(dateiname)
    if not gj:
        return {'error': f'Geschäftsjahr nicht aus Dateiname erkennbar: {dateiname}'}

    stichtag = _stichtag_aus_gj(gj)

    logger.info(f"Importiere JA {gj} aus {dateiname}")

    with pdfplumber.open(dateipfad) as pdf:
        # Strategie 1: Mehrjahresvergleich (Autohaus Greiner, volle Berichte)
        mjv_seite = _finde_mehrjahresvergleich_seite(pdf)
        if mjv_seite is not None:
            daten = _extrahiere_mehrjahresvergleich(pdf.pages[mjv_seite])
            logger.info(f"  Mehrjahresvergleich (S. {mjv_seite + 1}): {len(daten)} Werte")

            # Ertragslage finden und parsen
            el_seite = _finde_ertragslage_seite(pdf)
            if el_seite is not None:
                el_daten = _extrahiere_ertragslage(pdf.pages[el_seite])
                daten.update(el_daten)
                logger.info(f"  Ertragslage (S. {el_seite + 1}): {len(el_daten)} Werte")
        else:
            # Strategie 2: Bilanz + GuV aus Anlagen parsen (Auto Greiner, kürzere Berichte)
            logger.info(f"  Kein Mehrjahresvergleich → parse Bilanz + GuV aus Anlagen")
            daten = _extrahiere_aus_anlagen(pdf)
            logger.info(f"  Anlagen-Parser: {len(daten)} Werte")

    if not daten:
        return {'error': 'Keine Werte aus PDF extrahiert'}

    # In DB speichern
    from api.db_utils import db_session

    with db_session() as conn:
        cursor = conn.cursor()

        # UPSERT
        felder = ['geschaeftsjahr', 'gesellschaft', 'stichtag', 'quelldatei', 'importiert_von']
        werte = [gj, gesellschaft, stichtag, dateiname, importiert_von]

        db_felder = [
            'bilanzsumme', 'anlagevermoegen', 'umlaufvermoegen', 'eigenkapital',
            'ek_quote', 'rueckstellungen', 'verbindlichkeiten', 'umsatz',
            'rohertrag_pct', 'personalaufwand', 'abschreibungen', 'investitionen',
            'zinsergebnis', 'betriebsergebnis', 'finanzergebnis', 'neutrales_ergebnis',
            'jahresergebnis', 'cashflow_geschaeft', 'cashflow_invest', 'cashflow_finanz',
            'finanzmittel_jahresende'
        ]

        for feld in db_felder:
            felder.append(feld)
            werte.append(daten.get(feld))

        placeholders = ', '.join(['%s'] * len(felder))
        spalten = ', '.join(felder)
        update_clause = ', '.join([f"{f} = EXCLUDED.{f}" for f in felder if f not in ('geschaeftsjahr', 'gesellschaft')])

        sql = f"""
            INSERT INTO jahresabschluss_daten ({spalten})
            VALUES ({placeholders})
            ON CONFLICT (geschaeftsjahr, gesellschaft) DO UPDATE SET {update_clause}, importiert_am = NOW()
        """

        cursor.execute(sql, werte)
        conn.commit()

    zusammenfassung = {
        'geschaeftsjahr': gj,
        'gesellschaft': gesellschaft,
        'stichtag': str(stichtag),
        'quelldatei': dateiname,
        'werte': daten,
        'anzahl_werte': len(daten)
    }

    logger.info(f"  JA {gj} [{gesellschaft}] importiert: {len(daten)} Werte (EK: {daten.get('eigenkapital')} TEUR, Ergebnis: {daten.get('jahresergebnis')} TEUR)")

    return zusammenfassung


def get_verfuegbare_jahresabschluesse() -> list:
    """Listet alle verfügbaren JA-PDFs mit Import-Status."""
    from api.db_utils import db_session

    ergebnis = []

    if not os.path.exists(BUCHHALTUNG_PFAD):
        return ergebnis

    # Alle Abschluss-Verzeichnisse scannen (verschiedene Unterordner-Namen)
    raw_ordner_namen = ['Abschlüsse RAW', 'Jahresabschlüsse RAW', 'Jahresabschlüsse RAW Partner', 'RAW-Bilanzen']

    for ordner in sorted(os.listdir(BUCHHALTUNG_PFAD)):
        if not ordner.startswith('Abschluss '):
            continue

        ordner_pfad = os.path.join(BUCHHALTUNG_PFAD, ordner)

        # Suche in allen bekannten RAW-Unterordnern + direkt im Hauptordner
        # Auch Ordnernamen mit Präfix "Abschluss YYYY YYYY" prüfen
        such_pfade = [ordner_pfad] + [os.path.join(ordner_pfad, rn) for rn in raw_ordner_namen]
        # Ordner wie "Abschluss 2021 2022 Jahresabschlüsse RAW"
        such_pfade.append(os.path.join(ordner_pfad, ordner + ' Jahresabschlüsse RAW'))

        for such_pfad in such_pfade:
            if not os.path.exists(such_pfad) or not os.path.isdir(such_pfad):
                continue

            for datei in os.listdir(such_pfad):
                if not datei.endswith('.pdf'):
                    continue

                # Bestimme Gesellschaft anhand des Dateinamens
                gesellschaft = None
                if datei.startswith('Autohaus Greiner') or datei.startswith('AH Greiner'):
                    gesellschaft = 'autohaus'
                elif datei.startswith('Auto Greiner'):
                    gesellschaft = 'auto'
                elif 'Zusammenführung' in datei or 'Zusammenfuehrung' in datei:
                    gesellschaft = 'gruppe'
                else:
                    continue  # Datei gehört nicht zu unseren Gesellschaften

                if 'JA' not in datei and gesellschaft != 'gruppe':
                    continue

                if gesellschaft == 'gruppe':
                    gj = _gj_aus_zusammenfuehrung(datei)
                else:
                    gj = _gj_aus_dateiname(datei)
                if not gj:
                    continue

                # Duplikate vermeiden (gleiches GJ + Gesellschaft aus verschiedenen Ordnern)
                if any(e['geschaeftsjahr'] == gj and e.get('gesellschaft') == gesellschaft for e in ergebnis):
                    continue

                vollpfad = os.path.join(such_pfad, datei)

                ergebnis.append({
                    'geschaeftsjahr': gj,
                    'gesellschaft': gesellschaft,
                    'dateiname': datei,
                    'pfad': vollpfad,
                    'importiert': False,
                    'importiert_am': None
                })

    # Import-Status aus DB prüfen
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT geschaeftsjahr, gesellschaft, importiert_am FROM jahresabschluss_daten")
        importiert = {(row[0], row[1]): row[2] for row in cursor.fetchall()}

    for eintrag in ergebnis:
        key = (eintrag['geschaeftsjahr'], eintrag.get('gesellschaft', 'autohaus'))
        if key in importiert:
            eintrag['importiert'] = True
            eintrag['importiert_am'] = str(importiert[key])

    return sorted(ergebnis, key=lambda x: x['geschaeftsjahr'], reverse=True)


def import_alle_jahresabschluesse(importiert_von: str = 'system') -> list:
    """Importiert alle noch nicht importierten JAs."""
    verfuegbar = get_verfuegbare_jahresabschluesse()
    ergebnisse = []

    for ja in verfuegbar:
        if not ja['importiert']:
            result = import_jahresabschluss(ja['pfad'], gesellschaft=ja.get('gesellschaft', 'autohaus'), importiert_von=importiert_von)
            ergebnisse.append(result)

    return ergebnisse


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s: %(message)s')

    print("Verfügbare JAs:")
    for ja in get_verfuegbare_jahresabschluesse():
        status = "importiert" if ja['importiert'] else "nicht importiert"
        print(f"  {ja['geschaeftsjahr']}: {status} — {ja['dateiname']}")

    print("\nImportiere alle...")
    results = import_alle_jahresabschluesse()
    for r in results:
        if 'error' in r:
            print(f"  FEHLER: {r['error']}")
        else:
            print(f"  OK: {r['geschaeftsjahr']}: {r['anzahl_werte']} Werte")
