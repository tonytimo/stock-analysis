"""
This module fetches stock data from the Alpha Vantage API 
and produces it to a Kafka topic.

Functions:
    get_stock_data(symbol: str, api_key: str) -> dict[str, Any] | None:
        Fetches stock data for a given symbol from the Alpha Vantage API.

    produce_data() -> None:
        Continuously fetches stock data for a list of symbols 
        and sends it to a Kafka topic.
"""

import os
import time
import json
from typing import Any
import requests
from kafka import KafkaProducer
from helper import get_api_key


# TODO: Add better error handling


def get_stock_data(symbol: str, api_key: str) -> dict[str, Any] | None:
    """
    Args:
        symbol (str): The stock symbol to fetch data for.
        api_key (str): The API key for accessing the Alpha Vantage API.
    Returns:
        dict[str, Any] | None: A dictionary containing the stock data,
                            including symbol, price, volume, and timestamp.
                            Returns None if there is an error during the request.
    """
    try:
        # Requesting stock data
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        r = requests.get(url, timeout=10)
        data = r.json()

        # The API returns a nested JSON, extract price info
        global_quote = data.get("Global Quote", {})
        new_dict = {
            "symbol": global_quote.get("01. symbol", symbol),
            "price": float(global_quote.get("05. price", 0.0)),
            "volume": int(global_quote.get("06. volume", 0)),
            "timestamp": global_quote.get("07. latest trading day", ""),
        }

        return new_dict

    except Exception as e:
        print(f"error is: {e}")


def produce_data() -> None:
    """
    Continuously fetches stock data for a list of symbols
    and sends it to a Kafka topic.
    """

    kafka_server = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    producer = KafkaProducer(
        bootstrap_servers=kafka_server,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    symbols = ["AAPL", "GOOGL", "TSLA", "AMZN", "MSFT"]
    try:
        api_key = get_api_key("ALPHA_VANTAGE_API_KEY")
    except Exception as e:
        print(f"Error fetching API key: {e}")
        return

    while True:
        for sym in symbols:
            stock_info = get_stock_data(sym, api_key=api_key)
            producer.send("stock_prices", stock_info)
            print(f"Produced: {stock_info}")
            time.sleep(3)  # pace the requests to avoid rate limits


if __name__ == "__main__":
    produce_data()
