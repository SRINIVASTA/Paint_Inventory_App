import bcrypt
from database import get_connection

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def login_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if row and verify_password(password, row[2]):
        return row
    return None

def create_user(username, password, role):
    conn = get_connection()
    c = conn.cursor()
    try:
        hashed = hash_password(password)
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (username, hashed, role))
        conn.commit()
        return True
    except:
        return False
