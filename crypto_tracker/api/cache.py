import sqlite3
import json
from typing import List, Dict, Optional
from crypto_tracker.utils import config
import os

class CacheManager:
    def __init__(self):
        self.db_path = config.DB_PATH
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS coins (
                    id TEXT PRIMARY KEY,
                    symbol TEXT,
                    name TEXT,
                    rank INTEGER,
                    source TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id TEXT PRIMARY KEY
                )
            ''')
            conn.commit()

    def save_coins(self, coins: List[Dict]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # coins format: [{'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin', 'rank': 1, 'source': 'coingecko'}]
            cursor.executemany('''
                INSERT OR REPLACE INTO coins (id, symbol, name, rank, source)
                VALUES (:id, :symbol, :name, :rank, :source)
            ''', coins)
            conn.commit()

    def get_all_coins(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM coins ORDER BY rank ASC')
            return [dict(row) for row in cursor.fetchall()]
    
    def search_coins(self, query: str) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            wildcard = f"%{query}%"
            cursor.execute('''
                SELECT * FROM coins 
                WHERE id LIKE ? OR symbol LIKE ? OR name LIKE ? 
                ORDER BY rank ASC LIMIT 50
            ''', (wildcard, wildcard, wildcard))
            return [dict(row) for row in cursor.fetchall()]

    def add_favorite(self, coin_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO favorites (id) VALUES (?)', (coin_id,))
            conn.commit()

    def remove_favorite(self, coin_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM favorites WHERE id = ?', (coin_id,))
            conn.commit()

    def get_favorites(self) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM favorites')
            return [row[0] for row in cursor.fetchall()]

    def is_cache_empty(self) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM coins')
            return cursor.fetchone()[0] == 0
