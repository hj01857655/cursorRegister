import os
import sys
import threading
import tkinter as tk
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from loguru import logger

from registerAc import CursorRegistration
from utils import Utils, Result, error_handler, CursorManager

console_mode = False


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

    @staticmethod
    def create_loading_dialog(window: tk.Tk, message: str, on_close=None) -> tk.Toplevel:
        dialog = tk.Toplevel(window)
        dialog.title("处理中")
        dialog.geometry("250x100")
        UI.center_window(dialog, 250, 100)
        dialog.transient(window)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg=UI.COLORS['bg'])

        if on_close:
            dialog.protocol("WM_DELETE_WINDOW", on_close)

        frame = ttk.Frame(dialog, style='TFrame')
        frame.pack(expand=True)

        ttk.Label(
            frame,
            text=message,
            wraplength=200,
            justify="center",
            style="TLabel"
        ).pack(pady=10)

        return dialog


@dataclass
class WindowConfig:
    width: int = 450
    height: int = 520
    title: str = "Cursor注册小助手"
    backup_dir: str = "env_backups"
    env_vars: List[Tuple[str, str]] = field(default_factory=lambda: [
        ('DOMAIN', '域名'), ('EMAIL', '邮箱'), ('PASSWORD', '密码')
    ])
    buttons: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("生成账号", "generate_account"),
        ("自动注册", "auto_register"),
        ("重置机器ID", "reset_ID"),
        ("刷新cookie", "update_auth"),
        ("获取试用信息", "show_trial_info"),
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
        self.registrar = None

    def setup_ui(self) -> None:
        main_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        content_frame = ttk.Frame(main_frame, style='TFrame')
        content_frame.pack(fill=tk.BOTH, expand=False)

        title_label = ttk.Label(
            content_frame,
            text=self.config.title,
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 6))

        account_frame = UI.create_labeled_frame(content_frame, "账号信息")
        for row, (var_name, label_text) in enumerate(self.config.env_vars):
            entry = UI.create_labeled_entry(account_frame, label_text, row)
            if os.getenv(var_name):
                entry.insert(0, os.getenv(var_name))
            self.entries[var_name] = entry

        cookie_frame = UI.create_labeled_frame(content_frame, "Cookie设置")
        self.entries['cookie'] = UI.create_labeled_entry(cookie_frame, "Cookie", 0)
        if os.getenv('COOKIES_STR'):
            self.entries['cookie'].insert(0, os.getenv('COOKIES_STR'))
        else:
            self.entries['cookie'].insert(0, "WorkosCursorSessionToken")

        radio_frame = ttk.Frame(content_frame, style='TFrame')
        radio_frame.pack(fill=tk.X, pady=(8, 0))

        mode_label = ttk.Label(radio_frame, text="注册模式:", style='TLabel')
        mode_label.pack(side=tk.LEFT, padx=(3, 8))

        semi_radio = ttk.Radiobutton(
            radio_frame,
            text="人工过验证",
            variable=self.selected_mode,
            value="semi",
            style='TRadiobutton'
        )
        semi_radio.pack(side=tk.LEFT, padx=10)

        auto_radio = ttk.Radiobutton(
            radio_frame,
            text="自动过验证",
            variable=self.selected_mode,
            value="auto",
            style='TRadiobutton'
        )
        auto_radio.pack(side=tk.LEFT, padx=10)

        admin_radio = ttk.Radiobutton(
            radio_frame,
            text="全自动注册",
            variable=self.selected_mode,
            value="admin",
            style='TRadiobutton'
        )
        admin_radio.pack(side=tk.LEFT, padx=10)

        button_frame = ttk.Frame(content_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=(8, 0))

        for i, (text, command) in enumerate(self.config.buttons):
            row = i // 2
            col = i % 2
            btn = ttk.Button(
                button_frame,
                text=text,
                command=getattr(self, command),
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

        footer = ttk.Label(
            main_frame,
            text="powered by kto 仅供学习使用",
            style='Footer.TLabel'
        )
        footer.pack(side=tk.BOTTOM, pady=2)

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
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f".env_backup_{timestamp}"

        import shutil
        shutil.copy2(env_path, backup_path)

    @error_handler
    def generate_account(self) -> None:
        logger.info(f"当前环境变量 DOMAIN: {os.getenv('DOMAIN', '未设置')}")
        logger.info(f"当前环境变量 EMAIL: {os.getenv('EMAIL', '未设置')}")
        logger.info(f"当前环境变量 PASSWORD: {os.getenv('PASSWORD', '未设置')}")
        if domain := self.entries['DOMAIN'].get().strip():
            if not Utils.update_env_vars({'DOMAIN': domain}):
                raise RuntimeError("保存域名失败")
            load_dotenv(override=True)

        if not (result := CursorManager.generate_cursor_account()):
            raise RuntimeError(result.message)

        email, password = result.data if isinstance(result, Result) else result
        for key, value in {'EMAIL': email, 'PASSWORD': password}.items():
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, value)

    @error_handler
    def reset_ID(self) -> None:
        if not (result := CursorManager.reset()):
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
        result = CursorManager().process_cookies(cookie_str)
        if not result.success:
            UI.show_warning(self.root, result.message)
            return

        UI.show_success(self.root, result.message)
        self._save_env_vars()

    @error_handler
    def auto_register(self) -> None:
        mode = self.selected_mode.get()
        self._register_account(mode=mode)

    def _register_account(self, mode: str) -> None:
        self._save_env_vars()
        load_dotenv(override=True)
        loading_dialog = None

        def create_dialog(message: str) -> bool:
            nonlocal loading_dialog
            if loading_dialog:
                loading_dialog.destroy()
                loading_dialog = None
            dialog = tk.Toplevel(self.root)
            dialog.title("等待确认")
            dialog.geometry("250x180")
            UI.center_window(dialog, 300, 180)
            dialog.transient(self.root)
            dialog.grab_set()
            ttk.Label(
                dialog,
                text=message,
                wraplength=250,
                justify="center",
                style="TLabel"
            ).pack(pady=20)

            button_frame = ttk.Frame(dialog, style='TFrame')
            button_frame.pack(pady=10)

            result = {'continue': True}

            def on_continue():
                dialog.destroy()
                nonlocal loading_dialog
                loading_dialog = UI.create_loading_dialog(self.root, "正在处理，请稍候...")

            def on_terminate():
                result['continue'] = False
                dialog.destroy()

            ttk.Button(
                button_frame,
                text="继续",
                command=on_continue,
                style="Custom.TButton"
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                button_frame,
                text="终止",
                command=on_terminate,
                style="Custom.TButton"
            ).pack(side=tk.LEFT, padx=5)

            dialog.wait_window()
            if not result['continue']:
                raise Exception("用户终止了注册流程")

        def update_ui_success(token):
            nonlocal loading_dialog
            if loading_dialog:
                loading_dialog.destroy()
            self.entries['cookie'].delete(0, tk.END)
            self.entries['cookie'].insert(0, f"WorkosCursorSessionToken={token}")
            UI.show_success(self.root, "自动注册成功，Token已填入")

        def update_ui_warning(message):
            nonlocal loading_dialog
            if loading_dialog:
                loading_dialog.destroy()
            UI.show_warning(self.root, message)

        def _terminate_registration():
            nonlocal loading_dialog
            if loading_dialog:
                loading_dialog.destroy()
                loading_dialog = None
            if self.registrar and self.registrar.browser:
                self.registrar.browser.quit()
            self.root.after(0, lambda: update_ui_warning("注册流程已被终止"))

        def register_thread():
            nonlocal loading_dialog
            is_terminated = False

            def on_loading_dialog_close():
                nonlocal is_terminated
                is_terminated = True
                _terminate_registration()

            try:
                self.registrar = CursorRegistration()
                loading_dialog = UI.create_loading_dialog(
                    self.root,
                    "正在启动注册流程，请稍候...",
                    on_close=on_loading_dialog_close
                )

                if not (register_method := {
                    "auto": self.registrar.auto_register,
                    "semi": self.registrar.semi_auto_register,
                    "admin": self.registrar.admin_auto_register
                }.get(mode)):
                    raise ValueError(f"未知的注册模式: {mode}")

                if is_terminated:
                    return

                if token := register_method(create_dialog):
                    if not is_terminated:
                        self.root.after(0, lambda: update_ui_success(token))
                elif not is_terminated:
                    self.root.after(0, lambda: update_ui_warning("注册流程未完成"))

            except Exception as e:
                error_msg = str(e)
                if error_msg == "用户终止了注册流程":
                    self._terminate_registration()
                else:
                    logger.error(f"注册过程发生错误: {error_msg}")
                    if not is_terminated:
                        self.root.after(0, lambda: update_ui_warning(f"注册失败: {error_msg}"))
            finally:
                if self.registrar and self.registrar.browser:
                    self.registrar.browser.quit()

        def find_and_update_button(state: str):
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and child['text'] == button_text:
                            self.root.after(0, lambda: child.configure(state=state))

        button_text = "自动注册"
        find_and_update_button('disabled')

        thread = threading.Thread(target=register_thread, daemon=True)
        thread.start()

        def restore_button():
            thread.join()
            find_and_update_button('normal')

        threading.Thread(target=restore_button, daemon=True).start()

    @error_handler
    def backup_account(self) -> None:
        try:
            self.backup_env_file()
            UI.show_success(self.root, "账号备份成功")
        except Exception as e:
            UI.show_error(self.root, "账号备份失败", e)

    @error_handler
    def show_trial_info(self) -> None:
        loading_dialog = None

        def fetch_and_display_info():
            nonlocal loading_dialog
            try:
                cookie_str = self.entries['cookie'].get().strip() or os.getenv('COOKIES_STR', '').strip()
                if not cookie_str:
                    raise ValueError("未找到Cookie信息，请先更新账号信息")

                if "WorkosCursorSessionToken=" not in cookie_str:
                    cookie_str = f"WorkosCursorSessionToken={cookie_str}"
                self.registrar = CursorRegistration()
                self.registrar.init_browser()
                trial_info = self.registrar.get_trial_info(cookie=cookie_str)
                self.root.after(0, lambda: UI.show_success(
                    self.root,
                    f"账户可用额度: {trial_info.usage}\n试用天数: {trial_info.days}"
                ))
            except Exception as e:
                error_message = str(e)
                self.root.after(0, lambda: UI.show_error(self.root, "获取账号信息失败", error_message))
            finally:
                if loading_dialog:
                    self.root.after(0, loading_dialog.destroy)

        loading_dialog = UI.create_loading_dialog(self.root, "正在获取账号信息，请稍候...")
        threading.Thread(target=fetch_and_display_info, daemon=True).start()


def setup_logging() -> None:
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


def main() -> None:
    try:
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        env_path = os.path.join(base_path, '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        setup_logging()
        root = tk.Tk()
        app = CursorApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        if 'root' in locals():
            UI.show_error(root, "程序启动失败", e)


if __name__ == "__main__":
    main()
