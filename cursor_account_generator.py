from typing import Tuple
from dotenv import load_dotenv
from loguru import logger
from cursor_utils import error_handler, EnvManager, StringGenerator

class CursorAccountGenerator:
    def __init__(self):
        self.domain = EnvManager.get_env_var("DOMAIN")
        
    def generate_random_email(self, min_length: int = 5, max_length: int = 20) -> str:
        return f"{StringGenerator.generate_random_string(min_length)}@{self.domain}"

    def generate_account(self) -> Tuple[str, str]:
        email = self.generate_random_email()
        password = StringGenerator.generate_secure_password()
        return email, password

@error_handler
def generate_cursor_account() -> Tuple[str, str]:
    generator = CursorAccountGenerator()
    email, password = generator.generate_account()
    logger.info("生成的Cursor账号信息：")
    logger.info(f"邮箱: {email}")
    logger.info(f"密码: {password}")
    
    result = EnvManager.update_env_vars({'EMAIL': email, 'PASSWORD': password})
    if not result:
        raise RuntimeError(result.message)
    return email, password

def main():
    load_dotenv()
    result = generate_cursor_account()
    if result:
        logger.success(f"账号生成成功: {result.data}")
    else:
        logger.error(f"账号生成失败: {result.message}")

if __name__ == "__main__":
    main() 