#!/usr/bin/env python3
"""
WERKSTATT KPI DEFINITIONEN - Single Source of Truth
====================================================
ALLE KPI-Berechnungen für die Werkstatt an EINER Stelle.
Wird von API, Reports, Dashboards verwendet.

WICHTIG: Änderungen hier wirken sich auf ALLE Komponenten aus!

KPI-ÜBERSICHT (Branchenstandard Kfz-Gewerbe):
=============================================

1. ANWESENHEITSGRAD = Anwesend / Bezahlt × 100
   → Wie viel der bezahlten Zeit ist der MA da? (Ziel: ~79%)

2. AUSLASTUNGSGRAD = Gestempelt / Anwesend × 100  
   → Wie viel der Anwesenheit wird produktiv gestempelt? (Ziel: 90%)

3. LEISTUNGSGRAD = Vorgabe-AW / Gestempelt-AW × 100
   → Wie schnell vs. Kalkulation? (Ziel: 100%, >100% = schneller)

4. EFFIZIENZ = Anwesenheit × Auslastung × Leistung
   → Gesamtproduktivität - was kommt am Ende raus? (Ziel: ~71%)

5. ENTGANGENER UMSATZ = (Gestempelt - Vorgabe) × AW-Preis
   → Bei Überzeiten: Was hätte noch verdient werden können?

6. STUNDEN PRO DURCHGANG = Verkaufte Stunden / Anzahl Aufträge
   → Wie werthaltig ist ein Auftrag? (Branchenschnitt: ~1,8h)

7. STUNDENVERRECHNUNGSSATZ = Lohnumsatz / Verkaufte Stunden
   → Was wird pro Stunde verdient?

Author: Claude
Date: 2025-12-09 (TAG 110)
"""

from typing import Optional, Dict, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP


# =============================================================================
# KONSTANTEN
# =============================================================================

# Zeiteinheiten
MINUTEN_PRO_AW = 6                    # 1 AW = 6 Minuten (Branchenstandard)
STUNDEN_PRO_WOCHE = 40                # Standard-Arbeitszeit
ARBEITSTAGE_PRO_WOCHE = 5
STUNDEN_PRO_TAG = STUNDEN_PRO_WOCHE / ARBEITSTAGE_PRO_WOCHE  # 8h

# Zielwerte (Branchenstandard Kfz-Gewerbe)
ZIEL_ANWESENHEITSGRAD = 79.0          # ~79% (wg. Urlaub, Krankheit, etc.)
ZIEL_AUSLASTUNGSGRAD = 90.0           # 90% der Anwesenheit produktiv
ZIEL_LEISTUNGSGRAD = 100.0            # 100% = genau wie kalkuliert
ZIEL_EFFIZIENZ = 71.0                 # 0.79 × 0.90 × 1.00 = ~71%
ZIEL_STUNDEN_PRO_DURCHGANG = 1.8      # Branchenschnitt

# Schwellenwerte für Status-Bewertung
SCHWELLEN = {
    'anwesenheitsgrad': {'gut': 75.0, 'warnung': 65.0},
    'auslastungsgrad': {'gut': 85.0, 'warnung': 75.0},
    'leistungsgrad': {'gut': 85.0, 'warnung': 70.0},
    'effizienz': {'gut': 65.0, 'warnung': 55.0},
    'produktivitaet': {'gut': 80.0, 'warnung': 60.0},  # Alias für Auslastung
}

# =============================================================================
# MARKT-BENCHMARKS (Branchendurchschnitt - aus öffentlichen Studien)
# =============================================================================
# Quelle: DAT Report, IBISWorld, Auto Zeitung, Hans-Böckler-Stiftung (2023-2025)
# TAG 199: Statische Benchmarks für Marktvergleich (Phase 1)
# TODO: Phase 2: WESP API-Integration für dynamische Benchmarks

MARKT_BENCHMARKS = {
    # KPIs (Branchendurchschnitt)
    'leistungsgrad': 100.0,           # Ziel: 100% (genau wie kalkuliert)
    'auslastungsgrad': 90.0,           # Ziel: 90% der Anwesenheit produktiv
    'anwesenheitsgrad': 79.0,          # Ziel: ~79% (wg. Urlaub, Krankheit)
    'effizienz': 71.0,                 # Ziel: ~71% (0.79 × 0.90 × 1.00)
    'stunden_pro_durchgang': 1.8,      # Branchenschnitt: 1,8h pro Auftrag
    
    # Finanz-KPIs
    'stundensatz_durchschnitt': 148.55,  # €/h (Deutschland 2023, 20 Großstädte)
    'stundensatz_min': 126.0,            # €/h (Leipzig - niedrigster)
    'stundensatz_max': 174.5,            # €/h (München - höchster)
    'bruttomarge': 45.0,                 # % (Zielwert für gesunde Werkstatt)
    'teile_marge': 58.0,                 # % (Zielwert, aktuell 51-60% im Markt)
    'kundenbindungsrate': 75.0,          # % (Zielwert für Erfolg)
    
    # Wartezeiten & Auslastung
    'wartezeit_durchschnitt': 9.3,      # Tage (Durchschnittliche Wartezeit auf Termin)
    'werkstattdichte_min': 1000,         # Fahrzeuge pro Werkstatt (Wuppertal)
    'werkstattdichte_max': 2000,        # Fahrzeuge pro Werkstatt (München)
    
    # Quelle & Datum
    'quelle': 'DAT Report, IBISWorld, Auto Zeitung (2023-2025)',
    'datum': '2025-01',
    'hinweis': 'Statische Benchmarks - Phase 1. Phase 2: WESP API für dynamische Werte geplant.'
}


