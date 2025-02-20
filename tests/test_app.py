"""
This module contains a test suite for the Flask web app.
"""

import datetime
from sqlalchemy import create_engine
from consumer import db_manager
from consumer.db_manager import Base, SessionLocal, StockPrice, StockAlert
from webapp.app import app


class TestWebApp:
    """
    Test suite for the Flask web app.
    """

    @classmethod
    def setup_class(cls) -> None:
        """
        Run once before all tests in this class.
        We override the database engine in db_manager with an in-memory SQLite engine.
        Then we create the tables and insert sample data.
        Also, we configure the Flask app for testing.
        """
        # Create an in-memory SQLite engine.
        cls.test_engine = create_engine("sqlite:///:memory:", echo=False)

        db_manager.engine = cls.test_engine
        SessionLocal.configure(bind=cls.test_engine)

        # Recreate all tables using the in-memory engine.
        Base.metadata.drop_all(bind=cls.test_engine)
        Base.metadata.create_all(bind=cls.test_engine)

        # Insert sample data.
        with SessionLocal() as session:
            # Insert a sample stock price record.
            stock_price = StockPrice(
                symbol="AAPL",
                price=150.0,
                timestamp=datetime.datetime(2025, 1, 1, 10, 0, 0),
            )
            session.add(stock_price)
            # Insert a sample stock alert record.
            stock_alert = StockAlert(
                symbol="AAPL",
                message="Test Alert",
                timestamp=datetime.datetime(2025, 1, 1, 10, 5, 0),
            )
            session.add(stock_alert)
            session.commit()

        # Configure Flask app for testing.
        app.config["TESTING"] = True
        cls.client = app.test_client()

    @classmethod
    def teardown_class(cls):
        """
        Run once after all tests.
        """
        Base.metadata.drop_all(bind=cls.test_engine)
        cls.test_engine.dispose()

    def test_index_route(self) -> None:
        """
        Verify that the index ("/") route returns a 200 status code
        and renders content that includes "Real-Time Stock Prices".
        """
        response = self.client.get("/")
        assert response.status_code == 200
        # Check for some expected text in the rendered HTML.
        assert b"Real-Time Stock Prices" in response.data

    def test_api_stocks(self) -> None:
        """
        Verify that the /api/stocks endpoint returns JSON with the inserted stock data.
        """
        response = self.client.get("/api/stocks")
        assert response.status_code == 200
        json_data = response.get_json()
        # We expect our sample record for "AAPL" to appear.
        assert "AAPL" in json_data
        # The value should be a list containing at least one record.
        aapl_data = json_data["AAPL"]
        assert isinstance(aapl_data, list)
        assert len(aapl_data) == 1
        # Verify the record’s data.
        record = aapl_data[0]
        assert record["price"] == 150.0
        # Timestamp should be in ISO format.
        assert record["timestamp"] == "2025-01-01T10:00:00"

    def test_api_latest_alert(self) -> None:
        """
        Verify that the /api/latest-alert endpoint returns JSON with the inserted alert.
        """
        response = self.client.get("/api/latest-alert")
        assert response.status_code == 200
        json_data = response.get_json()
        # Check that we get the expected alert data.
        assert json_data["symbol"] == "AAPL"
        assert json_data["message"] == "Test Alert"
        # Ensure a timestamp is present.
        assert "timestamp" in json_data
