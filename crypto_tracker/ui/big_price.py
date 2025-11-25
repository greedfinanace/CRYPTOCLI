from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.console import Group

class BigPriceRenderer:
    def __init__(self):
        # STRICT 5-line height, 5-character width font (plus 1 px padding built-in if needed, but keeping raw 5x5 here)
        # Using full block █ for maximum visibility and "locking in" the alignment.
        self.font = {
            '0': [
                "█████",
                "█   █",
                "█   █",
                "█   █",
                "█████"
            ],
            '1': [
                "  █  ",
                " ██  ",
                "  █  ",
                "  █  ",
                "█████"
            ],
            '2': [
                "█████",
                "    █",
                "█████",
                "█    ",
                "█████"
            ],
            '3': [
                "█████",
                "    █",
                " ████",
                "    █",
                "█████"
            ],
            '4': [
                "█   █",
                "█   █",
                "█████",
                "    █",
                "    █"
            ],
            '5': [
                "█████",
                "█    ",
                "█████",
                "    █",
                "█████"
            ],
            '6': [
                "█████",
                "█    ",
                "█████",
                "█   █",
                "█████"
            ],
            '7': [
                "█████",
                "    █",
                "   █ ",
                "  █  ",
                " █   "
            ],
            '8': [
                "█████",
                "█   █",
                "█████",
                "█   █",
                "█████"
            ],
            '9': [
                "█████",
                "█   █",
                "█████",
                "    █",
                "█████"
            ],
            '.': [
                "     ",
                "     ",
                "     ",
                "     ",
                "  █  "
            ],
            ',': [
                "     ",
                "     ",
                "     ",
                "  █  ",
                " █   "
            ],
            '$': [
                "  █  ",
                " ███ ",
                "█ █ █",
                " ███ ",
                "  █  "
            ],
            '+': [
                "     ",
                "  █  ",
                "█████",
                "  █  ",
                "     "
            ],
            '-': [
                "     ",
                "     ",
                "█████",
                "     ",
                "     "
            ],
            '%': [
                "█   █",
                "   █ ",
                "  █  ",
                " █   ",
                "█   █"
            ]
        }

    def get_ascii_art(self, text: str, color: str, spacing: int = 1) -> Text:
        # Initialize 5 empty lines
        lines = ["", "", "", "", ""]
        space_str = " " * spacing
        
        for char in text:
            if char in self.font:
                char_lines = self.font[char]
                for i in range(5):
                    lines[i] += char_lines[i] + space_str
            else:
                # Fallback for unknown (5 wide space)
                for i in range(5):
                    lines[i] += "     " + space_str
        
        # Join with newlines
        final_art = "\n".join(lines)
        return Text(final_art, style=f"bold {color}")

    def render(self, symbol: str, price: float, change_percent: float = 0) -> Panel:
        # Colors
        trend_color = "green" if change_percent >= 0 else "red"
        price_color = "cyan" # Fixed Cyan as requested
        
        # Formatting
        # Adjust precision based on value to prevent string from being too long
        if price >= 1000:
             price_str = f"${price:,.2f}" 
        elif price >= 1:
             price_str = f"${price:,.4f}"
        else:
             price_str = f"${price:,.6f}"

        # Hard truncate if still too long to ensure it fits
        if len(price_str) > 14:
             price_str = f"${price:,.2f}"

        change_str = f"{change_percent:+.2f}%"
        
        # Dynamic Spacing Calculation
        # Screen width assumption: ~80-100 chars for chart area
        # Each char is 5 wide.
        # Len 10 * 5 = 50 chars.
        # Spacing 1 * 9 gaps = 9 chars. Total ~60. Fits easily.
        # Spacing 2 * 9 gaps = 18 chars. Total ~68. Fits.
        
        if len(price_str) > 10:
            spacing = 1 
        elif len(price_str) > 8:
            spacing = 2
        else:
            spacing = 3
        
        # Generate Art
        price_art = self.get_ascii_art(price_str, price_color, spacing)
        
        # Layout
        content = Group(
            Align.center(Text(f"\n{symbol.upper()}", style="bold white")),
            Text("\n"), 
            Align.center(price_art),
            Text("\n"),
            Align.center(Text(f" {change_str} ", style=f"bold white on {trend_color}")),
            Text("\n\n"),
            Align.center(Text("[P] Standard View", style="dim white"))
        )
        
        return Panel(
            content,
            title="[bold yellow]LIVE TICKER[/bold yellow]",
            border_style=trend_color,
            expand=True
        )