def get_markt_benchmark(kpi_name: str) -> Optional[float]:
    """
    Holt Markt-Benchmark für einen KPI (SSOT).
    
    Args:
        kpi_name: Name des KPIs (z.B. 'leistungsgrad', 'stundensatz_durchschnitt')
        
    Returns:
        Benchmark-Wert oder None wenn nicht gefunden
        
    Example:
        >>> get_markt_benchmark('leistungsgrad')
        100.0
        >>> get_markt_benchmark('stundensatz_durchschnitt')
        148.55
    """
    return MARKT_BENCHMARKS.get(kpi_name)


def vergleiche_mit_markt(ist_wert: Optional[float], kpi_name: str) -> Dict[str, Any]:
    """
    Vergleicht Ist-Wert mit Markt-Benchmark (SSOT).
    
    Args:
        ist_wert: Tatsächlicher Wert
        kpi_name: Name des KPIs
        
    Returns:
        Dict mit:
        - 'ist': Ist-Wert
        - 'benchmark': Benchmark-Wert
        - 'differenz': Differenz (Ist - Benchmark)
        - 'differenz_prozent': Differenz in % (relativ zum Benchmark)
        - 'status': 'besser', 'gleich', 'schlechter'
        - 'icon': Emoji für Status
        
    Example:
        >>> vergleiche_mit_markt(85.0, 'leistungsgrad')
        {
            'ist': 85.0,
            'benchmark': 100.0,
            'differenz': -15.0,
            'differenz_prozent': -15.0,
            'status': 'schlechter',
            'icon': '📉'
        }
    """
    if ist_wert is None:
        return {
            'ist': None,
            'benchmark': None,
            'differenz': None,
            'differenz_prozent': None,
            'status': 'unbekannt',
            'icon': '–'
        }
    
    benchmark = get_markt_benchmark(kpi_name)
    if benchmark is None:
        return {
            'ist': ist_wert,
            'benchmark': None,
            'differenz': None,
            'differenz_prozent': None,
            'status': 'unbekannt',
            'icon': '–'
        }
    
    differenz = ist_wert - benchmark
    
    # Für Prozent-KPIs: Differenz in Prozentpunkten
    if kpi_name in ['leistungsgrad', 'auslastungsgrad', 'anwesenheitsgrad', 'effizienz', 
                    'bruttomarge', 'teile_marge', 'kundenbindungsrate']:
        differenz_prozent = differenz  # Prozentpunkte
    else:
        # Für absolute Werte: Relativ zum Benchmark
        differenz_prozent = (differenz / benchmark * 100) if benchmark != 0 else 0
    
    # Status bestimmen (Toleranz: ±2% für "gleich")
    if abs(differenz_prozent) <= 2.0:
        status, icon = 'gleich', '➡️'
    elif differenz_prozent > 0:
        status, icon = 'besser', '📈'
    else:
        status, icon = 'schlechter', '📉'
    
    return {
        'ist': ist_wert,
        'benchmark': benchmark,
        'differenz': round(differenz, 2),
        'differenz_prozent': round(differenz_prozent, 1),
        'status': status,
        'icon': icon
    }


# =============================================================================
# KERN-BERECHNUNGEN
# =============================================================================

def berechne_anwesenheitsgrad(anwesend_h: float, bezahlt_h: float) -> Optional[float]:
    """
    Berechnet den Anwesenheitsgrad.
    
    Formel: Anwesende Stunden / Bezahlte Stunden × 100
    
    Args:
        anwesend_h: Tatsächlich anwesende Stunden
        bezahlt_h: Bezahlte Stunden (Soll lt. Arbeitsvertrag)
        
    Returns:
        Anwesenheitsgrad in % (Ziel: ~79%)
    """
    if bezahlt_h is None or bezahlt_h <= 0:
        return None
    if anwesend_h is None or anwesend_h < 0:
        return None
    
    return round((anwesend_h / bezahlt_h) * 100, 1)


