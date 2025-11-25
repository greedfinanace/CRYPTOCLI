# Universal Crypto Tracker v3.0 🚀

A powerful, production-grade terminal dashboard for cryptocurrency tracking. Featuring real-time data, beautiful ASCII visualizations, and a modern web dashboard companion.

## 🔥 New Features (v3.0)
*   **Big Price Ticker:** A massive, beautiful ASCII price display mode for focus.
*   **Liquidation Levels:** Track key resistance (Liquidation Short) and support (Liquidation Long) levels directly on the chart.
*   **Web Dashboard:** A full modern React + Tailwind web interface running locally.
*   **Minute Timeframes:** Support for 1m, 5m, 15m, 30m analysis.
*   **Dynamic Layout:** Resize every panel (Sidebar, Chart, Liquidation Window) in real-time.

## 🛠 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/crypto-tracker.git
   cd crypto-tracker
   ```

2. **Install dependencies:**
   *   **Windows:** Double-click `install.bat`
   *   **Manual:** `pip install -r requirements.txt`

## 🚀 Usage

### 1. Terminal Dashboard
Run the main TUI application:
*   **Windows:** Double-click `run.bat`
*   **Command:** `python main.py`

### 2. Web Dashboard (New!)
Launch the modern web interface:
*   **Windows:** Double-click `run_dashboard.bat`
*   **Access:** Open `http://localhost:8000` in your browser.

### 3. Professional Charts
Generate high-resolution PNG charts for sharing:
```bash
python generate_chart.py
```

## ⌨️ Controls (Terminal)

| Key | Action | 
| :--- | :--- | 
| **Navigation** | | 
| `S` | **Search** for any coin (Binance/CoinGecko) | 
| `1`-`9` | Select coin from Sidebar | 
| `?` or `'` | Open **Help Menu** | 
| **Timeframes** | | 
| `M` | Minute Menu (1m, 5m, 15m, 30m) | 
| `H`, `4`, `D` | 1 Hour, 4 Hour, 1 Day | 
| `W`, `M`, `Y` | 1 Week, 1 Month, 1 Year | 
| **Tools & View** | | 
| `P` / `X` | **Big Ticker Mode** (Toggle Chart Visibility) | 
| `O` | Toggle **Liquidation & Order Block Levels** | 
| `I` | Indicators Menu (RSI, BB, EMA, SMA) | 
| `C` | Cycle Chart Type (ASCII / Candle / Line) | 
| **Layout & Sizing** | | 
| `<` / `>` | Resize **Sidebar** (Watchlist) | 
| `[` / `]` | Resize **Liquidation Window** | 
| **Watchlist** | | 
| `F` | Add/Remove **Favorite** | 
| `T` | View **Trending** | 
| `G` / `L` | View **Gainers** / **Losers** | 
| `Q` | **Quit** | 

## 🏗 Architecture

The project is built with a modular architecture separating API logic, UI rendering, and data processing.

```
c:\web\
├── main.py                   # Main TUI Application Entry
├── server.py                 # FastAPI Backend for Web Dashboard
├── generate_chart.py         # High-Res Chart Generator
├── crypto_tracker/
│   ├── api/                  # Binance & CoinGecko integrations
│   ├── ui/                   # Rich & ASCII rendering engines
│   │   ├── ascii_chart.py    # Custom ASCII Candle Renderer
│   │   ├── big_price.py      # Big Ticker Renderer
│   │   └── ...
│   └── utils/                # Technical Indicators & WebSocket
└── web_dashboard/            # React + Vite + Tailwind Frontend
```

## 📦 Requirements
*   Python 3.10+
*   Node.js (Optional, for building Web Dashboard)

## 📄 License
MIT