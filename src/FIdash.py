from dotenv import load_dotenv
import os
import requests
from flask import Flask
import logging


# load environment variables from .env file
load_dotenv()

# set up the logger for this module
logger = logging.getLogger(__name__) 

class BanxicoDataFetcher():

    CETES_MATURITY_MAP = {
        "SF45470": "28 Days",
        "SF45471": "91 Days",
        "SF45472": "182 Days",
        "SF45473": "364 Days",
        "SF349889": "2 Years"
    }

    SUMMARY_MAP = {
        "SF331451": "TIIEF",
        "SF43783": "TIIE28",
        "SF61745": "TargetRate",
        "SP30578": "Inflation",
        "SP68257": "UDI_MXN",
        "SF343410": "USD_MXN"
    }

    api_url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/"

    def __init__(self):

        logger.debug("Initialising BanxicoDataFetcher.")

        self.api_key = os.getenv('BANXICO_API_KEY')
        if not self.api_key:
            logger.critical("BANXICO_API_KEY is missing. Cannot proceed with API calls.")
            raise ValueError("BANXICO_API_KEY not found in environment variables.")
        
        logger.debug("Successfuly read Banxico API key.")
        
        self.session = requests.Session()
        self.session.headers = {
        'Bmx-Token': self.api_key,
        'Accept': 'application/json'
        }  

        self.cetes_series_ids = ",".join(self.CETES_MATURITY_MAP.keys())
        self.summary_ids = ",".join(self.SUMMARY_MAP.keys())
        self.api_url_cetes = self.api_url + f"{self.cetes_series_ids}/datos/oportuno?decimales=sinCeros"
        self.api_url_summary = self.api_url + f"{self.summary_ids}/datos/oportuno?decimales=sinCeros"

    def get_data(self):

        logger.debug("BanxicoDataFetcher: fetching data.")

        banxico_data = self.call_api()

        reordered_cetes_data = self.reorder_cetes_data(banxico_data["cetes"])
        parsed_summary_data = self.parse_summary_data(banxico_data["summary"])


        curve_labels, curve_dates, curve_yields = self.get_labels_dates_yields(reordered_cetes_data)

        return curve_labels, curve_dates, curve_yields, parsed_summary_data
       
    def call_api(self):  
        
   
        # make the API request
        logger.debug("Fetching cetes data.")
        cetes_response = self.session.get(self.api_url_cetes, headers=self.session.headers, timeout=10)
        if cetes_response.status_code != 200:
             logger.critical(f"Error acquiring cetes data: {cetes_response.status_code}")
        cetes_response.raise_for_status()

        logger.debug("Fetching summary data.")
        summary_response = self.session.get(self.api_url_summary, headers=self.session.headers, timeout=10)
        if summary_response.status_code != 200:
            logger.critical(f"Error acquiring summary data: {summary_response.status_code}")
        summary_response.raise_for_status()

                
        cetes_response_json = cetes_response.json()["bmx"]["series"]
        summary_response_json = summary_response.json()["bmx"]["series"]

        returned_data = {
            "cetes": cetes_response_json, 
            "summary": summary_response_json
        }      

        return  returned_data
            
    def reorder_cetes_data(self, cetes_response_data):
            
            logger.debug("Reordering cetes data.")
            
            returned_maturities = [self.CETES_MATURITY_MAP.get(y.get("idSerie")) for y in cetes_response_data]

            def convert_to_days(maturity_str):
                parts = maturity_str.split(" ")
                if parts[1].lower() == "days":
                    return int(parts[0])
                elif parts[1].lower() == "years":
                    return int(parts[0]) * 364
                else:
                    raise ValueError(f"Unknown maturity format: {maturity_str}")
                
            # define the desired order
            mat_in_days = [convert_to_days(mat) for mat in returned_maturities]

            maturity_ranks = [x[0] for x in sorted(list(enumerate(mat_in_days)),key=lambda x: x[1])]
            
            ordered_cetes_data = [cetes_response_data[x] for x in maturity_ranks]
        

            return ordered_cetes_data

    def parse_summary_data(self, summary_response_data):

        parsed_summary={}

        for series in summary_response_data:
            series_id = series['idSerie']
            metric = self.SUMMARY_MAP.get(series_id, "Unknown")
            value = round(float(series['datos'][0]['dato']),6)
            dt = series['datos'][0]['fecha']
            parsed_summary[metric] = {
                "value": value,
                "date": dt
            }

        return parsed_summary 
    
    def get_labels_dates_yields(self, curve_reordered):
            
            curve_labels = []
            curve_dates = []
            curve_yields = []

            for tenor in curve_reordered:
                 curve_labels.append(self.CETES_MATURITY_MAP.get(tenor.get("idSerie")))
                 curve_dates.append(tenor.get("datos")[0].get("fecha"))
                 curve_yields.append(round(float(tenor.get("datos")[0].get("dato")),6))

            return curve_labels, curve_dates, curve_yields

    def __repr__(self):
        return f"<BanxicoData(cetes_series_ids={self.cetes_series_ids}, summary_ids={self.summary_ids})>"

if __name__ == "__main__":
    print("\n==== Testing Banxico Data Fetch ====\n")
    app = Flask(__name__)
    with app.app_context(): 
        test = BanxicoDataFetcher()
        test.get_data()