import os
import sys
import json
import shutil
import random
import string
import sqlite3
import subprocess
import ctypes
from pathlib import Path
from typing import Any, Dict, Union, TypeVar, Generic, Callable
from datetime import datetime
from loguru import logger
from functools import wraps
import tkinter as tk
from tkinter import ttk, messagebox

T = TypeVar('T')

class Result(Generic[T]):
    def __init__(self, success: bool, data: T = None, message: str = ""):
        self.success = success
        self.data = data
        self.message = message

    @classmethod
    def ok(cls, data: T = None, message: str = "操作成功") -> 'Result[T]':
        return cls(True, data, message)

    @classmethod
    def fail(cls, message: str = "操作失败") -> 'Result[T]':
        return cls(False, None, message)

    def __bool__(self) -> bool:
        return self.success

class PathManager:
    @staticmethod
    def get_base_path() -> Path:
        return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

    @staticmethod
    def get_env_path() -> Path:
        return PathManager.get_base_path() / '.env'

    @staticmethod
    def get_appdata_path() -> Path:
        if not (appdata := os.getenv("APPDATA")):
            raise EnvironmentError("APPDATA 环境变量未设置")
        return Path(appdata)

    @staticmethod
    def get_cursor_path() -> Path:
        return PathManager.get_appdata_path() / 'Cursor/User/globalStorage'

    @staticmethod
    def ensure_path(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

class EnvManager:
    @staticmethod
    def update_env_vars(updates: Dict[str, str]) -> Result[None]:
        try:
            env_path = PathManager.get_env_path()
            content = env_path.read_text(encoding='utf-8').splitlines() if env_path.exists() else []
            
            updated_content = []
            updated_keys = set()
            
            for line in content:
                key = line.split('=')[0] if '=' in line else None
                if key in updates:
                    updated_content.append(f'{key}=\'{updates[key]}\'')
                    updated_keys.add(key)
                else:
                    updated_content.append(line)
            
            for key, value in updates.items():
                if key not in updated_keys:
                    updated_content.append(f'{key}=\'{value}\'')
                os.environ[key] = value
                
            env_path.write_text('\n'.join(updated_content) + '\n', encoding='utf-8')
            logger.info(f"已更新环境变量: {', '.join(updates.keys())}")
            return Result.ok()
        except Exception as e:
            return Result.fail(f"更新环境变量失败: {e}")

    @staticmethod
    def get_env_var(key: str, raise_error: bool = True) -> str:
        if value := os.getenv(key):
            return value
        if raise_error:
            raise ValueError(f"环境变量 '{key}' 未设置")
        return ""

class FileManager:
    @staticmethod
    def backup_file(source: Path, backup_dir: Path, prefix: str, max_backups: int = 10) -> Result[None]:
        try:
            if not source.exists():
                return Result.fail(f"源文件不存在: {source}")
                
            PathManager.ensure_path(backup_dir)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / f"{prefix}_{timestamp}"
            
            backup_files = [(f, f.stat().st_ctime) for f in backup_dir.glob(f"{prefix}_*")]
            for f, _ in sorted(backup_files, key=lambda x: x[1])[:-max_backups+1]:
                f.unlink()
                
            shutil.copy2(source, backup_path)
            logger.info(f"已创建备份: {backup_path}")
            return Result.ok()
        except Exception as e:
            return Result.fail(f"备份文件失败: {e}")

    @staticmethod
    def take_ownership(path: Path) -> bool:
        try:
            subprocess.run(['takeown', '/f', str(path)], capture_output=True, check=True)
            subprocess.run(['icacls', str(path), '/grant', f'{os.getenv("USERNAME")}:F'], 
                         capture_output=True, check=True)
            return True
        except:
            return False

    @staticmethod
    def set_read_only(path: Path) -> None:
        os.chmod(path, 0o444)
        subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r', 
                      f'{os.getenv("USERNAME")}:(R)'], capture_output=True)

    @staticmethod
    def update_json_file(file_path: Path, updates: Dict[str, Any], 
                        make_read_only: bool = False) -> Result[None]:
        try:
            if not file_path.exists() or \
               (make_read_only and not FileManager.take_ownership(file_path)):
                return Result.fail(f"文件不存在或无法获取所有权: {file_path}")

            if make_read_only:
                os.chmod(file_path, 0o666)
                
            content = json.loads(file_path.read_text(encoding='utf-8'))
            content.update(updates)
            file_path.write_text(json.dumps(content, indent=2), encoding='utf-8')
            
            if make_read_only:
                FileManager.set_read_only(file_path)
            return Result.ok()
        except Exception as e:
            return Result.fail(f"更新JSON文件失败: {e}")

