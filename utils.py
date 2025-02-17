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
import re
import time
import requests
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    ContextManager,
    Dict,
    Generic,
    Tuple,
    TypeVar,
    Union,
    Optional
)

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


@contextmanager
def file_operation_context(file_path: Path, require_write: bool = True) -> ContextManager[Path]:
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    if require_write and not os.access(str(file_path), os.W_OK):
        Utils.manage_file_permissions(file_path, False)
    
    try:
        yield file_path
    finally:
        if require_write:
            Utils.manage_file_permissions(file_path, True)


class DatabaseManager:
    def __init__(self, db_path: Path, table: str = "itemTable"):
        self.db_path = db_path
        self.table = table

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def update(self, updates: Dict[str, str]) -> Result[None]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for key, value in updates.items():
                    cursor.execute(
                        f"INSERT INTO {self.table} (key, value) VALUES (?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value = ?",
                        (key, value, value)
                    )
                    logger.info(f"已更新 {key.split('/')[-1]}")
                conn.commit()
                return Result.ok()
        except Exception as e:
            return Result.fail(f"数据库更新失败: {e}")

    def query(self, keys: Union[str, list[str]] = None) -> Result[Dict[str, str]]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if isinstance(keys, str):
                    keys = [keys]

                if keys:
                    placeholders = ','.join(['?' for _ in keys])
                    cursor.execute(f"SELECT key, value FROM {self.table} WHERE key IN ({placeholders})", keys)
                else:
                    cursor.execute(f"SELECT key, value FROM {self.table}")

                results = dict(cursor.fetchall())
                logger.info(f"已查询 {len(results)} 条记录")
                return Result.ok(results)
        except Exception as e:
            return Result.fail(f"数据库查询失败: {e}")


class EnvManager:
    @staticmethod
    def update(updates: Dict[str, str]) -> Result[None]:
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
    def get(key: str, raise_error: bool = True) -> str:
        if value := os.getenv(key):
            return value
        if raise_error:
            raise ValueError(f"环境变量 '{key}' 未设置")
        return ""


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
            with file_operation_context(source, require_write=False) as src:
                Utils.ensure_path(backup_dir)
                backup_path = backup_dir / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                try:
                    backup_files = sorted(backup_dir.glob(f"{prefix}_*"), key=lambda x: x.stat().st_ctime)[:-max_backups + 1]
                    for f in backup_files:
                        try:
                            f.unlink()
                            logger.info(f"成功删除旧备份文件: {f}")
                        except Exception as del_err:
                            logger.warning(f"删除旧备份文件失败: {f}, 错误: {del_err}")
                except Exception as e:
                    logger.warning(f"处理旧备份文件时出错: {e}")

                shutil.copy2(src, backup_path)
                logger.info(f"已创建备份: {backup_path}")
                return Result.ok()
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
            with file_operation_context(file_path, require_write=make_read_only) as fp:
                content = json.loads(fp.read_text(encoding='utf-8'))
                content.update(updates)
                fp.write_text(json.dumps(content, indent=2), encoding='utf-8')
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
            if int(ret) > 32:
                sys.exit(0)
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


class CursorManager:
    def __init__(self):
        self.db_manager = DatabaseManager(Utils.get_path('cursor') / 'state.vscdb')
        self.env_manager = EnvManager()

    @staticmethod
    @error_handler
    def generate_cursor_account() -> Tuple[str, str]:
        try:
            random_length = random.randint(5, 20)
            email = f"{Utils.generate_random_string(random_length)}@{EnvManager.get('DOMAIN')}"
            password = Utils.generate_secure_password()

            logger.info("生成的Cursor账号信息：")
            logger.info(f"邮箱: {email}")
            logger.info(f"密码: {password}")

            if not (result := EnvManager.update({'EMAIL': email, 'PASSWORD': password})):
                raise RuntimeError(result.message)
            return email, password
        except Exception as e:
            logger.error(f"generate_cursor_account 执行失败: {e}")
            raise

    @staticmethod
    @error_handler
    def reset() -> Result:
        try:
            if not Utils.run_as_admin():
                return Result.fail("需要管理员权限")

            if not (result := Utils.kill_process(['Cursor', 'cursor'])):
                return result

            cursor_path = Utils.get_path('cursor')
            storage_file = cursor_path / 'storage.json'
            backup_dir = cursor_path / 'backups'

            if not (result := Utils.backup_file(storage_file, backup_dir, 'storage.json.backup')):
                return result
            new_ids = {
                f'telemetry.{key}': value for key, value in {
                    'machineId': f"auth0|user_{hashlib.sha256(os.urandom(32)).hexdigest()}",
                    'macMachineId': hashlib.sha256(os.urandom(32)).hexdigest(),
                    'devDeviceId': str(uuid.uuid4()),
                    'sqmId': "{" + str(uuid.uuid4()).upper() + "}"
                }.items()
            }

            if not (result := Utils.update_json_file(storage_file, new_ids)):
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
        except Exception as e:
            logger.error(f"reset 执行失败: {e}")
            return Result.fail(str(e))

    @error_handler
    def process_cookies(self, cookies: str) -> Result:
        try:
            auth_keys = {k: f"cursorAuth/{v}" for k, v in {
                "sign_up": "cachedSignUpType",
                "email": "cachedEmail",
                "access": "accessToken",
                "refresh": "refreshToken"
            }.items()}

            if not (result := Utils.update_env_vars({'COOKIES_STR': cookies})):
                return result

            if not (token := Utils.extract_token(cookies, "WorkosCursorSessionToken=")):
                return Result.fail("无效的 WorkosCursorSessionToken")

            updates = {
                auth_keys["sign_up"]: "Auth_0",
                auth_keys["email"]: os.getenv("EMAIL", ""),
                auth_keys["access"]: token,
                auth_keys["refresh"]: token
            }

            logger.info("正在更新认证信息...")
            if not (result := self.db_manager.update(updates)):
                return result

            return Result.ok(message="认证信息更新成功")
        except Exception as e:
            logger.error(f"process_cookies 执行失败: {e}")
            return Result.fail(str(e))

