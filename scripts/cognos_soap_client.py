#!/usr/bin/env python3
"""
Cognos SOAP Client
Ruft BWA-Reports direkt über Cognos SOAP API auf

Erstellt: TAG 182
Basierend auf HAR-Analyse
"""

import requests
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime, timedelta
import re
import json
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple

# Cognos Konfiguration
COGNOS_BASE_URL = "http://10.80.80.10:9300"
COGNOS_BI_URL = f"{COGNOS_BASE_URL}/bi"
COGNOS_REPORTS_URL = f"{COGNOS_BI_URL}/v1/reports"
LOGIN_USERNAME = "Greiner"
LOGIN_PASSWORD = "Hawaii#22"

# Report-ID aus HAR-Analyse
REPORT_ID = "i176278575AB142B18A70E1BDFAE95614"

# SOAP Namespaces
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
BUS_NS = "http://developer.cognos.com/schemas/bibus/3/"
RNS_NS = "http://developer.cognos.com/schemas/reportService/1"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
SOAP_ENC_NS = "http://schemas.xmlsoap.org/soap/encoding/"
XSD_NS = "http://www.w3.org/2001/XMLSchema"

# Session
session = requests.Session()
session.auth = (LOGIN_USERNAME, LOGIN_PASSWORD)  # Basic Auth
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
    'Accept': '*/*',
    'Accept-Language': 'de,de-DE;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Origin': 'http://10.80.80.10:9300',
    'Referer': 'http://10.80.80.10:9300/bi/pat/rsapp.htm',
})


