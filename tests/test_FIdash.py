import numpy as np
from datetime import datetime
from src import FIdash
import random
import subprocess

def test_banxico_data_initialization():
    test_object = FIdash.BanxicoDataFetcher()
    
    # test api key is available
    assert test_object.api_key is not None

    # test all Banxico API series ids are unique
    ids = test_object.CETES_MATURITY_MAP_YLD.copy()
    ids.update(test_object.CETES_MATURITY_MAP_DTM)
    ids.update(test_object.MBONOS_MATURITY_MAP_PX)
    ids.update(test_object.MBONOS_MATURITY_MAP_DTM)
    ids.update(test_object.MBONOS_MATURITY_MAP_COUP)
    ids.update(test_object.SUMMARY_MAP)

    assert len(ids) == len(set(ids.keys()))


def test_call_api():
    test_object = FIdash.BanxicoDataFetcher()
    test_data = test_object.call_api()

    # test returned series ids are the same as defined in BanxicoDataFetcher
    assert all(
        [
            y in test_object.CETES_MATURITY_MAP_YLD.keys()
            for y in [x["idSerie"] for x in test_data["cetes_yld"]]
        ]
    )
    assert all(
        [
            y in test_object.CETES_MATURITY_MAP_DTM.keys()
            for y in [x["idSerie"] for x in test_data["cetes_dtm"]]
        ]
    )
    assert all(
        [
            y in test_object.MBONOS_MATURITY_MAP_PX.keys()
            for y in [x["idSerie"] for x in test_data["mbonos_px"]]
        ]
    )
    assert all(
        [
            y in test_object.MBONOS_MATURITY_MAP_COUP.keys()
            for y in [x["idSerie"] for x in test_data["mbonos_coup"]]
        ]
    )
    assert all(
        [
            y in test_object.SUMMARY_MAP.keys()
            for y in [x["idSerie"] for x in test_data["summary"]]
        ]
    )

    # test all returned data is numeric
    assert all(
        [isinstance(float(x["datos"][0]["dato"]), float) for x in test_data["cetes_yld"]]
    )
    assert all(
        [isinstance(int(float(x["datos"][0]["dato"].replace(",",""))), int) for x in test_data["cetes_dtm"]]
    )
    assert all(
        [isinstance(float(x["datos"][0]["dato"]), float) for x in test_data["mbonos_px"]]
    )
    assert all(
        [isinstance(int(float(x["datos"][0]["dato"].replace(",",""))), int) for x in test_data["mbonos_dtm"]]
    )
    assert all(
        [isinstance(float(x["datos"][0]["dato"]), float) for x in test_data["mbonos_coup"]]
    )
    assert all(
        [isinstance(float(x["datos"][0]["dato"]), float) for x in test_data["summary"]]
    )

def test_clean_returned_data():

    test_object = FIdash.BanxicoDataFetcher()

    # generate random data
    banxico_data_many = generate_random_API_responses(100)

    for banxico_data in banxico_data_many:

        clean_ylds, clean_dtms_cetes = test_object.clean_returned_data(
            banxico_data["cetes_yld"],
            banxico_data["cetes_dtm"],
        )
        
        clean_pxs, clean_dtms_mbonos, clean_coups = test_object.clean_returned_data(
            banxico_data["mbonos_px"], 
            banxico_data["mbonos_dtm"], 
            banxico_data["mbonos_coup"], 
        )

        assert all(isinstance(x.get("datos")[0].get("dato"), float) for x in clean_ylds)
        assert all(isinstance(x.get("datos")[0].get("dato"), int) for x in clean_dtms_cetes)

        assert all(isinstance(x.get("datos")[0].get("dato"), float) for x in clean_pxs)
        assert all(isinstance(x.get("datos")[0].get("dato"), int) for x in clean_dtms_mbonos)
        assert all(isinstance(x.get("datos")[0].get("dato"), float) for x in clean_coups)