def berechne_auslastungsgrad(gestempelt_h: float, anwesend_h: float) -> Optional[float]:
    """
    Berechnet den Auslastungsgrad (= Produktivität).
    
    Formel: Gestempelte Auftragsstunden / Anwesende Stunden × 100
    
    Args:
        gestempelt_h: Auf Aufträge gestempelte Stunden
        anwesend_h: Anwesende Stunden
        
    Returns:
        Auslastungsgrad in % (Ziel: 90%)
    """
    if anwesend_h is None or anwesend_h <= 0:
        return None
    if gestempelt_h is None or gestempelt_h < 0:
        return None
    
    return round((gestempelt_h / anwesend_h) * 100, 1)


# Alias für Abwärtskompatibilität
def berechne_produktivitaet(gestempelt_min: float, anwesend_min: float) -> Optional[float]:
    """Alias für berechne_auslastungsgrad (mit Minuten statt Stunden)."""
    if anwesend_min is None or anwesend_min <= 0:
        return None
    if gestempelt_min is None or gestempelt_min < 0:
        return None
    return round((gestempelt_min / anwesend_min) * 100, 1)


def berechne_leistungsgrad(vorgabe_aw: float, gestempelt_aw: float) -> Optional[float]:
    """
    Berechnet den Leistungsgrad.
    
    Formel: Vorgabe-AW / Gestempelte-AW × 100
    
    Args:
        vorgabe_aw: Kalkulierte/verkaufte AW (was Kunde zahlt)
        gestempelt_aw: Tatsächlich gestempelte AW
        
    Returns:
        Leistungsgrad in % (Ziel: 100%, >100% = schneller als Vorgabe)
        
    Beispiele:
        10 AW Vorgabe, 10 AW gestempelt → 100% (genau wie kalkuliert)
        10 AW Vorgabe, 8 AW gestempelt  → 125% (schneller!)
        10 AW Vorgabe, 12 AW gestempelt → 83%  (langsamer)
    """
    if gestempelt_aw is None or gestempelt_aw <= 0:
        return None
    if vorgabe_aw is None or vorgabe_aw < 0:
        return None
    
    return round((vorgabe_aw / gestempelt_aw) * 100, 1)


def berechne_effizienz(
    anwesenheitsgrad: float = None,
    auslastungsgrad: float = None, 
    leistungsgrad: float = None,
    # Alternativ: Direktberechnung
    verkauft_h: float = None,
    bezahlt_h: float = None
) -> Optional[float]:
    """
    Berechnet die Gesamteffizienz.
    
    Formel A: Anwesenheitsgrad × Auslastungsgrad × Leistungsgrad / 10000
    Formel B: Verkaufte Stunden / Bezahlte Stunden × 100
    
    Args:
        Option 1: anwesenheitsgrad, auslastungsgrad, leistungsgrad (alle in %)
        Option 2: verkauft_h, bezahlt_h (Direktberechnung)
        
    Returns:
        Effizienz in % (Ziel: ~71%)
    """
    # Direktberechnung wenn möglich
    if verkauft_h is not None and bezahlt_h is not None and bezahlt_h > 0:
        return round((verkauft_h / bezahlt_h) * 100, 1)
    
    # Berechnung aus Einzelwerten
    if all(v is not None and v > 0 for v in [anwesenheitsgrad, auslastungsgrad, leistungsgrad]):
        effizienz = (anwesenheitsgrad / 100) * (auslastungsgrad / 100) * (leistungsgrad / 100) * 100
        return round(effizienz, 1)
    
    return None


def berechne_entgangener_umsatz(vorgabe_aw: float, gestempelt_aw: float, aw_preis: float) -> float:
    """
    Berechnet den entgangenen Umsatz bei Überzeiten.
    
    Formel: (Gestempelte-AW - Vorgabe-AW) × AW-Preis
    
    WICHTIG: Nur positive Werte! Schneller arbeiten = 0 € (kein "Gewinn")
    
    Returns:
        Entgangener Umsatz in € (immer >= 0)
    """
    if vorgabe_aw is None or gestempelt_aw is None or aw_preis is None:
        return 0.0
    
    diff_aw = gestempelt_aw - vorgabe_aw
    if diff_aw <= 0:
        return 0.0
    
    return round(diff_aw * aw_preis, 2)


def berechne_stunden_pro_durchgang(verkauft_h: float, anzahl_auftraege: int) -> Optional[float]:
    """
    Berechnet die durchschnittlichen Stunden pro Werkstattdurchgang.
    
    Formel: Verkaufte Stunden / Anzahl Aufträge
    
    Returns:
        Stunden pro Durchgang (Branchenschnitt: ~1,8h)
    """
    if anzahl_auftraege is None or anzahl_auftraege <= 0:
        return None
    if verkauft_h is None or verkauft_h < 0:
        return None
    
    return round(verkauft_h / anzahl_auftraege, 2)


