import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Callable, List, Tuple
from dataclasses import dataclass
from cursor_account_generator import generate_cursor_account
from cursor_id_resetter import CursorResetter
from cursor_auth_updater import CursorAuthUpdater
from loguru import logger
from dotenv import load_dotenv
from configlog import LogSetup
import os
from cursor_utils import (
    PathManager, FileManager, Result, UIManager, 
    StyleManager, MessageManager, error_handler
)

@dataclass
class WindowConfig:
    width: int = 480
    height: int = 500
    title: str = "Cursor账号管理工具"
    backup_dir: str = "env_backups"
    max_backups: int = 10
    env_vars: List[Tuple[str, str]] = None
    buttons: List[Tuple[str, str]] = None

    def __post_init__(self):
        self.env_vars = [
            ('domain', '域名'), 
            ('email', '邮箱'), 
            ('password', '密码')
        ]
        self.buttons = [
            ("生成账号", "generate_account"),
            ("重置ID", "reset_ID"),
            ("更新账号信息", "update_auth")
        ]

class CursorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.window_config = WindowConfig()
        self.root.title(self.window_config.title)
        self._configure_window()
        self._init_variables()
        self.setup_ui()

    def _configure_window(self) -> None:
        UIManager.center_window(self.root, self.window_config.width, self.window_config.height)
        self.root.resizable(False, False)
        self.root.configure(bg='#FFFFFF')
        if os.name == 'nt':
            self.root.attributes('-alpha', 0.98)
        
    def _init_variables(self) -> None:
        self.entries: Dict[str, ttk.Entry] = {}
        self.env_labels: Dict[str, ttk.Label] = {}
        self.main_frame: Optional[ttk.Frame] = None
        StyleManager.setup_styles()

    def setup_ui(self) -> None:
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self._create_frames()

    def _create_frames(self) -> None:
        env_frame = UIManager.create_labeled_frame(self.main_frame, "环境变量信息")
        for row, (var_name, label_text) in enumerate(self.window_config.env_vars):
            self._create_env_label(env_frame, row, var_name, label_text)

        info_frame = UIManager.create_labeled_frame(self.main_frame, "账号信息")
        for row, (var_name, label_text) in enumerate(self.window_config.env_vars[1:]):
            entry = UIManager.create_labeled_entry(info_frame, label_text, row)
            entry.bind('<FocusIn>', lambda e, entry=entry: entry.configure(style='TEntry'))
            entry.bind('<FocusOut>', lambda e, entry=entry: entry.configure(style='TEntry') if not entry.get().strip() else None)
            self.entries[var_name] = entry

        cookie_frame = UIManager.create_labeled_frame(self.main_frame, "Cookie设置")
        self.entries['cookie'] = UIManager.create_labeled_entry(cookie_frame, "Cookie", 0)
        self.entries['cookie'].insert(0, "WorkosCursorSessionToken")

        self._create_button_frame()

    def _create_env_label(self, frame: ttk.Frame, row: int, var_name: str, label_text: str) -> None:
        ttk.Label(frame, text=f"{label_text}:", style='Info.TLabel').grid(
            row=row, column=0, sticky=tk.W, padx=8, pady=4
        )
        self.env_labels[var_name] = ttk.Label(
            frame, 
            text=os.getenv(var_name.upper(), '未设置'),
            style='Info.TLabel'
        )
        self.env_labels[var_name].grid(
            row=row, column=1, sticky=tk.W, padx=8, pady=4
        )

    def _create_button_frame(self) -> None:
        button_frame = ttk.Frame(self.main_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=(15,0))

        container = ttk.Frame(button_frame, style='TFrame')
        container.pack()

        for col, (text, command) in enumerate(self.window_config.buttons):
            btn = ttk.Button(
                container,
                text=text,
                command=getattr(self, command),
                style='Custom.TButton'
            )
            btn.grid(row=0, column=col, padx=10)

        footer_frame = ttk.Frame(button_frame, style='TFrame')
        footer_frame.pack(fill=tk.X, pady=(10,5))
        ttk.Label(
            footer_frame,
            text="powered by kto 仅供学习使用",
            style='Footer.TLabel'
        ).pack()

    @error_handler
    def generate_account(self) -> None:
        result = generate_cursor_account()
        if isinstance(result, Result):
            if result:
                email, password = result.data
                self._update_entry_values(email, password)
                MessageManager.show_success(self.root, "账号生成成功")
                self.refresh_env_vars()
            else:
                raise RuntimeError(result.message)
        else:
            email, password = result
            self._update_entry_values(email, password)
            MessageManager.show_success(self.root, "账号生成成功")
            self.refresh_env_vars()

    def refresh_env_vars(self) -> None:
        load_dotenv(override=True)
        for var_name, label in self.env_labels.items():
            label.config(text=os.getenv(var_name.upper(), '未设置'))

    @error_handler
    def reset_ID(self) -> None:
        resetter = CursorResetter()
        result = resetter.reset()
        if result:
            MessageManager.show_success(self.root, result.message)
            self.refresh_env_vars()
        else:
            raise Exception(result.message)

    def backup_env_file(self) -> None:
        env_path = PathManager.get_env_path()
        if not env_path.exists():
            raise Exception(f"未找到.env文件: {env_path}")

        backup_dir = Path(self.window_config.backup_dir)
        result = FileManager.backup_file(env_path, backup_dir, '.env', self.window_config.max_backups)
        if not result:
            raise Exception(result.message)

    @error_handler
    def update_auth(self) -> None:
        cookie_str = self.entries['cookie'].get().strip()
        if not self._validate_cookie(cookie_str):
            return

        self.backup_env_file()
        updater = CursorAuthUpdater()
        result = updater.process_cookies(cookie_str)
        if result:
            MessageManager.show_success(self.root, result.message)
            self.entries['cookie'].delete(0, tk.END)
            self.refresh_env_vars()
        else:
            raise Exception(result.message)

    def _validate_cookie(self, cookie_str: str) -> bool:
        if not cookie_str:
            MessageManager.show_warning(self.root, "请输入Cookie字符串")
            return False

        if "WorkosCursorSessionToken=" not in cookie_str:
            MessageManager.show_warning(self.root, "Cookie字符串格式不正确，必须包含 WorkosCursorSessionToken")
            return False

        return True

    def _update_entry_values(self, email: str, password: str) -> None:
        self.entries['email'].delete(0, tk.END)
        self.entries['email'].insert(0, email)
        self.entries['password'].delete(0, tk.END)
        self.entries['password'].insert(0, password)

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
        env_path = PathManager.get_env_path()
        load_dotenv(dotenv_path=env_path)
        setup_logging()
        root = tk.Tk()
        app = CursorApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        MessageManager.show_error(root, "程序启动失败", e)

if __name__ == "__main__":
    main()
