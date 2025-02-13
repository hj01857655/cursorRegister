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
        self.success, self.data, self.message = success, data, message

    @classmethod
    def ok(cls, data: T = None, message: str = "操作成功") -> 'Result[T]':
        return cls(True, data, message)

    @classmethod
    def fail(cls, message: str = "操作失败") -> 'Result[T]':
        return cls(False, None, message)

    def __bool__(self) -> bool:
        return self.success

class Utils:
    @staticmethod
    def get_path(path_type: str) -> Path:
        paths = {
            'base': Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent,
            'env': lambda: Utils.get_path('base') / '.env',
            'appdata': lambda: Path(os.getenv("APPDATA") or ''),
            'cursor': lambda: Utils.get_path('appdata') / 'Cursor/User/globalStorage'
        }
        path_func = paths.get(path_type)
        if callable(path_func):
            return path_func()
        return paths.get(path_type, Path())

    @staticmethod
    def ensure_path(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def update_env_vars(updates: Dict[str, str]) -> Result[None]:
        try:
            env_path = Utils.get_path('env')
            content = env_path.read_text(encoding='utf-8').splitlines() if env_path.exists() else []
            updated = {line.split('=')[0]: line for line in content if '=' in line}
            
            for key, value in updates.items():
                updated[key] = f'{key}=\'{value}\''
                os.environ[key] = value
                
            env_path.write_text('\n'.join(updated.values()) + '\n', encoding='utf-8')
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

    @staticmethod
    def backup_file(source: Path, backup_dir: Path, prefix: str, max_backups: int = 10) -> Result[None]:
        try:
            if not source.exists():
                return Result.fail(f"源文件不存在: {source}")

            if not os.access(str(source), os.R_OK):
                return Result.fail(f"没有源文件的读取权限: {source}")
            
            Utils.ensure_path(backup_dir)
            
            if not os.access(str(backup_dir), os.W_OK):
                return Result.fail(f"没有备份目录的写入权限: {backup_dir}")
                
            backup_path = backup_dir / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            try:
                backup_files = sorted(backup_dir.glob(f"{prefix}_*"), key=lambda x: x.stat().st_ctime)[:-max_backups+1]

                for f in backup_files:
                    try:
                        # 首先尝试直接删除
                        try:
                            f.unlink()
                            logger.info(f"成功删除旧备份文件: {f}")
                            continue
                        except PermissionError:
                            logger.debug(f"尝试直接删除文件失败，准备修改权限: {f}")
                            pass

                        # 如果直接删除失败，尝试获取文件所有权并修改权限
                        if Utils.manage_file_permissions(f, False):
                            try:
                                f.unlink()
                                logger.info(f"修改权限后成功删除旧备份文件: {f}")
                            except Exception as e:
                                logger.warning(f"获取权限后仍无法删除文件: {f}, 错误: {e}")
                        else:
                            logger.warning(f"无法修改文件权限: {f}")
                            
                    except Exception as del_err:
                        logger.warning(f"删除旧备份文件失败: {f}, 错误: {del_err}")
                    
            except Exception as e:
                logger.warning(f"处理旧备份文件时出错: {e}")
        
            shutil.copy2(source, backup_path)
            
            logger.info(f"已创建备份: {backup_path}")
            return Result.ok()
            
        except PermissionError as pe:
            return Result.fail(f"权限错误: {pe}")
        except Exception as e:
            return Result.fail(f"备份文件失败: {e}")

    @staticmethod
    def manage_file_permissions(path: Path, make_read_only: bool = True) -> bool:
        try:
            if make_read_only:
                subprocess.run(['takeown', '/f', str(path)], capture_output=True, check=True)
                subprocess.run(['icacls', str(path), '/grant', f'{os.getenv("USERNAME")}:F'], capture_output=True, check=True)
                os.chmod(path, 0o444)
                subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r', f'{os.getenv("USERNAME")}:(R)'], capture_output=True)
            else:
                os.chmod(path, 0o666)
            return True
        except:
            return False

    @staticmethod
    def update_json_file(file_path: Path, updates: Dict[str, Any], make_read_only: bool = False) -> Result[None]:
        try:
            if not file_path.exists() or (make_read_only and not Utils.manage_file_permissions(file_path, False)):
                return Result.fail(f"文件不存在或无法获取所有权: {file_path}")
                
            content = json.loads(file_path.read_text(encoding='utf-8'))
            content.update(updates)
            file_path.write_text(json.dumps(content, indent=2), encoding='utf-8')
            
            if make_read_only:
                Utils.manage_file_permissions(file_path)
            return Result.ok()
        except Exception as e:
            return Result.fail(f"更新JSON文件失败: {e}")

    @staticmethod
    def kill_process(process_names: list[str]) -> Result[None]:
        try:
            for name in process_names:
                subprocess.run(['taskkill', '/F', '/IM', f'{name}.exe'], capture_output=True, check=False)
            return Result.ok()
        except Exception as e:
            return Result.fail(f"结束进程失败: {e}")

    @staticmethod
    def run_as_admin() -> bool:
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
            script = os.path.abspath(sys.argv[0])
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, 
                                                    ' '.join([script] + sys.argv[1:]), None, 1)
            return int(ret) > 32
        except:
            return False

    @staticmethod
    def update_sqlite_db(db_path: Path, updates: Dict[str, str], table: str = "itemTable") -> Result[None]:
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

    @staticmethod
    def generate_random_string(length: int, chars: str = string.ascii_lowercase + string.digits) -> str:
        return ''.join(random.choices(chars, k=length))

    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        required = [
            random.choice(string.ascii_uppercase),
            random.choice(string.ascii_lowercase),
            random.choice("!@#$%^&*()"),
            random.choice(string.digits)
        ]
        password = required + random.choices(chars, k=length-4)
        random.shuffle(password)
        return ''.join(password)

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

