import asyncio
import sys
import os

from rich.live import Live
from rich.panel import Panel
from rich.align import Align
from rich.console import Console
from rich.layout import Layout

from crypto_tracker.api.cache import CacheManager
from crypto_tracker.api.coingecko import CoinGeckoAPI
from crypto_tracker.api.binance import BinanceAPI
from crypto_tracker.utils.websocket_handler import BinanceWebSocket
from crypto_tracker.utils import indicators
from crypto_tracker.ui.search import SearchModal
from crypto_tracker.ui.chart import PlotextChart, make_layout
from crypto_tracker.ui.watchlist import create_watchlist_table
from crypto_tracker.utils import config
from crypto_tracker.utils.input_handler import InputHandler
import pandas as pd
from datetime import datetime

class CryptoTracker:
    def __init__(self):
        self.console = Console()
        self.cache = CacheManager()
        self.layout = make_layout()
        self.chart_renderer = PlotextChart()
        
        self.current_coin = None # {id, symbol, name}
        self.chart_data = pd.DataFrame()
        self.watchlist_data = []
        self.is_running = True
        
        # Settings
        self.timeframe = '1h'
        self.show_indicators = True
        self.chart_type = 'candle' # candle, line
        self.live_price = None
        self.sidebar_mode = 'Top' # Top, Favorites, Trending, Gainers, Losers
        
        # Initialize with Bitcoin
        self.current_coin = {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin', 'source': 'coingecko', 'rank': 1}
        
        self.binance_pairs = []
        self.ws = None
        
    async def initialize(self):
        """Load initial data"""
        self.console.print("[yellow]Initializing... Fetching coin list...[/yellow]")
        
        # 1. Load all coins if cache empty
        if self.cache.is_cache_empty():
            async with CoinGeckoAPI() as cg:
                try:
                    coins = await cg.get_coin_list()
                    self.cache.save_coins(coins)
                    self.console.print(f"[green]Loaded {len(coins)} coins into cache.[/green]")
                except Exception as e:
                    self.console.print(f"[red]Failed to load coins: {e}[/red]")
        
        # 2. Get Binance Pairs
        try:
            async with BinanceAPI() as bn:
                pairs = await bn.get_exchange_info()
                self.binance_pairs = [p['symbol'] for p in pairs]
        except Exception as e:
             self.console.print(f"[red]Failed to load binance pairs: {e}[/red]")

        # 3. Start WebSocket
        self.ws = BinanceWebSocket(self.on_ticker_update)
        self.ws.start()

        # 4. Initial Data Load
        await self.update_current_coin_data()
        await self.update_watchlist()

    def on_ticker_update(self, data):
        # Filter for current coin if it matches
        if not self.current_coin:
            return
            
        symbol = self.current_coin['symbol'].upper() + "USDT"
        
        # Data is a list of dicts from !ticker@arr
        target_ticker = next((x for x in data if x['s'] == symbol), None)
        
        if target_ticker:
            self.live_price = float(target_ticker['c'])

    def get_interval_params(self):
        # Map self.timeframe to Binance intervals and CoinGecko days
        # Timeframe: [H]1H [4]4H [D]Day [W]Week [M]Month [Y]Year
        mapping = {
            '1h': ('1h', '1'),
            '4h': ('4h', '1'),
            '1d': ('1d', '30'),
            '1w': ('1w', '90'),
            '1m': ('1M', '365'),
            '1y': ('1M', 'max') # Binance doesn't have 1Y, use 1M bars.
        }
        return mapping.get(self.timeframe.lower(), ('1h', '1'))

    async def update_current_coin_data(self):
        symbol = self.current_coin['symbol'].upper() + "USDT"
        
        df = pd.DataFrame()
        binance_interval, cg_days = self.get_interval_params()

        # Try Binance first
        if symbol in self.binance_pairs:
            async with BinanceAPI() as bn:
                klines = await bn.get_klines(symbol, interval=binance_interval)
                if klines:
                    data = []
                    for k in klines:
                        data.append({
                            'time': datetime.fromtimestamp(k[0]/1000),
                            'open': float(k[1]),
                            'high': float(k[2]),
                            'low': float(k[3]),
                            'close': float(k[4]),
                            'volume': float(k[5])
                        })
                    df = pd.DataFrame(data)
        else:
            # Fallback to CoinGecko
            async with CoinGeckoAPI() as cg:
                data = await cg.get_coin_market_chart(self.current_coin['id'], days=cg_days)
                prices = data.get('prices', [])
                if prices:
                    ohlc_data = []
                    for p in prices:
                        # Approximation for line chart
                        ohlc_data.append({
                            'time': datetime.fromtimestamp(p[0]/1000),
                            'open': p[1], 'high': p[1], 'low': p[1], 'close': p[1], 'volume': 0
                        })
                    df = pd.DataFrame(ohlc_data)

        if not df.empty:
            # Only calculate if we have enough data
            if len(df) > 50:
                df = indicators.calculate_indicators(df)
            self.chart_data = df
            self.live_price = df.iloc[-1]['close']

    async def update_watchlist(self):
        async with CoinGeckoAPI() as cg:
            if self.sidebar_mode == 'Top':
                self.watchlist_data = await cg.get_top_coins(limit=15)
            elif self.sidebar_mode == 'Trending':
                self.watchlist_data = await cg.get_trending()
            elif self.sidebar_mode == 'Favorites':
                fav_ids = self.cache.get_favorites()
                if fav_ids:
                    # Fetch details for favorites
                    # Need an endpoint for multiple ids, use markets with ids param
                    # CoinGecko `coins/markets` supports `ids`
                     # We need to construct url manually or update wrapper.
                     # For simplicity, reuse top coins logic but filter/param
                     # Actually let's just hack it: fetch top 250 and filter? No, unreliable.
                     # Better: Add `get_coins_by_id` to CoinGeckoAPI or use `markets` with `ids`
                     # Let's implement a basic fallback: assume they are in top 250 for now or fetch individual
                     pass
                self.watchlist_data = [] # Placeholder until improved API wrapper
            elif self.sidebar_mode in ['Gainers', 'Losers']:
                gl = await cg.get_gainers_losers()
                if self.sidebar_mode == 'Gainers':
                    self.watchlist_data = gl['gainers']
                else:
                    self.watchlist_data = gl['losers']

    def render_ui(self) -> Layout:
        # Header
        title_str = f"🪙 UNIVERSAL CRYPTO TRACKER v3.0 | {self.current_coin['name']} ({self.current_coin['symbol'].upper()})"
        if self.live_price:
             title_str += f" | ${self.live_price:,.2f}"
        
        self.layout["header"].update(Panel(
            Align.center(title_str),
            style="bold white on blue"
        ))

        # Chart
        if not self.chart_data.empty:
            title = f"{self.current_coin['symbol'].upper()}/USDT {self.timeframe.upper()}"
            chart_str = self.chart_renderer.render(self.chart_data, title, chart_type=self.chart_type)
            self.layout["chart"].update(Panel(chart_str))
        else:
            self.layout["chart"].update(Panel("Loading Chart or Data Unavailable..."))

        # Info Bar
        price = self.live_price or 0
        rank = self.current_coin.get('rank', 'N/A')
        
        # Detailed stats
        high_24h = self.chart_data['high'].max() if not self.chart_data.empty else 0
        low_24h = self.chart_data['low'].min() if not self.chart_data.empty else 0
        vol = self.chart_data['volume'].sum() if not self.chart_data.empty else 0
        
        info_text = (
            f"Price: ${price:,.2f} | Rank: #{rank} | "
            f"High: ${high_24h:,.2f} | Low: ${low_24h:,.2f} | Vol: {vol:,.0f} | "
            f"TF: {self.timeframe.upper()} | Ind: {'ON' if self.show_indicators else 'OFF'}"
        )
        self.layout["info_bar"].update(Panel(info_text))

        # Sidebar (Watchlist)
        self.layout["sidebar"].update(create_watchlist_table(self.watchlist_data))
        # Add Title to sidebar panel? Watchlist table has title.
        
        # Footer / Controls
        controls = (
            "[/] Search  [1-9] Select  [H,4,D,W,M,Y] TF  [I] Ind  [F] Fav/View  "
            "[T] Trend  [G] Gain  [L] Lose  [C] Chart Type  [Q] Quit"
        )
        self.layout["footer"].update(Panel(controls, title="Controls"))

        return self.layout

    async def run(self):
        await self.initialize()
        
        with InputHandler() as input_handler:
            with Live(self.render_ui(), refresh_per_second=4, screen=True) as live:
                while self.is_running:
                    key = input_handler.get_key()
                    if key:
                        if key.lower() == 'q':
                            self.is_running = False
                        elif key == '/':
                            live.stop()
                            input_handler.__exit__(None, None, None)
                            coins = self.cache.get_all_coins()
                            search = SearchModal(coins)
                            result = search.show()
                            if result:
                                self.current_coin = result
                                await self.update_current_coin_data()
                            input_handler.__enter__()
                            live.start()
                        
                        elif key in [str(i) for i in range(1, 10)]:
                            idx = int(key) - 1
                            if idx < len(self.watchlist_data):
                                w_coin = self.watchlist_data[idx]
                                self.current_coin = {
                                    'id': w_coin['id'],
                                    'symbol': w_coin['symbol'],
                                    'name': w_coin['name'],
                                    'rank': w_coin.get('market_cap_rank', 0)
                                }
                                await self.update_current_coin_data()
                        
                        elif key.lower() in ['h', '4', 'd', 'w', 'm', 'y']:
                            map_tf = {'h':'1h', '4':'4h', 'd':'1d', 'w':'1w', 'm':'1m', 'y':'1y'}
                            self.timeframe = map_tf[key.lower()]
                            await self.update_current_coin_data()
                        
                        elif key.lower() == 'i':
                            self.show_indicators = not self.show_indicators
                        
                        elif key.lower() == 'f':
                            # Toggle favorite
                            favorites = self.cache.get_favorites()
                            if self.current_coin['id'] in favorites:
                                self.cache.remove_favorite(self.current_coin['id'])
                            else:
                                self.cache.add_favorite(self.current_coin['id'])
                        
                        elif key.lower() == 'v':
                            # View favorites
                            self.sidebar_mode = 'Favorites'
                            await self.update_watchlist()
                                
                        elif key.lower() == 't':
                            self.sidebar_mode = 'Trending'
                            await self.update_watchlist()
                            
                        elif key.lower() == 'g':
                            self.sidebar_mode = 'Gainers'
                            await self.update_watchlist()
                            
                        elif key.lower() == 'l':
                            self.sidebar_mode = 'Losers'
                            await self.update_watchlist()
                            
                        elif key.lower() == 'c':
                            # Toggle chart type
                            if self.chart_type == 'candle':
                                self.chart_type = 'line'
                            else:
                                self.chart_type = 'candle'

                    live.update(self.render_ui())
                    await asyncio.sleep(0.1)
            
        if self.ws:
            self.ws.stop()

if __name__ == "__main__":
    app = CryptoTracker()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
