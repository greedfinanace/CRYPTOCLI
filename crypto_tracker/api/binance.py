import aiohttp
import asyncio
from typing import List, Dict, Any
from crypto_tracker.utils import config

class BinanceAPI:
    def __init__(self):
        self.base_url = config.BINANCE_API_URL
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_exchange_info(self) -> List[Dict[str, Any]]:
        """Fetches all trading pairs."""
        url = f"{self.base_url}/exchangeInfo"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                symbols = data.get('symbols', [])
                # Filter for USDT pairs
                return [s for s in symbols if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
            return []

    async def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[List[Any]]:
        """
        Fetches candlestick data.
        Intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        """
        url = f"{self.base_url}/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            return []

    async def get_ticker_24hr(self, symbol: str = None) -> Any:
        """Fetches 24hr ticker price change statistics."""
        url = f"{self.base_url}/ticker/24hr"
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            return []
