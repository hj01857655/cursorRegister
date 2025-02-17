import tkinter as tk
from tkinter import ttk, messagebox

from datetime import datetime
from .ui import UI


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




