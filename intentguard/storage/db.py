import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_DIR = Path.home() / ".intentguard"
DB_PATH = DB_DIR / "memory.db"

def init_db():
    """Initializes the SQLite database for storing user behavior history."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT NOT NULL,
            user TEXT NOT NULL,
            timestamp REAL NOT NULL,
            risk_score REAL NOT NULL,
            decision TEXT NOT NULL,
            user_confirmed BOOLEAN NOT NULL,
            intent TEXT,
            context TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_action(
    command: str, 
    user: str, 
    timestamp: float, 
    risk_score: float, 
    decision: str, 
    user_confirmed: bool, 
    intent: str = "", 
    context: Optional[Dict[str, Any]] = None
):
    """Logs an intercepted action and its decision into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    context_str = json.dumps(context) if context else "{}"
    cursor.execute('''
        INSERT INTO actions (command, user, timestamp, risk_score, decision, user_confirmed, intent, context)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (command, user, timestamp, risk_score, decision, user_confirmed, intent, context_str))
    conn.commit()
    conn.close()

def get_recent_actions(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves the most recent actions logged in the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM actions ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