class ProcessManager:
    @staticmethod
    def kill_process(process_names: list[str]) -> Result[None]:
        try:
            for name in process_names:
                subprocess.run(['taskkill', '/F', '/IM', f'{name}.exe'], 
                             capture_output=True, check=False)
            return Result.ok()
        except Exception as e:
            return Result.fail(f"结束进程失败: {e}")

    @staticmethod
    def run_as_admin() -> bool:
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([script] + sys.argv[1:])
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            return int(ret) > 32
        except:
            return False

class DatabaseManager:
    @staticmethod
    def update_sqlite_db(db_path: Path, updates: Dict[str, str], 
                        table: str = "itemTable") -> Result[None]:
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                for key, value in updates.items():
                    cursor.execute(
                        f"INSERT INTO {table} (key, value) VALUES (?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value = ?",
                        (key, value, value)
                    )
                    logger.info(f"已更新 {key.split('/')[-1]}")
                return Result.ok()
        except Exception as e:
            return Result.fail(f"数据库更新失败: {e}")

class StringGenerator:
    @staticmethod
    def generate_random_string(length: int, chars: str = string.ascii_lowercase + string.digits) -> str:
        return ''.join(random.choices(chars, k=length))

    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        common_special_chars = "!@#$%^&*()"
        password_chars = [
            random.choice(string.ascii_uppercase),
            random.choice(string.ascii_lowercase),
            random.choice(common_special_chars),
            random.choice(string.digits)
        ]
        remaining_length = length - len(password_chars)
        password_chars.extend(
            random.choices(
                string.ascii_letters + string.digits + common_special_chars,
                k=remaining_length
            )
        )
        random.shuffle(password_chars)
        return ''.join(password_chars)

    @staticmethod
    def extract_token(cookies: str, token_key: str) -> Union[str, None]:
        try:
            token_start = cookies.index(token_key) + len(token_key)
            token_end = cookies.find(';', token_start)
            token = cookies[token_start:] if token_end == -1 else cookies[token_start:token_end]
            return token.split("::")[1]
        except (ValueError, IndexError):
            logger.error(f"无效的 {token_key}")
            return None

def error_handler(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Result:
        try:
            result = func(*args, **kwargs)
            return Result.ok(result) if not isinstance(result, Result) else result
        except Exception as e:
            logger.error(f"{func.__name__} 执行失败: {e}")
            return Result.fail(str(e))
    return wrapper 

class UIManager:
    DEFAULT_STYLES = {
        'label': 'Info.TLabel',
        'entry': 'TEntry',
        'button': 'Custom.TButton',
        'frame': 'TFrame'
    }

    @staticmethod
    def create_labeled_entry(parent, label_text: str, row: int, style: str = None, **kwargs) -> ttk.Entry:
        style = style or UIManager.DEFAULT_STYLES['label']
        ttk.Label(parent, text=f"{label_text}:", style=style).grid(
            row=row, column=0, sticky=tk.W, padx=8, pady=4
        )
        entry = ttk.Entry(parent, width=40, style=UIManager.DEFAULT_STYLES['entry'], **kwargs)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=8, pady=4)
        return entry

    @staticmethod
    def create_labeled_frame(parent, title: str, padding: str = "12", **kwargs) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text=title, padding=padding, **kwargs)
        frame.pack(fill=tk.X, padx=12, pady=6)
        frame.columnconfigure(1, weight=1)
        return frame

    @staticmethod
    def create_button(parent, text: str, command: Callable, col: int = 0, **kwargs) -> ttk.Button:
        btn = ttk.Button(
            parent,
            text=text,
            command=command,
            style=UIManager.DEFAULT_STYLES['button'],
            **kwargs
        )
        btn.grid(row=0, column=col, padx=10)
        return btn

    @staticmethod
    def center_window(window, width: int, height: int) -> None:
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

