from rich.table import Table
from typing import List, Dict

def create_watchlist_table(coins_data: List[Dict]) -> Table:
    table = Table(title="Watchlist", expand=True)
    table.add_column("Symbol", style="cyan")
    table.add_column("Price", style="white")
    table.add_column("24h%", style="green")
    table.add_column("Vol (24h)", style="yellow")
    
    for coin in coins_data:
        price = coin.get('current_price') or 0
        change = coin.get('price_change_percentage_24h') or 0
        volume = coin.get('total_volume') or 0
        
        color = "green" if change >= 0 else "red"
        
        table.add_row(
            coin.get('symbol', '').upper(),
            f"${price:,.2f}",
            f"[{color}]{change:+.2f}%[/{color}]",
            f"${volume/1e9:.2f}B" if volume > 1e9 else f"${volume/1e6:.2f}M"
        )
    return table
