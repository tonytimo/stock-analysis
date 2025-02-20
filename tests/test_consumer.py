"""
This module contains tests for the consumer.py module.
"""

import os
import datetime
from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy import create_engine
from consumer import consumer, db_manager


class TestConsumer:
    """
    Test suite for the consumer module.
    """

    @classmethod
    def setup_class(cls) -> None:
        """
        Runs once before any tests in this class.
        We'll create an in-memory SQLite database and patch
        db_manager.SessionLocal so the consumer writes to an in-memory DB.
        """
        # 1. Create a separate in-memory engine
        cls.test_engine = create_engine("sqlite:///:memory:", echo=False)
        db_manager.engine = cls.test_engine

        # 2. Reconfigure SessionLocal to use this test engine
        #    instead of the file-based engine in db_manager.
        db_manager.SessionLocal.configure(bind=cls.test_engine)

        # 3. Create all tables on the new engine
        db_manager.Base.metadata.drop_all(bind=cls.test_engine)  # just to be safe
        db_manager.Base.metadata.create_all(bind=cls.test_engine)

    @classmethod
    def teardown_class(cls) -> None:
        """
        Runs once after all tests in this class. Clean up the test DB.
        """
        db_manager.Base.metadata.drop_all(bind=cls.test_engine)
        cls.test_engine.dispose()

    def setup_method(self) -> None:
        """
        Runs before each test. Clear the DB tables so each test starts fresh.
        """
        with db_manager.SessionLocal() as session:
            session.query(db_manager.StockPrice).delete()
            session.query(db_manager.StockAlert).delete()
            session.commit()

    @patch("consumer.consumer.time.sleep", return_value=None)
    def test_consume_data_basic(self, mock_sleep) -> None:
        """
        Test that consume_data() can read a few messages from a mocked KafkaConsumer,
        insert them into the DB, and then we forcibly stop after a few iterations.
        """
        # 1. Mock the environment variable for Kafka bootstrap
        with patch.dict(os.environ, {"KAFKA_BOOTSTRAP_SERVERS": "test-kafka:9092"}):
            # 2. Mock KafkaConsumer so it yields a few messages, then breaks
            fake_consumer = MagicMock()
            # We'll create a fake generator of messages
            # Each message has a .value attribute with a dict
            messages = [
                MagicMock(
                    value={
                        "symbol": "AAPL",
                        "price": 150.0,
                        "timestamp": "2025-01-01T10:00:00",
                    }
                ),
                MagicMock(
                    value={
                        "symbol": "TSLA",
                        "price": 700.0,
                        "timestamp": "2025-01-01T11:00:00",
                    }
                ),
            ]

            # We can make the consumer's __iter__ return these messages,
            # then raise EndOfTestData to simulate end of data
            def fake_iter():
                for m in messages:
                    yield m
                raise EndOfTestData("No more messages")  # force the loop to exit

            fake_consumer.__iter__.side_effect = fake_iter

            # 3. Mock KafkaProducer (we won't produce real messages to Kafka)
            fake_producer = MagicMock()

            with patch("consumer.consumer.KafkaConsumer", return_value=fake_consumer):
                with patch(
                    "consumer.consumer.KafkaProducer", return_value=fake_producer
                ):
                    # Run consume_data(), which should process the 2 messages, then stop
                    # because we raised EndOfTestData above.
                    try:
                        consumer.consume_data()
                    except EndOfTestData:
                        pass  # we expected this to force-loop exit

            # 4. Check the DB to ensure data was inserted
            with db_manager.SessionLocal() as session:
                stock_prices = session.query(db_manager.StockPrice).all()
                assert len(stock_prices) == 2
                # Check the first
                assert stock_prices[0].symbol in ("AAPL", "TSLA")

            # Also ensure no alerts triggered in this scenario
            # (since no price is 5% below average - only 2 data points)
            with db_manager.SessionLocal() as session:
                alerts = session.query(db_manager.StockAlert).all()
                assert len(alerts) == 0

    @patch("consumer.consumer.time.sleep", return_value=None)
    def test_alert_generation(self, mock_sleep):
        """
        Test that an alert is generated if a stock price is 5% below the average.
        We'll feed enough messages for an average, then a low price to trigger the alert.
        """
        with patch.dict(os.environ, {"KAFKA_BOOTSTRAP_SERVERS": "test-kafka:9092"}):
            fake_consumer = MagicMock()

            # We'll create several messages for the same symbol,
            # so we can compute an average. Then a final message is 5% below that average.
            messages = [
                MagicMock(
                    value={
                        "symbol": "AMZN",
                        "price": 200.0,
                        "timestamp": "2025-01-02T10:00:00",
                    }
                ),
                MagicMock(
                    value={
                        "symbol": "AMZN",
                        "price": 210.0,
                        "timestamp": "2025-01-02T10:01:00",
                    }
                ),
                MagicMock(
                    value={
                        "symbol": "AMZN",
                        "price": 190.0,
                        "timestamp": "2025-01-02T10:02:00",
                    }
                ),
                MagicMock(
                    value={
                        "symbol": "AMZN",
                        "price": 205.0,
                        "timestamp": "2025-01-02T10:03:00",
                    }
                ),
                MagicMock(
                    value={
                        "symbol": "AMZN",
                        "price": 210.0,
                        "timestamp": "2025-01-02T10:04:00",
                    }
                ),
                # Now we have 5 data points. Next point is 5% below average.
                # Average so far is (200+210+190+205+210) / 5 = 203.0
                # 5% below 203.0 => 192.85 -> let's pick 190.0
                MagicMock(
                    value={
                        "symbol": "AMZN",
                        "price": 190.0,
                        "timestamp": "2025-01-02T10:05:00",
                    }
                ),
            ]

            def fake_iter():
                for m in messages:
                    yield m
                raise EndOfTestData("No more messages")

            fake_consumer.__iter__.side_effect = fake_iter

            fake_producer = MagicMock()

            with patch(
                "consumer.consumer.KafkaConsumer", return_value=fake_consumer
            ), patch("consumer.consumer.KafkaProducer", return_value=fake_producer):
                try:
                    consumer.consume_data()
                except EndOfTestData:
                    pass

            # Now check if an alert was created for the last message
            with db_manager.SessionLocal() as session:
                alerts = session.query(db_manager.StockAlert).all()
                assert len(alerts) == 1
                assert alerts[0].symbol == "AMZN"

                # Also confirm that the KafkaProducer was called with the "stock_alerts" topic
                fake_producer.send.assert_called_with(
                    "stock_alerts",
                    value={
                        "symbol": "AMZN",
                        "massage": "Price 190.0 is 5% below avg 203.00",
                        "timestamp": datetime.datetime(2025, 1, 2, 10, 5),
                    },
                )


class EndOfTestData(Exception):
    pass
