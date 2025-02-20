"""
Test suite for producer.py
"""

import os
import requests
from unittest.mock import patch, MagicMock
import pytest
from producer.producer import get_stock_data, produce_data


class EndOfTestData(Exception):
    pass


class TestProducer:
    """
    Test suite for producer.py
    """

    @patch("producer.producer.requests.get")
    def test_get_stock_data_success(self, mock_get) -> None:
        """
        Test that get_stock_data() returns a list of dicts when the API call succeeds.
        """
        # 1. Mock the API response
        fake_json = [
            {
                "ticker": "AAPL",
                "tngoLast": 150.0,
                "timestamp": "2025-01-01T10:00:00+00:00",
            },
            {
                "ticker": "TSLA",
                "tngoLast": 700.0,
                "timestamp": "2025-01-01T11:00:00+00:00",
            },
        ]
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None  # no error
        mock_resp.json.return_value = fake_json

        mock_get.return_value = mock_resp

        # 2. Call get_stock_data
        api_key = "FAKE_API_KEY"
        result = get_stock_data(api_key)

        # 3. Verify
        assert len(result) == 2
        assert result[0]["symbol"] == "AAPL"
        assert result[0]["price"] == 150.0
        assert result[0]["timestamp"] == "2025-01-01T10:00:00+00:00"
        assert result[1]["symbol"] == "TSLA"

        # Also ensure requests.get was called with correct URL
        symbols = "aapl,googl,tsla,amzn,msft"
        expected_url = f"https://api.tiingo.com/iex/?tickers={symbols}&token={api_key}"
        mock_get.assert_called_once_with(
            expected_url, {"Content-Type": "application/json"}, timeout=10
        )

    @patch("producer.producer.requests.get")
    def test_get_stock_data_error(self, mock_get) -> None:
        """
        Test that get_stock_data() returns an empty list if an HTTPError or parse error occurs.
        """
        # 1. Mock an error
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("Bad Request")
        mock_get.return_value = mock_resp

        api_key = "FAKE_API_KEY"
        result = get_stock_data(api_key)
        assert not result  # empty due to error

    @patch("producer.producer.time.sleep", return_value=None)
    @patch("producer.producer.get_api_key", return_value="FAKE_API_KEY")
    def test_produce_data_basic(self, mock_api_key, mock_sleep) -> None:
        """
        Test produce_data() once through the loop with a mock KafkaProducer and mock get_stock_data.
        We'll break out of the infinite loop after one iteration by raising a custom exception.
        """

        fake_producer = MagicMock()
        # 1. Mock the environment variable
        with patch.dict(os.environ, {"KAFKA_BOOTSTRAP_SERVERS": "test-kafka:9092"}):
            # 2. Mock the KafkaProducer
            with patch("producer.producer.KafkaProducer", return_value=fake_producer):
                # 3. Mock get_stock_data with two stock prices and a custom exception
                with patch(
                    "producer.producer.get_stock_data",
                    side_effect=[
                        [
                            {
                                "symbol": "AAPL",
                                "price": 150.0,
                                "timestamp": "2025-01-01T10:00:00+00:00",
                            },
                            {
                                "symbol": "TSLA",
                                "price": 700.0,
                                "timestamp": "2025-01-01T11:00:00+00:00",
                            },
                        ],
                        EndOfTestData("Break loop"),
                    ],
                ) as mock_gsd:

                    # 4. Call produce_data() and catch EndOfTestData
                    try:
                        produce_data()
                    except EndOfTestData:
                        pass

                    # 5. Verify that KafkaProducer was created
                    fake_producer_inst = fake_producer
                    fake_producer_inst.send.assert_any_call(
                        "stock_prices",
                        {
                            "symbol": "AAPL",
                            "price": 150.0,
                            "timestamp": "2025-01-01T10:00:00+00:00",
                        },
                    )
                    fake_producer_inst.send.assert_any_call(
                        "stock_prices",
                        {
                            "symbol": "TSLA",
                            "price": 700.0,
                            "timestamp": "2025-01-01T11:00:00+00:00",
                        },
                    )

                    # Ensure get_api_key was called for "TIINGO_API_KEY"
                    mock_api_key.assert_called_with("TIINGO_API_KEY")
                    # Ensure get_stock_data was called with "FAKE_API_KEY"
                    mock_gsd.assert_called_with(api_key="FAKE_API_KEY")
