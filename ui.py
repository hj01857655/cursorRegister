import os
import tkinter as tk
from tkinter import ttk, messagebox
from loguru import logger
from datetime import datetime
from typing import Dict, List, Tuple, Callable


class UI:
    FONT = ('Microsoft YaHei UI', 10)
    BUTTON_PADDING = (8, 4)
    BUTTON_GRID_PADDING = 4
    BUTTON_GRID_MARGIN = 3
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
                        padding=UI.BUTTON_PADDING,
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

        style.configure('TRadiobutton',
                        font=UI.FONT,
                        background=UI.COLORS['bg'],
                        foreground=UI.COLORS['label_fg']
                        )

        style.map('TRadiobutton',
                  background=[('active', UI.COLORS['bg'])],
                  foreground=[('active', UI.COLORS['primary'])]
                  )

        style.configure('TCheckbutton',
                        font=UI.FONT,
                        background=UI.COLORS['bg'],
                        foreground=UI.COLORS['label_fg']
                        )

        style.map('TCheckbutton',
                  background=[('active', UI.COLORS['bg'])],
                  foreground=[('active', UI.COLORS['primary'])]
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
            row = i // 2
            col = i % 2
            btn = ttk.Button(
                button_frame,
                text=text,
                command=self.button_commands[command],
                style='Custom.TButton',
                width=8
            )
            btn.grid(
                row=row,
                column=col,
                padx=3,
                pady=2,
                sticky='nsew'
            )

        for i in range(2):
            button_frame.grid_columnconfigure(i, weight=1)


class ManageTab(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.setup_ui()

    def setup_ui(self):
        accounts_frame = UI.create_labeled_frame(self, "已保存账号")
        
        columns = ('域名', '邮箱', '到期时间', '状态')
        tree = ttk.Treeview(accounts_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(accounts_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        button_frame = ttk.Frame(self, style='TFrame')
        button_frame.pack(fill=tk.X, pady=(8, 0))

        buttons = [
            ("导入账号", self.import_account),
            ("导出账号", self.export_account),
            ("删除账号", self.delete_account),
            ("刷新列表", self.refresh_list)
        ]

        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(
                button_frame,
                text=text,
                command=command,
                style='Custom.TButton',
                width=10
            )
            btn.pack(side=tk.LEFT, padx=5)

        self.account_tree = tree

    def import_account(self):
        pass

    def export_account(self):
        pass

    def delete_account(self):
        pass

    def refresh_list(self):
        pass 