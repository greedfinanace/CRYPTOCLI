from prompt_toolkit import PromptSession
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from prompt_toolkit.shortcuts import prompt
from typing import List, Dict, Optional

class SearchModal:
    def __init__(self, coin_list: List[Dict]):
        # coin_list is [{'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'}, ...]
        self.coin_map = {
            f"{c['symbol'].upper()} - {c['name']}": c 
            for c in coin_list
        }
        self.completer = FuzzyCompleter(WordCompleter(list(self.coin_map.keys())))
        self.session = PromptSession()

    async def show(self) -> Optional[Dict]:
        """
        Shows the search prompt.
        Returns the selected coin dict or None if cancelled.
        """
        try:
            # Pause Rich live update before calling this
            selected = await self.session.prompt_async("Search coin: ", completer=self.completer)
            return self.coin_map.get(selected)
        except (KeyboardInterrupt, EOFError):
            return None
