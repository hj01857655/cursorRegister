import os
import random
import re
import time

from DrissionPage import ChromiumOptions, Chromium
from dotenv import load_dotenv
from loguru import logger

from utils import Utils


class CursorRegistration:
    CURSOR_URL = "https://www.cursor.com/"
    CURSOR_SIGNIN_URL = "https://authenticator.cursor.sh"  # 登录页
    CURSOR_PASSWORD_URL = "https://authenticator.cursor.sh/password"  # 密码输入页
    CURSOR_MAGAIC_CODE_URL = "https://authenticator.cursor.sh/magic-code"  # 验证码输入页
    CURSOR_SIGNUP_URL = "https://authenticator.cursor.sh/sign-up"  # 注册页
    CURSOR_SIGNUP_PASSWORD_URL = "https://authenticator.cursor.sh/sign-up/password"  # 注册密码设置页
    CURSOR_SETTING_URL = "https://www.cursor.com/settings"  # 个人信息设置页
    CURSOR_EMAIL_VERIFICATION_URL = "https://authenticator.cursor.sh/email-verification"  # 邮箱验证页

    def __init__(self):
        load_dotenv()
        required_vars = ['EMAIL', 'PASSWORD', 'DOMAIN']
        if not all(os.getenv(var) for var in required_vars):
            raise ValueError("请确保.env文件中配置了 EMAIL、PASSWORD 和 DOMAIN")
        self.headless = False
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.domain = os.getenv('DOMAIN')
        self.first_name = self.last_name = Utils.generate_random_string(4)
        self.retry_times = 5
        self.browser = self.tab = None
        self.admin = False

    def _safe_action(self, action, *args, **kwargs):
        try:
            return action(*args, **kwargs)
        except Exception as e:
            logger.error(f"{action.__name__}失败: {str(e)}")
            raise

    def init_browser(self):
        co = ChromiumOptions()
        co.incognito()
        co.add_extension("turnstilePatch")
        if self.headless:
            co.headless()
        self.browser = Chromium(co)
        self.tab = self.browser.latest_tab
        self.tab.get(self.CURSOR_SIGNUP_URL)
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

    def get_trial_info(self, cookie=None):
        self.tab.get(self.CURSOR_SETTING_URL)
        if cookie:
            self.tab.set.cookies(cookie)
            self.tab.get(self.CURSOR_SETTING_URL)
        usage_ele = self.tab.ele(
            "css:div.col-span-2 > div > div > div > div > div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > span.font-mono.text-sm\\/\\[0\\.875rem\\]")
        trial_days = self.tab.ele("css:div > span.ml-1\\.5.opacity-50")
        if not usage_ele or not trial_days:
            raise ValueError("无法获取试用信息，页面结构可能已更改")
        return usage_ele.text, trial_days.text

    def get_user_info(self):
        usage_ele, trial_days = self._safe_action(self.get_trial_info)
        if usage_ele:
            logger.info(f"账户可用额度: {usage_ele}\n试用天数: {trial_days}")

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

    def _handle_page_transition(self, current_url, target_url, action_description, max_retries=5):
        for retry in range(max_retries):
            try:
                if self.tab.wait.url_change(current_url, timeout=5):
                    logger.info(f"抵达{action_description}")

                if not self.tab.wait.url_change(target_url, timeout=3) and current_url in self.tab.url:
                    self._cursor_turnstile()

                if self.tab.wait.url_change(target_url, timeout=5):
                    logger.info(f"成功前往{action_description}")
                    return True

                if self.tab.wait.eles_loaded("xpath=//div[contains(text(), 'Sign up is restricted.')]", timeout=3):
                    raise Exception("注册收到限制.")

                self.tab.refresh()

            except Exception as e:
                logger.error(f"在{action_description}时出现错误: {str(e)}")
                if retry == max_retries - 1:
                    raise Exception(f"在{action_description}时超时")
        return False

    def semi_auto_register(self, wait_callback=None):
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
                    except Exception as e:
                        logger.info("用户终止了注册流程")
                        return None
                    self._safe_action(step)

            self._safe_action(self.get_user_info)
            if token := self._safe_action(self.get_cursor_token):
                if not Utils.update_env_vars({"COOKIES_STR": f"WorkosCursorSessionToken={token}"}).success:
                    logger.error("更新环境变量COOKIES_STR失败")
            return token

        except Exception as e:
            logger.error(f"注册过程发生错误: {str(e)}")
            raise
        finally:
            if self.browser:
                self.browser.quit()

    def auto_register(self, wait_callback=None):
        try:
            self._safe_action(self.init_browser)

            self._safe_action(self.fill_registration_form)
            self.tab.ele("@type=submit").click()
            if not self._handle_page_transition(
                    self.CURSOR_SIGNUP_URL,
                    self.CURSOR_SIGNUP_PASSWORD_URL,
                    "密码设置页面"
            ):
                raise Exception("无法进入密码设置页面")

            self._safe_action(self.fill_password)
            self.tab.ele("@type=submit").click()
            if not self._handle_page_transition(
                    self.CURSOR_SIGNUP_PASSWORD_URL,
                    self.CURSOR_EMAIL_VERIFICATION_URL,
                    "邮箱验证页面"
            ):
                raise Exception("无法进入邮箱验证页面")

            if self.admin:
                verify_code = self._safe_action(self.get_email_verification)
                self._safe_action(self.input_email_verification, verify_code)
            else:
                if wait_callback:
                    try:
                        wait_callback("请输入邮箱验证码继续")
                    except Exception as e:
                        logger.info("用户终止了注册流程")
                        return None
            self._safe_action(self.get_user_info)
            if token := self._safe_action(self.get_cursor_token):
                if not Utils.update_env_vars({"COOKIES_STR": f"WorkosCursorSessionToken={token}"}).success:
                    logger.error("更新环境变量COOKIES_STR失败")
            return token

        except Exception as e:
            logger.error(f"注册过程发生错误: {str(e)}")
            raise
        finally:
            if self.browser:
                self.browser.quit()
    def admin_auto_register(self, wait_callback=None):
        self.admin = True
        self._safe_action(self.auto_register, wait_callback)
    def _cursor_turnstile(self):
        max_retries = 5
        for retry in range(max_retries):
            try:
                turnstile_element = self.tab.ele('@id=cf-turnstile', timeout=10)
                if not turnstile_element:
                    logger.warning(f"未找到验证码元素，重试 {retry + 1}/{max_retries}")
                    continue

                shadow_root = turnstile_element.child().shadow_root
                iframe = shadow_root.ele("tag:iframe", timeout=10)

                if not iframe:
                    logger.warning(f"未找到验证码iframe，重试 {retry + 1}/{max_retries}")
                    continue

                checkbox = iframe.ele("tag:body").sr("xpath=//input[@type='checkbox']", timeout=10)
                if checkbox:
                    checkbox.click()
                    logger.info("成功点击验证码")
                    return True

            except Exception as e:
                logger.warning(f"验证码处理失败 ({retry + 1}/{max_retries}): {str(e)}")
                time.sleep(1)

        logger.error("验证码处理失败")
        return False

    def parse_cursor_verification_code(self, email_data):
        message = ""
        verify_code = None

        if "content" in email_data:
            message = email_data["content"]
            message = message.replace(" ", "")
            verify_code = re.search(r'(?:\r?\n)(\d{6})(?:\r?\n)', message).group(1)
        elif "text" in email_data:
            message = email_data["text"]
            message = message.replace(" ", "")
            verify_code = re.search(r'(?:\r?\n)(\d{6})(?:\r?\n)', message).group(1)

        return verify_code
    def get_email_verification(self, email_data):
        pass

    def input_email_verification(self, verify_code):
        for retry in range(self.retry_times):
            try:
                for idx, digit in enumerate(verify_code, start=0):
                    self.tab.ele(f"xpath=//input[@data-index={idx}]").input(digit, clear=True)
                    self.tab.wait(0.1, 0.3)
                self.tab.wait(0.5, 1.5)

                if not self.tab.wait.url_change(self.CURSOR_URL,
                                                timeout=3) and self.CURSOR_EMAIL_VERIFICATION_URL in self.tab.url:
                    self._cursor_turnstile()

            except Exception as e:
                logger.error("在处理邮箱验证码时出现错误.")
                logger.error(e)

            if self.tab.wait.url_change(self.CURSOR_URL, timeout=3):
                break

            self.tab.refresh()
            if retry == self.retry_times - 1:
                logger.error("在输入验证码时超时")
                raise Exception("在输入验证码时超时")