def berechne_stundenverrechnungssatz(
    lohnumsatz_eur: float, 
    verkauft_h: float,
    vorgabe_h: float = None
) -> Dict[str, Optional[float]]:
    """
    Berechnet den Stundenverrechnungssatz (erzielt vs. Vorgabe).
    
    Formeln:
        SVS_erzielt = Lohnumsatz / Verkaufte Stunden
        SVS_vorgabe = Lohnumsatz / Vorgabe Stunden (wenn vorhanden)
    
    Returns:
        {
            'erzielt': Tatsächlich erzielter SVS,
            'vorgabe': SVS basierend auf Vorgabezeiten (falls berechnet),
            'differenz': Abweichung in €
        }
    """
    result = {'erzielt': None, 'vorgabe': None, 'differenz': None}
    
    if lohnumsatz_eur is not None and verkauft_h is not None and verkauft_h > 0:
        result['erzielt'] = round(lohnumsatz_eur / verkauft_h, 2)
    
    if lohnumsatz_eur is not None and vorgabe_h is not None and vorgabe_h > 0:
        result['vorgabe'] = round(lohnumsatz_eur / vorgabe_h, 2)
    
    if result['erzielt'] and result['vorgabe']:
        result['differenz'] = round(result['erzielt'] - result['vorgabe'], 2)
    
    return result


# =============================================================================
# KONVERTIERUNGEN
# =============================================================================

def minuten_zu_aw(minuten: float) -> float:
    """Konvertiert Minuten in AW (1 AW = 6 min)."""
    if minuten is None:
        return 0.0
    return round(minuten / MINUTEN_PRO_AW, 1)


def aw_zu_minuten(aw: float) -> float:
    """Konvertiert AW in Minuten."""
    if aw is None:
        return 0.0
    return round(aw * MINUTEN_PRO_AW, 0)


def minuten_zu_stunden(minuten: float) -> float:
    """Konvertiert Minuten in Stunden."""
    if minuten is None:
        return 0.0
    return round(minuten / 60, 2)


def stunden_zu_minuten(stunden: float) -> float:
    """Konvertiert Stunden in Minuten."""
    if stunden is None:
        return 0.0
    return round(stunden * 60, 0)


def aw_zu_stunden(aw: float) -> float:
    """Konvertiert AW in Stunden (1 AW = 0.1h = 6min)."""
    if aw is None:
        return 0.0
    return round(aw / 10, 2)


def stunden_zu_aw(stunden: float) -> float:
    """Konvertiert Stunden in AW."""
    if stunden is None:
        return 0.0
    return round(stunden * 10, 1)


# =============================================================================
# STATUS-BEWERTUNGEN
# =============================================================================

def _bewerte_kpi(wert: Optional[float], kpi_name: str, invers: bool = False) -> Dict[str, Any]:
    """
    Interne Hilfsfunktion zur KPI-Bewertung.
    
    Args:
        wert: KPI-Wert
        kpi_name: Name für Schwellenwert-Lookup
        invers: True wenn niedrigere Werte besser sind
    """
    if wert is None:
        return {
            'status': 'unbekannt',
            'icon': '–',
            'farbe': '#6c757d',
            'text': 'Keine Daten'
        }
    
    schwellen = SCHWELLEN.get(kpi_name, {'gut': 85.0, 'warnung': 70.0})
    
    if invers:
        # Niedrigere Werte sind besser (z.B. bei Kosten)
        if wert <= schwellen['warnung']:
            status, icon, farbe = 'gut', '✅', '#28a745'
        elif wert <= schwellen['gut']:
            status, icon, farbe = 'warnung', '⚠️', '#ffc107'
        else:
            status, icon, farbe = 'kritisch', '❌', '#dc3545'
    else:
        # Höhere Werte sind besser (Standard)
        if wert >= schwellen['gut']:
            status, icon, farbe = 'gut', '✅', '#28a745'
        elif wert >= schwellen['warnung']:
            status, icon, farbe = 'warnung', '⚠️', '#ffc107'
        else:
            status, icon, farbe = 'kritisch', '❌', '#dc3545'
    
    return {
        'status': status,
        'icon': icon,
        'farbe': farbe,
        'text': f'{wert:.1f}%' if wert else '–'
    }


def bewerte_anwesenheitsgrad(wert: Optional[float]) -> Dict[str, Any]:
    """Bewertet Anwesenheitsgrad."""
    return _bewerte_kpi(wert, 'anwesenheitsgrad')


def bewerte_auslastungsgrad(wert: Optional[float]) -> Dict[str, Any]:
    """Bewertet Auslastungsgrad."""
    return _bewerte_kpi(wert, 'auslastungsgrad')


