from dotenv import load_dotenv
import os
import requests
import numpy as np
from flask import jsonify

# load environment variables from .env file
load_dotenv()
banxico_api_key = os.getenv('BANXICO_API_KEY')

def get_banxico_data():
    # Logic to fetch and return data from Banxico using the API key
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

    # define series IDs and API URL
    cetes_series_ids = "SF45470,SF45471,SF45472,SF45473,SF349889"
    api_url_cetes = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{cetes_series_ids}/datos/oportuno"

    summary_ids = "SF331451,SF43783,SF61745,SP30578,SP68257,SF343410"
    api_url_summary = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{summary_ids}/datos/oportuno"

    headers = {
        'Bmx-Token': banxico_api_key,
        'Accept': 'application/json'
    }

    # check if API key is available
    if not banxico_api_key:
        return jsonify({"error": "BANXICO_API_KEY not found in environment variables."}), 500
    else:# make the API request
        cetes_response = requests.get(api_url_cetes, headers=headers, timeout=10)
        if cetes_response.status_code == 200:
            pass
        else:
            cetes_response.raise_for_status()
        summary_response = requests.get(api_url_summary, headers=headers, timeout=10)
        if summary_response.status_code == 200:
            pass
        else:
            summary_response.raise_for_status()

    #clean and process data
    cetes_response_json = cetes_response.json()
    summary_response_json = summary_response.json()

    curve_raw = {}
    for series in cetes_response_json['bmx']['series']:
        
        series_id = series['idSerie']
        maturity = CETES_MATURITY_MAP.get(series_id, "Unknown Maturity")

        dt = series['datos'][0]['fecha']
        yld = np.round(float(series['datos'][0]['dato']),6)
    
        curve_raw[maturity]= {
            "date": dt,
            "yield": yld
        }

    curve_labels, curve_dates, curve_yields = reorder_curve_data(curve_raw)

    summary_data={}
    for series in summary_response_json['bmx']['series']:
        series_id = series['idSerie']
        metric = SUMMARY_MAP.get(series_id, "Unknown")
        value = np.round(float(series['datos'][0]['dato']),6)
        dt = series['datos'][0]['fecha']
        summary_data[metric] = {
            "value": value,
            "date": dt
        }

    return curve_labels, curve_dates, curve_yields, summary_data

def reorder_curve_data(curve_raw):

    # Define the desired order
    desired_order = ["28 Days", "91 Days", "182 Days", "364 Days", "2 Years"]

    curve_labels = []
    curve_dates = []
    curve_yields = []
    
    for tenor in desired_order:

        rate = curve_raw.get(tenor).get('yield')
        date = curve_raw.get(tenor).get('date')

        curve_labels.append(tenor)
        curve_dates.append(date)
        curve_yields.append(rate)

    return curve_labels, curve_dates, curve_yields
    