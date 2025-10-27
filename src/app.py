from flask import Flask, render_template
import os
import sys
import FIdash
import logging
import requests

# set up the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stderr)
logger = logging.getLogger(__name__) # Get a logger instance for this module

# declare project root and template path
current_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.dirname(current_dir)
template_path = os.path.join(project_root, 'templates')

# instantiate the data fetcher object only once when the application starts
try:
    banxico_data_fetcher = FIdash.BanxicoDataFetcher()
    logger.info("Banxico Data Fetcher intialised successfuly.")
except ValueError as e:
    # handle the critical error if the API key is missing during initialisation
    logger.critical("Banxico API initialisation: could not find API key in environment variables.")
    logger.exception(e)
    banxico_data_fetcher = None 
except Exception as e:
    # handle unexpected intialisation error
    logger.critical("Banxico API initialisation: unexpected error.")
    logger.exception(e) 
    banxico_data_fetcher = None

# declare flask app
app = Flask(
    __name__, 
    template_folder=template_path 
)

# home page route
@app.route('/')
def home():
    return render_template('index.html')

# fixed income dashboard route
@app.route('/fi_dashboard')
def fi_dashboard():
    # check proper api setup
    if banxico_data_fetcher is None:
        error_data = {"message": "Banxico API Key setup failed.",
                "code": 503,
                "reason": "Service Unavailable"}
        return handle_error(error_data)   
    
    # try get banxico data
    try:
        curve_labels, curve_dates, curve_yields, summary_data = banxico_data_fetcher.get_data()
        logger.info("Retrieved data from Banxico API successfully.") 
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        # connection errors
        logger.error("Network or timeout error fetching data from Banxico API.")
        logger.exception(e)
        error_data = {"message": "Connection failed. This could be due to an issue with the Banxico API or a network issue.",
                "code": 504,
                "reason": "Gateway Timeout"}
        return handle_error(error_data)
    
    except requests.exceptions.HTTPError as e:
        # request and response errors
        logger.error("Error fetching data from Banxico API during dashboard rendering.")
        logger.exception(e)

        status_code = getattr(e.response, 'status_code', 503)
        reason = getattr(e.response, 'reason', 'Service Unavailable')

        error_data = {"message": "Failed to retrieve data from Banxico API.",
                "code": status_code,
                "reason": reason}
        
        return handle_error(error_data)
    
    except Exception as e:
        # other errors
        logger.critical("UNEXPECTED Local Error during dashboard rendering.")
        logger.exception(e)
        
        status_code = 500
        reason = "Internal Server Error"
        
        error_data = {"message": f"An unexpected local processing error occurred: {str(e)}.",
                "code": status_code,
                "reason": reason}
        
        return handle_error(error_data)
    
    return render_template(
        'dashboard.html', 
        curve_labels=curve_labels,
        curve_dates=curve_dates,
        curve_yields=curve_yields,
        summary_data=summary_data,
    )

# options pricer route
@app.route('/options_pricing')
def options_pricer():
    return render_template('options_pricing.html')

@app.errorhandler(404)
def not_found_error(e):
    # log the not found error
    logger.warning("Page not found")

    error_data = {
        "message": "Page not found.",
        "code": 404,
        "reason": "Not Found"
    }
    return handle_error(error_data)

@app.errorhandler(500)
def internal_server_error(e):
    # log the unhandled error
    logger.error("Unexpected error occured.")
    logger.exception(e)

    error_data = {
        "message": "An unexpected error occurred.",
        "code": 500,
        "reason": "Internal Server Error"
    }
    return handle_error(error_data)

def handle_error(error_data):

    status_code = error_data.get("code", 500)

    if not isinstance(status_code, int) or status_code < 400 or status_code > 599:
        status_code = 500
        
    return render_template(
        'error.html',
        error_data=error_data
    ), status_code

if __name__ == '__main__':
    app.run(debug=True)