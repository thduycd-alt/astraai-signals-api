import sqlite3
import os
from datetime import datetime

DB_PATH = "comments.db"

class CommentService:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                user_name TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def get_comments(self, symbol: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_name, content, timestamp FROM comments WHERE symbol=? ORDER BY id DESC", (symbol.upper(),))
        rows = cursor.fetchall()
        conn.close()
        
        return [{"user_name": r[0], "content": r[1], "timestamp": r[2]} for r in rows]

    def add_comment(self, symbol: str, user_name: str, content: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO comments (symbol, user_name, content, timestamp) VALUES (?, ?, ?, ?)",
                       (symbol.upper(), user_name, content, timestamp))
        conn.commit()
        conn.close()
        return {"status": "success"}

comment_service = CommentService()