def test_reorder_data():

    test_object = FIdash.BanxicoDataFetcher()

    # generate random data
    banxico_data_many = generate_random_API_responses(100)

    for banxico_data in banxico_data_many:

        cetes_yld_data, cetes_dtm_data = test_object.clean_returned_data(
            banxico_data["cetes_yld"],
            banxico_data["cetes_dtm"],
        )

        mbonos_px_data, mbonos_dtm_data, mbonos_coup_data = test_object.clean_returned_data(
            banxico_data["mbonos_px"],
            banxico_data["mbonos_dtm"],
            banxico_data["mbonos_coup"],
        )

     

        # --- test cetes reordering --- 
        reordered_cetes_yld, reordered_cetes_dtm = test_object.reorder_data(cetes_yld_data, cetes_dtm_data)

        for tenor in reordered_cetes_yld: #yld
            # test reordered data is in acquired data
            assert tenor in cetes_yld_data
            # test reordered series ids is in originally requested series
            assert tenor.get("idSerie") in test_object.CETES_MATURITY_MAP_YLD.keys()
            # test reordered series ids in acquired series ids
            assert tenor.get("idSerie") in [data.get("idSerie") for data in cetes_yld_data]

            maturity = test_object.CETES_MATURITY_MAP_YLD.get(tenor.get("idSerie"))

            # test reordered tenor (maturity) in originally requested tenors
            assert maturity in test_object.CETES_MATURITY_MAP_YLD.values()

        for tenor in reordered_cetes_dtm: #dtm
            # test reordered data is in acquired data
            assert tenor in cetes_dtm_data
            # test reordered series ids is in oringially requested series
            assert tenor.get("idSerie") in test_object.CETES_MATURITY_MAP_DTM.keys()
            # test reordered series ids in acquired series ids
            assert tenor.get("idSerie") in [data.get("idSerie") for data in cetes_dtm_data]

            maturity = test_object.CETES_MATURITY_MAP_DTM.get(tenor.get("idSerie"))

            # test reordered tenor (maturity) in originally requested tenors
            assert maturity in test_object.CETES_MATURITY_MAP_DTM.values()

        # test yield data is reordered correctly with increasing days to maturity
        yld_maturities_in_days = [
            (
                int(test_object.CETES_MATURITY_MAP_YLD.get(tenor.get("idSerie")).split()[0])
                if test_object.CETES_MATURITY_MAP_YLD.get(tenor.get("idSerie"))
                .split()[1]
                .lower()
                == "days"
                else int(
                    test_object.CETES_MATURITY_MAP_YLD.get(tenor.get("idSerie")).split()[0]
                )
                * 364
            )
            for tenor in reordered_cetes_yld
        ]

        assert yld_maturities_in_days == sorted(yld_maturities_in_days)

        # test dtm data is ordered correctly

        dtm_maturities_in_days = [
            x.get("datos")[0]["dato"] for x in reordered_cetes_dtm
        ]

        assert dtm_maturities_in_days == sorted(dtm_maturities_in_days)

        # --- test mbonos reordering --- 

        reordered_bonos_px, reordered_bonos_dtm, reordered_bonos_coup = test_object.reorder_data(
            mbonos_px_data,
            mbonos_dtm_data,
            mbonos_coup_data
        )

        for tenor in reordered_bonos_px: #px
            # test reordered data is in acquired data
            assert tenor in mbonos_px_data
            # test reordered series ids is in oringially requested series
            assert tenor.get("idSerie") in test_object.MBONOS_MATURITY_MAP_PX.keys()
            # test reordered series ids in acquired series ids
            assert tenor.get("idSerie") in [data.get("idSerie") for data in mbonos_px_data]

            maturity = test_object.MBONOS_MATURITY_MAP_PX.get(tenor.get("idSerie"))

            # test reordered tenor (maturity) in originally requested tenors
            assert maturity in test_object.MBONOS_MATURITY_MAP_PX.values()

        for tenor in reordered_bonos_dtm: #dtm
            # test reordered data is in acquired data
            assert tenor in mbonos_dtm_data
            # test reordered series ids is in oringially requested series
            assert tenor.get("idSerie") in test_object.MBONOS_MATURITY_MAP_DTM.keys()
            # test reordered series ids in acquired series ids
            assert tenor.get("idSerie") in [data.get("idSerie") for data in mbonos_dtm_data]

            maturity = test_object.MBONOS_MATURITY_MAP_DTM.get(tenor.get("idSerie"))

            # test reordered tenor (maturity) in originally requested tenors
            assert maturity in test_object.MBONOS_MATURITY_MAP_DTM.values()

        for tenor in reordered_bonos_coup: #coup
            # test reordered data is in acquired data
            assert tenor in mbonos_coup_data
            # test reordered series ids is in oringially requested series
            assert tenor.get("idSerie") in test_object.MBONOS_MATURITY_MAP_COUP.keys()
            # test reordered series ids in acquired series ids
            assert tenor.get("idSerie") in [data.get("idSerie") for data in mbonos_coup_data]

            maturity = test_object.MBONOS_MATURITY_MAP_COUP.get(tenor.get("idSerie"))

            # test reordered tenor (maturity) in originally requested tenors
            assert maturity in test_object.MBONOS_MATURITY_MAP_COUP.values()

        # test price data is reordered correctly with increasing days to maturity
        px_maturities_in_days = [
            (
                int(test_object.MBONOS_MATURITY_MAP_PX.get(tenor.get("idSerie")).split()[0])
                if test_object.MBONOS_MATURITY_MAP_PX.get(tenor.get("idSerie"))
                .split()[1]
                .lower()
                == "days"
                else int(
                    test_object.MBONOS_MATURITY_MAP_PX.get(tenor.get("idSerie")).split()[0]
                )
                * 364
            )
            for tenor in reordered_bonos_px
        ]

        assert px_maturities_in_days == sorted(px_maturities_in_days)

        # test coup data is reordered correctly with increasing days to maturity
        coup_maturities_in_days = [
            (
                int(test_object.MBONOS_MATURITY_MAP_COUP.get(tenor.get("idSerie")).split()[0])
                if test_object.MBONOS_MATURITY_MAP_COUP.get(tenor.get("idSerie"))
                .split()[1]
                .lower()
                == "days"
                else int(
                    test_object.MBONOS_MATURITY_MAP_COUP.get(tenor.get("idSerie")).split()[0]
                )
                * 364
            )
            for tenor in reordered_bonos_coup
        ]

        assert coup_maturities_in_days == sorted(coup_maturities_in_days)

        # test dtm data is ordered correctly

        dtm_maturities_in_days = [
            x.get("datos")[0]["dato"] for x in reordered_bonos_dtm
        ]

        assert dtm_maturities_in_days == sorted(dtm_maturities_in_days)

