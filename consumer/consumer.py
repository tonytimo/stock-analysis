"""
This module consumes stock prices from the Kafka topic "stock_prices"
"""

import time
import os
import json
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from consumer.db_manager import init_db, insert_stock_alert, insert_stock_price


def consume_data() -> None:
    """
    This function will consumes stock prices from the Kafka topic
    "stock_prices" and produces alerts to the Kafka topic
    "stock_alerts" when a stock price is 5%
    below the average of the last 5 prices we consumed.
    """
    time.sleep(10)  # wait for Kafka to star
    kafka_server = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    try:
        consumer = KafkaConsumer(
            "stock_prices",
            bootstrap_servers=kafka_server,
            auto_offset_reset="earliest",
            group_id="stock_consumers",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        print("KafkaConsumer created successfully. " + f"Connected to {kafka_server}")

    except KafkaError as ke:
        print(f"Error creating KafkaConsumer: {ke}")
        return
    except Exception as e:
        print(f"Unexpected error creating KafkaConsumer: {e}")
        return

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

    # Initialize DB (create table if it doesn't exist)
    init_db()
    print("Consumer is ready and DB initialized...")

    recent_prices = {}
    old_avg_price = 0

    while True:
        for message in consumer:
            stock_data = message.value
            symbol = stock_data.get("symbol")
            price = stock_data.get("price")
            timestamp = stock_data.get("timestamp")

            if symbol is None or price is None:
                print("Invalid stock data received.")
                continue

            if symbol not in recent_prices:
                recent_prices[symbol] = []
            recent_prices[symbol].append(price)

            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except ValueError:
                    timestamp = datetime.utcnow()

            # Insert record
            insert_stock_price(symbol, price, timestamp)
            print(f"Inserted: {symbol}, {price}, {timestamp}")

            avg_price = sum(recent_prices[symbol]) / len(recent_prices[symbol])
            print(f"Received: Symbol={symbol}, Price={price}, Avg(5)={avg_price:.2f}")

            if len(recent_prices[symbol]) > 5:
                if price < old_avg_price * 0.95:
                    alert_data = {
                        "symbol": symbol,
                        "massage": f"Price {price} is 5% below avg {old_avg_price:.2f}",
                        "timestamp": timestamp,
                    }
                    try:
                        producer.send("stock_alerts", value=alert_data)
                        print(f"ALERT SENT: {alert_data}")

                    except (KafkaError, KafkaTimeoutError) as ke:
                        print(f"Kafka error while sending data: {ke}")
                    except Exception as e:
                        print(f"Unexpected error sending message to Kafka: {e}")

                    # Insert record
                    insert_stock_alert(symbol, price, timestamp)
                    print(f"Inserted: {symbol}, {price}, {timestamp}")

            if len(recent_prices[symbol]) > 5:
                recent_prices[symbol].pop(0)

            old_avg_price = avg_price


if __name__ == "__main__":
    consume_data()
