import os
from dotenv import load_dotenv
from loguru import logger
from cursor_utils import (
    PathManager, EnvManager, DatabaseManager, 
    StringGenerator, error_handler, Result
)

class CursorAuthUpdater:
    AUTH_KEYS = {
        "sign_up": "cursorAuth/cachedSignUpType",
        "email": "cursorAuth/cachedEmail",
        "access": "cursorAuth/accessToken",
        "refresh": "cursorAuth/refreshToken"
    }

    def __init__(self):
        self.db_path = PathManager.get_cursor_path() / 'state.vscdb'
        load_dotenv()

    @error_handler
    def process_cookies(self, cookies: str) -> Result:
        env_result = EnvManager.update_env_vars({'COOKIES_STR': cookies})
        if not env_result:
            return env_result
        
        if not (token := StringGenerator.extract_token(cookies, "WorkosCursorSessionToken=")):
            return Result.fail("无效的 WorkosCursorSessionToken")
            
        updates = {
            self.AUTH_KEYS["sign_up"]: "Auth_0",
            self.AUTH_KEYS["email"]: os.getenv("EMAIL", ""),
            self.AUTH_KEYS["access"]: token,
            self.AUTH_KEYS["refresh"]: token
        }
        
        logger.info("正在更新认证信息...")
        db_result = DatabaseManager.update_sqlite_db(self.db_path, updates)
        if not db_result:
            return db_result
            
        return Result.ok(message="认证信息更新成功")

def main():
    try:
        updater = CursorAuthUpdater()
        cookies = input("请输入Cookie字符串: ").strip()
        result = updater.process_cookies(cookies)
        if result:
            logger.success(result.message)
        else:
            logger.error(result.message)
    except Exception as e:
        logger.error(f"程序执行失败: {e}")

if __name__ == "__main__":
    main() 