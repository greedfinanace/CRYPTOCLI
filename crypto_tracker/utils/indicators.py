import pandas as pd
import numpy as np

def calculate_indicators(df: pd.DataFrame):
    """
    Adds technical indicators to the dataframe using pure pandas.
    Expected columns: 'open', 'high', 'low', 'close', 'volume'
    """
    if df.empty:
        return df

    # Ensure numeric types
    close = pd.to_numeric(df['close'])
    
    # 1. Simple Moving Averages (SMA)
    df['SMA_50'] = close.rolling(window=50).mean()
    df['SMA_200'] = close.rolling(window=200).mean()
    
    # 2. Exponential Moving Average (EMA)
    df['EMA_9'] = close.ewm(span=9, adjust=False).mean()
    df['EMA_20'] = close.ewm(span=20, adjust=False).mean()
    
    # 3. Bollinger Bands (20, 2)
    sma_20 = close.rolling(window=20).mean()
    std_20 = close.rolling(window=20).std()
    df['BBU_20_2.0'] = sma_20 + (std_20 * 2)
    df['BBL_20_2.0'] = sma_20 - (std_20 * 2)
    
    # 4. MACD (12, 26, 9)
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    df['MACD_12_26_9'] = exp1 - exp2
    df['MACDs_12_26_9'] = df['MACD_12_26_9'].ewm(span=9, adjust=False).mean() # Signal line
    df['MACDh_12_26_9'] = df['MACD_12_26_9'] - df['MACDs_12_26_9'] # Histogram

    # 5. RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    
    # Wilder's Smoothing
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # 6. Advanced: Order Blocks and Liquidation
    df = calculate_order_blocks(df)
    df = calculate_liquidation_levels(df)
    
    return df

def calculate_order_blocks(df: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """
    Identifies potential Order Blocks.
    Bullish OB: Last bearish candle before a strong bullish move that breaks structure.
    Bearish OB: Last bullish candle before a strong bearish move.
    """
    df['bullish_ob'] = np.nan
    df['bearish_ob'] = np.nan
    
    # Simple algorithm for visualization purposes
    for i in range(lookback, len(df) - 2):
        # Bullish OB Detection
        # 1. Current candle is Green, Strong move
        if df['close'].iloc[i] > df['open'].iloc[i] and \
           (df['close'].iloc[i] - df['open'].iloc[i]) > (df['high'].iloc[i-1] - df['low'].iloc[i-1]):
            # 2. Previous candle was Red (The OB candidate)
            if df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                 # Mark the open of the bearish candle as the OB level
                 df.loc[df.index[i], 'bullish_ob'] = df['open'].iloc[i-1]

        # Bearish OB Detection
        # 1. Current candle is Red, Strong move
        if df['close'].iloc[i] < df['open'].iloc[i] and \
           (df['open'].iloc[i] - df['close'].iloc[i]) > (df['high'].iloc[i-1] - df['low'].iloc[i-1]):
            # 2. Previous candle was Green
            if df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                 # Mark the open of the bullish candle
                 df.loc[df.index[i], 'bearish_ob'] = df['open'].iloc[i-1]
                 
    # Forward fill the last detected OB for visualization continuity (optional, but good for charts)
    df['bullish_ob'] = df['bullish_ob'].ffill()
    df['bearish_ob'] = df['bearish_ob'].ffill()
    
    return df

def calculate_liquidation_levels(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Estimates Liquidation Levels based on Swing Highs/Lows.
    """
    df['liq_short'] = df['high'].rolling(window=window).max()
    df['liq_long'] = df['low'].rolling(window=window).min()
    return df
