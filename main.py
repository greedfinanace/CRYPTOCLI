import asyncio
import sys
import os

# Set up path resolution
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Debug check for package existence
PACKAGE_DIR = os.path.join(SCRIPT_DIR, 'crypto_tracker')
if not os.path.exists(PACKAGE_DIR):
    print(f"CRITICAL ERROR: 'crypto_tracker' folder not found in {SCRIPT_DIR}")
    sys.exit(1)

try:
    from rich.live import Live
    from rich.panel import Panel
    from rich.align import Align
    from rich.console import Console
    from rich.layout import Layout
    from crypto_tracker.ui.chart import PlotextChart, make_layout
    from crypto_tracker.ui.ascii_chart import AsciiCandleChart
except ImportError as e:
    print("Dependency Error: " + str(e))
    pass 

try:
    from crypto_tracker.api.cache import CacheManager
    from crypto_tracker.api.coingecko import CoinGeckoAPI
    from crypto_tracker.api.binance import BinanceAPI
    from crypto_tracker.utils.websocket_handler import BinanceWebSocket
    from crypto_tracker.utils import indicators
    from crypto_tracker.ui.search import SearchModal
    from crypto_tracker.ui.watchlist import create_watchlist_table
    from crypto_tracker.ui.help import HelpModal
    from crypto_tracker.utils import config
    from crypto_tracker.utils.input_handler import InputHandler
    from crypto_tracker.ui.big_price import BigPriceRenderer
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

import pandas as pd
from datetime import datetime