def bewerte_leistungsgrad(wert: Optional[float]) -> Dict[str, Any]:
    """Bewertet Leistungsgrad."""
    return _bewerte_kpi(wert, 'leistungsgrad')


def bewerte_effizienz(wert: Optional[float]) -> Dict[str, Any]:
    """Bewertet Gesamteffizienz."""
    return _bewerte_kpi(wert, 'effizienz')


def bewerte_produktivitaet(wert: Optional[float]) -> Dict[str, Any]:
    """Bewertet Produktivität (Alias für Auslastungsgrad)."""
    return _bewerte_kpi(wert, 'produktivitaet')


# =============================================================================
# LOCOSOFT-KOMPATIBLE BERECHNUNGEN
# =============================================================================

def berechne_stempelzeit_locosoft(
    stempelungen: list,
    pausenzeiten: list = None
) -> float:
    """
    Berechnet Stempelzeit nach Locosoft-Logik (SSOT).
    
    Locosoft-Berechnung:
    1. Zeit-Spanne pro Tag = letzte Stempelung - erste Stempelung
    2. Minus Lücken zwischen Stempelungen
    3. Minus konfigurierte Pausenzeiten (wenn innerhalb der Zeit-Spanne)
    
    Args:
        stempelungen: Liste von Dicts mit 'start_time' und 'end_time' (datetime)
        pausenzeiten: Liste von Dicts mit 'datum' (date), 'break_start' (float Stunden), 'break_end' (float Stunden)
        
    Returns:
        Stempelzeit in Minuten (nach Locosoft-Logik)
        
    Example:
        >>> stempelungen = [
        ...     {'start_time': datetime(2025, 12, 1, 7, 49), 'end_time': datetime(2025, 12, 1, 8, 29)},
        ...     {'start_time': datetime(2025, 12, 1, 8, 30), 'end_time': datetime(2025, 12, 1, 9, 35)},
        ...     {'start_time': datetime(2025, 12, 1, 16, 38), 'end_time': datetime(2025, 12, 1, 16, 38)}
        ... ]
        >>> pausenzeiten = [{'datum': date(2025, 12, 1), 'break_start': 12.0, 'break_end': 12.733}]
        >>> berechne_stempelzeit_locosoft(stempelungen, pausenzeiten)
        4945.0
    """
    if not stempelungen:
        return 0.0
    
    from collections import defaultdict
    from datetime import datetime, date, time
    
    # Gruppiere Stempelungen nach Tag
    stempelungen_pro_tag = defaultdict(list)
    for st in stempelungen:
        if isinstance(st['start_time'], datetime):
            tag = st['start_time'].date()
        else:
            tag = st['start_time']
        stempelungen_pro_tag[tag].append(st)
    
    # Pausenzeiten nach Tag gruppieren
    pausen_pro_tag = {}
    if pausenzeiten:
        for p in pausenzeiten:
            if isinstance(p['datum'], date):
                tag = p['datum']
            else:
                tag = p['datum']
            pausen_pro_tag[tag] = p
    
    gesamt_minuten = 0.0
    
    # Für jeden Tag berechnen
    for tag, stempelungen_tag in stempelungen_pro_tag.items():
        if not stempelungen_tag:
            continue
        
        # Sortiere nach start_time
        stempelungen_tag.sort(key=lambda x: x['start_time'])
        
        # Erste und letzte Stempelung
        erste = stempelungen_tag[0]['start_time']
        letzte = stempelungen_tag[-1]['end_time']
        
        # Zeit-Spanne in Minuten
        if isinstance(erste, datetime) and isinstance(letzte, datetime):
            spanne_minuten = (letzte - erste).total_seconds() / 60
        else:
            # Fallback für andere Datentypen
            spanne_minuten = 0
        
        # Lücken zwischen Stempelungen berechnen
        luecken_minuten = 0.0
        for i in range(len(stempelungen_tag) - 1):
            ende_aktuell = stempelungen_tag[i]['end_time']
            start_naechst = stempelungen_tag[i + 1]['start_time']
            
            if isinstance(ende_aktuell, datetime) and isinstance(start_naechst, datetime):
                if start_naechst > ende_aktuell:
                    luecke = (start_naechst - ende_aktuell).total_seconds() / 60
                    luecken_minuten += luecke
        
        # Konfigurierte Pausenzeiten abziehen (wenn innerhalb der Zeit-Spanne)
        pausen_minuten = 0.0
        if tag in pausen_pro_tag:
            pause = pausen_pro_tag[tag]
            break_start_h = pause.get('break_start', 0)
            break_end_h = pause.get('break_end', 0)
            
            if break_start_h and break_end_h:
                # Konvertiere Stunden (z.B. 12.0) zu datetime
                break_start = datetime.combine(tag, time(int(break_start_h), int((break_start_h % 1) * 60)))
                break_end = datetime.combine(tag, time(int(break_end_h), int((break_end_h % 1) * 60)))
                
                # Prüfe, ob Pause innerhalb der Zeit-Spanne liegt
                if break_start >= erste and break_end <= letzte:
                    pause_dauer = (break_end - break_start).total_seconds() / 60
                    pausen_minuten += pause_dauer
        
        # Locosoft-Berechnung: Zeit-Spanne - Lücken - Pausen
        tag_minuten = spanne_minuten - luecken_minuten - pausen_minuten
        gesamt_minuten += max(0, tag_minuten)  # Nicht negativ
    
    return round(gesamt_minuten, 0)


