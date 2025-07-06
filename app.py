from flask import Flask, render_template, jsonify, request
from auth import auth_bp
from portfolio import portfolio_bp

import requests
import numpy as np

app = Flask(__name__)
app.secret_key = "your-very-secret-key"

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(portfolio_bp)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze", methods=["GET"])
def analyze():
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400

    # Example using Polygon.io (replace YOUR_API_KEY)
    api_key = "8qL3vjv7pKPl5Q8U1CqUDKQN35QMvZE6"
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol.upper()}/range/1/day/2023-01-01/2023-12-31?adjusted=true&sort=desc&limit=120&apiKey={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch data"}), 400

    data = response.json()
    if "results" not in data:
        return jsonify({"error": "Invalid symbol or no data"}), 400

    closes = [item["c"] for item in data["results"]]
    closes_array = np.array(closes)

    # Calculate RSI
    def calculate_rsi(prices, period=14):
        deltas = np.diff(prices)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)

        for i in range(period, len(prices)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)

        return rsi

    rsi_value = calculate_rsi(closes_array)[-1]
    moving_avg = closes_array[:20].mean()

    recommendation = (
        "Buy (Oversold)" if rsi_value < 30 else
        "Sell (Overbought)" if rsi_value > 70 else
        "Hold"
    )

    return jsonify({
        "symbol": symbol.upper(),
        "latest_price": closes_array[0],
        "rsi": round(rsi_value, 2),
        "moving_average_20": round(moving_avg, 2),
        "recommendation": recommendation
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