class CryptoTracker:
    def __init__(self):
        self.console = Console()
        self.cache = CacheManager()
        self.layout = make_layout()
        self.plotext_renderer = PlotextChart()
        self.ascii_renderer = AsciiCandleChart()
        self.big_price_renderer = BigPriceRenderer()
        
        self.current_coin = None 
        self.chart_data = pd.DataFrame()
        self.watchlist_data = []
        self.is_running = True
        
        # Settings
        self.timeframe = '1h'
        self.chart_type = 'ascii' # default to user preference
        self.live_price = None
        self.sidebar_mode = 'Top'
        self.show_chart = True
        self.view_mode = 'standard' # 'standard' or 'big_price'
        
        # Layout Settings
        self.chart_ratio = 3
        self.sidebar_ratio = 1
        self.levels_height = 4
        
        # Indicator State
        self.active_indicators = {'sma', 'rsi'} # Default set
        self.show_liquidation_ob = False
        
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
                    
                    # Fetch top 250 coins metadata
                    self.console.print("[yellow]Updating ranks for top coins...[/yellow]")
                    top_coins = await cg.get_top_coins(limit=250)
                    # Update these in cache
                    coins_update = []
                    for c in top_coins:
                        coins_update.append({
                            'id': c['id'],
                            'symbol': c['symbol'],
                            'name': c['name'],
                            'rank': c['market_cap_rank'],
                            'source': 'coingecko'
                        })
                    self.cache.save_coins(coins_update)
                    
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
        if not self.current_coin:
            return
        symbol = self.current_coin['symbol'].upper() + "USDT"
        target_ticker = next((x for x in data if x['s'] == symbol), None)
        if target_ticker:
            self.live_price = float(target_ticker['c'])

    def get_interval_params(self):
        mapping = {
            '1m': ('1m', '1'),
            '5m': ('5m', '1'),
            '15m': ('15m', '1'),
            '30m': ('30m', '1'),
            '1h': ('1h', '1'),
            '4h': ('4h', '1'),
            '1d': ('1d', '30'),
            '1w': ('1w', '90'),
            '1m_month': ('1M', '365'), # Renamed from '1m' to avoid conflict
            '1y': ('1M', 'max')
        }
        # Handle the old '1m' key if it comes from the 'M' keypress (Month)
        if self.timeframe == '1m' and mapping.get('1m')[0] == '1m': 
             # This is ambiguous, but usually M key means Month in standard TUI
             pass
        
        return mapping.get(self.timeframe.lower(), ('1h', '1'))

    async def update_current_coin_data(self):
        symbol = self.current_coin['symbol'].upper() + "USDT"
        df = pd.DataFrame()
        binance_interval, cg_days = self.get_interval_params()

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
            async with CoinGeckoAPI() as cg:
                data = await cg.get_coin_market_chart(self.current_coin['id'], days=cg_days)
                prices = data.get('prices', [])
                if prices:
                    ohlc_data = []
                    for p in prices:
                        ohlc_data.append({
                            'time': datetime.fromtimestamp(p[0]/1000),
                            'open': p[1], 'high': p[1], 'low': p[1], 'close': p[1], 'volume': 0
                        })
                    df = pd.DataFrame(ohlc_data)

        if not df.empty:
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
                    self.watchlist_data = await cg.get_coins_by_ids(fav_ids)
                else:
                    self.watchlist_data = []
            elif self.sidebar_mode in ['Gainers', 'Losers']:
                gl = await cg.get_gainers_losers()
                if self.sidebar_mode == 'Gainers':
                    self.watchlist_data = gl['gainers']
                else:
                    self.watchlist_data = gl['losers']

    def render_ui(self) -> Layout:
        # Handle Big Price Mode
        if self.view_mode == 'big_price':
            price = self.live_price or 0
            # Calculate change if data exists
            change = 0
            if not self.chart_data.empty:
                open_price = self.chart_data['open'].iloc[-1]
                if open_price > 0:
                    change = ((price - open_price) / open_price) * 100
            
            layout = Layout()
            layout.update(self.big_price_renderer.render(
                self.current_coin['symbol'],
                price,
                change
            ))
            return layout

        # Header
        title_str = f"🪙 UNIVERSAL CRYPTO TRACKER v3.0 | {self.current_coin['name']} ({self.current_coin['symbol'].upper()})"
        if self.live_price:
             title_str += f" | ${self.live_price:,.2f}"
        
        self.layout["header"].update(Panel(
            Align.center(title_str),
            style="bold white on blue"
        ))

        # Chart
        if self.show_chart and not self.chart_data.empty:
            title = f"{self.current_coin['symbol'].upper()}/USDT {self.timeframe.upper()}"
            
            if self.chart_type == 'ascii':
                # Pass specific flags to ASCII renderer
                # Render Chart
                chart_str = self.ascii_renderer.render(
                    self.chart_data, 
                    title, 
                    active_indicators=self.active_indicators,
                    show_liq_ob=self.show_liquidation_ob
                )
                # Render Levels Panel separately
                levels_panel = self.ascii_renderer.render_levels_panel(
                    self.chart_data,
                    self.show_liquidation_ob
                )
            else:
                # Legacy plotext renderer
                chart_str = self.plotext_renderer.render(self.chart_data, title, chart_type=self.chart_type)
                levels_panel = None
                
            self.layout["chart"].update(Panel(chart_str))
            self.layout["chart"].ratio = 1 # Reset to fill available space
            
            # Update Levels Layout
            if levels_panel:
                self.layout["levels"].update(levels_panel)
                self.layout["levels"].size = self.levels_height
            else:
                self.layout["levels"].update(Panel("")) # Clear it
                self.layout["levels"].size = 0
                
        elif not self.show_chart:
             # Chart Hidden -> Show Big Price in its place
             price = self.live_price or 0
             change = 0
             if not self.chart_data.empty:
                open_price = self.chart_data['open'].iloc[-1]
                if open_price > 0:
                    change = ((price - open_price) / open_price) * 100
            
             big_price_panel = self.big_price_renderer.render(
                self.current_coin['symbol'],
                price,
                change
             )
             
             self.layout["chart"].update(big_price_panel)
             self.layout["chart"].ratio = 1 # Ensure it fills space
             
             # Still show levels if enabled
             levels_panel = self.ascii_renderer.render_levels_panel(
                    self.chart_data,
                    self.show_liquidation_ob
             )
             if levels_panel:
                self.layout["levels"].update(levels_panel)
                self.layout["levels"].size = self.levels_height
             else:
                self.layout["levels"].size = 0
             
        else:
            self.layout["chart"].update(Panel("Loading Chart or Data Unavailable..."))
            self.layout["levels"].size = 0

        # Info Bar
        price = self.live_price or 0
        rank = self.current_coin.get('rank', 'N/A')
        
        high_24h = self.chart_data['high'].max() if not self.chart_data.empty else 0
        low_24h = self.chart_data['low'].min() if not self.chart_data.empty else 0
        vol = self.chart_data['volume'].sum() if not self.chart_data.empty else 0
        
        # Display active indicators status
        ind_status = ",".join(list(self.active_indicators)) if self.active_indicators else "None"
        if self.show_liquidation_ob:
            ind_status += ",LIQ/OB"
            
        info_text = (
            f"Price: ${price:,.2f} | Rank: #{rank} | "
            f"High: ${high_24h:,.2f} | Low: ${low_24h:,.2f} | Vol: {vol:,.0f} | "
            f"TF: {self.timeframe.upper()} | Inds: {ind_status}"
        )
        self.layout["info_bar"].update(Panel(info_text))

        # Sidebar
        self.layout["sidebar"].update(create_watchlist_table(self.watchlist_data))
        
        # Apply Dynamic Ratios
        self.layout["chart_area"].ratio = self.chart_ratio
        self.layout["sidebar"].ratio = self.sidebar_ratio
        
        # Footer / Controls
        controls = (
            "\\[S] Search  \\[1-9] Select  \\[H,4,D,W,M,Y] TF  \\[M] Min TF  \\[I] Ind Menu  \\[O] Liq/OB  \\[F] Fav  "
            "\\[T] Trend  \\[G] Gain  \\[L] Lose  \\[C] Chart Mode  \\[X] Hide Chart  \\[<,>] Resize Sidebar  \\[[,]] Resize Levels  \\[?] Help  \\[Q] Quit"
        )
        self.layout["footer"].update(Panel(controls, title="Controls"))

        return self.layout

    async def toggle_minute_menu(self, live_ctx, input_handler):
        """Menu for sub-1h timeframes"""
        live_ctx.stop()
        input_handler.__exit__(None, None, None)
        
        print("\n--- Minute Timeframes ---")
        print("1. 1 Minute")
        print("2. 5 Minutes")
        print("3. 15 Minutes")
        print("4. 30 Minutes")
        print("Press Enter to cancel")
        
        choice = input("Select option: ")
        if choice == '1': self.timeframe = '1m'
        elif choice == '2': self.timeframe = '5m'
        elif choice == '3': self.timeframe = '15m'
        elif choice == '4': self.timeframe = '30m'
        
        await self.update_current_coin_data()
            
        input_handler.__enter__()
        live_ctx.start()

    async def toggle_indicator_menu(self, live_ctx, input_handler):
        """Simple menu to toggle indicators"""
        # Stop live mode temporarily
        live_ctx.stop()
        input_handler.__exit__(None, None, None)
        
        print("\n--- Indicator Menu ---")
        print("Current Active: " + ", ".join(self.active_indicators))
        print("1. Toggle SMA")
        print("2. Toggle EMA")
        print("3. Toggle Bollinger Bands (BB)")
        print("4. Toggle RSI")
        print("5. Clear All")
        print("Press Enter to return")
        
        choice = input("Select option: ")
        if choice == '1':
            if 'sma' in self.active_indicators: self.active_indicators.remove('sma')
            else: self.active_indicators.add('sma')
        elif choice == '2':
            if 'ema' in self.active_indicators: self.active_indicators.remove('ema')
            else: self.active_indicators.add('ema')
        elif choice == '3':
            if 'bb' in self.active_indicators: self.active_indicators.remove('bb')
            else: self.active_indicators.add('bb')
        elif choice == '4':
            if 'rsi' in self.active_indicators: self.active_indicators.remove('rsi')
            else: self.active_indicators.add('rsi')
        elif choice == '5':
            self.active_indicators.clear()
            
        # Restart live mode
        input_handler.__enter__()
        live_ctx.start()

    async def run(self):
        await self.initialize()
        
        with InputHandler() as input_handler:
            with Live(self.render_ui(), refresh_per_second=4, screen=True) as live:
                while self.is_running:
                    key = input_handler.get_key()
                    if key:
                        if key.lower() == 'q':
                            self.is_running = False
                        elif key.lower() == 's':
                            live.stop()
                            input_handler.__exit__(None, None, None)
                            coins = self.cache.get_all_coins()
                            search = SearchModal(coins)
                            result = await search.show()
                            if result:
                                self.current_coin = result
                                await self.update_current_coin_data()
                            input_handler.__enter__()
                            live.start()
                        
                        elif key in ["'", "?"]:
                            live.stop()
                            input_handler.__exit__(None, None, None)
                            
                            help_modal = HelpModal()
                            # Temporarily clear screen or just print over
                            console = Console()
                            console.clear()
                            console.print(help_modal.render())
                            
                            input() # Wait for any key (enter)
                            
                            input_handler.__enter__()
                            live.start()

                        elif key == ',' or key == '<':
                            # Shrink Sidebar / Grow Chart
                            if self.sidebar_ratio > 1:
                                self.sidebar_ratio -= 1
                                self.chart_ratio += 1
                                
                        elif key == '.' or key == '>':
                            # Grow Sidebar / Shrink Chart
                            if self.chart_ratio > 1:
                                self.sidebar_ratio += 1
                                self.chart_ratio -= 1
                                
                        elif key == '[':
                             # Shrink Levels Panel
                             if self.levels_height > 3:
                                 self.levels_height -= 1
                                 
                        elif key == ']':
                             # Grow Levels Panel
                             if self.levels_height < 40:
                                 self.levels_height += 1

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
                            await self.toggle_indicator_menu(live, input_handler)
                        
                        elif key.lower() == 'o':
                            self.show_liquidation_ob = not self.show_liquidation_ob
                            
                        elif key.lower() == 'f':
                            favorites = self.cache.get_favorites()
                            if self.current_coin['id'] in favorites:
                                self.cache.remove_favorite(self.current_coin['id'])
                            else:
                                self.cache.add_favorite(self.current_coin['id'])
                        
                        elif key.lower() == 'v':
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
                            # Cycle chart types: ascii -> candle (plotext) -> line (plotext)
                            if self.chart_type == 'ascii':
                                self.chart_type = 'candle'
                            elif self.chart_type == 'candle':
                                self.chart_type = 'line'
                            else:
                                self.chart_type = 'ascii'
                                
                        elif key.lower() == 'x':
                            self.show_chart = not self.show_chart
                            
                        elif key.lower() == 'm':
                            await self.toggle_minute_menu(live, input_handler)
                            
                        elif key.lower() == 'p':
                            if self.view_mode == 'standard':
                                self.view_mode = 'big_price'
                            else:
                                self.view_mode = 'standard'

                    live.update(self.render_ui())
                    await asyncio.sleep(0.1)
            
        if self.ws:
            self.ws.stop()

if __name__ == "__main__":
    try:
        import plotext
        import rich
    except ImportError as e:
        print("Error: Dependencies are not installed.")
        print(f"Missing module: {e.name}")
        sys.exit(1)

    app = CryptoTracker()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass