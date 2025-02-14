import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from cursor_account_generator import generate_cursor_account
from cursor_id_resetter import reset
from cursor_auth_updater import process_cookies
from loguru import logger
from dotenv import load_dotenv
import os
from pathlib import Path
from cursor_utils import Utils, Result, error_handler
import threading
from cursor_registerAc import CursorRegistration, RegistrationInterrupted


class UI:
    FONT = ('Microsoft YaHei UI', 10)
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
            padding=(12, 6),
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

@dataclass
class WindowConfig:
    width: int = 450
    height: int = 500
    title: str = "Cursor账号管理工具"
    backup_dir: str = "env_backups"
    max_backups: int = 10
    env_vars: List[Tuple[str, str]] = field(default_factory=lambda: [
        ('DOMAIN', '域名'), ('EMAIL', '邮箱'), ('PASSWORD', '密码')
    ])
    buttons: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("生成账号", "generate_account"),
        ("自动注册", "auto_register"),
        ("重置ID", "reset_ID"),
        ("更新账号信息", "update_auth"),
        ("账号试用信息", "show_trial_info")
    ])

class CursorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.config = WindowConfig()
        self.entries: Dict[str, ttk.Entry] = {}

        self.root.title(self.config.title)
        UI.center_window(self.root, self.config.width, self.config.height)
        self.root.resizable(False, False)
        self.root.configure(bg=UI.COLORS['bg'])
        if os.name == 'nt':
            self.root.attributes('-alpha', 0.98)

        UI.setup_styles()
        self.setup_ui()

    def setup_ui(self) -> None:
        main_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        content_frame = ttk.Frame(main_frame, style='TFrame')
        content_frame.pack(fill=tk.BOTH, expand=False)

        title_label = ttk.Label(
            content_frame,
            text=self.config.title,
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 6))

        account_frame = UI.create_labeled_frame(content_frame, "账号信息")
        for row, (var_name, label_text) in enumerate(self.config.env_vars):
            entry = UI.create_labeled_entry(account_frame, label_text, row)
            if os.getenv(var_name):
                entry.insert(0, os.getenv(var_name))
            self.entries[var_name] = entry

        cookie_frame = UI.create_labeled_frame(content_frame, "Cookie设置")
        self.entries['cookie'] = UI.create_labeled_entry(cookie_frame, "Cookie", 0)
        if os.getenv('COOKIES_STR'):
            self.entries['cookie'].insert(0, os.getenv('COOKIES_STR'))
        else:
            self.entries['cookie'].insert(0, "WorkosCursorSessionToken")

        button_frame = ttk.Frame(content_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=(8, 0))

        for i, (text, command) in enumerate(self.config.buttons):
            row = i // 2
            col = i % 2
            btn = ttk.Button(
                button_frame,
                text=text,
                command=getattr(self, command),
                style='Custom.TButton'
            )
            btn.grid(row=row, column=col, padx=4, pady=3, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        footer = ttk.Label(
            main_frame,
            text="powered by kto 仅供学习使用",
            style='Footer.TLabel'
        )
        footer.pack(side=tk.BOTTOM, pady=2)

    def _save_env_vars(self, updates: Dict[str, str] = None) -> None:
        if not updates:
            updates = {
                var_name: value.strip()
                for var_name, _ in self.config.env_vars
                if (value := self.entries[var_name].get().strip())
            }

        if updates and not Utils.update_env_vars(updates):
            UI.show_warning(self.root, "保存环境变量失败")

    def backup_env_file(self) -> None:
        env_path = Utils.get_path('env')
        if not env_path.exists():
            raise Exception(f"未找到.env文件: {env_path}")

        backup_dir = Path(self.config.backup_dir)
        if not Utils.backup_file(env_path, backup_dir, '.env', self.config.max_backups):
            raise Exception("备份文件失败")

    @error_handler
    def generate_account(self) -> None:

        if domain := self.entries['DOMAIN'].get().strip():
            if not Utils.update_env_vars({'DOMAIN': domain}):
                raise RuntimeError("保存域名失败")
            load_dotenv(override=True)

        if not (result := generate_cursor_account()):
            raise RuntimeError(result.message)

        email, password = result.data if isinstance(result, Result) else result
        for key, value in {'EMAIL': email, 'PASSWORD': password}.items():
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, value)

    @error_handler
    def reset_ID(self) -> None:
        if not (result := reset()):
            raise Exception(result.message)
        UI.show_success(self.root, result.message)
        self._save_env_vars()

    @error_handler
    def update_auth(self) -> None:
        cookie_str = self.entries['cookie'].get().strip()
        if not cookie_str:
            UI.show_warning(self.root, "请输入Cookie字符串")
            return

        if "WorkosCursorSessionToken=" not in cookie_str:
            UI.show_warning(self.root, "Cookie字符串格式不正确，必须包含 WorkosCursorSessionToken")
            return

        self.backup_env_file()
        if not (result := process_cookies(cookie_str)):
            raise Exception(result.message)

        UI.show_success(self.root, result.message)
        self.entries['cookie'].delete(0, tk.END)
        self._save_env_vars()

    @error_handler
    def auto_register(self) -> None:
        self._save_env_vars()
        load_dotenv(override=True)

        def create_dialog(message: str) -> bool:
            dialog = tk.Toplevel(self.root)
            dialog.title("等待确认")
            dialog.geometry("250x180")
            UI.center_window(dialog, 300, 180)
            dialog.transient(self.root)
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
                raise RegistrationInterrupted()

        def update_ui_success(token):
            self.entries['cookie'].delete(0, tk.END)
            self.entries['cookie'].insert(0, f"WorkosCursorSessionToken={token}")
            UI.show_success(self.root, "自动注册成功，Token已填入")
            self.backup_env_file()

        def update_ui_warning(message):
            UI.show_warning(self.root, message)

        def register_thread():
            registrar = None
            try:
                registrar = CursorRegistration()
                if token := registrar.register(create_dialog):
                    self.root.after(0, lambda: update_ui_success(token))
                else:
                    self.root.after(0, lambda: update_ui_warning("注册流程未完成"))
            except RegistrationInterrupted:
                self.root.after(0, lambda: update_ui_warning("注册流程已被终止"))
            except Exception as e:
                logger.error(f"注册过程发生错误: {str(e)}")
                self.root.after(0, lambda: update_ui_warning(f"注册失败: {str(e)}"))
            finally:
                if registrar and registrar.browser:
                    registrar.browser.quit()

        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and child['text'] == "自动注册":
                        child.configure(state='disabled')

        thread = threading.Thread(target=register_thread, daemon=True)
        thread.start()


        def restore_button():
            thread.join()
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and child['text'] == "自动注册":
                            self.root.after(0, lambda: child.configure(state='normal'))

        threading.Thread(target=restore_button, daemon=True).start()

    @error_handler
    def show_trial_info(self) -> None:
        try:
            def get_trial_info():
                pass
            self._save_env_vars()
            load_dotenv(override=True)
            thread = threading.Thread(target=get_trial_info, daemon=True)
            thread.start()
        except Exception as e:
            UI.show_error(self.root, "获取账号信息失败", e)

def setup_logging() -> None:
    logger.remove()
    logger.add(
        sink=Path("./cursorRegister_log") / "{time:YYYY-MM-DD_HH}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} |{level:8}| - {message}",
        rotation="10 MB",
        retention="14 days",
        compression="gz",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        level="DEBUG"
    )

def main() -> None:
    try:
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        env_path = os.path.join(base_path, '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        setup_logging()
        root = tk.Tk()
        app = CursorApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        if 'root' in locals():
            UI.show_error(root, "程序启动失败", e)

if __name__ == "__main__":
    main()
