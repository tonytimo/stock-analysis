"""
This module fetches stock data from the Tiingo API 
and produces it to a Kafka topic.
"""

import os
import time
import json
from typing import Any
import requests
from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from requests.exceptions import HTTPError, ConnectionError, Timeout
from helper import get_api_key


def get_stock_data(api_key: str) -> list[dict[str, Any]]:
    """
    Args:
        api_key (str): The API key for accessing the Tiingo API.
    Returns:
        list[dict[str, Any]] : A list of dictionaries containing the stock data,
                               including symbol, price and timestamp.
                               Returns empty list if there is an error during the request.
    """

    # Requesting stock data for multiple symbols
    symbols = "aapl,googl,tsla,amzn,msft"
    headers = {"Content-Type": "application/json"}
    url = f"https://api.tiingo.com/iex/?tickers={symbols}&token={api_key}"

    try:
        r = requests.get(url, headers, timeout=10)
        r.raise_for_status()
        data = r.json()

    except (HTTPError, ConnectionError, Timeout, json.JSONDecodeError) as e:
        print("Request failed: %s", e)
        return []

    # Validate structure and build the results
    if not isinstance(data, list):
        print(f"Unexpected data format (expected list): {data}")
        return []

    # make a list of dictionaries with the required data
    # if the data is not found return None
    new_list = []
    for item in data:
        new_dict = {
            "symbol": item.get("ticker", None),
            "price": item.get("tngoLast", None),
            "timestamp": item.get("timestamp", None),
        }
        new_list.append(new_dict)

    return new_list


def produce_data() -> None:
    """
    Continuously fetches stock data and sends it to a Kafka topic.
    """
    time.sleep(10)  # wait for Kafka to start
    kafka_server = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    try:
        producer = KafkaProducer(
            bootstrap_servers=kafka_server,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        print(f"KafkaProducer created successfully. Connected to {kafka_server}")

    except KafkaError as ke:
        print(f"Error creating KafkaProducer: {ke}")
        return
    except Exception as e:
        print(f"Unexpected error creating KafkaProducer: {e}")
        return

    try:
        api_key = get_api_key("TIINGO_API_KEY")
    except Exception as e:
        print(f"Error fetching API key: {e}")
        return

    while True:
        stock_info = get_stock_data(api_key=api_key)
        if not stock_info:
            print("No stock data found.")
            time.sleep(90)
            continue
        try:
            for stock in stock_info:
                producer.send("stock_prices", stock)
                print(f"Produced: {stock}")
        except (KafkaError, KafkaTimeoutError) as ke:
            print(f"Kafka error while sending data: {ke}")
        except Exception as e:
            print(f"Unexpected error sending message to Kafka: {e}")

        time.sleep(90)  # pace the requests to avoid rate limits 1000 requests/day


if __name__ == "__main__":
    produce_data()