class UI:
    FONT = ('Microsoft YaHei UI', 9)
    COLORS = {
        'primary': '#1976D2',
        'secondary': '#424242',
        'success': '#388E3C',
        'error': '#D32F2F',
        'warning': '#F57C00',
        'bg': '#FFFFFF',
        'disabled': '#9E9E9E'
    }

    @staticmethod
    def setup_styles() -> None:
        style = ttk.Style()
        base_style = {'font': UI.FONT, 'background': UI.COLORS['bg']}
        
        styles = {
            '.': base_style,
            'TFrame': {'background': UI.COLORS['bg']},
            'TLabelframe': {**base_style, 'padding': 12, 'relief': 'groove'},
            'TLabelframe.Label': {
                **base_style,
                'font': (UI.FONT[0], 10, 'bold'),
                'foreground': UI.COLORS['primary']
            },
            'Custom.TButton': {
                **base_style,
                'padding': (20, 8),
                'font': (UI.FONT[0], 9, 'bold'),
                'background': '#E3F2FD',
                'foreground': UI.COLORS['secondary'],
                'relief': 'raised'
            },
            'TEntry': {
                'padding': 6,
                'relief': 'solid',
                'selectbackground': UI.COLORS['primary'],
                'selectforeground': UI.COLORS['bg'],
                'fieldbackground': '#F5F5F5'
            }
        }

        label_styles = {
            'Info.TLabel': {'foreground': UI.COLORS['secondary']},
            'Error.TLabel': {'foreground': UI.COLORS['error']},
            'Success.TLabel': {'foreground': UI.COLORS['success']},
            'Footer.TLabel': {
                'font': (UI.FONT[0], 8),
                'foreground': UI.COLORS['disabled']
            }
        }

        for name, config in {**styles, **{k: {**base_style, **v} for k, v in label_styles.items()}}.items():
            style.configure(name, **config)
            
        style.map('Custom.TButton',
            background=[('pressed', '#BBDEFB'), ('active', '#E3F2FD'), ('disabled', '#F5F5F5')],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised')],
            foreground=[('disabled', UI.COLORS['disabled']), ('!disabled', UI.COLORS['secondary'])]
        )

    @staticmethod
    def create_labeled_entry(parent, label_text: str, row: int, **kwargs) -> ttk.Entry:
        ttk.Label(parent, text=f"{label_text}:", style='Info.TLabel').grid(
            row=row, column=0, sticky=tk.W, padx=8, pady=4
        )
        entry = ttk.Entry(parent, width=40, style='TEntry', **kwargs)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=8, pady=4)
        return entry

    @staticmethod
    def create_labeled_frame(parent, title: str, padding: str = "12", **kwargs) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text=title, padding=padding, **kwargs)
        frame.pack(fill=tk.X, padx=12, pady=6)
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