class CognosSOAPClient:
    """
    Cognos SOAP Client für BWA-Reports
    """
    
    def __init__(self):
        self.session = session
        self.authenticity_token = None
        self.context_id = None
        self.xsrf_token = None
        self.logged_in = False
    
    def login(self, cookies_file: str = None) -> bool:
        """
        Login ins Cognos Portal
        
        Args:
            cookies_file: Optional: Pfad zu JSON-Datei mit Cookies aus HAR
        """
        print("=== Cognos Login ===\n")
        
        try:
            # Lade Cookies aus HAR-Datei falls vorhanden
            if cookies_file:
                try:
                    import json
                    with open(cookies_file, 'r', encoding='utf-8') as f:
                        har_cookies = json.load(f)
                    
                    # Setze Cookies in Session
                    for name, value in har_cookies.items():
                        self.session.cookies.set(name, value, domain='10.80.80.10')
                    
                    print(f"✅ Cookies aus HAR geladen: {len(har_cookies)}")
                    
                    # Extrahiere XSRF-Token
                    if 'XSRF-TOKEN' in har_cookies:
                        self.xsrf_token = har_cookies['XSRF-TOKEN']
                        print(f"✅ XSRF-Token: {self.xsrf_token[:30]}...")
                    
                except Exception as e:
                    print(f"⚠️  Fehler beim Laden der Cookies: {e}")
            
            # Schritt 1: Lade Hauptseite, um Session zu initialisieren
            print("Schritt 1: Lade Hauptseite...")
            response = self.session.get(f"{COGNOS_BI_URL}/", timeout=10)
            
            if response.status_code == 200:
                print("✅ Portal erreichbar")
                
                # Prüfe ob Login erforderlich
                if 'login' in response.url.lower() or 'anmeldung' in response.text.lower():
                    print("⚠️  Login erforderlich")
                    # Versuche Basic Auth
                    self.session.auth = (LOGIN_USERNAME, LOGIN_PASSWORD)
                    response = self.session.get(f"{COGNOS_BI_URL}/", timeout=10)
                else:
                    print("✅ Bereits eingeloggt oder kein Login erforderlich")
                
                # Schritt 2: Lade Report-App-Seite, um XSRF-Token zu bekommen
                print("\nSchritt 2: Lade Report-App-Seite...")
                app_response = self.session.get(f"{COGNOS_BI_URL}/pat/rsapp.htm", timeout=10)
                
                if app_response.status_code == 200:
                    print("✅ Report-App-Seite geladen")
                    
                    # Versuche XSRF-Token zu extrahieren
                    # Token kann in Cookies oder HTML sein
                    cookies = self.session.cookies
                    if cookies:
                        print(f"✅ Cookies in Session: {len(cookies)}")
                        for cookie in cookies:
                            if 'XSRF' in cookie.name.upper() or 'TOKEN' in cookie.name.upper():
                                print(f"   {cookie.name} = {cookie.value[:50]}...")
                                if not self.xsrf_token:
                                    self.xsrf_token = cookie.value
                    
                    # Versuche Token aus HTML zu extrahieren
                    if not self.xsrf_token:
                        import re
                        # Suche in HTML
                        token_match = re.search(r'XSRF[_-]?TOKEN["\']?\s*[:=]\s*["\']?([^"\'\s]+)', app_response.text, re.I)
                        if token_match:
                            self.xsrf_token = token_match.group(1)
                            print(f"✅ XSRF-Token aus HTML extrahiert")
                        
                        # Suche in JavaScript
                        if not self.xsrf_token:
                            js_token_match = re.search(r'["\']XSRF[_-]?TOKEN["\']\s*:\s*["\']([^"\']+)["\']', app_response.text, re.I)
                            if js_token_match:
                                self.xsrf_token = js_token_match.group(1)
                                print(f"✅ XSRF-Token aus JavaScript extrahiert")
                    
                    # Schritt 3: Warm-up Request - Lade Report-Metadaten
                    if self.xsrf_token:
                        print(f"\n✅ XSRF-Token vorhanden: {self.xsrf_token[:30]}...")
                        print("Schritt 3: Warm-up Request...")
                        
                        # Versuche Report-Metadaten abzurufen
                        try:
                            metadata_url = f"{COGNOS_BI_URL}/v1/reports/{REPORT_ID}"
                            metadata_response = self.session.get(
                                metadata_url,
                                headers={
                                    'X-XSRF-TOKEN': self.xsrf_token,
                                    'X-RsCMStoreID': REPORT_ID,
                                },
                                timeout=10
                            )
                            
                            if metadata_response.status_code == 200:
                                print("✅ Warm-up Request erfolgreich")
                            else:
                                print(f"⚠️  Warm-up Request: {metadata_response.status_code}")
                        except Exception as e:
                            print(f"⚠️  Warm-up Request fehlgeschlagen: {e}")
                        
                        self.logged_in = True
                        return True
                    else:
                        print("⚠️  XSRF-Token nicht gefunden, versuche trotzdem...")
                        self.logged_in = True
                        return True
                
                self.logged_in = True
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Fehler beim Login: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_soap_envelope(self, report_id: str, parameters: List[Dict] = None) -> str:
        """
        Erstellt SOAP-Envelope für Report-Request
        """
        # Root: Envelope
        envelope = Element('SOAP-ENV:Envelope')
        envelope.set('xmlns:SOAP-ENV', SOAP_NS)
        envelope.set('xmlns:xsi', XSI_NS)
        envelope.set('SOAP-ENV:encodingStyle', f"{SOAP_ENC_NS}")
        envelope.set('xmlns:SOAP-ENC', SOAP_ENC_NS)
        envelope.set('xmlns:xsd', XSD_NS)
        envelope.set('xmlns:xs', XSD_NS)
        envelope.set('xmlns:bus', BUS_NS)
        envelope.set('xmlns:rns1', RNS_NS)
        
        # Header
        header = SubElement(envelope, 'SOAP-ENV:Header')
        bi_bus_header = SubElement(header, 'bus:biBusHeader')
        bi_bus_header.set('xsi:type', 'bus:biBusHeader')
        
        # CAM (Authentifizierung)
        cam = SubElement(bi_bus_header, 'bus:CAM')
        cam.set('xsi:type', 'bus:CAM')
        if self.authenticity_token:
            auth_token = SubElement(cam, 'authenticityToken')
            auth_token.set('xsi:type', 'xsd:base64Binary')
            auth_token.text = self.authenticity_token
        else:
            # Default Token (wird beim ersten Request gesetzt)
            auth_token = SubElement(cam, 'authenticityToken')
            auth_token.set('xsi:type', 'xsd:base64Binary')
            auth_token.text = "VjHWOxCiNmt6Y2F9FC3K6AYFlwdUwl4WEWsVdNwCtWbQRA=="
        
        # CAF (Context)
        caf = SubElement(bi_bus_header, 'bus:CAF')
        caf.set('xsi:type', 'bus:CAF')
        if self.context_id:
            context_id = SubElement(caf, 'contextID')
            context_id.set('xsi:type', 'xsd:string')
            context_id.text = self.context_id
        else:
            # Default Context-ID (wird beim ersten Request gesetzt)
            context_id = SubElement(caf, 'contextID')
            context_id.set('xsi:type', 'xsd:string')
            context_id.text = "CAFW000000a0Q0FGQTYwMDAwMDAwMDlBaFFBQUFBR1RDRU1ib0szN3RLbDkwNnZXVUVuU3FsckFRY0FBQUJUU0VFdE1qVTJJQUFBQU1DV1dXTTRaaTdMdkpLamNNZHcxT3JpQzZhaExuNUdBVTBEOTlsTGtsdnA0OTExNzR8cnM_"
        
        # Session
        hdr_session = SubElement(bi_bus_header, 'bus:hdrSession')
        hdr_session.set('xsi:type', 'bus:hdrSession')
        form_field_vars = SubElement(hdr_session, 'bus:formFieldVars')
        form_field_vars.set('SOAP-ENC:arrayType', 'bus:formFieldVar[]')
        form_field_vars.set('xsi:type', 'SOAP-ENC:Array')
        
        # User Preferences
        user_pref_vars = SubElement(bi_bus_header, 'bus:userPreferenceVars')
        user_pref_vars.set('SOAP-ENC:arrayType', 'bus:userPreferenceVar[]')
        user_pref_vars.set('xsi:type', 'SOAP-ENC:Array')
        
        pref_item1 = SubElement(user_pref_vars, 'item')
        pref_name1 = SubElement(pref_item1, 'bus:name')
        pref_name1.set('xsi:type', 'xsd:string')
        pref_name1.text = 'productLocale'
        pref_value1 = SubElement(pref_item1, 'bus:value')
        pref_value1.set('xsi:type', 'xsd:string')
        pref_value1.text = 'de'
        
        pref_item2 = SubElement(user_pref_vars, 'item')
        pref_name2 = SubElement(pref_item2, 'bus:name')
        pref_name2.set('xsi:type', 'xsd:string')
        pref_name2.text = 'contentLocale'
        pref_value2 = SubElement(pref_item2, 'bus:value')
        pref_value2.set('xsi:type', 'xsd:string')
        pref_value2.text = 'de'
        
        # Dispatcher Transport Vars
        dispatcher_vars = SubElement(bi_bus_header, 'bus:dispatcherTransportVars')
        dispatcher_vars.set('xsi:type', 'SOAP-ENC:Array')
        dispatcher_vars.set('SOAP-ENC:arrayType', 'bus:dispatcherTransportVar[]')
        
        dispatcher_item = SubElement(dispatcher_vars, 'item')
        dispatcher_item.set('xsi:type', 'bus:dispatcherTransportVar')
        dispatcher_name = SubElement(dispatcher_item, 'name')
        dispatcher_name.set('xsi:type', 'xsd:string')
        dispatcher_name.text = 'rs'
        dispatcher_value = SubElement(dispatcher_item, 'value')
        dispatcher_value.set('xsi:type', 'xsd:string')
        dispatcher_value.text = 'true'
        
        # Body
        body = SubElement(envelope, 'SOAP-ENV:Body')
        run = SubElement(body, 'rns1:run')
        
        # Object Path (Report-ID)
        object_path = SubElement(run, 'bus:objectPath')
        object_path.set('xsi:type', 'bus:searchPathSingleObject')
        object_path.text = f'storeID("{report_id}")'
        
        # Parameter Values
        param_values = SubElement(run, 'bus:parameterValues')
        param_values.set('xmlns:bus', BUS_NS)
        param_values.set('xmlns:xsi', XSI_NS)
        param_values.set('xmlns:SOAP-ENC', SOAP_ENC_NS)
        
        if parameters:
            param_values.set('SOAP-ENC:arrayType', f'bus:parameterValue[{len(parameters)}]')
            param_values.set('xsi:type', 'SOAP-ENC:Array')
            
            for param in parameters:
                param_item = SubElement(param_values, 'item')
                param_item.set('xsi:type', 'bus:parameterValue')
                
                param_name = SubElement(param_item, 'bus:name')
                param_name.set('xsi:type', 'xsd:string')
                param_name.text = param['name']
                
                param_value = SubElement(param_item, 'bus:value')
                param_value.set('SOAP-ENC:arrayType', 'bus:simpleParameterValue[1]')
                param_value.set('xsi:type', 'SOAP-ENC:Array')
                
                simple_param = SubElement(param_value, 'item')
                simple_param.set('xsi:type', 'bus:simpleParameterValue')
                
                param_use = SubElement(simple_param, 'bus:use')
                param_use.set('xsi:type', 'xsd:string')
                param_use.text = param['use']
                
                param_display = SubElement(simple_param, 'bus:display')
                param_display.set('xsi:type', 'xsd:string')
                param_display.text = param['display']
        else:
            param_values.set('SOAP-ENC:arrayType', 'bus:parameterValue[]')
            param_values.set('xsi:type', 'SOAP-ENC:Array')
        
        # Options
        options = SubElement(run, 'bus:options')
        options.set('SOAP-ENC:arrayType', 'bus:option[]')
        options.set('xsi:type', 'SOAP-ENC:Array')
        
        # Output Format
        output_format_item = SubElement(options, 'item')
        output_format_item.set('xsi:type', 'bus:runOptionStringArray')
        output_format_name = SubElement(output_format_item, 'bus:name')
        output_format_name.set('xsi:type', 'bus:runOptionEnum')
        output_format_name.text = 'outputFormat'
        output_format_value = SubElement(output_format_item, 'bus:value')
        output_format_value.set('SOAP-ENC:arrayType', 'xsd:string[1]')
        output_format_value.set('xsi:type', 'SOAP-ENC:Array')
        output_format_item2 = SubElement(output_format_value, 'item')
        output_format_item2.text = 'XHTML'
        
        # Return Output When Available
        return_output_item = SubElement(options, 'item')
        return_output_item.set('xsi:type', 'bus:runOptionBoolean')
        return_output_name = SubElement(return_output_item, 'bus:name')
        return_output_name.set('xsi:type', 'bus:runOptionEnum')
        return_output_name.text = 'returnOutputWhenAvailable'
        return_output_value = SubElement(return_output_item, 'bus:value')
        return_output_value.set('xsi:type', 'xsd:boolean')
        return_output_value.text = 'true'
        
        # XSL Parameters
        xsl_params_item = SubElement(options, 'item')
        xsl_params_item.set('xsi:type', 'bus:runOptionNameValueArray')
        xsl_params_name = SubElement(xsl_params_item, 'bus:name')
        xsl_params_name.set('xsi:type', 'bus:runOptionEnum')
        xsl_params_name.text = 'xslParameters'
        xsl_params_value = SubElement(xsl_params_item, 'bus:value')
        xsl_params_value.set('SOAP-ENC:arrayType', 'bus:nameValue[]')
        xsl_params_value.set('xsi:type', 'SOAP-ENC:Array')
        
        cv_gateway_item = SubElement(xsl_params_value, 'item')
        cv_gateway_item.set('xsi:type', 'bus:nameValue')
        cv_gateway_name = SubElement(cv_gateway_item, 'name')
        cv_gateway_name.set('xsi:type', 'xsd:string')
        cv_gateway_name.text = 'CVGateway'
        cv_gateway_value = SubElement(cv_gateway_item, 'value')
        cv_gateway_value.set('xsi:type', 'xsd:string')
        cv_gateway_value.text = '../v1/disp'
        
        # Convert to string
        xml_str = tostring(envelope, encoding='unicode')
        return xml_str
    
    def _format_date_range(self, monat: int, jahr: int) -> Tuple[str, str]:
        """
        Formatiert Datumsbereich für Cognos (YYYYMMDD-YYYYMMDD)
        """
        # Erster Tag des Monats
        date_from = datetime(jahr, monat, 1)
        # Letzter Tag des Monats
        if monat == 12:
            date_to = datetime(jahr + 1, 1, 1) - timedelta(days=1)
        else:
            date_to = datetime(jahr, monat + 1, 1) - timedelta(days=1)
        
        date_from_str = date_from.strftime('%Y%m%d')
        date_to_str = date_to.strftime('%Y%m%d')
        
        return date_from_str, date_to_str
    
    def _get_standort_code(self, standort: str) -> str:
        """
        Konvertiert Standort-Name zu Cognos-Code
        """
        standort_mapping = {
            '1': '00',  # Deggendorf Opel
            '2': '01',  # Deggendorf Hyundai
            '3': '02',  # Landau
            'deggendorf': '00',
            'deggendorf_opel': '00',
            'deggendorf_hyundai': '01',
            'hyundai': '01',
            'landau': '02',
        }
        
        return standort_mapping.get(standort.lower(), standort)
    
    def _get_standort_display(self, standort: str) -> str:
        """
        Konvertiert Standort-Name zu Display-Name
        """
        display_mapping = {
            '1': 'Deggendorf',
            '2': 'Deggendorf HYU',
            '3': 'Landau',
            '00': 'Deggendorf',
            '01': 'Deggendorf HYU',
            '02': 'Landau',
            'deggendorf': 'Deggendorf',
            'deggendorf_opel': 'Deggendorf',
            'deggendorf_hyundai': 'Deggendorf HYU',
            'hyundai': 'Deggendorf HYU',
            'landau': 'Landau',
        }
        
        return display_mapping.get(standort.lower(), standort)
    
    def _get_monat_display(self, monat: int, jahr: int) -> str:
        """
        Konvertiert Monat/Jahr zu Display-Name
        """
        monate = ['', 'Jan.', 'Feb.', 'Mär.', 'Apr.', 'Mai', 'Jun.', 
                 'Jul.', 'Aug.', 'Sep.', 'Okt.', 'Nov.', 'Dez.']
        return f"{monate[monat]}/{jahr}"
    
    def get_bwa_report(self, monat: int = None, jahr: int = None, 
                      standort: str = None, xsrf_token: str = None) -> Optional[Dict]:
        """
        Ruft BWA-Report ab
        
        Args:
            monat: Monat (1-12), None = aktueller Monat
            jahr: Jahr, None = aktuelles Jahr
            standort: Standort ('1', '2', '3', '00', '01', '02', oder Name)
            xsrf_token: XSRF-Token für Authentifizierung
        
        Returns:
            Dict mit Response-Daten oder None
        """
        print(f"\n=== BWA-Report abrufen ===")
        print(f"Monat: {monat}, Jahr: {jahr}, Standort: {standort}\n")
        
        # Default-Werte
        if monat is None:
            monat = datetime.now().month
        if jahr is None:
            jahr = datetime.now().year
        
        # Parameter erstellen
        parameters = []
        
        # Zeit-Parameter
        date_from, date_to = self._format_date_range(monat, jahr)
        zeit_use = f"[F_Belege].[Zeit].[Zeit].[Monat]->:[PC].[@MEMBER].[{date_from}-{date_to}]"
        zeit_display = self._get_monat_display(monat, jahr)
        
        parameters.append({
            'name': '[F_Belege].[Zeit].[Zeit].[Monat]',
            'use': zeit_use,
            'display': zeit_display
        })
        
        # Standort-Parameter (falls angegeben)
        if standort:
            standort_code = self._get_standort_code(standort)
            standort_display = self._get_standort_display(standort)
            standort_use = f"[AH-Gruppe].[Betrieb]->:[PC].[@MEMBER].[{standort_code}]"
            
            parameters.append({
                'name': '[AH-Gruppe].[Betrieb]',
                'use': standort_use,
                'display': standort_display
            })
        
        # SOAP-Envelope erstellen
        soap_envelope = self._create_soap_envelope(REPORT_ID, parameters)
        
        # Headers für Request
        request_headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://www.ibm.com/xmlns/prod/cognos/reportService/202004/',
            'X-RsCMStoreID': REPORT_ID,
            'X-UseRsConsumerMode': 'true',
            'Origin': 'http://10.80.80.10:9300',
            'Referer': 'http://10.80.80.10:9300/bi/pat/rsapp.htm',
        }
        
        # Verwende XSRF-Token aus Session falls nicht übergeben
        if not xsrf_token:
            xsrf_token = self.xsrf_token
        
        if xsrf_token:
            request_headers['X-XSRF-TOKEN'] = xsrf_token
        
        # Request senden
        try:
            print(f"Sende SOAP-Request...")
            print(f"URL: {COGNOS_REPORTS_URL}")
            print(f"XSRF-Token: {xsrf_token[:30] if xsrf_token else 'NICHT GESETZT'}...")
            print(f"Cookies: {len(self.session.cookies)}")
            
            response = self.session.post(
                COGNOS_REPORTS_URL,
                data=soap_envelope.encode('utf-8'),
                headers=request_headers,
                timeout=60
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Request erfolgreich\n")
                return {
                    'status': 'success',
                    'content': response.text,
                    'headers': dict(response.headers),
                    'parameters': parameters
                }
            else:
                print(f"❌ Fehler: Status {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
                # Prüfe ob XSRF-Token benötigt wird
                if response.status_code == 441 or 'XSRF' in response.text:
                    print("\n⚠️  XSRF-Token möglicherweise erforderlich")
                    print("   Versuche Session zu initialisieren...")
                
                return None
                
        except Exception as e:
            print(f"❌ Fehler beim Request: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_multipart_response(self, response_text: str) -> Dict:
        """
        Parst multipart/related Response
        """
        # Suche Boundary
        boundary_match = re.search(r'boundary=([^\s;]+)', response_text[:500], re.I)
        if not boundary_match:
            # Versuche Boundary aus Response zu extrahieren
            boundary_match = re.search(r'^--([^\r\n]+)', response_text)
        
        if not boundary_match:
            return {'error': 'Boundary nicht gefunden'}
        
        boundary = boundary_match.group(1)
        parts = response_text.split(f'--{boundary}')
        
        result = {
            'parts': [],
            'html': None,
            'xml': None
        }
        
        for i, part in enumerate(parts[1:-1], 1):  # Erste und letzte sind leer
            if '\r\n\r\n' in part:
                header, body = part.split('\r\n\r\n', 1)
            elif '\n\n' in part:
                header, body = part.split('\n\n', 1)
            else:
                continue
            
            part_info = {
                'index': i,
                'header': header,
                'body_size': len(body),
                'content_type': None
            }
            
            # Extrahiere Content-Type
            content_type_match = re.search(r'Content-Type:\s*([^\r\n]+)', header, re.I)
            if content_type_match:
                part_info['content_type'] = content_type_match.group(1).strip()
            
            # Speichere HTML und XML
            if 'text/html' in part_info.get('content_type', '').lower():
                result['html'] = body
                part_info['type'] = 'html'
            elif 'text/xml' in part_info.get('content_type', '').lower() or body.strip().startswith('<?xml'):
                result['xml'] = body
                part_info['type'] = 'xml'
            
            result['parts'].append(part_info)
        
        return result


def main():
    """
    Test-Funktion
    """
    print("=" * 80)
    print("Cognos SOAP Client - Test")
    print("=" * 80)
    
    client = CognosSOAPClient()
    
    # Login mit Cookies aus HAR
    cookies_file = "/tmp/cognos_cookies.json"
    if not client.login(cookies_file=cookies_file):
        print("⚠️  Login mit HAR-Cookies fehlgeschlagen, versuche ohne...")
        if not client.login():
            print("❌ Login fehlgeschlagen")
            return
    
    # Test: BWA-Report für Dezember 2025, alle Standorte
    print("\n" + "=" * 80)
    print("Test 1: Dezember 2025, alle Standorte")
    print("=" * 80)
    
    result = client.get_bwa_report(monat=12, jahr=2025, xsrf_token=client.xsrf_token)
    
    if result:
        # Parse Response
        parsed = client.parse_multipart_response(result['content'])
        
        print(f"\nGefundene Parts: {len(parsed.get('parts', []))}")
        if parsed.get('html'):
            print(f"✅ HTML-Part gefunden ({len(parsed['html'])} Zeichen)")
            # Speichere HTML
            with open('/tmp/cognos_bwa_html_test.html', 'w', encoding='utf-8') as f:
                f.write(parsed['html'])
            print(f"💾 HTML gespeichert: /tmp/cognos_bwa_html_test.html")
        
        if parsed.get('xml'):
            print(f"✅ XML-Part gefunden ({len(parsed['xml'])} Zeichen)")
    
    # Test: BWA-Report für Dezember 2025, Landau
    print("\n" + "=" * 80)
    print("Test 2: Dezember 2025, Landau")
    print("=" * 80)
    
    result = client.get_bwa_report(monat=12, jahr=2025, standort='3', xsrf_token=client.xsrf_token)
    
    if result:
        parsed = client.parse_multipart_response(result['content'])
        print(f"✅ Response geparst: {len(parsed.get('parts', []))} Parts")
        if parsed.get('html'):
            print(f"✅ HTML-Part: {len(parsed['html'])} Zeichen")


if __name__ == '__main__':
    main()
