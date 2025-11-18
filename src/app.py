from flask import Flask, render_template, request
from . import FIdash
import os
import sys

import logging
import requests

# --- Preliminary Tasks ---

# set up the logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# declare project root and template path
current_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.dirname(current_dir)
template_path = os.path.join(project_root, "templates")
static_path = os.path.join(project_root, "static")

# --- Initialisations ---

# instantiate the data fetcher object only once when the application starts
try:
    banxico_data_fetcher = FIdash.BanxicoDataFetcher()
    logger.info("BanxicoDataFetcher: intialised successfuly.")
except ValueError as e:
    # handle the error if the API key is missing during initialisation
    logger.exception(e)
    banxico_data_fetcher = None
except Exception as e:
    # handle unexpected intialisation error
    logger.critical("BanxicoDataFetcher: unexpected error.")
    logger.exception(e)
    banxico_data_fetcher = None

# declare flask app
app = Flask(
    __name__,
    static_folder=static_path,
    template_folder=template_path
    )

# --- Routes ---


# home page route
@app.route("/")
def home():
    logger.debug("Rendering home page.")
    return render_template("index.html")


# fixed income dashboard route
@app.route("/fi_dashboard")
def fi_dashboard():
    # check proper api setup
    if banxico_data_fetcher is None:
        error_data = {
            "message": "Banxico API Key setup failed.",
            "code": 503,
            "reason": "Service Unavailable",
        }
        return handle_error(error_data)

    # try get banxico data
    try:
        curve_labels, curve_dates, curve_yields, curve_dtms, curve_pxs, curve_ids, summary_data = (
            banxico_data_fetcher.get_data()
        )
        logger.info("Retrieved data from Banxico API successfully.")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        # connection errors
        logger.error("Network or timeout error fetching data from Banxico API.")
        logger.exception(e)
        error_data = {
            "message": "Connection failed. This could be due to an issue with the\
                  Banxico API or your network.",
            "code": 504,
            "reason": "Gateway Timeout",
        }
        return handle_error(error_data)

    except requests.exceptions.HTTPError as e:
        # request and response errors
        logger.exception(e)

        status_code = getattr(e.response, "status_code", 503)
        reason = getattr(e.response, "reason", "Service Unavailable")

        error_data = {
            "message": "Failed to retrieve data from Banxico API.",
            "code": status_code,
            "reason": reason,
        }

        return handle_error(error_data)

    except Exception as e:
        # other errors
        logger.critical("Unexpected error during dashboard rendering.")
        logger.exception(e)

        status_code = 500
        reason = "Internal Server Error"

        error_data = {
            "message": "An unexpected error occurred.",
            "code": status_code,
            "reason": reason,
        }

        return handle_error(error_data)

    logger.debug("Rendering dashboard.")
    return render_template(
        "dashboard.html",
        curve_labels=curve_labels,
        curve_dates=curve_dates,
        curve_yields=curve_yields,
        curve_dtms=curve_dtms,
        curve_pxs=curve_pxs,
        curve_ids=curve_ids,
        summary_data=summary_data,
        anchor_date=banxico_data_fetcher.anchor_date
    )


# options pricer route
@app.route("/options_pricing")
def options_pricer():
    logger.debug("Rendering options pricing.")
    return render_template("options_pricing.html")


# --- Error Handling ---


@app.errorhandler(404)
def not_found_error(e):
    # log the not found error
    logger.warning(f"Page not found {request.path}")

    error_data = {"message": "Page not found.", "code": 404, "reason": "Not Found"}
    return handle_error(error_data)


@app.errorhandler(500)
def internal_server_error(e):
    # log the unhandled error
    logger.error("Unexpected error occured.")
    logger.exception(e)

    error_data = {
        "message": "An unexpected error occurred.",
        "code": 500,
        "reason": "Internal Server Error",
    }
    return handle_error(error_data)


def handle_error(error_data):

    status_code = error_data.get("code", 500)

    if not isinstance(status_code, int) or status_code < 400 or status_code > 599:
        status_code = 500

    logger.debug("Rendering error page.")
    return render_template("error.html", error_data=error_data), status_code


if __name__ == "__main__":
    app.run(debug=True)