def test_cpp_price_to_yield():
    result = subprocess.run(
        ["cpp_engine/tests/test_price_to_yield", "--gtest_filter=price_to_yieldTest.BasicCase"],
         capture_output=True,
         text=True)
    print(result.stdout)  # so pytest shows GTest output
    assert result.returncode == 0, "GTest failed!"

def test_get_labels_dates_yields():
    test_object = FIdash.BanxicoDataFetcher()
    cetes_data = [
        {
            "idSerie": "SF45470",
            "titulo": "Vector de precios de títulos gubernamentales Cetes 28 días - Tasa Rendimiento",
            "datos": [{"fecha": "20/10/2025", "dato": "7.399977"}],
        },
        {
            "idSerie": "SF45471",
            "titulo": "Vector de precios de títulos gubernamentales Cetes 91 días - Tasa Rendimiento",
            "datos": [{"fecha": "20/10/2025", "dato": "7.310613"}],
        },
        {
            "idSerie": "SF45472",
            "titulo": "Vector de precios de títulos gubernamentales Cetes 182 días - Tasa Rendimiento",
            "datos": [{"fecha": "20/10/2025", "dato": "7.409998"}],
        },
        {
            "idSerie": "SF45473",
            "titulo": "Vector de precios de títulos gubernamentales Cetes 364 días - Tasa Rendimiento",
            "datos": [{"fecha": "20/10/2025", "dato": "7.500388"}],
        },
    ]

    curve_labels, curve_dates, curve_yields = test_object.get_labels_dates_yields(
        cetes_data
    )

    for i, tenor in enumerate(cetes_data):
        expected_label = test_object.CETES_MATURITY_MAP.get(tenor.get("idSerie"))
        expected_date = tenor.get("datos")[0].get("fecha")
        expected_yield = np.round(float(tenor.get("datos")[0].get("dato")), 6)

        assert curve_labels[i] == expected_label
        assert curve_dates[i] == expected_date
        assert curve_yields[i] == expected_yield

        try:
            # Attempt to parse the string using the format code
            parsed_date = datetime.strptime(expected_date, "%d/%m/%Y")
            assert isinstance(parsed_date, datetime)
        except ValueError:
            assert (
                False
            ), f"Date string '{expected_date}' is not in the expected format DD/MM/YYYY"


