#!/usr/bin/env python3
"""
Leasys Rate Calculator - Direkte API-Integration
Berechnet Leasingraten über die OData API
"""

import requests
import json
from datetime import datetime

class LeasysRateCalculator:
    """Berechnet Leasingraten direkt über die Leasys OData API."""
    
    BASE_URL = "https://e-touch.leasys.com/sap/opu/odata/sap/ZNFC_P23_SRV"
    
    # Standard-Parameter (aus HAR-Analyse)
    DEFAULT_PARAMS = {
        "salesAreaCode": "O 50020901",
        "quotTypeCode": "ZEV7",
        "distrChannelCode": "I2",
        "bpId": "1186289565",  # Autohaus Greiner
        "salesMngId": "1185834152",
        "brandCode": "000020",  # OPEL
    }
    
    def __init__(self, session_cookies=None):
        """
        Initialisiert den Calculator.
        
        Args:
            session_cookies: Cookies von einer authentifizierten Session
        """
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        
        if session_cookies:
            for cookie in session_cookies:
                self.session.cookies.set(cookie['name'], cookie['value'])
    
    def get_vehicles(self, brand_code="000020", gamma="CORSA", fuel_code="B"):
        """
        Holt Fahrzeugliste.
        
        Args:
            brand_code: Marken-Code (000020 = OPEL)
            gamma: Modell (CORSA, ASTRA, etc.)
            fuel_code: Kraftstoff (B=Benzin, D=Diesel, E=Elektro)
        
        Returns:
            Liste der Fahrzeuge mit Preisen
        """
        url = f"{self.BASE_URL}/VEHICLE"
        params = {
            "$skip": 0,
            "$top": 100,
            "$filter": f"brandCode eq '{brand_code}' and Gamma eq '{gamma}' and engineCode eq '{fuel_code}'",
            "$inlinecount": "allpages"
        }
        
        response = self.session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('d', {}).get('results', [])
        
        return []
    
    def calculate_rate(self, product_id, mast_ag_id="1000026115", 
                       duration=48, mileage=40000):
        """
        Berechnet die Leasingrate für ein Fahrzeug.
        
        Args:
            product_id: Fahrzeug Product-ID
            mast_ag_id: Master Agreement ID
            duration: Laufzeit in Monaten
            mileage: km/Jahr
        
        Returns:
            Dict mit Raten-Details
        """
        # 1. FIN_CALC aufrufen für Basis-Kalkulation
        url = f"{self.BASE_URL}/FIN_CALC"
        params = {
            "$filter": (
                f"SoldId eq '{self.DEFAULT_PARAMS['bpId']}' and "
                f"MastAgId eq '{mast_ag_id}' and "
                f"ProcessType eq '{self.DEFAULT_PARAMS['quotTypeCode']}' and "
                f"ProductId eq '{product_id}'"
            )
        }
        
        response = self.session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('d', {}).get('results', [])
            
            if results:
                calc = results[0]
                return {
                    "product_id": product_id,
                    "list_price": calc.get("ListPrice", "0.00"),
                    "duration": duration,
                    "mileage": mileage,
                    "mast_ag_id": mast_ag_id,
                    # Rate muss über FC_WIDGET berechnet werden
                }
        
        return None
    
    def get_master_agreements(self):
        """Holt verfügbare Master Agreements."""
        url = f"{self.BASE_URL}/QUOT_TYPE('ZEV7')/MAST_AG"
        params = {
            "$skip": 0,
            "$top": 75,
            "$filter": (
                f"salesAreaCode eq '{self.DEFAULT_PARAMS['salesAreaCode']}' and "
                f"distrChannelCode eq '{self.DEFAULT_PARAMS['distrChannelCode']}' and "
                f"bpId eq '{self.DEFAULT_PARAMS['bpId']}'"
            )
        }
        
        response = self.session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('d', {}).get('results', [])
        
        return []


# Test
if __name__ == "__main__":
    print("🚗 Leasys Rate Calculator")
    print("="*50)
    print("Hinweis: Benötigt authentifizierte Session-Cookies")
    print("Verwende leasys_api_client.py für Login")
