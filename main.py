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
from tab import LogWindow, ManageTab, RegisterTab, UI

console_mode = False


@dataclass
class WindowConfig:
    width: int = 900
    height: int = 560
    title: str = "Cursor注册小助手"
    backup_dir: str = "env_backups"
    env_vars: List[Tuple[str, str]] = field(default_factory=lambda: [
        ('DOMAIN', '域名'), ('EMAIL', '邮箱'), ('PASSWORD', '密码')
    ])
    buttons: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("生成账号", "generate_account"),
        ("自动注册", "auto_register"),
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

        button_commands = {
            'generate_account': self.generate_account,
            'auto_register': self.auto_register,
            'backup_account': self.backup_account
        }

        register_tab = RegisterTab(
            notebook,
            env_vars=self.config.env_vars,
            buttons=self.config.buttons,
            entries=self.entries,
            selected_mode=self.selected_mode,
            button_commands=button_commands
        )
        notebook.add(register_tab, text="账号注册")

        manage_tab = ManageTab(notebook)
        notebook.add(manage_tab, text="账号管理")

        footer = ttk.Label(
            content_frame,
            text="powered by kto 仅供学习使用",
            style='Footer.TLabel'
        )
        footer.pack(side=tk.BOTTOM, pady=2)

        separator = ttk.Separator(main_frame, orient='vertical')
        separator.pack(side=tk.LEFT, fill=tk.Y)

        right_frame = ttk.Frame(main_frame, style='TFrame')
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self.log_window = LogWindow(right_frame)
        self.log_window.pack(fill=tk.BOTH, expand=True)

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
        logger.debug(f"当前环境变量 DOMAIN: {os.getenv('DOMAIN', '未设置')}")
        logger.debug(f"当前环境变量 EMAIL: {os.getenv('EMAIL', '未设置')}")
        logger.debug(f"当前环境变量 PASSWORD: {os.getenv('PASSWORD', '未设置')}")
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
    def auto_register(self) -> None:
        mode = self.selected_mode.get()
        self._register_account(mode=mode)

    def _register_account(self, mode: str) -> None:
        self._save_env_vars()
        load_dotenv(override=True)

        def create_dialog(message: str) -> bool:
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

        def update_ui_warning(message):
            UI.show_warning(self.root, message)

        def _terminate_registration():
            if self.registrar and self.registrar.browser:
                self.registrar.browser.quit()
            self.root.after(0, lambda: update_ui_warning("注册流程已被终止"))

        def register_thread():
            is_terminated = False

            try:
                self.registrar = CursorRegistration()
                logger.debug("正在启动注册流程...")

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
                        self.root.after(0, lambda: [
                            self.entries['EMAIL'].delete(0, tk.END),
                            self.entries['EMAIL'].insert(0, os.getenv('EMAIL', '未获取到')),
                            self.entries['PASSWORD'].delete(0, tk.END),
                            self.entries['PASSWORD'].insert(0, os.getenv('PASSWORD', '未获取到')),
                            self.entries['cookie'].delete(0, tk.END),
                            self.entries['cookie'].insert(0, f"WorkosCursorSessionToken={token}"),
                            UI.show_success(self.root, "自动注册成功，账号信息已填入")
                        ])
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
        
            env_vars = {
                "DOMAIN": os.getenv("DOMAIN", ""),
                "EMAIL": os.getenv("EMAIL", ""),
                "PASSWORD": os.getenv("PASSWORD", ""),
                "COOKIES_STR": os.getenv("COOKIES_STR", ""),
                "API_KEY": os.getenv("API_KEY", ""),
                "MOE_MAIL_URL": os.getenv("MOE_MAIL_URL", "")
            }

          
            if not any(env_vars.values()):
                raise ValueError("未找到任何账号信息，请先注册或更新账号")

      
            backup_dir = Path(self.config.backup_dir)
            backup_dir.mkdir(exist_ok=True)

       
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"cursor_account_{timestamp}.csv"

        
            with open(backup_path, 'w', encoding='utf-8', newline='') as f:
                f.write("variable,value\n")
                for key, value in env_vars.items():
                    if value:  
                        f.write(f"{key},{value}\n")

            logger.info(f"账号信息已备份到: {backup_path}")
            UI.show_success(self.root, f"账号备份成功\n保存位置: {backup_path}")

        except Exception as e:
            logger.error(f"账号备份失败: {str(e)}")
            UI.show_error(self.root, "账号备份失败", e)


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
