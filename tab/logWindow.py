import tkinter as tk
from tkinter import ttk, messagebox
from threading import Lock
from datetime import datetime
from collections import deque
from .ui import UI
import io


class LogWindow(tk.Toplevel):
    MAX_BUFFER_SIZE = 1000
    UI_UPDATE_BATCH = 50
    MAX_TEXT_LENGTH = 50000
    
    LOG_COLORS = {
        'DEBUG': UI.COLORS['secondary'],
        'INFO': UI.COLORS['primary'],
        'WARNING': UI.COLORS['warning'],
        'ERROR': UI.COLORS['error'],
        'SUCCESS': UI.COLORS['success']
    }
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.title("日志窗口")
        self.withdraw()
        
        width = 460
        height = 530
        x = parent.winfo_x() + parent.winfo_width()
        y = parent.winfo_y()
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.configure(bg=UI.COLORS['bg'])
        if hasattr(parent, 'attributes') and '-alpha' in parent.attributes():
            self.attributes('-alpha', 0.98)
        
        self.protocol("WM_DELETE_WINDOW", self.withdraw)  
        
        self.show_debug = tk.BooleanVar(value=True)
        self.log_buffer = deque(maxlen=self.MAX_BUFFER_SIZE)
        self.buffer_lock = Lock()
        self.pending_logs = []
        self.update_scheduled = False
        self.text_buffer = io.StringIO()
        
        self.setup_ui()
        self.setup_tags()
    
    def setup_ui(self):
        title_frame = ttk.Frame(self, style='TFrame')
        title_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        debug_checkbox = ttk.Checkbutton(
            title_frame,
            text="调试模式",
            variable=self.show_debug,
            style='TCheckbutton',
            command=self.refresh_logs
        )
        debug_checkbox.pack(side=tk.LEFT, padx=(10, 20))

        clear_button = ttk.Button(
            title_frame,
            text="清除日志",
            command=self.clear_logs,
            style='Custom.TButton',
            width=10
        )
        clear_button.pack(side=tk.RIGHT, padx=(0, 10))

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

    def setup_tags(self):
        for level, color in self.LOG_COLORS.items():
            self.text.tag_configure(level, foreground=color)

    def clear_logs(self):
        with self.buffer_lock:
            self.log_buffer.clear()
            self.pending_logs.clear()
            self.text_buffer = io.StringIO()
        self.text.configure(state='normal')
        self.text.delete(1.0, tk.END)
        self.text.configure(state='disabled')

    def refresh_logs(self):
        with self.buffer_lock:
            logs_to_display = list(self.log_buffer)
        
        if not logs_to_display:
            return
            
        self.text.configure(state='normal')
        self.text.delete(1.0, tk.END)
        show_debug = self.show_debug.get()
        
        for log in logs_to_display:
            if show_debug or log['level'] != 'DEBUG':
                log_line = f"[{log['timestamp']}] [{log['level']}] {log['message']}\n"
                self.text.insert(tk.END, log_line, log['level'])
        
        self.text.see(tk.END)
        self.text.configure(state='disabled')

    def schedule_update(self):
        if not self.update_scheduled:
            self.update_scheduled = True
            self.winfo_toplevel().after(self.UI_UPDATE_BATCH, self.batch_update)

    def batch_update(self):
        self.update_scheduled = False
        
        with self.buffer_lock:
            if not self.pending_logs:
                return
            logs_to_update = self.pending_logs[:]
            self.pending_logs.clear()
        
        if not logs_to_update:
            return
            
        show_debug = self.show_debug.get()
        
        current_length = float(self.text.index(tk.END))
        if current_length > self.MAX_TEXT_LENGTH:
            self.text.configure(state='normal')
            self.text.delete(1.0, f"{current_length - self.MAX_TEXT_LENGTH}.0")
            self.text.configure(state='disabled')
        
        self.text.configure(state='normal')
        for log in logs_to_update:
            if show_debug or log['level'] != 'DEBUG':
                log_line = f"[{log['timestamp']}] [{log['level']}] {log['message']}\n"
                self.text.insert(tk.END, log_line, log['level'])
        
        if float(self.text.yview()[1]) > 0.9:
            self.text.see(tk.END)
        
        self.text.configure(state='disabled')

    def add_log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        level = level.upper()
        log_entry = {
            'message': message,
            'level': level,
            'timestamp': timestamp
        }
        
        with self.buffer_lock:
            self.log_buffer.append(log_entry)
            self.pending_logs.append(log_entry)
            
        self.schedule_update()

    def __del__(self):
        if hasattr(self, 'text_buffer'):
            self.text_buffer.close()

    def show_window(self):
        width = 460
        height = 530
        parent = self.master
        
        parent.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() + 10
        y = parent.winfo_y()
        
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        
        if x + width > screen_width:
            x = screen_width - width
        if y + height > screen_height:
            y = screen_height - height
            
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()
        self.lift()


