import os
import random
import string
from typing import Tuple, Optional
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger


class CursorAccountGenerator:
    def __init__(self):
        self.domain = os.getenv("DOMAIN")
        if not self.domain:
            raise ValueError("环境变量 'DOMAIN' 未设置")
        
    def generate_random_email(self, min_length: int = 5, max_length: int = 20) -> str:
        email_length = random.randint(min_length, max_length)
        random_chars = ''.join(
            random.choices(string.ascii_lowercase + string.digits, k=email_length)
        )
        return f"{random_chars}@{self.domain}"

    def generate_secure_password(self, length: int = 16) -> str:
        common_special_chars = "!@#$%^&*()"
        password_chars = [
            random.choice(string.ascii_uppercase),
            random.choice(string.ascii_lowercase),
            random.choice(common_special_chars),
            random.choice(string.digits)
        ]
        remaining_length = length - len(password_chars)
        password_chars.extend(
            random.choices(
                string.ascii_letters + string.digits + common_special_chars,
                k=remaining_length
            )
        )
        random.shuffle(password_chars)
        return ''.join(password_chars)

    def generate_account(self) -> Tuple[str, str]:
        email = self.generate_random_email()
        password = self.generate_secure_password()
        return email, password

    @staticmethod
    def update_env_file(email: str, password: str, env_path: Optional[Path] = None) -> None:
        if env_path is None:
            env_path = Path(__file__).parent / '.env'
            
        logger.info(f"正在更新.env文件: {env_path.absolute()}")
            
        try:
            if env_path.exists():
                content = env_path.read_text(encoding='utf-8').splitlines()
            else:
                content = []

            new_vars = {
                'EMAIL': email,
                'PASSWORD': password
            }

            updated_content = []
            updated_keys = set()

            for line in content:
                key = line.split('=')[0] if '=' in line else None
                if key in new_vars:
                    updated_content.append(f'{key}=\'{new_vars[key]}\'')
                    updated_keys.add(key)
                else:
                    updated_content.append(line)

            for key, value in new_vars.items():
                if key not in updated_keys:
                    updated_content.append(f'{key}=\'{value}\'')

            env_path.write_text('\n'.join(updated_content) + '\n', encoding='utf-8')

        except Exception as e:
            raise IOError(f"更新.env文件失败: {str(e)}")


def generate_cursor_account() -> bool:
    try:
        generator = CursorAccountGenerator()
        email, password = generator.generate_account()
        logger.info("生成的Cursor账号信息：")
        logger.info(f"邮箱: {email}")
        logger.info(f"密码: {password}")
        
        env_path = Path(__file__).parent / '.env'
        logger.info(f".env文件位置: {env_path.absolute()}")
        
        generator.update_env_file(email, password)
        os.environ['EMAIL'] = email
        os.environ['PASSWORD'] = password
        logger.success("账号信息已成功更新到.env文件并更新环境变量")
        return email, password
    except ValueError as e:
        logger.error(f"配置错误: {str(e)}")
        return False
    except IOError as e:
        logger.error(f"文件操作错误: {str(e)}")
        return False
    except Exception as e:
        logger.exception("生成Cursor账号时发生未知错误")
        return False


if __name__ == "__main__":
    load_dotenv()
    generate_cursor_account()