# =============================================================================
# AGGREGATIONS-FUNKTIONEN
# =============================================================================

def berechne_gesamt_leistungsgrad(total_vorgabe_aw: float, total_gestempelt_aw: float) -> Optional[float]:
    """
    Berechnet Gesamt-Leistungsgrad für mehrere Aufträge/Mechaniker.
    
    WICHTIG: (Summe Vorgabe) / (Summe Gestempelt) - NICHT Durchschnitt!
    """
    return berechne_leistungsgrad(total_vorgabe_aw, total_gestempelt_aw)


def berechne_gesamt_entgangener_umsatz(auftraege: list) -> float:
    """
    Berechnet gesamten entgangenen Umsatz für Auftragsliste.
    
    Args:
        auftraege: Liste mit Dicts {'vorgabe_aw', 'gestempelt_aw', 'aw_preis'}
    """
    total = 0.0
    for a in auftraege:
        vorgabe = a.get('vorgabe_aw', 0) or 0
        gestempelt = a.get('gestempelt_aw', 0) or 0
        aw_preis = a.get('aw_preis', 0) or 0
        total += berechne_entgangener_umsatz(vorgabe, gestempelt, aw_preis)
    return round(total, 2)


def berechne_anwesenheitsgrad_fuer_mechaniker_liste(mechaniker_liste: list, stunden_pro_tag: float = STUNDEN_PRO_TAG) -> Tuple[Optional[float], list]:
    """
    Berechnet Anwesenheitsgrad für eine Liste von Mechanikern (SSOT).
    
    WICHTIG: Gesamt = Summe der einzelnen, nicht anzahl_tage × 8 × anzahl_mechaniker!
    Grund: Mechaniker haben unterschiedlich viele Arbeitstage.
    
    Nutzt intern `berechne_mechaniker_kpis()` für jeden Mechaniker (SSOT).
    
    Args:
        mechaniker_liste: Liste mit Dicts {'tage', 'anwesenheit', 'stempelzeit', 'aw', ...}
                         (anwesenheit, stempelzeit in Minuten)
        stunden_pro_tag: Stunden pro Arbeitstag (default: 8h)
        
    Returns:
        Tuple: (gesamt_anwesenheitsgrad, aktualisierte_mechaniker_liste)
        - gesamt_anwesenheitsgrad: Gesamt-Anwesenheitsgrad in %
        - aktualisierte_mechaniker_liste: Liste mit erweiterten Dicts:
          - 'anwesenheitsgrad': Anwesenheitsgrad pro Mechaniker
          - 'bezahlt_h': Bezahlte Stunden
          - 'anwesend_h': Anwesende Stunden
    
    Example:
        >>> mechaniker = [
        ...     {'tage': 6, 'anwesenheit': 3000, 'stempelzeit': 2700, 'aw': 45},  # 6 Tage, 50h anwesend
        ...     {'tage': 2, 'anwesenheit': 1080, 'stempelzeit': 900, 'aw': 15}   # 2 Tage, 18h anwesend
        ... ]
        >>> gesamt, mechaniker = berechne_anwesenheitsgrad_fuer_mechaniker_liste(mechaniker)
        >>> gesamt  # (50 + 18) / (48 + 16) = 68/64 = 106.25%
        106.3
        >>> mechaniker[0]['anwesenheitsgrad']  # 50/48 = 104.2%
        104.2
    """
    gesamt_bezahlt_h_summe = 0
    gesamt_anwesend_h_summe = 0
    
    for m in mechaniker_liste:
        # WICHTIG: PostgreSQL gibt Decimal zurück, muss zu float konvertiert werden
        tage = int(float(m.get('tage') or 0))
        anwesenheit_min = float(m.get('anwesenheit') or 0)
        stempelzeit_min = float(m.get('stempelzeit') or 0)
        vorgabe_aw = float(m.get('aw') or 0)
        
        # Nutze zentrale KPI-Funktion (SSOT)
        kpis = berechne_mechaniker_kpis(
            anwesend_min=anwesenheit_min,
            gestempelt_min=stempelzeit_min,
            vorgabe_aw=vorgabe_aw,
            tage=tage,
            stunden_pro_tag=stunden_pro_tag
        )
        
        # Erweitere Mechaniker-Dict mit KPI-Ergebnissen
        m['anwesenheitsgrad'] = kpis.get('anwesenheitsgrad')
        m['bezahlt_h'] = kpis.get('bezahlt_h', 0)
        m['anwesend_h'] = round(kpis.get('anwesend_h', 0), 1)
        
        # Für Gesamt-Berechnung summieren
        gesamt_bezahlt_h_summe += kpis.get('bezahlt_h', 0)
        gesamt_anwesend_h_summe += kpis.get('anwesend_h', 0)
    
    # Gesamt-Anwesenheitsgrad = Summe Anwesend / Summe Bezahlt
    gesamt_anwesenheitsgrad = berechne_anwesenheitsgrad(gesamt_anwesend_h_summe, gesamt_bezahlt_h_summe) if gesamt_bezahlt_h_summe > 0 else None
    
    return gesamt_anwesenheitsgrad, mechaniker_liste


