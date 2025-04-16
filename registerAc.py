import os
import random
import re
import time
import secrets
import uuid
import hashlib
import base64
import requests
import threading
import queue
from DrissionPage import ChromiumOptions, Chromium
from loguru import logger
from utils import MoemailManager, Utils, CursorManager, Result
#生成随机字符串
from faker import Faker
import json

#cursor注册类
class CursorRegistration:
    #主页
    CURSOR_URL = "https://www.cursor.com/cn"
    #登录页面
    CURSOR_SIGNIN_URL = "https://www.cursor.com/api/auth/login"
    #密码设置页面
    CURSOR_PASSWORD_URL = "https://authenticator.cursor.sh/password"
    #魔法代码页面
    CURSOR_MAGAIC_CODE_URL = "https://authenticator.cursor.sh/magic-code"
    #注册页面
    CURSOR_SIGNUP_URL = "https://authenticator.cursor.sh/sign-up"
    #密码设置页面
    CURSOR_SIGNUP_PASSWORD_URL = "https://authenticator.cursor.sh/sign-up/password"
    
    #设置页面
    CURSOR_SETTING_URL = "https://www.cursor.com/settings"
    #邮箱验证页面
    CURSOR_EMAIL_VERIFICATION_URL = "https://authenticator.cursor.sh/email-verification"
    #使用信息页面
    CURSOR_USAGE_URL = "https://www.cursor.com/api/usage"
    

    #初始化
    def __init__(self,browser=None):
        # #加载环境变量
        # load_dotenv()
        #是否无头
        self.headless = False
        #如果不在github actions中，则需要配置EMAIL、PASSWORD
        if not os.getenv('GITHUB_ACTIONS'):
            #如果未配置，则抛出异常
            required_vars = ['DOMAIN','EMAIL', 'PASSWORD']
            if not all(os.getenv(var) for var in required_vars):
                raise ValueError("请确保.env文件中配置了 DOMAIN、EMAIL 和 PASSWORD")
        #获取环境变量
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.domain = os.getenv('DOMAIN')
        self.first_name = Utils.generate_random_string(4)
        self.last_name = Utils.generate_random_string(4)

        # 清除可能存在的代理环境变量，确保直连
        if 'HTTP_PROXY' in os.environ:
            del os.environ['HTTP_PROXY']
            logger.debug("已清除 HTTP_PROXY 环境变量，使用直连模式")
        if 'HTTPS_PROXY' in os.environ:
            del os.environ['HTTPS_PROXY']
            logger.debug("已清除 HTTPS_PROXY 环境变量，使用直连模式")
        if 'NO_PROXY' in os.environ:
            del os.environ['NO_PROXY']
            logger.debug("已清除 NO_PROXY 环境变量")

        #邮箱队列
        self.email_queue=queue.Queue()
        #获取当前线程ID
        self.thread_id = threading.current_thread().ident
        #重试次数
        self.retry_times = 5
        #初始化浏览器，通过browser参数传入
        self.browser = self.tab = self.moe = None
        #是否全自动
        self.admin = False
        

    #安全操作，防止异常中断注册流程，接受一个函数作为参数，并返回函数执行结果
    def _safe_action(self, action, *args, **kwargs):
        try:
            return action(*args, **kwargs)
        except Exception as e:
            logger.error(f"{action.__name__}失败: {str(e)}")
            raise

    #初始化浏览器，并访问登录页面
    def init_browser(self):
        # 如果已有浏览器实例，返回
        if self.browser:
            #获取最新tab
            self.tab = self.browser.latest_tab
            #访问登录页面
            self.tab.get(self.CURSOR_SETTING_URL)
            return
        #初始化浏览器
        co = ChromiumOptions()
        #设置为隐身模式
        co.set_argument("--incognito")
        #自动端口
        co.auto_port()
        #新环境
        co.new_env()
        #禁用所有代理设置，确保直连
        co.set_argument("--no-proxy-server")
        #是否无头
        if self.headless:
            #设置无头
            co.headless()
        else:   
            #添加扩展
            turnstile_path = str(Utils.get_path('turnstilePatch'))
            if os.path.exists(turnstile_path):
                logger.debug(f"添加扩展: {turnstile_path}")
                #允许扩展在隐身模式下使用
                co.set_argument("--allow-extensions-in-incognito")
                #添加扩展
                co.add_extension(turnstile_path)
        #初始化浏览器
        self.browser = Chromium(co)
        #获取最新tab
        self.tab = self.browser.latest_tab
        logger.debug(f"浏览器初始化成功: {self.browser}")
        
        
        time.sleep(random.uniform(2, 5))  # 增加随机等待时间
        
        # 在页面上执行一些随机滚动，模拟人类行为
        self.tab.run_js('window.scrollTo(0, document.body.scrollHeight / 3);')
        time.sleep(random.uniform(0.5, 1.5))
        self.tab.run_js('window.scrollTo(0, document.body.scrollHeight / 1.5);')
        time.sleep(random.uniform(0.5, 2))
        self.tab.run_js('window.scrollTo(0, 0);')
        time.sleep(random.uniform(1, 3))
        
        # 然后访问登录页面
        logger.debug(f"访问登录页面: {self.CURSOR_SIGNIN_URL}")
        #访问登录页面
        self.tab.get(self.CURSOR_SIGNIN_URL)
        #随机等待
        time.sleep(random.uniform(2, 4))
        
        # 模拟在登录页面上的一些操作
        try:
            #获取邮箱输入框
            email_field = self.tab.ele("xpath=//input[@name='email']")
            #如果邮箱输入框存在
            if email_field:
                #点击邮箱输入框
                email_field.click()
                #随机等待
                time.sleep(random.uniform(0.3, 0.8))
        except:
            pass
        #换一种方式进入注册页面

        # 最后访问注册页面
        logger.debug(f"访问注册页面: {self.CURSOR_SIGNUP_URL}")
        self.tab.get(self.CURSOR_SIGNUP_URL)
        logger.debug(f"成功进入注册页面")
    
    #处理页面跳转
    def _handle_page_transition(self, current_url, target_url, action_description, max_retries=5):
        #重试
        for retry in range(max_retries):
            try:
                #如果当前页面发生变化
                if self.tab.wait.url_change(current_url, timeout=5):
                    logger.debug(f"抵达{action_description}")
                    #随机等待
                    wait_time = random.uniform(2, 5)
                    logger.debug(f"随机等待 {wait_time:.2f} 秒")
                    time.sleep(wait_time)
                #如果当前页面发生变化
                if not self.tab.wait.url_change(target_url, timeout=3) and current_url in self.tab.url:
                    # 这里添加等待用户手动验证的提示
                    logger.info("等待用户手动完成验证...")
                    #随机等待
                    # 等待用户手动验证 (30秒)
                    for i in range(30):
                        #如果注册收到限制
                        if self.tab.wait.eles_loaded("xpath=//div[contains(text(), 'Sign up is restricted.')]", timeout=3):
                            raise Exception("注册收到限制.")
                        #每5秒提示一次
                        if i % 5 == 0:  # 每5秒提示一次
                            logger.info(f"请手动完成验证，已等待 {i} 秒...")
                    #尝试处理 turnstile
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
    
    #输入注册信息
    def input_field(self, fields_dict):
        # 存储已输入的值
        input_values = {}
        for name, value in fields_dict.items():
            # 获取当前输入框的值
            field = self.tab.ele(f'@name={name}')
            # 保存当前输入的值
            input_values[name] = value
            # 再次检查之前输入的内容是否还在
            for prev_name, prev_value in input_values.items():
                if prev_name != name:
                    prev_field = self.tab.ele(f'@name={prev_name}')
                    prev_current_value = prev_field.attr('value')
                    # 如果之前的值被清空，重新输入
                    if not prev_current_value or prev_current_value != prev_value:
                        logger.debug(f"检测到 {prev_name} 的值被清空，正在重新输入")
                        prev_field.input(prev_value)
                        time.sleep(random.uniform(0.5, 1))
            # 输入当前字段的值
            field.input(value)
            time.sleep(random.uniform(1, 2))
            logger.debug(f"成功输入 {name}: {value}")
    

    #填写注册表单
    def fill_registration_form(self):
        # 分别输入每个字段，检查并维护所有字段的值
        self.input_field({
            'first_name': self.first_name
        })
        time.sleep(random.uniform(0.5, 1))
        
        # 检查 first_name 是否仍然存在
        first_name_field = self.tab.ele('@name=first_name')
        first_name_value = first_name_field.attr('value')
        if not first_name_value or first_name_value != self.first_name:
            logger.debug(f"检测到 first_name 的值已被清空，重新输入")
            first_name_field.input(self.first_name)
            time.sleep(random.uniform(0.5, 1))
            
        # 输入 last_name
        self.tab.ele('@name=last_name').input(self.last_name)
        time.sleep(random.uniform(1, 2))
        logger.debug(f"成功输入 last_name: {self.last_name}")
        
        # 检查 first_name 和 last_name 是否仍然存在
        first_name_field = self.tab.ele('@name=first_name')
        first_name_value = first_name_field.attr('value')
        if not first_name_value or first_name_value != self.first_name:
            logger.debug(f"检测到 first_name 的值已被清空，重新输入")
            first_name_field.input(self.first_name)
            time.sleep(random.uniform(0.5, 1))
            
        # 输入 email
        self.tab.ele('@name=email').input(self.email)
        time.sleep(random.uniform(1, 2))
        logger.debug(f"成功输入 email: {self.email}")
        
        # 最终检查并确保所有字段都有值
        fields = {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email
        }
        
        for name, value in fields.items():
            field = self.tab.ele(f'@name={name}')
            current_value = field.attr('value')
            if not current_value or current_value != value:
                logger.debug(f"最终检查: {name} 的值需要重新输入")
                field.input(value)
                time.sleep(random.uniform(0.5, 1))
    
    #填写密码
    def fill_password(self):
        self.input_field({'password': self.password})
    
    
    #人工验证
    def semi_auto_register(self, wait_callback=None):
        try:
            #初始化浏览器
            self._safe_action(self.init_browser)
            #填写注册信息
            self._safe_action(self.fill_registration_form)
            #填写密码
            for step, message in [
                (self.fill_password, "请点击按钮继续"),
                (lambda: None, "请完成注册和验证码验证后继续")
            ]:
                if wait_callback:
                    try:
                        wait_callback(message)
                    except Exception as e:
                        logger.info("用户终止了注册流程")
                        return None, None
                    self._safe_action(step)

            # 获取短期和长期令牌
            cookie_token, access_token, refresh_token = self._safe_action(self.get_cursor_access_token_and_refresh_token_and_cookie)
            
            # 更新环境变量
            if cookie_token or access_token or refresh_token:
                env_updates = {}
                if cookie_token:
                    env_updates["COOKIES_STR"] = f"WorkosCursorSessionToken={cookie_token}"
                if access_token:
                    env_updates["TOKEN"] = access_token
                if refresh_token:
                    env_updates["REFRESH_TOKEN"] = refresh_token
                
                if not Utils.update_env_vars(env_updates).success:
                    logger.error("更新环境变量失败")
            
            # 返回获取的令牌
            return cookie_token, access_token, refresh_token

        except Exception as e:
            logger.error(f"【人工验证】注册过程发生错误: {str(e)}")
            raise
        finally:
            if self.browser:
                self.browser.quit()
    
    #自动注册
    def auto_register(self, wait_callback=None):
        try:
            self._safe_action(self.init_browser)
            self._safe_action(self.fill_registration_form)
            time.sleep(random.uniform(1, 4))
            
            # 最后检查一次所有字段是否已填写
            fields = {
                'first_name': self.first_name,
                'last_name': self.last_name,
                'email': self.email
            }
            for name, value in fields.items():
                field = self.tab.ele(f'@name={name}')
                current_value = field.attr('value')
                if not current_value or current_value != value:
                    logger.info(f"提交前检查: {name} 需要重新输入")
                    field.input(value)
                    time.sleep(random.uniform(0.5, 1))
            
            submit = self.tab.ele("@type=submit")
            self.tab.actions.move_to(ele_or_loc=submit)
            self.tab.actions.click(submit)
            
            # 等待用户完成验证 (最多60秒)
            logger.info("等待用户完成 Turnstile 验证...")
            max_wait_time = 60  # 等待最长60秒
            for i in range(max_wait_time):
                # 每秒检查一次页面是否已跳转
                if self.tab.wait.url_change(self.CURSOR_SIGNUP_URL, timeout=1):
                    logger.info("检测到页面变化，验证可能已完成")
                    break
                if i % 10 == 0:  # 每10秒提示一次
                    logger.info(f"请手动完成验证，已等待 {i} 秒，还有 {max_wait_time - i} 秒...")
            
            # 检查是否进入密码设置页面
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
            
            # 等待用户完成验证 (最多60秒)
            logger.info("等待用户完成密码页面的 Turnstile 验证...")
            for i in range(max_wait_time):
                # 每秒检查一次页面是否已跳转
                if self.tab.wait.url_change(self.CURSOR_SIGNUP_PASSWORD_URL, timeout=1):
                    logger.info("检测到页面变化，验证可能已完成")
                    break
                if i % 10 == 0:  # 每10秒提示一次
                    logger.info(f"请手动完成验证，已等待 {i} 秒，还有 {max_wait_time - i} 秒...")
            
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
                        return None, None
                        
            # 获取短期和长期令牌
            cookie_token, access_token, refresh_token = self._safe_action(self.get_cursor_access_token_and_refresh_token_and_cookie)
            
            # 返回获取的令牌
            return cookie_token, access_token, refresh_token

        except Exception as e:
            logger.error(f"【自动注册】注册过程发生错误: {str(e)}")
            raise
        finally:
            if self.browser:
                self.browser.quit()
    
    #全自动注册
    def admin_auto_register(self, wait_callback=None):
        try:
            self.moe = MoemailManager()
            email_info = self.moe.create_email(email=self.email)
            logger.debug(f"已创建邮箱 ： {email_info.data.get('email')}")
            self.admin = True
            
            # 初始化浏览器
            self._safe_action(self.init_browser)
            # 填写注册表单
            self._safe_action(self.fill_registration_form)
            time.sleep(random.uniform(1, 4))
            
            # 最后检查一次所有字段是否已填写
            fields = {
                'first_name': self.first_name,
                'last_name': self.last_name,
                'email': self.email
            }
            for name, value in fields.items():
                field = self.tab.ele(f'@name={name}')
                current_value = field.attr('value')
                if not current_value or current_value != value:
                    logger.info(f"提交前检查: {name} 需要重新输入")
                    field.input(value)
                    time.sleep(random.uniform(0.5, 1))
            
            # 点击提交按钮
            submit = self.tab.ele("@type=submit")
            self.tab.actions.move_to(ele_or_loc=submit)
            self.tab.actions.click(submit)
            
            # 等待用户完成验证 (最多90秒)
            logger.info("等待用户完成 Turnstile 验证...")
            max_wait_time = 90  # 等待最长90秒
            for i in range(max_wait_time):
                # 每秒检查一次页面是否已跳转
                if self.tab.wait.url_change(self.CURSOR_SIGNUP_URL, timeout=1):
                    logger.info("检测到页面变化，验证可能已完成")
                    break
                if i % 10 == 0:  # 每10秒提示一次
                    logger.info(f"请手动完成验证，已等待 {i} 秒，还有 {max_wait_time - i} 秒...")
                    if wait_callback:
                        try:
                            wait_callback(f"请手动完成验证，已等待 {i} 秒")
                        except Exception as e:
                            logger.info("用户终止了注册流程")
                            return None, None
            
            # 检查是否进入密码设置页面
            if not self._handle_page_transition(
                    self.CURSOR_SIGNUP_URL,
                    self.CURSOR_SIGNUP_PASSWORD_URL,
                    "密码设置页面"
            ):
                raise Exception("无法进入密码设置页面")

            # 填写密码
            self._safe_action(self.fill_password)
            time.sleep(random.uniform(1, 4))
            
            # 点击提交按钮
            submit = self.tab.ele("@type=submit")
            self.tab.actions.move_to(ele_or_loc=submit)
            self.tab.actions.click(submit)
            
            # 等待用户完成验证 (最多90秒)
            logger.info("等待用户完成密码页面的 Turnstile 验证...")
            for i in range(max_wait_time):
                # 每秒检查一次页面是否已跳转
                if self.tab.wait.url_change(self.CURSOR_SIGNUP_PASSWORD_URL, timeout=1):
                    logger.info("检测到页面变化，验证可能已完成")
                    break
                if i % 10 == 0:  # 每10秒提示一次
                    logger.info(f"请手动完成验证，已等待 {i} 秒，还有 {max_wait_time - i} 秒...")
                    if wait_callback:
                        try:
                            wait_callback(f"请手动完成密码页面验证，已等待 {i} 秒")
                        except Exception as e:
                            logger.info("用户终止了注册流程")
                            return None, None
            
            # 检查是否进入邮箱验证页面
            if not self._handle_page_transition(
                    self.CURSOR_SIGNUP_PASSWORD_URL,
                    self.CURSOR_EMAIL_VERIFICATION_URL,
                    "邮箱验证页面"
            ):
                raise Exception("无法进入邮箱验证页面")

            # 获取并输入验证码
            email_data = self.get_email_data()
            verify_code = self.parse_cursor_verification_code(email_data)
            time.sleep(random.uniform(2, 5))
            self._safe_action(self.input_email_verification, verify_code)
            
            # 获取短期和长期令牌
            cookie_token, access_token, refresh_token = self._safe_action(self.get_cursor_access_token_and_refresh_token_and_cookie)
            
            # 更新环境变量
            if cookie_token or access_token or refresh_token:
                env_updates = {
                    "EMAIL": self.email,
                    "PASSWORD": self.password
                }
                if cookie_token:
                    env_updates["COOKIES_STR"] = f"WorkosCursorSessionToken={cookie_token}"
                if access_token:
                    env_updates["TOKEN"] = access_token
                if refresh_token:
                    env_updates["REFRESH_TOKEN"] = refresh_token
                
                Utils.update_env_vars(env_updates)
            
            # 返回获取的令牌
            return cookie_token, access_token, refresh_token

        except Exception as e:
            logger.error(f"注册过程发生错误: {str(e)}")
            raise
        finally:
            if self.browser:
                self.browser.quit()
    
    #获取使用信息
    def get_usage(self,user_id):
        try:
            # 设置更长的超时时间
            self.browser.set.timeout(30)
            tab=self.browser.new_tab(f"{self.CURSOR_USAGE_URL}?user={user_id}")
            return tab.json
        except Exception as e:
            logger.error(f"获取使用信息失败: {str(e)}")
            return None
    
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

    #删除账号
    def delete_account(self):
        tab=self.browser.new_tab(self.CURSOR_SETTING_URL)
        tab.ele("xpath=//div[contains(text(), 'Advanced')]").click()
        tab.ele("xpath=//button[contains(text(), 'Delete Account')]").click()
        tab.ele("""xpath=//input[@placeholder="Type 'Delete' to confirm"]""").input("Delete", clear=True)
        tab.ele("xpath=//span[contains(text(), 'Delete')]").click()
        return tab

    #处理clouldflare验证
    def _cursor_turnstile(self, tab=None):
        # 如果未传入tab参数，使用当前tab
        if tab is None:
            tab = self.tab
            
        logger.debug("开始处理Turnstile验证码")
        try:
            # 1. 尝试重置turnstile (如果已存在)
            tab.run_js("try { turnstile.reset() } catch(e) { }")
            
            # 记录当前时间戳，用于后面保存错误截图
            timestamp = int(time.time())
            
            # 2. 尝试直接通过JavaScript绕过验证
            logger.debug("尝试通过JavaScript绕过验证")
            try:
                # 尝试执行JS绕过 - 模拟成功的turnstile响应
                js_bypass_result = tab.run_js("""
                try {
                    // 模拟turnstile的回调函数
                    if (typeof window.turnstile !== 'undefined' && typeof window.turnstile.execute === 'function') {
                        // 尝试直接调用turnstile.execute
                        window.turnstile.execute();
                        return "尝试调用turnstile.execute()";
                    }
                    
                    // 查找turnstile相关元素
                    const elements = document.querySelectorAll('[class*="turnstile"], [id*="turnstile"], [data-sitekey]');
                    if (elements.length > 0) {
                        for (let elem of elements) {
                            // 尝试触发任何可能的事件处理程序
                            elem.click();
                        }
                        return "点击了turnstile相关元素";
                    }
                    
                    return "未找到turnstile元素";
                } catch (e) {
                    return "JS执行错误: " + e.toString();
                }
                """)
                logger.debug(f"JavaScript绕过结果: {js_bypass_result}")
            except Exception as e:
                logger.debug(f"JavaScript绕过尝试失败: {str(e)}")
            
            # 3. 查找验证码iframe - 方法1：通过ID
            logger.debug("查找验证码iframe - 方法1：通过ID")
            try:
                # 首先尝试通过cf-turnstile-response元素查找
                turnstile_element = tab.ele('@id=cf-cf-turnstile-response', timeout=3)
                if turnstile_element:
                    logger.debug(f"找到验证码元素: {turnstile_element}")
                    shadow_root = turnstile_element.child().shadow_root
                    iframe = shadow_root.ele("tag:iframe", timeout=3)
                    if iframe:
                        logger.debug("找到验证码iframe，准备点击")
                        checkbox = iframe.ele("tag:body").sr("xpath=//input[@type='checkbox']", timeout=3)
                        if checkbox:
                            checkbox.click()
                            logger.debug("成功点击验证码")
                            time.sleep(2)  # 等待验证完成
                            
                            # 检查是否成功解决验证码
                            js_result = tab.run_js("try { return turnstile.getResponse() } catch(e) { return null }")
                            if js_result:
                                logger.debug(f"成功获取turnstile响应: {js_result[:30]}...")
                                return True
            except Exception as e:
                logger.debug(f"通过ID查找验证码元素失败: {str(e)}")
            
            # 4. 检查是否有data-sitekey属性的元素
            logger.debug("查找data-sitekey属性的元素")
            try:
                sitekey_elements = tab.eles("xpath=//*[@data-sitekey]")
                if sitekey_elements:
                    logger.debug(f"找到{len(sitekey_elements)}个带data-sitekey的元素")
                    for i, elem in enumerate(sitekey_elements):
                        try:
                            sitekey = elem.attr("data-sitekey")
                            logger.debug(f"元素 {i+1} 的 data-sitekey: {sitekey}")
                            elem.click()
                            logger.debug(f"已点击data-sitekey元素 {i+1}")
                            time.sleep(1)
                        except Exception as click_e:
                            logger.debug(f"点击data-sitekey元素 {i+1} 失败: {str(click_e)}")
            except Exception as e:
                logger.debug(f"查找data-sitekey元素失败: {str(e)}")
            
            # 5. 查找所有iframe - 方法2：遍历
            logger.debug("查找验证码iframe - 方法2：遍历所有iframe")
            try:
                iframes = tab.eles("tag:iframe")
                logger.debug(f"找到 {len(iframes)} 个iframe")
                
                for i, iframe in enumerate(iframes):
                    try:
                        iframe_src = iframe.attr("src") or ""
                        logger.debug(f"检查iframe {i+1}/{len(iframes)}, src: {iframe_src}")
                        
                        if "challenges.cloudflare.com" in iframe_src or "turnstile" in iframe_src:
                            logger.debug(f"找到Turnstile相关iframe: {iframe_src}")
                            
                            # 切换到iframe
                            iframe_document = iframe.ele("tag:body")
                            logger.debug("已切换到iframe内部")
                            
                            # 查找验证按钮 (可能是checkbox或其他可点击元素)
                            for selector in ["input[type='checkbox']", "button", ".mark", "input", "div[role='button']", "div.m-1"]:
                                try:
                                    checkbox = iframe_document.sr(f"css:{selector}")
                                    if checkbox:
                                        logger.debug(f"在iframe中找到可点击元素: {selector}")
                                        checkbox.click()
                                        logger.debug("成功点击验证码元素")
                                        time.sleep(2)  # 等待验证完成
                                        
                                        # 检查是否成功
                                        js_result = tab.run_js("try { return turnstile.getResponse() } catch(e) { return null }")
                                        if js_result:
                                            logger.debug(f"成功获取turnstile响应: {js_result[:30]}...")
                                            return True
                                except Exception as e:
                                    logger.debug(f"选择器 {selector} 查找失败: {str(e)}")
                    except Exception as e:
                        logger.debug(f"处理iframe {i+1} 失败: {str(e)}")
            except Exception as e:
                logger.debug(f"查找所有iframe失败: {str(e)}")
            
            # 6. 尝试使用选择器直接查找
            logger.debug("尝试使用选择器直接查找验证码元素")
            selectors = [
                "div[class*='turnstile']", 
                "div[data-sitekey]",
                "iframe[src*='cloudflare']", 
                "iframe[src*='turnstile']",
                "div[id^='cf-']",
                "div[class*='cf-']",
                "div.cf-turnstile",
                "iframe.cf-iframe"
            ]
            
            for selector in selectors:
                try:
                    elements = tab.eles(f"css:{selector}")
                    logger.debug(f"使用选择器 {selector} 找到 {len(elements)} 个元素")
                    
                    if elements:
                        elements[0].click()
                        logger.debug(f"点击了第一个 {selector} 元素")
                        time.sleep(1.5)
                        
                        # 检查点击后是否出现新的iframe
                        iframes_after = tab.eles("tag:iframe")
                        if len(iframes_after) > len(iframes):
                            logger.debug(f"点击后出现了新的iframe，现在有 {len(iframes_after)} 个")
                            new_iframe = iframes_after[-1]  # 假设最新的iframe是最后一个
                            try:
                                iframe_document = new_iframe.ele("tag:body")
                                checkbox = iframe_document.sr("css:input[type='checkbox'], button, .mark")
                                if checkbox:
                                    logger.debug("在新iframe中找到复选框")
                                    checkbox.click()
                                    logger.debug("点击了新iframe中的复选框")
                                    time.sleep(2)
                            except Exception as e:
                                logger.debug(f"处理新iframe失败: {str(e)}")
                except Exception as e:
                    logger.debug(f"选择器 {selector} 操作失败: {str(e)}")
            
            # 7. 尝试模拟人类行为，包括鼠标移动和点击
            logger.debug("尝试模拟人类行为绕过验证")
            try:
                # 执行随机鼠标移动
                for _ in range(5):
                    x = random.randint(100, 500)
                    y = random.randint(100, 500)
                    tab.move_to(x=x, y=y)
                    time.sleep(random.uniform(0.1, 0.3))
                
                # 随机滚动页面
                tab.run_js("window.scrollTo(0, document.body.scrollHeight / 3);")
                time.sleep(random.uniform(0.5, 1))
                tab.run_js("window.scrollTo(0, 0);")
                time.sleep(random.uniform(0.5, 1))
                
                # 检查可能的验证码元素
                possible_elements = tab.eles("css:iframe[src*='cloudflare'], iframe[src*='turnstile'], div[class*='turnstile']")
                if possible_elements:
                    logger.debug("找到可能的验证码元素，进行点击")
                    possible_elements[0].click()
                    time.sleep(1.5)
                
                # 再次检查验证是否成功
                response = tab.run_js("try { return turnstile.getResponse() } catch(e) { return null }")
                if response:
                    logger.debug(f"验证成功，获取到token: {response[:20]}...")
                    return True
            except Exception as e:
                logger.debug(f"模拟人类行为失败: {str(e)}")
            
            # 8. 尝试通过添加自定义WebDriver参数绕过检测
            logger.debug("尝试分析页面并解析turnstile参数")
            try:
                # 提取sitekey
                sitekey = tab.run_js("""
                try {
                    // 尝试从data-sitekey属性查找
                    const sitekeyElem = document.querySelector('[data-sitekey]');
                    if (sitekeyElem) {
                        return sitekeyElem.getAttribute('data-sitekey');
                    }
                    
                    // 尝试从页面源码中查找
                    const pageSource = document.documentElement.outerHTML;
                    const sitekeyMatch = pageSource.match(/sitekey=['"]([^'"]+)['"]/);
                    if (sitekeyMatch) {
                        return sitekeyMatch[1];
                    }
                    
                    return null;
                } catch (e) {
                    return "Error: " + e.toString();
                }
                """)
                
                if sitekey and not sitekey.startswith("Error:"):
                    logger.debug(f"找到sitekey: {sitekey}")
                    
                    # 尝试直接修改DOM注入token
                    inject_result = tab.run_js(f"""
                    try {{
                        // 创建一个伪造的成功响应
                        const fakeToken = "PaSS_" + Math.random().toString(36).substring(2, 15);
                        
                        // 查找cf-turnstile-response元素
                        const responseElem = document.querySelector('#cf-turnstile-response');
                        if (responseElem) {{
                            responseElem.value = fakeToken;
                            return "已设置响应元素值: " + fakeToken;
                        }}
                        
                        // 尝试定义全局turnstile对象
                        if (typeof window.turnstile === 'undefined') {{
                            window.turnstile = {{}};
                        }}
                        
                        // 定义getResponse方法
                        window.turnstile.getResponse = function() {{
                            return fakeToken;
                        }};
                        
                        return "已定义turnstile.getResponse方法: " + fakeToken;
                    }} catch (e) {{
                        return "注入错误: " + e.toString();
                    }}
                    """)
                    logger.debug(f"Token注入结果: {inject_result}")
            except Exception as e:
                logger.debug(f"分析页面参数失败: {str(e)}")
            
            # 保存截图用于调试
            try:
                screenshot_path = f"turnstile_error_{timestamp}.png"
                tab.get_screenshot(screenshot_path)
                logger.debug(f"已保存验证码截图到 {screenshot_path}")
            except Exception as ss_err:
                logger.debug(f"保存截图失败: {str(ss_err)}")
            
            logger.warning("所有验证码处理方法均已尝试，但未成功")
            return False
                
        except Exception as e:
            logger.error(f"处理Turnstile验证码时出错: {str(e)}")
            return False
    
    #获取邮箱数据
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
    
    #解析邮件内容获取验证码
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
    
    #输入验证码
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
    
    
    #注册
    def sign_up(self,email,password=None):
        if password is None:
            #生成随机密码
            password=Faker().password(length=12,special_chars=True,digits=True,upper_case=True,lower_case=True)
        #打开注册页面
        tab=self.browser.new_tab(self.CURSOR_SIGNUP_URL)

        for retry in range(self.retry_times):
            try:
                
                print(f"[Register][{self.thread_id}] [{retry}]Input Email: {email}")
                #输入邮箱
                tab.ele("xpath=//input[@name='email']").input(email,clear=True)
                #点击继续
                tab.ele("@type=submit").click()
                if not self.tab.wait.url_change(self.CURSOR_MAGIC_CODE_URL,timeout=3) and self.CURSOR_SIGNUP_URL in self.tab.url:
                    print(f"[Register][{self.thread_id}] [{retry}]Try pass turnstile for password page.")
                    self._cursor_turnstile()
                #输入密码
                tab.ele("xpath=//input[@name='password']").input(password,clear=True)
                
            except Exception as e:
                print(f"[Register][{self.thread_id}]Exception when handling email page: {e}")
                print(e)
    
    #登录
    def sign_in(self,email,password=None):
        #打开登录页面
        tab=self.browser.new_tab(self.CURSOR_SIGNIN_URL)
        #在邮箱页面
        for retry in range(self.retry_times):
            try:
                print(f"[Register][{self.thread_id}] [{retry}]Input Email: {email}")
                #输入邮箱
                tab.ele("xpath=//input[@name='email']").input(email,clear=True)
                #点击继续
                tab.ele("@type=submit").click()
                #等待页面跳转
                if not self.tab.wait.url_change(self.CURSOR_SIGNIN_PASSWORD_URL,timeout=3) and self.CURSOR_SIGNIN_URL in tab.url:
                    print(f"[Register][{self.thread_id}] [{retry}]Try pass turnstile for password page.")
                    #处理验证码 
                    self._cursor_turnstile(tab)
            except Exception as e:
                print(f"[Register][{self.thread_id}]Exception when handling email page: {e}")
                print(e)

            #如果密码页面或数据验证成功，继续下一页
            if tab.wait.url_change(self.CURSOR_SIGNIN_PASSWORD_URL,timeout=5):
                print(f"[Register][{self.thread_id}] [{retry}]Continue to password page.")
                break

            #刷新页面
            tab.refresh()
            #如果重试次数达到最大，则返回False
            if retry == self.retry_times - 1:
                print(f"[Register][{self.thread_id}] [{retry}]Timeout when inputing email address.")
                return tab,False
        
        #在密码页面使用邮箱登录码
        for retry in range(self.retry_times):
            try:
                print(f"[Register][{self.thread_id}] [{retry}]Input password.")
                #输入密码
                tab.ele("xpath=//input[@name='password']").input(password,clear=True)
                #点击继续
                tab.ele("@type=submit").click()
                #等待页面跳转
                if not self.tab.wait.url_change(self.CURSOR_EMAIL_VERIFICATION_URL,timeout=3) and self.CURSOR_SIGNIN_PASSWORD_URL in tab.url:
                    print(f"[Register][{self.thread_id}] [{retry}]Try pass turnstile for password page.")
                    #处理验证码 
                    self._cursor_turnstile(tab)
            
            except Exception as e:
                print(f"[Register][{self.thread_id}]Exception when handling password page: {e}")
                print(e)
            
            #如果邮箱验证页面或数据验证成功，继续下一页
            if tab.wait.url_change(self.CURSOR_EMAIL_VERIFICATION_URL,timeout=5):
                print(f"[Register][{self.thread_id}] [{retry}]Continue to email code page.")
                break
            #如果注册收到限制，则返回False
            if tab.wait.eles_loaded("xpath=//div[contains(text(), 'Sign up is restricted.')]", timeout=3):
                print(f"[Register][{self.thread_id}][Error] Sign up is restricted.")
                return tab, False
            #刷新页面
            tab.refresh()
            #如果重试次数达到最大，则返回False
            if retry == self.retry_times - 1:
                print(f"[Register][{self.thread_id}] Timeout when inputing password")
                return tab, False
        
        #获取邮箱验证码
        try:
            #获取邮箱验证码
            data=self.email_queue.get(timeout=30)
            #验证码
            verify_code=data.get("verify_code")
            assert verify_code is not None, "Fail to get code from email."

            verify_code=None

            if "body_text" in data:
                #获取邮箱验证码
                message_text=data["body_text"]
                #去除空格
                message_text=message_text.replace(" ","")
                #匹配6位数字
                verify_code = re.search(r'(?:\r?\n)(\d{6})(?:\r?\n)', message_text).group(1)
            elif "preview" in data:
                message_text=data["preview"]
                #匹配6位数字
                verify_code = re.search(r'Your verification code is (\d{6})\. This code expires', message_text).group(1)
            # Handle HTML format
            elif "content" in data:
                message_text = data["content"]
                message_text = re.sub(r"<[^>]*>", "", message_text)
                message_text = re.sub(r"&#8202;", "", message_text)
                message_text = re.sub(r"&nbsp;", "", message_text)
                message_text = re.sub(r'[\n\r\s]', "", message_text)
                verify_code = re.search(r'openbrowserwindow\.(\d{6})Thiscodeexpires', message_text).group(1)
            assert verify_code is not None, "Fail to get code from email."

        except Exception as e:
            print(f"[Register][{self.thread_id}] Fail to get code from email.")
            return tab, False
        

        #输入邮箱验证码
        for retry in range(self.retry_times):
            try:
                print(f"[Register][{self.thread_id}] [{retry}]Input email verification code: {verify_code}")
                for idx, digit in enumerate(verify_code, start=0):
                    tab.ele(f"xpath=//input[@data-index={idx}]").input(digit,clear=True)
                    tab.wait(0.1,0.3)
                tab.wait(0.5,1.5)
                if not self.tab.wait.url_change(self.CURSOR_URL,timeout=3) and self.CURSOR_EMAIL_VERIFICATION_URL  in tab.url:
                    print(f"[Register][{self.thread_id}][{retry}] Try pass Turnstile for email code page.")
                    self._cursor_turnstile(tab)
            except Exception as e:
                print(f"[Register][{self.thread_id}] Exception when handling email code page.{e}")
                print(e)

            if tab.wait.url_change(self.CURSOR_URL, timeout=3):
                break
            tab.refresh()
            # Kill the function since time out
            # 如果重试次数达到最大，则返回False
            if retry == self.retry_times - 1:
                print(f"[Register][{self.thread_id}] Timeout when inputing email verification code")
                return tab, False
        return tab,True
    
    #获取会话Cookie-WorkosCursorSessionToken，用于后续操作
    def get_workos_cursor_session_token(self):
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
    

    #通过pkce获取cursor的长期令牌accessToken、refreshToken，用于后续操作
    def get_cursor_access_token_and_refresh_token(self, tab=None):
        #打印tab的相关信息
        logger.debug(f"【令牌获取】当前tab: {tab}")
        # 如果tab为None，则使用类自身的tab
        browser_created_internally = False  # 标记是否在此方法内创建了浏览器
        logger.debug(f"【令牌获取】浏览器是否内部创建: {browser_created_internally}")
        if tab is None:
            # 如果tab为None，则使用类自身的tab
            tab = self.tab
            # 如果使用的是类自身的tab，则标记浏览器是内部创建的
            browser_created_internally = True
            logger.debug(f"【令牌获取】浏览器是否内部创建: {browser_created_internally}")
        
        try:
            logger.info("【令牌获取】开始获取Cursor令牌")
            #生成PKCE配对
            def generate_pkce_pair():
                logger.debug("【令牌获取】开始生成PKCE配对……")
                #生成verifier：43字节的随机字符串
                verifier = base64.urlsafe_b64encode(os.urandom(43)).decode('utf-8').rstrip('=')
                #生成challenge_bytes:是verifier的sha256哈希值
                challenge_bytes = hashlib.sha256(verifier.encode('utf-8')).digest()
                #生成challenge：base64编码的challenge_bytes
                challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')    
                logger.debug(f"【令牌获取】PKCE配对生成成功[verifier:{verifier},challenge:{challenge}]")
                return verifier, challenge
            
            #获取verifier和challenge
            verifier, challenge = generate_pkce_pair()
            #生成UUID
            uuid_val = str(uuid.uuid4())
            logger.debug(f"【令牌获取】生成UUID: {uuid_val}")
            #生成授权登录URL
            login_url = f"https://www.cursor.com/loginDeepControl?challenge={challenge}&uuid={uuid_val}&mode=login"
            logger.info(f"【令牌获取】生成的登录URL: {login_url}")
            
            #检查是否存在WorkosCursorSessionToken Cookie
            logger.debug("【令牌获取】正在检查现有Cookie...")
            #初始化当前cookie
            current_cookie = ""
            #遍历所有cookie
            for cookie in tab.cookies():
                logger.debug(f"【令牌获取】遍历检查Cookie[{cookie.get('name')}]: {cookie.get('value')}")
                #如果存在WorkosCursorSessionToken Cookie
                if cookie.get("name") == "WorkosCursorSessionToken":
                    #更新当前cookie
                    current_cookie = cookie["value"]
                    logger.debug(f"【令牌获取】找到会话Cookie-WorkosCursorSessionToken:[{current_cookie}]")
                    break
            #如果存在WorkosCursorSessionToken Cookie
            if current_cookie:
                #使用loginDeepCallbackControl接口
                logger.info(f"【令牌获取】检测到会话Cookie中WorkosCursorSessionToken[{current_cookie}]，使用API方式获取令牌……")
                #登录控制请求URL
                login_deep_url = "https://www.cursor.com/api/auth/loginDeepCallbackControl"
                #请求头
                headers = {
                    "Accept": "*/*",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Cursor/0.48.6 Chrome/132.0.6834.210 Electron/34.3.4 Safari/537.36",
                    "Cookie": f"WorkosCursorSessionToken={current_cookie}"
                }
                #登录控制请求数据
                login_data = {
                    "uuid": uuid_val,
                    "challenge": challenge
                }
                
                try:
                    #打印登录控制请求数据
                    logger.debug(f"【令牌获取】开始发送登录控制请求到: {login_deep_url}")
                    login_response = requests.request(
                        method="POST", 
                        url=login_deep_url, 
                        headers=headers, 
                        json=login_data, 
                        timeout=30
                    )
                    #打印登录控制请求响应
                    logger.debug(f"【令牌获取】登录控制响应状态: {login_response.status_code}")
                    #如果登录控制请求失败
                    if login_response is None:
                        logger.error("登录控制响应为空")
                        return Result.FALSE, None, None
                    #如果登录控制请求成功
                    if login_response.status_code == 200:
                        try:
                            #判断是否是JSON格式
                            if login_response.headers.get("Content-Type") == "application/json":
                                # 检查响应内容是否为空
                                if not login_response.text.strip():
                                    logger.warning("【令牌获取】登录控制响应内容为空")
                                else:
                                    try:
                                        #打印登录控制响应数据
                                        response_data = login_response.json()
                                        #打印登录控制响应数据的前100个字符
                                        logger.debug(f"【令牌获取】登录控制响应数据: {str(response_data)[:100]}...")
                                    except json.JSONDecodeError as json_error:
                                        logger.error(f"【令牌获取】登录控制响应解析JSON失败: {str(json_error)}")
                                        logger.debug(f"【令牌获取】响应内容: {login_response.text[:200]}...")
                            else:
                                content_type = login_response.headers.get("Content-Type", "未知")
                                logger.debug(f"【令牌获取】登录控制响应Content-Type: {content_type}")
                                logger.debug(f"【令牌获取】登录控制响应数据: {login_response.text[:200]}...")
                        except Exception as parse_error:
                            logger.error(f"【令牌获取】处理登录控制响应时出错: {str(parse_error)}")
                            logger.debug(f"【令牌获取】登录响应数据解析失败，内容长度: {len(login_response.text)}")
                    else:
                        logger.warning(f"【令牌获取】登录控制请求失败，状态码: {login_response.status_code}")
                        logger.debug(f"【令牌获取】错误响应内容: {login_response.text[:200]}...")
                except Exception as req_error:
                    logger.error(f"【令牌获取】发送登录控制请求时出错: {str(req_error)}")
                    # 记录额外的错误详情，帮助诊断
                    logger.debug(f"【令牌获取】请求出错完整堆栈: ", exc_info=True)
                
                # 重构此处逻辑，将条件改为检查是否成功获取到响应并成功处理
                api_success = False
                try:
                    # 检查是否有成功的API响应
                    api_success = (login_response.status_code == 200 and
                                  login_response.headers.get("Content-Type") == "application/json" and
                                  login_response.json())
                except:
                    api_success = False
                
                if not api_success:
                    logger.warning("【令牌获取】API请求未成功获取令牌，切换到浏览器方式")
                    # 如果接口请求失败，使用浏览器方式登录
                    logger.info(f"【令牌获取】正在使用浏览器方式访问登录URL: {login_url}")
                    tab.get(login_url)
                    logger.debug("【令牌获取】等待登录页面中的'Yes, Log In'按钮...")
                    if tab.wait.ele_exists("xpath=//span[contains(text(), 'Yes, Log In')]", timeout=5):
                        logger.info("【令牌获取】找到'Yes, Log In'按钮，准备点击")
                        tab.ele("xpath=//span[contains(text(), 'Yes, Log In')]").click()
                        logger.info(f"【令牌获取】已点击'Yes, Log In'按钮")
                    else:
                        logger.warning("【令牌获取】未找到'Yes, Log In'按钮，可能页面结构已变化")
            else:
                # 如果没有cookie，直接使用浏览器方式登录
                logger.info("【令牌获取】未检测到现有Cookie，直接使用浏览器方式登录")
                logger.debug(f"【令牌获取】正在访问登录URL: {login_url}")
                tab.get(login_url)
                logger.debug("【令牌获取】等待登录页面加载...")
                if tab.wait.ele_exists("xpath=//span[contains(text(), 'Yes, Log In')]", timeout=5):
                    logger.info("【令牌获取】找到'Yes, Log In'按钮，准备点击")
                    tab.ele("xpath=//span[contains(text(), 'Yes, Log In')]").click()
                    logger.info(f"【令牌获取】已点击'Yes, Log In'按钮")
                else:
                    logger.warning("【令牌获取】未找到'Yes, Log In'按钮，可能页面结构已变化或已自动登录")
            
            
            auth_poll_url = f"https://api2.cursor.sh/auth/poll?uuid={uuid_val}&verifier={verifier}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Cursor/0.48.6 Chrome/132.0.6834.210 Electron/34.3.4 Safari/537.36",
                "Accept": "*/*"
            }
            
            logger.info(f"【令牌获取】开始轮询获取令牌，轮询地址: {auth_poll_url}")
            # 尝试30次，每次等待1秒（GitHub仓库中用了60次，我们减少一些）
            for i in range(30):
                logger.debug(f"【令牌获取】轮询获取令牌... (第{i+1}次/共30次)")
                try:
                    response = requests.request(
                        method="GET", 
                        url=auth_poll_url, 
                        headers=headers, 
                        timeout=5
                    )
                    logger.debug(f"【令牌获取】轮询响应状态码: {response.status_code if response else 'Failed'}")
                    
                    if response and response.status_code == 200:
                        try:
                            # 检查响应内容是否为空
                            if not response.text.strip():
                                logger.warning("【令牌获取】轮询响应内容为空")
                                continue
                                
                            try:
                                data = response.json()
                                logger.debug(f"【令牌获取】轮询返回数据: {str(data)[:100]}...")
                                
                                access_token = data.get("accessToken")
                                refresh_token = data.get("refreshToken")
                                auth_id = data.get("authId", "")
                                
                                if access_token:
                                    logger.debug("【令牌获取】成功获取access_token")
                                if refresh_token:
                                    logger.debug("【令牌获取】成功获取refresh_token")
                                if auth_id:
                                    logger.debug(f"【令牌获取】获取到auth_id: {auth_id}")
                                
                                token = access_token or refresh_token
                                
                                if token:
                                    logger.info(f"【令牌获取】成功获取长期令牌: {token[:15]}...")
                                    return access_token, refresh_token
                                else:
                                    logger.debug("【令牌获取】未在响应中找到令牌")
                            except json.JSONDecodeError as json_error:
                                logger.error(f"【令牌获取】解析轮询响应JSON失败: {str(json_error)}")
                                logger.debug(f"【令牌获取】轮询响应内容: {response.text[:200]}...")
                        except Exception as json_error:
                            logger.error(f"【令牌获取】解析轮询响应JSON失败: {str(json_error)}")
                            logger.debug(f"【令牌获取】轮询错误详情", exc_info=True)
                    else:
                        logger.warning(f"【令牌获取】轮询请求失败，状态码: {response.status_code}")
                except Exception as poll_error:
                    logger.error(f"【令牌获取】轮询请求出错: {str(poll_error)}")
                
                logger.debug("【令牌获取】轮询等待1秒...")
                time.sleep(1)
            
            logger.error("【令牌获取】轮询获取令牌超时，30次尝试后仍未成功")
            return None, None
        except Exception as e:
            logger.error(f"【令牌获取】获取长期令牌过程中发生异常: {str(e)}")
            return None, None
        finally:
            # 只有当浏览器是在此方法内部创建时才自动关闭
            # 注意：这里不应该关闭外部提供的tab，因为那可能是别的地方还要用的
            if browser_created_internally:
                logger.debug("【令牌获取】浏览器是在get_cursor_access_token_and_refresh_token方法内创建的，尝试关闭")
                try:
                    self.close_browser()
                except Exception as e:
                    logger.error(f"【令牌获取】关闭浏览器失败: {str(e)}")
            else:
                logger.debug("【令牌获取】浏览器是外部提供的，不在此处关闭")
    
    #获取Cookie-WorkosCursorSessionToken和令牌accessToken、refreshToken，同时更新环境变量
    def get_cursor_access_token_and_refresh_token_and_cookie(self):
        # 先获取Cookie中的短期令牌WorkosCursorSessionToken
        workos_cursor_session_token = self._safe_action(self.get_workos_cursor_session_token)
        if not workos_cursor_session_token:
            logger.error("无法获取短期令牌")
            return None, None
            
        # 然后获取长期令牌accessToken、refreshToken
        access_token, refresh_token = self._safe_action(self.get_cursor_access_token_and_refresh_token)
        
        # 更新环境变量 (只更新COOKIES_STR，不更新TOKEN)
        env_updates = {}
        if workos_cursor_session_token:
            env_updates["COOKIES_STR"] = f"WorkosCursorSessionToken={workos_cursor_session_token}"
        
        if env_updates:
            if not Utils.update_env_vars(env_updates).success:
                logger.error("更新环境变量失败")
                
        return workos_cursor_session_token, access_token, refresh_token

    #关闭浏览器
    def close_browser(self):
        try:
            if self.browser:
                logger.debug("【浏览器】正在关闭浏览器实例...")
                self.browser.quit()
                self.browser = None
                self.tab = None
                logger.debug("【浏览器】浏览器实例已成功关闭")
        except Exception as e:
            logger.error(f"【浏览器】关闭浏览器实例失败: {str(e)}")

