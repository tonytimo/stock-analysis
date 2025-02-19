# Stock Analysis Project

This project is a real-time stock analysis application that consists of several components working together to fetch, process, and visualize stock data, as well as generate alerts based on price fluctuations.

## Overview

The application is composed of the following services:

-   **Producer**: Fetches stock data from the Tingo API and publishes it to a Kafka topic.
-   **Consumer**: Consumes stock data from the Kafka topic, calculates price averages, and generates alerts when prices drop below a certain threshold. It also stores stock prices and alerts in a SQLite database.
-   **Webapp**: A Flask-based web application that provides a user interface to visualize real-time stock prices and display the latest stock alerts.
-   **Kafka**: A distributed streaming platform used for building real-time data pipelines and streaming applications.
-   **Zookeeper**: A centralized service for maintaining configuration information, naming, providing distributed synchronization, and providing group services.

## Architecture
+---------------------+ +-----------------+ +-------------------+ | Producer | | Kafka | | Consumer | | (Fetches stock data|--->| (Message Broker)|--->| (Analyzes & Alerts)| +---------------------+ +-----------------+ +-------------------+ | ^ | | | | v | v +---------------------+ +-----------------+ +-------------------+ | Tingo API | | Zookeeper | | SQLite DB | +---------------------+ +-----------------+ +-------------------+ | v +---------------------+ | Webapp | | (Visualizes data) | +---------------------+

## Requirements

-   Python 3.10
-   Poetry
-   Docker
-   Docker Compose

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Set up environment variables:**

    -   Create a [.env](http://_vscodecontentref_/0) file in the root directory.
    -   Add your Tingo API key to the [.env](http://_vscodecontentref_/1) file:

        ```
        TINGO_API_KEY=<your_tingo_api_key>
        ```

3.  **Start the services using Docker Compose:**

    ```bash
    docker-compose up --build
    ```

    This command builds the Docker images and starts all the services defined in the [docker-compose.yml](http://_vscodecontentref_/2) file.

4.  **Access the Webapp:**

    -   Open your web browser and navigate to `http://localhost:5000`.

## Configuration

-   **Kafka**: The Kafka broker is configured in the [docker-compose.yml](http://_vscodecontentref_/3) file. The `KAFKA_CFG_ADVERTISED_LISTENERS` environment variable should match the address that the producer and consumer use to connect to Kafka.
-   **Producer**: The producer fetches stock data for the symbols defined in the [producer.py](http://_vscodecontentref_/4) file. The `TINGO_API_KEY` environment variable is used to authenticate with the Tingo API.
-   **Consumer**: The consumer subscribes to the `stock_prices` Kafka topic and publishes alerts to the `stock_alerts` topic. The alert threshold is set to 5% below the average of the last 5 prices.
-   **Webapp**: The webapp fetches stock data and alerts from the SQLite database. The database file is stored in the [stock_data](http://_vscodecontentref_/5) Docker volume.

## Usage

1.  **View Real-Time Stock Prices**:
    -   Open the web application in your browser. The main page displays real-time stock prices for AAPL, GOOGL, TSLA, AMZN, and MSFT. The prices are updated every 95 seconds.

2.  **Receive Stock Alerts**:
    -   The web application also displays stock alerts when the price of a stock drops 5% below the average of the last 5 prices. An alert message will pop up in your browser.

##停止
To stop the application, run:

```bash
docker-compose down
