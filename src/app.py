from flask import Flask, render_template
import os
import sys
import FIdash


# declare project root and template path
current_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.dirname(current_dir)
template_path = os.path.join(project_root, 'templates')

# instantiate the data fetcher object only once when the application starts
try:
    banxico_data_fetcher = FIdash.BanxicoDataFetcher()
except ValueError as e:
    # Handle the critical error if the API key is missing during initialization
    print("\n===============================================================")
    print(f"CRITICAL ERROR during BanxicoData setup: {e}", file=sys.stderr)
    print("===============================================================\n")
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
@app.route('/FI_Dashboard')
def fi_dashboard():
    
    # check proper api setup
    if banxico_data_fetcher is None:
        return "Service unavailable. API Key setup failed.", 503  
    
    # try get banxico data
    try:
        curve_labels, curve_dates, curve_yields, summary_data = banxico_data_fetcher.get_data() 
    except Exception as e:
        print(f"Error fetching data from Banxico: {e}")
        return "Failed to retrieve data from external APIs.", e.response.status_code

    return render_template(
        'dashboard.html', 
        curve_labels=curve_labels,
        curve_dates=curve_dates,
        curve_yields=curve_yields,
        summary_data=summary_data,
    )

# options pricer route
@app.route('/Options_Pricer')
def options_pricer():
    return render_template('options.html')

if __name__ == '__main__':
    app.run(debug=True)