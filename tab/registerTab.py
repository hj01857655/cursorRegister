import os
import tkinter as tk
from tkinter import ttk, messagebox
from loguru import logger
from datetime import datetime
from typing import Dict, List, Tuple, Callable
from pathlib import Path
import threading
from dotenv import load_dotenv

from .ui import UI
from utils import Utils, Result, error_handler, CursorManager
from registerAc import CursorRegistration


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
        self.registrar = None
        self.setup_ui()

    def setup_ui(self):
        account_frame = UI.create_labeled_frame(self, "账号信息")
        for row, (var_name, label_text) in enumerate(self.env_vars):
            entry = UI.create_labeled_entry(account_frame, label_text, row)
            if os.getenv(var_name):
                entry.insert(0, os.getenv(var_name))
            self.entries[var_name] = entry

        self.entries['cookie'] = UI.create_labeled_entry(account_frame, "Cookie", len(self.env_vars))
        if os.getenv('COOKIES_STR'):
            self.entries['cookie'].insert(0, os.getenv('COOKIES_STR'))
        else:
            self.entries['cookie'].insert(0, "WorkosCursorSessionToken")

        radio_frame = ttk.Frame(account_frame, style='TFrame')
        radio_frame.grid(row=len(self.env_vars) + 1, column=0, columnspan=2, sticky='w', pady=(8, 0))

        mode_label = ttk.Label(radio_frame, text="注册模式:", style='TLabel')
        mode_label.pack(side=tk.LEFT, padx=(3, 8))

        modes = [
            ("人工验证", "semi"),
            ("自动验证", "auto"),
            ("全自动", "admin")
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
            btn = ttk.Button(
                button_frame,
                text=text,
                command=getattr(self, command),
                style='Custom.TButton',
                width=10
            )
            btn.pack(fill=tk.X, padx=2, pady=3)

    def _save_env_vars(self, updates: Dict[str, str] = None) -> None:
        if not updates:
            updates = {
                var_name: value.strip()
                for var_name, _ in self.env_vars
                if (value := self.entries[var_name].get().strip())
            }

        if updates and not Utils.update_env_vars(updates):
            UI.show_warning(self, "保存环境变量失败")

    @error_handler
    def generate_account(self) -> None:
        logger.debug(f"当前环境变量 DOMAIN: {os.getenv('DOMAIN', '未设置')}")
        logger.debug(f"当前环境变量 EMAIL: {os.getenv('EMAIL', '未设置')}")
        logger.debug(f"当前环境变量 PASSWORD: {os.getenv('PASSWORD', '未设置')}")
        if domain := self.entries['DOMAIN'].get().strip():
            if not Utils.update_env_vars({'DOMAIN': domain}):
                raise RuntimeError("保存域名失败")
            load_dotenv(override=True)

        if not (result := CursorManager.generate_cursor_account()):
            raise RuntimeError(result.message)

        email, password = result.data if isinstance(result, Result) else result
        for key, value in {'EMAIL': email, 'PASSWORD': password}.items():
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, value)

    @error_handler
    def auto_register(self) -> None:
        mode = self.selected_mode.get()
        self._register_account(mode=mode)

    def _register_account(self, mode: str) -> None:
        self._save_env_vars()
        load_dotenv(override=True)

        def create_dialog(message: str) -> bool:
            dialog = tk.Toplevel(self)
            dialog.title("等待确认")
            dialog.geometry("250x180")
            UI.center_window(dialog, 300, 180)
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

        def update_ui_warning(message):
            UI.show_warning(self, message)

        def _terminate_registration():
            if self.registrar and self.registrar.browser:
                self.registrar.browser.quit()
            self.after(0, lambda: update_ui_warning("注册流程已被终止"))

        def register_thread():
            is_terminated = False

            try:
                self.registrar = CursorRegistration()
                logger.debug("正在启动注册流程...")

                if not (register_method := {
                    "auto": self.registrar.auto_register,
                    "semi": self.registrar.semi_auto_register,
                    "admin": self.registrar.admin_auto_register
                }.get(mode)):
                    raise ValueError(f"未知的注册模式: {mode}")

                if is_terminated:
                    return

                if token := register_method(create_dialog):
                    if not is_terminated:
                        self.after(0, lambda: [
                            self.entries['EMAIL'].delete(0, tk.END),
                            self.entries['EMAIL'].insert(0, os.getenv('EMAIL', '未获取到')),
                            self.entries['PASSWORD'].delete(0, tk.END),
                            self.entries['PASSWORD'].insert(0, os.getenv('PASSWORD', '未获取到')),
                            self.entries['cookie'].delete(0, tk.END),
                            self.entries['cookie'].insert(0, f"WorkosCursorSessionToken={token}"),
                            UI.show_success(self, "自动注册成功，账号信息已填入")
                        ])
                        threading.Thread(target=self.backup_account, daemon=True).start()
                elif not is_terminated:
                    self.after(0, lambda: update_ui_warning("注册流程未完成"))

            except Exception as e:
                error_msg = str(e)
                if error_msg == "用户终止了注册流程":
                    self._terminate_registration()
                else:
                    logger.error(f"注册过程发生错误: {error_msg}")
                    if not is_terminated:
                        self.after(0, lambda: update_ui_warning(f"注册失败: {error_msg}"))
            finally:
                if self.registrar and self.registrar.browser:
                    self.registrar.browser.quit()

        def find_and_update_button(state: str):
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and child['text'] == button_text:
                            self.after(0, lambda: child.configure(state=state))

        button_text = "自动注册"
        find_and_update_button('disabled')

        thread = threading.Thread(target=register_thread, daemon=True)
        thread.start()

        def restore_button():
            thread.join()
            find_and_update_button('normal')

        threading.Thread(target=restore_button, daemon=True).start()

    @error_handler
    def backup_account(self) -> None:
        try:
            if cookie_value := self.entries['cookie'].get().strip():
                if not Utils.update_env_vars({'COOKIES_STR': cookie_value}):
                    raise RuntimeError("更新COOKIES_STR环境变量失败")
                load_dotenv(override=True)
        
            env_vars = {
                "DOMAIN": os.getenv("DOMAIN", ""),
                "EMAIL": os.getenv("EMAIL", ""),
                "PASSWORD": os.getenv("PASSWORD", ""),
                "COOKIES_STR": os.getenv("COOKIES_STR", ""),
                "API_KEY": os.getenv("API_KEY", ""),
                "MOE_MAIL_URL": os.getenv("MOE_MAIL_URL", "")
            }

            if not any(env_vars.values()):
                raise ValueError("未找到任何账号信息，请先注册或更新账号")

            backup_dir = Path("env_backups")
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"cursor_account_{timestamp}.csv"

            with open(backup_path, 'w', encoding='utf-8', newline='') as f:
                f.write("variable,value\n")
                for key, value in env_vars.items():
                    if value:  
                        f.write(f"{key},{value}\n")

            logger.info(f"账号信息已备份到: {backup_path}")
            UI.show_success(self, f"账号备份成功\n保存位置: {backup_path}")

        except Exception as e:
            logger.error(f"账号备份失败: {str(e)}")
            UI.show_error(self, "账号备份失败", e)


