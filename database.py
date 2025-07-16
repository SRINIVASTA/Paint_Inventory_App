import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'inventory.db'

def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY,
            date TEXT, supplier TEXT, type TEXT,
            color TEXT, qty REAL, unit_cost REAL, total_cost REAL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY,
            date TEXT, customer TEXT, type TEXT,
            color TEXT, qty REAL, unit_price REAL, total_sale REAL
        )
    ''')

    # Insert default admin if none exists
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        from user_auth import hash_password
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ('admin', hash_password('admin123'), 'admin'))

    conn.commit()
    conn.close()
