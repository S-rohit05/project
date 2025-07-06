from flask import Flask, render_template, request, jsonify
import requests
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = "8qL3vjv7pKPl5Q8U1CqUDKQN35QMvZE6"

# Helper function: calculate RSI
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
def calculate_macd(prices, slow=26, fast=12, signal=9):
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def ema(prices, period):
    ema_values = np.zeros_like(prices)
    k = 2 / (period + 1)
    ema_values[0] = prices[0]
    for i in range(1, len(prices)):
        ema_values[i] = prices[i] * k + ema_values[i - 1] * (1 - k)
    return ema_values

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze", methods=["GET"])
def analyze():
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400

    # Calculate date range (last 30 days)
    today = datetime.today()
    start_date = (today - timedelta(days=45)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    # Fetch data from Polygon.io
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol.upper()}/range/1/day/{start_date}/{end_date}"
    params = {
        "adjusted": "true",
        "sort": "desc",
        "limit": "30",
        "apiKey": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "results" not in data or len(data["results"]) == 0:
        return jsonify({"error": "Invalid symbol or no data available"}), 400

    # Extract close prices
    closes = [day["c"] for day in data["results"]]
    closes_array = np.array(closes)
    macd_line, signal_line, histogram = calculate_macd(closes_array)


    # Calculate RSI and Moving Average
    if len(closes_array) < 20:
        return jsonify({"error": "Not enough data to compute indicators"}), 400

    rsi = calculate_rsi(closes_array)[-1]
    moving_avg = closes_array[:20].mean()

    # Simple decision logic
    if rsi < 30:
        recommendation = "Buy (Oversold)"
    elif rsi > 70:
        recommendation = "Sell (Overbought)"
    else:
        recommendation = "Hold"

    return jsonify({
    "symbol": symbol.upper(),
    "latest_price": closes_array[0],
    "rsi": round(rsi, 2),
    "moving_average_20": round(moving_avg, 2),
    "recommendation": recommendation,
    "dates": [datetime.utcfromtimestamp(day["t"]/1000).strftime('%Y-%m-%d') for day in data["results"]],
    "closes": closes,
    "rsi_series": list(calculate_rsi(closes_array)),
    "macd_line": list(macd_line),
    "signal_line": list(signal_line),
    "histogram": list(histogram)
})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
