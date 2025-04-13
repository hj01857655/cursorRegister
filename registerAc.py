import os
import random
import re
import time

from DrissionPage import ChromiumOptions, Chromium
from dotenv import load_dotenv
from loguru import logger

from utils import MoemailManager
from utils import Utils


class CursorRegistration:
    CURSOR_URL = "https://www.cursor.com/"
    CURSOR_SIGNIN_URL = "https://authenticator.cursor.sh"
    CURSOR_PASSWORD_URL = "https://authenticator.cursor.sh/password"
    CURSOR_MAGAIC_CODE_URL = "https://authenticator.cursor.sh/magic-code"
    CURSOR_SIGNUP_URL = "https://authenticator.cursor.sh/sign-up"
    CURSOR_SIGNUP_PASSWORD_URL = "https://authenticator.cursor.sh/sign-up/password"
    CURSOR_SETTING_URL = "https://www.cursor.com/settings"
    CURSOR_EMAIL_VERIFICATION_URL = "https://authenticator.cursor.sh/email-verification"
    
    def __init__(self):
        load_dotenv()
        self.headless = True
        if not os.getenv('GITHUB_ACTIONS'):
            required_vars = ['EMAIL', 'PASSWORD', 'DOMAIN']
            if not all(os.getenv(var) for var in required_vars):
                raise ValueError("请确保.env文件中配置了 EMAIL、PASSWORD 和 DOMAIN")
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.domain = os.getenv('DOMAIN')
        self.first_name = Utils.generate_random_string(4)
        self.last_name = Utils.generate_random_string(4)
        self.retry_times = 5
        self.browser = self.tab = self.moe = None
        self.admin = False

    #安全操作，防止异常中断注册流程
    def _safe_action(self, action, *args, **kwargs):
        try:
            return action(*args, **kwargs)
        except Exception as e:
            logger.error(f"{action.__name__}失败: {str(e)}")
            raise

    #初始化浏览器，并访问注册页面
    def init_browser(self):
        co = ChromiumOptions()
        co.new_env()
        if self.headless:
            co.headless()
        else:
            co.add_extension("./turnstilePatch")
        self.browser = Chromium(co)
        self.tab = self.browser.latest_tab
        self.tab.get(self.CURSOR_SIGNUP_URL)
        logger.debug("浏览器初始化成功")

    #输入注册信息
    def input_field(self, fields_dict):
        for name, value in fields_dict.items():
            self.tab.ele(f'@name={name}').input(value)
            time.sleep(random.uniform(1, 4))
            logger.debug(f"成功输入 {name}")
            logger.debug(f"{value}")
    #填写注册表单
    def fill_registration_form(self):
        self.input_field({
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email
        })
    #填写密码
    def fill_password(self):
        self.input_field({'password': self.password})
    #获取试用信息
    def get_trial_info(self, cookie=None):
        logger.debug("开始获取试用信息")
        self.tab.get(self.CURSOR_SETTING_URL)
        logger.debug(f"已访问设置页面: {self.CURSOR_SETTING_URL}")

        if cookie:
            logger.debug(f"使用提供的cookie: {cookie}")
            self.tab.set.cookies(cookie)
            self.tab.get(self.CURSOR_SETTING_URL)
            logger.debug("已使用cookie重新加载页面")

        logger.debug("尝试定位使用额度元素")
        usage_ele = self.tab.ele(
            "css:div.col-span-2 > div > div > div > div > div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > span.font-mono.text-sm\\/\\[0\\.875rem\\]")

        logger.debug("尝试定位试用天数元素")
        trial_days = self.tab.ele("css:div > span.ml-1\\.5.opacity-50")

        if not usage_ele:
            logger.error("未能找到使用额度元素")
        else:
            logger.debug(f"成功找到使用额度元素，内容为: {usage_ele.text}")

        if not trial_days:
            logger.error("未能找到试用天数元素")
        else:
            logger.debug(f"成功找到试用天数元素，内容为: {trial_days.text}")

        if not usage_ele or not trial_days:
            raise ValueError("无法获取试用信息，页面结构可能已更改")

        logger.debug("成功获取所有试用信息")
        return usage_ele.text, trial_days.text

    #获取cookie中的token值，用于后续操作
    def get_cursor_token(self):
        for attempt in range(3):
            try:
                for cookie in self.tab.cookies():
                    if cookie.get("name") == "WorkosCursorSessionToken":
                        return cookie["value"]
                logger.debug(f"第 {attempt + 1} 次尝试未获取到Cookie，3秒后重试...")
                time.sleep(3)
            except Exception as e:
                logger.error(f"获取cookie失败: {str(e)}")
        return None

    def _handle_page_transition(self, current_url, target_url, action_description, max_retries=5):
        for retry in range(max_retries):
            try:
                if self.tab.wait.url_change(current_url, timeout=5):
                    logger.debug(f"抵达{action_description}")
                    wait_time = random.uniform(2, 5)
                    logger.debug(f"随机等待 {wait_time:.2f} 秒")
                    time.sleep(wait_time)

                if not self.tab.wait.url_change(target_url, timeout=3) and current_url in self.tab.url:
                    self._cursor_turnstile()

                if self.tab.wait.url_change(target_url, timeout=5):
                    logger.debug(f"成功前往{action_description}")
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
            time.sleep(random.uniform(1, 4))
            submit = self.tab.ele("@type=submit")
            self.tab.actions.move_to(ele_or_loc=submit)
            self.tab.actions.click(submit)
            # self.tab.ele("@type=submit").click()
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
            # self.tab.ele("@type=submit").click()
            if not self._handle_page_transition(
                    self.CURSOR_SIGNUP_PASSWORD_URL,
                    self.CURSOR_EMAIL_VERIFICATION_URL,
                    "邮箱验证页面"
            ):
                raise Exception("无法进入邮箱验证页面")

            if self.admin:
                email_data = self.get_email_data()
                verify_code = self.parse_cursor_verification_code(email_data)
                time.sleep(random.uniform(2, 5))
                self._safe_action(self.input_email_verification, verify_code)
            else:
                if wait_callback:
                    try:
                        wait_callback("请输入邮箱验证码继续")
                    except Exception as e:
                        logger.info("用户终止了注册流程")
                        return None
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
        self.moe = MoemailManager()
        email_info = self.moe.create_email(email=self.email)
        logger.debug(f"已创建邮箱 ： {email_info.data.get('email')}")
        self.admin = True
        token = self._safe_action(self.auto_register, wait_callback)
        if token:
            env_updates = {
                "COOKIES_STR": f"WorkosCursorSessionToken={token}",
                "EMAIL": self.email,
                "PASSWORD": self.password
            }
            Utils.update_env_vars(env_updates)
        return token

    def _cursor_turnstile(self):
        max_retries = 5
        for retry in range(max_retries):
            try:
                turnstile_element = self.tab.ele('@id=cf-turnstile', timeout=10)
                if not turnstile_element:
                    logger.debug(f"未找到验证码元素，重试 {retry + 1}/{max_retries}")
                    continue

                shadow_root = turnstile_element.child().shadow_root
                iframe = shadow_root.ele("tag:iframe", timeout=10)

                if not iframe:
                    logger.debug(f"未找到验证码iframe，重试 {retry + 1}/{max_retries}")
                    continue

                checkbox = iframe.ele("tag:body").sr("xpath=//input[@type='checkbox']", timeout=10)
                if checkbox:
                    checkbox.click()
                    logger.debug("成功点击验证码")
                    return True

            except Exception as e:
                logger.debug(f"验证码处理失败 ({retry + 1}/{max_retries}): {str(e)}")
                time.sleep(1)

        logger.error("验证码处理失败")
        return False

    def get_email_data(self):
        for retry in range(self.retry_times):
            try:
                logger.debug(f"尝试获取最新邮件，第 {retry + 1} 次尝试")
                email_data = self.moe.get_latest_email_messages(self.email).data
                logger.debug("成功获取最新邮件数据")
                logger.debug(f"邮件数据结构: {email_data.keys() if isinstance(email_data, dict) else type(email_data)}")
                return email_data
            except Exception as e:
                logger.error(f"获取邮件内容时出错 (第 {retry + 1} 次尝试): {str(e)}")
                if retry == self.retry_times - 1:
                    logger.error(f"已达到最大重试次数 {self.retry_times}，获取邮件失败")
                    raise Exception("获取邮件内容失败")
            time.sleep(2)

    def parse_cursor_verification_code(self, email_data):
        verify_code = None
        logger.debug("开始解析邮件内容获取验证码")

        try:
            if isinstance(email_data, dict) and 'message' in email_data:
                message = email_data['message']
                if 'content' in message:
                    content = message['content']

                    match = re.search(r'\n(\d{6})\n', content)
                    if match:
                        verify_code = match.group(1)
                        logger.info(f"成功提取验证码: {verify_code}")
                    else:
                        logger.error("未在邮件内容中找到6位数字验证码")
                else:
                    logger.error("邮件message中未找到content字段")
            else:
                logger.error("邮件数据格式不正确，缺少message字段")

            if not verify_code:
                raise Exception("无法从邮件内容中提取验证码")

            return verify_code

        except Exception as e:
            logger.error(f"解析验证码时出错: {str(e)}")
            raise

    def input_email_verification(self, verify_code):
        logger.debug(f"开始输入验证码: {verify_code}")
        for retry in range(self.retry_times):
            try:
                logger.debug(f"尝试输入验证码，第 {retry + 1} 次尝试")
                for idx, digit in enumerate(verify_code, start=0):
                    input_element = self.tab.ele(f"xpath=//input[@data-index={idx}]")
                    if input_element:
                        input_element.input(digit, clear=True)
                        logger.debug(f"成功在位置 {idx} 输入数字 {digit}")
                    else:
                        logger.error(f"未找到位置 {idx} 的输入框")
                time.sleep(random.uniform(1, 3))
                if not self.tab.wait.url_change(self.CURSOR_URL,
                                                timeout=3) and self.CURSOR_EMAIL_VERIFICATION_URL in self.tab.url:
                    logger.debug("检测到需要验证码验证，开始处理")
                    self._cursor_turnstile()
                    time.sleep(random.uniform(1, 3))

            except Exception as e:
                logger.error(f"在处理邮箱验证码时出现错误 (第 {retry + 1} 次尝试): {str(e)}")

            if self.tab.wait.url_change(self.CURSOR_URL, timeout=3):
                logger.info("验证码验证成功，页面已跳转")
                break
            if retry == self.retry_times - 1:
                logger.error("在输入验证码时超时，已达到最大重试次数")
                raise Exception("在输入验证码时超时")
