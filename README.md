# Stock Analysis Project

This project is a real-time stock analysis application that consists of several components working together to fetch, process, and visualize stock data, as well as generate alerts based on price fluctuations.

## Overview

The application is composed of the following services:

-   **Producer**: Fetches stock data from the Tingo API and publishes it to a Kafka topic.
-   **Consumer**: Consumes stock data from the Kafka topic, calculates price averages, and generates alerts when prices drop below a certain threshold. It also stores stock prices and alerts in a SQLite database.
-   **Webapp**: A Flask-based web application that provides a user interface to visualize real-time stock prices and display the latest stock alerts.
-   **Kafka**: A distributed streaming platform used for building real-time data pipelines and streaming applications.
-   **Zookeeper**: A centralized service for maintaining configuration information, naming, providing distributed synchronization, and providing group services.


## Requirements

-   Python 3.10
-   Poetry
-   Docker

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/tonytimo/stock-analysis.git
    ```

2.  **Set up environment variables:**

    -   Create a .env file in the root directory.
    -   Add your [Tiingo API](https://www.tiingo.com/) key to the .env file:

        ```
        TIINGO_API_KEY=<your_tiingo_api_key>
        ```
3.  **Install requirements with poetry**

    ```bash
    poetry install
    ```

3.  **Start the services using Docker Compose:**

    ```bash
    docker-compose up --build
    ```

    This command builds the Docker images and starts all the services defined in the [docker-compose.yml](https://github.com/tonytimo/stock-analysis/blob/main/docker-compose.yml) file.

4.  **Access the Webapp:**

    -   Open your web browser and navigate to `http://localhost:5000`.

## Usage

1.  **View Real-Time Stock Prices**:
    -   Open the web application in your browser. The main page displays real-time stock prices for AAPL, GOOGL, TSLA, AMZN, and MSFT. The prices are updated every 95 seconds.

2.  **Receive Stock Alerts**:
    -   The web application also displays stock alerts when the price of a stock drops 5% below the average of the last 5 prices. An alert message will pop up in your browser.

To stop the application, run:

```bash
docker-compose down
