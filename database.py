import sqlite3
import hashlib
from typing import List, Dict, Any, Optional

DB_NAME = "kakeibo.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,          -- 購入日
            store TEXT NOT NULL,         -- 店舗名
            amount INTEGER NOT NULL,     -- 合計金額
            category TEXT NOT NULL,      -- カテゴリ
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()
    print("データベースが正常に初期化されました。")

def register_user(username: str, password: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_expense(user_id: int, date: str, store: str, amount: int, category: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (user_id, date, store, amount, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, date, store, amount, category))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"データ保存エラー: {e}")
        return False

def get_expenses_by_period(user_id: int, period_type: str, target_str: str) -> List[Dict[str, Any]]:
    """ログインユーザーのデータのみを取得"""
    conn = get_connection()
    cursor = conn.cursor()

    if period_type == "日":
        query = "SELECT * FROM expenses WHERE user_id = ? AND date = ? ORDER BY id DESC"
        cursor.execute(query, (user_id, target_str))
    elif period_type == "月":
        query = "SELECT * FROM expenses WHERE user_id = ? AND date LIKE ? ORDER BY date ASC, id DESC"
        cursor.execute(query, (user_id, f"{target_str}%"))
    elif period_type == "年":
        query = "SELECT * FROM expenses WHERE user_id = ? AND date LIKE ? ORDER BY date ASC, id DESC"
        cursor.execute(query, (user_id, f"{target_str}%"))
    else:
        query = "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC"
        cursor.execute(query, (user_id,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_expense(expense_id: int, user_id: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"データ削除エラー: {e}")
        return False

if __name__ == "__main__":
    init_db()