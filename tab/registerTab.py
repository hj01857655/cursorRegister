DIALOG_WIDTH = 250
DIALOG_HEIGHT = 180
DIALOG_CENTER_WIDTH = 300
DIALOG_CENTER_HEIGHT = 180
BUTTON_WIDTH = 10

import os
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk
from typing import Dict, List, Tuple, Callable

from dotenv import load_dotenv
from loguru import logger

from registerAc import CursorRegistration
from utils import Utils, Result, error_handler, CursorManager, ConfigManager
from .ui import UI


class RegisterTab(ttk.Frame):
    def __init__(self, parent, env_vars: List[Tuple[str, str]], buttons: List[Tuple[str, str]],
                 entries: Dict[str, ttk.Entry], selected_mode: tk.StringVar,
                 button_commands: Dict[str, Callable], **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.env_vars = [(var_name, label_text) for var_name, label_text in env_vars if var_name != 'DOMAIN']
        self.buttons = buttons
        self.entries = entries
        self.selected_mode = selected_mode
        self.button_commands = button_commands
        self.registrar = None
        self.setup_ui()

    def setup_ui(self):
        account_frame = UI.create_labeled_frame(self, "账号信息")
        # 定义输入框的提示信息
        tooltips = {
            'EMAIL': '用于登录Cursor的邮箱账号',
            'PASSWORD': '用于登录Cursor的密码',
            'cookie': 'Cursor登录的会话Cookie信息'
        }
        
        # 添加邮箱和密码输入框
        for row, (var_name, label_text) in enumerate(self.env_vars):
            entry = UI.create_labeled_entry(account_frame, label_text, row)
            if os.getenv(var_name):
                entry.insert(0, os.getenv(var_name))
            self.entries[var_name] = entry
            # 添加提示信息
            if var_name in tooltips:
                UI.create_tooltip(entry, tooltips[var_name])

        # 添加Cookie输入框，标签改为"Cookies"
        self.entries['cookie'] = UI.create_labeled_entry(account_frame, "Cookies", len(self.env_vars))
        if os.getenv('COOKIES_STR'):
            self.entries['cookie'].insert(0, os.getenv('COOKIES_STR'))
        else:
            self.entries['cookie'].insert(0, "WorkosCursorSessionToken")
        # 添加提示信息
        UI.create_tooltip(self.entries['cookie'], tooltips['cookie'])

        radio_frame = ttk.Frame(account_frame, style='TFrame')
        radio_frame.grid(row=len(self.env_vars) + 1, column=0, columnspan=2, sticky='w', pady=(8, 0))

        mode_label = ttk.Label(radio_frame, text="注册模式:", style='TLabel')
        mode_label.pack(side=tk.LEFT, padx=(3, 8))

        modes = [
            ("全自动", "admin"),
            ("自动验证", "auto"),
            ("人工验证", "semi")
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
        button_frame.pack(pady=(8, 0))


        inner_button_frame = ttk.Frame(button_frame, style='TFrame')
        inner_button_frame.pack(expand=True)

        for i, (text, command) in enumerate(self.buttons):
            btn = ttk.Button(
                inner_button_frame,
                text=text,
                command=getattr(self, command),
                style='Custom.TButton',
                width=10
            )
            btn.pack(side=tk.LEFT, padx=10)

    def _save_env_vars(self, updates: Dict[str, str] = None) -> None:
        if not updates:
            updates = {
                var_name: value.strip()
                for var_name, _ in self.env_vars
                if (value := self.entries[var_name].get().strip())
            }
            
            domain_result = ConfigManager.get_config('DOMAIN')
            if domain_result.success and domain_result.data:
                domain = domain_result.data
                logger.debug(f"从ConfigManager获取到域名: {domain}")
                updates['DOMAIN'] = domain
            else:
                logger.warning("未能从ConfigManager获取域名配置")

        if updates and not Utils.update_env_vars(updates):
            UI.show_warning(self, "保存环境变量失败")

    @error_handler
    def generate_account(self) -> None:
        def generate_thread():
            try:
                self.winfo_toplevel().after(0, lambda: UI.show_loading(
                    self.winfo_toplevel(),
                    "生成账号",
                    "正在生成账号信息，请稍候..."
                ))
                
                # 记录当前环境变量状态
                logger.debug(f"当前环境变量 DOMAIN: {os.getenv('DOMAIN', '未设置')}")
                logger.debug(f"当前环境变量 EMAIL: {os.getenv('EMAIL', '未设置')}")
                logger.debug(f"当前环境变量 PASSWORD: {os.getenv('PASSWORD', '未设置')}")
                
                # 从ConfigManager获取域名配置
                domain_result = ConfigManager.get_config('DOMAIN')
                if domain_result.success and domain_result.data:
                    domain = domain_result.data
                    logger.debug(f"从ConfigManager获取到域名: {domain}")
                    
                    # 更新环境变量中的DOMAIN，但不显示在界面上
                    if not Utils.update_env_vars({'DOMAIN': domain}):
                        raise RuntimeError("保存域名失败")
                    load_dotenv(override=True)
                else:
                    logger.warning("未能获取到域名，将使用默认域名")

                if not (result := CursorManager.generate_cursor_account()):
                    raise RuntimeError(result.message)

                email, password = result.data if isinstance(result, Result) else result
                
                self.winfo_toplevel().after(0, lambda: [
                    self.entries[key].delete(0, tk.END) or 
                    self.entries[key].insert(0, value) 
                    for key, value in {'EMAIL': email, 'PASSWORD': password}.items()
                ])

                self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                self.winfo_toplevel().after(0, lambda: UI.show_success(
                    self.winfo_toplevel(),
                    "账号生成成功"
                ))

            except Exception as e:
                self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                self.winfo_toplevel().after(0, lambda: UI.show_error(
                    self.winfo_toplevel(),
                    "生成账号失败",
                    str(e)
                ))

        threading.Thread(target=generate_thread, daemon=True).start()
    
    #自动注册
    @error_handler
    def auto_register(self) -> None:
        mode = self.selected_mode.get()
        
        # 先获取ConfigManager中的域名配置
        domain_result = ConfigManager.get_config('DOMAIN')
        if domain_result.success and domain_result.data:
            domain = domain_result.data
            logger.debug(f"从ConfigManager获取到域名: {domain}")
            # 更新环境变量中的DOMAIN
            os.environ['DOMAIN'] = domain
        
        # 保存所有环境变量，包括从ConfigManager获取的域名
        self._save_env_vars()
        load_dotenv(override=True)
        #创建对话框
        def create_dialog(message: str) -> bool:
            dialog = tk.Toplevel(self)
            dialog.title("等待确认")
            dialog.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}")
            UI.center_window(dialog, DIALOG_CENTER_WIDTH, DIALOG_CENTER_HEIGHT)
            dialog.transient(self)
            dialog.grab_set()
            ttk.Label(
                dialog,
                text=message,
                wraplength=250,
                justify="center",
                style="TLabel"
            ).pack(pady=20)

            button_frame = ttk.Frame(dialog, style='TFrame')
            button_frame.pack(pady=10)

            result = {'continue': True}

            def on_continue():
                dialog.destroy()

            def on_terminate():
                result['continue'] = False
                dialog.destroy()

            ttk.Button(
                button_frame,
                text="继续",
                command=on_continue,
                style="Custom.TButton"
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                button_frame,
                text="终止",
                command=on_terminate,
                style="Custom.TButton"
            ).pack(side=tk.LEFT, padx=5)

            dialog.wait_window()
            if not result['continue']:
                raise Exception("用户终止了注册流程")

        def register_thread():
            try:
                self.winfo_toplevel().after(0, lambda: UI.show_loading(
                    self.winfo_toplevel(),
                    "全自动注册",
                    "正在执行全自动注册流程，无需手动干预，请稍候..."
                ))

                self.registrar = CursorRegistration()
                logger.debug("正在启动注册流程...")

                if not (register_method := {
                    "auto": self.registrar.auto_register,
                    "semi": self.registrar.semi_auto_register,
                    "admin": self.registrar.admin_auto_register
                }.get(mode)):
                    raise ValueError(f"未知的注册模式: {mode}")

                if token := register_method(create_dialog):
                    cookies_value = f"WorkosCursorSessionToken={token}"
                    
                    # 更新输入框
                    self.winfo_toplevel().after(0, lambda: [
                        self.entries['EMAIL'].delete(0, tk.END),
                        self.entries['EMAIL'].insert(0, os.getenv('EMAIL', '未获取到')),
                        self.entries['PASSWORD'].delete(0, tk.END),
                        self.entries['PASSWORD'].insert(0, os.getenv('PASSWORD', '未获取到')),
                        self.entries['cookie'].delete(0, tk.END),
                        self.entries['cookie'].insert(0, cookies_value)
                    ])
                    
                    # 更新环境变量中的COOKIES_STR
                    Utils.update_env_vars({'COOKIES_STR': cookies_value})
                    load_dotenv(override=True)
                    logger.debug("已更新COOKIES_STR环境变量")
                    
                    # 同时更新ConfigManager中的配置
                    config = ConfigManager.load_config()
                    if config.success:
                        updated_config = config.data
                        updated_config['COOKIES_STR'] = cookies_value
                        ConfigManager.save_config(updated_config)
                        logger.debug("已同步更新ConfigManager中的COOKIES_STR配置")
                    
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_success(
                        self.winfo_toplevel(),
                        "全自动注册成功，账号信息已填入"
                    ))
                    
                    threading.Thread(target=self.backup_account, daemon=True).start()
                else:
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_warning(
                        self.winfo_toplevel(),
                        "注册流程未完成"
                    ))

            except Exception as e:
                error_msg = str(e)
                if error_msg == "用户终止了注册流程":
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_warning(
                        self.winfo_toplevel(),
                        "注册流程已被终止"
                    ))
                else:
                    logger.error(f"注册过程发生错误: {error_msg}")
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "注册失败",
                        error_msg
                    ))
            finally:
                if self.registrar and self.registrar.browser:
                    self.registrar.browser.quit()

        def find_and_update_button(state: str):
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and child['text'] == "全自动注册":
                            self.after(0, lambda: child.configure(state=state))

        find_and_update_button('disabled')
        thread = threading.Thread(target=register_thread, daemon=True)
        thread.start()

        def restore_button():
            thread.join()
            find_and_update_button('normal')

        threading.Thread(target=restore_button, daemon=True).start()
    
    #备份账号
    @error_handler
    def backup_account(self) -> None:
        def backup_thread():
            try:
                self.winfo_toplevel().after(0, lambda: UI.show_loading(
                    self.winfo_toplevel(),
                    "备份账号",
                    "正在备份账号信息，请稍候..."
                ))

                if cookie_value := self.entries['cookie'].get().strip():
                    if not Utils.update_env_vars({'COOKIES_STR': cookie_value}):
                        raise RuntimeError("更新COOKIES_STR环境变量失败")
                    load_dotenv(override=True)
                
                # 只备份账号相关信息
                account_vars = {
                    "EMAIL": os.getenv("EMAIL", ""),
                    "PASSWORD": os.getenv("PASSWORD", ""),
                    "COOKIES_STR": os.getenv("COOKIES_STR", "")
                }

                if not any(account_vars.values()):
                    raise ValueError("未找到任何账号信息，请先注册或更新账号")

                backup_dir = Path("env_backups")
                backup_dir.mkdir(exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"cursor_account_{timestamp}.csv"

                with open(backup_path, 'w', encoding='utf-8', newline='') as f:
                    f.write("variable,value\n")
                    for key, value in account_vars.items():
                        if value:
                            f.write(f"{key},{value}\n")

                self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                logger.info(f"账号信息已备份到: {backup_path}")
                self.winfo_toplevel().after(0, lambda: UI.show_success(
                    self.winfo_toplevel(),
                    f"账号备份成功\n保存位置: {backup_path}"
                ))

            except Exception as e:
                self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                logger.error(f"账号备份失败: {str(e)}")
                self.winfo_toplevel().after(0, lambda: UI.show_error(
                    self.winfo_toplevel(),
                    "账号备份失败",
                    str(e)
                ))

        threading.Thread(target=backup_thread, daemon=True).start()
