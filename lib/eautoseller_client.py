"""
eAutoseller Client
API-Client für eAutoseller Integration
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import re
import warnings
warnings.filterwarnings('ignore')

class EAutosellerClient:
    """Client für eAutoseller API-Zugriff"""
    
    BASE_URL = "https://greiner.eautoseller.de/"
    
    def __init__(self, username, password, loginbereich='kfz'):
        """
        Initialisiert eAutoseller Client
        
        Args:
            username: eAutoseller Benutzername
            password: eAutoseller Passwort
            loginbereich: Login-Bereich (default: 'kfz')
        """
        self.username = username
        self.password = password
        self.loginbereich = loginbereich
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        self._logged_in = False
    
    def login(self):
        """Login zu eAutoseller"""
        try:
            # Login-Seite laden
            resp = self.session.get(self.BASE_URL)
            soup = BeautifulSoup(resp.text, 'html.parser')
            form = soup.find('form')
            
            if not form:
                raise Exception("Login-Formular nicht gefunden")
            
            # Login-Daten sammeln
            login_data = {}
            for field in form.find_all(['input', 'select']):
                name = field.get('name')
                if not name:
                    continue
                
                if field.name == 'select':
                    options = field.find_all('option')
                    if options:
                        # Loginbereich setzen
                        for opt in options:
                            if opt.get('value', '').lower() == self.loginbereich.lower():
                                login_data[name] = opt.get('value', opt.text.strip())
                                break
                        if name not in login_data:
                            login_data[name] = options[0].get('value', options[0].text.strip())
                elif field.get('type') == 'text' and 'user' in name.lower():
                    login_data[name] = self.username
                elif field.get('type') == 'password':
                    login_data[name] = self.password
                elif field.get('type') == 'checkbox' and field.get('checked'):
                    login_data[name] = field.get('value', '1')
            
            # Login durchführen
            login_url = urljoin(self.BASE_URL, form.get('action', 'login.asp'))
            resp = self.session.post(login_url, data=login_data)
            
            # Prüfe ob Login erfolgreich
            if 'err=' in resp.url:
                raise Exception(f"Login fehlgeschlagen: {resp.url}")
            
            self._logged_in = True
            return True
            
        except Exception as e:
            self._logged_in = False
            raise Exception(f"Login-Fehler: {str(e)}")
    
    def ensure_login(self):
        """Stellt sicher, dass eingeloggt ist"""
        if not self._logged_in:
            self.login()
    
    def get_vehicle_list(self, active_only=True, fetch_hereinnahme=False):
        """
        Ruft Fahrzeugliste ab
        
        Args:
            active_only: Nur aktive Fahrzeuge (default: True)
            fetch_hereinnahme: Hereinnahme-Datum aus Detail-Seiten abrufen (default: False, langsamer)
            
        Returns:
            List[Dict]: Liste von Fahrzeugen mit Details
        """
        self.ensure_login()
        
        # kfzuebersicht.asp aufrufen
        params = {'start': '1'}
        if active_only:
            params['txtAktiv'] = '1'
        
        url = urljoin(self.BASE_URL, 'administration/kfzuebersicht.asp')
        resp = self.session.get(url, params=params, timeout=15)
        
        if resp.status_code != 200:
            raise Exception(f"Fehler beim Abrufen der Fahrzeugliste: {resp.status_code}")
        
        # HTML parsen
        soup = BeautifulSoup(resp.text, 'html.parser')
        vehicles = []
        
        # STRATEGIE 1: Suche nach Links zu Fahrzeugdetails und extrahiere Daten aus Tabellenzeilen
        vehicle_links = soup.find_all('a', href=re.compile(r'kfzdetail\.asp\?kfzID=', re.I))
        
        for link in vehicle_links:
            # Gehe zur übergeordneten Tabellenzeile
            row = link.find_parent('tr')
            if not row:
                continue
            
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                continue
            
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Extrahiere Fahrzeugdaten
            vehicle_data = self._extract_vehicle_from_row(cell_texts, link)
            if vehicle_data and vehicle_data.get('marke') and len(vehicle_data.get('marke', '')) < 50:
                # Hierinnahme-Datum aus Detail-Seite abrufen (optional)
                if fetch_hereinnahme and not vehicle_data.get('hereinnahme'):
                    detail_href = link.get('href', '')
                    if detail_href:
                        hereinnahme = self._get_hereinnahme_from_detail(detail_href)
                        if hereinnahme:
                            vehicle_data['hereinnahme'] = hereinnahme.isoformat()
                            vehicle_data['standzeit_tage'] = (datetime.now().date() - hereinnahme).days
                
                vehicles.append(vehicle_data)
        
        # STRATEGIE 2: Falls keine Links gefunden, suche nach Tabellen mit vielen Spalten
        if not vehicles:
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                # Analysiere Header
                header_row = rows[0]
                header_cells = header_row.find_all(['th', 'td'])
                header_texts = [h.get_text(strip=True).lower() for h in header_cells]
                
                # Finde Spalten-Indizes
                marke_idx = None
                modell_idx = None
                preis_idx = None
                hereinnahme_idx = None
                
                for i, header in enumerate(header_texts):
                    if 'marke' in header or 'hersteller' in header:
                        marke_idx = i
                    elif 'modell' in header or 'typ' in header:
                        modell_idx = i
                    elif 'preis' in header or 'verkauf' in header:
                        preis_idx = i
                    elif 'hereinnahme' in header or 'aufnahme' in header or 'datum' in header:
                        hereinnahme_idx = i
                
                # Wenn relevante Spalten gefunden, parse Datenzeilen
                if marke_idx is not None or len(header_cells) > 10:
                    for row in rows[1:]:  # Überspringe Header
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 3:
                            continue
                        
                        cell_texts = [cell.get_text(strip=True) for cell in cells]
                        
                        # Extrahiere mit bekannten Indizes
                        vehicle_data = {}
                        
                        if marke_idx is not None and marke_idx < len(cell_texts):
                            vehicle_data['marke'] = cell_texts[marke_idx]
                        else:
                            vehicle_data['marke'] = cell_texts[0] if len(cell_texts) > 0 else ''
                        
                        if modell_idx is not None and modell_idx < len(cell_texts):
                            vehicle_data['modell'] = cell_texts[modell_idx]
                        elif len(cell_texts) > 1:
                            vehicle_data['modell'] = cell_texts[1]
                        else:
                            vehicle_data['modell'] = ''
                        
                        # Preis
                        if preis_idx is not None and preis_idx < len(cell_texts):
                            price_text = cell_texts[preis_idx]
                        else:
                            price_text = None
                            for text in cell_texts:
                                if '€' in text:
                                    price_text = text
                                    break
                        
                        if price_text:
                            price_match = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', price_text.replace('.', '').replace(',', '.'))
                            if price_match:
                                try:
                                    vehicle_data['preis'] = float(price_match.group(1).replace('.', '').replace(',', '.'))
                                except:
                                    vehicle_data['preis'] = None
                            else:
                                vehicle_data['preis'] = None
                        else:
                            vehicle_data['preis'] = None
                        
                        # Hereinnahme
                        if hereinnahme_idx is not None and hereinnahme_idx < len(cell_texts):
                            date_text = cell_texts[hereinnahme_idx]
                        else:
                            date_text = None
                            for text in cell_texts:
                                date_match = re.search(r'(\d{2})[.-](\d{2})[.-](\d{4})', text)
                                if date_match:
                                    date_text = text
                                    break
                        
                        if date_text:
                            date_match = re.search(r'(\d{2})[.-](\d{2})[.-](\d{4})', date_text)
                            if date_match:
                                try:
                                    day, month, year = date_match.groups()
                                    hereinnahme = datetime(int(year), int(month), int(day)).date()
                                    vehicle_data['hereinnahme'] = hereinnahme.isoformat()
                                    vehicle_data['standzeit_tage'] = (datetime.now().date() - hereinnahme).days
                                except:
                                    vehicle_data['hereinnahme'] = None
                                    vehicle_data['standzeit_tage'] = None
                            else:
                                vehicle_data['hereinnahme'] = None
                                vehicle_data['standzeit_tage'] = None
                        else:
                            vehicle_data['hereinnahme'] = None
                            vehicle_data['standzeit_tage'] = None
                        
                        # Nur hinzufügen wenn mindestens Marke oder Modell vorhanden
                        if vehicle_data.get('marke') and len(vehicle_data['marke']) < 50:
                            # Prüfe ob es keine Filter-Optionen sind (lange Strings)
                            if not any(len(t) > 100 for t in cell_texts[:5]):
                                vehicles.append(vehicle_data)
        
        return vehicles
    
    def _extract_vehicle_from_row(self, cell_texts, link=None):
        """Extrahiert Fahrzeugdaten aus einer Tabellenzeile"""
        vehicle_data = {}
        
        # Basierend auf der Analyse: Spalte 0 = IntNr, Spalte 1 = Marke, Spalte 2 = Modell, Spalte 7 = Preis
        if len(cell_texts) < 8:
            return None
        
        # Spalte 0: IntNr (kann ignoriert werden oder als ID verwendet werden)
        intnr = cell_texts[0] if len(cell_texts) > 0 else ''
        
        # Spalte 1: Marke (z.B. "OpelVers.:DE")
        if len(cell_texts) > 1:
            marke_full = cell_texts[1]
            # Extrahiere Marke (vor "Vers" oder "Vers.:DE")
            # Entferne "Vers", "Vers.:DE", etc.
            marke_clean = re.sub(r'Vers.*$', '', marke_full, flags=re.I).strip()
            if marke_clean:
                vehicle_data['marke'] = marke_clean
            else:
                # Fallback: Nimm ersten Teil
                vehicle_data['marke'] = marke_full.split()[0] if marke_full else ''
        else:
            return None
        
        # Prüfe ob es keine Filter-Optionen sind
        if any(keyword in vehicle_data['marke'].lower() for keyword in ['alle', 'filter', 'suche', 'auswahl']):
            return None
        
        # Spalte 2: Modell (z.B. "Corsa 1.2 Turbo GS NKleinwagenEx-Mietwagen")
        if len(cell_texts) > 2:
            modell_full = cell_texts[2]
            # Extrahiere Modell (erste Wörter vor "NKleinwagen" oder ähnlich)
            modell_match = re.match(r'^([A-Za-z0-9\s\.\-]+?)(?:N[A-Z]|$)', modell_full)
            if modell_match:
                vehicle_data['modell'] = modell_match.group(1).strip()
            else:
                # Fallback: Nimm ersten Teil
                vehicle_data['modell'] = modell_full.split('N')[0].strip() if 'N' in modell_full else modell_full[:30]
        else:
            vehicle_data['modell'] = ''
        
        # Spalte 7: Preis (z.B. "19.980 €netto: 16.790")
        price = None
        if len(cell_texts) > 7:
            price_text = cell_texts[7]
            # Suche nach Preis mit €
            price_match = re.search(r'(\d{1,3}(?:\.\d{3})*)\s*€', price_text)
            if price_match:
                try:
                    price = float(price_match.group(1).replace('.', ''))
                except:
                    pass
        
        # Fallback: Suche in allen Spalten nach Preis
        if price is None:
            for text in cell_texts:
                if '€' in text:
                    price_match = re.search(r'(\d{1,3}(?:\.\d{3})*)\s*€', text)
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace('.', ''))
                            break
                        except:
                            pass
        
        vehicle_data['preis'] = price
        
        # Spalte 5: KM (kann als zusätzliche Info gespeichert werden)
        if len(cell_texts) > 5:
            km_text = cell_texts[5]
            km_match = re.search(r'(\d{1,3}(?:\.\d{3})*)', km_text)
            if km_match:
                try:
                    vehicle_data['km'] = int(km_match.group(1).replace('.', ''))
                except:
                    pass
        
        # Hereinnahme: Wird möglicherweise nicht in der Übersicht angezeigt
        # Versuche es trotzdem in allen Spalten zu finden
        hereinnahme = None
        for text in cell_texts:
            date_match = re.search(r'(\d{2})[.-](\d{2})[.-](\d{4})', text)
            if date_match:
                try:
                    day, month, year = date_match.groups()
                    hereinnahme = datetime(int(year), int(month), int(day)).date()
                    break
                except:
                    pass
        
        if hereinnahme:
            vehicle_data['hereinnahme'] = hereinnahme.isoformat()
            vehicle_data['standzeit_tage'] = (datetime.now().date() - hereinnahme).days
        else:
            vehicle_data['hereinnahme'] = None
            vehicle_data['standzeit_tage'] = None
        
        # IntNr als ID speichern
        if intnr:
            vehicle_data['intnr'] = intnr[:20]  # Kürze auf 20 Zeichen
        
        return vehicle_data
    
    def _get_hereinnahme_from_detail(self, detail_href):
        """
        Extrahiert Hereinnahme-Datum aus Fahrzeugdetail-Seite
        
        Args:
            detail_href: Relativer oder absoluter Link zur Detail-Seite
            
        Returns:
            date: Hereinnahme-Datum oder None
        """
        try:
            # URL zusammenbauen
            if detail_href.startswith('http'):
                detail_url = detail_href
            else:
                detail_url = urljoin(self.BASE_URL, 'administration/' + detail_href.lstrip('/'))
            
            # Detail-Seite abrufen
            resp = self.session.get(detail_url, timeout=10)
            if resp.status_code != 200:
                return None
            
            # HTML parsen
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Suche nach verstecktem Input-Feld "hfHereinnahme"
            hereinnahme_input = soup.find('input', {'name': 'hfHereinnahme'})
            if hereinnahme_input:
                date_value = hereinnahme_input.get('value', '')
                if date_value:
                    # Parse Datum (Format: DD.MM.YYYY)
                    date_match = re.match(r'(\d{2})[.-](\d{2})[.-](\d{4})', date_value)
                    if date_match:
                        try:
                            day, month, year = date_match.groups()
                            return datetime(int(year), int(month), int(day)).date()
                        except:
                            pass
            
            return None
        except:
            return None
    
    def get_dashboard_kpis(self):
        """
        Ruft Dashboard-KPIs ab
        
        Returns:
            Dict: KPIs mit verschiedenen Widget-IDs
        """
        self.ensure_login()
        
        # Time-Parameter aus start.asp extrahieren
        start_resp = self.session.get(urljoin(self.BASE_URL, 'administration/start.asp'))
        time_match = re.search(r'startdata\.asp\?id=\d+&time=(\d+)', start_resp.text)
        time_param = time_match.group(1) if time_match else str(int(datetime.now().timestamp()))
        
        # Bekannte Widget-IDs
        widget_ids = [201, 202, 203, 204, 205, 206, 207, 210, 211, 212, 215, 225, 226, 228, 229, 231]
        
        kpis = {}
        
        for widget_id in widget_ids:
            try:
                url = urljoin(self.BASE_URL, f'administration/startdata.asp?id={widget_id}&time={time_param}')
                resp = self.session.get(url, timeout=5)
                
                if resp.status_code == 200:
                    data = resp.text.strip()
                    if data and data != "NoWarnCookie Found":
                        # Pipe-separated Werte
                        values = data.split('|')
                        kpis[f'widget_{widget_id}'] = {
                            'raw': data,
                            'values': values,
                            'count': len(values)
                        }
            except:
                pass
        
        return kpis

