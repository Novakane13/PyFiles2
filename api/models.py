import sqlite3
import os

def get_db_connection():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models/pos_system.db'))
    conn = sqlite3.connect(db_path, timeout=30.0)  # Adding a timeout to handle locking issues
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")  # Enable Write-Ahead Logging for better concurrency
    return conn