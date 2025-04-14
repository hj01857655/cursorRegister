WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 520
WINDOW_TITLE = "Cursor注册小助手"
BACKUP_DIR = "env_backups"
CONTENT_RATIO = 0.5  # 对半分

import os
import sys
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import ttk
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from loguru import logger

from tab import ManageTab, RegisterTab, AboutTab, ConfigTab, UI
from tab.logWindow import MAX_BUFFER_SIZE, UI_UPDATE_BATCH, MAX_TEXT_LENGTH

console_mode = False



@dataclass
class WindowConfig:
    width: int = WINDOW_WIDTH
    height: int = WINDOW_HEIGHT
    title: str = WINDOW_TITLE
    backup_dir: str = BACKUP_DIR
    env_vars: List[Tuple[str, str]] = field(default_factory=lambda: [
        ('EMAIL', '邮箱'), ('PASSWORD', '密码')
    ])
    buttons: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("生成账号", "generate_account"),
        ("全自动注册", "auto_register"),
        ("备份账号", "backup_account")
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
            
        # 计算有效内容区域宽度（减去内边距）
        padding = 20  # 左右各10像素的padding
        self.effective_width = self.config.width - padding
        # 计算分隔位置
        self.sash_position = int(self.effective_width * CONTENT_RATIO)
        # 计算两侧面板宽度
        self.content_width = int(self.effective_width * CONTENT_RATIO)
        self.log_width = self.effective_width - self.content_width

        UI.setup_styles()
        self.setup_ui()
        
        # 窗口显示后立即设置分隔线位置
        self.root.update_idletasks()
        self.set_sash_position()
        
        # 绑定窗口大小变化和分隔线移动事件
        self.root.bind("<Configure>", self.on_window_configure)
        self.paned_window.bind("<ButtonRelease-1>", self.on_sash_moved)

    def set_sash_position(self):
        """设置分隔线位置"""
        try:
            self.paned_window.sashpos(0, self.sash_position)
        except:
            # 如果设置失败，可能是窗口还未完全初始化
            self.root.after(100, self.set_sash_position)
            
    def on_window_configure(self, event=None):
        """窗口配置改变时调用"""
        if event and event.widget == self.root:
            # 重新设置分隔线位置
            self.set_sash_position()
            
    def on_sash_moved(self, event=None):
        """用户移动分隔线后重置到预设位置"""
        self.root.after(10, self.set_sash_position)  # 短暂延迟后重置分隔线位置

    def setup_ui(self) -> None:
        self.main_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建分隔窗口
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # 左侧内容区域
        self.content_frame = ttk.Frame(self.paned_window, style='TFrame', width=self.content_width)
        
        # 强制框架保持固定宽度
        self.content_frame.pack_propagate(False)

        title_label = ttk.Label(
            self.content_frame,
            text=self.config.title,
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 6))

        notebook = ttk.Notebook(self.content_frame)
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
        notebook.add(config_tab, text="系统配置")

        about_tab = AboutTab(notebook)
        notebook.add(about_tab, text="关于")

        footer_frame = ttk.Frame(self.content_frame, style='TFrame')
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=6)

        footer = ttk.Label(
            footer_frame,
            text="POWERED BY KTO 仅供学习使用",
            style='Footer.TLabel'
        )
        footer.pack(side=tk.LEFT)

        # 添加左侧内容区域
        self.paned_window.add(self.content_frame, weight=1)
        
        # 设置日志面板
        self.setup_log_panel()

    def setup_log_panel(self):
        # 右侧日志面板
        self.log_frame = ttk.Frame(self.paned_window, style='TFrame', width=self.log_width)
        # 强制框架保持固定宽度
        self.log_frame.pack_propagate(False)
        
        title_frame = ttk.Frame(self.log_frame, style='TFrame')
        title_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        log_title = ttk.Label(
            title_frame,
            text="操作日志",
            style='Title.TLabel'
        )
        log_title.pack(side=tk.LEFT, padx=5)
        
        # 设置调试模式默认开启
        self.show_debug = tk.BooleanVar(value=True)
        debug_checkbox = ttk.Checkbutton(
            title_frame,
            text="调试模式",
            variable=self.show_debug,
            style='TCheckbutton',
            command=self.refresh_logs
        )
        debug_checkbox.pack(side=tk.LEFT, padx=(5, 5))

        clear_button = ttk.Button(
            title_frame,
            text="清除日志",
            command=self.clear_logs,
            style='Custom.TButton',
            width=6
        )
        clear_button.pack(side=tk.RIGHT, padx=(0, 5))

        text_container = ttk.Frame(self.log_frame, style='TFrame')
        text_container.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            text_container,
            wrap=tk.WORD,
            width=25,
            font=UI.FONT,
            bg=UI.COLORS['card_bg'],
            fg=UI.COLORS['label_fg'],
            relief='flat',
            padx=5,
            pady=5
        )
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_text.configure(state='disabled')
        self.setup_log_tags()
        
        self.log_buffer = []
        self.pending_logs = []
        self.update_scheduled = False
        
        # 添加右侧日志面板
        self.paned_window.add(self.log_frame, weight=1)

    def setup_log_tags(self):
        log_colors = {
            'DEBUG': UI.COLORS['secondary'],
            'INFO': UI.COLORS['primary'],
            'WARNING': UI.COLORS['warning'],
            'ERROR': UI.COLORS['error'],
            'SUCCESS': UI.COLORS['success']
        }
        for level, color in log_colors.items():
            self.log_text.tag_configure(level, foreground=color)

    def refresh_logs(self):
        logs_to_display = list(self.log_buffer)
        if not logs_to_display:
            return

        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        show_debug = self.show_debug.get()

        for log in logs_to_display:
            if show_debug or log['level'] != 'DEBUG':
                log_line = f"[{log['timestamp']}] [{log['level']}] {log['message']}\n"
                self.log_text.insert(tk.END, log_line, log['level'])

        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def schedule_update(self):
        if not self.update_scheduled:
            self.update_scheduled = True
            self.root.after(UI_UPDATE_BATCH, self.batch_update)

    def batch_update(self):
        self.update_scheduled = False

        if not self.pending_logs:
            return
        logs_to_update = self.pending_logs[:]
        self.pending_logs.clear()

        if not logs_to_update:
            return

        show_debug = self.show_debug.get()

        current_length = float(self.log_text.index(tk.END))
        if current_length > MAX_TEXT_LENGTH:
            self.log_text.configure(state='normal')
            self.log_text.delete(1.0, f"{current_length - MAX_TEXT_LENGTH}.0")
            self.log_text.configure(state='disabled')

        self.log_text.configure(state='normal')
        for log in logs_to_update:
            if show_debug or log['level'] != 'DEBUG':
                log_line = f"[{log['timestamp']}] [{log['level']}] {log['message']}\n"
                self.log_text.insert(tk.END, log_line, log['level'])

        if float(self.log_text.yview()[1]) > 0.9:
            self.log_text.see(tk.END)

        self.log_text.configure(state='disabled')

    def clear_logs(self):
        self.log_buffer.clear()
        self.pending_logs.clear()
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        
    def add_log(self, message: str, level: str = "INFO"):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        level = level.upper()
        log_entry = {
            'message': message,
            'level': level,
            'timestamp': timestamp
        }

        self.log_buffer.append(log_entry)
        if len(self.log_buffer) > MAX_BUFFER_SIZE:
            self.log_buffer.pop(0)
            
        self.pending_logs.append(log_entry)
        self.schedule_update()


def setup_logging(app=None) -> None:
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

    if app:
        def gui_sink(message):
            record = message.record
            level = record["level"].name
            text = record["message"]
            app.add_log(text, level)

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
