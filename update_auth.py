import os
import sqlite3
import sys
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

class CursorAuthUpdater:
    """Cursor认证信息管理器"""
    
    DB_PATHS = {
        "win32": "{APPDATA}/Cursor/User/globalStorage/state.vscdb",
        "darwin": "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb",
        "linux": "~/.config/Cursor/User/globalStorage/state.vscdb"
    }

    AUTH_KEYS = {
        "sign_up": "cursorAuth/cachedSignUpType",
        "email": "cursorAuth/cachedEmail",
        "access": "cursorAuth/accessToken",
        "refresh": "cursorAuth/refreshToken"
    }

    def __init__(self):
        self.db_path = self._get_db_path()
        load_dotenv()

    def _get_db_path(self) -> Path:
        """获取数据库路径"""
        if sys.platform not in self.DB_PATHS:
            raise NotImplementedError(f"不支持的操作系统: {sys.platform}")
            
        path_template = self.DB_PATHS[sys.platform]
        if sys.platform == "win32":
            if not (appdata := os.getenv("APPDATA")):
                raise EnvironmentError("APPDATA 环境变量未设置")
            path = path_template.format(APPDATA=appdata)
        else:
            path = path_template
            
        return Path(path).expanduser().resolve()

    def _update_env_file(self, cookies: str) -> None:
        """更新环境变量文件"""
        env_path = Path(__file__).parent / '.env'
        env_content = env_path.read_text(encoding='utf-8')
        updated_content = []
        
        for line in env_content.splitlines():
            if line.startswith('COOKIES_STR='):
                updated_content.append(f"COOKIES_STR='{cookies}'")
            else:
                updated_content.append(line)
                
        env_path.write_text('\n'.join(updated_content), encoding='utf-8')
        os.environ['COOKIES_STR'] = cookies

    def _extract_token(self, cookies: str) -> str | None:
        """从cookies中提取token"""
        token_key = "WorkosCursorSessionToken="
        if token_key not in cookies:
            logger.error("未找到 WorkosCursorSessionToken")
            return None
            
        token_start = cookies.index(token_key) + len(token_key)
        token_end = cookies.find(';', token_start)
        token_value = cookies[token_start:] if token_end == -1 else cookies[token_start:token_end]
        
        if len(token_parts := token_value.split("::")) < 2:
            logger.error("WorkosCursorSessionToken 格式不正确")
            return None
            
        return token_parts[1]

    def update_db(self, updates: dict) -> bool:
        """更新数据库中的认证信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for key, value in updates.items():
                    cursor.execute(
                        """INSERT INTO itemTable (key, value) 
                           VALUES (?, ?) 
                           ON CONFLICT(key) DO UPDATE SET value = ?""",
                        (key, value, value)
                    )
                    logger.info(f"已更新 {key.split('/')[-1]}")
                conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"数据库错误: {e}")
            return False
        except Exception as e:
            logger.error(f"更新失败: {e}")
            return False

    def update_with_cookie(self, cookies: str) -> None:
        """使用提供的cookie字符串更新认证信息"""
        self._update_env_file(cookies)
        
        if not (token := self._extract_token(cookies)):
            raise ValueError("无效的Cookie字符串")
            
        updates = {
            self.AUTH_KEYS["sign_up"]: "Auth_0",
            self.AUTH_KEYS["email"]: os.getenv("EMAIL", ""),
            self.AUTH_KEYS["access"]: token,
            self.AUTH_KEYS["refresh"]: token
        }
        
        logger.info("正在更新认证信息...")
        if not self.update_db(updates):
            raise RuntimeError("更新认证信息失败")

    def run(self) -> None:
        """运行更新流程"""
        cookies = input("请输入Cookie字符串: ").strip()
        self._update_env_file(cookies)
        
        if not (token := self._extract_token(cookies)):
            return
            
        updates = {
            self.AUTH_KEYS["sign_up"]: "Auth_0",
            self.AUTH_KEYS["email"]: os.getenv("EMAIL", ""),
            self.AUTH_KEYS["access"]: token,
            self.AUTH_KEYS["refresh"]: token
        }
        
        logger.info("正在更新认证信息...")
        if self.update_db(updates):
            logger.info("认证信息更新完成")
        else:
            logger.error("认证信息更新失败")

def main():
    try:

        updater = CursorAuthUpdater()
        updater.run()
    except Exception as e:
        logger.error(f"程序执行失败: {e}")

if __name__ == "__main__":
    main()