def berechne_mechaniker_kpis(
    anwesend_min: float,
    gestempelt_min: float,
    vorgabe_aw: float,
    bezahlt_h: float = None,
    tage: int = None,
    stunden_pro_tag: float = STUNDEN_PRO_TAG,
    lohnumsatz_eur: float = None,
    anzahl_auftraege: int = None
) -> Dict[str, Any]:
    """
    Berechnet alle KPIs für einen Mechaniker auf einen Schlag (SSOT).
    
    Args:
        anwesend_min: Anwesende Minuten (aus Stempelung type=1)
        gestempelt_min: Produktiv gestempelte Minuten (type=2)
        vorgabe_aw: Summe Vorgabe-AW
        bezahlt_h: Bezahlte Stunden (optional, wird aus tage berechnet falls nicht gegeben)
        tage: Anzahl Arbeitstage (optional, wird zu bezahlt_h = tage × stunden_pro_tag)
        stunden_pro_tag: Stunden pro Arbeitstag (default: 8h)
        lohnumsatz_eur: Lohnumsatz in € (optional)
        anzahl_auftraege: Anzahl Aufträge (optional)
        
    Returns:
        Dict mit allen KPIs und Bewertungen
    """
    # Bezahlte Zeit berechnen (aus tage oder direkt)
    if bezahlt_h is None:
        if tage is not None:
            bezahlt_h = tage * stunden_pro_tag
        else:
            bezahlt_h = STUNDEN_PRO_TAG  # Default: 1 Tag
    
    anwesend_h = minuten_zu_stunden(anwesend_min)
    gestempelt_h = minuten_zu_stunden(gestempelt_min)
    gestempelt_aw = minuten_zu_aw(gestempelt_min)
    verkauft_h = aw_zu_stunden(vorgabe_aw)
    
    # Einzelne KPIs
    anwesenheitsgrad = berechne_anwesenheitsgrad(anwesend_h, bezahlt_h)
    auslastungsgrad = berechne_auslastungsgrad(gestempelt_h, anwesend_h)
    leistungsgrad = berechne_leistungsgrad(vorgabe_aw, gestempelt_aw)
    effizienz = berechne_effizienz(anwesenheitsgrad, auslastungsgrad, leistungsgrad)
    
    result = {
        # Rohdaten
        'anwesend_h': anwesend_h,
        'gestempelt_h': gestempelt_h,
        'gestempelt_aw': gestempelt_aw,
        'vorgabe_aw': vorgabe_aw,
        'verkauft_h': verkauft_h,
        'bezahlt_h': bezahlt_h,
        
        # KPIs
        'anwesenheitsgrad': anwesenheitsgrad,
        'auslastungsgrad': auslastungsgrad,
        'leistungsgrad': leistungsgrad,
        'effizienz': effizienz,
        
        # Bewertungen
        'anwesenheitsgrad_status': bewerte_anwesenheitsgrad(anwesenheitsgrad),
        'auslastungsgrad_status': bewerte_auslastungsgrad(auslastungsgrad),
        'leistungsgrad_status': bewerte_leistungsgrad(leistungsgrad),
        'effizienz_status': bewerte_effizienz(effizienz),
    }
    
    # Optionale KPIs
    if anzahl_auftraege:
        result['stunden_pro_durchgang'] = berechne_stunden_pro_durchgang(verkauft_h, anzahl_auftraege)
        result['anzahl_auftraege'] = anzahl_auftraege
    
    if lohnumsatz_eur:
        result['lohnumsatz_eur'] = lohnumsatz_eur
        result['svs'] = berechne_stundenverrechnungssatz(lohnumsatz_eur, verkauft_h, gestempelt_h)
    
    return result


# =============================================================================
# FORMATIERUNG
# =============================================================================

