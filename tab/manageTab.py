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
import threading
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk, messagebox
from typing import Dict, List, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor
import base64
import json
import sqlite3

import requests
from loguru import logger

from utils import CursorManager, error_handler,Utils
from .ui import UI
from database import create_cursor_database


class ManageTab(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.registrar = None
        # 确保数据库存在
        create_cursor_database()
        self.setup_ui()
        self.update_timer = None  # 初始化定时器变量
        
        # 绑定标签页切换事件
        if isinstance(parent, ttk.Notebook):
            parent.bind('<<NotebookTabChanged>>', self.on_tab_changed)

    def on_tab_changed(self, event):
        """处理标签页切换事件"""
        notebook = event.widget
        current_tab = notebook.select()
        if notebook.index(current_tab) == notebook.index(self):
            # 当切换到账号管理标签页时
            self.refresh_list()  # 刷新账号列表
            # 不自动更新账号信息，让用户手动点击"更新信息"按钮

    def setup_ui(self):
        accounts_frame = UI.create_labeled_frame(self, "已保存账号")

        columns = ('域名', '邮箱', '额度', '剩余天数')
        tree = ttk.Treeview(accounts_frame, columns=columns, show='headings', height=TREE_VIEW_HEIGHT)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=COLUMN_WIDTH)

        tree.bind('<<TreeviewSelect>>', self.on_select)

        scrollbar = ttk.Scrollbar(accounts_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        outer_button_frame = ttk.Frame(self, style='TFrame')
        outer_button_frame.pack(pady=(PADDING['LARGE'], 0), expand=True)

        button_frame = ttk.Frame(outer_button_frame, style='TFrame')
        button_frame.pack(anchor=tk.W)

        first_row_frame = ttk.Frame(button_frame, style='TFrame')
        first_row_frame.pack(pady=(0, PADDING['MEDIUM']), anchor=tk.W)
        
        ttk.Button(first_row_frame, text="切换账号", command=self.update_auth, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        ttk.Button(first_row_frame, text="重置ID", command=self.reset_machine_id, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        ttk.Button(first_row_frame, text="删除账号", command=self.delete_account, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])

        self.account_tree = tree
        self.selected_item = None

    def start_auto_update(self):
        """启动自动更新定时器"""
        self.update_all_accounts()  # 立即更新所有账号
        self.schedule_next_update()  # 安排下一次更新

    def schedule_next_update(self):
        """安排下一次自动更新"""
        if self.update_timer:
            self.after_cancel(self.update_timer)
        self.update_timer = self.after(30 * 60 * 1000, self.update_all_accounts)  # 30分钟后更新
    #更新所有账号信息
    def update_all_accounts(self):
        """更新所有账号信息"""
        try:
            items = self.account_tree.get_children()
            if not items:
                return

            # 使用线程池控制并发数量
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for item in items:
                    try:
                        csv_file_path = item
                        account_data = self.parse_csv_file(csv_file_path)
                        future = executor.submit(self.update_single_account, csv_file_path, account_data)
                        futures.append(future)
                    except Exception as e:
                        logger.error(f"提交更新任务失败 {item}: {str(e)}")

                # 等待所有任务完成
                for future in futures:
                    try:
                        future.result()  # 获取结果，如果有异常会在这里抛出
                    except Exception as e:
                        logger.error(f"执行更新任务失败: {str(e)}")

            self.schedule_next_update()  # 安排下一次更新
        except Exception as e:
            logger.error(f"批量更新账号失败: {str(e)}")
            raise  # 向上传递异常，让调用者处理

    #更新单个账号信息
    def update_single_account(self, csv_file_path: str, account_data: Dict[str, str]) -> None:
        """更新单个账号信息"""
        cookie_str = account_data.get('COOKIES_STR', '')
        if not cookie_str:
            return

        try:
            user_id = self.extract_user_id_from_jwt(cookie_str)
            reconstructed_cookie = f"WorkosCursorSessionToken={user_id}%3A%3A{cookie_str.split('%3A%3A')[-1]}" if '%3A%3A' in cookie_str else cookie_str

            domain, email, quota, days = self.get_trial_usage(reconstructed_cookie)
            
            # 使用 after 方法确保在主线程中更新 UI
            self.winfo_toplevel().after(0, lambda: self.account_tree.set(csv_file_path, '域名', domain))
            self.winfo_toplevel().after(0, lambda: self.account_tree.set(csv_file_path, '邮箱', email))
            self.winfo_toplevel().after(0, lambda: self.account_tree.set(csv_file_path, '额度', quota))
            self.winfo_toplevel().after(0, lambda: self.account_tree.set(csv_file_path, '剩余天数', days))

            # 更新CSV文件
            self.update_csv_file(csv_file_path,
                               DOMAIN=domain,
                               EMAIL=email,
                               QUOTA=quota,
                               DAYS=days,
                               COOKIES_STR=reconstructed_cookie)

            # 更新数据库
            self.update_database(domain, email, account_data.get('PASSWORD', ''), 
                               reconstructed_cookie, quota, days)

            logger.debug(f"已更新账号信息: {email}")
        except Exception as e:
            logger.error(f"更新账号 {csv_file_path} 失败: {str(e)}")
            raise  # 向上传递异常，让线程池捕获

    def update_database(self, domain: str, email: str, password: str, 
                       cookie_str: str, quota: str, days: str) -> None:
        """更新数据库中的账号信息"""
        try:
            conn = sqlite3.connect('cursor.db')
            cursor = conn.cursor()

            # 检查账号是否已存在
            cursor.execute('SELECT id FROM accounts WHERE email = ?', (email,))
            existing_account = cursor.fetchone()

            if existing_account:
                # 更新现有账号
                cursor.execute('''
                    UPDATE accounts 
                    SET domain = ?, password = ?, cookie_str = ?, 
                        quota = ?, days = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE email = ?
                ''', (domain, password, cookie_str, quota, days, email))
            else:
                # 插入新账号
                cursor.execute('''
                    INSERT INTO accounts (domain, email, password, cookie_str, quota, days)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (domain, email, password, cookie_str, quota, days))

            conn.commit()
            logger.debug(f"数据库更新成功: {email}")
        except Exception as e:
            logger.error(f"数据库更新失败: {str(e)}")
        finally:
            conn.close()

    #选择账号
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
        account_data = {
            'DOMAIN': '',
            'EMAIL': '',
            'COOKIES_STR': '',
            'QUOTA': '未知',
            'DAYS': '未知',
            'PASSWORD': '',
            'API_KEY': '',
            'MOE_MAIL_URL': ''
        }
        try:
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

    def refresh_list(self):
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)

        try:
            csv_files = self.get_csv_files()
            for csv_file in csv_files:
                account_data = self.parse_csv_file(csv_file)
                self.account_tree.insert('', 'end', iid=csv_file, values=(
                    account_data['DOMAIN'],
                    account_data['EMAIL'],
                    account_data['QUOTA'],
                    account_data['DAYS']
                ))

            logger.info("账号列表已刷新")
            
            # 显示加载提示
            self.winfo_toplevel().after(0, lambda: UI.show_loading(
                self.winfo_toplevel(),
                "更新账号信息",
                "正在获取所有账号信息，请稍候..."
            ))
            
            # 在新线程中更新所有账号信息
            def update_thread():
                try:
                    self.update_all_accounts()
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_success(
                        self.winfo_toplevel(),
                        "所有账号信息已更新"
                    ))
                except Exception as e:
                    logger.error(f"更新账号信息失败: {str(e)}")
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "更新账号信息失败",
                        str(e)
                    ))
            
            threading.Thread(target=update_thread, daemon=True).start()
            
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), "刷新列表失败", e)

    def get_selected_account(self) -> Tuple[str, Dict[str, str]]:
        if not self.selected_item:
            raise ValueError("请先选择要操作的账号")

        item_values = self.account_tree.item(self.selected_item)['values']
        if not item_values or len(item_values) < 2:
            raise ValueError("所选账号信息不完整")

        csv_file_path = self.selected_item
        account_data = self.parse_csv_file(csv_file_path)

        if not account_data['DOMAIN'] or not account_data['EMAIL']:
            raise ValueError("账号信息不完整")

        return csv_file_path, account_data

    def handle_account_action(self, action_name: str, action: Callable[[str, Dict[str, str]], None]) -> None:
        try:
            csv_file_path, account_data = self.get_selected_account()
            action(csv_file_path, account_data)
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), f"{action_name}失败", e)
            logger.error(f"{action_name}失败: {str(e)}")

    def get_trial_usage(self, cookie_str: str) -> Tuple[str, str, str, str]:
        if not cookie_str:
            raise ValueError("Cookie信息不能为空")

        try:
            user_id = self.extract_user_id_from_jwt(cookie_str)
            
            if not cookie_str.startswith('WorkosCursorSessionToken='):
                cookie_str = f'WorkosCursorSessionToken={cookie_str}'

            headers = {
                'Cookie': cookie_str,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }

            timeout = 10
            session = requests.Session()
            session.headers.update(headers)

            def make_request(url: str) -> dict:
                try:
                    response = session.get(url, timeout=timeout)
                    response.raise_for_status()
                    return response.json()
                except requests.RequestException as e:
                    logger.error(f"请求 {url} 失败: {str(e)}")
                    raise ValueError(f"API请求失败: {str(e)}")

            try:
                with ThreadPoolExecutor(max_workers=3) as executor:
                    future_user_info = executor.submit(make_request, "https://www.cursor.com/api/auth/me")
                    future_trial = executor.submit(make_request, "https://www.cursor.com/api/auth/stripe")
                    future_usage = executor.submit(make_request, f"https://www.cursor.com/api/usage?user={user_id}")

                    user_info = future_user_info.result()
                    email = user_info.get('email', '未知')
                    domain = email.split('@')[-1] if '@' in email else '未知'

                    trial_data = future_trial.result()
                    days = str(trial_data.get('daysRemainingOnTrial', '未知'))

                    usage_data = future_usage.result()
                    gpt4_data = usage_data.get('gpt-4', {})
                    used_quota = gpt4_data.get('numRequestsTotal', 0)
                    max_quota = gpt4_data.get('maxRequestUsage', 0)
                    quota = f"{used_quota} / {max_quota}" if max_quota else '未知'

                    return domain, email, quota, days

            except Exception as e:
                logger.error(f"获取账号信息失败: {str(e)}")
                raise ValueError(f"获取账号信息失败: {str(e)}")
            finally:
                session.close()
        except Exception as e:
            logger.error(f"处理 JWT 失败: {str(e)}")
            raise ValueError(f"处理 JWT 失败: {str(e)}")

    def extract_user_id_from_jwt(self, cookies: str) -> str:
        try:
            jwt_token = Utils.extract_token(cookies, "WorkosCursorSessionToken")
            parts = jwt_token.split('.')
            if len(parts) != 3:
                raise ValueError("无效的 JWT 格式")
            
            payload = parts[1]
            payload += '=' * (-len(payload) % 4)
            decoded = base64.b64decode(payload)
            payload_data = json.loads(decoded)
            
            user_id = payload_data.get('sub')
            if not user_id:
                raise ValueError("JWT 中未找到用户 ID")
                
            return user_id
        except Exception as e:
            logger.error(f"从 JWT 提取用户 ID 失败: {str(e)}")
            raise ValueError(f"JWT 解析失败: {str(e)}")

    def update_account_info(self):
        def get_trial_info(csv_file_path: str, account_data: Dict[str, str]) -> None:
            cookie_str = account_data.get('COOKIES_STR', '')
            if not cookie_str:
                raise ValueError(f"未找到账号 {account_data['EMAIL']} 的Cookie信息")

            def fetch_and_display_info():
                try:
                    self.winfo_toplevel().after(0, lambda: UI.show_loading(
                        self.winfo_toplevel(),
                        "更新账号信息",
                        "正在获取账号信息，请稍候..."
                    ))

                    logger.debug("开始获取账号信息...")
                    logger.debug(f"获取到的cookie字符串长度: {len(cookie_str) if cookie_str else 0}")

                    user_id = self.extract_user_id_from_jwt(cookie_str)
                    reconstructed_cookie = f"WorkosCursorSessionToken={user_id}%3A%3A{cookie_str.split('%3A%3A')[-1]}" if '%3A%3A' in cookie_str else cookie_str

                    domain, email, quota, days = self.get_trial_usage(reconstructed_cookie)
                    logger.info(f"成功获取账号信息: 域名={domain}, 邮箱={email}, 额度={quota}, 天数={days}")

                    self.account_tree.set(self.selected_item, '域名', domain)
                    self.account_tree.set(self.selected_item, '邮箱', email)
                    self.account_tree.set(self.selected_item, '额度', quota)
                    self.account_tree.set(self.selected_item, '剩余天数', days)

                    try:
                        self.update_csv_file(csv_file_path,
                                           DOMAIN=domain,
                                           EMAIL=email,
                                           QUOTA=quota,
                                           DAYS=days,
                                           COOKIES_STR=reconstructed_cookie)
                    except Exception as e:
                        logger.error(f"更新CSV文件失败: {str(e)}")
                        raise ValueError(f"更新CSV文件失败: {str(e)}")

                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_success(
                        self.winfo_toplevel(),
                        f"域名: {domain}\n"
                        f"邮箱: {email}\n"
                        f"可用额度: {quota}\n"
                        f"剩余天数: {days}"
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

    def update_auth(self) -> None:
        def update_account_auth(csv_file_path: str, account_data: Dict[str, str]) -> None:
            cookie_str = account_data.get('COOKIES_STR', '')
            email = account_data.get('EMAIL', '')
            if not cookie_str:
                raise ValueError(f"未找到账号 {email} 的Cookie信息")

            if "WorkosCursorSessionToken=" not in cookie_str:
                cookie_str = f"WorkosCursorSessionToken={cookie_str}"

            def process_auth():
                try:
                    self.winfo_toplevel().after(0, lambda: UI.show_loading(
                        self.winfo_toplevel(),
                        "切换账号",
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
                        "切换账号失败",
                        str(e)
                    ))

            threading.Thread(target=process_auth, daemon=True).start()

        self.handle_account_action("刷新Cookie", update_account_auth)

    def delete_account(self):
        def delete_account_file(csv_file_path: str, account_data: Dict[str, str]) -> None:
            confirm_message = (
                f"确定要删除以下账号吗？\n\n"
                f"域名：{account_data['DOMAIN']}\n"
                f"邮箱：{account_data['EMAIL']}\n"
                f"额度：{account_data['QUOTA']}\n"
                f"剩余天数：{account_data['DAYS']}"
            )

            if not messagebox.askyesno("确认删除", confirm_message, icon='warning'):
                return

            def process_delete():
                try:
                    self.winfo_toplevel().after(0, lambda: UI.show_loading(
                        self.winfo_toplevel(),
                        "删除账号",
                        "正在删除账号信息，请稍候..."
                    ))

                    # 删除CSV文件
                    os.remove(csv_file_path)
                    
                    # 从数据库中删除
                    try:
                        conn = sqlite3.connect('cursor.db')
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM accounts WHERE email = ?', (account_data['EMAIL'],))
                        conn.commit()
                        logger.debug(f"从数据库中删除账号: {account_data['EMAIL']}")
                    except Exception as e:
                        logger.error(f"从数据库删除账号失败: {str(e)}")
                    finally:
                        conn.close()

                    # 从树形视图中删除
                    self.account_tree.delete(self.selected_item)
                    
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    logger.info(f"已删除账号: {account_data['DOMAIN']} - {account_data['EMAIL']}")
                    UI.show_success(self.winfo_toplevel(),
                                    f"已删除账号: {account_data['DOMAIN']} - {account_data['EMAIL']}")
                except Exception as e:
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "删除账号失败",
                        str(e)
                    ))

            threading.Thread(target=process_delete, daemon=True).start()

        self.handle_account_action("删除账号", delete_account_file)

    @error_handler
    def reset_machine_id(self) -> None:
        def reset_thread():
            try:
          
                self.after(0, lambda: UI.show_loading(
                    self.winfo_toplevel(),
                    "正在重置机器ID",
                    "正在执行重置操作，请稍候..."
                ))
                
               
                result = CursorManager.reset()
                
               
                self.after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                
                if not result.success:
                    self.after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "重置机器ID失败",
                        result.message
                    ))
                    return
                    
                self.after(0, lambda: UI.show_success(
                    self.winfo_toplevel(),
                    result.message
                ))
                
            except Exception as e:
               
                self.after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                self.after(0, lambda: UI.show_error(
                    self.winfo_toplevel(),
                    "重置机器ID失败",
                    str(e)
                ))
        
      
        threading.Thread(target=reset_thread, daemon=True).start()