class MoemailManager:
    
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("未设置API_KEY环境变量")
        
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        self.base_url = os.getenv("MOE_MAIL_URL")
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Result[dict]:
        try:
            url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
            response = requests.request(method, url, headers=self.headers, **kwargs)
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"API响应数据: {response_data}")
                return Result.ok(response_data)
            return Result.fail(f"请求失败: {response.text}")
            
        except Exception as e:
            return Result.fail(f"请求出错: {str(e)}")
    
    def create_email(self,DOMAIN, expiry_time: int = 3600000) -> Result[dict]:
        try:
            random_length = random.randint(5, 20)
            data = {
                "name": Utils.generate_random_string(random_length),
                "expiryTime": expiry_time,
                "domain": DOMAIN
            }
            
            result = self._make_request("POST", "/emails/generate", json=data)
            if not result.success:
                logger.error(f"创建邮箱失败: {result.message}")
                return result

            email_data = result.data
            email_address = email_data.get('email')
            return Result.ok(email_address)
            
        except Exception as e:
            logger.error(f"创建邮箱时出错: {str(e)}")
            return Result.fail(str(e))
    
    def get_email_list(self, cursor: Optional[str] = None) -> Result[dict]:
        params = {"cursor": cursor} if cursor else {}
        return self._make_request("GET", "/emails", params=params)
    
    def get_email_messages(self, email_id: str, cursor: Optional[str] = None) -> Result[dict]:
        params = {"cursor": cursor} if cursor else {}
        return self._make_request("GET", f"/emails/{email_id}", params=params)
    
    def get_message_detail(self, email_id: str, message_id: str) -> Result[dict]:
        return self._make_request("GET", f"/emails/{email_id}/{message_id}")

    def get_latest_email_messages(self, target_email: str, max_retries: int = 3, timeout: int = 30) -> Result[dict]:
        logger.debug(f"开始获取邮箱 {target_email} 的最新邮件，最大重试次数: {max_retries}, 超时时间: {timeout}秒")

        for attempt in range(max_retries):
            try:
                logger.debug(f"第 {attempt + 1} 次尝试获取邮件")

                email_list_result = self.get_email_list()
                if not email_list_result:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.debug(f"获取邮箱列表失败，等待 {wait_time} 秒后重试")
                        time.sleep(wait_time)
                        continue
                    return Result.fail(f"获取邮箱列表失败: {email_list_result.message}")

                target = next((
                    email for email in email_list_result.data.get('emails', [])
                    if email.get('address') == target_email
                ), None)

                if not target or not target.get('id'):
                    return Result.fail(f"未找到目标邮箱: {target_email}")

                logger.debug(f"找到目标邮箱，ID: {target.get('id')}")

                messages_result = self.get_email_messages(target['id'])
                if not messages_result:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.debug(f"获取邮件列表失败，等待 {wait_time} 秒后重试")
                        time.sleep(wait_time)
                        continue
                    return Result.fail(f"获取邮件列表失败: {messages_result.message}")

                messages = messages_result.data.get('messages', [])
                if not messages:
                    return Result.fail("邮箱中没有任何邮件")

                logger.debug(f"成功获取邮件列表，共有 {len(messages)} 封邮件")

                latest_message = max(messages, key=lambda x: x.get('received_at', 0))
                if not latest_message.get('id'):
                    return Result.fail("无法获取最新邮件ID")

                logger.debug(f"找到最新邮件，ID: {latest_message.get('id')}")

                detail_result = self.get_message_detail(target['id'], latest_message['id'])
                if not detail_result:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.debug(f"获取邮件详情失败，等待 {wait_time} 秒后重试")
                        time.sleep(wait_time)
                        continue
                    return Result.fail(f"获取邮件详情失败: {detail_result.message}")

                logger.debug("成功获取邮件详情")
                logger.debug(f"邮件数据: {detail_result.data}")

                return Result.ok(detail_result.data)

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.debug(f"发生异常: {str(e)}，等待 {wait_time} 秒后重试")
                    time.sleep(wait_time)
                    continue
                logger.error(f"获取邮件内容时发生错误: {str(e)}")
                return Result.fail(str(e))

        logger.debug("达到最大重试次数，操作失败")
        return Result.fail("达到最大重试次数，操作失败")