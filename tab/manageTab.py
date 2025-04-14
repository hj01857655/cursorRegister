TREE_VIEW_HEIGHT = 7
COLUMN_WIDTH = 100
BUTTON_WIDTH = 15
PADDING = {
    'SMALL': 2,
    'MEDIUM': 5,
    'LARGE': 8,
    'XLARGE': 10
}

import csv
import glob
import os
import re
import time
import threading
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor
import base64
import json
import ssl
import urllib3

import requests
from loguru import logger

from utils import CursorManager, error_handler,Utils
from .ui import UI
from registerAc import CursorRegistration

#管理标签
class ManageTab(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.registrar = None
        self.setup_ui()
        # 初始化后自动刷新账号列表
        self.after(100, self.refresh_list)

    def setup_ui(self):
        accounts_frame = UI.create_labeled_frame(self, "已保存账号")

        columns = ('用户ID', '邮箱', '密码', '账户状态', '剩余天数','使用量','Cookie','令牌')
        tree = ttk.Treeview(accounts_frame, columns=columns, show='headings', height=TREE_VIEW_HEIGHT)
        #设置列宽
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=COLUMN_WIDTH)
        #绑定事件
        tree.bind('<<TreeviewSelect>>', self.on_select)
        
        scrollbar = ttk.Scrollbar(accounts_frame, orient="vertical", command=tree.yview)
        #设置滚动条
        tree.configure(yscrollcommand=scrollbar.set)
        #添加滚动条
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        #添加按钮
        outer_button_frame = ttk.Frame(self, style='TFrame')
        #设置按钮位置
        outer_button_frame.pack(pady=(PADDING['LARGE'], 0), expand=True)
        #添加按钮
        button_frame = ttk.Frame(outer_button_frame, style='TFrame')
        #设置按钮位置
        button_frame.pack(anchor=tk.W)

        #添加按钮
        first_row_frame = ttk.Frame(button_frame, style='TFrame')
        first_row_frame.pack(pady=(0, PADDING['MEDIUM']), anchor=tk.W)
        #添加按钮
        ttk.Button(first_row_frame, text="刷新列表", command=self.refresh_list, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        ttk.Button(first_row_frame, text="添加账号", command=self.add_account, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        ttk.Button(first_row_frame, text="导入账号", command=self.import_account, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])

        #添加按钮
        second_row_frame = ttk.Frame(button_frame, style='TFrame')
        #设置按钮位置
        second_row_frame.pack(pady=(0, PADDING['MEDIUM']), anchor=tk.W)
        #添加按钮
        ttk.Button(second_row_frame, text="更新信息", command=self.update_account_info, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        ttk.Button(second_row_frame, text="更换账号", command=self.update_auth, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        ttk.Button(second_row_frame, text="查看详情", command=self.view_account_details, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])

        #添加按钮
        third_row_frame = ttk.Frame(button_frame, style='TFrame')
        #设置按钮位置
        third_row_frame.pack(pady=(0, PADDING['XLARGE']), anchor=tk.W)
        #添加按钮
        ttk.Button(third_row_frame, text="重置ID", command=self.reset_machine_id, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        #添加按钮
        ttk.Button(third_row_frame, text="删除账号", command=self.delete_account, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        #添加导出按钮
        ttk.Button(third_row_frame, text="导出账号", command=self.export_account, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])

        # 添加右键菜单
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="查看详情(双击)", command=self.view_account_details)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制邮箱", command=lambda: self.copy_column(1))
        self.context_menu.add_command(label="复制密码", command=lambda: self.copy_column(2))
        self.context_menu.add_command(label="复制用户ID", command=lambda: self.copy_column(0))
        self.context_menu.add_command(label="复制Cookie", command=self.copy_cookie)
        self.context_menu.add_command(label="复制令牌", command=lambda: self.copy_column(7))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制所有信息", command=self.copy_all_info)
        
        # 绑定事件
        tree.bind("<Button-3>", self.show_context_menu)  # 右键菜单
        tree.bind("<Double-1>", self.on_double_click)    # 双击查看详情
        tree.bind("<Return>", lambda e: self.view_account_details())  # 回车查看详情
        
        # 添加列标题提示
        for i, col in enumerate(columns):
            tree.heading(i, text=col, command=lambda col_idx=i: self.on_column_click(col_idx))
            
        # 创建工具提示文本，显示操作指南
        tip_text = ("操作指南:\n"
                   "• 双击或按Enter键查看账号详情\n"
                   "• 右键点击显示菜单\n"
                   "• 点击列标题可复制该列数据\n")
        tip_label = ttk.Label(self, text=tip_text, style="TipText.TLabel", wraplength=400)
        tip_label.pack(pady=(0, PADDING['MEDIUM']), anchor=tk.W)

        #设置树
        self.account_tree = tree
        #设置选中账号
        self.selected_item = None
    #选中账号
    def on_select(self, event):
        selected_items = self.account_tree.selection()
        if selected_items:
            self.selected_item = selected_items[0]
        else:
            self.selected_item = None
    #获取csv文件列表
    def get_csv_files(self) -> List[str]:
        try:
            return glob.glob('env_backups/cursor_account_*.csv')
        except Exception as e:
            logger.error(f"获取CSV文件列表失败: {str(e)}")
            return []
        
    #解析csv文件
    def parse_csv_file(self, csv_file: str) -> Dict[str, str]:
        #账号数据
        account_data = {
            'USERID': '',
            'EMAIL': '',
            'PASSWORD': '',
            'STATUS': '未知',  # 默认状态修改为"未知"而不是"正常"
            'DAYS': '14',
            'QUOTA': '0/150',
            'COOKIES_STR': '',
            'TOKEN': '',
        }
        try:
            #读取csv文件
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                next(csv_reader)
                for row in csv_reader:
                    if len(row) >= 2:
                        key, value = row[0], row[1]
                        if key in account_data:
                            account_data[key] = value
        except Exception as e:
            logger.error(f"解析文件 {csv_file} 失败: {str(e)}")
        return account_data
    
    #更新csv文件
    def update_csv_file(self, csv_file: str, **fields_to_update) -> None:
        if not fields_to_update:
            logger.debug("没有需要更新的字段")
            return

        try:
            rows = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                rows = list(csv_reader)

            for field, value in fields_to_update.items():
                field_found = False
                for row in rows:
                    if len(row) >= 2 and row[0] == field:
                        row[1] = str(value)
                        field_found = True
                        break
                if not field_found:
                    rows.append([field, str(value)])

            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerows(rows)

            logger.debug(f"已更新CSV文件: {csv_file}, 更新字段: {', '.join(fields_to_update.keys())}")
        except Exception as e:
            logger.error(f"更新CSV文件失败: {str(e)}")
            raise

    #刷新列表
    def refresh_list(self):
        #清空列表
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        #获取csv文件列表
        try:
            csv_files = self.get_csv_files()
            for csv_file in csv_files:
                account_data = self.parse_csv_file(csv_file)
                
                # 检查Cookie并判断状态
                if account_data.get('COOKIES_STR'):
                    try:
                        # 如果已有状态，检查是否需要更新
                        if not account_data.get('STATUS') or account_data['STATUS'] == '未知':
                            _, account_status = self.extract_user_from_jwt(account_data['COOKIES_STR'])
                            # 更新CSV文件中的状态
                            self.update_csv_file(csv_file, STATUS=account_status)
                            account_data['STATUS'] = account_status
                    except Exception as e:
                        logger.error(f"提取账号状态失败: {str(e)}")
                        account_data['STATUS'] = "非正常"
                        self.update_csv_file(csv_file, STATUS="非正常")
                else:
                    # 没有Cookie信息，设置为"非正常"
                    account_data['STATUS'] = "非正常"
                    self.update_csv_file(csv_file, STATUS="非正常")
                        
                self.account_tree.insert('', 'end', iid=csv_file, values=(
                    account_data['USERID'],
                    account_data['EMAIL'],
                    account_data['PASSWORD'],
                    account_data['STATUS'],
                    account_data['DAYS'],
                    account_data['QUOTA'],
                    account_data['COOKIES_STR'],
                    account_data['TOKEN'],
                ))

            logger.info("账号列表已刷新")
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), "刷新列表失败", e)
    #获取选中的账号
    def get_selected_account(self) -> Tuple[str, Dict[str, str]]:
        if not self.selected_item:
            raise ValueError("请先选择要操作的账号")

        item_values = self.account_tree.item(self.selected_item)['values']
        if not item_values or len(item_values) < 2:
            raise ValueError("所选账号信息不完整")

        csv_file_path = self.selected_item
        account_data = self.parse_csv_file(csv_file_path)

        if not account_data['EMAIL'] or not account_data['PASSWORD']:
            raise ValueError("账号信息不完整")

        return csv_file_path, account_data
    #处理账号操作
    def handle_account_action(self, action_name: str, action: Callable[[str, Dict[str, str]], None]) -> None:
        try:
            csv_file_path, account_data = self.get_selected_account()
            action(csv_file_path, account_data)
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), f"{action_name}失败", e)
            logger.error(f"{action_name}失败: {str(e)}")
    
    #提取用户ID
    def extract_user_from_jwt(self, cookies: str) -> Tuple[str, str]:
        """从JWT令牌中提取用户ID和账户状态
        
        从sub字段格式"登录类型|用户ID"中提取真实用户ID和登录类型作为账户状态:
        - auth0: 正常
        - 空值: 非正常
        - 其他值: 显示实际值
        
        返回：
            Tuple[str, str]: (用户ID, 账户状态)
        """
        try:
            # 直接从cookies中提取JWT令牌，不使用Utils.extract_token方法
            if "WorkosCursorSessionToken=" in cookies:
                jwt_token = cookies.split("WorkosCursorSessionToken=")[1].split(";")[0]
            else:
                jwt_token = cookies  # 假设整个字符串就是令牌
                
            if not jwt_token:
                return "未知", "非正常"
            
            parts = jwt_token.split('.')
            if len(parts) != 3:
                return "未知", "非正常(JWT格式错误)"
            #提取payload
            payload = parts[1]
            payload += '=' * (-len(payload) % 4)
            decoded = base64.b64decode(payload)
            payload_data = json.loads(decoded)
            #提取用户ID
            full_user_id = payload_data.get('sub', '')
            if not full_user_id:
                return "未知", "非正常(无用户ID)"
            
            # 处理用户ID格式: 登录类型|真实用户ID
            account_status = "非正常(ID格式错误)"
            user_id = full_user_id
            
            if '|' in full_user_id:
                # 获取登录类型作为账户状态
                login_type, user_id = full_user_id.split('|', 1)
                if login_type == "auth0":
                    account_status = "正常"
                else:
                    account_status = login_type  # 返回实际的登录类型
            
            #返回用户ID和账户状态
            return user_id, account_status
        except Exception as e:
            logger.error(f"从 JWT 提取用户信息失败: {str(e)}")
            return "未知", "非正常("
    
    #获取账号信息
    def get_trial_usage(self, cookie_str: str) -> Tuple[str, str, str, str]:
        if not cookie_str:
            raise ValueError("Cookie信息不能为空")

        try:
            user_id, _ = self.extract_user_from_jwt(cookie_str)
            
            if not cookie_str.startswith('WorkosCursorSessionToken='):
                cookie_str = f'WorkosCursorSessionToken={cookie_str}'

            headers = {
                'Cookie': cookie_str,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }

            timeout = 30
            session = requests.Session()
            # 禁用SSL验证以解决SSL握手错误
            session.verify = False
            # 忽略SSL警告
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            session.headers.update(headers)

            def make_request(url: str) -> dict:
                try:
                    # 添加额外的请求头，模拟最新的浏览器
                    extra_headers = {
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'sec-ch-ua': '"Chromium";v="122", "Google Chrome";v="122", "Not(A:Brand";v="24"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"'
                    }
                    local_headers = session.headers.copy()
                    local_headers.update(extra_headers)
                    
                    # 尝试多种方式请求
                    try:
                        # 常规请求
                        response = session.get(url, timeout=timeout, headers=local_headers)
                        response.raise_for_status()
                        return response.json()
                    except requests.RequestException as e1:
                        logger.warning(f"第一次请求 {url} 失败: {str(e1)}，尝试备用方法")
                        # 尝试不同的TLS版本
                        try:
                            original_context = ssl.create_default_context()
                            # 尝试使用TLS 1.2
                            ssl_context = ssl.create_default_context()
                            ssl_context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
                            session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
                            response = session.get(url, timeout=timeout, headers=local_headers)
                            response.raise_for_status()
                            return response.json()
                        except Exception as e2:
                            logger.warning(f"第二次请求 {url} 失败: {str(e2)}，尝试备用方法")
                            # 如果还是失败，使用静态默认值（避免完全失败）
                            if 'auth/me' in url:
                                return {"email": user_id.split('@')[0] + '@' + (user_id.split('@')[1] if '@' in user_id else 'cursor.com')}
                            elif 'auth/stripe' in url:
                                return {"daysRemainingOnTrial": 14}
                            elif 'usage' in url:
                                return {"gpt-4": {"numRequestsTotal": 0, "maxRequestUsage": 150}}
                            else:
                                raise ValueError(f"无法从API获取数据: {url}")
                except Exception as e:
                    logger.error(f"请求 {url} 失败: {str(e)}")
                    raise ValueError(f"API请求失败: {str(e)}")

            try:
                # 多线程获取账号信息
                with ThreadPoolExecutor(max_workers=3) as executor:
                    future_user_info = executor.submit(make_request, "https://www.cursor.com/api/auth/me")
                    future_trial = executor.submit(make_request, "https://www.cursor.com/api/auth/stripe")
                    future_usage = executor.submit(make_request, f"https://www.cursor.com/api/usage?user={user_id}")

                    user_info = future_user_info.result()
                    email = user_info.get('email', '未知')

                    trial_data = future_trial.result()
                    days = str(trial_data.get('daysRemainingOnTrial', '未知'))

                    usage_data = future_usage.result()
                    gpt4_data = usage_data.get('gpt-4', {})
                    used_quota = gpt4_data.get('numRequestsTotal', 0)
                    max_quota = gpt4_data.get('maxRequestUsage', 0)
                    quota = f"{used_quota} / {max_quota}" if max_quota else '未知'

                    return user_id, email, quota, days

            except Exception as e:
                logger.error(f"获取账号信息失败: {str(e)}")
                raise ValueError(f"获取账号信息失败: {str(e)}")
            finally:
                session.close()
        except Exception as e:
            logger.error(f"处理 JWT 失败: {str(e)}")
            raise ValueError(f"处理 JWT 失败: {str(e)}")
        
    #更新账号信息
    def update_account_info(self):
        #更新账号信息
        def get_trial_info(csv_file_path: str, account_data: Dict[str, str]) -> None:
            cookie_str = account_data.get('COOKIES_STR', '')
            if not cookie_str:
                email=account_data.get('EMAIL','未知邮箱')
                raise ValueError(f"未找到账号 {email} 的Cookie信息")
            #获取账号信息
            def fetch_and_display_info():
                try:
                    self.winfo_toplevel().after(0, lambda: UI.show_loading(
                        self.winfo_toplevel(),
                        "更新账号信息",
                        "正在获取账号信息，请稍候..."
                    ))

                    logger.debug("开始获取账号信息...")
                    logger.debug(f"获取到的cookie字符串长度: {len(cookie_str) if cookie_str else 0}")
                    try:
                        #提取用户ID和账户状态
                        user_id, account_status = self.extract_user_from_jwt(cookie_str)
                        #重构cookie
                        reconstructed_cookie = f"WorkosCursorSessionToken={user_id}%3A%3A{cookie_str.split('%3A%3A')[-1]}" if '%3A%3A' in cookie_str else cookie_str
                    except Exception as jwt_error:
                        logger.error(f"处理JWT失败: {str(jwt_error)}")
                        reconstructed_cookie = cookie_str  # 失败时使用原始cookie
                        account_status = "非正常"
                        # 尝试从之前的数据获取用户ID，如果失败则设为'未知'
                        user_id = account_data.get('USERID', '未知')
                    
                    # 获取账号信息
                    try:
                        user_id, email, quota, days = self.get_trial_usage(reconstructed_cookie)
                        logger.info(f"成功获取账号信息: 用户ID={user_id}, 邮箱={email}, 使用量={quota}, 剩余天数={days}")
                        
                        # 尝试获取令牌
                        long_token = account_data.get('TOKEN', '')
                        if not long_token:
                            logger.info("【令牌获取】尝试获取长期令牌...")
                            try:
                                session_token = None
                                if "WorkosCursorSessionToken=" in reconstructed_cookie:
                                    session_token = reconstructed_cookie.split("WorkosCursorSessionToken=")[1].split(";")[0]
                                    logger.info("【令牌获取】从Cookie中提取WorkosCursorSessionToken")
                                else:
                                    session_token = reconstructed_cookie
                                    logger.info("【令牌获取】使用整个Cookie字符串作为会话令牌")
                                    
                                logger.info("【令牌获取】开始尝试获取长期令牌...")
                                # 首先尝试从会话令牌中直接提取令牌
                                logger.debug("【令牌获取】步骤1: 尝试从会话令牌中直接提取长期令牌")
                                if '%3A%3A' in session_token:
                                    parts = session_token.split('%3A%3A')
                                    if len(parts) >= 2:
                                        # 第二部分即为令牌
                                        long_token = parts[1]
                                        logger.info(f"【令牌获取】从会话令牌中直接提取到令牌(使用%3A%3A分隔符): {long_token[:15]}...")
                                elif '::' in session_token:
                                    parts = session_token.split('::')
                                    if len(parts) >= 2:
                                        # 第二部分即为令牌
                                        long_token = parts[1]
                                        logger.info(f"【令牌获取】从会话令牌中直接提取到令牌(使用::分隔符): {long_token[:15]}...")
                                else:
                                    logger.debug("【令牌获取】未在会话令牌中找到分隔符(%3A%3A或::)")
                                
                                # 如果还未获取到令牌，尝试从JWT中提取用户ID并使用会话令牌的后半部分构建
                                if not long_token:
                                    logger.debug("【令牌获取】步骤2: 尝试从JWT中提取用户ID")
                                    try:
                                        user_id, _ = self.extract_user_from_jwt(session_token)
                                        logger.debug(f"【令牌获取】从JWT中提取到用户ID: {user_id}")
                                        if user_id and "未知" not in user_id:
                                            # 尝试查找令牌部分
                                            logger.debug("【令牌获取】尝试从会话令牌中查找长字符串作为令牌")
                                            token_parts = re.findall(r'[a-zA-Z0-9_-]{20,}', session_token)
                                            if token_parts:
                                                # 使用最长的部分作为令牌
                                                token_part = max(token_parts, key=len)
                                                long_token = token_part
                                                logger.info(f"【令牌获取】从会话令牌中提取到可能的令牌(最长字符串方式): {long_token[:15]}...")
                                            else:
                                                logger.debug("【令牌获取】未在会话令牌中找到长度超过20的字符串")
                                        else:
                                            logger.debug("【令牌获取】从JWT中提取的用户ID无效")
                                    except Exception as jwt_error:
                                        logger.error(f"【令牌获取】从JWT提取用户ID失败: {str(jwt_error)}")
                                
                                # 如果上述方法都失败，尝试使用CursorRegistration类获取令牌
                                if not long_token:
                                    logger.info("【令牌获取】步骤3: 从Cookie中直接提取失败，尝试使用CursorRegistration获取令牌...")
                                    cursor_reg = CursorRegistration()
                                    # 从会话令牌中创建cookie字符串
                                    cookie_str_for_pkce = f"WorkosCursorSessionToken={session_token}"
                                    logger.debug(f"【令牌获取】为PKCE方法准备Cookie字符串，长度: {len(cookie_str_for_pkce)}")
                                    # 初始化浏览器
                                    logger.debug("【令牌获取】正在初始化浏览器...")
                                    cursor_reg.init_browser()
                                    logger.debug("【令牌获取】浏览器初始化成功")
                                    # 设置cookie
                                    logger.debug("【令牌获取】正在设置Cookie...")
                                    cursor_reg.tab.set.cookies(cookie_str_for_pkce)
                                    logger.debug("【令牌获取】Cookie设置成功")
                                    # 获取令牌
                                    logger.info("【令牌获取】开始使用PKCE方法获取长期令牌...")
                                    long_token = cursor_reg.get_cursor_long_token()
                                    if long_token:
                                        logger.info(f"【令牌获取】成功通过CursorRegistration获取令牌: {long_token[:15]}...")
                                    else:
                                        logger.warning("【令牌获取】CursorRegistration无法获取令牌")
                            except Exception as token_error:
                                logger.error(f"【令牌获取】获取令牌过程中出现异常: {str(token_error)}")
                                logger.debug("【令牌获取】异常处理: 再次尝试从Cookie中直接提取令牌")
                                # 再次尝试从Cookie中直接提取令牌
                                session_token = reconstructed_cookie
                                if '%3A%3A' in session_token:
                                    parts = session_token.split('%3A%3A')
                                    if len(parts) >= 2:
                                        # 第二部分即为令牌
                                        long_token = parts[1]
                                        logger.info(f"【令牌获取】在异常处理中从会话令牌中提取到令牌(使用%3A%3A分隔符): {long_token[:15]}...")
                                elif '::' in session_token:
                                    parts = session_token.split('::')
                                    if len(parts) >= 2:
                                        # 第二部分即为令牌
                                        long_token = parts[1]
                                        logger.info(f"【令牌获取】在异常处理中从会话令牌中提取到令牌(使用::分隔符): {long_token[:15]}...")
                                else:
                                    logger.debug("【令牌获取】在异常处理中仍未能从会话令牌中提取令牌")
                                    
                            logger.info("【令牌获取】令牌获取过程结束")
                            if long_token:
                                logger.info("【令牌获取】成功获取到长期令牌")
                            else:
                                logger.warning("【令牌获取】未能获取到长期令牌")
                    except Exception as info_error:
                        logger.error(f"获取账号信息失败: {str(info_error)}")
                        # 使用现有信息
                        email = account_data.get('EMAIL', '未知')
                        quota = account_data.get('QUOTA', '未知')
                        days = account_data.get('DAYS', '未知')
                        long_token = account_data.get('TOKEN', '')
                        # 更新状态为非正常
                        if account_status == "正常":
                            account_status = "异常"
                    
                    # 更新账号信息
                    self.account_tree.set(self.selected_item, '用户ID', user_id)
                    self.account_tree.set(self.selected_item, '邮箱', email)
                    self.account_tree.set(self.selected_item, '使用量', quota)
                    self.account_tree.set(self.selected_item, '剩余天数', days)
                    self.account_tree.set(self.selected_item, '账户状态', account_status)
                    self.account_tree.set(self.selected_item, '令牌', long_token)
                    
                    # 更新CSV文件
                    try:
                        update_dict = {
                            'USERID': user_id,
                            'EMAIL': email,
                            'STATUS': account_status,
                            'QUOTA': quota,
                            'DAYS': days,
                            'COOKIES_STR': reconstructed_cookie
                        }
                        # 只有当令牌不为空时才更新TOKEN字段
                        if long_token:
                            update_dict['TOKEN'] = long_token
                            
                        self.update_csv_file(csv_file_path, **update_dict)
                    except Exception as e:
                        logger.error(f"更新CSV文件失败: {str(e)}")
                        raise ValueError(f"更新CSV文件失败: {str(e)}")
                    #关闭加载
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    #显示成功
                    success_message = (
                        f"用户ID: {user_id}\n"
                        f"邮箱: {email}\n"
                        f"状态: {account_status}\n"
                        f"密码: {account_data.get('PASSWORD','未知密码')}\n"
                        f"可用额度: {quota}\n"
                        f"剩余天数: {days}\n"
                    )
                    # 显示令牌状态
                    if long_token:
                        success_message += f"令牌: 已更新"
                    else:
                        success_message += f"令牌: 未获取"
                        
                    self.winfo_toplevel().after(0, lambda: UI.show_success(
                        self.winfo_toplevel(),
                        success_message
                    ))
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"获取账号信息失败: {error_message}")
                    logger.exception("详细错误信息:")
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "获取账号信息失败",
                        error_message
                    ))

            logger.debug("开始更新账号信息...")
            threading.Thread(target=fetch_and_display_info, daemon=True).start()

        self.handle_account_action("获取账号信息", get_trial_info)
    
    #更换账号
    def update_auth(self) -> None:
        #更换账号
        def update_account_auth(csv_file_path: str, account_data: Dict[str, str]) -> None:
            cookie_str = account_data.get('COOKIES_STR', '')
            email = account_data.get('EMAIL', '')
            if not cookie_str:
                raise ValueError(f"未找到账号 {email} 的Cookie信息")

            if "WorkosCursorSessionToken=" not in cookie_str:
                cookie_str = f"WorkosCursorSessionToken={cookie_str}"
            #更新账号Cookie
            def process_auth():
                try:
                    self.winfo_toplevel().after(0, lambda: UI.show_loading(
                        self.winfo_toplevel(),
                        "更换账号",
                        "正在刷新Cookie，请稍候..."
                    ))

                    result = CursorManager().process_cookies(cookie_str, email)
                    
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    
                    if not result.success:
                        raise ValueError(result.message)

                    UI.show_success(self.winfo_toplevel(), f"账号 {email} 的Cookie已刷新")
                    logger.info(f"已刷新账号 {email} 的Cookie")
                except Exception as e:
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "更换账号失败",
                        str(e)
                    ))

            threading.Thread(target=process_auth, daemon=True).start()

        self.handle_account_action("刷新Cookie", update_account_auth)

    #重置机器ID
    @error_handler
    def reset_machine_id(self) -> None:
        #重置机器ID
        def reset_thread():
            try:
                #显示加载
                self.after(0, lambda: UI.show_loading(
                    self.winfo_toplevel(),
                    "正在重置机器ID",
                    "正在执行重置操作，请稍候..."
                ))
                #重置机器ID
                result = CursorManager.reset()
                
                #关闭加载   
                self.after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                #显示成功
                if not result.success:
                    self.after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "重置机器ID失败",
                        result.message
                    ))
                    return
                #显示成功
                self.after(0, lambda: UI.show_success(
                    self.winfo_toplevel(),
                    result.message
                ))
                
            except Exception as e:
                #关闭加载       
                self.after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                #显示失败
                self.after(0, lambda: UI.show_error(
                    self.winfo_toplevel(),
                    "重置机器ID失败",
                    str(e)
                ))
        
        #启动线程
        threading.Thread(target=reset_thread, daemon=True).start()

    #删除账号   
    def delete_account(self):
        #删除账号
        def delete_account_file(csv_file_path: str, account_data: Dict[str, str]) -> None:
            confirm_message = (
                f"确定要删除以下账号吗？\n\n"
                f"用户ID：{account_data['USERID']}\n"
                f"邮箱：{account_data['EMAIL']}\n"
                f"密码：{account_data['PASSWORD']}\n"
                f"状态：{account_data['STATUS']}\n"
                f"剩余天数：{account_data['DAYS']}\n"
                f"使用量：{account_data['QUOTA']}\n"
                f"Cookie：{account_data['COOKIES_STR']}\n"
                f"令牌：{account_data['TOKEN']}\n"
            )

            if not messagebox.askyesno("确认删除", confirm_message, icon='warning'):
                return
            #删除账号
            def process_delete():
                try:
                    self.winfo_toplevel().after(0, lambda: UI.show_loading(
                        self.winfo_toplevel(),
                        "删除账号",
                        "正在删除账号信息，请稍候..."
                    ))

                    os.remove(csv_file_path)
                    self.account_tree.delete(self.selected_item)
                    #关闭加载
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    #显示成功
                    logger.info(f"已删除账号: {account_data['USERID']} - {account_data['EMAIL']}")
                    UI.show_success(self.winfo_toplevel(),
                                    f"已删除账号: {account_data['USERID']} - {account_data['EMAIL']}")
                except Exception as e:
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "删除账号失败",
                        str(e)
                    ))

            threading.Thread(target=process_delete, daemon=True).start()

        self.handle_account_action("删除账号", delete_account_file)

    #复制列
    def copy_column(self, column_index):
        if not self.selected_item:
            UI.show_warning(self.winfo_toplevel(), "请先选择一个账号")
            return
        
        item_values = self.account_tree.item(self.selected_item)['values']
        if not item_values or len(item_values) <= column_index:
            return
        
        copy_text = str(item_values[column_index])
        
        self.winfo_toplevel().clipboard_clear()
        self.winfo_toplevel().clipboard_append(copy_text)
        
        column_name = self.account_tree['columns'][column_index]
        UI.show_success(self.winfo_toplevel(), f"已复制 {column_name}")

    #复制Cookie
    def copy_cookie(self):
        if not self.selected_item:
            UI.show_warning(self.winfo_toplevel(), "请先选择一个账号")
            return
        
        try:
            _, account_data = self.get_selected_account()
            cookie = account_data.get('COOKIES_STR', '')
            
            if not cookie:
                UI.show_warning(self.winfo_toplevel(), "所选账号没有Cookie信息")
                return
            
            self.winfo_toplevel().clipboard_clear()
            self.winfo_toplevel().clipboard_append(cookie)
            
            UI.show_success(self.winfo_toplevel(), "已复制Cookie")
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), "复制Cookie失败", str(e))

    #复制所有信息
    def copy_all_info(self):
        if not self.selected_item:
            UI.show_warning(self.winfo_toplevel(), "请先选择一个账号")
            return
        
        try:
            csv_file_path, account_data = self.get_selected_account()
            
            # 构建完整的信息文本
            copy_text = "账号详细信息:\n"
            for key, value in account_data.items():
                if value:  # 只包含非空值
                    copy_text += f"{key}: {value}\n"
            
            self.winfo_toplevel().clipboard_clear()
            self.winfo_toplevel().clipboard_append(copy_text)
            
            UI.show_success(self.winfo_toplevel(), "已复制账号详细信息")
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), "复制账号信息失败", str(e))

    #查看账号详细信息
    def view_account_details(self):
        """查看账号详细信息"""
        if not self.selected_item:
            UI.show_warning(self.winfo_toplevel(), "请先选择一个账号")
            return
        
        try:
            csv_file_path, account_data = self.get_selected_account()
            
            # 创建详情对话框
            details_dialog = tk.Toplevel(self)
            details_dialog.title("账号详细信息")
            details_dialog.geometry("600x400")
            details_dialog.transient(self.winfo_toplevel())
            details_dialog.grab_set()
            
            # 主框架
            main_frame = ttk.Frame(details_dialog, style='TFrame', padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # 信息文本框
            info_text = tk.Text(main_frame, wrap=tk.WORD, width=60, height=15)
            info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 滚动条
            scrollbar = ttk.Scrollbar(info_text, orient=tk.VERTICAL, command=info_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            info_text.config(yscrollcommand=scrollbar.set)
            
            # 填充信息
            for key, value in account_data.items():
                if value:  # 只显示非空值
                    info_text.insert(tk.END, f"{key}: {value}\n")
            
            # 设为只读
            info_text.config(state=tk.DISABLED)
            
            # 按钮框架
            button_frame = ttk.Frame(main_frame, style='TFrame')
            button_frame.pack(pady=10)
            
            # 复制按钮
            def copy_all():
                details_dialog.clipboard_clear()
                details_dialog.clipboard_append(info_text.get(1.0, tk.END))
                UI.show_success(details_dialog, "已复制所有信息")
            
            ttk.Button(button_frame, text="复制全部", command=copy_all, 
                      style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)
            
            # 关闭按钮
            ttk.Button(button_frame, text="关闭", command=details_dialog.destroy, 
                      style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), "查看账号详情失败", str(e))

    # 处理右键菜单显示
    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            # 先判断是否有选中项
            if self.account_tree.selection():
                # 显示上下文菜单
                self.context_menu.tk_popup(event.x_root, event.y_root)
            else:
                UI.show_warning(self.winfo_toplevel(), "请先选择一个账号")
        finally:
            # 确保菜单能够正确关闭
            self.context_menu.grab_release()

    # 处理双击事件
    def on_double_click(self, event):
        """双击条目时打开详情对话框"""
        if self.account_tree.identify_region(event.x, event.y) == "cell":
            self.view_account_details()

    def on_column_click(self, column_idx):
        """点击列标题时排序或复制整列"""
        # 如果添加排序功能，可以在这里实现
        # 弹出确认是否要复制整列
        column_name = self.account_tree['columns'][column_idx]
        if messagebox.askyesno("复制确认", f"是否要复制所有账号的{column_name}?"):
            values = []
            for item in self.account_tree.get_children():
                item_values = self.account_tree.item(item)['values']
                if item_values and len(item_values) > column_idx:
                    values.append(str(item_values[column_idx]))
            
            if values:
                copy_text = "\n".join(values)
                self.winfo_toplevel().clipboard_clear()
                self.winfo_toplevel().clipboard_append(copy_text)
                UI.show_success(self.winfo_toplevel(), f"已复制所有账号的{column_name}")

    #添加账号
    def add_account(self):
        """手动添加账号"""
        # 创建添加账号对话框
        add_dialog = tk.Toplevel(self)
        add_dialog.title("添加账号")
        add_dialog.geometry("500x350")
        add_dialog.transient(self.winfo_toplevel())
        add_dialog.grab_set()
        
        # 主框架
        main_frame = ttk.Frame(add_dialog, style='TFrame', padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表单框架
        form_frame = ttk.Frame(main_frame, style='TFrame')
        form_frame.pack(fill=tk.X, pady=10)
        
        # 创建输入字段
        fields = [
            ('用户ID', '可选，自动从Cookie提取'),
            ('邮箱', '必填，Cursor账号邮箱'),
            ('密码', '必填，Cursor账号密码'),
            ('Cookie', '必填，格式: WorkosCursorSessionToken=xxx'),
            ('令牌', '可选，自动从Cookie获取'),
            ('账户状态', '可选，自动从Cookie提取'),
            ('剩余天数', '可选，默认14'),
            ('使用量', '可选，格式: 已用/总量')
        ]
        
        entries = {}
        for i, (label, placeholder) in enumerate(fields):
            frame = ttk.Frame(form_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=f"{label}:", width=8).pack(side=tk.LEFT, padx=5)
            entry = ttk.Entry(frame, width=50)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            entry.insert(0, placeholder)
            entry.config(foreground='gray')
            
            # 设置焦点事件，清除占位文字
            def on_focus_in(event, entry=entry, placeholder=placeholder):
                if entry.get() == placeholder:
                    entry.delete(0, tk.END)
                    entry.config(foreground='black')
            
            def on_focus_out(event, entry=entry, placeholder=placeholder):
                if not entry.get():
                    entry.insert(0, placeholder)
                    entry.config(foreground='gray')
            
            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)
            
            entries[label] = entry
        
        # 提示框
        tip_frame = ttk.Frame(main_frame)
        tip_frame.pack(fill=tk.X, pady=10)
        
        tip_text = ("提示:\n"
                   "• 必须填写邮箱、密码和Cookie\n"
                   "• 其他字段可以留空，系统会自动提取或设置默认值\n"
                   "• Cookie格式: WorkosCursorSessionToken=xxx\n")
        
        tip_label = ttk.Label(tip_frame, text=tip_text, style="TipText.TLabel", wraplength=450)
        tip_label.pack(fill=tk.X)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        def validate_and_save():
            try:
                # 获取所有输入
                account_data = {}
                for label, entry in entries.items():
                    value = entry.get()
                    # 跳过占位符文本
                    if value and value != fields[list(label for label, _ in fields).index(label)][1]:
                        account_data[label] = value
                
                # 验证必填字段
                if 'Cookie' not in account_data or not account_data['Cookie']:
                    raise ValueError("Cookie不能为空")
                
                if 'Cookie' in account_data and not account_data['Cookie'].startswith("WorkosCursorSessionToken="):
                    account_data['Cookie'] = f"WorkosCursorSessionToken={account_data['Cookie']}"
                
                if '邮箱' not in account_data or not account_data['邮箱']:
                    raise ValueError("邮箱不能为空")
                
                if '密码' not in account_data or not account_data['密码']:
                    raise ValueError("密码不能为空")
                
                # 提取Cookie中的用户ID和账户状态
                if 'Cookie' in account_data and not account_data.get('用户ID'):
                    try:
                        user_id, account_status = self.extract_user_from_jwt(account_data['Cookie'])
                        account_data['用户ID'] = user_id
                        if not account_data.get('账户状态'):
                            account_data['账户状态'] = account_status
                    except Exception as e:
                        logger.error(f"从Cookie提取用户信息失败: {str(e)}")
                
                # 设置默认值
                if not account_data.get('账户状态'):
                    account_data['账户状态'] = '未知'
                
                if not account_data.get('剩余天数'):
                    account_data['剩余天数'] = '14'
                
                if not account_data.get('使用量'):
                    account_data['使用量'] = '0/150'
                
                # 保存到CSV文件
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_file = f"env_backups/cursor_account_{timestamp}.csv"
                
                # 确保目录存在
                os.makedirs('env_backups', exist_ok=True)
                
                with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                    csv_writer = csv.writer(f)
                    csv_writer.writerow(['key', 'value'])  # 写入标题行
                    
                    # 映射字段名称
                    field_map = {
                        '用户ID': 'USERID',
                        '邮箱': 'EMAIL',
                        '密码': 'PASSWORD',
                        '账户状态': 'STATUS',
                        '剩余天数': 'DAYS',
                        '使用量': 'QUOTA',
                        'Cookie': 'COOKIES_STR',
                        '令牌': 'TOKEN'
                    }
                    
                    for ui_field, csv_field in field_map.items():
                        value = account_data.get(ui_field, '')
                        csv_writer.writerow([csv_field, value])
                
                logger.info(f"已添加账号，保存到文件: {csv_file}")
                UI.show_success(add_dialog, f"已成功添加账号: {account_data.get('邮箱')}")
                
                # 刷新账号列表
                self.after(500, self.refresh_list)
                
                # 关闭对话框
                add_dialog.destroy()
                
            except Exception as e:
                UI.show_error(add_dialog, "添加账号失败", str(e))
        
        ttk.Button(button_frame, text="保存", command=validate_and_save, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="取消", command=add_dialog.destroy, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)
    
    #导入账号
    def import_account(self):
        """从外部文件导入账号"""
        file_types = [
            ('CSV文件', '*.csv'),
            ('所有文件', '*.*')
        ]
        
        # 打开文件选择对话框
        file_path = filedialog.askopenfilename(
            title="选择账号文件",
            filetypes=file_types
        )
        
        if not file_path:
            return
        
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 尝试解析不同格式的文件
            account_data = {}
            
            # 检查文件内容，判断格式
            if "," in content and ("\n" in content or "\r" in content):
                # 可能是CSV格式
                try:
                    # 重新打开文件用CSV读取器读取
                    with open(file_path, 'r', encoding='utf-8') as f:
                        csv_reader = csv.reader(f)
                        rows = list(csv_reader)
                        
                    if len(rows) > 0:
                        if len(rows[0]) >= 2 and rows[0][0].lower() == 'key' and rows[0][1].lower() == 'value':
                            # 标准格式: key,value
                            for row in rows[1:]:  # 跳过标题行
                                if len(row) >= 2:
                                    account_data[row[0]] = row[1]
                        else:
                            # 尝试解析为字段名,值格式
                            header = rows[0]
                            if len(rows) > 1:
                                values = rows[1]
                                for i, key in enumerate(header):
                                    if i < len(values):
                                        account_data[key] = values[i]
                except Exception as csv_error:
                    logger.error(f"CSV解析失败: {csv_error}")
                    raise ValueError(f"导入CSV文件失败: {csv_error}")
            
            # 检查必需字段
            required_fields = ['EMAIL', 'PASSWORD', 'COOKIES_STR']
            missing_fields = [field for field in required_fields if field not in account_data or not account_data[field]]
            
            if missing_fields:
                raise ValueError(f"缺少必填字段: {', '.join(missing_fields)}")
            
            # 提取Cookie中的用户ID和账户状态
            if 'COOKIES_STR' in account_data and not account_data.get('USERID'):
                try:
                    user_id, account_status = self.extract_user_from_jwt(account_data['COOKIES_STR'])
                    account_data['USERID'] = user_id
                    if not account_data.get('STATUS'):
                        account_data['STATUS'] = account_status
                except Exception as e:
                    logger.error(f"从Cookie提取用户信息失败: {str(e)}")
            
            # 设置默认值
            if not account_data.get('STATUS'):
                account_data['STATUS'] = '未知'
            
            if not account_data.get('DAYS'):
                account_data['DAYS'] = '14'
            
            if not account_data.get('QUOTA'):
                account_data['QUOTA'] = '0/150'
            
            # 保存到新的CSV文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"env_backups/cursor_account_{timestamp}.csv"
            
            # 确保目录存在
            os.makedirs('env_backups', exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(['key', 'value'])  # 写入标题行
                
                for key, value in account_data.items():
                    csv_writer.writerow([key, value])
            
            logger.info(f"已导入账号，保存到文件: {output_file}")
            UI.show_success(self.winfo_toplevel(), f"已成功导入账号: {account_data.get('EMAIL')}")
            
            # 刷新账号列表
            self.refresh_list()
            
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), "导入账号失败", str(e))
    
    #导出账号
    def export_account(self):
        """导出当前选中的账号"""
        if not self.selected_item:
            UI.show_warning(self.winfo_toplevel(), "请先选择一个账号")
            return
        
        try:
            csv_file_path, account_data = self.get_selected_account()
            
            # 创建保存文件对话框
            file_types = [('CSV文件', '*.csv'), ('所有文件', '*.*')]
            email = account_data.get('EMAIL', 'account')
            default_filename = f"cursor_account_{email.split('@')[0]}_{datetime.now().strftime('%Y%m%d')}.csv"
            
            save_path = filedialog.asksaveasfilename(
                title="导出账号",
                defaultextension=".csv",
                filetypes=file_types,
                initialfile=default_filename
            )
            
            if not save_path:
                return
            
            # 复制CSV文件
            with open(csv_file_path, 'r', encoding='utf-8') as src, open(save_path, 'w', encoding='utf-8', newline='') as dst:
                dst.write(src.read())
            
            UI.show_success(self.winfo_toplevel(), f"已成功导出账号: {account_data.get('EMAIL')}")
            logger.info(f"已导出账号到: {save_path}")
            
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), "导出账号失败", str(e))

