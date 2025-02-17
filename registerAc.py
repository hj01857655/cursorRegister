import os
import random
import re
import time
from pathlib import Path

import requests
from utils import MoemailManager
from DrissionPage import ChromiumOptions, Chromium
from dotenv import load_dotenv
from loguru import logger

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
        self.headless = False
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
    def _safe_action(self, action, *args, **kwargs):
        try:
            return action(*args, **kwargs)
        except Exception as e:
            logger.error(f"{action.__name__}失败: {str(e)}")
            raise

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
        logger.info("浏览器初始化成功")

    def _random_wait(self, min_seconds=1, max_seconds=4, message=None):
        """
        随机等待一段时间
        :param min_seconds: 最小等待秒数
        :param max_seconds: 最大等待秒数
        :param message: 等待时显示的消息
        :return: 实际等待的秒数
        """
        wait_time = random.uniform(min_seconds, max_seconds)
        if message:
            logger.info(f"{message} {wait_time:.2f} 秒")
        time.sleep(wait_time)
        return wait_time

    def _wait_for_element(self, selector, selector_type="", timeout=10, description="元素"):
        """
        等待元素出现
        :param selector: 元素选择器
        :param selector_type: 选择器类型（xpath, css, @attribute等）
        :param timeout: 超时时间
        :param description: 元素描述
        :return: 找到的元素
        """
        try:
            if selector_type:
                element = self.tab.ele(f"{selector_type}:{selector}", timeout=timeout)
            else:
                element = self.tab.ele(selector, timeout=timeout)
            if element:
                logger.info(f"成功找到{description}")
                return element
            logger.warning(f"未找到{description}")
            return None
        except Exception as e:
            logger.error(f"等待{description}时出错: {str(e)}")
            return None

    def _wait_for_url_change(self, expected_url, timeout=5, description="目标页面"):
        try:
            if self.tab.wait.url_change(expected_url, timeout=timeout):
                logger.info(f"成功到达{description}")
                return True
            logger.warning(f"等待{description}超时")
            return False
        except Exception as e:
            logger.error(f"等待{description}时出错: {str(e)}")
            return False

    def input_field(self, fields_dict):
        for name, value in fields_dict.items():
            self.tab.ele(f'@name={name}').input(value)
            self._random_wait(message=f"输入 {name} 后等待")
            logger.info(f"成功输入 {name}")
            logger.info(f"{value}")

    def fill_registration_form(self):
        self.input_field({
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email
        })

    def fill_password(self):
        self.input_field({'password': self.password})

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
                if self._wait_for_url_change(current_url, description=action_description):
                    self._random_wait(2, 5, "随机等待")

                if not self._wait_for_url_change(target_url, timeout=3) and current_url in self.tab.url:
                    self._cursor_turnstile()

                if self._wait_for_url_change(target_url, description=action_description):
                    return True

                if self._wait_for_element("//div[contains(text(), 'Sign up is restricted.')]", "xpath", 3, "注册限制提示"):
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
            self._random_wait()
            submit = self._wait_for_element("@type=submit", description="提交按钮")
            if submit:
                self.tab.actions.move_to(ele_or_loc=submit)
                self.tab.actions.click(submit)

            if not self._handle_page_transition(
                    self.CURSOR_SIGNUP_URL,
                    self.CURSOR_SIGNUP_PASSWORD_URL,
                    "密码设置页面"
            ):
                raise Exception("无法进入密码设置页面")

            self._safe_action(self.fill_password)
            self._random_wait()
            submit = self._wait_for_element("@type=submit", description="提交按钮")
            if submit:
                self.tab.actions.move_to(ele_or_loc=submit)
                self.tab.actions.click(submit)

            if not self._handle_page_transition(
                    self.CURSOR_SIGNUP_PASSWORD_URL,
                    self.CURSOR_EMAIL_VERIFICATION_URL,
                    "邮箱验证页面"
            ):
                raise Exception("无法进入邮箱验证页面")

            if self.admin:
                email_data = self.get_email_data()
                verify_code = self.parse_cursor_verification_code(email_data)
                self._random_wait(2, 5)
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
        self.moe = MoemailManager()
        email_address = self.moe.create_email(DOMAIN=os.getenv("DOMAIN"))
        self.email = email_address.data
        self.password = Utils.generate_secure_password()
        self.admin = True
        token = self._safe_action(self.auto_register, wait_callback)
        return token
    def _cursor_turnstile(self):
        max_retries = 5
        for retry in range(max_retries):
            try:
                turnstile_element = self._wait_for_element('@id=cf-turnstile', description="验证码元素")
                if not turnstile_element:
                    logger.warning(f"未找到验证码元素，重试 {retry + 1}/{max_retries}")
                    continue

                shadow_root = turnstile_element.child().shadow_root
                iframe = self._wait_for_element("tag:iframe", description="验证码iframe", timeout=10)

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
                self._random_wait(1, 1)

        logger.error("验证码处理失败")
        return False

    def get_email_data(self):
        for retry in range(self.retry_times):
            try:
                logger.info(f"尝试获取最新邮件，第 {retry + 1} 次尝试")
                email_data = self.moe.get_latest_email_messages(self.email).data
                logger.info("成功获取最新邮件数据")
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
        logger.info("开始解析邮件内容获取验证码")

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
        logger.info(f"开始输入验证码: {verify_code}")
        for retry in range(self.retry_times):
            try:
                logger.info(f"尝试输入验证码，第 {retry + 1} 次尝试")
                for idx, digit in enumerate(verify_code, start=0):
                    input_element = self.tab.ele(f"xpath=//input[@data-index={idx}]")
                    if input_element:
                        input_element.input(digit, clear=True)
                        logger.debug(f"成功在位置 {idx} 输入数字 {digit}")
                    else:
                        logger.error(f"未找到位置 {idx} 的输入框")
                time.sleep(random.uniform(1, 3))
                if not self.tab.wait.url_change(self.CURSOR_URL, timeout=3) and self.CURSOR_EMAIL_VERIFICATION_URL in self.tab.url:
                    logger.info("检测到需要验证码验证，开始处理")
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

    def github_action_register(self):
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
        token =self.admin_auto_register()
        if token:
            env_updates = {
                "COOKIES_STR": f"WorkosCursorSessionToken={token}",
                "EMAIL": self.email,
                "PASSWORD": self.password
            }
            Utils.update_env_vars(env_updates)
            try:
                with open('env_variables.csv', 'w', encoding='utf-8', newline='') as f:
                    f.write("variable,value\n")
                    for key, value in env_updates.items():
                        f.write(f"{key},{value}\n")
                logger.info("环境变量已保存到 env_variables.csv 文件中")
            except Exception as e:
                logger.error(f"保存环境变量到文件时出错: {str(e)}")



if __name__ == "__main__":
    load_dotenv()
    CursorRegistration().github_action_register()