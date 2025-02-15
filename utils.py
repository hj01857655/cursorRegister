import ctypes
import hashlib
import json
import os
import random
import shutil
import sqlite3
import string
import subprocess
import sys
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Union, TypeVar, Generic, Callable, Tuple

from loguru import logger

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
                backup_files = sorted(backup_dir.glob(f"{prefix}_*"), key=lambda x: x.stat().st_ctime)[
                               :-max_backups + 1]

                for f in backup_files:
                    try:
                        try:
                            f.unlink()
                            logger.info(f"成功删除旧备份文件: {f}")
                            continue
                        except PermissionError:
                            logger.debug(f"尝试直接删除文件失败，准备修改权限: {f}")
                            pass

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
                subprocess.run(['icacls', str(path), '/grant', f'{os.getenv("USERNAME")}:F'], capture_output=True,
                               check=True)
                os.chmod(path, 0o444)
                subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r', f'{os.getenv("USERNAME")}:(R)'],
                               capture_output=True)
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
    def query_sqlite_db(db_path: Path, keys: Union[str, list[str]] = None, table: str = "itemTable") -> Result[
        Dict[str, str]]:
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                if isinstance(keys, str):
                    keys = [keys]

                if keys:
                    placeholders = ','.join(['?' for _ in keys])
                    cursor.execute(f"SELECT key, value FROM {table} WHERE key IN ({placeholders})", keys)
                else:
                    cursor.execute(f"SELECT key, value FROM {table}")

                results = dict(cursor.fetchall())
                logger.info(f"已查询 {len(results)} 条记录")
                return Result.ok(results)
        except Exception as e:
            return Result.fail(f"数据库查询失败: {e}")

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
        password = required + random.choices(chars, k=length - 4)
        random.shuffle(password)
        return ''.join(password)

    @staticmethod
    def extract_token(cookies: str, token_key: str) -> Union[str, None]:
        try:
            token_start = cookies.index(token_key) + len(token_key)
            token_end = cookies.find(';', token_start)
            token = cookies[token_start:] if token_end == -1 else cookies[token_start:token_end]
            if '::' in token:
                return token.split('::')[1]
            elif '%3A%3A' in token:
                return token.split('%3A%3A')[1]

            logger.error(f"在token中未找到有效的分隔符: {token}")
            return None
        except (ValueError, IndexError) as e:
            logger.error(f"无效的 {token_key}: {str(e)}")
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


def generate_ids() -> dict:
    return {
        f'telemetry.{key}': value for key, value in {
            'machineId': f"auth0|user_{hashlib.sha256(os.urandom(32)).hexdigest()}",
            'macMachineId': hashlib.sha256(os.urandom(32)).hexdigest(),
            'devDeviceId': str(uuid.uuid4()),
            'sqmId': "{" + str(uuid.uuid4()).upper() + "}"
        }.items()
    }


@error_handler
def reset() -> Result:
    if not Utils.run_as_admin():
        return Result.fail("需要管理员权限")

    if not (result := Utils.kill_process(['Cursor', 'cursor'])):
        return result

    cursor_path = Utils.get_path('cursor')
    storage_file = cursor_path / 'storage.json'
    backup_dir = cursor_path / 'backups'

    if not (result := Utils.backup_file(storage_file, backup_dir, 'storage.json.backup')):
        return result

    if not (result := Utils.update_json_file(storage_file, generate_ids())):
        return Result.fail("更新配置文件失败")

    try:
        updater_path = Path(os.getenv('LOCALAPPDATA')) / 'cursor-updater'

        if updater_path.is_dir():
            try:
                import shutil
                shutil.rmtree(updater_path)
            except Exception as e:
                logger.warning(f"删除cursor-updater文件夹失败: {e}")

        if not updater_path.exists():
            updater_path.touch(exist_ok=True)
            Utils.manage_file_permissions(updater_path)
        else:
            try:
                Utils.manage_file_permissions(updater_path)
            except PermissionError:

                pass

        return Result.ok(message="重置机器码成功，已禁用自动更新")
    except Exception as e:
        return Result.fail(f"禁用自动更新失败: {e}")


AUTH_KEYS = {k: f"cursorAuth/{v}" for k, v in {
    "sign_up": "cachedSignUpType",
    "email": "cachedEmail",
    "access": "accessToken",
    "refresh": "refreshToken"
}.items()}


@error_handler
def process_cookies(cookies: str) -> Result:
    if not (result := Utils.update_env_vars({'COOKIES_STR': cookies})):
        return result

    if not (token := Utils.extract_token(cookies, "WorkosCursorSessionToken=")):
        return Result.fail("无效的 WorkosCursorSessionToken")

    updates = {
        AUTH_KEYS["sign_up"]: "Auth_0",
        AUTH_KEYS["email"]: os.getenv("EMAIL", ""),
        AUTH_KEYS["access"]: token,
        AUTH_KEYS["refresh"]: token
    }

    logger.info("正在更新认证信息...")
    if not (result := Utils.update_sqlite_db(Utils.get_path('cursor') / 'state.vscdb', updates)):
        return result

    return Result.ok(message="认证信息更新成功")


@error_handler
def generate_cursor_account() -> Tuple[str, str]:
    random_length = random.randint(5, 20)
    email = f"{Utils.generate_random_string(random_length)}@{Utils.get_env_var('DOMAIN')}"
    password = Utils.generate_secure_password()

    logger.info("生成的Cursor账号信息：")
    logger.info(f"邮箱: {email}")
    logger.info(f"密码: {password}")

    if not (result := Utils.update_env_vars({'EMAIL': email, 'PASSWORD': password})):
        raise RuntimeError(result.message)
    return email, password
