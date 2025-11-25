import threading
import websocket
import json
import time
from typing import Callable, Dict

class WebSocketHandler:
    def __init__(self, url: str, on_message: Callable[[Dict], None]):
        self.url = url
        self.on_message_callback = on_message
        self.ws = None
        self.thread = None
        self.running = False

    def start(self):
        self.running = True
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()

    def _on_message(self, ws, message):
        if self.on_message_callback:
            data = json.loads(message)
            self.on_message_callback(data)

    def _on_error(self, ws, error):
        # In production, log this
        pass

    def _on_close(self, ws, close_status_code, close_msg):
        if self.running:
            # Auto-reconnect
            time.sleep(1)
            self.start()

class BinanceWebSocket(WebSocketHandler):
    def __init__(self, on_ticker_update: Callable[[Dict], None]):
        # Stream all tickers
        url = "wss://stream.binance.com:9443/ws/!ticker@arr"
        super().__init__(url, on_ticker_update)

    def subscribe_kline(self, symbol: str, interval: str):
        # If we needed specific subscriptions, we would send JSON payloads here.
        # But for !ticker@arr it's a global stream.
        pass
