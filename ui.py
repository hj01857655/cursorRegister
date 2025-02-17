import os
import tkinter as tk
from tkinter import ttk, messagebox
from loguru import logger
from datetime import datetime
from typing import Dict, List, Tuple, Callable
import glob
import csv
import threading
from registerAc import CursorRegistration
from utils import CursorManager, error_handler


class UI:
    FONT = ('Microsoft YaHei UI', 10)
    BUTTON_PADDING = (8, 4)
    BUTTON_GRID_PADDING = 4
    BUTTON_GRID_MARGIN = 3
    COLORS = {
        'primary': '#2563EB',
        'secondary': '#64748B',
        'success': '#059669',
        'error': '#DC2626',
        'warning': '#D97706',
        'bg': '#F8FAFC',
        'card_bg': '#FFFFFF',
        'disabled': '#94A3B8',
        'hover': '#1D4ED8',
        'pressed': '#1E40AF',
        'border': '#E2E8F0',
        'input_bg': '#FFFFFF',
        'label_fg': '#334155',
        'title_fg': '#1E40AF',
        'subtitle_fg': '#475569'
    }

    @staticmethod
    def setup_styles() -> None:
        style = ttk.Style()
        base_style = {
            'font': UI.FONT,
            'background': UI.COLORS['bg']
        }

        style.configure('TFrame', background=UI.COLORS['bg'])

        style.configure('TLabelframe',
                        background=UI.COLORS['card_bg'],
                        padding=10,
                        relief='flat',
                        borderwidth=1
                        )

        style.configure('TLabelframe.Label',
                        font=(UI.FONT[0], 11, 'bold'),
                        foreground=UI.COLORS['title_fg'],
                        background=UI.COLORS['bg'],
                        padding=(0, 4)
                        )

        style.configure('Custom.TButton',
                        font=(UI.FONT[0], 10, 'bold'),
                        padding=UI.BUTTON_PADDING,
                        background=UI.COLORS['primary'],
                        foreground='black',
                        borderwidth=0,
                        relief='flat'
                        )

        style.map('Custom.TButton',
                  background=[
                      ('pressed', UI.COLORS['pressed']),
                      ('active', UI.COLORS['hover']),
                      ('disabled', UI.COLORS['disabled'])
                  ],
                  foreground=[
                      ('pressed', 'black'),
                      ('active', 'black'),
                      ('disabled', '#94A3B8')
                  ]
                  )

        style.configure('TEntry',
                        padding=8,
                        relief='flat',
                        borderwidth=1,
                        selectbackground=UI.COLORS['primary'],
                        selectforeground='white',
                        fieldbackground=UI.COLORS['input_bg']
                        )

        style.configure('TLabel',
                        font=(UI.FONT[0], 10),
                        background=UI.COLORS['bg'],
                        foreground=UI.COLORS['label_fg'],
                        padding=(4, 2)
                        )

        style.configure('Footer.TLabel',
                        font=(UI.FONT[0], 9),
                        foreground=UI.COLORS['subtitle_fg'],
                        background=UI.COLORS['bg']
                        )

        style.configure('Title.TLabel',
                        font=(UI.FONT[0], 14, 'bold'),
                        foreground=UI.COLORS['title_fg'],
                        background=UI.COLORS['bg']
                        )

        style.configure('TRadiobutton',
                        font=UI.FONT,
                        background=UI.COLORS['bg'],
                        foreground=UI.COLORS['label_fg']
                        )

        style.map('TRadiobutton',
                  background=[('active', UI.COLORS['bg'])],
                  foreground=[('active', UI.COLORS['primary'])]
                  )

        style.configure('TCheckbutton',
                        font=UI.FONT,
                        background=UI.COLORS['bg'],
                        foreground=UI.COLORS['label_fg']
                        )

        style.map('TCheckbutton',
                  background=[('active', UI.COLORS['bg'])],
                  foreground=[('active', UI.COLORS['primary'])]
                  )

    @staticmethod
    def create_labeled_entry(parent, label_text: str, row: int, **kwargs) -> ttk.Entry:
        frame = ttk.Frame(parent, style='TFrame')
        frame.grid(row=row, column=0, columnspan=2, sticky='ew', padx=6, pady=3)

        label = ttk.Label(frame, text=f"{label_text}:", style='TLabel')
        label.pack(side=tk.LEFT, padx=(3, 8))

        entry = ttk.Entry(frame, style='TEntry', **kwargs)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        return entry

    @staticmethod
    def create_labeled_frame(parent, title: str, padding: str = "10", **kwargs) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(
            parent,
            text=title,
            padding=padding,
            style='TLabelframe',
            **kwargs
        )
        frame.pack(fill=tk.X, padx=10, pady=4)
        frame.columnconfigure(1, weight=1)
        return frame

    @staticmethod
    def center_window(window, width: int, height: int) -> None:
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def show_message(window: tk.Tk, title: str, message: str, msg_type: str) -> None:
        window.bell()
        getattr(messagebox, msg_type)(title, message)
        log_level = 'error' if msg_type == 'showerror' else 'warning' if msg_type == 'showwarning' else 'info'
        getattr(logger, log_level)(message)

    @staticmethod
    def show_error(window: tk.Tk, title: str, error: Exception) -> None:
        UI.show_message(window, "错误", f"{title}: {str(error)}", 'showerror')

    @staticmethod
    def show_success(window: tk.Tk, message: str) -> None:
        UI.show_message(window, "成功", message, 'showinfo')

    @staticmethod
    def show_warning(window: tk.Tk, message: str) -> None:
        UI.show_message(window, "警告", message, 'showwarning')