def generate_random_API_responses(n):

    # simulates n random API responses for yield curve and summary data

    random.seed(42)

    def convert_to_days(maturity_str):
        parts = maturity_str.split(" ")
        if parts[1].lower() == "days":
            return int(parts[0])
        elif parts[1].lower() == "years":
            return int(parts[0]) * 364
        else:
            raise ValueError(f"Unknown maturity format: {maturity_str}")

    test_object = FIdash.BanxicoDataFetcher()

    response_list = []

    possible_coupons = np.arange(0.25,15.25,0.25)

    for _ in range(min(n,10000)):

        ylds = []
        dtms_cetes = []
        
        pxs = []
        dtms_mbonos = []
        coups = []

        summary = []

        # establish random response orders
        rand_order_cetes_yld = random.sample(range(5), 5)
        rand_order_cetes_dtm = random.sample(range(5), 5)

        rand_order_mbonos_px = random.sample(range(5), 5)
        rand_order_mbonos_dtm = random.sample(range(5), 5) 
        rand_order_mbonos_coup = random.sample(range(5), 5) 

        rand_order_summary = random.sample(range(6), 6)

        # establish other random data
        rand_date = f"{random.randrange(1,29)}/{random.randrange(1,13)}/{random.randrange(2000,2026)}"

        # generate random mbonos and cetes data
        for i in range(5):
            ylds.append({
                "idSerie": list(test_object.CETES_MATURITY_MAP_YLD.keys())[rand_order_cetes_yld[i]],
                "titulo": list(test_object.CETES_MATURITY_MAP_YLD.values())[rand_order_cetes_yld[i]],
                "datos": [{"fecha": rand_date, "dato": str(round(random.uniform(0, 15), 6))}]
            })

            titulo = list(test_object.CETES_MATURITY_MAP_DTM.values())[rand_order_cetes_dtm[i]]
            dtm = int(convert_to_days(titulo))
            rand_err = -1**random.randrange(0,2)*random.randrange(0,5)
            dtms_cetes.append({
                "idSerie": list(test_object.CETES_MATURITY_MAP_DTM.keys())[rand_order_cetes_dtm[i]],
                "titulo": titulo,
                "datos": [{"fecha": rand_date, "dato": f"{dtm+rand_err:,.6f}"}]
            })

            pxs.append({
                "idSerie": list(test_object.MBONOS_MATURITY_MAP_PX.keys())[rand_order_mbonos_px[i]],
                "titulo": list(test_object.MBONOS_MATURITY_MAP_PX.values())[rand_order_mbonos_px[i]],
                "datos": [{"fecha": rand_date, "dato": str(round(random.uniform(70, 130), 6))}]
            })

            titulo = list(test_object.MBONOS_MATURITY_MAP_DTM.values())[rand_order_mbonos_dtm[i]]
            dtm = int(convert_to_days(titulo))
            rand_err = -1**random.randrange(0,2)*random.randrange(0,50)
            dtms_mbonos.append({
                "idSerie": list(test_object.MBONOS_MATURITY_MAP_DTM.keys())[rand_order_mbonos_dtm[i]],
                "titulo": titulo,
                "datos": [{"fecha": rand_date, "dato": f"{dtm+rand_err:,.6f}"}]
            })

            coups.append({
                "idSerie": list(test_object.MBONOS_MATURITY_MAP_COUP.keys())[rand_order_mbonos_coup[i]],
                "titulo": list(test_object.MBONOS_MATURITY_MAP_COUP.values())[rand_order_mbonos_coup[i]],
                "datos": [{"fecha": rand_date, "dato": f"{np.random.choice((possible_coupons)):.6f}"}]
            })

        # generate random summary data
        for i in range(6):
            summary.append({
                "idSerie": list(test_object.SUMMARY_MAP.keys())[rand_order_summary[i]],
                "titulo": list(test_object.SUMMARY_MAP.values())[rand_order_summary[i]],
                "datos": [{"fecha": rand_date, "dato": str(round(random.uniform(0, 20),6))}]
            })

        # simulate response structure
        response = {
            "cetes_yld": ylds,
            "cetes_dtm": dtms_cetes,
            "mbonos_px" : pxs,
            "mbonos_dtm" : dtms_mbonos,
            "mbonos_coup" : coups,
            "summary": summary,
        }

        response_list.append(response)

    return response_list   
