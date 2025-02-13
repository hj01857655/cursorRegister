import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

class CursorAuthUpdater:
    DB_PATH = "{APPDATA}/Cursor/User/globalStorage/state.vscdb"
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
        if not (appdata := os.getenv("APPDATA")):
            raise EnvironmentError("APPDATA 环境变量未设置")
        return Path(self.DB_PATH.format(APPDATA=appdata))

    def _update_env_file(self, cookies: str) -> None:
        env_path = Path(__file__).parent / '.env'
        env_content = env_path.read_text(encoding='utf-8')
        updated_content = [
            f"COOKIES_STR='{cookies}'" if line.startswith('COOKIES_STR=') else line
            for line in env_content.splitlines()
        ]
        env_path.write_text('\n'.join(updated_content), encoding='utf-8')
        os.environ['COOKIES_STR'] = cookies

    def _extract_token(self, cookies: str) -> str | None:
        token_key = "WorkosCursorSessionToken="
        try:
            token_start = cookies.index(token_key) + len(token_key)
            token_end = cookies.find(';', token_start)
            token = cookies[token_start:] if token_end == -1 else cookies[token_start:token_end]
            return token.split("::")[1]
        except (ValueError, IndexError):
            logger.error("无效的 WorkosCursorSessionToken")
            return None

    def update_db(self, updates: dict) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for key, value in updates.items():
                    cursor.execute(
                        "INSERT INTO itemTable (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
                        (key, value, value)
                    )
                    logger.info(f"已更新 {key.split('/')[-1]}")
                return True
        except Exception as e:
            logger.error(f"数据库更新失败: {e}")
            return False

    def process_cookies(self, cookies: str) -> tuple[bool, str]:
        try:
            self._update_env_file(cookies)
            
            if not (token := self._extract_token(cookies)):
                return False, "无效的 WorkosCursorSessionToken"
                
            updates = {
                self.AUTH_KEYS["sign_up"]: "Auth_0",
                self.AUTH_KEYS["email"]: os.getenv("EMAIL", ""),
                self.AUTH_KEYS["access"]: token,
                self.AUTH_KEYS["refresh"]: token
            }
            
            logger.info("正在更新认证信息...")
            if not self.update_db(updates):
                return False, "数据库更新失败"
            return True, "认证信息更新成功"
        except Exception as e:
            return False, f"更新认证信息失败: {str(e)}"

    def run(self) -> None:
        cookies = input("请输入Cookie字符串: ").strip()
        success, message = self.process_cookies(cookies)
        if success:
            logger.success(message)
        else:
            logger.error(message)

def main():
    try:
        updater = CursorAuthUpdater()
        updater.run()
    except Exception as e:
        logger.error(f"程序执行失败: {e}")

if __name__ == "__main__":
    main()
