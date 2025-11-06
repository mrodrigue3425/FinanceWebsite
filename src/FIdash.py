from dotenv import load_dotenv
import os
import requests
from flask import Flask
import logging


# load environment variables from .env file
load_dotenv()

# set up the logger for this module
logger = logging.getLogger(__name__)


class BanxicoDataFetcher:
    """
        Fetches data from Banxico SIE API.

        See https://www.banxico.org.mx/SieAPIRest/service/v1/
    """
    # --- cetes data Banxico API series ids ---

    # cetes yields
    CETES_MATURITY_MAP_YLD = {
        "SF45470": "28 Days",
        "SF45471": "91 Days",
        "SF45472": "182 Days",
        "SF45473": "364 Days",
        "SF349889": "2 Years",
    }

    # cetes days to maturity
    CETES_MATURITY_MAP_DTM = {
        "SF45422": "28 Days",
        "SF45423": "91 Days",
        "SF45424": "182 Days",
        "SF45425": "364 Days",
        "SF349886": "2 Years",
    }

    # --- mbono data Banxico API series ids ---

    # mbono dirty prices
    MBONOS_MATURITY_MAP_PX = {
        "SF45448": "3 Years",
        "SF45450": "5 Years",
        "SF45454": "10 Years",
        "SF45456": "20 Years",
        "SF60721": "30 Years",
    }

    # mbono days to maturity
    MBONOS_MATURITY_MAP_DTM = {
        "SF45427": "3 Years",
        "SF45428": "5 Years",
        "SF45430": "10 Years",
        "SF45431": "20 Years",
        "SF60720": "30 Years",
    }

    # mbono current coupons
    MBONOS_MATURITY_MAP_COUP = {
        "SF45475": "3 Years",
        "SF45476": "5 Years",
        "SF45478": "10 Years",
        "SF45479": "20 Years",
        "SF60723": "30 Years",
    }

    # --- summary data Banxico API series ids ---

    SUMMARY_MAP = {
        "SF331451": "TIIEF",
        "SF43783": "TIIE28",
        "SF61745": "TargetRate",
        "SP30578": "Inflation",
        "SP68257": "UDI_MXN",
        "SF343410": "USD_MXN",
    }

    api_url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/"

    def __init__(self):

        logger.debug("Initialising BanxicoDataFetcher.")

        self.api_key = os.getenv("BANXICO_API_KEY")

        # check if Banxico API key in environment variables
        if not self.api_key:
            logger.critical(
                "BANXICO_API_KEY is missing. Cannot proceed with API calls."
            )
            raise ValueError("BANXICO_API_KEY not found in environment variables.")

        logger.debug("Successfuly read Banxico API key.")

        self.session = requests.Session()
        self.session.headers = {"Bmx-Token": self.api_key, "Accept": "application/json"}

        # --- define class variable series ids ---

        # cetes
        self.cetes_yld_ids = ",".join(self.CETES_MATURITY_MAP_YLD.keys())
        self.cetes_dtm_ids = ",".join(self.CETES_MATURITY_MAP_DTM.keys())

        # mbonos
        self.mbonos_px_ids = ",".join(self.MBONOS_MATURITY_MAP_PX.keys())
        self.mbonos_dtm_ids = ",".join(self.MBONOS_MATURITY_MAP_DTM.keys())
        self.mbonos_coup_ids = ",".join(self.MBONOS_MATURITY_MAP_COUP.keys())

        # summary data
        self.summary_ids = ",".join(self.SUMMARY_MAP.keys())

        # --- define class variable API query URLs ---

        # cetes
        self.api_url_cetes_yld = (
            self.api_url + f"{self.cetes_yld_ids}/datos/oportuno?decimales=sinCeros"
        )
        self.api_url_cetes_dtm = (
            self.api_url + f"{self.cetes_dtm_ids}/datos/oportuno?decimales=sinCeros"
        )

        # mbonos
        self.api_url_m_px = (
            self.api_url + f"{self.mbonos_px_ids}/datos/oportuno?decimales=sinCeros"
        )
        self.api_url_m_dtm = (
            self.api_url + f"{self.mbonos_dtm_ids}/datos/oportuno?decimales=sinCeros"
        )
        self.api_url_m_coup = (
            self.api_url + f"{self.mbonos_coup_ids}/datos/oportuno?decimales=sinCeros"
        )

        # summary data
        self.api_url_summary = (
            self.api_url + f"{self.summary_ids}/datos/oportuno?decimales=sinCeros"
        )

    def get_data(self):

        logger.debug("BanxicoDataFetcher: fetching data.")

        banxico_data = self.call_api()

        reordered_cetes_data = self.reorder_cetes_data(banxico_data["cetes"])
        parsed_summary_data = self.parse_summary_data(banxico_data["summary"])

        curve_labels, curve_dates, curve_yields = self.get_labels_dates_yields(
            reordered_cetes_data
        )

        return curve_labels, curve_dates, curve_yields, parsed_summary_data

    def call_api(self):

        # --- make the API requests ---

        # cetes
        logger.debug("Fetching cetes yield data.")
        cetes_response_yld = self.session.get(
            self.api_url_cetes_yld, headers=self.session.headers, timeout=10
        )
        if cetes_response_yld.status_code != 200:
            logger.critical(f"Error acquiring cetes yield data: {cetes_response_yld.status_code}")
        cetes_response_yld.raise_for_status()
        
        logger.debug("Fetching cetes days do maturity data.")
        cetes_response_dtm = self.session.get(
            self.api_url_cetes_dtm, headers=self.session.headers, timeout=10
        )
        if cetes_response_dtm.status_code != 200:
            logger.critical(f"Error acquiring cetes dtm data: {cetes_response_dtm.status_code}")
        cetes_response_dtm.raise_for_status()

        # mbonos
        logger.debug("Fetching mbonos price data.")
        mbonos_response_px = self.session.get(
            self.api_url_m_px, headers=self.session.headers, timeout=10
        )
        if mbonos_response_px.status_code != 200:
            logger.critical(f"Error acquiring mbono price data: {mbonos_response_px.status_code}")
        mbonos_response_px.raise_for_status()

        logger.debug("Fetching mbonos dtm data.")
        mbonos_response_dtm = self.session.get(
            self.api_url_m_dtm, headers=self.session.headers, timeout=10
        )
        if mbonos_response_dtm.status_code != 200:
            logger.critical(f"Error acquiring mbono dtm data: {mbonos_response_dtm.status_code}")
        mbonos_response_dtm.raise_for_status()

        logger.debug("Fetching mbonos current coupon data.")
        mbonos_response_coup = self.session.get(
            self.api_url_m_coup, headers=self.session.headers, timeout=10
        )
        if mbonos_response_coup.status_code != 200:
            logger.critical(f"Error acquiring mbono current coupon data: {mbonos_response_coup.status_code}")
        mbonos_response_coup.raise_for_status()

        # summary data
        logger.debug("Fetching summary data.")
        summary_response = self.session.get(
            self.api_url_summary, headers=self.session.headers, timeout=10
        )
        if summary_response.status_code != 200:
            logger.critical(
                f"Error acquiring summary data: {summary_response.status_code}"
            )
        summary_response.raise_for_status()

        # --- parse responses ---

        #cetes
        cetes_yld_response_json = cetes_response_yld.json()["bmx"]["series"]
        cetes_dtm_response_json = cetes_response_dtm.json()["bmx"]["series"]

        # mbonos
        m_px_response_json = mbonos_response_px.json()["bmx"]["series"]
        m_dtm_response_json = mbonos_response_dtm.json()["bmx"]["series"]
        m_coup_response_json = mbonos_response_coup.json()["bmx"]["series"]

        # summary data
        summary_response_json = summary_response.json()["bmx"]["series"]

        returned_data = {
            "cetes_yld": cetes_yld_response_json,
            "cetes_dtm": cetes_dtm_response_json,
            "mbonos_px": m_px_response_json,
            "mbonos_dtm": m_dtm_response_json,
            "mbonos_coup": m_coup_response_json,
            "summary": summary_response_json,
            }

        return returned_data

    def reorder_data(self, yld_px_response_data, dtm_response_data, coup_response_data = None):

        def convert_to_days(maturity_str):
            parts = maturity_str.split(" ")
            if parts[1].lower() == "days":
                return int(parts[0])
            elif parts[1].lower() == "years":
                return int(parts[0]) * 364
            else:
                raise ValueError(f"Unknown maturity format: {maturity_str}")

        def reorder_cetes(yld_response_data, dtm_response_data):
            returned_yld_maturities = [
                self.CETES_MATURITY_MAP_YLD.get(y.get("idSerie")) for y in yld_response_data
            ]

            returned_dtm_maturities = [
                self.CETES_MATURITY_MAP_DTM.get(y.get("idSerie")) for y in dtm_response_data
            ]

            # define the desired order
            mat_in_days_yld = [convert_to_days(mat) for mat in returned_yld_maturities]
            mat_in_days_dtm = [convert_to_days(mat) for mat in returned_dtm_maturities]

            # get ranks of returned data
            maturity_ranks_yld = [
                x[0] for x in sorted(list(enumerate(mat_in_days_yld)), key=lambda x: x[1])
            ]
            maturity_ranks_dtm = [
                x[0] for x in sorted(list(enumerate(mat_in_days_dtm)), key=lambda x: x[1])
            ]

            # reorder data
            ordered_cetes_data_yld = [yld_response_data[x] for x in maturity_ranks_yld]
            ordered_cetes_data_dtm = [dtm_response_data[x] for x in maturity_ranks_dtm]

            return ordered_cetes_data_yld, ordered_cetes_data_dtm

        def reorder_bonos(px_response_data, dtm_response_data, coup_response_data):
            
            returned_px_maturities = [
                self.MBONOS_MATURITY_MAP_PX.get(y.get("idSerie")) for y in px_response_data
            ]

            returned_dtm_maturities = [
                self.MBONOS_MATURITY_MAP_DTM.get(y.get("idSerie")) for y in dtm_response_data
            ]

            returned_coup_maturities = [
                self.MBONOS_MATURITY_MAP_COUP.get(y.get("idSerie")) for y in coup_response_data
            ]

            # define the desired order
            mat_in_days_px = [convert_to_days(mat) for mat in returned_px_maturities]
            mat_in_days_dtm = [convert_to_days(mat) for mat in returned_dtm_maturities]
            mat_in_days_coup = [convert_to_days(mat) for mat in returned_coup_maturities]

            # get ranks of returned data
            maturity_ranks_px = [
                x[0] for x in sorted(list(enumerate(mat_in_days_px)), key=lambda x: x[1])
            ]
            maturity_ranks_dtm = [
                x[0] for x in sorted(list(enumerate(mat_in_days_dtm)), key=lambda x: x[1])
            ]
            maturity_ranks_coup = [
                x[0] for x in sorted(list(enumerate(mat_in_days_coup)), key=lambda x: x[1])
            ]

            # reorder data
            ordered_bonos_data_px = [px_response_data[x] for x in maturity_ranks_px]
            ordered_bonos_data_dtm = [dtm_response_data[x] for x in maturity_ranks_dtm]
            ordered_bonos_data_coup = [coup_response_data[x] for x in maturity_ranks_coup]

            return ordered_bonos_data_px, ordered_bonos_data_dtm, ordered_bonos_data_coup

        if not coup_response_data:
            logger.debug("Reordering cetes data.")
            return reorder_cetes(yld_px_response_data, dtm_response_data)
            
        else:
            logger.debug("Reordering bonos data.")
            return reorder_bonos(yld_px_response_data, dtm_response_data, coup_response_data)

    def parse_summary_data(self, summary_response_data):

        parsed_summary = {}

        for series in summary_response_data:
            series_id = series["idSerie"]
            metric = self.SUMMARY_MAP.get(series_id, "Unknown")
            value = round(float(series["datos"][0]["dato"]), 6)
            dt = series["datos"][0]["fecha"]
            parsed_summary[metric] = {"value": value, "date": dt}

        return parsed_summary

    def get_labels_dates_yields(self, curve_reordered):

        curve_labels = []
        curve_dates = []
        curve_yields = []

        for tenor in curve_reordered:
            curve_labels.append(self.CETES_MATURITY_MAP_YLD.get(tenor.get("idSerie")))
            curve_dates.append(tenor.get("datos")[0].get("fecha"))
            curve_yields.append(round(float(tenor.get("datos")[0].get("dato")), 6))

        return curve_labels, curve_dates, curve_yields

    def __repr__(self):
        return f"<BanxicoData(cetes_yld_ids={self.cetes_yld_ids}, summary_ids={self.summary_ids})>"


if __name__ == "__main__":
    print("\n==== Testing Banxico Data Fetch ====\n")
    app = Flask(__name__)
    with app.app_context():
        test = BanxicoDataFetcher()
        test.get_data()