class StyleManager:
    DEFAULT_FONT = ('Microsoft YaHei UI', 9)
    DEFAULT_COLORS = {
        'primary': '#1976D2',
        'secondary': '#424242',
        'success': '#388E3C',
        'error': '#D32F2F',
        'warning': '#F57C00',
        'background': '#FFFFFF',
        'disabled': '#9E9E9E'
    }

    @staticmethod
    def setup_styles() -> None:
        style = ttk.Style()
        styles = {
            '.': {'font': StyleManager.DEFAULT_FONT},
            'TLabelframe': {
                'padding': 12,
                'background': StyleManager.DEFAULT_COLORS['background'],
                'relief': 'groove'
            },
            'TLabelframe.Label': {
                'font': (StyleManager.DEFAULT_FONT[0], 10, 'bold'),
                'foreground': StyleManager.DEFAULT_COLORS['primary'],
                'background': StyleManager.DEFAULT_COLORS['background']
            },
            'TFrame': {'background': StyleManager.DEFAULT_COLORS['background']},
            'Custom.TButton': {
                'padding': (20, 8),
                'font': (StyleManager.DEFAULT_FONT[0], 9, 'bold'),
                'background': '#E3F2FD',
                'foreground': StyleManager.DEFAULT_COLORS['secondary'],
                'relief': 'raised'
            },
            'Info.TLabel': {
                'font': StyleManager.DEFAULT_FONT,
                'foreground': StyleManager.DEFAULT_COLORS['secondary'],
                'background': StyleManager.DEFAULT_COLORS['background']
            },
            'Error.TLabel': {
                'font': StyleManager.DEFAULT_FONT,
                'foreground': StyleManager.DEFAULT_COLORS['error'],
                'background': StyleManager.DEFAULT_COLORS['background']
            },
            'Success.TLabel': {
                'font': StyleManager.DEFAULT_FONT,
                'foreground': StyleManager.DEFAULT_COLORS['success'],
                'background': StyleManager.DEFAULT_COLORS['background']
            },
            'Footer.TLabel': {
                'font': (StyleManager.DEFAULT_FONT[0], 8),
                'foreground': StyleManager.DEFAULT_COLORS['disabled'],
                'background': StyleManager.DEFAULT_COLORS['background']
            },
            'TEntry': {
                'padding': 6,
                'relief': 'solid',
                'selectbackground': StyleManager.DEFAULT_COLORS['primary'],
                'selectforeground': StyleManager.DEFAULT_COLORS['background'],
                'fieldbackground': '#F5F5F5'
            }
        }
        
        for style_name, config in styles.items():
            style.configure(style_name, **config)
            
        style.map('Custom.TButton',
            background=[('pressed', '#BBDEFB'), ('active', '#E3F2FD'), ('disabled', '#F5F5F5')],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised')],
            foreground=[('disabled', StyleManager.DEFAULT_COLORS['disabled']), 
                       ('!disabled', StyleManager.DEFAULT_COLORS['secondary'])]
        )

class MessageManager:
    @staticmethod
    def _show_message(window: tk.Tk, title: str, message: str, message_type: str) -> None:
        window.bell()
        getattr(messagebox, message_type)(title, message)
        log_level = 'error' if message_type == 'showerror' else \
                   'warning' if message_type == 'showwarning' else 'info'
        getattr(logger, log_level)(message)

    @staticmethod
    def show_error(window: tk.Tk, title: str, error: Exception) -> None:
        error_msg = f"{title}: {str(error)}"
        MessageManager._show_message(window, "错误", error_msg, 'showerror')

    @staticmethod
    def show_success(window: tk.Tk, message: str) -> None:
        MessageManager._show_message(window, "成功", message, 'showinfo')

    @staticmethod
    def show_warning(window: tk.Tk, message: str) -> None:
        MessageManager._show_message(window, "警告", message, 'showwarning')