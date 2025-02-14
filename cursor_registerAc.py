from DrissionPage import ChromiumOptions, Chromium
import time
import random
import os
from dotenv import load_dotenv
from cursor_utils import Utils
from loguru import logger

class RegistrationInterrupted(Exception):
    """用户中断注册流程的异常"""
    pass

class CursorRegistration:
    def __init__(self):
        load_dotenv()
        required_vars = ['EMAIL', 'PASSWORD', 'DOMAIN']
        if not all(os.getenv(var) for var in required_vars):
            raise ValueError("请确保.env文件中配置了 EMAIL、PASSWORD 和 DOMAIN")
            
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.domain = os.getenv('DOMAIN')
        self.first_name = self.last_name = Utils.generate_random_string(4)
        self.browser = self.tab = None
    
    def _safe_action(self, action, *args, **kwargs):
        try:
            return action(*args, **kwargs)
        except Exception as e:
            logger.error(f"{action.__name__}失败: {str(e)}")
            raise
    
    def init_browser(self):
        co = ChromiumOptions().incognito()
        self.browser = Chromium(co)
        self.tab = self.browser.latest_tab
        self.tab.get('https://authenticator.cursor.sh/sign-up')
        logger.info("浏览器初始化成功")
    
    def input_field(self, fields_dict):
        for name, value in fields_dict.items():
            time.sleep(random.uniform(1, 3))
            self.tab.ele(f'@name={name}').input(value)
            logger.info(f"成功输入 {name}")
    
    def fill_registration_form(self):
        self.input_field({
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email
        })
        
    def fill_password(self):
        self.input_field({'password': self.password})
            
    def get_user_info(self):
        self.tab.get("https://www.cursor.com/settings")
        usage_ele = self.tab.ele("css:div.col-span-2 > div > div > div > div > div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > span.font-mono.text-sm\\/\\[0\\.875rem\\]")
        if usage_ele:
            logger.info(f"账户可用额度上限: {usage_ele.text.split('/')[-1].strip()}")

    def get_cursor_token(self):
        for attempt in range(3):
            try:
                for cookie in self.tab.cookies():
                    if cookie.get("name") == "WorkosCursorSessionToken":
                        return cookie["value"]
                logger.warning(f"第 {attempt + 1} 次尝试未获取到Cookie，3秒后重试...")
                time.sleep(3)
            except Exception as e:
                logger.error(f"获取cookie失败: {str(e)}")
        return None
                    
    def register(self, wait_callback=None):
        try:
            self._safe_action(self.init_browser)
            self._safe_action(self.fill_registration_form)
            
            for step, message in [
                (self.fill_password, "请点击按钮继续"),
                (lambda: None, "请完成注册和验证码验证后继续")
            ]:
                if wait_callback:
                    try:
                        wait_callback(message)
                    except RegistrationInterrupted:
                        logger.info("用户终止了注册流程")
                        return None
                self._safe_action(step)
                
            self._safe_action(self.get_user_info)
            if token := self._safe_action(self.get_cursor_token):
                if not Utils.update_env_vars({"COOKIES_STR": token}).success:
                    logger.error("更新环境变量COOKIES_STR失败")
            return token
            
        except Exception as e:
            if not isinstance(e, RegistrationInterrupted):
                logger.error(f"注册过程发生错误: {str(e)}")
            raise
        finally:
            if self.browser:
                self.browser.quit()

def main():
    try:
        registrar = CursorRegistration()
        if token := registrar.register(lambda msg: input(f"{msg}，完成后按回车键继续...")):
            logger.info(f"获取到的Cookie: {token}")
            logger.info("Cookie已成功更新到环境变量COOKIES_STR")
        else:
            logger.error("获取Cookie失败")
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        