def format_euro(betrag: float) -> str:
    """Formatiert Euro-Betrag: 1.234,56 €"""
    if betrag is None:
        return "–"
    return f"{betrag:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def format_prozent(wert: float, nachkommastellen: int = 1) -> str:
    """Formatiert Prozentwert: 85,5%"""
    if wert is None:
        return "–"
    return f"{wert:.{nachkommastellen}f}%".replace(".", ",")


def format_aw(aw: float) -> str:
    """Formatiert AW-Wert: 12,5 AW"""
    if aw is None:
        return "–"
    return f"{aw:.1f} AW".replace(".", ",")


def format_stunden(stunden: float) -> str:
    """Formatiert Stunden: 8,5 h"""
    if stunden is None:
        return "–"
    return f"{stunden:.1f} h".replace(".", ",")


def format_zeit_hhmm(minuten: float) -> str:
    """Formatiert Minuten als HH:MM"""
    if minuten is None:
        return "–"
    h = int(minuten // 60)
    m = int(minuten % 60)
    return f"{h}:{m:02d}"


# =============================================================================
# TESTS
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("WERKSTATT KPI - TESTS")
    print("=" * 60)
    
    print("\n1. EINZELNE KPIs:")
    print("-" * 40)
    
    # Anwesenheitsgrad
    ag = berechne_anwesenheitsgrad(anwesend_h=6.5, bezahlt_h=8)
    print(f"Anwesenheitsgrad (6.5h/8h): {format_prozent(ag)} (Ziel: ~79%)")
    
    # Auslastungsgrad  
    au = berechne_auslastungsgrad(gestempelt_h=5.5, anwesend_h=6.5)
    print(f"Auslastungsgrad (5.5h/6.5h): {format_prozent(au)} (Ziel: 90%)")
    
    # Leistungsgrad
    lg = berechne_leistungsgrad(vorgabe_aw=50, gestempelt_aw=55)
    print(f"Leistungsgrad (50AW/55AW): {format_prozent(lg)} (Ziel: 100%)")
    
    # Effizienz
    eff = berechne_effizienz(ag, au, lg)
    print(f"Effizienz (kombiniert): {format_prozent(eff)} (Ziel: ~71%)")
    
    print("\n2. ENTGANGENER UMSATZ:")
    print("-" * 40)
    verlust = berechne_entgangener_umsatz(vorgabe_aw=10, gestempelt_aw=12, aw_preis=11.90)
    print(f"10 AW Vorgabe, 12 AW gestempelt, 11.90€/AW: {format_euro(verlust)}")
    
    verlust2 = berechne_entgangener_umsatz(vorgabe_aw=10, gestempelt_aw=8, aw_preis=11.90)
    print(f"10 AW Vorgabe, 8 AW gestempelt (schneller!): {format_euro(verlust2)}")
    
    print("\n3. ZUSATZ-KPIs:")
    print("-" * 40)
    spd = berechne_stunden_pro_durchgang(verkauft_h=54, anzahl_auftraege=30)
    print(f"Stunden/Durchgang (54h/30 Auftr.): {format_stunden(spd)} (Schnitt: 1,8h)")
    
    svs = berechne_stundenverrechnungssatz(lohnumsatz_eur=5400, verkauft_h=54, vorgabe_h=60)
    print(f"SVS erzielt: {format_euro(svs['erzielt'])}/h")
    print(f"SVS Vorgabe: {format_euro(svs['vorgabe'])}/h")
    print(f"SVS Differenz: {format_euro(svs['differenz'])}/h")
    
    print("\n4. KOMPLETT-BERECHNUNG (Mechaniker):")
    print("-" * 40)
    kpis = berechne_mechaniker_kpis(
        anwesend_min=390,      # 6.5h
        gestempelt_min=330,    # 5.5h
        vorgabe_aw=50,
        bezahlt_h=8,
        lohnumsatz_eur=595,
        anzahl_auftraege=5
    )
    print(f"Anwesenheitsgrad: {format_prozent(kpis['anwesenheitsgrad'])} {kpis['anwesenheitsgrad_status']['icon']}")
    print(f"Auslastungsgrad:  {format_prozent(kpis['auslastungsgrad'])} {kpis['auslastungsgrad_status']['icon']}")
    print(f"Leistungsgrad:    {format_prozent(kpis['leistungsgrad'])} {kpis['leistungsgrad_status']['icon']}")
    print(f"Effizienz:        {format_prozent(kpis['effizienz'])} {kpis['effizienz_status']['icon']}")
    print(f"Std/Durchgang:    {format_stunden(kpis.get('stunden_pro_durchgang'))}")
    print(f"SVS erzielt:      {format_euro(kpis.get('svs', {}).get('erzielt'))}/h")
    
    print("\n" + "=" * 60)
    print("✅ Alle Tests erfolgreich!")
    print("=" * 60)
