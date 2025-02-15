import os
from dotenv import load_dotenv
from loguru import logger
from utils import Utils, error_handler, Result

AUTH_KEYS = {k: f"cursorAuth/{v}" for k, v in {
    "sign_up": "cachedSignUpType",
    "email": "cachedEmail",
    "access": "accessToken",
    "refresh": "refreshToken"
}.items()}

@error_handler
def process_cookies(cookies: str) -> Result:
    if not (result := Utils.update_env_vars({'COOKIES_STR': cookies})):
        return result
    
    if not (token := Utils.extract_token(cookies, "WorkosCursorSessionToken=")):
        return Result.fail("无效的 WorkosCursorSessionToken")
        
    updates = {
        AUTH_KEYS["sign_up"]: "Auth_0",
        AUTH_KEYS["email"]: os.getenv("EMAIL", ""),
        AUTH_KEYS["access"]: token,
        AUTH_KEYS["refresh"]: token
    }
    
    logger.info("正在更新认证信息...")
    if not (result := Utils.update_sqlite_db(Utils.get_path('cursor') / 'state.vscdb', updates)):
        return result
        
    return Result.ok(message="认证信息更新成功")

if __name__ == "__main__":
    try:
        load_dotenv()
        if result := process_cookies(input("请输入Cookie字符串: ").strip()):
            logger.success(result.message)
        else:
            logger.error(result.message)
    except Exception as e:
        logger.error(f"程序执行失败: {e}") 