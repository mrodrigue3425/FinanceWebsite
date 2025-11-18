from dotenv import load_dotenv
import os
import requests
import logging
import cpp_engine
import copy
from datetime import datetime
from dateutil.relativedelta import *


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
        "SF45470": "28D",
        "SF45471": "91D",
        "SF45472": "182D",
        "SF45473": "364D",
        "SF349889": "2Y",
    }

    # cetes days to maturity
    CETES_MATURITY_MAP_DTM = {
        "SF45422": "28D",
        "SF45423": "91D",
        "SF45424": "182D",
        "SF45425": "364D",
        "SF349886": "2Y",
    }

    # --- mbono data Banxico API series ids ---

    # mbono dirty prices
    MBONOS_MATURITY_MAP_PX = {
        "SF45448": "3Y",
        "SF45450": "5Y",
        "SF45454": "10Y",
        "SF45456": "20Y",
        "SF60721": "30Y",
    }

    # mbono days to maturity
    MBONOS_MATURITY_MAP_DTM = {
        "SF45427": "3Y",
        "SF45428": "5Y",
        "SF45430": "10Y",
        "SF45431": "20Y",
        "SF60720": "30Y",
    }

    # mbono current coupons
    MBONOS_MATURITY_MAP_COUP = {
        "SF45475": "3Y",
        "SF45476": "5Y",
        "SF45478": "10Y",
        "SF45479": "20Y",
        "SF60723": "30Y",
    }

    # --- summary data Banxico API series ids ---

    SUMMARY_MAP = {
        "SF331451": "TIIEF",
        "SF43783": "TIIE28",
        "SF61745": "TargetRate",
        "SP68257": "UDI_MXN",
        "SF343410": "USD_MXN",
    }

    # --- inflation data Banxico API series ids ---

    INFLATION_MAP = {
        "SP30578": "MonthlyCPIYoY",
    }

    api_url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/"

    def __init__(self):

        logger.debug("Initialising BanxicoDataFetcher.")

        self.api_key = os.getenv("BANXICO_API_KEY").strip()

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
        self.summary_ids = ",".join(self.SUMMARY_MAP.keys())

        # inflation data
        self.inflation_ids = ",".join(self.INFLATION_MAP.keys())

    def get_data(self):

        logger.debug("BanxicoDataFetcher: fetching data.")

        # acquire curve data from the Banxico API
        banxico_curve_data = self.call_api_curve_data()

        # acquire summary and inflation data from the Banxico API
        banxico_summ_inf_data = self.call_api_summ_inf_data()

        # --- clean returned curve data ---

        # cetes
        cleaned_cetes_ylds, cleaned_cetes_dtms = self.clean_returned_data(
            banxico_curve_data["cetes_yld"], banxico_curve_data["cetes_dtm"]
        )

        # mbonos
        cleaned_mbonos_pxs, cleaned_mbonos_dtms, cleaned_mbonos_coups = (
            self.clean_returned_data(
                banxico_curve_data["mbonos_px"],
                banxico_curve_data["mbonos_dtm"],
                banxico_curve_data["mbonos_coup"],
            )
        )

        # --- reorder returned curve data ---

        # cetes
        reordered_cetes_ylds, reordered_cetes_dtms = self.reorder_data(
            cleaned_cetes_ylds, cleaned_cetes_dtms
        )

        # mbonos
        reordered_bonos_pxs, reordered_bonos_dtms, reordered_bonos_coups = (
            self.reorder_data(
                cleaned_mbonos_pxs, cleaned_mbonos_dtms, cleaned_mbonos_coups
            )
        )

        # --- convert mbono prices into yields ---

        reordered_bonos_ylds = self.prc_to_yld(
            reordered_bonos_pxs, reordered_bonos_dtms, reordered_bonos_coups
        )

        # --- parse summary data ---

        parsed_summary_data = self.parse_summary_data(banxico_summ_inf_data)

        # --- final yield curve data ---

        yield_curve_data = {
            "cetes": {"ylds": reordered_cetes_ylds, "dtms": reordered_cetes_dtms},
            "mbonos": {"ylds": reordered_bonos_ylds, "pxs": reordered_bonos_pxs,  "dtms": reordered_bonos_dtms},
        }

        curve_labels, curve_dates, curve_yields, curve_dtms, curve_pxs = (
            self.get_labels_dates_yields(yield_curve_data)
        )

        return curve_labels, curve_dates, curve_yields, curve_dtms, curve_pxs, parsed_summary_data

    def call_api_curve_data(self):

        # === make the API requests for curve data ===

        # -- cetes --
        logger.debug("Fetching cetes yield data.")
        cetes_response_yld = self.session.get(
            self.api_url_cetes_yld, headers=self.session.headers, timeout=10
        )
        if cetes_response_yld.status_code != 200:
            logger.critical(
                f"Error acquiring cetes yield data: {cetes_response_yld.status_code}"
            )
        cetes_response_yld.raise_for_status()

        logger.debug("Fetching cetes days do maturity data.")
        cetes_response_dtm = self.session.get(
            self.api_url_cetes_dtm, headers=self.session.headers, timeout=10
        )
        if cetes_response_dtm.status_code != 200:
            logger.critical(
                f"Error acquiring cetes dtm data: {cetes_response_dtm.status_code}"
            )
        cetes_response_dtm.raise_for_status()

        # -- mbonos --
        logger.debug("Fetching mbonos price data.")
        mbonos_response_px = self.session.get(
            self.api_url_m_px, headers=self.session.headers, timeout=10
        )
        if mbonos_response_px.status_code != 200:
            logger.critical(
                f"Error acquiring mbono price data: {mbonos_response_px.status_code}"
            )
        mbonos_response_px.raise_for_status()

        logger.debug("Fetching mbonos dtm data.")
        mbonos_response_dtm = self.session.get(
            self.api_url_m_dtm, headers=self.session.headers, timeout=10
        )
        if mbonos_response_dtm.status_code != 200:
            logger.critical(
                f"Error acquiring mbono dtm data: {mbonos_response_dtm.status_code}"
            )
        mbonos_response_dtm.raise_for_status()

        logger.debug("Fetching mbonos current coupon data.")
        mbonos_response_coup = self.session.get(
            self.api_url_m_coup, headers=self.session.headers, timeout=10
        )
        if mbonos_response_coup.status_code != 200:
            logger.critical(
                f"Error acquiring mbono current coupon data: {mbonos_response_coup.status_code}"
            )
        mbonos_response_coup.raise_for_status()

        # --- parse responses ---

        # cetes
        cetes_yld_response_json = cetes_response_yld.json()["bmx"]["series"]
        cetes_dtm_response_json = cetes_response_dtm.json()["bmx"]["series"]

        # mbonos
        m_px_response_json = mbonos_response_px.json()["bmx"]["series"]
        m_dtm_response_json = mbonos_response_dtm.json()["bmx"]["series"]
        m_coup_response_json = mbonos_response_coup.json()["bmx"]["series"]

         # -- find curve date --
        returned_datestrings = [x.get("datos")[0]["fecha"] for x in cetes_yld_response_json]
        returned_datestrings.extend([x.get("datos")[0]["fecha"] for x in cetes_dtm_response_json])
        returned_datestrings.extend([x.get("datos")[0]["fecha"] for x in m_px_response_json])
        returned_datestrings.extend([x.get("datos")[0]["fecha"] for x in m_dtm_response_json])
        returned_datestrings.extend([x.get("datos")[0]["fecha"] for x in m_coup_response_json])

        parsed_datestrings = [datetime.strptime(x, "%d/%m/%Y") for x in returned_datestrings]

        # expect all Banxico curve data items to have the same latest date
        if len(set(parsed_datestrings)) != 1:
            raise Exception("Banxico API curve data dates are inconsistent.")

        # use curve data to anchor the date of the summary data, preventing data date mismatches
        # date for front end
        self.anchor_date = min(parsed_datestrings).strftime("%d/%m/%Y")
        # date for Banxico API query
        curve_date = min(parsed_datestrings).strftime("%Y-%m-%d")

        self.api_url_summary = (
            self.api_url + f"{self.summary_ids}/datos/{curve_date}/{curve_date}?decimales=sinCeros"
        )

        # use curve data to anchor inflation data search range
        inflation_from_date = (min(parsed_datestrings) + relativedelta(months=-2))
        # add 1 day to prevent query from returning more than one result
        inflation_from_date = (inflation_from_date + relativedelta(days=+1)).strftime("%Y-%m-%d") 

        inflation_to_date = curve_date

        self.api_url_inflation = (
            self.api_url + f"{self.inflation_ids}/datos/{inflation_from_date}/{inflation_to_date}?decimales=sinCeros"
        )

        acquired_curve_data = {
            "cetes_yld": cetes_yld_response_json,
            "cetes_dtm": cetes_dtm_response_json,
            "mbonos_px": m_px_response_json,
            "mbonos_dtm": m_dtm_response_json,
            "mbonos_coup": m_coup_response_json,
        }

        return acquired_curve_data
    
    def call_api_summ_inf_data(self):

        # === make the API requests for summary and inflation data ===

        # -- summary --
        logger.debug("Fetching summary data.")
        summary_response = self.session.get(
            self.api_url_summary, headers=self.session.headers, timeout=10
        )
        if summary_response.status_code != 200:
            logger.critical(
                f"Error acquiring summary data: {summary_response.status_code}"
            )
        summary_response.raise_for_status()

        # -- inflation --
        logger.debug("Fetching inflation data.")
        inlfation_response = self.session.get(
            self.api_url_inflation, headers=self.session.headers, timeout=10
        )
        if inlfation_response.status_code != 200:
            logger.critical(
                f"Error acquiring inflation data: {inlfation_response.status_code}"
            )
        inlfation_response.raise_for_status()

        # --- parse responses ---

        # summary
        summary_response_json = summary_response.json()["bmx"]["series"]

        #inflation
        inflation_response_json = inlfation_response.json()["bmx"]["series"]

        acquired_summ_inf_data = {
            "summary": summary_response_json,
            "inflation": inflation_response_json,
        }

        return acquired_summ_inf_data

    def clean_returned_data(self, px_ylds, dtms, coups=None):

        # covert to float returned prices, yields, and coupon rates
        # convert to int days to maturity

        clean_px_ylds = copy.deepcopy(px_ylds)
        clean_dtms = copy.deepcopy(dtms)

        if coups is None:
            logger.debug("Cleaning returned cetes data.")
        else:
            logger.debug("Cleaning returned mbonos data.")

        for px_yld in clean_px_ylds:
            px_yld["datos"][0]["dato"] = round(float(px_yld["datos"][0]["dato"]), 6)
        for dtm in clean_dtms:
            dtm["datos"][0]["dato"] = int(
                float(dtm["datos"][0]["dato"].replace(",", ""))
            )

        if coups is None:
            return clean_px_ylds, clean_dtms
        else:
            clean_coups = copy.deepcopy(coups)
            for coup in clean_coups:
                coup["datos"][0]["dato"] = round(float(coup["datos"][0]["dato"]), 2)
            return clean_px_ylds, clean_dtms, clean_coups

    def reorder_data(
        self, yld_px_response_data, dtm_response_data, coup_response_data=None
    ):

        # ensure returned data is in order of increasing term to maturity

        def convert_to_days(maturity_str):
            day_or_year = maturity_str[-1]
            num = maturity_str[:-1]
            if day_or_year.lower() == "d":
                return int(num)
            elif day_or_year.lower() == "y":
                return int(num) * 364
            else:
                raise ValueError(f"Unknown maturity format: {maturity_str}")

        def reorder_cetes(yld_response_data, dtm_response_data):
            returned_yld_maturities = [
                self.CETES_MATURITY_MAP_YLD.get(y.get("idSerie"))
                for y in yld_response_data
            ]

            returned_dtm_maturities = [
                self.CETES_MATURITY_MAP_DTM.get(y.get("idSerie"))
                for y in dtm_response_data
            ]

            # define the desired order
            mat_in_days_yld = [convert_to_days(mat) for mat in returned_yld_maturities]
            mat_in_days_dtm = [convert_to_days(mat) for mat in returned_dtm_maturities]

            # get ranks of returned data
            maturity_ranks_yld = [
                x[0]
                for x in sorted(list(enumerate(mat_in_days_yld)), key=lambda x: x[1])
            ]
            maturity_ranks_dtm = [
                x[0]
                for x in sorted(list(enumerate(mat_in_days_dtm)), key=lambda x: x[1])
            ]

            # reorder data
            ordered_cetes_data_yld = [yld_response_data[x] for x in maturity_ranks_yld]
            ordered_cetes_data_dtm = [dtm_response_data[x] for x in maturity_ranks_dtm]

            return ordered_cetes_data_yld, ordered_cetes_data_dtm

        def reorder_bonos(px_response_data, dtm_response_data, coup_response_data):

            returned_px_maturities = [
                self.MBONOS_MATURITY_MAP_PX.get(y.get("idSerie"))
                for y in px_response_data
            ]

            returned_dtm_maturities = [
                self.MBONOS_MATURITY_MAP_DTM.get(y.get("idSerie"))
                for y in dtm_response_data
            ]

            returned_coup_maturities = [
                self.MBONOS_MATURITY_MAP_COUP.get(y.get("idSerie"))
                for y in coup_response_data
            ]

            # define the desired order
            mat_in_days_px = [convert_to_days(mat) for mat in returned_px_maturities]
            mat_in_days_dtm = [convert_to_days(mat) for mat in returned_dtm_maturities]
            mat_in_days_coup = [
                convert_to_days(mat) for mat in returned_coup_maturities
            ]

            # get ranks of returned data
            maturity_ranks_px = [
                x[0]
                for x in sorted(list(enumerate(mat_in_days_px)), key=lambda x: x[1])
            ]
            maturity_ranks_dtm = [
                x[0]
                for x in sorted(list(enumerate(mat_in_days_dtm)), key=lambda x: x[1])
            ]
            maturity_ranks_coup = [
                x[0]
                for x in sorted(list(enumerate(mat_in_days_coup)), key=lambda x: x[1])
            ]

            # reorder data
            ordered_bonos_data_px = [px_response_data[x] for x in maturity_ranks_px]
            ordered_bonos_data_dtm = [dtm_response_data[x] for x in maturity_ranks_dtm]
            ordered_bonos_data_coup = [
                coup_response_data[x] for x in maturity_ranks_coup
            ]

            return (
                ordered_bonos_data_px,
                ordered_bonos_data_dtm,
                ordered_bonos_data_coup,
            )

        if not coup_response_data:
            logger.debug("Reordering cetes data.")
            return reorder_cetes(yld_px_response_data, dtm_response_data)

        else:
            logger.debug("Reordering bonos data.")
            return reorder_bonos(
                yld_px_response_data, dtm_response_data, coup_response_data
            )

    def parse_summary_data(self, summ_inf_response_data):

        month_to_string = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December"
        }

        logger.debug("Parsing summary data.")

        parsed_summ_inf = {}

        # parse summary data
        for series in summ_inf_response_data["summary"]:
            series_id = series["idSerie"]
            metric = self.SUMMARY_MAP.get(series_id, "Unknown")
            value = round(float(series["datos"][0]["dato"]), 6)
        
            dt = series["datos"][0]["fecha"]

            parsed_summ_inf[metric] = {"value": value, "date": dt}
            
        # parsed inflation data    
        for series in summ_inf_response_data["inflation"]:

            # minus one to get latest incase more than one inflation data point is returned
            data_index = -1

            series_id = series["idSerie"]
            metric = self.INFLATION_MAP.get(series_id, "Unknown")
            value = round(float(series["datos"][data_index]["dato"]), 6)

            month = month_to_string.get(int(series["datos"][data_index]["fecha"].split("/")[1]))
            year = int(series["datos"][data_index]["fecha"].split("/")[2])

            # for informative tooltip
            dt = f"{month} {year - 1} - {month} {year}"

            parsed_summ_inf[metric] = {"value": value, "date": dt}

        return parsed_summ_inf

    def prc_to_yld(self, prices, dtms, coups):

        logger.debug("Converting mbono clean prices into yields.")

        # convert mbono clean prices into yields
        pxs = copy.deepcopy(prices)

        pxs_ = [x["datos"][0]["dato"] for x in pxs]
        dtms_ = [x["datos"][0]["dato"] for x in dtms]
        coups_ = [x["datos"][0]["dato"] for x in coups]

        reordered_bonos_yields = cpp_engine.price_to_yield(pxs_, dtms_, coups_)

        for i, px in enumerate(pxs):
            px["datos"][0]["dato"] = reordered_bonos_yields[i]

        yields = pxs

        return yields

    def get_labels_dates_yields(self, curve_dict):

        def yield_to_price(yld,d):
            px = 10/(1+((yld*d)/36000))
            return px

        # get labels, dates, and yields to parse in html
        logger.debug("Getting labels, dates, yields and dtms.")

        curve_labels = []
        curve_dates = []
        curve_yields = []
        curve_dtms = []
        curve_pxs = []

        # cetes
        for i, tenor in enumerate(curve_dict.get("cetes").get("ylds")):
            curve_labels.append(self.CETES_MATURITY_MAP_YLD.get(tenor.get("idSerie")) + " CETES")
            curve_dates.append(tenor.get("datos")[0].get("fecha"))
            curve_yields.append(tenor.get("datos")[0].get("dato"))
            curve_dtms.append(
                curve_dict.get("cetes").get("dtms")[i].get("datos")[0].get("dato")
            )
            curve_pxs.append(yield_to_price(tenor.get("datos")[0].get("dato"),curve_dict.get("cetes").get("dtms")[i].get("datos")[0].get("dato")))

        # mbonos
        for i, tenor in enumerate(curve_dict.get("mbonos").get("ylds")):
            curve_labels.append(self.MBONOS_MATURITY_MAP_PX.get(tenor.get("idSerie")) + " MBONOS")
            curve_dates.append(tenor.get("datos")[0].get("fecha"))
            curve_yields.append(tenor.get("datos")[0].get("dato"))
            curve_dtms.append(
                curve_dict.get("mbonos").get("dtms")[i].get("datos")[0].get("dato")
            )
            curve_pxs.append(curve_dict.get("mbonos").get("pxs")[i].get("datos")[0].get("dato"))

        return curve_labels, curve_dates, curve_yields, curve_dtms, curve_pxs

    def __repr__(self):
        return f"<BanxicoData({len(self.CETES_MATURITY_MAP_YLD.keys())} cetes, \
{len(self.MBONOS_MATURITY_MAP_PX.keys())} mbonos , {len(self.SUMMARY_MAP.keys())} summary stats, \
{len(self.INFLATION_MAP.keys())} inflation stats)>"
