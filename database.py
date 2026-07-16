import sqlite3
import os
from datetime import datetime

DB_PATH = "history.db"

def init_db():
    """Tạo bảng sessions nếu chưa tồn tại."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            video_source TEXT,
            total_entry INTEGER,
            total_exit INTEGER,
            excel_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_session(video_source: str, total_entry: int, total_exit: int, excel_path: str):
    """Thêm một bản ghi mới vào lịch sử."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO sessions (timestamp, video_source, total_entry, total_exit, excel_path)
        VALUES (?, ?, ?, ?, ?)
    ''', (now, video_source, total_entry, total_exit, excel_path))
    conn.commit()
    conn.close()

def get_all_sessions():
    """Lấy toàn bộ lịch sử (mới nhất lên đầu)."""
    if not os.path.exists(DB_PATH):
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, timestamp, video_source, total_entry, total_exit, excel_path FROM sessions ORDER BY id DESC")
        rows = cursor.fetchall()
        return rows
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()