class LogWindow(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.show_debug = tk.BooleanVar(value=True)
        self.setup_ui()

    def setup_ui(self):
        title_frame = ttk.Frame(self, style='TFrame')
        title_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(
            title_frame,
            text="日志信息",
            style='Title.TLabel'
        ).pack(side=tk.LEFT)

        debug_checkbox = ttk.Checkbutton(
            title_frame,
            text="调试模式",
            variable=self.show_debug,
            style='TCheckbutton',
            command=self.refresh_logs
        )
        debug_checkbox.pack(side=tk.RIGHT, padx=(20, 10))

        clear_button = ttk.Button(
            title_frame,
            text="清除日志",
            command=self.clear_logs,
            style='Custom.TButton',
            width=10
        )
        clear_button.pack(side=tk.RIGHT)

        text_container = ttk.Frame(self, style='TFrame')
        text_container.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(
            text_container,
            wrap=tk.WORD,
            width=50,
            font=UI.FONT,
            bg=UI.COLORS['card_bg'],
            fg=UI.COLORS['label_fg'],
            relief='flat',
            padx=8,
            pady=8
        )
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.text.configure(state='disabled')
        self.log_buffer = []

    def clear_logs(self):
        self.text.configure(state='normal')
        self.text.delete(1.0, tk.END)
        self.text.configure(state='disabled')
        self.log_buffer = []

    def refresh_logs(self):
        self.text.configure(state='normal')
        self.text.delete(1.0, tk.END)
        for log in self.log_buffer:
            if self.show_debug.get() or log['level'] != 'DEBUG':
                self._insert_log(log['message'], log['level'], log['timestamp'])
        self.text.configure(state='disabled')

    def add_log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_buffer.append({
            'message': message,
            'level': level,
            'timestamp': timestamp
        })
        if self.show_debug.get() or level != 'DEBUG':
            self._insert_log(message, level, timestamp)

    def _insert_log(self, message: str, level: str, timestamp: str):
        self.text.configure(state='normal')
        tag = f"log_{level.lower()}"
        
        level_colors = {
            'DEBUG': UI.COLORS['secondary'],
            'INFO': UI.COLORS['primary'],
            'WARNING': UI.COLORS['warning'],
            'ERROR': UI.COLORS['error'],
            'SUCCESS': UI.COLORS['success']
        }
        
        self.text.tag_configure(tag, foreground=level_colors.get(level, UI.COLORS['label_fg']))
        
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        self.text.insert(tk.END, log_entry, tag)
        self.text.see(tk.END)
        self.text.configure(state='disabled')


class RegisterTab(ttk.Frame):
    def __init__(self, parent, env_vars: List[Tuple[str, str]], buttons: List[Tuple[str, str]], 
                 entries: Dict[str, ttk.Entry], selected_mode: tk.StringVar, 
                 button_commands: Dict[str, Callable], **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.env_vars = env_vars
        self.buttons = buttons
        self.entries = entries
        self.selected_mode = selected_mode
        self.button_commands = button_commands
        self.setup_ui()

    def setup_ui(self):
        account_frame = UI.create_labeled_frame(self, "账号信息")
        for row, (var_name, label_text) in enumerate(self.env_vars):
            entry = UI.create_labeled_entry(account_frame, label_text, row)
            if os.getenv(var_name):
                entry.insert(0, os.getenv(var_name))
            self.entries[var_name] = entry

        cookie_frame = UI.create_labeled_frame(self, "Cookie设置")
        self.entries['cookie'] = UI.create_labeled_entry(cookie_frame, "Cookie", 0)
        if os.getenv('COOKIES_STR'):
            self.entries['cookie'].insert(0, os.getenv('COOKIES_STR'))
        else:
            self.entries['cookie'].insert(0, "WorkosCursorSessionToken")

        radio_frame = ttk.Frame(self, style='TFrame')
        radio_frame.pack(fill=tk.X, pady=(8, 0))

        mode_label = ttk.Label(radio_frame, text="注册模式:", style='TLabel')
        mode_label.pack(side=tk.LEFT, padx=(3, 8))

        modes = [
            ("人工过验证", "semi"),
            ("自动过验证", "auto"),
            ("全自动注册", "admin")
        ]

        for text, value in modes:
            ttk.Radiobutton(
                radio_frame,
                text=text,
                variable=self.selected_mode,
                value=value,
                style='TRadiobutton'
            ).pack(side=tk.LEFT, padx=10)

        button_frame = ttk.Frame(self, style='TFrame')
        button_frame.pack(fill=tk.X, pady=(8, 0))

        for i, (text, command) in enumerate(self.buttons):
            row = i // 2
            col = i % 2
            btn = ttk.Button(
                button_frame,
                text=text,
                command=self.button_commands[command],
                style='Custom.TButton',
                width=8
            )
            btn.grid(
                row=row,
                column=col,
                padx=3,
                pady=2,
                sticky='nsew'
            )

        for i in range(2):
            button_frame.grid_columnconfigure(i, weight=1)


class ManageTab(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.registrar = None
        self.setup_ui()

    def setup_ui(self):
        accounts_frame = UI.create_labeled_frame(self, "已保存账号")
        
        columns = ('域名', '邮箱', '额度', '剩余天数')
        tree = ttk.Treeview(accounts_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.bind('<<TreeviewSelect>>', self.on_select)
        
        scrollbar = ttk.Scrollbar(accounts_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        button_frame = ttk.Frame(self, style='TFrame')
        button_frame.pack(fill=tk.X, pady=(8, 0))

        buttons = [
            ("刷新列表", self.refresh_list),
            ("获取试用信息", self.show_trial_info),
            ("刷新cookie", self.update_auth),
            ("重置机器ID", self.reset_machine_id),
            ("删除账号", self.delete_account)
        ]

        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(
                button_frame,
                text=text,
                command=command,
                style='Custom.TButton',
                width=10
            )
            btn.pack(side=tk.LEFT, padx=5)

        self.account_tree = tree
        self.selected_item = None

    def on_select(self, event):
        selected_items = self.account_tree.selection()
        if selected_items:
            self.selected_item = selected_items[0]
        else:
            self.selected_item = None

    def get_csv_files(self) -> List[str]:
        try:
            return glob.glob('env_backups/cursor_account_*.csv')
        except Exception as e:
            logger.error(f"获取CSV文件列表失败: {str(e)}")
            return []

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

    def update_csv_file(self, csv_file: str, quota: str, days: str) -> None:
        try:
            rows = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                rows = list(csv_reader)

            quota_found = days_found = False
            for row in rows:
                if len(row) >= 2:
                    if row[0] == 'QUOTA':
                        row[1] = quota
                        quota_found = True
                    elif row[0] == 'DAYS':
                        row[1] = days
                        days_found = True

            if not quota_found:
                rows.append(['QUOTA', quota])
            if not days_found:
                rows.append(['DAYS', days])

            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerows(rows)

            logger.debug(f"已更新CSV文件: {csv_file}")
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

    def show_trial_info(self):
        def get_trial_info(csv_file_path: str, account_data: Dict[str, str]) -> None:
            cookie_str = account_data.get('COOKIES_STR', '')
            if not cookie_str:
                raise ValueError(f"未找到账号 {account_data['EMAIL']} 的Cookie信息")

            def fetch_and_display_info():
                try:
                    logger.debug("开始获取试用信息...")
                    logger.debug(f"获取到的cookie字符串长度: {len(cookie_str) if cookie_str else 0}")

                    if "WorkosCursorSessionToken=" not in cookie_str:
                        logger.debug("Cookie字符串中未包含WorkosCursorSessionToken前缀，正在添加...")
                        cookie_str_with_prefix = f"WorkosCursorSessionToken={cookie_str}"
                    else:
                        cookie_str_with_prefix = cookie_str
                    
                    logger.debug("正在初始化浏览器...")
                    self.registrar = CursorRegistration()
                    self.registrar.headless = True
                    self.registrar.init_browser()
                    logger.debug("浏览器初始化完成")
                    
                    logger.debug("正在获取试用信息...")
                    trial_info = self.registrar.get_trial_info(cookie=cookie_str_with_prefix)
                    quota, days = trial_info[0], trial_info[1]
                    logger.info(f"成功获取试用信息: 额度={quota}, 天数={days}")
                    
                    self.account_tree.set(self.selected_item, '额度', quota)
                    self.account_tree.set(self.selected_item, '剩余天数', f"{days}")
                    
                    try:
                        rows = []
                        with open(csv_file_path, 'r', encoding='utf-8') as f:
                            csv_reader = csv.reader(f)
                            rows = list(csv_reader)

                        quota_found = days_found = False
                        for row in rows:
                            if len(row) >= 2:
                                if row[0] == 'QUOTA':
                                    row[1] = str(quota)
                                    quota_found = True
                                elif row[0] == 'DAYS':
                                    row[1] = str(days)
                                    days_found = True

                        if not quota_found:
                            rows.append(['QUOTA', str(quota)])
                        if not days_found:
                            rows.append(['DAYS', str(days)])

                        with open(csv_file_path, 'w', encoding='utf-8', newline='') as f:
                            csv_writer = csv.writer(f)
                            csv_writer.writerows(rows)
                        
                        logger.debug(f"已更新CSV文件: {csv_file_path}")
                    except Exception as e:
                        logger.error(f"更新CSV文件失败: {str(e)}")
                        raise ValueError(f"更新CSV文件失败: {str(e)}")
                    
                    self.registrar.browser.quit()
                    logger.debug("浏览器已关闭")
                    
                    self.winfo_toplevel().after(0, lambda: UI.show_success(
                        self.winfo_toplevel(),
                        f"账户可用额度: {quota}\n剩余天数: {days}"
                    ))
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"获取试用信息失败: {error_message}")
                    logger.exception("详细错误信息:")
                    self.winfo_toplevel().after(0, lambda: UI.show_error(
                        self.winfo_toplevel(), 
                        "获取账号信息失败", 
                        error_message
                    ))
                finally:
                    if hasattr(self, 'registrar') and self.registrar and self.registrar.browser:
                        self.registrar.browser.quit()

            logger.debug("开始获取信息...")
            threading.Thread(target=fetch_and_display_info, daemon=True).start()

        self.handle_account_action("获取试用信息", get_trial_info)

    def update_auth(self) -> None:
        def update_account_auth(csv_file_path: str, account_data: Dict[str, str]) -> None:
            cookie_str = account_data.get('COOKIES_STR', '')
            if not cookie_str:
                raise ValueError(f"未找到账号 {account_data['EMAIL']} 的Cookie信息")

            if "WorkosCursorSessionToken=" not in cookie_str:
                cookie_str = f"WorkosCursorSessionToken={cookie_str}"

            result = CursorManager().process_cookies(cookie_str)
            if not result.success:
                raise ValueError(result.message)

            UI.show_success(self.winfo_toplevel(), f"账号 {account_data['EMAIL']} 的Cookie已刷新")
            logger.info(f"已刷新账号 {account_data['EMAIL']} 的Cookie")

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

            try:
                os.remove(csv_file_path)
                self.account_tree.delete(self.selected_item)
                logger.info(f"已删除账号: {account_data['DOMAIN']} - {account_data['EMAIL']}")
                UI.show_success(self.winfo_toplevel(), 
                              f"已删除账号: {account_data['DOMAIN']} - {account_data['EMAIL']}")
            except Exception as e:
                raise Exception(f"删除文件失败: {str(e)}")

        self.handle_account_action("删除账号", delete_account_file)

    @error_handler
    def reset_machine_id(self) -> None:
        try:
            result = CursorManager.reset()
            if not result:
                raise Exception(result.message)
            UI.show_success(self.winfo_toplevel(), result.message)
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), "重置机器ID失败", e) 