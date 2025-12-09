#!/usr/bin/env python3
"""
API: Jahresprämie
================
Berechnung von Jahresprämien basierend auf Lohnjournal

Endpoints:
- GET  /api/jahrespraemie/berechnungen          - Liste aller Berechnungen
- GET  /api/jahrespraemie/berechnung/<id>       - Details einer Berechnung
- POST /api/jahrespraemie/berechnung/neu        - Neue Berechnung starten
- POST /api/jahrespraemie/upload/<id>           - Lohnjournal hochladen
- POST /api/jahrespraemie/berechnen/<id>        - Berechnung durchführen
- POST /api/jahrespraemie/kulanz/<id>           - Kulanz-Regeln setzen
- POST /api/jahrespraemie/freigeben/<id>        - Berechnung freigeben
- GET  /api/jahrespraemie/health                - Health Check
"""

from flask import Blueprint, request, jsonify
import sqlite3
import pandas as pd
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
import os
import hashlib
import tempfile

jahrespraemie_api = Blueprint('jahrespraemie_api', __name__, url_prefix='/api/jahrespraemie')

# DB-Pfad (wie andere APIs)
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'


def get_db_connection():
    """Datenbankverbindung holen"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_date(d):
    """Datum aus verschiedenen Formaten parsen"""
    if pd.isna(d) or str(d) in ['00.00.0000', 'nan', '', 'None', 'NaT']:
        return None
    try:
        d_str = str(d).split(' ')[0]
        return datetime.strptime(d_str, '%Y-%m-%d').date()
    except:
        try:
            return datetime.strptime(str(d), '%d.%m.%Y').date()
        except:
            return None


def runden_kaufmaennisch(betrag):
    """Kaufmännisch auf ganze Euro runden"""
    return int(Decimal(str(betrag)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


# ============================================================================
# PRÄMIENBERECHNUNG - KERNLOGIK
# ============================================================================

class PraemienRechner:
    """Kernklasse für die Prämienberechnung"""
    
    AZUBI_FESTBETRAEGE = {1: 100, 2: 125, 3: 150}
    
    def __init__(self, berechnung_id, conn):
        self.berechnung_id = berechnung_id
        self.conn = conn
        self.cursor = conn.cursor()
        self.berechnung = None
        self.mitarbeiter = []
        self.kulanz_regeln = []
        
    def laden(self):
        """Berechnung und Mitarbeiter laden"""
        self.cursor.execute(
            "SELECT * FROM praemien_berechnungen WHERE id = ?", 
            (self.berechnung_id,)
        )
        row = self.cursor.fetchone()
        if row:
            self.berechnung = dict(row)
            
        self.cursor.execute(
            "SELECT * FROM praemien_mitarbeiter WHERE berechnung_id = ?",
            (self.berechnung_id,)
        )
        self.mitarbeiter = [dict(row) for row in self.cursor.fetchall()]
        
        self.cursor.execute(
            "SELECT * FROM praemien_kulanz_regeln WHERE berechnung_id = ? AND aktiv = 1",
            (self.berechnung_id,)
        )
        self.kulanz_regeln = [dict(row) for row in self.cursor.fetchall()]
        
    def kategorisiere_mitarbeiter(self, row, vz_tz_grenze=30):
        """Mitarbeiter-Kategorie bestimmen"""
        std = row.get('std_woche', 0) or 0
        ang_arb = str(row.get('ang_arb', '')).lower()
        brutto_monat = (row.get('jahresbrutto', 0) or 0) / 12
        
        # Azubi erkennen
        if 'auszubild' in ang_arb or 'azubi' in ang_arb:
            if brutto_monat < 950:
                return 'Azubi_1'
            elif brutto_monat < 1050:
                return 'Azubi_2'
            else:
                return 'Azubi_3'
        
        # Minijob
        if brutto_monat < 600 and std < 15:
            return 'Minijob'
        
        # VZ/TZ nach Grenze
        if std < vz_tz_grenze:
            return 'Teilzeit'
        
        return 'Vollzeit'
    
    def pruefe_berechtigung(self, row, wj_start, wj_ende):
        """Prämienberechtigung prüfen"""
        eintritt = row.get('eintritt')
        austritt = row.get('austritt')
        
        if not eintritt:
            return False, "Kein Eintrittsdatum"
        
        if isinstance(eintritt, str):
            eintritt = parse_date(eintritt)
        if isinstance(wj_start, str):
            wj_start = parse_date(wj_start)
            
        if eintritt and wj_start and eintritt > wj_start:
            return False, f"Eintritt {eintritt} nach WJ-Start"
        
        if austritt:
            if isinstance(austritt, str):
                austritt = parse_date(austritt)
            if isinstance(wj_ende, str):
                wj_ende = parse_date(wj_ende)
            if austritt and wj_ende and austritt < wj_ende:
                return False, f"Austritt {austritt}"
        
        return True, "OK"
    
    def ist_festgehalt(self, taetigkeit):
        """Prüfen ob Festgehalt (keine variable Vergütung)"""
        if not taetigkeit:
            return True
        taet = str(taetigkeit).lower()
        if 'verkäufer' in taet or 'verkauf' in taet:
            return False
        return True
    
    def berechne(self):
        """Hauptberechnung durchführen"""
        if not self.berechnung or not self.mitarbeiter:
            return {"error": "Keine Daten geladen"}
        
        praemientopf = self.berechnung['praemientopf']
        vz_tz_grenze = self.berechnung.get('vz_tz_grenze', 30)
        wj_start = self.berechnung['wj_start']
        wj_ende = self.berechnung['wj_ende']
        
        # Schritt 1: Kategorisierung und Berechtigung
        for ma in self.mitarbeiter:
            ma['kategorie'] = self.kategorisiere_mitarbeiter(ma, vz_tz_grenze)
            ma['ist_festgehalt'] = 1 if self.ist_festgehalt(ma.get('taetigkeit')) else 0
            berechtigt, grund = self.pruefe_berechtigung(ma, wj_start, wj_ende)
            ma['ist_berechtigt'] = 1 if berechtigt else 0
            ma['berechtigung_grund'] = grund
        
        # Schritt 2: Höchstes Festgehalt ermitteln
        festgehalt_ma = [m for m in self.mitarbeiter 
                         if m['ist_berechtigt'] and m['ist_festgehalt']]
        if festgehalt_ma:
            hoechstes = max(festgehalt_ma, key=lambda x: x.get('jahresbrutto', 0) or 0)
            hoechstes_festgehalt = hoechstes.get('jahresbrutto', 0)
            hoechstes_festgehalt_ma_id = hoechstes['id']
        else:
            hoechstes_festgehalt = 0
            hoechstes_festgehalt_ma_id = None
        
        # Schritt 3: Kulanz-Regeln anwenden
        kulanz_kategorie_regeln = {r['kategorie']: r['pauschal_betrag'] 
                                   for r in self.kulanz_regeln if r['regel_typ'] == 'kategorie'}
        kulanz_individuell = {r['mitarbeiter_id']: r 
                              for r in self.kulanz_regeln if r['regel_typ'] == 'individuell'}
        
        # Schritt 4: Kulanz-Volumen berechnen
        kulanz_volumen = 0
        
        for ma_id, regel in kulanz_individuell.items():
            ma = next((m for m in self.mitarbeiter if m['id'] == ma_id), None)
            if ma and not ma['ist_berechtigt']:
                ma['ist_kulanz'] = 1
                ma['kulanz_betrag'] = regel['pauschal_betrag']
                ma['kulanz_grund'] = regel.get('beschreibung', 'Individuelle Kulanz')
                kulanz_volumen += regel['pauschal_betrag']
        
        # Zählen der berechtigten Mitarbeiter
        n_vz = len([m for m in self.mitarbeiter if m['ist_berechtigt'] and m['kategorie'] == 'Vollzeit'])
        n_tz = len([m for m in self.mitarbeiter if m['ist_berechtigt'] and m['kategorie'] == 'Teilzeit'])
        n_mj = len([m for m in self.mitarbeiter if m['ist_berechtigt'] and m['kategorie'] == 'Minijob'])
        n_azubi_1 = len([m for m in self.mitarbeiter if m['ist_berechtigt'] and m['kategorie'] == 'Azubi_1'])
        n_azubi_2 = len([m for m in self.mitarbeiter if m['ist_berechtigt'] and m['kategorie'] == 'Azubi_2'])
        n_azubi_3 = len([m for m in self.mitarbeiter if m['ist_berechtigt'] and m['kategorie'] == 'Azubi_3'])
        
        # Kulanz-Kategorien: Berechne Differenz
        for kat, pauschal in kulanz_kategorie_regeln.items():
            if kat == 'Minijob':
                azubi_fest = n_azubi_1 * 100 + n_azubi_2 * 125 + n_azubi_3 * 150
                rest = (praemientopf / 2) - azubi_fest
                divisor = n_vz + (n_tz / 3) + (n_mj / 3)
                if divisor > 0:
                    vz_normal = rest / divisor
                    mj_normal = vz_normal / 3
                    mehrkosten = n_mj * (pauschal - mj_normal)
                    kulanz_volumen += max(0, mehrkosten)
        
        # Bereinigter Topf
        bereinigter_topf = praemientopf - kulanz_volumen
        praemie_I_topf = bereinigter_topf / 2
        praemie_II_topf = bereinigter_topf / 2
        
        # Schritt 5: Berechnungsbasis für Prämie I
        berechnungsbasis = 0
        for ma in self.mitarbeiter:
            if ma['ist_berechtigt'] and ma['kategorie'] != 'Minijob' and not ma.get('ist_kulanz'):
                brutto = ma.get('jahresbrutto', 0) or 0
                gekappt = min(brutto, hoechstes_festgehalt) if hoechstes_festgehalt > 0 else brutto
                ma['jahresbrutto_gekappt'] = gekappt
                berechnungsbasis += gekappt
            else:
                ma['jahresbrutto_gekappt'] = 0
        
        # Schritt 6: Prämie I berechnen
        for ma in self.mitarbeiter:
            if ma['ist_berechtigt'] and ma['kategorie'] != 'Minijob' and not ma.get('ist_kulanz'):
                if berechnungsbasis > 0:
                    anteil = ma['jahresbrutto_gekappt'] / berechnungsbasis
                    ma['anteil_lohnsumme'] = anteil
                    ma['praemie_I'] = anteil * praemie_I_topf
                else:
                    ma['anteil_lohnsumme'] = 0
                    ma['praemie_I'] = 0
            else:
                ma['anteil_lohnsumme'] = 0
                ma['praemie_I'] = 0
        
        # Schritt 7: Prämie II berechnen
        azubi_fest = n_azubi_1 * 100 + n_azubi_2 * 125 + n_azubi_3 * 150
        mj_pauschal = kulanz_kategorie_regeln.get('Minijob')
        
        if mj_pauschal:
            rest_prokopf = praemie_II_topf - azubi_fest
            divisor = n_vz + (n_tz / 3)
        else:
            rest_prokopf = praemie_II_topf - azubi_fest
            divisor = n_vz + (n_tz / 3) + (n_mj / 3)
        
        if divisor > 0:
            vz_prokopf = rest_prokopf / divisor
            tz_prokopf = vz_prokopf / 3
            mj_prokopf = mj_pauschal if mj_pauschal else (vz_prokopf / 3)
        else:
            vz_prokopf = tz_prokopf = mj_prokopf = 0
        
        for ma in self.mitarbeiter:
            if ma.get('ist_kulanz') and ma.get('kulanz_betrag'):
                ma['praemie_II'] = ma['kulanz_betrag']
                ma['praemie_I'] = 0  # Kulanz-Empfänger nur Prämie II
            elif ma['ist_berechtigt']:
                kat = ma['kategorie']
                if kat == 'Vollzeit':
                    ma['praemie_II'] = vz_prokopf
                elif kat == 'Teilzeit':
                    ma['praemie_II'] = tz_prokopf
                elif kat == 'Minijob':
                    ma['praemie_II'] = mj_prokopf
                elif kat == 'Azubi_1':
                    ma['praemie_II'] = 100
                elif kat == 'Azubi_2':
                    ma['praemie_II'] = 125
                elif kat == 'Azubi_3':
                    ma['praemie_II'] = 150
                else:
                    ma['praemie_II'] = 0
            else:
                ma['praemie_II'] = 0
        
        # Schritt 8: Gesamtprämie und Rundung
        for ma in self.mitarbeiter:
            ma['praemie_gesamt'] = ma.get('praemie_I', 0) + ma.get('praemie_II', 0)
            ma['praemie_gerundet'] = runden_kaufmaennisch(ma['praemie_gesamt'])
        
        # Schritt 9: Ergebnisse speichern
        self.berechnung.update({
            'hoechstes_festgehalt': hoechstes_festgehalt,
            'hoechstes_festgehalt_ma_id': hoechstes_festgehalt_ma_id,
            'berechnungsbasis': berechnungsbasis,
            'kulanz_volumen': kulanz_volumen,
            'bereinigter_topf': bereinigter_topf,
            'praemie_I_topf': praemie_I_topf,
            'praemie_II_topf': praemie_II_topf,
            'prokopf_vollzeit': vz_prokopf,
            'prokopf_teilzeit': tz_prokopf,
            'prokopf_minijob': mj_prokopf,
            'anzahl_vollzeit': n_vz,
            'anzahl_teilzeit': n_tz,
            'anzahl_minijob': n_mj,
            'anzahl_azubi_1': n_azubi_1,
            'anzahl_azubi_2': n_azubi_2,
            'anzahl_azubi_3': n_azubi_3,
            'anzahl_gesamt': n_vz + n_tz + n_mj + n_azubi_1 + n_azubi_2 + n_azubi_3,
            'status': 'berechnet'
        })
        
        return {
            "berechnung": self.berechnung,
            "mitarbeiter": self.mitarbeiter
        }
    
    def speichern(self):
        """Berechnung und Mitarbeiter speichern"""
        self.cursor.execute("""
            UPDATE praemien_berechnungen SET
                hoechstes_festgehalt = ?,
                hoechstes_festgehalt_ma_id = ?,
                berechnungsbasis = ?,
                kulanz_volumen = ?,
                bereinigter_topf = ?,
                praemie_I_topf = ?,
                praemie_II_topf = ?,
                prokopf_vollzeit = ?,
                prokopf_teilzeit = ?,
                prokopf_minijob = ?,
                anzahl_vollzeit = ?,
                anzahl_teilzeit = ?,
                anzahl_minijob = ?,
                anzahl_azubi_1 = ?,
                anzahl_azubi_2 = ?,
                anzahl_azubi_3 = ?,
                anzahl_gesamt = ?,
                status = ?,
                geaendert_am = ?
            WHERE id = ?
        """, (
            self.berechnung['hoechstes_festgehalt'],
            self.berechnung['hoechstes_festgehalt_ma_id'],
            self.berechnung['berechnungsbasis'],
            self.berechnung['kulanz_volumen'],
            self.berechnung['bereinigter_topf'],
            self.berechnung['praemie_I_topf'],
            self.berechnung['praemie_II_topf'],
            self.berechnung['prokopf_vollzeit'],
            self.berechnung['prokopf_teilzeit'],
            self.berechnung['prokopf_minijob'],
            self.berechnung['anzahl_vollzeit'],
            self.berechnung['anzahl_teilzeit'],
            self.berechnung['anzahl_minijob'],
            self.berechnung['anzahl_azubi_1'],
            self.berechnung['anzahl_azubi_2'],
            self.berechnung['anzahl_azubi_3'],
            self.berechnung['anzahl_gesamt'],
            self.berechnung['status'],
            datetime.now().isoformat(),
            self.berechnung_id
        ))
        
        for ma in self.mitarbeiter:
            self.cursor.execute("""
                UPDATE praemien_mitarbeiter SET
                    kategorie = ?,
                    ist_festgehalt = ?,
                    jahresbrutto_gekappt = ?,
                    ist_berechtigt = ?,
                    berechtigung_grund = ?,
                    ist_kulanz = ?,
                    kulanz_betrag = ?,
                    kulanz_grund = ?,
                    anteil_lohnsumme = ?,
                    praemie_I = ?,
                    praemie_II = ?,
                    praemie_gesamt = ?,
                    praemie_gerundet = ?
                WHERE id = ?
            """, (
                ma['kategorie'],
                ma['ist_festgehalt'],
                ma.get('jahresbrutto_gekappt'),
                ma['ist_berechtigt'],
                ma['berechtigung_grund'],
                ma.get('ist_kulanz', 0),
                ma.get('kulanz_betrag'),
                ma.get('kulanz_grund'),
                ma.get('anteil_lohnsumme'),
                ma.get('praemie_I', 0),
                ma.get('praemie_II', 0),
                ma.get('praemie_gesamt', 0),
                ma.get('praemie_gerundet', 0),
                ma['id']
            ))
        
        self.conn.commit()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@jahrespraemie_api.route('/berechnungen', methods=['GET'])
def get_berechnungen():
    """Liste aller Berechnungen"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM praemien_berechnungen 
        ORDER BY erstellt_am DESC
    """)
    berechnungen = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"berechnungen": berechnungen})


@jahrespraemie_api.route('/berechnung/<int:id>', methods=['GET'])
def get_berechnung(id):
    """Details einer Berechnung"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM praemien_berechnungen WHERE id = ?", (id,))
    berechnung = cursor.fetchone()
    if not berechnung:
        conn.close()
        return jsonify({"error": "Berechnung nicht gefunden"}), 404
    
    berechnung = dict(berechnung)
    
    cursor.execute("""
        SELECT * FROM praemien_mitarbeiter 
        WHERE berechnung_id = ?
        ORDER BY nachname, vorname
    """, (id,))
    mitarbeiter = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT * FROM praemien_kulanz_regeln
        WHERE berechnung_id = ?
    """, (id,))
    kulanz_regeln = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        "berechnung": berechnung,
        "mitarbeiter": mitarbeiter,
        "kulanz_regeln": kulanz_regeln
    })


@jahrespraemie_api.route('/berechnung/neu', methods=['POST'])
def neue_berechnung():
    """Neue Berechnung anlegen"""
    data = request.get_json()
    
    wirtschaftsjahr = data.get('wirtschaftsjahr')
    praemientopf = data.get('praemientopf')
    wj_start = data.get('wj_start')
    wj_ende = data.get('wj_ende')
    vz_tz_grenze = data.get('vz_tz_grenze', 30)
    
    if not all([wirtschaftsjahr, praemientopf, wj_start, wj_ende]):
        return jsonify({"error": "Pflichtfelder fehlen"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM praemien_berechnungen WHERE wirtschaftsjahr = ?",
        (wirtschaftsjahr,)
    )
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": f"Berechnung für {wirtschaftsjahr} existiert bereits"}), 400
    
    cursor.execute("""
        INSERT INTO praemien_berechnungen (
            wirtschaftsjahr, wj_start, wj_ende, praemientopf, vz_tz_grenze,
            prokopf_azubi_1, prokopf_azubi_2, prokopf_azubi_3, status
        ) VALUES (?, ?, ?, ?, ?, 100, 125, 150, 'entwurf')
    """, (wirtschaftsjahr, wj_start, wj_ende, praemientopf, vz_tz_grenze))
    
    berechnung_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "berechnung_id": berechnung_id,
        "message": f"Berechnung für {wirtschaftsjahr} angelegt"
    })


@jahrespraemie_api.route('/upload/<int:berechnung_id>', methods=['POST'])
def upload_lohnjournal(berechnung_id):
    """Lohnjournal hochladen und Mitarbeiter importieren"""
    if 'file' not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Keine Datei ausgewählt"}), 400
    
    temp_path = os.path.join(tempfile.gettempdir(), file.filename)
    file.save(temp_path)
    
    try:
        df = pd.read_excel(temp_path, sheet_name='01446_Mon_AN', header=0)
        
        df_clean = df[[
            'Zeitraum', 'Personalnummer', 'Name', 'Vorname', 'Name #2',
            'Eintritt', 'Austritt', 'Std/Woche', 'Bruttobezug', 
            'Zeitraum (JJJJMM)', 'Ang/Arb/Ausz/Sons', 'Tätigkeit'
        ]].copy()
        
        df_clean.columns = [
            'zeitraum', 'pers_nr', 'name_voll', 'vorname', 'nachname',
            'eintritt', 'austritt', 'std_woche', 'bruttobezug',
            'monat', 'ang_arb', 'taetigkeit'
        ]
        
        df_clean['pers_nr'] = pd.to_numeric(df_clean['pers_nr'], errors='coerce').fillna(0).astype(int)
        df_clean['bruttobezug'] = pd.to_numeric(df_clean['bruttobezug'], errors='coerce').fillna(0)
        df_clean['monat'] = pd.to_numeric(df_clean['monat'], errors='coerce').fillna(0).astype(int)
        df_clean['std_woche'] = df_clean['std_woche'].astype(str).str.replace(',', '.').astype(float)
        
        # WJ-Monate: Sept 2024 - Aug 2025
        wj_monate = list(range(202409, 202413)) + list(range(202501, 202509))
        df_wj = df_clean[df_clean['monat'].isin(wj_monate)]
        
        ma_agg = df_wj.groupby('pers_nr').agg({
            'bruttobezug': 'sum',
            'vorname': 'first',
            'nachname': 'first',
            'eintritt': 'first',
            'austritt': 'first',
            'std_woche': 'first',
            'ang_arb': 'first',
            'taetigkeit': 'first'
        }).reset_index()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM praemien_mitarbeiter WHERE berechnung_id = ?", (berechnung_id,))
        
        for _, row in ma_agg.iterrows():
            eintritt = parse_date(row['eintritt'])
            austritt = parse_date(row['austritt'])
            
            cursor.execute("""
                INSERT INTO praemien_mitarbeiter (
                    berechnung_id, personalnummer, vorname, nachname,
                    eintritt, austritt, std_woche, taetigkeit, ang_arb, jahresbrutto
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                berechnung_id,
                str(row['pers_nr']),
                row['vorname'],
                row['nachname'],
                eintritt.isoformat() if eintritt else None,
                austritt.isoformat() if austritt else None,
                row['std_woche'],
                row['taetigkeit'],
                row['ang_arb'],
                row['bruttobezug']
            ))
        
        file_hash = hashlib.md5(open(temp_path, 'rb').read()).hexdigest()
        cursor.execute("""
            UPDATE praemien_berechnungen 
            SET lohnjournal_datei = ?, lohnjournal_hash = ?
            WHERE id = ?
        """, (file.filename, file_hash, berechnung_id))
        
        conn.commit()
        conn.close()
        
        os.remove(temp_path)
        
        return jsonify({
            "success": True,
            "mitarbeiter_count": len(ma_agg),
            "message": f"{len(ma_agg)} Mitarbeiter importiert"
        })
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": str(e)}), 500


