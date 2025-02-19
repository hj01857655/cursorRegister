ABOUT_TAB_HEIGHT = 300
VERSION = "版本: 0.1.6"

import tkinter as tk
import webbrowser
from tkinter import ttk

version = VERSION


class AboutTab(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.configure(height=ABOUT_TAB_HEIGHT)
        self.pack_propagate(False)
        self.setup_ui()

    def open_github(self, event):
        webbrowser.open("https://github.com/Ktovoz/cursorRegister")

    def create_separator(self, container):
        separator = ttk.Separator(container, orient='horizontal')
        separator.pack(fill=tk.X, pady=2, padx=40)

    def setup_ui(self):
        main_container = ttk.Frame(self, style='TFrame')
        main_container.pack(expand=True, fill=tk.BOTH, padx=40, pady=5)

        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X)

        version_info = ttk.Label(
            title_frame,
            text=version,
            style='TLabel',
            font=('Microsoft YaHei UI', 10),
            foreground='#5f6368'
        )
        version_info.pack()

        self.create_separator(main_container)

        info_frame = ttk.Frame(main_container)
        info_frame.pack(fill=tk.X)

        author_info = ttk.Label(
            info_frame,
            text="作者: kto",
            style='TLabel',
            font=('Microsoft YaHei UI', 10),
            foreground='#202124'
        )
        author_info.pack(pady=(0, 1))

        description = ttk.Label(
            info_frame,
            text="这是一个用于自动注册和管理Cursor账号的工具。",
            style='TLabel',
            wraplength=400,
            justify='center',
            font=('Microsoft YaHei UI', 10),
            foreground='#202124'
        )
        description.pack(pady=(0, 1))

        description2 = ttk.Label(
            info_frame,
            text="仅供学习和研究使用，请勿用于商业用途。",
            style='TLabel',
            wraplength=400,
            justify='center',
            font=('Microsoft YaHei UI', 10),
            foreground='#202124'
        )
        description2.pack(pady=(0, 1))

        github_info = ttk.Label(
            info_frame,
            text="项目地址: https://github.com/Ktovoz/cursorRegister",
            style='TLabel',
            cursor="hand2",
            foreground='#1a73e8',
            font=('Microsoft YaHei UI', 10, 'underline')
        )
        github_info.pack(pady=(0, 1))
        github_info.bind("<Button-1>", self.open_github)

        self.create_separator(main_container)

        disclaimer_frame = ttk.Frame(main_container)
        disclaimer_frame.pack(fill=tk.X)

        disclaimer_title = ttk.Label(
            disclaimer_frame,
            text="免责声明",
            style='TLabel',
            font=('Microsoft YaHei UI', 10, 'bold'),
            foreground='#5f6368'
        )
        disclaimer_title.pack(pady=(0, 1))

        disclaimer_text = ttk.Label(
            disclaimer_frame,
            text="本工具仅供学习交流使用，",
            style='TLabel',
            wraplength=400,
            justify='center',
            font=('Microsoft YaHei UI', 10),
            foreground='#5f6368'
        )
        disclaimer_text.pack(pady=(0, 1))

        disclaimer_text2_frame = ttk.Frame(disclaimer_frame)
        disclaimer_text2_frame.pack(fill=tk.X)

        disclaimer_text2 = ttk.Label(
            disclaimer_text2_frame,
            text="使用本工具所产生的一切后果由使用者自行承担。",
            style='TLabel',
            wraplength=400,
            justify='center',
            font=('Microsoft YaHei UI', 10),
            foreground='#5f6368'
        )
        disclaimer_text2.pack(pady=(0, 1))

        license_info = ttk.Label(
            disclaimer_frame,
            text="本项目采用 CC BY-NC-ND 4.0 许可证",
            style='TLabel',
            font=('Microsoft YaHei UI', 10),
            foreground='#5f6368',
            justify='center'
        )
        license_info.pack(pady=(0, 1))

        copyright_info = ttk.Label(
            main_container,
            text="© 2025 仅供学习交流",
            style='Footer.TLabel',
            font=('Microsoft YaHei UI', 9),
            foreground='#80868b'
        )
        copyright_info.pack(side=tk.BOTTOM, pady=2)
