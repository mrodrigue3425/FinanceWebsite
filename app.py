from flask import Flask, render_template
import dash

#declare flask app
app = Flask(__name__)

#home page route
@app.route('/')
def home():
    return render_template('index.html')

#fixed income dashboard route
@app.route('/FI_Dashboard')
def fi_dashboard():

    curve_labels, curve_dates, curve_yields, summary_data = dash.get_banxico_data() 
        
    return render_template(
        'dashboard.html', 
        curve_labels=curve_labels,
        curve_dates=curve_dates,
        curve_yields=curve_yields,
        summary_data=summary_data,
    )


#home page route
@app.route('/Options_Pricer')
def options_pricer():
    return render_template('options.html')

if __name__ == '__main__':
    app.run(debug=True)