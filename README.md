# FinanceWebsite

*A collection of financial analytics tools and dashboards built for flexibility, accuracy, and easy local deployment.*

This project is intended to evolve into a suite of financial utilities. Each module lives within the same unified web interface.

Currently, the project includes its first major tool:

---

## 📈 Fixed Income Dashboard — Mexico Sovereign Curve

The **Fixed Income Dashboard** provides an interactive visualization of the Mexican sovereign yield curve and key macroeconomic indicators.

### Features
- Fetches data from the Mexican Central Bank (Banxico) [API](https://www.banxico.org.mx/SieAPIRest/service/v1/):
  - Macro data:
    - TIIEF (1d)
    - TIIE (28d)
    - Target Rate
    - Inflation
    - UDI/MXN
    - USD/MXN
  - Bond yield/price data:
    - CETES (zero-coupon): 28D, 91D, 182D, 364D, 2Y
    - MBONOS (fixed-rate semi-annual day payers): 3Y, 5Y, 10Y, 20Y, 30Y
- Displays acquired data:
  - Summary bar containing macro data.   
  - Plots the sovereign yield curve for the selected date.
- Back end:
  - Python: flask interface and Banxico API calls.
  - C++: implementation of numerical schemes.
    - Newton Raphson for price-to-yield conversions. MBONOS yields not available from Banxico API. See [docs](./docs/mbono_yields_newton_raphson.md).    
- Front end:
  - Smooth UI built with Bootstrap & Chart.js.

---

## 🧩 Project Structure
```
FinanceWebsite/
├── cpp_engine                           # C++ engine
│   ├── __init__.py
│   ├── binding.cpp                      # pybind11 binding
│   ├── price_to_yield.cpp               # Price-to-yield Newton Raphson solver
│   ├── price_to_yield.h
│   └── tests                            # C++ tests
│       ├── test_price_to_yield          
│       └── test_price_to_yield.cpp
├── docs
│   └── mbono_yields_newton_raphson.md
├── requirements.txt
├── setup.py
├── src
│   ├── __init__.py
│   ├── app.py                            # Flask app
│   └── FIdash.py                         # Fixed income dashboard
├── static
|   ├── css
|   |   └── style.css                     # For front end visual format
│   └── js
│       └── dashboard.js                  # For front end interactions
├── templates
│   ├── base.html                         # Common base
│   ├── index.html                        # Home page
│   ├── dashboard.html                    # Fixed income dashboard 
│   └── error.html                        # Error page
│  
└── tests                                 # Python tests
    ├── __init__.py
    ├── test_FIdash.py
    └── test_errorhandling.py

```
---
## ⚙️ Local Setup Instructions

### Quick Setup
```bash
git clone https://github.com/mrodrigue3425/FinanceWebsite.git
cd FinanceWebsite

python -m venv venv
source venv/bin/activate       

pip install -r requirements.txt

python setup.py build_ext --inplace

flask run
```
The website will be available in your browser at 
```
http://127.0.0.1:5000
```
### Step by Step
### 1. Clone the Repository
```bash
git clone https://github.com/mrodrigue3425/FinanceWebsite.git
cd FinanceWebsite
```
### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt

```

### 4. Build the C++ Engine
```bash
python setup.py build_ext --inplace
```

### 5. Run the Flask Server
```bash
  flask run
```
---

## 🧪 Testing

For all python tests, including an integrated subprocess which runs the main C++ engine tests, run

```bash
pytest
```

To run a more in-depth C++ engine test suite with performance metrics, run
```bash
g++ -std=c++17 cpp_engine/tests/test_price_to_yield.cpp cpp_engine/price_to_yield.cpp -o cpp_engine/tests/test_price_to_yield -lgtest -lgtest_main -pthread && ./cpp_engine/tests/test_price_to_yield
```
---
## 📝 License

This project is licensed under the Apache License 2.0. Click [here](./LICENSE) for more details.

You are free to use, modify, and distribute this software under the terms of the license.
---

## 📌 Roadmap

- Equity option pricer
  - Black-Scholes
  - Fourier Transform
  - Monte Carlo
  - Finite Difference Methods
