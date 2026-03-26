"""
eAutoseller Client
API-Client für eAutoseller Integration
"""

import json
import logging
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import re
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Projekt-Root für absoluten Credentials-Pfad (unabhängig von CWD bei Gunicorn)
_EAUTOSELLER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_CREDENTIALS_PATH = os.path.join(_EAUTOSELLER_ROOT, 'config', 'credentials.json')


def _num(val):
    """Hilfe: String/Zahl zu float oder None."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        if isinstance(val, str):
            clean = val.replace('.', '').replace(',', '.')
            try:
                return float(clean)
            except ValueError:
                pass
    return None


def _int(val):
    """Hilfe: zu int oder None."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


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
    
    # ============================================================================
    # SWAGGER API METHODS (Neue DMS API)
    # ============================================================================
    
    def get_swagger_client(self, api_key=None, client_secret=None):
        """
        Erstellt einen separaten Session-Client für die Swagger API
        
        Args:
            api_key: API-Key (falls nicht in Config)
            client_secret: Client Secret (falls nicht in Config)
            
        Returns:
            requests.Session: Session mit korrekten Headers
        """
        import os
        import json
        
        # Quelle: zuerst .env (EAUTOSELLER_API_KEY, EAUTOSELLER_CLIENT_SECRET), dann credentials.json
        api_key = (api_key or os.getenv('EAUTOSELLER_API_KEY') or '').strip()
        client_secret = (client_secret or os.getenv('EAUTOSELLER_CLIENT_SECRET') or '').strip()
        if not api_key or not client_secret:
            if os.path.exists(_CREDENTIALS_PATH):
                try:
                    with open(_CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
                        creds = json.load(f)
                        if 'eautoseller' in creds:
                            es = creds['eautoseller']
                            api_key = (api_key or es.get('api_key') or es.get('API_Key') or es.get('apiKey') or '').strip()
                            client_secret = (client_secret or es.get('client_secret') or es.get('clientSecret') or '').strip()
                    if api_key and client_secret:
                        logger.info("eautoseller swagger: credentials from %s", _CREDENTIALS_PATH)
                except Exception as e:
                    logger.warning("eautoseller swagger: could not read credentials from %s: %s", _CREDENTIALS_PATH, e)
            else:
                logger.warning("eautoseller swagger: credentials file not found: %s", _CREDENTIALS_PATH)
        else:
            logger.info("eautoseller swagger: credentials from environment (EAUTOSELLER_*)")
        
        if not api_key or not client_secret:
            raise Exception("API-Key und Client-Secret erforderlich für Swagger API")
        
        # Erstelle Session für Swagger API (Header-Namen laut Swagger: X-API-Key, X-CLIENT-KEY)
        swagger_session = requests.Session()
        swagger_session.verify = True  # SSL-Verifizierung für API
        swagger_session.headers.update({
            'X-API-Key': api_key,
            'X-CLIENT-KEY': client_secret,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'DRIVE-Portal/1.0',
            'system-id': 'DRIVE-Portal',  # max 15 Zeichen, für BWA/eAutoSeller Anzeige
        })
        
        return swagger_session
    
    def get_vehicles_swagger(self, offer_reference=None, vin=None,
                              mobile_ad_id=None, as24_ad_id=None,
                              changed_since=None, status=None, use_swagger=True):
        """
        Ruft Fahrzeugliste über Swagger API ab.
        Laut OpenAPI 2.0.40 unterstützt /dms/vehicles NUR: offerReference, vin,
        mobileAdId, as24AdId, changedSince, status (1=Aktiv, 99=Gesperrt, 199=Archiviert).
        Alle anderen Filter (Preis, km, Kraftstoff, etc.) im Backend nach dem Abruf anwenden.

        Args:
            offer_reference: Angebotsreferenz (optional)
            vin: VIN 17 Zeichen (optional)
            mobile_ad_id: Mobile.de Ad-ID (optional)
            as24_ad_id: AutoScout24 Ad-ID (optional)
            changed_since: Nur geänderte seit Datum (optional)
            status: 1=Aktiv, 99=Gesperrt, 199=Archiviert. Default 1 (Verkaufsbestand).
            use_swagger: Swagger API verwenden (True) oder HTML-Parsing (False)

        Returns:
            List[Dict]: Liste von Fahrzeugen (internes Format)
        """
        if not use_swagger:
            return self.get_vehicle_list()

        try:
            swagger_session = self.get_swagger_client()
            api_base_url = 'https://api.eautoseller.de'

            params = {}
            if offer_reference:
                params['offerReference'] = offer_reference
            if vin:
                params['vin'] = str(vin).strip()
            if mobile_ad_id:
                params['mobileAdId'] = mobile_ad_id
            if as24_ad_id:
                params['as24AdId'] = as24_ad_id
            if changed_since:
                if isinstance(changed_since, datetime):
                    params['changedSince'] = changed_since.isoformat()
                else:
                    params['changedSince'] = changed_since
            params['status'] = status if status is not None else 1  # Immer 1 = Aktiv (Verkaufsbestand)

            response = swagger_session.get(
                f"{api_base_url}/dms/vehicles",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Konvertiere API-Response zu unserem Format
            # API kann Liste oder Dict mit 'data' zurückgeben
            vehicles = []
            if isinstance(data, list):
                vehicle_list = data
            elif isinstance(data, dict):
                vehicle_list = data.get('data', [])
            else:
                vehicle_list = []
            
            for vehicle in vehicle_list:
                try:
                    vehicle_data = self._convert_swagger_vehicle(vehicle)
                    if vehicle_data:
                        vehicles.append(vehicle_data)
                except Exception as e:
                    print(f"Fehler beim Konvertieren eines Fahrzeugs: {str(e)}")
                    continue
            
            return vehicles
            
        except Exception as e:
            print(f"Swagger API Fehler: {str(e)}")
            import traceback
            traceback.print_exc()
            # Fallback zu HTML-Parsing
            print("Fallback zu HTML-Parsing...")
            return self.get_vehicle_list()
    
    def get_vehicle_details_swagger(self, vehicle_id, use_swagger=True):
        """
        Ruft Fahrzeugdetails über Swagger API ab
        
        Args:
            vehicle_id: Fahrzeug-ID
            use_swagger: Swagger API verwenden (True) oder HTML-Parsing (False)
            
        Returns:
            Dict: Fahrzeugdetails
        """
        if not use_swagger:
            # Fallback zu HTML-Parsing (nicht implementiert für Details)
            return None
        
        try:
            swagger_session = self.get_swagger_client()
            api_base_url = 'https://api.eautoseller.de'
            
            response = swagger_session.get(
                f"{api_base_url}/dms/vehicle/{vehicle_id}/details",
                params={
                    'withAdditionalInformation': 'true',
                    'resolveEquipments': 'true'
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            return self._convert_swagger_vehicle(data)
            
        except Exception as e:
            print(f"Swagger API Fehler: {str(e)}")
            return None
    
    def get_vehicle_prices_swagger(self, from_date=None, use_swagger=True):
        """
        Ruft Preise über Swagger API ab
        
        Args:
            from_date: Nur Preise seit Datum (optional)
            use_swagger: Swagger API verwenden (True) oder HTML-Parsing (False)
            
        Returns:
            List[Dict]: Liste von Fahrzeugen mit Preisen
        """
        if not use_swagger:
            # Fallback zu HTML-Parsing
            vehicles = self.get_vehicle_list()
            return [v for v in vehicles if v.get('preis')]
        
        try:
            swagger_session = self.get_swagger_client()
            api_base_url = 'https://api.eautoseller.de'
            
            params = {}
            if from_date:
                if isinstance(from_date, datetime):
                    params['from'] = from_date.isoformat()
                else:
                    params['from'] = from_date
            
            response = swagger_session.get(
                f"{api_base_url}/dms/vehicles/prices",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Konvertiere API-Response zu unserem Format
            # API kann Liste oder Dict mit 'data' zurückgeben
            vehicles = []
            if isinstance(data, list):
                vehicle_list = data
            elif isinstance(data, dict):
                vehicle_list = data.get('data', [])
            else:
                vehicle_list = []
            
            for vehicle in vehicle_list:
                try:
                    vehicle_data = self._convert_swagger_vehicle(vehicle)
                    if vehicle_data:
                        vehicles.append(vehicle_data)
                except Exception as e:
                    print(f"Fehler beim Konvertieren eines Fahrzeugs: {str(e)}")
                    continue
            
            return vehicles
            
        except Exception as e:
            print(f"Swagger API Fehler: {str(e)}")
            import traceback
            traceback.print_exc()
            # Fallback zu HTML-Parsing
            vehicles = self.get_vehicle_list()
            return [v for v in vehicles if v.get('preis')]

    def get_publications_swagger(self, statistics=True, use_swagger=True):
        """
        GET /dms/publications/vehicles/publicated?statistics=true
        Liefert pro Fahrzeug: mobilePublication (adId, link), autoscout24Publication,
        statistics (leadsTotal, leadsOpen, mobileStatistic: clicks, favorites, calls, emails, priceRating 1-5).
        """
        if not use_swagger:
            return []
        try:
            swagger_session = self.get_swagger_client()
            api_base = 'https://api.eautoseller.de'
            if os.path.exists(_CREDENTIALS_PATH):
                try:
                    with open(_CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
                        creds = json.load(f)
                        if creds.get('eautoseller', {}).get('api_base_url'):
                            api_base = creds['eautoseller']['api_base_url'].rstrip('/')
                except Exception:
                    pass
            params = {'statistics': 'true'} if statistics else {}
            r = swagger_session.get(
                f"{api_base}/dms/publications/vehicles/publicated",
                params=params,
                timeout=30
            )
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else data.get('data', [])
        except Exception as e:
            logger.warning("eAutoseller publications: %s", e)
            return []

    def get_vehicles_pending_swagger(self, use_swagger=True):
        """GET /dms/vehicles/pending – Fahrzeuge mit unvollständigen Daten."""
        if not use_swagger:
            return []
        try:
            swagger_session = self.get_swagger_client()
            api_base = 'https://api.eautoseller.de'
            if os.path.exists(_CREDENTIALS_PATH):
                try:
                    with open(_CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
                        creds = json.load(f)
                        if creds.get('eautoseller', {}).get('api_base_url'):
                            api_base = creds['eautoseller']['api_base_url'].rstrip('/')
                except Exception:
                    pass
            r = swagger_session.get(f"{api_base}/dms/vehicles/pending", timeout=30)
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else data.get('data', [])
        except Exception as e:
            logger.warning("eAutoseller pending: %s", e)
            return []

    def reservation_post_swagger(self, vehicle_id, name=None, phone=None, duration_days=7, use_swagger=True):
        """POST /dms/vehicle/{id}/reservation – Reservierung setzen."""
        if not use_swagger:
            return {'success': False, 'error': 'Swagger required'}
        try:
            swagger_session = self.get_swagger_client()
            api_base = 'https://api.eautoseller.de'
            if os.path.exists(_CREDENTIALS_PATH):
                try:
                    with open(_CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
                        creds = json.load(f)
                        if creds.get('eautoseller', {}).get('api_base_url'):
                            api_base = creds['eautoseller']['api_base_url'].rstrip('/')
                except Exception:
                    pass
            body = {}
            if name is not None:
                body['name'] = name
            if phone is not None:
                body['phone'] = phone
            if duration_days is not None:
                body['durationDays'] = duration_days
            r = swagger_session.post(
                f"{api_base}/dms/vehicle/{vehicle_id}/reservation",
                json=body if body else None,
                timeout=15
            )
            r.raise_for_status()
            return {'success': True, 'data': r.json() if r.content else {}}
        except Exception as e:
            return {'success': False, 'error': str(e)[:200]}

    def reservation_delete_swagger(self, vehicle_id, use_swagger=True):
        """DELETE /dms/vehicle/{id}/reservation – Reservierung löschen."""
        if not use_swagger:
            return {'success': False, 'error': 'Swagger required'}
        try:
            swagger_session = self.get_swagger_client()
            api_base = 'https://api.eautoseller.de'
            if os.path.exists(_CREDENTIALS_PATH):
                try:
                    with open(_CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
                        creds = json.load(f)
                        if creds.get('eautoseller', {}).get('api_base_url'):
                            api_base = creds['eautoseller']['api_base_url'].rstrip('/')
                except Exception:
                    pass
            r = swagger_session.delete(
                f"{api_base}/dms/vehicle/{vehicle_id}/reservation",
                timeout=15
            )
            r.raise_for_status()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)[:200]}

    def _convert_swagger_vehicle(self, vehicle_data):
        """
        Konvertiert Swagger API Vehicle-Format (OpenAPI 2.0.40) zu unserem Format.
        Felder aus /dms/vehicles: id, vin, offerReference, make, model, type, category,
        priceGross, professionalPriceGross, mileage, firstRegistrationDate, stockEntrance,
        transmissionType, fuel, power, exteriorColor, conditionType, status, pointOfSale, etc.
        Standzeit wird aus stockEntrance berechnet (heute - stockEntrance.date()).
        """
        try:
            converted = {}

            # --- Basis ---
            converted['id'] = vehicle_data.get('id')
            converted['offer_reference'] = vehicle_data.get('offerReference')
            converted['vin'] = (
                vehicle_data.get('vin')
                or vehicle_data.get('vehicleIdentificationNumber')
                or vehicle_data.get('identificationNumber')
                or ''
            )
            if converted['vin'] and not isinstance(converted['vin'], str):
                converted['vin'] = str(converted['vin']).strip()

            # --- Marke / Modell (make, makeId, model, modelId, type, category) ---
            if 'make' in vehicle_data:
                m = vehicle_data['make']
                converted['marke'] = m.get('name') or m.get('wording') if isinstance(m, dict) else m
            else:
                converted['marke'] = vehicle_data.get('makeName', '')
            converted['make_id'] = vehicle_data.get('makeId')
            if 'model' in vehicle_data:
                m = vehicle_data['model']
                converted['modell'] = m.get('name') or m.get('wording') if isinstance(m, dict) else m
            else:
                converted['modell'] = vehicle_data.get('modelName', '')
            converted['model_id'] = vehicle_data.get('modelId')
            converted['typ'] = vehicle_data.get('type', '')
            converted['kategorie'] = vehicle_data.get('category', '')

            # --- Preis: priceGross (Brutto), professionalPriceGross (Händlerpreis) ---
            for key, out_key in [('priceGross', 'preis'), ('professionalPriceGross', 'haendlerpreis')]:
                val = vehicle_data.get(key)
                if val is not None:
                    try:
                        converted[out_key] = float(val)
                    except (TypeError, ValueError):
                        converted[out_key] = None
            if 'preis' not in converted or converted.get('preis') is None:
                if 'price' in vehicle_data:
                    p = vehicle_data['price']
                    if isinstance(p, dict):
                        converted['preis'] = _num(p.get('gross') or p.get('value'))
                    else:
                        converted['preis'] = _num(p)
                for f in ['sellingPrice', 'priceNet', 'priceValue', 'amount']:
                    if converted.get('preis') is not None:
                        break
                    converted['preis'] = _num(vehicle_data.get(f))

            # --- Lagereingang / Standzeit: stockEntrance (date-time), KEIN separater Call ---
            stock_entrance = vehicle_data.get('stockEntrance') or vehicle_data.get('dateOfEntry') or vehicle_data.get('entryDate')
            if stock_entrance:
                try:
                    if isinstance(stock_entrance, str):
                        date_part = stock_entrance.split('T')[0].split(' ')[0]
                        for fmt in ('%Y-%m-%d', '%d.%m.%Y'):
                            try:
                                date_obj = datetime.strptime(date_part, fmt).date()
                                break
                            except ValueError:
                                date_obj = None
                        if date_obj:
                            converted['hereinnahme'] = date_obj.isoformat()
                            converted['lagereingang'] = date_obj.isoformat()
                            converted['standzeit_tage'] = (datetime.now().date() - date_obj).days
                except Exception:
                    pass
            if 'hereinnahme' not in converted:
                converted['hereinnahme'] = None
                converted['lagereingang'] = None
                converted['standzeit_tage'] = None

            # --- Laufleistung ---
            converted['km'] = _int(vehicle_data.get('mileage') or vehicle_data.get('kilometer'))

            # --- Erstzulassung: firstRegistrationDate ---
            ez = vehicle_data.get('firstRegistrationDate')
            if ez:
                if isinstance(ez, str):
                    converted['ez'] = ez[:7] if len(ez) >= 7 else ez  # YYYY-MM
                    try:
                        converted['ez_jahr'] = int(ez[:4])
                    except (TypeError, ValueError):
                        converted['ez_jahr'] = None
                else:
                    converted['ez'] = str(ez)
                    converted['ez_jahr'] = _int(ez) if isinstance(ez, (int, float)) else None
            else:
                converted['ez'] = None
                converted['ez_jahr'] = _int(vehicle_data.get('year'))

            # --- Getriebe: transmissionType.id (0=Manuell, 1=Automatik, 2=Halbautomatik) ---
            tt = vehicle_data.get('transmissionType')
            if isinstance(tt, dict):
                converted['getriebe_id'] = tt.get('id')
                converted['getriebe'] = tt.get('wording') or tt.get('name') or ''
            else:
                converted['getriebe_id'] = None
                converted['getriebe'] = vehicle_data.get('transmission', '')

            # --- Kraftstoff: fuel.id, fuel.wording ---
            fuel = vehicle_data.get('fuel')
            if isinstance(fuel, dict):
                converted['kraftstoff_id'] = fuel.get('id')
                converted['kraftstoff'] = fuel.get('wording') or fuel.get('name') or ''
            else:
                converted['kraftstoff_id'] = None
                converted['kraftstoff'] = vehicle_data.get('fuelType', '')

            # --- Leistung (kW), PS = kW * 1.36 ---
            kw = _num(vehicle_data.get('power'))
            converted['leistung_kw'] = kw
            converted['leistung_ps'] = int(kw * 1.36) if kw is not None else None

            # --- Farbe: exteriorColor.base, exteriorColor.wording, isMetallic, isMatte ---
            ec = vehicle_data.get('exteriorColor')
            if isinstance(ec, dict):
                converted['farbe_basis'] = ec.get('base', '')
                converted['farbe_wording'] = ec.get('wording') or ec.get('name') or ''
                converted['ist_metallic'] = ec.get('isMetallic', False)
                converted['ist_matte'] = ec.get('isMatte', False)
            else:
                converted['farbe_basis'] = ''
                converted['farbe_wording'] = ''
                converted['ist_metallic'] = False
                converted['ist_matte'] = False

            # --- Zustand: conditionType (NEW|DEMO|DAILY|USED|...) ---
            converted['zustand'] = vehicle_data.get('conditionType', '')
            converted['zustand_wording'] = vehicle_data.get('conditionType', '')

            # --- Status (1=Aktiv, 99=Gesperrt, 199=Archiviert) ---
            st = vehicle_data.get('status')
            if isinstance(st, dict):
                converted['status'] = st.get('id')
                converted['status_wording'] = st.get('wording') or st.get('name') or ''
            else:
                converted['status'] = st
                converted['status_wording'] = ''

            # --- Standort: pointOfSale.id, .name, .city ---
            pos = vehicle_data.get('pointOfSale')
            if isinstance(pos, dict):
                converted['standort_id'] = pos.get('id')
                converted['standort'] = pos.get('name') or pos.get('city') or ''
                converted['standort_stadt'] = pos.get('city', '')
            else:
                converted['standort_id'] = None
                converted['standort'] = ''
                converted['standort_stadt'] = ''

            converted['license_plate'] = vehicle_data.get('licensePlate', '')
            converted['last_change'] = vehicle_data.get('lastChange')
            converted['last_price_change'] = vehicle_data.get('lastPriceChange')
            converted['last_picture_change'] = vehicle_data.get('lastPictureChange')
            converted['last_file_change'] = vehicle_data.get('lastFileChange')

            # MwSt / Besteuerung (für Bewertungskatalog)
            for key in ('taxType', 'saleType', 'vatDeductible', 'invoiceType'):
                if key in vehicle_data:
                    val = vehicle_data[key]
                    if isinstance(val, bool):
                        converted['out_sale_type'] = 'F' if val else 'B'
                        break
                    s = str(val).upper()
                    if 'REGEL' in s or s == 'F' or 'JA' in s:
                        converted['out_sale_type'] = 'F'
                        break
                    if 'DIFF' in s or '25A' in s or s == 'B' or 'NEIN' in s:
                        converted['out_sale_type'] = 'B'
                        break

            for key in ('previousOwnerCount', 'ownerCount', 'numberOfOwners'):
                if key in vehicle_data:
                    try:
                        converted['vorbesitzer'] = int(vehicle_data[key])
                        break
                    except (TypeError, ValueError):
                        pass

            return converted

        except Exception as e:
            logger.exception("Fehler beim Konvertieren der Fahrzeugdaten: %s", e)
            return None

    def get_prices_suggestions_swagger(self, use_swagger=True):
        """
        GET /dms/vehicles/prices/suggestions – offizielle API für mobile.de Platzierung.
        Liefert pro Fahrzeug: current.mobilePosition, target.mobilePosition, current.priceGross, target.priceGross.
        Kein separater BWA-Call nötig; gleiche Auth wie DMS.

        Returns:
            dict vin -> {
                'mobile_platz': int (current.mobilePosition),
                'target_mobile_platz': int (target.mobilePosition),
                'platz_1_retail_gross': float (target.priceGross, Preis für bessere Platzierung),
                'current_price_gross': float,
                'target_price_gross': float,
                'error': None oder str
            }
        """
        result_by_vin = {}
        if not use_swagger:
            return result_by_vin
        try:
            swagger_session = self.get_swagger_client()
            api_base = 'https://api.eautoseller.de'
            if os.path.exists(_CREDENTIALS_PATH):
                try:
                    with open(_CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
                        creds = json.load(f)
                        if creds.get('eautoseller', {}).get('api_base_url'):
                            api_base = creds['eautoseller']['api_base_url'].rstrip('/')
                except Exception:
                    pass
            r = swagger_session.get(
                f"{api_base}/dms/vehicles/prices/suggestions",
                timeout=30
            )
            r.raise_for_status()
            data = r.json()
            items = data if isinstance(data, list) else (data.get('data') or data.get('suggestions') or [])
            if not isinstance(items, list):
                items = []
            for item in items:
                vin = (item.get('vin') or '').strip()
                if not vin or len(vin) != 17:
                    continue
                current = item.get('current') or {}
                target = item.get('target') or {}
                mobile_platz = _int(current.get('mobilePosition') or current.get('mobile_position'))
                target_platz = _int(target.get('mobilePosition') or target.get('mobile_position'))
                current_price = _num(current.get('priceGross') or current.get('price_gross'))
                target_price = _num(target.get('priceGross') or target.get('price_gross'))
                result_by_vin[vin] = {
                    'mobile_platz': mobile_platz,
                    'target_mobile_platz': target_platz,
                    'platz_1_retail_gross': target_price,
                    'current_price_gross': current_price,
                    'target_price_gross': target_price,
                    'error': None,
                }
                if vin.upper() != vin:
                    result_by_vin[vin.upper()] = result_by_vin[vin]
            return result_by_vin
        except requests.exceptions.HTTPError as e:
            code = getattr(e.response, 'status_code', None)
            url = getattr(e.response, 'url', '?')
            logger.warning("eautoseller prices/suggestions %s: %s", code, url)
            # 403 = oft „Berechtigung für diesen Endpoint fehlt“ – bei eAutoSeller freischalten lassen
            return {}
        except Exception as e:
            logger.warning("eautoseller prices/suggestions: %s", e)
            return {}

    def get_bwa_market_placement(self, vin, use_swagger=True):
        """
        Ruft für eine VIN die BWA-Evaluation (Bewerter/Marktanalyse) ab.
        Liefert mobile.de Börsenplatzierung (targetPosition) und Treffer (totalHits).
        Optional: Preis Platz 1 (erstes Valuation pricing.retailGross).
        Bevorzugt: get_prices_suggestions_swagger() (ein GET, keine BWA-Berechtigung nötig).

        Args:
            vin: 17-stellige VIN
            use_swagger: Swagger API verwenden (True)

        Returns:
            dict: {
                'mobile_platz': int oder None,   # Börsenplatz (z.B. 10)
                'total_hits': int oder None,     # Treffer (z.B. 85)
                'platz_1_retail_gross': float oder None,  # Preis Platz 1 brutto (falls vorhanden)
                'mobile_url': str oder None,
                'setup_name': str oder None,
                'error': str oder None
            }
        """
        result = {'mobile_platz': None, 'total_hits': None, 'platz_1_retail_gross': None,
                  'mobile_url': None, 'setup_name': None, 'error': None}
        if not vin or len(str(vin).strip()) != 17:
            result['error'] = 'VIN muss 17 Zeichen haben'
            return result
        vin = str(vin).strip()
        if not use_swagger:
            return result
        try:
            swagger_session = self.get_swagger_client()
            api_base = 'https://api.eautoseller.de'
            if os.path.exists(_CREDENTIALS_PATH):
                try:
                    with open(_CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
                        creds = json.load(f)
                        if creds.get('eautoseller', {}).get('api_base_url'):
                            api_base = creds['eautoseller']['api_base_url'].rstrip('/')
                except Exception:
                    pass
            # 1) Fahrzeug per VIN suchen (Liste)
            r = swagger_session.get(
                f"{api_base}/dms/vehicles",
                params={'vin': vin},
                timeout=15
            )
            r.raise_for_status()
            data = r.json()
            vehicle_list = data if isinstance(data, list) else data.get('data', [])
            if not vehicle_list:
                result['error'] = 'Fahrzeug nicht in eAutoSeller gefunden'
                return result
            vehicle_id = vehicle_list[0].get('id') if isinstance(vehicle_list[0], dict) else vehicle_list[0].get('id')
            if not vehicle_id:
                result['error'] = 'Keine Fahrzeug-ID'
                return result
            # 2) Fahrzeugdetails holen (für BWA-Body)
            r2 = swagger_session.get(
                f"{api_base}/dms/vehicle/{vehicle_id}/details",
                params={'withAdditionalInformation': 'true', 'resolveEquipments': 'true'},
                timeout=15
            )
            r2.raise_for_status()
            details = r2.json()
            # 3) BWA Evaluation (mobile.de Platzierung) – API erlaubt nur POST (GET liefert 405)
            r3 = swagger_session.post(
                f"{api_base}/bwa/evaluation",
                json=details,
                timeout=30
            )
            r3.raise_for_status()
            eval_data = r3.json()
            valuations = eval_data.get('valuation') or []
            for v in valuations:
                if not v:
                    continue
                setup = (v.get('setupName') or v.get('setup_name') or '')
                pos = v.get('targetPosition') or v.get('target_position')
                hits = v.get('totalHits') or v.get('total_hits')
                if pos is not None:
                    result['mobile_platz'] = int(pos)
                if hits is not None:
                    result['total_hits'] = int(hits)
                if v.get('mobileUrl') or v.get('mobile_url'):
                    result['mobile_url'] = v.get('mobileUrl') or v.get('mobile_url')
                if setup:
                    result['setup_name'] = setup
                pricing = v.get('pricing') or {}
                retail = pricing.get('retailGross') or pricing.get('retail_gross')
                if retail is not None and result.get('platz_1_retail_gross') is None:
                    try:
                        result['platz_1_retail_gross'] = float(retail)
                    except (TypeError, ValueError):
                        pass
                break  # erstes Valuation (meist mobile.de/Abverkauf) reicht
            return result
        except requests.exceptions.HTTPError as e:
            url = getattr(e.response, 'url', None) or '?'
            logger.warning("eautoseller BWA %s: url=%s", e.response.status_code, url)
            result['error'] = f"API {e.response.status_code}: {getattr(e.response, 'text', str(e))[:200]}"
            return result
        except Exception as e:
            result['error'] = str(e)[:200]
            return result

