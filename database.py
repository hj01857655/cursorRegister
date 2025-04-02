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
            cookie_str VARCHAR(1000),  -- 存储完整的 JWT token
            quota TEXT,
            days TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建账号生成记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            status TEXT NOT NULL,  -- 生成状态：success/failed
            error_message TEXT,    -- 如果失败，记录错误信息
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建配置信息表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            api_key TEXT,
            moe_mail_url TEXT,
            cookie_str VARCHAR(1000),  -- 存储完整的 JWT token
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_email ON accounts(email)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_generation_email ON account_generations(email)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_config_domain ON configurations(domain)
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