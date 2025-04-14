import random
import time
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

import utils
from registerAc import CursorRegistration


class GithubActionRegistration(CursorRegistration):
    def __init__(self):
        super().__init__()
        logger.add(
            sink=Path("./cursorRegister_log") / "{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} |{level:8}| - {message}",
            rotation="50 MB",
            retention="30 days",
            compression="gz",
            enqueue=True,
            backtrace=True,
            diagnose=True,
            level="DEBUG"
        )
        self.headless = True

    def admin_auto_register(self, **kwargs):
        try:

            self.admin = True
            self._safe_action(self.init_browser)
            email_password_result = utils.CursorManager.generate_cursor_account()
            if not email_password_result.success:
                raise Exception(f"生成账号信息失败: {email_password_result.message}")
            self.email, self.password = email_password_result.data
            logger.debug(f"已生成随机邮箱: {self.email}")
            logger.debug(f"已生成随机密码: {self.password}")
            self.moe = utils.MoemailManager()
            email_info = self.moe.create_email(email=self.email)
            logger.debug(f"已创建邮箱 ： {email_info.data.get('email')}")
            self._safe_action(self.fill_registration_form)
            time.sleep(random.uniform(1, 4))
            submit = self.tab.ele("@type=submit")
            self.tab.actions.move_to(ele_or_loc=submit)
            self.tab.actions.click(submit)

            if not self._handle_page_transition(
                    self.CURSOR_SIGNUP_URL,
                    self.CURSOR_SIGNUP_PASSWORD_URL,
                    "密码设置页面"
            ):
                raise Exception("无法进入密码设置页面")

            self._safe_action(self.fill_password)
            time.sleep(random.uniform(1, 4))
            submit = self.tab.ele("@type=submit")
            self.tab.actions.move_to(ele_or_loc=submit)
            self.tab.actions.click(submit)

            if not self._handle_page_transition(
                    self.CURSOR_SIGNUP_PASSWORD_URL,
                    self.CURSOR_EMAIL_VERIFICATION_URL,
                    "邮箱验证页面"
            ):
                raise Exception("无法进入邮箱验证页面")

            email_data = self.get_email_data()
            verify_code = self.parse_cursor_verification_code(email_data)
            time.sleep(random.uniform(2, 5))
            self._safe_action(self.input_email_verification, verify_code)

            # 获取短期和长期令牌
            return self._safe_action(self.get_cursor_token_and_cookie)
        except Exception as e:
            logger.error(f"注册过程发生错误: {str(e)}")
            raise
        finally:
            if self.browser:
                self.browser.quit()


if __name__ == "__main__":
    load_dotenv()
    registration = GithubActionRegistration()
    cookie_token, long_token = registration.admin_auto_register()
    
    # 准备环境变量
    env_updates = {
        "EMAIL": registration.email,
        "PASSWORD": registration.password
    }
    
    # 添加短期和长期令牌
    if cookie_token:
        env_updates["COOKIES_STR"] = f"WorkosCursorSessionToken={cookie_token}"
    if long_token:
        env_updates["TOKEN"] = long_token
        
    # 更新环境变量
    if env_updates:
        registration.utils.update_env_vars(env_updates)
        
        # 保存到文件
        try:
            with open('env_variables.csv', 'w', encoding='utf-8-sig', newline='') as f:
                f.write("variable,value\n")
                for key, value in env_updates.items():
                    f.write(f"{key},{value}\n")
            logger.info("环境变量已保存到 env_variables.csv 文件中")
        except Exception as e:
            logger.error(f"保存环境变量到文件时出错: {str(e)}")
