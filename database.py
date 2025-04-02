import sqlite3
from pathlib import Path
from loguru import logger
from typing import Dict, List, Optional, Union
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str = "cursor.db"):
        self.db_path = Path(db_path)
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def execute(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """执行SQL查询并返回结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith("SELECT"):
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                conn.commit()
                return None
    
    def insert_account(self, account_data: Dict[str, str]) -> bool:
        """插入账号数据"""
        try:
            query = """
            INSERT INTO accounts (domain, email, password, cookie_str, quota, days)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                account_data.get('domain'),
                account_data.get('email'),
                account_data.get('password'),
                account_data.get('cookie_str'),
                account_data.get('quota'),
                account_data.get('days')
            )
            self.execute(query, params)
            logger.success(f"账号添加成功: {account_data.get('email')}")
            return True
        except Exception as e:
            logger.error(f"添加账号失败: {str(e)}")
            return False
    
    def delete_account(self, email: str) -> bool:
        """根据邮箱删除账号"""
        try:
            self.execute("DELETE FROM accounts WHERE email = ?", (email,))
            logger.success(f"账号删除成功: {email}")
            return True
        except Exception as e:
            logger.error(f"删除账号失败: {str(e)}")
            return False
    
    def get_account(self, email: str) -> Optional[Dict]:
        """根据邮箱获取账号信息"""
        try:
            result = self.execute("SELECT * FROM accounts WHERE email = ?", (email,))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"查询账号失败: {str(e)}")
            return None
    
    def update_account(self, email: str, updates: Dict[str, str]) -> bool:
        """更新账号信息"""
        try:
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            query = f"UPDATE accounts SET {set_clause} WHERE email = ?"
            params = tuple(list(updates.values()) + [email])
            self.execute(query, params)
            logger.success(f"账号更新成功: {email}")
            return True
        except Exception as e:
            logger.error(f"更新账号失败: {str(e)}")
            return False

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