import pandas as pd
import numpy as np
from datetime import datetime
from src import FIdash


def test_banxico_data_initialization():
    test_object = FIdash.BanxicoDataFetcher()
    assert test_object.api_key is not None


def test_call_api():
    test_object = FIdash.BanxicoDataFetcher()
    test_data = test_object.call_api()
    assert all(
        [
            y in test_object.CETES_MATURITY_MAP.keys()
            for y in [x["idSerie"] for x in test_data["cetes"]]
        ]
    )
    assert all(
        [
            y in test_object.SUMMARY_MAP.keys()
            for y in [x["idSerie"] for x in test_data["summary"]]
        ]
    )
    assert all(
        [isinstance(float(x["datos"][0]["dato"]), float) for x in test_data["cetes"]]
    )
    assert all(
        [isinstance(float(x["datos"][0]["dato"]), float) for x in test_data["summary"]]
    )


def test_reorder_cetes_data():
    test_object = FIdash.BanxicoDataFetcher()
    cetes_data = [
        {
            "idSerie": "SF349889",
            "titulo": "",
            "datos": [{"fecha": "20/10/2025", "dato": "7.789997"}],
        },
        {
            "idSerie": "SF45470",
            "titulo": "Vector de precios de títulos gubernamentales Cetes 28 días - Tasa Rendimiento",
            "datos": [{"fecha": "20/10/2025", "dato": "7.399977"}],
        },
        {
            "idSerie": "SF45472",
            "titulo": "Vector de precios de títulos gubernamentales Cetes 182 días - Tasa Rendimiento",
            "datos": [{"fecha": "20/10/2025", "dato": "7.409998"}],
        },
        {
            "idSerie": "SF45471",
            "titulo": "Vector de precios de títulos gubernamentales Cetes 91 días - Tasa Rendimiento",
            "datos": [{"fecha": "20/10/2025", "dato": "7.310613"}],
        },
        {
            "idSerie": "SF45473",
            "titulo": "Vector de precios de títulos gubernamentales Cetes 364 días - Tasa Rendimiento",
            "datos": [{"fecha": "20/10/2025", "dato": "7.500388"}],
        },
    ]

    reordered_cetes_data = test_object.reorder_cetes_data(cetes_data)

    for tenor in reordered_cetes_data:
        assert tenor in cetes_data
        assert tenor.get("idSerie") in test_object.CETES_MATURITY_MAP.keys()
        assert tenor.get("idSerie") in [data.get("idSerie") for data in cetes_data]

        maturity = test_object.CETES_MATURITY_MAP.get(tenor.get("idSerie"))
        assert maturity in test_object.CETES_MATURITY_MAP.values()

    maturities_in_days = [
        (
            int(test_object.CETES_MATURITY_MAP.get(tenor.get("idSerie")).split()[0])
            if test_object.CETES_MATURITY_MAP.get(tenor.get("idSerie"))
            .split()[1]
            .lower()
            == "days"
            else int(
                test_object.CETES_MATURITY_MAP.get(tenor.get("idSerie")).split()[0]
            )
            * 364
        )
        for tenor in reordered_cetes_data
    ]

    assert maturities_in_days == sorted(maturities_in_days)


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


# if __name__ == '__main__':
#     pytest.main(["tests/test_FIdash.py"])
