"""
This module contains the Flask app that serves the web interface.
"""

from flask import Flask, Response, jsonify, render_template

from consumer.db_manager import get_last_stock_alert, get_recent_stock_prices, init_db


app = Flask(__name__)


@app.route("/")
def index() -> str:
    """
    Renders the main page.
    """

    return render_template("index.html")


@app.route("/api/stocks")
def api_stocks() -> Response:
    """
    Returns recent stock data in JSON form. The front-end
    will poll this endpoint periodically to update the chart.
    """
    records = get_recent_stock_prices(limit=50)
    # Group by symbol
    data = {}
    for r in records:
        if r.symbol not in data:
            data[r.symbol] = []
        data[r.symbol].append({"price": r.price, "timestamp": r.timestamp.isoformat()})
    return jsonify(data)


@app.route("/api/latest-alert")
def latest_alert() -> Response:
    """
    Returns the most recent alert in JSON format.
    If no alert exists, returns an empty object {}.
    """
    alert = get_last_stock_alert()
    if alert is None:
        return jsonify({})  # no alerts yet
    return jsonify(
        {
            "id": alert.id,
            "symbol": alert.symbol,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
        }
    )


if __name__ == "__main__":
    init_db()  # ensure DB schema
    app.run(host="0.0.0.0", port=5000)
