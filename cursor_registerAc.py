from DrissionPage import ChromiumOptions, Chromium, SessionPage
import time
import random
import os
from dotenv import load_dotenv
from cursor_utils import Utils, Result
from loguru import logger

class CursorRegistration:
    def __init__(self):
        self.load_config()
        self.browser = None
        self.tab = None
        
    def load_config(self):
        load_dotenv()
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.domain = os.getenv('DOMAIN')
        
        if not all([self.email, self.password, self.domain]):
            raise ValueError("请确保.env文件中配置了 EMAIL、PASSWORD 和 DOMAIN")
            
        self.first_name = Utils.generate_random_string(4)
        self.last_name = Utils.generate_random_string(4)
    
    def init_browser(self):
        try:
            co = ChromiumOptions()
            co.incognito()
            self.browser = Chromium(co)
            self.tab = self.browser.latest_tab
            self.tab.get('https://authenticator.cursor.sh/sign-up')
            logger.info("浏览器初始化成功")
        except Exception as e:
            logger.error(f"浏览器初始化失败: {str(e)}")
            raise
    
    def input_field(self, field_name, value):
        try:
            time.sleep(random.uniform(1, 3))
            ele = self.tab.ele(f'@name={field_name}')
            ele.input(value)
            logger.info(f"成功输入 {field_name}")
        except Exception as e:
            logger.error(f"输入 {field_name} 失败: {str(e)}")
            raise
    
    def fill_registration_form(self):
        try:
            self.input_field('first_name', self.first_name)
            self.input_field('last_name', self.last_name)
            self.input_field('email', self.email)
        except Exception as e:
            logger.error(f"填写表单失败: {str(e)}")
            raise

    def fill_password(self):
        try:
            self.input_field('password', self.password)
        except Exception as e:
            logger.error(f"填写表单失败: {str(e)}")
            raise
            
    def get_user_info(self):
        self.tab.get("https://www.cursor.com/settings")
        try:
            usage_selector = (
                "css:div.col-span-2 > div > div > div > div > "
                "div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > "
                "span.font-mono.text-sm\\/\\[0\\.875rem\\]"
            )
            usage_ele = self.tab.ele(usage_selector)
            if usage_ele:
                usage_info = usage_ele.text
                total_usage = usage_info.split("/")[-1].strip()
                logger.info(f"账户可用额度上限: {total_usage}")
        except Exception as e:
            logger.error(f"获取账户额度信息失败: {str(e)}")

    def get_cursor_token(self):
        logger.info("开始获取cookie")
        attempts = 0
        max_attempts =3
        retry_interval =3
        while attempts < max_attempts:
            try:
                cookies = self.tab.cookies()
                for cookie in cookies:
                    if cookie.get("name") == "WorkosCursorSessionToken":
                        return cookie["value"]
                attempts += 1
                if attempts < max_attempts:
                    logger.warning(
                        f"第 {attempts} 次尝试未获取到Cookie，{retry_interval}秒后重试..."
                    )
                    time.sleep(retry_interval)
                else:
                    logger.error(
                        f"已达到最大尝试次数({max_attempts})，获取Cookie失败"
                    )

            except Exception as e:
                logger.error(f"获取cookie失败: {str(e)}")
                attempts += 1
                if attempts < max_attempts:
                    logger.info(f"将在 {retry_interval} 秒后重试...")
                    time.sleep(retry_interval)
                    
    def register(self, wait_callback=None):
        try:
            self.init_browser()
            self.fill_registration_form()
            if wait_callback:
                wait_callback("请点击按钮继续")
            self.fill_password()
            if wait_callback:
                wait_callback("请完成注册和验证码验证后继续")
            self.get_user_info()
            token = self.get_cursor_token()
            if token:
                update_result = Utils.update_env_vars({"COOKIES_STR": token})
                if not update_result.success:
                    logger.error(f"更新环境变量COOKIES_STR失败: {update_result.message}")
            return token
        except Exception as e:
            logger.error(f"注册过程发生错误: {str(e)}")
            raise
        finally:
            if self.browser:
                self.browser.quit()

def main():
    try:
        registrar = CursorRegistration()
        token = registrar.register(lambda msg: input(f"{msg}，完成后按回车键继续..."))
        if token:
            logger.info(f"获取到的Cookie: {token}")
            logger.info("Cookie已成功更新到环境变量COOKIES_STR")
        else:
            logger.error("获取Cookie失败")
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        
