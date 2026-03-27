# TODO FÜR CLAUDE - SESSION START TAG86

## ZIEL: Integration des Leasys API-Clients in DRIVE als "Leasys Kalkulator"

## WAS WURDE IN TAG85 ERREICHT

1. API-Client: /opt/greiner-portal/tools/scrapers/leasys_full_api.py
   - Selenium + Cookie-Caching, 54 OPEL Fahrzeuge abrufbar

2. API-Endpoints:
   BASE_URL = https://e-touch.leasys.com/sap/opu/odata/sap/ZNFC_P23_SRV
   /VEHICLE, /BRAND, /BRAND('x')/VHL_SET, /FIN_CALC, /FC_WIDGET

3. Parameter Autohaus Greiner:
   salesAreaCode=O 50020901, quotTypeCode=ZEV7, bpId=1186289565
   MA: 1000026115 (KM LEASING Opel 36-60)
   OPEL=000020, Benzin=B, Diesel=D, Elektro=E

4. Deep-Link: https://e-touch.leasys.com/e-saml2/index.html?sap-client=100#/quotation/BusinessPartnership/1186289565

## AUFGABEN TAG86

1. API erweitern: /opt/greiner-portal/api/leasys_api.py
   GET /api/leasys/vehicles?brand=OPEL&fuel=Benzin
   GET /api/leasys/models?brand=OPEL

2. Template: /opt/greiner-portal/templates/leasys_kalkulator.html
   Erbt von base.html, Bootstrap 4, Vanilla JS

3. Route: /opt/greiner-portal/routes/verkauf_routes.py
   @verkauf_bp.route('/leasys-kalkulator')

## RELEVANTE DATEIEN
/opt/greiner-portal/tools/scrapers/leasys_full_api.py   # API-Client
/opt/greiner-portal/api/leasys_api.py                   # Bestehende API
/opt/greiner-portal/templates/leasys_programmfinder.html
/opt/greiner-portal/templates/base.html
/opt/greiner-portal/routes/verkauf_routes.py

## TEST
cd /opt/greiner-portal && ./venv/bin/python -c "
from tools.scrapers.leasys_full_api import LeasysAPI
api = LeasysAPI()
api.authenticate()
print(len(api.get_vehicles(brand='OPEL', fuel='Benzin')), 'Fahrzeuge')
"
