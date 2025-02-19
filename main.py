import os
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from loguru import logger

from registerAc import CursorRegistration
from utils import Utils, Result, error_handler, CursorManager
from tab import LogWindow, ManageTab, RegisterTab, AboutTab, UI

console_mode = False


@dataclass
class WindowConfig:
    width: int = 460
    height: int = 560
    title: str = "Cursor注册小助手"
    backup_dir: str = "env_backups"
    env_vars: List[Tuple[str, str]] = field(default_factory=lambda: [
        ('DOMAIN', '域名'), ('EMAIL', '邮箱'), ('PASSWORD', '密码')
    ])
    buttons: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("生成账号", "generate_account"),
        ("注册账号", "auto_register"),
        ("备份账号", "backup_account")
    ])


class CursorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.config = WindowConfig()
        self.entries: Dict[str, ttk.Entry] = {}
        self.selected_mode = tk.StringVar(value="semi")

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
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 0))
        content_frame.configure(width=450)
        content_frame.pack_propagate(False)

        title_label = ttk.Label(
            content_frame,
            text=self.config.title,
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 6))

        notebook = ttk.Notebook(content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 2))

        register_tab = RegisterTab(
            notebook,
            env_vars=self.config.env_vars,
            buttons=self.config.buttons,
            entries=self.entries,
            selected_mode=self.selected_mode,
            button_commands={}
        )
        notebook.add(register_tab, text="账号注册")

        manage_tab = ManageTab(notebook)
        notebook.add(manage_tab, text="账号管理")

        about_tab = AboutTab(notebook)
        notebook.add(about_tab, text="关于")

        footer_frame = ttk.Frame(content_frame, style='TFrame')
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

        footer = ttk.Label(
            footer_frame,
            text="powered by kto 仅供学习使用",
            style='Footer.TLabel'
        )
        footer.pack(side=tk.LEFT)


        self.log_window_var = tk.BooleanVar(value=False)
        log_checkbox = ttk.Checkbutton(
            footer_frame,
            text="显示日志",
            variable=self.log_window_var,
            style='TCheckbutton',
            command=self.toggle_log_window
        )
        log_checkbox.pack(side=tk.RIGHT)


        self.log_window = LogWindow(self.root)

    def toggle_log_window(self):
        if self.log_window_var.get():
            self.log_window.show_window()
        else:
            self.log_window.withdraw()


def setup_logging(log_window=None) -> None:
    logger.remove()
    
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

    if console_mode:
        logger.add(
            sink=sys.stderr,
            colorize=True,
            enqueue=True,
            backtrace=True,
            diagnose=True,
            level="DEBUG"
        )
    
    if log_window:
        def gui_sink(message):
            record = message.record
            level = record["level"].name
            text = record["message"]
            log_window.add_log(text, level)

        logger.add(
            sink=gui_sink,
            format="{message}",
            level="DEBUG",
            enqueue=True
        )


def main() -> None:
    try:
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        env_path = os.path.join(base_path, '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        
        root = tk.Tk()
        app = CursorApp(root)
        setup_logging(app.log_window)
        root.mainloop()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        if 'root' in locals():
            UI.show_error(root, "程序启动失败", e)


if __name__ == "__main__":
    main()
