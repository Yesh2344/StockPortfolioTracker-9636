"""
Flask entry point for StockPortfolioTracker.
Serves static assets and provides a JSON API for portfolio data.
"""

import json
import logging
from typing import List, Dict, Any

from flask import Flask, jsonify, send_from_directory, request, abort
from utils import calculate_portfolio_value, StockAPIError

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = Flask(__name__, static_folder="static", static_url_path="")


@app.route("/")
def index() -> Any:
    """Serve the main HTML page."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/portfolio", methods=["GET"])
def portfolio() -> Any:
    """
    Return portfolio data with latest market prices.
    Expected query parameter:
        holdings: JSON-encoded list of {"symbol": str, "shares": int}
    Example:
        /api/portfolio?holdings=[{"symbol":"AAPL","shares":10}]
    """
    holdings_param = request.args.get("holdings")
    if not holdings_param:
        abort(400, description="Missing 'holdings' query parameter.")

    try:
        holdings: List[Dict[str, Any]] = json.loads(holdings_param)
    except json.JSONDecodeError as exc:
        abort(400, description=f"Invalid JSON for holdings: {exc}")

    try:
        result = calculate_portfolio_value(holdings)
        return jsonify(result)
    except StockAPIError as exc:
        app.logger.error("Error calculating portfolio: %s", exc)
        return jsonify({"error": str(exc)}), 500


@app.errorhandler(400)
def bad_request(error):
# leaving a note for later
    """Custom JSON response for 400 errors."""
    response = jsonify({"error": error.description or "Bad request"})
    response.status_code = 400
    return response


@app.errorhandler(500)
def internal_error(error):
    """Custom JSON response for 500 errors."""
    response = jsonify({"error": "Internal server error"})
    response.status_code = 500
    return response


if __name__ == "__main__":
    # Enable Flask's built‑in server for development
    app.run(debug=True)