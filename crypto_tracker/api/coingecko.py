import aiohttp
import asyncio
from typing import List, Dict, Any
from crypto_tracker.utils import config

class CoinGeckoAPI:
    def __init__(self):
        self.base_url = config.COINGECKO_API_URL
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_coin_list(self) -> List[Dict[str, Any]]:
        """Fetches the list of all supported coins (ID, name, symbol)."""
        url = f"{self.base_url}/coins/list"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                # Add source field
                for coin in data:
                    coin['source'] = 'coingecko'
                    coin['rank'] = 999999 # Default rank for lightweight list
                return data
            return []

    async def get_top_coins(self, limit=100, order='market_cap_desc') -> List[Dict[str, Any]]:
        """Fetches market data for top coins."""
        url = f"{self.base_url}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': order,
            'per_page': limit,
            'page': 1,
            'sparkline': 'false'
        }
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            return []

    async def get_coins_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Fetches market data for specific coins by ID."""
        if not ids:
            return []
        
        url = f"{self.base_url}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'ids': ','.join(ids),
            'order': 'market_cap_desc',
            'per_page': len(ids),
            'page': 1,
            'sparkline': 'false'
        }
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            return []

    async def get_gainers_losers(self) -> Dict[str, List]:
        """
        CoinGecko doesn't have a direct free endpoint for gainers/losers list in one go 
        sorted by change without pagination logic or paying.
        However, we can fetch top 250 and sort them locally.
        """
        data = await self.get_top_coins(limit=250)
        if not data:
            return {'gainers': [], 'losers': []}
        
        sorted_data = sorted(data, key=lambda x: x.get('price_change_percentage_24h') or 0, reverse=True)
        return {
            'gainers': sorted_data[:15],
            'losers': sorted_data[-15:][::-1]
        }

    async def get_coin_market_chart(self, coin_id: str, days: str = '1') -> Dict[str, Any]:
        """Fetches historical market data (prices, market_caps, total_volumes)."""
        url = f"{self.base_url}/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days
        }
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            return {}

    async def get_trending(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search/trending"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                # Normalize trending data structure to match market data if possible
                # Trending returns 'item' key inside 'coins' list
                result = []
                for item in data.get('coins', []):
                    coin = item['item']
                    result.append({
                        'id': coin['id'],
                        'symbol': coin['symbol'],
                        'name': coin['name'],
                        'market_cap_rank': coin.get('market_cap_rank'),
                        'current_price': float(str(coin.get('data', {}).get('price', 0)).replace('$','').replace(',','')) if 'data' in coin else 0,
                        'price_change_percentage_24h': float(coin.get('data', {}).get('price_change_percentage_24h', {}).get('usd', 0)) if 'data' in coin else 0,
                         # Volume not always available in trending
                        'total_volume': float(str(coin.get('data', {}).get('total_volume', 0)).replace('$','').replace(',','')) if 'data' in coin else 0
                    })
                return result
            return []
