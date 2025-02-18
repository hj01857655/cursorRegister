from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

import utils
from utils import MoemailManager
from registerAc import CursorRegistration
import random
import time
import os



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
        self.dev_websites = [
            "https://github.com",
            "https://stackoverflow.com",
            "https://dev.to",
            "https://medium.com/tag/programming",
            "https://www.freecodecamp.org",
            "https://www.codecademy.com",
            "https://www.geeksforgeeks.org",
            "https://www.w3schools.com",
            "https://leetcode.com",
            "https://www.hackerrank.com",
            "https://www.codewars.com",
            "https://www.coursera.org/browse/computer-science",
            "https://www.udemy.com/courses/development",
            "https://www.pluralsight.com",
            "https://replit.com",
            "https://codesandbox.io",
            "https://codepen.io",
            "https://www.digitalocean.com/community/tutorials",
            "https://www.reddit.com/r/programming",
            "https://news.ycombinator.com"
        ]

    def nurture_browser(self, min_visits=10, max_visits=20):
     
        logger.info("开始养号过程...")
        num_visits = random.randint(min_visits, max_visits)
        visited_sites = random.sample(self.dev_websites, num_visits)
        
        for site in visited_sites:
            try:
                logger.info(f"访问网站: {site}")
                self.tab.get(site)
                
            
                wait_time = random.uniform(5, 15)
                logger.debug(f"在页面停留 {wait_time:.2f} 秒")
                time.sleep(wait_time)
                
                
                scroll_times = random.randint(2, 5)
                for _ in range(scroll_times):
                    scroll_amount = random.randint(300, 1000)
                    self.tab.run_js(f"window.scrollBy(0, {scroll_amount})")
                    time.sleep(random.uniform(1, 3))
                
                logger.info(f"完成访问: {site}")
            except Exception as e:
                logger.error(f"访问 {site} 时出错: {str(e)}")
                continue
        
        logger.info(f"养号完成，共访问了 {len(visited_sites)} 个网站")

    def admin_auto_register(self, **kwargs):
       
        try:
            email_password_result = utils.CursorManager.generate_cursor_account()
            if not isinstance(email_password_result, tuple):
                raise Exception("生成账号信息失败")
            self.email, self.password = email_password_result
            logger.debug(f"已生成随机邮箱: {self.email}")
            logger.debug(f"已生成随机密码: {self.password}")
            self.moe = MoemailManager()
            email_info = self.moe.create_email(email=self.email)
            logger.debug(f"已创建邮箱 ： {email_info.data.get('email')}")
            self.admin = True

        
            self._safe_action(self.init_browser)
            
         
            self._safe_action(self.nurture_browser)
            
         
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

            return self._safe_action(self.get_cursor_token)
        except Exception as e:
            logger.error(f"注册过程发生错误: {str(e)}")
            raise
        finally:
            if self.browser:
                self.browser.quit()

if __name__ == "__main__":
    load_dotenv()
    registration = GithubActionRegistration()
    token = registration.admin_auto_register()
    if token:
        env_updates = {
            "COOKIES_STR": f"WorkosCursorSessionToken={token}",
            "EMAIL": registration.email,
            "PASSWORD": registration.password
        }
        registration.utils.update_env_vars(env_updates)
        try:
            with open('env_variables.csv', 'w', encoding='utf-8', newline='') as f:
                f.write("variable,value\n")
                for key, value in env_updates.items():
                    f.write(f"{key},{value}\n")
            logger.info("环境变量已保存到 env_variables.csv 文件中")
        except Exception as e:
            logger.error(f"保存环境变量到文件时出错: {str(e)}") 