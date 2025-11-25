from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.layout import Layout
from rich.console import Group

class HelpModal:
    def __init__(self):
        pass

    def render(self) -> Panel:
        table = Table(title="Keyboard Shortcuts", border_style="blue", expand=True)
        table.add_column("Key", style="bold cyan", justify="center")
        table.add_column("Action", style="white")
        table.add_column("Category", style="yellow")

        # Navigation
        table.add_row("S", "Search for Coin", "Nav")
        table.add_row("1-9", "Select from Watchlist", "Nav")
        table.add_row("Q", "Quit Application", "Nav")

        # Timeframe
        table.add_row("H, 4, D", "1h, 4h, 1d Timeframes", "Data")
        table.add_row("W, M, Y", "1w, 1m, 1y Timeframes", "Data")
        table.add_row("m", "Minute Timeframes (1,5,15,30)", "Data")

        # Sizing (The requested 'Size' section)
        table.add_row("< / >", "Resize Watchlist (Sidebar)", "Size")
        table.add_row("[ / ]", "Resize Liquidation Panel", "Size")

        # Tools
        table.add_row("I", "Indicators Menu", "Tools")
        table.add_row("O", "Toggle Liq/OB Levels", "Tools")
        table.add_row("C", "Cycle Chart Mode (Ascii/Candle/Line)", "Tools")
        table.add_row("X", "Toggle Chart Visibility", "Tools")
        table.add_row("P", "Big Price Ticker Mode", "Tools")
        
        # Watchlist
        table.add_row("F", "Favorite Current Coin", "List")
        table.add_row("V", "View Favorites", "List")
        table.add_row("T", "View Trending", "List")
        table.add_row("G/L", "View Gainers/Losers", "List")

        content = Group(
            Align.center("[bold]UNIVERSAL CRYPTO TRACKER HELP[/bold]"),
            Text(" "),
            table,
            Text(" "),
            Align.center("[dim]Press any key to return...[/dim]")
        )

        return Panel(
            content,
            title="[bold red]Help & Controls[/bold red]",
            border_style="red",
            expand=False,
            padding=(1, 2)
        )
