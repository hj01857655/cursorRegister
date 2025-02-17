import os
import tkinter as tk
from tkinter import ttk, messagebox
from loguru import logger
from datetime import datetime
from typing import Dict, List, Tuple, Callable
from .ui import UI


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
        self.setup_ui()

    def setup_ui(self):
        account_frame = UI.create_labeled_frame(self, "账号信息")
        for row, (var_name, label_text) in enumerate(self.env_vars):
            entry = UI.create_labeled_entry(account_frame, label_text, row)
            if os.getenv(var_name):
                entry.insert(0, os.getenv(var_name))
            self.entries[var_name] = entry

        cookie_frame = UI.create_labeled_frame(self, "Cookie设置")
        self.entries['cookie'] = UI.create_labeled_entry(cookie_frame, "Cookie", 0)
        if os.getenv('COOKIES_STR'):
            self.entries['cookie'].insert(0, os.getenv('COOKIES_STR'))
        else:
            self.entries['cookie'].insert(0, "WorkosCursorSessionToken")

        radio_frame = ttk.Frame(self, style='TFrame')
        radio_frame.pack(fill=tk.X, pady=(8, 0))

        mode_label = ttk.Label(radio_frame, text="注册模式:", style='TLabel')
        mode_label.pack(side=tk.LEFT, padx=(3, 8))

        modes = [
            ("人工过验证", "semi"),
            ("自动过验证", "auto"),
            ("全自动注册", "admin")
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
                command=self.button_commands[command],
                style='Custom.TButton',
                width=10
            )
            btn.pack(fill=tk.X, padx=2, pady=3)


