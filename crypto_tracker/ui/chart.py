import plotext as plt
from rich.ansi import AnsiDecoder
from rich.console import Group
from rich.jupyter import JupyterMixin
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
import pandas as pd

class PlotextChart:
    def __init__(self):
        self.decoder = AnsiDecoder()

    def render(self, df: pd.DataFrame, title: str, chart_type: str = 'candle') -> Group:
        try:
            plt.clf()
            plt.plotsize(100, 20)
            plt.title(title)
            plt.theme('dark')
            
            # Disable legend to avoid IndexError in plotext _build.py
            # This is a known stability issue with plotext overlays in some versions
            # plt.show_legend(False) 
            
            dates = plt.datetimes_to_string(df['time'].tolist())
            
            # Validate data length
            if len(dates) == 0:
                return Group(Text("No data available"))

            # Main price chart
            if chart_type == 'candle':
                # Plotext 5.3.2 expects a dictionary for candlestick data
                data = {
                    'Open': df['open'].tolist(),
                    'High': df['high'].tolist(),
                    'Low': df['low'].tolist(),
                    'Close': df['close'].tolist()
                }
                plt.candlestick(dates, data, label="Price")
            else:
                plt.plot(dates, df['close'].tolist(), label="Price")
                
            # Indicators Overlay (SMA, EMA, Bollinger Bands)
            # Check for NaN values which might crash plotext if passed directly
            if 'SMA_50' in df.columns:
                 valid_sma = df['SMA_50'].fillna(0).tolist()
                 plt.plot(dates, valid_sma, color='cyan', label="SMA50")
            if 'SMA_200' in df.columns:
                 valid_sma = df['SMA_200'].fillna(0).tolist()
                 plt.plot(dates, valid_sma, color='magenta', label="SMA200")
            
            if 'BBU_20_2.0' in df.columns: 
                 valid_bb = df['BBU_20_2.0'].fillna(0).tolist()
                 plt.plot(dates, valid_bb, color='yellow', label="BB_Upper")
            if 'BBL_20_2.0' in df.columns:
                 valid_bb = df['BBL_20_2.0'].fillna(0).tolist()
                 plt.plot(dates, valid_bb, color='yellow', label="BB_Lower")

            return Group(Text.from_ansi(plt.build()))
        except Exception as e:
            return Group(Text(f"Chart Error: {str(e)}"))

def make_layout() -> Layout:
    layout = Layout(name="root")
    
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=7)
    )
    
    layout["main"].split_row(
        Layout(name="chart_area", ratio=3),
        Layout(name="sidebar", ratio=1)
    )
    
    layout["chart_area"].split(
        Layout(name="info_bar", size=3),
        Layout(name="chart", ratio=1),
        Layout(name="levels", size=0) # Model Key Levels (Dynamic Height)
    )

    return layout
