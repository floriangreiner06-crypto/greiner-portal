#!/usr/bin/env python3
"""
Leasys Rate Calculator - Direkte API-Integration
Berechnet Leasingraten über die OData API
"""

import requests
import json
import uuid
import time
from datetime import datetime


class LeasysRateCalculator:
    """Berechnet Leasingraten direkt über die Leasys OData API."""

    BASE_URL = "https://e-touch.leasys.com/sap/opu/odata/sap/ZNFC_P23_SRV"

    DEFAULT_PARAMS = {
        "salesAreaCode": "O 50020901",
        "quotTypeCode": "ZEV7",
        "distrChannelCode": "I2",
        "bpId": "1186289565",
        "salesMngId": "1185834152",
        "brandCode": "000020",
    }

    def __init__(self, session_cookies=None):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        if session_cookies:
            for cookie in session_cookies:
                self.session.cookies.set(cookie['name'], cookie['value'])

    def calculate_full_rate(self, product_id, mast_ag_id="1000026115",
                            duration=48, mileage=40000, dealer_discount=17.0):
        """
        Berechnet die vollständige Leasingrate über EVALUATION.
        """
        quote_id = f"drv{int(time.time())}p{uuid.uuid4().hex[:12]}"
        
        eval_payload = {
            "bpId": self.DEFAULT_PARAMS["bpId"],
            "distrChannelCode": self.DEFAULT_PARAMS["distrChannelCode"],
            "quotTypeCode": self.DEFAULT_PARAMS["quotTypeCode"],
            "salesAreaCode": self.DEFAULT_PARAMS["salesAreaCode"],
            "salesAreaRespCode": "O 50020904",
            "salesMngId": self.DEFAULT_PARAMS["salesMngId"],
            "EVALUATION_ITEM": [{
                "bpId": self.DEFAULT_PARAMS["bpId"],
                "Vtc": False,
                "quotTypeCode": self.DEFAULT_PARAMS["quotTypeCode"],
                "salesAreaCode": self.DEFAULT_PARAMS["salesAreaCode"],
                "salesAreaRespCode": "O 50020904",
                "distrChannelCode": self.DEFAULT_PARAMS["distrChannelCode"],
                "agreementId": mast_ag_id,
                "redeemerBpId": "",
                "bbAgreementId": "",
                "buagId": "",
                "productId": product_id,
                "classRateCode": "ZIT029",
                "mileage": str(mileage),
                "duration": str(duration),
                "canalizationCode": "Z002",
                "extradealerDisc": f"{dealer_discount:.3f}",
                "extConfigCode": "",
                "GrilleFluidite": False,
                "StartMonth": "0",
                "EndMonth": "0",
                "IntMonth": "0",
                "StartKm": "0",
                "EndKm": "0",
                "IntKm": "0",
                "BbFlag": False,
                "CreateMode": "S",
                "ZzHomclFlag": False,
                "FcQuoteId": quote_id,
                "SERVICE": [],
                "ACCESSORY": []
            }]
        }
        
        try:
            resp = self.session.post(
                f"{self.BASE_URL}/EVALUATION",
                json=eval_payload,
                timeout=60
            )
            
            print(f"EVALUATION Status: {resp.status_code}")
            
            if resp.status_code not in [200, 201]:
                print(f"Response: {resp.text[:500]}")
                return None
            
            data = resp.json()
            d = data.get('d', {})
            items = d.get('EVALUATION_ITEM', {}).get('results', [])
            
            if items:
                item = items[0]
                return {
                    "product_id": product_id,
                    "duration": duration,
                    "mileage": mileage,
                    "dealer_discount": dealer_discount,
                    "list_price": float(item.get("ListPrice", 0) or 0),
                    "fin_rate": float(item.get("FinrentInstalment", 0) or 0),
                    "srv_rate": float(item.get("SrvrentInstalment", 0) or 0),
                    "total_rate": float(item.get("TotrentInstalment", 0) or 0),
                    "residual_value": float(item.get("Zi55", 0) or 0),
                    "loan_amount": float(item.get("LoanAmount", 0) or 0),
                    "tan": float(item.get("Tan", 0) or 0),
                }
            else:
                print("Keine EVALUATION_ITEM results")
                print(f"Response keys: {d.keys()}")
            
            return None
            
        except Exception as e:
            print(f"Rate calculation error: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    print("Leasys Rate Calculator - benötigt Session-Cookies")
