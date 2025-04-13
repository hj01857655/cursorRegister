import tkinter as tk
from tkinter import ttk, messagebox

from loguru import logger


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

        style.configure('TNotebook',
                        background=UI.COLORS['bg'],
                        borderwidth=0)

        style.configure('TNotebook.Tab',
                        padding=(15, 5),
                        font=(UI.FONT[0], 10),
                        background=UI.COLORS['bg'],
                        foreground=UI.COLORS['label_fg'])

        style.map('TNotebook.Tab',
                  background=[('selected', UI.COLORS['primary']),
                              ('active', UI.COLORS['hover'])],
                  foreground=[('selected', 'black'),
                              ('active', 'black')])

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
                        padding=5,
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
        frame.grid(row=row, column=0, columnspan=2, sticky='ew', padx=6, pady=6)

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

    @staticmethod
    def show_loading(window: tk.Tk, title: str, message: str) -> tk.Toplevel:
        loading_dialog = tk.Toplevel(window)
        loading_dialog.title(title)
        loading_dialog.transient(window)
        loading_dialog.grab_set()
    
        dialog_width = 300
        dialog_height = 100
        UI.center_window(loading_dialog, dialog_width, dialog_height)
        
    
        loading_dialog.configure(bg=UI.COLORS['bg'])
        loading_dialog.resizable(False, False)
        
      
        message_label = ttk.Label(
            loading_dialog,
            text=message,
            style='TLabel',
            wraplength=250,
            justify='center'
        )
        message_label.pack(pady=20)
        
     
        progress = ttk.Progressbar(
            loading_dialog,
            mode='indeterminate',
            style='TProgressbar'
        )
        progress.pack(fill=tk.X, padx=20, pady=(0, 20))
        progress.start(10)
        

        window.loading_dialog = loading_dialog
        return loading_dialog

    @staticmethod
    def close_loading(window: tk.Tk) -> None:
        if hasattr(window, 'loading_dialog'):
            try:
                window.loading_dialog.destroy()
                delattr(window, 'loading_dialog')
            except Exception:
                pass

    @staticmethod
    def create_tooltip(widget, text: str) -> None:
        """为控件创建悬停提示信息"""
        tooltip = tk.Toplevel(widget, bg=UI.COLORS['primary'])
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        
        # 创建提示文本标签
        label = tk.Label(
            tooltip, 
            text=text, 
            bg=UI.COLORS['primary'],
            fg='white',
            padx=8,
            pady=4,
            wraplength=300,
            font=(UI.FONT[0], 9)
        )
        label.pack()
        
        # 显示和隐藏提示的函数
        def show_tooltip(event=None):
            x, y, _, _ = widget.bbox('insert')
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()
            
        def hide_tooltip(event=None):
            tooltip.withdraw()
            
        # 绑定事件
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