@jahrespraemie_api.route('/berechnen/<int:berechnung_id>', methods=['POST'])
def berechne_praemien(berechnung_id):
    """Prämien berechnen"""
    conn = get_db_connection()
    
    rechner = PraemienRechner(berechnung_id, conn)
    rechner.laden()
    
    if not rechner.berechnung:
        conn.close()
        return jsonify({"error": "Berechnung nicht gefunden"}), 404
    
    if not rechner.mitarbeiter:
        conn.close()
        return jsonify({"error": "Keine Mitarbeiter vorhanden. Bitte erst Lohnjournal hochladen."}), 400
    
    ergebnis = rechner.berechne()
    rechner.speichern()
    
    conn.close()
    
    return jsonify({
        "success": True,
        "berechnung": ergebnis['berechnung'],
        "mitarbeiter_count": len(ergebnis['mitarbeiter']),
        "summe_praemien": sum(m.get('praemie_gerundet', 0) for m in ergebnis['mitarbeiter'])
    })


@jahrespraemie_api.route('/kulanz/<int:berechnung_id>', methods=['POST'])
def setze_kulanz(berechnung_id):
    """Kulanz-Regeln setzen"""
    data = request.get_json()
    regeln = data.get('regeln', [])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM praemien_kulanz_regeln WHERE berechnung_id = ?", (berechnung_id,))
    
    for regel in regeln:
        cursor.execute("""
            INSERT INTO praemien_kulanz_regeln (
                berechnung_id, regel_typ, kategorie, pauschal_betrag,
                mitarbeiter_id, beschreibung, aktiv
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (
            berechnung_id,
            regel.get('regel_typ'),
            regel.get('kategorie'),
            regel.get('pauschal_betrag'),
            regel.get('mitarbeiter_id'),
            regel.get('beschreibung')
        ))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": f"{len(regeln)} Kulanz-Regeln gespeichert"
    })


@jahrespraemie_api.route('/freigeben/<int:berechnung_id>', methods=['POST'])
def freigeben(berechnung_id):
    """Berechnung freigeben"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE praemien_berechnungen 
        SET status = 'freigegeben', freigegeben_am = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), berechnung_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "Berechnung freigegeben"
    })


@jahrespraemie_api.route('/health', methods=['GET'])
def health_check():
    """Health Check"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM praemien_berechnungen")
        count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            "status": "ok",
            "module": "jahrespraemie",
            "berechnungen": count,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "module": "jahrespraemie",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
