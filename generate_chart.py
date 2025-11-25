import pandas as pd
import mplfinance as mpf
from crypto_tracker.api.binance import BinanceAPI
import asyncio
import os

async def generate_chart():
    # 1. Fetch Data
    print("Fetching data for BTCUSDT...")
    async with BinanceAPI() as api:
        # Fetch data
        raw_data = await api.get_klines('BTCUSDT', '1h', limit=300)
    
    if not raw_data:
        print("Error: No data returned from Binance API")
        return

    # 2. Process Data
    df = pd.DataFrame(raw_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 
        'close_time', 'quote_asset_volume', 'trades', 
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
        
    df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('Date', inplace=True)
    
    # 3. Calculate Indicators
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA50'] = df['close'].rolling(window=50).mean()
    df['MA200'] = df['close'].rolling(window=200).mean()
    
    df['BB_mid'] = df['MA20']
    df['BB_std'] = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_mid'] + (2 * df['BB_std'])
    df['BB_lower'] = df['BB_mid'] - (2 * df['BB_std'])

    # Slice for display (Last 60 candles for better visibility of shapes)
    plot_df = df.iloc[-60:]
    current_price = plot_df['close'].iloc[-1]

    # 4. Configure Style (Dark Theme)
    mc = mpf.make_marketcolors(
        up='#26a69a', down='#ef5350',
        edge='inherit', wick='inherit',
        volume='inherit', ohlc='i'
    )
    
    s = mpf.make_mpf_style(
        base_mpf_style='nightclouds',
        marketcolors=mc,
        facecolor='#1e222d',
        edgecolor='#2c303b',
        gridcolor='#2c303b',
        gridstyle='--',
        y_on_right=True,
        rc={
            'axes.labelcolor': 'white',
            'xtick.labelcolor': 'white', 
            'ytick.labelcolor': 'white',
            'axes.edgecolor': '#2c303b'
        }
    )

    # 5. Create Plots
    apds = [
        mpf.make_addplot(plot_df['MA20'], color='cyan', width=0.8),
        mpf.make_addplot(plot_df['MA50'], color='orange', width=0.8),
        mpf.make_addplot(plot_df['MA200'], color='magenta', width=0.8),
        mpf.make_addplot(plot_df['BB_upper'], color='gray', width=0.5, alpha=0.3),
        mpf.make_addplot(plot_df['BB_lower'], color='gray', width=0.5, alpha=0.3),
    ]

    # 6. Generate Chart with Custom Layout
    filename = 'BTC_USDT_1H_Professional.png'
    print(f"Generating {filename}...")

    # Use returnfig=True to access axes for custom text
    fig, axlist = mpf.plot(
        plot_df,
        type='candle',
        style=s,
        volume=True,
        addplot=apds,
        hlines=dict(hlines=[current_price], colors=['white'], linestyle='dashed', linewidths=1, alpha=0.5),
        figsize=(16, 9),
        tight_layout=True,
        scale_width_adjustment=dict(volume=0.2),
        returnfig=True
    )

    # Add Custom Annotations
    ax_main = axlist[0] # Main chart axis
    
    # Top-Left: Asset Info
    ax_main.text(
        0.02, 0.96, 
        "BTC/USDT 1H", 
        transform=ax_main.transAxes, 
        color='white', 
        fontsize=16, 
        fontweight='bold',
        verticalalignment='top'
    )
    
    # Top-Right: Current Price (Large)
    price_str = f"${current_price:,.2f}"
    ax_main.text(
        0.98, 0.96, 
        price_str, 
        transform=ax_main.transAxes, 
        color='white', 
        fontsize=24, 
        fontweight='bold',
        horizontalalignment='right',
        verticalalignment='top'
    )

    # Save
    fig.savefig(filename, dpi=300, bbox_inches='tight', facecolor='#1e222d')
    print(f"Success! Chart saved to {os.path.abspath(filename)}")

if __name__ == "__main__":
    asyncio.run(generate_chart())
