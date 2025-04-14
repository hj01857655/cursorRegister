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
from dotenv import load_dotenv
from loguru import logger
from cursor import Cursor
from utils import MoemailManager
from utils import Utils
#生成随机字符串
from faker import Faker

#cursor注册类
class CursorRegistration:
    #主页
    CURSOR_URL = "https://www.cursor.com/"
    #登录页面
    CURSOR_SIGNIN_URL = "https://authenticator.cursor.sh"
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
            required_vars = ['EMAIL', 'PASSWORD', 'DOMAIN']
            if not all(os.getenv(var) for var in required_vars):
                raise ValueError("请确保.env文件中配置了 EMAIL、PASSWORD 和 DOMAIN")
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.domain = os.getenv('DOMAIN')
        self.first_name = Utils.generate_random_string(4)
        self.last_name = Utils.generate_random_string(4)

        #
        self.email_queue=queue.Queue()
        #获取当前线程ID
        self.thread_id = threading.current_thread().ident
        #重试次数
        self.retry_times = 5
        #初始化浏览器，通过browser参数传入
        self.browser = self.tab = self.moe = None
        #是否全自动
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
        # 如果已有浏览器实例，返回
        if self.browser:
            self.tab = self.browser.latest_tab
            self.tab.get(self.CURSOR_SIGNUP_URL)
            logger.debug("使用已有浏览器访问注册页面")
            return
        #初始化浏览器
        co = ChromiumOptions()
        #设置为隐身模式
        co.set_argument("--incognito")
        #自动端口
        co.auto_port()
        #新环境
        co.new_env()
        #是否无头
        if self.headless:
            #设置无头
            co.headless()
        else:   
            #添加扩展
            turnstile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "turnstilePatch"))
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
        #访问注册页面
        self.tab.get(self.CURSOR_SIGNUP_URL)
        logger.debug(f"访问注册页面: {self.CURSOR_SIGNUP_URL}")

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
    
    #处理页面跳转
    def _handle_page_transition(self, current_url, target_url, action_description, max_retries=5):
        for retry in range(max_retries):
            try:
                if self.tab.wait.url_change(current_url, timeout=5):
                    logger.debug(f"抵达{action_description}")
                    wait_time = random.uniform(2, 5)
                    logger.debug(f"随机等待 {wait_time:.2f} 秒")
                    time.sleep(wait_time)

                if not self.tab.wait.url_change(target_url, timeout=3) and current_url in self.tab.url:
                    self._cursor_turnstile( )

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
    
    #半自动注册
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
    
    #半自动注册
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
    
    #全自动注册
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
    #获取使用信息
    def get_usage(self,user_id):
        tab=self.browser.new_tab(f"{self.CURSOR_USAGE_URL}?user={user_id}")
        return tab.json
    
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
    def _cursor_turnstile(self,tab):
        max_retries = 5
        for retry in range(max_retries):
            try:
                turnstile_element = tab.ele('@id=cf-turnstile', timeout=10)
                print(turnstile_element)
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
                    self._cursor_turnstile(self.tab)
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
    
    #获取短期token，用于后续操作
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
    

    #通过pkce获取cursor的长期token，用于后续操作
    def get_cursor_cookie(self, tab):
        def _generate_pkce_pair():
            code_verifier = secrets.token_urlsafe(43)
            code_challenge_digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
            code_challenge = base64.urlsafe_b64encode(code_challenge_digest).decode('utf-8').rstrip('=')    
            return code_verifier, code_challenge
        try:
            verifier, challenge = _generate_pkce_pair()
            id = uuid.uuid4()
            client_login_url = f"https://www.cursor.com/cn/loginDeepControl?challenge={challenge}&uuid={id}&mode=login"
            tab.get(client_login_url)
            tab.ele("xpath=//span[contains(text(), 'Yes, Log In')]").click()

            auth_pooll_url = f"https://api2.cursor.sh/auth/poll?uuid={id}&verifier={verifier}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Cursor/0.48.6 Chrome/132.0.6834.210 Electron/34.3.4 Safari/537.36",
                "Accept": "*/*"
            }
            response = requests.get(auth_pooll_url, headers = headers, timeout=5)
            data = response.json()
            accessToken = data.get("accessToken", None)
            authId = data.get("authId", "")
            if len(authId.split("|")) > 1:
                userId = authId.split("|")[1]
                token = f"{userId}%3A%3A{accessToken}"
            else:
                token = accessToken
        except:
            print(f"[Register][{self.thread_id}] Fail to get cookie.")
            return None

        if token is not None:
            print(f"[Register][{self.thread_id}] Get Account Cookie Successfully.")
        else:
            print(f"[Register][{self.thread_id}] Get Account Cookie Failed.")
        return token#

