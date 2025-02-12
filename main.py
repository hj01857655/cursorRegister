import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from generate_cursor_account import generate_cursor_account
from reset_ID import CursorResetter
from update_auth import CursorAuthUpdater
from loguru import logger
from dotenv import load_dotenv
from configlog import LogSetup
import os
from functools import wraps

@dataclass
class WindowConfig:
    width: int = 450
    height: int = 360
    title: str = "Cursor账号管理工具"

def error_handler(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            self._handle_error(f"{func.__name__}执行错误", e)
    return wrapper

class CursorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.window_config = WindowConfig()
        self.root.title(self.window_config.title)
        self._configure_window()
        self._init_variables()
        self.setup_ui()

    def _configure_window(self) -> None:
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.window_config.width) // 2
        y = (screen_height - self.window_config.height) // 2
        self.root.geometry(
            f"{self.window_config.width}x{self.window_config.height}+{x}+{y}"
        )
        self.root.resizable(False, False)

    def _init_variables(self) -> None:
        self.email_entry: Optional[ttk.Entry] = None
        self.password_entry: Optional[ttk.Entry] = None
        self.cookie_entry: Optional[ttk.Entry] = None
        self.env_labels: Dict[str, ttk.Label] = {}
        self.main_frame: Optional[ttk.Frame] = None
        self._create_styles()

    def _create_styles(self) -> None:
        style = ttk.Style()
        style.configure('Custom.TButton', padding=(12, 5))
        style.configure('Info.TLabel', font=('Arial', 11))
        style.configure('Error.TLabel', foreground='red')
        style.configure('Success.TLabel', foreground='green')

    def setup_ui(self) -> None:
        self.main_frame = ttk.Frame(self.root, padding="3")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self._create_frames()

    def _create_frames(self) -> None:
        frames = [
            self.create_env_info_frame,
            self.create_account_info_frame,
            self.create_cookie_frame,
            self.create_button_frame
        ]
        for create_frame in frames:
            create_frame()

    def create_env_info_frame(self) -> None:
        env_frame = ttk.LabelFrame(self.main_frame, text="环境变量信息", padding="5")
        env_frame.pack(fill=tk.X, padx=5, pady=(5,2))

        env_vars: list[tuple[str, str]] = [
            ('domain', '域名'),
            ('email', '邮箱'),
            ('password', '密码')
        ]

        for row, (var_name, label_text) in enumerate(env_vars):
            self._create_env_label(env_frame, row, var_name, label_text)

        env_frame.columnconfigure(1, weight=1)

    def _create_env_label(self, frame: ttk.Frame, row: int, var_name: str, label_text: str) -> None:
        ttk.Label(frame, text=f"{label_text}:").grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.env_labels[var_name] = ttk.Label(
            frame, 
            text=os.getenv(var_name.upper(), '未设置'),
            style='Info.TLabel'
        )
        self.env_labels[var_name].grid(
            row=row, column=1, sticky=tk.W, padx=5, pady=2
        )

    def create_account_info_frame(self) -> None:
        info_frame = ttk.LabelFrame(self.main_frame, text="账号信息", padding="5")
        info_frame.pack(fill=tk.X, padx=5, pady=2)

        fields: list[tuple[str, str]] = [
            ('email_entry', '邮箱'),
            ('password_entry', '密码')
        ]

        for row, (field_name, label_text) in enumerate(fields):
            self._create_input_field(info_frame, row, field_name, label_text)

        info_frame.columnconfigure(1, weight=1)

    def _create_input_field(self, frame: ttk.Frame, row: int, field_name: str, label_text: str) -> None:
        ttk.Label(frame, text=f"{label_text}:").grid(
            row=row, column=0, sticky=tk.W, padx=5, pady=2
        )
        entry = ttk.Entry(frame, width=40)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=2)
        setattr(self, field_name, entry)

    @error_handler
    def generate_account(self) -> None:
        email, password = generate_cursor_account()
        self._update_entry_values(email, password)
        logger.success("账号生成成功")
        self.refresh_env_vars()

    def refresh_env_vars(self) -> None:
        load_dotenv(override=True)
        for var_name, label in self.env_labels.items():
            label.config(text=os.getenv(var_name.upper(), '未设置'))

    @error_handler
    def reset_ID(self) -> None:
        resetter = CursorResetter()
        if resetter.reset():
            self._show_success("重置机器码完成")
            self.refresh_env_vars()
        else:
            raise Exception("重置失败")

    @error_handler
    def update_auth(self) -> None:
        cookie_str = self.cookie_entry.get().strip()
        if not self._validate_cookie(cookie_str):
            return

        updater = CursorAuthUpdater()
        updater.update_with_cookie(cookie_str)
        self._show_success("更新登录信息完成")
        self.cookie_entry.delete(0, tk.END)
        self.refresh_env_vars()

    def _validate_cookie(self, cookie_str: str) -> bool:
        if not cookie_str:
            self._show_error("请输入Cookie字符串")
            return False

        if "WorkosCursorSessionToken=" not in cookie_str:
            self._show_error("Cookie字符串格式不正确，必须包含 WorkosCursorSessionToken")
            return False

        return True

    def _handle_error(self, title: str, error: Exception) -> None:
        error_msg = f"{title}: {str(error)}"
        logger.error(error_msg)
        self._show_error(error_msg)

    def _show_error(self, message: str) -> None:
        messagebox.showerror("错误", message)

    def _show_success(self, message: str) -> None:
        logger.info(message)
        messagebox.showinfo("成功", message)

    def create_cookie_frame(self) -> None:
        cookie_frame = ttk.LabelFrame(self.main_frame, text="Cookie设置", padding="5")
        cookie_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(cookie_frame, text="Cookie:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.cookie_entry = ttk.Entry(cookie_frame, width=40)
        self.cookie_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        self.cookie_entry.insert(0, "WorkosCursorSessionToken")

        cookie_frame.columnconfigure(1, weight=1)

    def create_button_frame(self) -> None:
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=5)

        buttons = [
            ("生成账号", self.generate_account),
            ("重置ID", self.reset_ID),
            ("更新账号信息", self.update_auth)
        ]

        container = ttk.Frame(button_frame)
        container.pack(pady=5)

        for col, (text, command) in enumerate(buttons):
            ttk.Button(
                container,
                text=text,
                command=command,
                style='Custom.TButton'
            ).grid(row=0, column=col, padx=5)

        ttk.Label(
            button_frame,
            text="powered by kto 仅供学习使用",
            style='Info.TLabel'
        ).pack(pady=5)

    def _update_entry_values(self, email: str, password: str) -> None:
        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, email)
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, password)

def setup_logging() -> None:
    config_dict = {
        '日志路径': './cursorRegister_log',
        '日志级别': 'DEBUG',
        '颜色化': '开启',
        '日志轮转': '10 MB',
        '日志保留时间': '14 days',
        '压缩方式': 'gz',
        '控制台模式': '关闭',
        '记录日志': '开启'
    }
    LogSetup(config=config_dict)

def main() -> None:
    try:
        load_dotenv()
        setup_logging()
        root = tk.Tk()
        app = CursorApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        messagebox.showerror("错误", f"程序启动失败: {e}")

if __name__ == "__main__":
    main()
