import os

# Database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'coins.db')
FAVORITES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'favorites.json')

# APIs
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
BINANCE_API_URL = "https://api.binance.com/api/v3"
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"

# Settings
REFRESH_RATE = 10  # seconds for watchlist
CHART_HEIGHT = 20