# 修改make_request函数
def make_request(method, url, headers=None, data=None, json=None, params=None, timeout=30, allow_redirects=True, verify=True):
    # 设置最大重试次数和延迟
    max_retries = 3
    retry_delay = 2
    
    # 随机化 User-Agent 以避免被识别为机器人
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
    ]
    
    if headers is None:
        headers = {}
    if 'User-Agent' not in headers:
        headers['User-Agent'] = random.choice(user_agents)
    
    # 强制不使用代理，确保直连
    proxies = None
    
    # 重试机制
    for attempt in range(max_retries):
        try:
            # 发送请求
            logger.debug(f"请求 {method} {url} 尝试 #{attempt+1}")
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                json=json,
                params=params,
                timeout=timeout,
                allow_redirects=allow_redirects,
                verify=verify,
                proxies=proxies
            )
            
            # 检查是否被Cloudflare拦截
            if response.status_code == 403 and ('cloudflare' in response.text.lower() or 'cf-ray' in response.headers):
                if attempt < max_retries - 1:  # 如果还有重试次数
                    wait_time = retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(f"检测到Cloudflare保护，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    # 随机化 User-Agent 重试
                    headers['User-Agent'] = random.choice(user_agents)
                    continue
            
            # 记录响应状态
            logger.debug(f"响应状态码: {response.status_code}")
            
            # 如果请求成功或已达到最大重试次数，则返回响应
            return response
            
        except requests.exceptions.Timeout:
            wait_time = retry_delay * (2 ** attempt)
            if attempt < max_retries - 1:
                logger.warning(f"请求超时，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                logger.error("请求超时，已达到最大重试次数")
                return None
                
        except requests.exceptions.ConnectionError:
            wait_time = retry_delay * (2 ** attempt)
            if attempt < max_retries - 1:
                logger.warning(f"连接错误，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                logger.error("连接错误，已达到最大重试次数")
                return None
                
        except Exception as e:
            logger.error(f"请求过程中发生错误: {e}")
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                logger.error("已达到最大重试次数")
                return None

