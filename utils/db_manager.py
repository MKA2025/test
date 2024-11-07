import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path: str = 'data/bot.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    settings TEXT,
                    is_premium BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Downloads table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    file_url TEXT,
                    file_path TEXT,
                    file_size INTEGER,
                    format TEXT,
                    quality TEXT,
                    status TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY,
                    preferred_quality TEXT,
                    preferred_format TEXT,
                    auto_download BOOLEAN DEFAULT TRUE,
                    notifications BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            conn.commit()

    def add_user(self, user_id: int, username: str, first_name: str = None, last_name: str = None):
        """Add or update user in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, last_active) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, datetime.now()))
            
            # Initialize user settings if new user
            cursor.execute('''
                INSERT OR IGNORE INTO settings 
                (user_id, preferred_quality, preferred_format) 
                VALUES (?, ?, ?)
            ''', (user_id, 'HIGH', 'MP3'))
            
            conn.commit()

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            result = cursor.execute(
                'SELECT * FROM users WHERE user_id = ?',
                (user_id,)
            ).fetchone()
            
            if result:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'first_name': result[2],
                    'last_name': result[3],
                    'settings': json.loads(result[4]) if result[4] else {},
                    'is_premium': bool(result[5]),
                    'created_at': result[6],
                    'last_active': result[7]
                }
            return None

    def update_user_settings(self, user_id: int, settings: Dict[str, Any]):
        """Update user settings"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE settings SET preferred_quality=?, preferred_format=?, auto_download=?, notifications=? WHERE user_id=?',
                (
                    settings.get('preferred_quality'),
                    settings.get('preferred_format'),
                    settings.get('auto_download', True),
                    settings.get('notifications', True),
                    user_id
                )
            )
            conn.commit()

    def add_download(self, user_id: int, file_url: str, file_path: str, 
                    file_size: int, format: str, quality: str):
        """Record new download"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO downloads 
                (user_id, file_url, file_path, file_size, format, quality, status) 
                VALUES (?, ?, ?, ?,
                
    def add_download(self, user_id: int, file_url: str, file_path: str, 
                    file_size: int, format: str, quality: str):
        """Record new download"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO downloads 
                (user_id, file_url, file_path, file_size, format, quality, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, file_url, file_path, file_size, format, quality, 'pending'))
            conn.commit()
            return cursor.lastrowid

    def update_download_status(self, download_id: int, status: str, error_message: str = None):
        """Update download status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if status == 'completed':
                cursor.execute('''
                    UPDATE downloads 
                    SET status = ?, completed_at = ? 
                    WHERE id = ?
                ''', (status, datetime.now(), download_id))
            else:
                cursor.execute('''
                    UPDATE downloads 
                    SET status = ?, error_message = ? 
                    WHERE id = ?
                ''', (status, error_message, download_id))
            conn.commit()

    def get_download_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's download history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            results = cursor.execute('''
                SELECT * FROM downloads 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit)).fetchall()
            
            return [{
                'id': row[0],
                'file_url': row[2],
                'file_path': row[3],
                'file_size': row[4],
                'format': row[5],
                'quality': row[6],
                'status': row[7],
                'error_message': row[8],
                'created_at': row[9],
                'completed_at': row[10]
            } for row in results]

    def get_active_downloads(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's active downloads"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            results = cursor.execute('''
                SELECT * FROM downloads 
                WHERE user_id = ? AND status IN ('pending', 'downloading')
                ORDER BY created_at DESC
            ''', (user_id,)).fetchall()
            
            return [{
                'id': row[0],
                'file_url': row[2],
                'file_path': row[3],
                'status': row[7],
                'created_at': row[9]
            } for row in results]

    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            result = cursor.execute('''
                SELECT preferred_quality, preferred_format, auto_download, notifications 
                FROM settings 
                WHERE user_id = ?
            ''', (user_id,)).fetchone()
            
            if result:
                return {
                    'preferred_quality': result[0],
                    'preferred_format': result[1],
                    'auto_download': bool(result[2]),
                    'notifications': bool(result[3])
                }
            return None

    def update_last_active(self, user_id: int):
        """Update user's last active timestamp"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET last_active = ? 
                WHERE user_id = ?
            ''', (datetime.now(), user_id))
            conn.commit()

    def get_download_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's download statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total downloads
            total = cursor.execute('''
                SELECT COUNT(*) FROM downloads 
                WHERE user_id = ?
            ''', (user_id,)).fetchone()[0]
            
            # Downloads by status
            status_counts = cursor.execute('''
                SELECT status, COUNT(*) FROM downloads 
                WHERE user_id = ? 
                GROUP BY status
            ''', (user_id,)).fetchall()
            
            # Total downloaded size
            total_size = cursor.execute('''
                SELECT SUM(file_size) FROM downloads 
                WHERE user_id = ? AND status = 'completed'
            ''', (user_id,)).fetchone()[0] or 0
            
            return {
                'total_downloads': total,
                'status_counts': dict(status_counts),
                'total_size': total_size
            }

    def clear_old_downloads(self, days: int = 30):
        """Clear download records older than specified days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM downloads 
                WHERE created_at < datetime('now', ?)
            ''', (f'-{days} days',))
            conn.commit()

    def optimize_database(self):
        """Optimize database by cleaning up and vacuuming"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('VACUUM')
            conn.commit()
