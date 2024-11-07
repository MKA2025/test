import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: str = 'bot.db'):
        self.db_path
