import sqlite3
from pathlib import Path
from loguru import logger

def create_cursor_database():
    try:
        # 创建数据库连接（直接在当前目录创建）
        db_path = Path("cursor.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建账号表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            cookie TEXT,
            quota TEXT,
            days TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_email ON accounts(email)
        ''')
        
        # 提交更改并关闭连接
        conn.commit()
        conn.close()
        
        logger.success(f"数据库创建成功: {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"创建数据库失败: {str(e)}")
        return False

if __name__ == "__main__":
    create_cursor_database() 