WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
WINDOW_TITLE = "Cursor 账号管理器"
BACKUP_DIR = "env_backups"

import os
import sys
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import ttk
from typing import Dict, List, Tuple
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger

from tab import LogWindow, ManageTab, RegisterTab, AboutTab, UI
from tab.configTab import ConfigTab

console_mode = True


@dataclass
class WindowConfig:
    width: int = WINDOW_WIDTH
    height: int = WINDOW_HEIGHT
    title: str = WINDOW_TITLE
    backup_dir: str = BACKUP_DIR
    env_vars: List[Tuple[str, str]] = field(default_factory=lambda: [
        ('DOMAIN', '域名'), ('EMAIL', '邮箱'), ('PASSWORD', '密码')
    ])
    buttons: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("✨ 生成账号", "generate_account"),
        ("🚀 自动注册", "auto_register"),
        ("💾 备份账号", "backup_account")
    ])


class CursorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.config = WindowConfig()
        self.entries: Dict[str, ttk.Entry] = {}
        self.selected_mode = tk.StringVar(value="admin")

        self.root.title(self.config.title)
        UI.center_window(self.root, self.config.width, self.config.height)
        self.root.resizable(False, False)
        self.root.configure(bg=UI.COLORS['bg'])
        if os.name == 'nt':
            self.root.attributes('-alpha', 0.98)

        UI.setup_styles()
        self.setup_ui()

    def setup_ui(self) -> None:
        # 创建主布局框架
        main_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧内容区域
        content_frame = ttk.Frame(main_frame, style='TFrame')
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
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

        config_tab = ConfigTab(notebook)
        notebook.add(config_tab, text="环境配置")

        about_tab = AboutTab(notebook)
        notebook.add(about_tab, text="关于")

        footer_frame = ttk.Frame(content_frame, style='TFrame')
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=6)

        footer = ttk.Label(
            footer_frame,
            text="POWERED BY KTO 仅供学习使用",
            style='Footer.TLabel'
        )
        footer.pack(side=tk.LEFT)

        # 右侧日志区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5", style='Card.TLabelframe')
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 创建日志文本框
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20, width=40)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建日志滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # 设置日志文本框样式
        self.log_text.configure(
            font=('Consolas', 9),
            bg='#1E1E1E',
            fg='#FFFFFF',
            insertbackground='white',
            selectbackground='#264F78',
            selectforeground='white'
        )

        # 设置只读模式
        self.log_text.configure(state='disabled')

    def add_log(self, message: str, level: str = "INFO") -> None:
        self.log_text.configure(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根据日志级别设置不同的颜色
        colors = {
            "DEBUG": "#808080",
            "INFO": "#FFFFFF",
            "WARNING": "#FFA500",
            "ERROR": "#FF4444",
            "SUCCESS": "#00FF00"
        }
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"{message}\n", level)
        
        # 设置标签颜色
        self.log_text.tag_configure("timestamp", foreground="#888888")
        self.log_text.tag_configure(level, foreground=colors.get(level, "#FFFFFF"))
        
        # 自动滚动到底部
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')


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
        setup_logging(app)
        root.mainloop()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        if 'root' in locals():
            UI.show_error(root, "程序启动失败", e)


if __name__ == "__main__":
    main()
