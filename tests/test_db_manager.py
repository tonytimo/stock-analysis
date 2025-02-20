"""
This file contains tests for the db_manager module.
"""

import datetime
import pytest
from sqlalchemy import create_engine
from consumer import db_manager


class TestDBManager:
    """
    Test suite for the db_manager module.
    """

    @classmethod
    def setup_class(cls) -> None:
        """
        Runs once before any tests in this class.
        We'll create an in-memory SQLite database and patch
        the db_manager engine/SessionLocal to point to it.
        """
        # 1. Create a separate in-memory engine
        cls.test_engine = create_engine("sqlite:///:memory:", echo=False)

        # 2. Reconfigure SessionLocal to use this test engine
        #    instead of the file-based engine in db_manager.
        db_manager.SessionLocal.configure(bind=cls.test_engine)

        # 3. Create all tables on the new engine
        db_manager.Base.metadata.drop_all(bind=cls.test_engine)  # just to be safe
        db_manager.Base.metadata.create_all(bind=cls.test_engine)

    @classmethod
    def teardown_class(cls) -> None:
        """
        Runs once after all tests. We can drop tables or dispose the engine.
        """
        db_manager.Base.metadata.drop_all(bind=cls.test_engine)
        cls.test_engine.dispose()

    def setup_method(self):
        """
        Runs before each test method. You might truncate tables here if needed.
        """
        # Example: truncating tables before each test to start fresh.
        with db_manager.SessionLocal() as session:
            session.query(db_manager.StockPrice).delete()
            session.query(db_manager.StockAlert).delete()
            session.commit()

    def test_insert_and_retrieve_stock_price(self):
        """
        Test the insert_stock_price and get_recent_stock_prices functions.
        """
        # Insert two records
        db_manager.insert_stock_price(
            symbol="AAPL", price=150.0, ts=datetime.datetime(2025, 1, 1, 10, 0, 0)
        )
        db_manager.insert_stock_price(
            symbol="TSLA", price=700.0, ts=datetime.datetime(2025, 1, 1, 11, 0, 0)
        )

        # Retrieve
        results = db_manager.get_recent_stock_prices(limit=10)
        assert len(results) == 2

        # Since we sort by timestamp DESC, TSLA should come first
        assert results[0].symbol == "TSLA"
        assert results[0].price == 700.0

        # Then AAPL
        assert results[1].symbol == "AAPL"
        assert results[1].price == 150.0

    def test_get_recent_stock_prices_limit(self):
        """
        Test that the 'limit' parameter works correctly.
        """
        # Insert 3 records
        db_manager.insert_stock_price(symbol="AAPL", price=150.0)
        db_manager.insert_stock_price(symbol="TSLA", price=700.0)
        db_manager.insert_stock_price(symbol="AMZN", price=3300.0)

        # Retrieve only 2
        results = db_manager.get_recent_stock_prices(limit=2)
        assert len(results) == 2

    def test_insert_and_retrieve_stock_alert(self):
        """
        Test the insert_stock_alert and get_last_stock_alert functions.
        """
        # Insert first alert
        db_manager.insert_stock_alert(
            symbol="AAPL", msg="Alert 1", ts=datetime.datetime(2025, 1, 2, 8, 0, 0)
        )

        # Check that it's the last alert
        last_alert = db_manager.get_last_stock_alert()
        assert last_alert is not None
        assert last_alert.symbol == "AAPL"
        assert last_alert.message == "Alert 1"

        # Insert a second alert with a newer timestamp
        db_manager.insert_stock_alert(
            symbol="TSLA", msg="Alert 2", ts=datetime.datetime(2025, 1, 2, 9, 0, 0)
        )
        last_alert = db_manager.get_last_stock_alert()
        assert last_alert is not None
        assert last_alert.symbol == "TSLA"
        assert last_alert.message == "Alert 2"
