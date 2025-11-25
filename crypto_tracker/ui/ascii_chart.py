import math
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
import pandas as pd
import numpy as np

class AsciiCandleChart:
    """
    A custom chart renderer that uses standard ASCII/Unicode block characters
    instead of Braille patterns. Designed for "retro" or "terminal" aesthetics.
    """
    def __init__(self):
        pass

    def render(self, df: pd.DataFrame, title: str, active_indicators: set, show_liq_ob: bool = False) -> Group:
        if df.empty:
            return Group(Text("No data available"))

        # Configuration
        HEIGHT = 24
        WIDTH = 100 
        MAX_WIDTH = WIDTH - 1

        # 1. Scaling / Sampling Logic
        total_data_points = len(df)
        
        if total_data_points > WIDTH:
            # Downsample: Pick 'WIDTH' indices evenly distributed
            indices = np.linspace(0, total_data_points - 1, WIDTH).astype(int)
            plot_df = df.iloc[indices].copy()
        else:
            plot_df = df.copy()

        # Reset index to ensure we can iterate cleanly
        plot_df.reset_index(drop=True, inplace=True)
        final_count = len(plot_df)

        # 2. Determine Y-Axis Range
        valid_lows = plot_df['low'][plot_df['low'] > 0]
        valid_highs = plot_df['high'][plot_df['high'] > 0]
        
        min_price = valid_lows.min() if not valid_lows.empty else 0
        max_price = valid_highs.max() if not valid_highs.empty else 100
        
        # Active Liq/OB levels (Latest values)
        active_levels = []
        latest_liq_short = None
        latest_liq_long = None
        latest_bull_ob = None
        latest_bear_ob = None

        if show_liq_ob:
             if 'liq_short' in plot_df.columns:
                 valid = plot_df['liq_short'][plot_df['liq_short'] > 0]
                 if not valid.empty:
                     latest_liq_short = valid.iloc[-1]
                     max_price = max(max_price, latest_liq_short)
                     active_levels.append(f"[red]Liq Short: ${latest_liq_short:,.2f}[/red]")
                     
             if 'liq_long' in plot_df.columns:
                 valid = plot_df['liq_long'][plot_df['liq_long'] > 0]
                 if not valid.empty:
                     latest_liq_long = valid.iloc[-1]
                     min_price = min(min_price, latest_liq_long)
                     active_levels.append(f"[green]Liq Long: ${latest_liq_long:,.2f}[/green]")
            
             if 'bullish_ob' in plot_df.columns:
                 valid = plot_df['bullish_ob'].dropna()
                 if not valid.empty:
                     latest_bull_ob = valid.iloc[-1]
                     active_levels.append(f"[green]Bull OB: ${latest_bull_ob:,.2f}[/green]")
             
             if 'bearish_ob' in plot_df.columns:
                 valid = plot_df['bearish_ob'].dropna()
                 if not valid.empty:
                     latest_bear_ob = valid.iloc[-1]
                     active_levels.append(f"[red]Bear OB: ${latest_bear_ob:,.2f}[/red]")

        # Add padding to range
        padding = (max_price - min_price) * 0.05
        min_price = max(0, min_price - padding)
        max_price = max_price + padding
        
        price_range = max_price - min_price
        if price_range <= 0: price_range = 1

        def price_to_row(price):
            if pd.isna(price) or price <= 0: return -1
            ratio = (price - min_price) / price_range
            row = int(ratio * (HEIGHT - 1))
            return max(0, min(HEIGHT - 1, row))

        # Create Canvas
        canvas = [[" " for _ in range(WIDTH)] for _ in range(HEIGHT)]
        colors = [["default" for _ in range(WIDTH)] for _ in range(HEIGHT)]

        # LAYER 1: Draw Special Levels
        if show_liq_ob:
            if latest_liq_short is not None:
                r = price_to_row(latest_liq_short)
                if 0 <= r < HEIGHT:
                    for c in range(WIDTH):
                        canvas[r][c] = "─"
                        colors[r][c] = "red"

            if latest_liq_long is not None:
                r = price_to_row(latest_liq_long)
                if 0 <= r < HEIGHT:
                    for c in range(WIDTH):
                        canvas[r][c] = "─"
                        colors[r][c] = "green"
            
            if latest_bull_ob is not None:
                r = price_to_row(latest_bull_ob)
                if 0 <= r < HEIGHT:
                    for c in range(WIDTH):
                        canvas[r][c] = "="
                        colors[r][c] = "green"

            if latest_bear_ob is not None:
                r = price_to_row(latest_bear_ob)
                if 0 <= r < HEIGHT:
                    for c in range(WIDTH):
                        canvas[r][c] = "="
                        colors[r][c] = "red"

        # Pre-calculate Screen X coordinates for all points
        screen_xs = []
        for i in range(final_count):
            if final_count > 1:
                # Using (final_count - 1) ensures the last point hits MAX_WIDTH
                # This distributes candles evenly across the full width
                scr_x = int((i / (final_count - 1)) * MAX_WIDTH)
            else:
                scr_x = MAX_WIDTH // 2
            screen_xs.append(scr_x)

        # LAYER 2: Draw Indicators
        ind_chars = {
            'SMA_50': ('*', 'cyan'),
            'SMA_200': ('#', 'magenta'),
            'EMA_9': ('-', 'yellow'),
            'BBU_20_2.0': ('^', 'blue'),
            'BBL_20_2.0': ('v', 'blue'),
        }
        
        for col_name, (char, color) in ind_chars.items():
            should_draw = False
            if 'SMA' in col_name and 'sma' in active_indicators: should_draw = True
            if 'EMA' in col_name and 'ema' in active_indicators: should_draw = True
            if 'BB' in col_name and 'bb' in active_indicators: should_draw = True
            
            if should_draw and col_name in plot_df.columns:
                for i, val in plot_df[col_name].items():
                    if i >= len(screen_xs): continue
                    r = price_to_row(val)
                    col = screen_xs[i]
                    if 0 <= r < HEIGHT and 0 <= col < WIDTH:
                        canvas[r][col] = char
                        colors[r][col] = color

        # LAYER 3: Draw Candles
        for i, row in plot_df.iterrows():
            if i >= len(screen_xs): continue
            
            o = row['open']
            c = row['close']
            h = row['high']
            l = row['low']
            
            row_o = price_to_row(o)
            row_c = price_to_row(c)
            row_h = price_to_row(h)
            row_l = price_to_row(l)
            
            if row_o == -1 or row_c == -1: continue
            
            col = screen_xs[i]
            if not (0 <= col < WIDTH): continue

            is_green = c >= o
            color = "green" if is_green else "red"

            # Draw Wick
            for r in range(row_l, row_h + 1):
                canvas[r][col] = "│"
                colors[r][col] = color
                
            # Draw Body
            start, end = sorted([row_o, row_c])
            for r in range(start, end + 1):
                canvas[r][col] = "█" 
                colors[r][col] = color

        # Build Final Output
        output_lines = []
        
        # Header with Big Price
        last_price = plot_df['close'].iloc[-1] if not plot_df.empty else 0
        header_text = Text(f"{title}", style="bold white")
        header_text.append(f"  ${last_price:,.2f}", style="bold green" if last_price >= plot_df['open'].iloc[-1] else "bold red")
        output_lines.append(header_text)
        
        output_lines.append(Text("┌" + "─" * WIDTH + "┐"))
        
        for r in range(HEIGHT - 1, -1, -1):
            row_text = Text("│")
            for c in range(WIDTH):
                row_text.append(canvas[r][c], style=colors[r][c])
            row_text.append("│")
            
            if r % 2 == 0:
                price_label = min_price + (r / (HEIGHT-1) * price_range)
                row_text.append(f" {price_label:,.2f}", style="white")
                
            output_lines.append(row_text)
            
        output_lines.append(Text("└" + "─" * WIDTH + "┘"))
        
        # The levels panel is now handled separately
        return Group(*output_lines)

    def render_levels_panel(self, df: pd.DataFrame, show_liq_ob: bool):
        """Returns a dedicated Panel for Model Key Levels or None if inactive."""
        if not show_liq_ob or df.empty:
            return None

        # We need to find the latest valid values from the FULL dataframe (or the plotted one)
        # Since we just need the scalar values, checking the last non-null is sufficient.
        latest_liq_short = None
        latest_liq_long = None
        latest_bull_ob = None
        latest_bear_ob = None

        if 'liq_short' in df.columns:
             valid = df['liq_short'][df['liq_short'] > 0]
             if not valid.empty: latest_liq_short = valid.iloc[-1]
             
        if 'liq_long' in df.columns:
             valid = df['liq_long'][df['liq_long'] > 0]
             if not valid.empty: latest_liq_long = valid.iloc[-1]

        if 'bullish_ob' in df.columns:
             valid = df['bullish_ob'].dropna()
             if not valid.empty: latest_bull_ob = valid.iloc[-1]
        
        if 'bearish_ob' in df.columns:
             valid = df['bearish_ob'].dropna()
             if not valid.empty: latest_bear_ob = valid.iloc[-1]

        if not (latest_liq_short or latest_liq_long or latest_bull_ob or latest_bear_ob):
            return None

        # Create a distinct "Bar" for the Model Levels
        stats_text = Text()
        
        # Resistance Side (Red)
        if latest_liq_short:
            stats_text.append(f" Liq Short: ${latest_liq_short:,.2f} ", style="bold white on red")
            stats_text.append("  ")
        if latest_bear_ob:
            stats_text.append(f" Bear OB: ${latest_bear_ob:,.2f} ", style="white on red")
            stats_text.append("  ")
            
        stats_text.append(" | ", style="bold yellow")
        stats_text.append("  ")

        # Support Side (Green)
        if latest_bull_ob:
            stats_text.append(f" Bull OB: ${latest_bull_ob:,.2f} ", style="white on green")
            stats_text.append("  ")
        if latest_liq_long:
            stats_text.append(f" Liq Long: ${latest_liq_long:,.2f} ", style="bold white on green")

        return Panel(
            Align.center(stats_text), 
            title="[bold yellow]Model Key Levels[/bold yellow]",
            border_style="cyan",
            expand=True
        )
