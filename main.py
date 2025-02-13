import sys
import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from cursor_account_generator import generate_cursor_account
from cursor_id_resetter import reset
from cursor_auth_updater import process_cookies
from loguru import logger
from dotenv import load_dotenv
import os
from pathlib import Path
from cursor_utils import Utils, UI, Result, error_handler

@dataclass
class WindowConfig:
    width: int = 480
    height: int = 385
    title: str = "Cursor账号管理工具"
    backup_dir: str = "env_backups"
    max_backups: int = 10
    env_vars: List[Tuple[str, str]] = field(default_factory=lambda: [
        ('DOMAIN', '域名'), ('EMAIL', '邮箱'), ('PASSWORD', '密码')
    ])
    buttons: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("生成账号", "generate_account"),
        ("重置ID", "reset_ID"),
        ("更新账号信息", "update_auth")
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
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        account_frame = UI.create_labeled_frame(main_frame, "账号信息")
        for row, (var_name, label_text) in enumerate(self.config.env_vars):
            entry = UI.create_labeled_entry(account_frame, label_text, row)
            entry.bind('<FocusIn>', lambda e, entry=entry: entry.configure(style='TEntry'))
            entry.bind('<FocusOut>', lambda e, entry=entry: entry.configure(style='TEntry') if not entry.get().strip() else None)
            if os.getenv(var_name):
                entry.insert(0, os.getenv(var_name))
            self.entries[var_name] = entry

        cookie_frame = UI.create_labeled_frame(main_frame, "Cookie设置")
        self.entries['cookie'] = UI.create_labeled_entry(cookie_frame, "Cookie", 0)
        self.entries['cookie'].insert(0, "WorkosCursorSessionToken")

        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=(15,0))
        
        container = ttk.Frame(button_frame, style='TFrame')
        container.pack(pady=(0,5))
        
        for col, (text, command) in enumerate(self.config.buttons):
            ttk.Button(
                container,
                text=text,
                command=getattr(self, command),
                style='Custom.TButton'
            ).grid(row=0, column=col, padx=10)

        ttk.Label(
            button_frame,
            text="powered by kto 仅供学习使用",
            style='Footer.TLabel'
        ).pack(pady=(0,5))

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
        self.backup_env_file()
        
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
            
        UI.show_success(self.root, "账号生成成功")
        self._save_env_vars()

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
    logger.add(
        sink=sys.stderr,
        colorize=True,
        enqueue=True,
        backtrace=True,
        diagnose=True,
        level="DEBUG"
    )

def main() -> None:
    try:
        load_dotenv(dotenv_path=Utils.get_path('env'))
        setup_logging()
        root = tk.Tk()
        app = CursorApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        UI.show_error(root, "程序启动失败", e)

if __name__ == "__main__":
    main()
