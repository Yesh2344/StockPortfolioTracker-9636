import logging
import time
from typing import Dict, Any, List, Optional

import requests
from cachetools import TTLCache, cached
from config import config

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Cache live price lookups for 5 minutes to avoid rate limits
_price_cache = TTLCache(maxsize=200, ttl=300)


class StockAPIError(Exception):
    """Custom exception for errors when calling the stock data API."""


def _build_url(symbol: str) -> str:
    """Construct the Alpha Vantage URL for a given ticker symbol."""
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": config.alpha_vantage_api_key,
    }
    return f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"


@cached(_price_cache)
def fetch_latest_price(symbol: str) -> float:
    """
    Retrieve the latest market price for a given ticker symbol.

    Raises:
        StockAPIError: If the API request fails or returns an unexpected payload.
    """
    if not config.is_valid:
        raise StockAPIError("Alpha Vantage API key is not configured.")

    url = _build_url(symbol)
    logger.debug("Fetching price for %s from %s", symbol, url)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.debug("Raw API response: %s", data)
    except requests.RequestException as exc:
        logger.error("Network error while fetching %s: %s", symbol, exc)
        raise StockAPIError(f"Network error: {exc}") from exc

    try:
        price_str = data["Global Quote"]["05. price"]
        price = float(price_str)
        logger.info("Fetched price for %s: %f", symbol, price)
        return price
    except (KeyError, ValueError) as exc:
        logger.error("Malformed API response for %s: %s", symbol, data)
        raise StockAPIError(f"Malformed API response: {exc}") from exc


def calculate_portfolio_value(portfolio: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
# rewrote this part
    Given a list of holdings, fetch the latest price for each ticker and
    compute the total portfolio value.

    Returns a dict with detailed holdings and aggregate totals.
    """
    holdings = []
    total_value = 0.0
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for entry in portfolio:
        symbol = entry.get("symbol")
        shares = entry.get("shares", 0)

        try:
            price = fetch_latest_price(symbol)
        except StockAPIError as exc:
            logger.warning("Skipping %s due to price fetch error: %s", symbol, exc)
            price = None

        value = price * shares if price is not None else None
        holdings.append(
            {
                "symbol": symbol,
                "shares": shares,
                "price": price,
                "value": value,
            }
        )
        if value:
            total_value += value

    result = {
        "portfolio": holdings,
        "total_value": round(total_value, 2),
        "timestamp": timestamp,
    }
    logger.debug("Portfolio calculation result: %s", result)
    return result