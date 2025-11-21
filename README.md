# Universal Crypto Tracker v3.0

A production-ready, cross-platform command-line cryptocurrency tracker with massive full-screen charts, real-time data streaming, and support for over 17,000 coins.

![Terminal Screenshot](https://placeholder.com/screenshot)

## Features

- **Massive Coin Support**: Access 300+ Binance pairs and 17,000+ CoinGecko coins.
- **Real-Time Data**: Live price streaming via WebSocket for Binance pairs.
- **Interactive Charts**: Full-screen terminal charts with Zoom, Pan, and Candlesticks.
- **Technical Indicators**: RSI, MACD, Bollinger Bands, EMA, SMA.
- **Search**: Fuzzy search for any coin by symbol or name.
- **Watchlist & Favorites**: Keep track of your top coins.
- **Multi-Timeframe**: 1H, 4H, 1D, 1W, 1M, 1Y analysis.
- **Cross-Platform**: Works on Linux, macOS, and Windows.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/crypto-tracker.git
   cd crypto-tracker
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   *Note: Requires Python 3.10+*

## Usage

Run the application:

```bash
python crypto_tracker/main.py
```

### Controls

| Key | Action |
| --- | --- |
| `/` | **Search** for a coin |
| `1`-`9` | Quick select coin from **Watchlist** |
| `H`, `4`, `D`, `W`, `M`, `Y` | Change **Timeframe** (Hour, 4H, Day, Week, Month, Year) |
| `I` | Toggle **Indicators** (RSI, MACD, etc.) |
| `F` | Add/Remove from **Favorites** |
| `Q` | **Quit** application |

## Tech Stack

- **Language**: Python 3.10+
- **UI**: [Rich](https://github.com/Textualize/rich) (Panels, Tables, Live updates)
- **Charting**: [Plotext](https://github.com/piccolomo/plotext) (Terminal plotting)
- **Input**: Custom cross-platform handler (Unix `termios` / Windows `msvcrt`)
- **Data**: 
  - [Binance API](https://binance.com) (Real-time)
  - [CoinGecko API](https://coingecko.com) (Historical & Metadata)
- **Cache**: SQLite3

## Structure

```
crypto_tracker/
├── main.py                    # Entry point & main loop
├── api/
│   ├── binance.py            # Binance API wrapper
│   ├── coingecko.py          # CoinGecko API wrapper
│   └── cache.py              # SQLite caching layer
├── ui/
│   ├── chart.py              # Plotext chart rendering
│   ├── search.py             # Coin search modal
│   └── watchlist.py          # Multi-coin watchlist
├── utils/
│   ├── indicators.py         # Technical indicators
│   ├── websocket_handler.py  # WebSocket manager
│   └── input_handler.py      # Cross-platform input
└── data/                     # Local database storage
```

## License

MIT
