import pytest
import requests

# Import the main Flask app instance and the real DataFetcher class
from src.app import app
from src.FIdash import BanxicoDataFetcher

# ----------------------------------------------
# Mock classes for simulating failure conditions
# ----------------------------------------------


class MockSuccessFetcher(BanxicoDataFetcher):
    """Mocks a successful data fetch."""

    def __init__(self):
        pass

    def get_data(self):
        """Returns the structure expected by the successful route logic."""
        mock_summary = {
            "TIIE28": {"value": 7.8114, "date": "29/10/2025"},
            "TIIEF": {"value": 7.55, "date": "27/10/2025"},
            "TargetRate": {"value": 7.5, "date": "29/10/2025"},
            "USD_MXN": {"value": 18.4315, "date": "28/10/2025"},
            "UDI_MXN": {"value": 8.586547, "date": "10/11/2025"},
            "Inflation": {"value": 3.76, "date": "01/09/2025"},
        }
        curve_labels = ["28 Days", "91 Days", "182 Days", "364 Days", "2 Years"]
        curve_dates = [
            "27/10/2025",
            "27/10/2025",
            "27/10/2025",
            "27/10/2025",
            "27/10/2025",
        ]
        curve_yields = [7.000015, 7.28126, 7.345685, 7.418118, 7.679998]
        return curve_labels, curve_dates, curve_yields, mock_summary


class MockConnectionErrorFetcher:
    """Mocks a ConnectionError to test the 504 handling."""

    def __init__(self):
        pass

    def get_data(self):
        raise requests.exceptions.ConnectionError("Mocked network failure.")


class MockHTTPErrorFetcher:
    """Mocks an HTTPError (e.g., 401, 403, 503) to test the HTTPError handling."""

    def __init__(self):
        pass

    def get_data(self):
        # Create a mock response object to attach to the HTTPError
        mock_response = requests.Response()
        mock_response.status_code = 503
        mock_response.reason = "Service Unavailable"

        http_error = requests.exceptions.HTTPError(
            "503 Service Unavailable", response=mock_response
        )
        http_error.response = mock_response
        raise http_error


class MockGenericErrorFetcher:
    """Mocks an unexpected error (like a parsing error) to test the 500 handling."""

    def __init__(self):
        pass

    def get_data(self):
        raise TypeError("Mocked unexpected parsing failure.")


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def client_ready(monkeypatch):
    """
    Patches the variable `banxico_data_fetcher` in src.app
    with a successful fetcher.
    """
    # Create the mock instance
    mock_instance = MockSuccessFetcher()

    # Patch the global banxico_data_fetcher variable
    monkeypatch.setattr("src.app.banxico_data_fetcher", mock_instance)

    app.testing = True
    with app.test_client() as client:
        yield client


@pytest.fixture(
    params=[
        (MockConnectionErrorFetcher, 504, b"Connection failed"),
        (MockHTTPErrorFetcher, 503, b"Service Unavailable"),
        (MockGenericErrorFetcher, 500, b"An unexpected error occurred."),
    ]
)
def client_failing_route(request, monkeypatch):
    """
    Patches the variable `banxico_data_fetcher` in src.app
    with unsuccessful fetchers.
    """
    MockFetcher, expected_code, expected_msg = request.param

    # Create the specific failing mock instance
    failing_instance = MockFetcher()

    # Patch the global banxico_data_fecther variable
    monkeypatch.setattr("src.app.banxico_data_fetcher", failing_instance)

    app.testing = True
    with app.test_client() as client:
        yield client, expected_code, expected_msg


@pytest.fixture
def client_failing_init(monkeypatch):
    """
    Client that forces the critical startup failure (banxico_data_fetcher = None).
    """
    # Force the API Key to be missing *before* app.py's global code runs
    monkeypatch.setattr("src.app.banxico_data_fetcher", None)

    app.testing = True
    with app.test_client() as client:
        yield client


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------


# --- Successful Response Test ---
def test_fi_dashboard_successful_data_fetch(client_ready):
    """Tests the successful path when mock data is returned."""
    response = client_ready.get("/fi_dashboard")
    assert response.status_code == 200
    # Check for content that proves the data was processed
    assert b"7.345685" in response.data


# --- Critical Startup Failure Test ---
def test_fi_dashboard_critical_init_failure(client_failing_init):
    """
    Tests API key missing on startup.
    This tests the 'if banxico_data_fetcher is None' logic, which should return 503.
    """
    response = client_failing_init.get("/fi_dashboard")
    assert response.status_code == 503
    assert b"Banxico API Key setup failed" in response.data
    assert b"Service Unavailable" in response.data


# --- Connection and HTTP Exception Handling Tests ---


def test_fi_dashboard_route_errors(client_failing_route):
    """
    Tests the try/except blocks for Connection, HTTP, and Generic errors.
    This fixture is run three times due to the 'params' defined above.
    """
    client, expected_code, expected_msg = client_failing_route

    response = client.get("/fi_dashboard")

    # Check the HTTP status code
    assert response.status_code == expected_code

    # Check the message content
    assert expected_msg in response.data


# --- Other Routes Tests ---
def test_other_routes_work(client_ready):
    """Ensure non-data-dependent routes are unaffected."""
    response = client_ready.get("/")
    assert response.status_code == 200
    response = client_ready.get("/options_pricing")
    assert response.status_code == 200


# --- Non-existent Route Handling Tests ---
def test_not_found_error(client_ready):
    """Test the 404 handler."""
    response = client_ready.get("/nonexistent_route")
    assert response.status_code == 404
    assert b"Page not found" in response.data
