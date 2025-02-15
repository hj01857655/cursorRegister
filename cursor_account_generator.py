from typing import Tuple
from dotenv import load_dotenv
from loguru import logger
from cursor_utils import error_handler, Utils
import random

@error_handler
def generate_cursor_account() -> Tuple[str, str]:
    random_length = random.randint(5, 20)
    email = f"{Utils.generate_random_string(random_length)}@{Utils.get_env_var('DOMAIN')}"
    password = Utils.generate_secure_password()
    
    logger.info("生成的Cursor账号信息：")
    logger.info(f"邮箱: {email}")
    logger.info(f"密码: {password}")
    
    if not (result := Utils.update_env_vars({'EMAIL': email, 'PASSWORD': password})):
        raise RuntimeError(result.message)
    return email, password

if __name__ == "__main__":
    load_dotenv()
    if result := generate_cursor_account():
        logger.success(f"账号生成成功: {result.data}")
    else:
        logger.error(f"账号生成失败: {result.message}") 