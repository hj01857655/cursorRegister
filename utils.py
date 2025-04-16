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
import time
import uuid
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

import requests
from loguru import logger

T = TypeVar('T')

#错误处理装饰器
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

#数据库管理类
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
                    logger.debug(f"已更新 {key.split('/')[-1]}")
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
                logger.debug(f"已查询 {len(results)} 条记录")
                return Result.ok(results)
        except Exception as e:
            return Result.fail(f"数据库查询失败: {e}")

#环境变量管理类
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
            logger.debug(f"已更新环境变量: {', '.join(updates.keys())}")
            return Result.ok()
        except Exception as e:
            return Result.fail(f"更新环境变量失败: {e}")
    #获取环境变量
    @staticmethod
    def get(key: str, raise_error: bool = True) -> str:
        if value := os.getenv(key):
            return value
        if raise_error:
            raise ValueError(f"环境变量 '{key}' 未设置")
        return ""

#工具类
class Utils:
    #获取路径
    @staticmethod
    def get_path(path_type: str) -> Path:
        # 获取资源路径的基础目录
        # 对于PyInstaller打包的应用，使用sys._MEIPASS作为基础路径
        base_path = Path(sys._MEIPASS) if getattr(sys, '_MEIPASS', False) else (
            Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        )
        
        paths = {
            # 获取当前执行文件路径
            'base': base_path,
            # 获取.env文件路径
            'env': lambda: Utils.get_path('base') / '.env',
            # 获取appdata路径
            'appdata': lambda: Path(os.getenv("APPDATA") or ''),
            # 获取cursor路径
            'cursor': lambda: Utils.get_path('appdata') / 'Cursor/User/globalStorage',
            # 获取turnstilePatch路径
            'turnstilePatch': lambda: Utils.get_path('base') / 'turnstilePatch',
            # 获取assets路径
            'assets': lambda: Utils.get_path('base') / 'assets',
        }
        # 获取路径函数
        path_func = paths.get(path_type)
        if callable(path_func):
            return path_func()
        return paths.get(path_type, Path())
    
    #确保路径存在
    @staticmethod
    def ensure_path(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    #更新环境变量
    @staticmethod
    def update_env_vars(updates: Dict[str, str]) -> Result[None]:
        try:
            #获取.env文件路径
            env_path = Utils.get_path('env')
            #读取.env文件内容
            content = env_path.read_text(encoding='utf-8').splitlines() if env_path.exists() else []
            #更新环境变量
            updated = {line.split('=')[0]: line for line in content if '=' in line}
            #更新环境变量
            for key, value in updates.items():
                updated[key] = f'{key}=\'{value}\''
                os.environ[key] = value
            #写入.env文件
            env_path.write_text('\n'.join(updated.values()) + '\n', encoding='utf-8')
            logger.debug(f"已更新环境变量: {', '.join(updates.keys())}")
            return Result.ok()
        except Exception as e:
            return Result.fail(f"更新环境变量失败: {e}")
    #移除环境变量
    @staticmethod
    def remove_env_var(key: str) -> Result[None]:
        """从环境变量和.env文件中移除指定的变量"""
        try:
            # 获取.env文件路径
            env_path = Utils.get_path('env')
            if not env_path.exists():
                return Result.ok()
                
            # 读取.env文件内容
            content = env_path.read_text(encoding='utf-8').splitlines()
            # 过滤掉要移除的变量
            updated_content = [line for line in content if not line.startswith(f"{key}=")]
            
            # 如果该变量存在于环境变量中，也移除它
            if key in os.environ:
                os.environ.pop(key, None)
                
            # 如果该变量存在于核心配置列表中，也移除它
            if key in ConfigManager._CORE_CONFIG_KEYS:
                ConfigManager._CORE_CONFIG_KEYS.remove(key)
                
            # 写回.env文件
            env_path.write_text('\n'.join(updated_content) + '\n', encoding='utf-8')
            logger.debug(f"已移除环境变量: {key}")
            return Result.ok()
        except Exception as e:
            return Result.fail(f"移除环境变量失败: {e}")
    #备份文件
    @staticmethod
    def backup_file(source: Path, backup_dir: Path, prefix: str, max_backups: int = 10) -> Result[None]:
        try:
            with file_operation_context(source, require_write=False) as src:
                Utils.ensure_path(backup_dir)
                backup_path = backup_dir / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                try:
                    backup_files = sorted(backup_dir.glob(f"{prefix}_*"), key=lambda x: x.stat().st_ctime)[
                                   :-max_backups + 1]
                    for f in backup_files:
                        try:
                            f.unlink()
                            logger.debug(f"成功删除旧备份文件: {f}")
                        except Exception as del_err:
                            logger.warning(f"删除旧备份文件失败: {f}, 错误: {del_err}")
                except Exception as e:
                    logger.warning(f"处理旧备份文件时出错: {e}")

                shutil.copy2(src, backup_path)
                logger.info(f"已创建备份: {backup_path}")
                return Result.ok()
        except Exception as e:
            return Result.fail(f"备份文件失败: {e}")
    #管理文件权限
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
    #更新json文件
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
    #结束进程
    @staticmethod
    def kill_process(process_names: list[str] = None) -> Result[None]:
        """
        关闭Cursor进程
        
        Args:
            process_names: 已废弃参数，保留兼容性
                
        Returns:
            Result: 操作结果
        """
        try:
            # 尝试使用psutil更精确地终止进程
            try:
                import psutil
                current_pid = os.getpid()  # 获取当前进程ID
                
                # 查找所有Cursor.exe进程
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    proc_name = proc.info.get('name', '').lower()
                    proc_pid = proc.info.get('pid')
                    proc_exe = proc.info.get('exe', '')
                    
                    # 跳过当前进程
                    if proc_pid == current_pid:
                        logger.debug(f"跳过当前进程: {proc_name} (PID: {proc_pid})")
                        continue
                    
                    # 只关闭Cursor.exe进程
                    if (proc_name == 'cursor.exe' or 
                        (proc_exe and ('\\cursor\\cursor.exe' in proc_exe.lower() or 
                                       '\\cursor\\resources\\app\\out\\cursor.exe' in proc_exe.lower() or
                                       '\\programs\\cursor\\cursor.exe' in proc_exe.lower()))):
                        logger.info(f"正在终止Cursor进程: {proc_name} (PID: {proc_pid})")
                        try:
                            p = psutil.Process(proc_pid)
                            p.terminate()  # 先尝试优雅终止
                            gone, alive = psutil.wait_procs([p], timeout=2)
                            if alive:  # 如果进程还活着，强制终止
                                logger.warning(f"进程 {proc_name} (PID: {proc_pid}) 未响应terminate请求，将强制结束")
                                p.kill()
                        except psutil.NoSuchProcess:
                            logger.debug(f"进程 {proc_pid} 已不存在")
                        except Exception as e:
                            logger.error(f"使用psutil终止进程 {proc_pid} 失败: {e}")
            except ImportError:
                logger.warning("未安装psutil，将使用taskkill终止进程")
            
            # 使用taskkill作为备用方法，精确定位Cursor.exe
            logger.debug("使用taskkill终止Cursor.exe进程")
            subprocess.run(['taskkill', '/F', '/IM', 'Cursor.exe'], 
                           capture_output=True, check=False)
                
            return Result.ok()
        except Exception as e:
            return Result.fail(f"结束进程失败: {e}")
    #管理员权限
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
    #生成随机字符串
    @staticmethod
    def generate_random_string(length: int, chars: str = string.ascii_lowercase + string.digits) -> str:
        return ''.join(random.choices(chars, k=length))
    #生成安全密码
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
    
    #提取token
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

    #确保必要的包已安装
    @staticmethod
    @error_handler
    def ensure_packages() -> Result:
        try:
            # 需要确保安装的包
            required_packages = {
                'psutil': '5.9.0',  # 指定最低版本
                'requests': '2.28.0',
                'loguru': '0.6.0'
            }
            
            # 导入importlib
            import importlib
            import importlib.util
            import sys
            import platform
            import subprocess
            
            # 检查是否为Windows系统
            is_windows = platform.system().lower() == 'windows'
            
            # 检查是否可以使用yarn
            use_yarn = False
            if is_windows:
                try:
                    yarn_result = subprocess.run(['yarn', '--version'], 
                                               capture_output=True, 
                                               text=True, 
                                               shell=True)
                    if yarn_result.returncode == 0:
                        logger.debug(f"检测到yarn: {yarn_result.stdout.strip()}")
                        use_yarn = True
                except Exception:
                    logger.debug("未检测到yarn，将使用pip安装")
            
            # 检查每个包是否已安装
            missing_packages = {}
            for package, min_version in required_packages.items():
                try:
                    # 尝试导入包
                    module = importlib.import_module(package)
                    if hasattr(module, '__version__'):
                        current_version = module.__version__
                        logger.debug(f"包 {package} 已安装，版本: {current_version}")
                        
                        # 检查版本是否满足要求
                        if current_version < min_version:
                            logger.warning(f"包 {package} 版本过低 ({current_version} < {min_version})，需要更新")
                            missing_packages[package] = min_version
                    else:
                        logger.debug(f"包 {package} 已安装，但无法确定版本")
                except ImportError:
                    logger.warning(f"包 {package} 未安装，将尝试安装")
                    missing_packages[package] = min_version
            
            # 如果有缺失的包，尝试安装
            if missing_packages:
                logger.info(f"正在安装缺失的包: {', '.join(missing_packages.keys())}")
                
                for package, version in missing_packages.items():
                    try:
                        logger.info(f"正在安装 {package} (>={version})...")
                        package_spec = f"{package}>={version}"
                        
                        if use_yarn:
                            # 使用yarn安装
                            cmd = ['yarn', 'add', package_spec]
                            logger.debug(f"执行命令: {' '.join(cmd)}")
                            subprocess.check_call(cmd, shell=True)
                            logger.info(f"包 {package} 安装成功 (使用yarn)")
                        else:
                            # 使用pip安装
                            cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade', package_spec]
                            logger.debug(f"执行命令: {' '.join(cmd)}")
                            subprocess.check_call(cmd)
                            logger.info(f"包 {package} 安装成功 (使用pip)")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"安装包 {package} 失败: {e}")
                        # 尝试使用备用方法安装
                        try:
                            logger.debug("尝试使用备用方法安装...")
                            if use_yarn:
                                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', package_spec])
                            else:
                                subprocess.check_call(['pip', 'install', '--upgrade', package_spec], shell=True)
                            logger.info(f"包 {package} 使用备用方法安装成功")
                        except Exception as alt_err:
                            logger.error(f"备用安装方法也失败: {alt_err}")
            
            # 再次检查包是否已全部安装
            still_missing = []
            for package in required_packages.keys():
                try:
                    importlib.import_module(package)
                except ImportError:
                    still_missing.append(package)
            
            if still_missing:
                return Result.fail(f"以下包安装失败: {', '.join(still_missing)}")
            
            return Result.ok("所有必要的包已安装")
        except Exception as e:
            logger.error(f"确保包安装时出错: {e}")
            return Result.fail(str(e))

#Cursor管理类
class CursorManager:
    # 认证信息键（静态变量）
    AUTH_KEYS = {
        "sign_up": "cursorAuth/cachedSignUpType",
        "email": "cursorAuth/cachedEmail",
        "access": "cursorAuth/accessToken",
        "refresh": "cursorAuth/refreshToken",
        "stripe": "cursorAuth/stripeMembershipType"
    }
    
    # 可能的Cursor可执行文件路径
    CURSOR_PATHS = [
        Path(os.path.expandvars('%LOCALAPPDATA%/Programs/Cursor/Cursor.exe')),
        Path(os.path.expandvars('%LOCALAPPDATA%/Cursor/Cursor.exe')),
        Path(os.path.expandvars('%PROGRAMFILES%/Cursor/Cursor.exe')),
        Path(os.path.expandvars('%PROGRAMFILES(X86)%/Cursor/Cursor.exe')),
        # VSCode路径 (Cursor基于VSCode)
        Path(os.path.expandvars('%LOCALAPPDATA%/Programs/Microsoft VS Code/Code.exe')),
    ]
    
    def __init__(self):
        self.db_manager = DatabaseManager(Utils.get_path('cursor') / 'state.vscdb')
        self.env_manager = EnvManager()
    
    @staticmethod
    def find_cursor_executable() -> Optional[Path]:
        """
        查找Cursor可执行文件
        
        Returns:
            Optional[Path]: 找到的Cursor可执行文件路径，如果未找到则返回None
        """
        for path in CursorManager.CURSOR_PATHS:
            if path.exists():
                logger.info(f"找到Cursor可执行文件: {path}")
                return path
        
        logger.error("找不到Cursor可执行文件")
        return None

    @staticmethod
    def is_cursor_running() -> Tuple[bool, Optional[int]]:
        """
        检查Cursor进程是否正在运行
        
        Returns:
            Tuple[bool, Optional[int]]: (是否运行, 进程ID)
        """
        try:
            # 确保psutil已安装
            Utils.ensure_packages()
            
            # 检查进程
            import psutil
            for proc in psutil.process_iter(['name', 'pid']):
                proc_name = proc.info.get('name')
                if proc_name and proc_name.lower() in ['cursor.exe', 'cursor']:
                    pid = proc.info.get('pid')
                    logger.debug(f"检测到Cursor进程正在运行 (PID: {pid})")
                    return True, pid
            
            logger.debug("未检测到Cursor进程运行")
            return False, None
        except ImportError:
            logger.warning("未安装psutil库，无法检查进程状态")
            return False, None
        except Exception as e:
            logger.error(f"检查进程状态出错: {e}")
            return False, None

    # 获取令牌
    @error_handler
    def get_access_token_and_refresh_token(self, session_token: str) -> Result[str]:
        cursor_reg = None
        try:
            logger.info("【令牌获取-CM】开始使用CursorManager尝试获取长期令牌...")
            
            # 导入CursorRegistration
            try:
                logger.debug("【令牌获取-CM】正在导入CursorRegistration类...")
                from registerAc import CursorRegistration
                logger.debug("【令牌获取-CM】成功导入CursorRegistration类")
            except ImportError as e:
                logger.error(f"【令牌获取-CM】导入CursorRegistration失败: {str(e)}")
                return Result.fail(f"导入CursorRegistration失败: {str(e)}")
                
            # 创建CursorRegistration实例并初始化浏览器
            try:
                logger.debug("【令牌获取-CM】正在创建CursorRegistration实例...")
                cursor_reg = CursorRegistration()
                cursor_reg.headless = True  # 使用无头模式避免弹出浏览器窗口
                logger.debug("【令牌获取-CM】成功创建CursorRegistration实例，设置为无头模式")
                
                logger.debug("【令牌获取-CM】正在初始化浏览器...")
                cursor_reg.init_browser()
                logger.debug("【令牌获取-CM】浏览器初始化成功")
                
                # 设置cookie
                cookie_str = f"WorkosCursorSessionToken={session_token}"
                logger.debug(f"【令牌获取-CM】准备设置Cookie，Cookie字符串长度: {len(cookie_str)}")
                cursor_reg.tab.set.cookies(cookie_str)
                logger.debug("【令牌获取-CM】Cookie设置成功")
                
                # 获取令牌
                logger.info("【令牌获取-CM】开始调用get_cursor_access_token_and_refresh_token方法...")
                access_token, refresh_token = cursor_reg.get_cursor_access_token_and_refresh_token()
                if not access_token or not refresh_token:
                    logger.error("【令牌获取-CM】get_cursor_access_token_and_refresh_token方法返回空值，获取令牌失败")
                    return Result.fail("获取令牌失败")
                #返回令牌的前
                logger.info(f"【令牌获取-CM】成功获取长期令牌: {access_token[:15]}...")
                return Result.ok(access_token, "成功获取令牌")
                
            except Exception as e:
                logger.error(f"【令牌获取-CM】获取令牌过程中发生异常: {str(e)}")
                return Result.fail(f"获取令牌失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"【令牌获取-CM】get_access_token_and_refresh_token方法执行失败: {e}")
            return Result.fail(str(e))
        finally:
            # 确保浏览器实例被关闭
            try:
                if cursor_reg and hasattr(cursor_reg, 'browser'):
                    logger.debug("【令牌获取-CM】正在关闭浏览器实例...")
                    cursor_reg.browser.quit()
                    logger.debug("【令牌获取-CM】浏览器实例已成功关闭")
            except Exception as e:
                logger.error(f"【令牌获取-CM】关闭浏览器实例失败: {str(e)}")

    # 启动Cursor应用程序
    @staticmethod
    @error_handler
    def start_cursor_app() -> Result:
        try:
            # 检查Cursor是否已在运行
            is_running, pid = CursorManager.is_cursor_running()
            if is_running:
                logger.info(f"Cursor已在运行 (PID: {pid})，无需重新启动")
                return Result.ok("Cursor已在运行")
            
            # 查找Cursor可执行文件
            cursor_exe = CursorManager.find_cursor_executable()
            if not cursor_exe:
                return Result.fail("找不到Cursor可执行文件，请确保已安装Cursor")
                
            # 启动Cursor应用
            logger.info(f"正在启动Cursor应用: {cursor_exe}")
            try:
                subprocess.Popen([str(cursor_exe)], shell=True, creationflags=subprocess.CREATE_NO_WINDOW, start_new_session=True)
                logger.info("启动命令已发送")
                return Result.ok("已启动Cursor应用")
            except Exception as start_error:
                logger.error(f"启动应用时出错: {start_error}")
                # 尝试使用其他方法启动
                try:
                    os.startfile(str(cursor_exe))
                    logger.info("使用备用方法启动")
                    return Result.ok("已使用备用方法启动Cursor应用")
                except Exception as alt_error:
                    logger.error(f"备用启动方法也失败: {alt_error}")
                    return Result.fail(f"所有启动方法都失败，请手动启动Cursor")
        except Exception as e:
            logger.error(f"启动Cursor应用失败: {e}")
            return Result.fail(f"启动Cursor应用失败: {e}")
    
    #生成Cursor账号
    @staticmethod
    @error_handler
    def generate_cursor_account() -> Tuple[str, str]:
        try:
            #生成随机长度
            random_length = random.randint(5, 20)
            
            # 首先尝试从ConfigManager获取域名配置
            domain_result = ConfigManager.get_config('DOMAIN')
            if domain_result.success and domain_result.data:
                domain = domain_result.data
                logger.debug(f"从ConfigManager获取到域名: {domain}")
            else:
                # 如果无法从ConfigManager获取，则尝试从环境变量获取
                domain = EnvManager.get('DOMAIN')
                logger.debug(f"从环境变量获取到域名: {domain}")
            
            email = f"{Utils.generate_random_string(random_length)}@{domain}"
            password = Utils.generate_secure_password()

            logger.debug("生成的Cursor账号信息：")
            logger.debug(f"邮箱: {email}")
            logger.debug(f"密码: {password}")

            if not (result := EnvManager.update({'EMAIL': email, 'PASSWORD': password})):
                raise RuntimeError(result.message)
            return email, password
        except Exception as e:
            logger.error(f"generate_cursor_account 执行失败: {e}")
            raise
    
    #重置机器码
    @staticmethod
    @error_handler
    def reset() -> Result:
        try:
            if not Utils.run_as_admin():
                return Result.fail("需要管理员权限")

            if not (result := Utils.kill_process()):
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
    def process_access_token_and_refresh_token(self, access_token: str, refresh_token: str, email: str) -> Result:
        """
        使用长期令牌更新Cursor认证信息
        
        Args:
            access_token: 访问令牌
            refresh_token: 刷新令牌
            email: 账号邮箱
            
        Returns:
            Result: 处理结果
        """
        try:
            if not access_token or not refresh_token:
                return Result.fail("长期令牌不能为空")
                
            if not email:
                return Result.fail("邮箱不能为空")
            
            # 首先确保 psutil 包已安装
            Utils.ensure_packages()
            
            # 检查 Cursor 进程是否在运行
            cursor_running, pid = CursorManager.is_cursor_running()
            
            # 如果 Cursor 在运行，则先关闭进程
            if cursor_running:
                logger.info(f"正在关闭 Cursor 进程 (PID: {pid})...")
                kill_result = Utils.kill_process()
                if not kill_result.success:
                    logger.warning(f"关闭 Cursor 进程可能失败: {kill_result.message}")
                
                # 等待进程完全关闭，最多等待5秒
                import time
                import psutil
                wait_time = 0
                check_interval = 0.5
                max_wait_time = 5  # 最多等待5秒
                
                logger.debug("等待Cursor进程完全关闭...")
                while wait_time < max_wait_time:
                    still_running, _ = CursorManager.is_cursor_running()
                    if not still_running:
                        logger.debug(f"Cursor进程已完全关闭，耗时 {wait_time:.1f} 秒")
                        break
                    time.sleep(check_interval)
                    wait_time += check_interval
                
                if wait_time >= max_wait_time:
                    logger.warning(f"等待Cursor进程关闭超时 ({max_wait_time}秒)，将继续执行")
            else:
                logger.info("未检测到 Cursor 进程运行，将直接更新认证信息")
                
            # 日志记录长期令牌信息
            logger.debug(f"使用长期令牌: {access_token[:15]}... 更新认证信息")
            
            # 准备要更新的数据
            updates = {
                self.AUTH_KEYS["sign_up"]: "Auth_0",
                self.AUTH_KEYS["email"]: email,
                self.AUTH_KEYS["access"]: access_token,
                self.AUTH_KEYS["refresh"]: refresh_token,
                self.AUTH_KEYS["stripe"]: "free_trial"  # 设置为免费试用类型
            }
            #打印更新数据
            logger.debug(f"更新数据: {updates}")

            if not (result := self.db_manager.update(updates)):
                return result
                
            # 启动 Cursor 应用（如果之前在运行或用户希望启动）
            if cursor_running:
                logger.info("认证信息已更新，正在重启 Cursor 应用...")
                start_result = CursorManager.start_cursor_app()
                if not start_result.success:
                    logger.warning(f"重启 Cursor 应用失败: {start_result.message}")
                    return Result.ok(message="使用长期令牌更新认证信息成功，但重启应用失败")
                return Result.ok(message="使用长期令牌更新认证信息成功，已重启应用")
            else:
                logger.info("认证信息已更新，准备启动 Cursor 应用...")
                start_result = CursorManager.start_cursor_app()
                if not start_result.success:
                    logger.warning(f"启动 Cursor 应用失败: {start_result.message}")
                    return Result.ok(message="使用长期令牌更新认证信息成功，但启动应用失败")
                return Result.ok(message="使用长期令牌更新认证信息成功，已启动应用")
        except Exception as e:
            logger.error(f"process_access_token_and_refresh_token 执行失败: {e}")
            return Result.fail(str(e))

    @error_handler
    def get_cookies(self) -> Result[Dict[str, str]]:
        try:
            logger.debug("正在查询认证信息...")
            logger.debug(f"查询的键值: {list(self.AUTH_KEYS.values())}")
            
            result = self.db_manager.query(list(self.AUTH_KEYS.values()))
            if not result:
                logger.error(f"查询失败: {result.message}")
                return Result.fail("查询认证信息失败")

            auth_data = result.data
            if not auth_data:
                logger.warning("数据库中未找到认证信息")
                return Result.fail("未找到认证信息")

            logger.debug("=== 数据库中的原始数据 ===")
            for key, value in auth_data.items():
                logger.debug(f"键: {key}")
                logger.debug(f"值: {value}")
                logger.debug("-" * 50)

            # 反转AUTH_KEYS字典，用于将数据库键映射回原始键名
            reverse_keys = {v: k for k, v in self.AUTH_KEYS.items()}
            logger.debug(f"键值映射关系: {reverse_keys}")
            
            return Result.ok(auth_data)
        except Exception as e:
            logger.error(f"get_cookies 执行失败: {e}")
            logger.error(f"错误详情: {str(e)}")
            return Result.fail(str(e))

# MoemailManager类用于管理MoeMail的相关操作
class MoemailManager:
    @staticmethod
    def _check_env_vars() -> Result[Tuple[str, str]]:
        try:
            api_key = os.getenv("API_KEY")
            moe_mail_url = os.getenv("MOE_MAIL_URL")
            
            missing_vars = []
            if not api_key:
                missing_vars.append("API_KEY")
            if not moe_mail_url:
                missing_vars.append("MOE_MAIL_URL")
            
            if missing_vars:
                return Result.fail(f"缺少必需的环境变量: {', '.join(missing_vars)}")
            
            return Result.ok((api_key, moe_mail_url))
        except Exception as e:
            return Result.fail(f"检查环境变量时出错: {str(e)}")

    def __init__(self):
        env_check = self._check_env_vars()
        if not env_check.success:
            logger.error(env_check.message)
            raise ValueError(env_check.message)
        
        self.api_key, base_url = env_check.data
        # 使用浏览器标准请求头
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "max-age=0",
            "sec-ch-ua": "\"Microsoft Edge\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
            # 保留API密钥
            'X-API-Key': self.api_key
        }
        
        self.base_url = base_url

        # 确保URL末尾没有斜杠
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
            
        # 添加API路径前缀
        if not '/api' in self.base_url:
            self.base_url = f"{self.base_url}/api"
            
        logger.debug(f"邮箱API基础URL: {self.base_url}")
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头信息"""
        return self.headers

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Result[dict]:
        max_retries = 3  # 最大重试次数
        retry_delay = 2  # 重试间隔（秒）
        
        for retry in range(max_retries):
            try:
                # 准备请求参数
                url = f"{self.base_url}{endpoint}"
                headers = self.get_headers()
                
                # 添加一些随机性到请求头，避免被识别为机器人
                headers["User-Agent"] = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.{random.randint(4000, 5000)}.{random.randint(100, 200)} Safari/537.36"
                
                # 设置正确的请求参数
                request_kwargs = {
                    'method': method,
                    'url': url,
                    'headers': headers,
                    'timeout': 30
                }
                
                # 根据提供的fetch，我们需要设置credentials参数
                # 在requests中，这对应于cookies和auth参数
                request_kwargs['allow_redirects'] = True
                
                # 检查是否设置了代理环境变量
                http_proxy = os.getenv('HTTP_PROXY')
                https_proxy = os.getenv('HTTPS_PROXY')
                
                if http_proxy or https_proxy:
                    proxies = {}
                    if http_proxy:
                        proxies['http'] = http_proxy
                    if https_proxy:
                        proxies['https'] = https_proxy
                    logger.debug(f"邮件API使用代理: {proxies}")
                    request_kwargs['proxies'] = proxies
                
                # 添加其他参数
                for key, value in kwargs.items():
                    if key in ['json', 'data', 'params']:
                        request_kwargs[key] = value
                
                logger.debug(f"发送请求: {method} {url}")
                logger.debug(f"请求头: {headers}")
                
                # 发送请求
                response = requests.request(**request_kwargs)
                
                # 记录响应信息
                logger.debug(f"响应状态码: {response.status_code}")
                logger.debug(f"响应头: {response.headers}")
                
                # 检查是否遇到Cloudflare保护
                if response.status_code == 403 and ('cloudflare' in response.text.lower() or '<!DOCTYPE html>' in response.text):
                    logger.warning(f"检测到Cloudflare保护（第 {retry+1} 次尝试）")
                    if retry < max_retries - 1:
                        wait_time = retry_delay * (retry + 1)  # 指数退避
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return Result.fail("API访问被Cloudflare拦截，请检查代理设置或稍后再试")
                
                # 处理响应
                if response.status_code in [200, 201, 204]:
                    try:
                        data = response.json()
                        return Result.ok(data)
                    except:
                        return Result.ok(response.text)
                else:
                    logger.error(f"API请求失败: {response.status_code}")
                    logger.error(f"响应内容: {response.text[:200]}")
                    try:
                        error_data = response.json()
                        error_message = error_data.get('message', f"请求失败: {response.status_code}")
                        return Result.fail(f"{error_message} - {error_data}")
                    except:
                        return Result.fail(f"请求失败: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"请求超时 (第 {retry+1} 次尝试)")
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return Result.fail("请求超时，请检查网络连接或使用代理")
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"连接错误 (第 {retry+1} 次尝试)")
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return Result.fail("连接错误，请检查网络连接或使用代理")
                
            except Exception as e:
                logger.error(f"请求出错 {method} {endpoint}: {str(e)}")
                return Result.fail(str(e))
    #创建邮箱
    def create_email(self, email: str, expiry_time: int = 3600000) -> Result[dict]:
        try:
            #获取邮箱名称和域名
            name, domain = email.split('@')
            
            # 先检查邮箱是否已存在
            logger.debug(f"检查邮箱 {email} 是否已存在")
            email_list_result = self.get_email_list()
            
            # 检查是否成功获取邮箱列表
            if email_list_result.success:
                #获取邮箱列表
                emails = email_list_result.data.get('emails', [])
                
                # 检查邮箱是否已存在
                for existing_email in emails:
                    if existing_email.get('address') == email:
                        logger.info(f"邮箱 {email} 已存在，直接使用现有邮箱")
                        #返回邮箱信息
                        return Result.ok({
                            "id": existing_email.get('id'),
                            "email": email,
                            "expiresAt": existing_email.get('expiresAt')
                        })
            else:
                #打印邮箱未找到
                logger.warning(f"邮箱未找到: {email_list_result.message}，将尝试直接创建邮箱")
            
            # 邮箱不存在，创建新邮箱
            data = {
                "domain": domain,
                "name": name,
                "expiryTime": expiry_time,
            }

            logger.debug(f"创建新邮箱: {email}")
            #发送请求:创建邮箱
            result = self._make_request("POST", "/emails/generate", json=data)
            #如果请求失败
            if not result.success:
                # 如果创建失败，但错误是因为邮箱已存在
                if hasattr(result, 'data') and isinstance(result.data, dict):
                    error = result.data.get('error', '')
                    if 'already exists' in error or 'already registered' in error:
                        logger.info(f"邮箱 {email} 已存在（从错误响应中确认）")
                        # 尝试再次获取邮箱列表，找到已存在的邮箱
                        retry_list_result = self.get_email_list()
                        if retry_list_result.success:
                            for existing_email in retry_list_result.data.get('emails', []):
                                if existing_email.get('address') == email:
                                    return Result.ok({
                                        "email": email,
                                        "id": existing_email.get('id'),
                                        "expiresAt": existing_email.get('expiresAt')
                                    })
                
                logger.error(f"创建邮箱失败: {result.message}")
                return result
                
            return Result.ok(result.data)

        except Exception as e:
            logger.error(f"创建邮箱时出错: {str(e)}")
            return Result.fail(str(e))
    #获取邮箱列表
    def get_email_list(self, cursor: Optional[str] = None) -> Result[dict]:
        #请求参数
        params = {"cursor": cursor} if cursor else {}
        #发送请求
        return self._make_request("GET", "/emails", params=params)
    #获取邮件列表
    def get_email_messages(self, email_id: str, cursor: Optional[str] = None) -> Result[dict]:
        params = {"cursor": cursor} if cursor else {}
        return self._make_request("GET", f"/emails/{email_id}", params=params)
    #获取邮件详情
    def get_message_detail(self, email_id: str, message_id: str) -> Result[dict]:
        return self._make_request("GET", f"/emails/{email_id}/{message_id}")
    #获取最新邮件
    def get_latest_email_messages(self, target_email: str, timeout: int = 60) -> Result[dict]:
        logger.debug(f"开始获取邮箱 {target_email} 的最新邮件")

        try:
            email_list_result = self.get_email_list()
            if not email_list_result:
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
                return Result.fail(f"获取邮件列表失败: {messages_result.message}")

            messages = messages_result.data.get('messages', [])
            start_time = time.time()
            retry_interval = 2

            while not messages:
                if time.time() - start_time > timeout:
                    return Result.fail("等待邮件超时，1分钟内未收到任何邮件")

                logger.debug(f"邮箱暂无邮件，{retry_interval}秒后重试...")
                time.sleep(retry_interval)

                messages_result = self.get_email_messages(target['id'])
                if not messages_result:
                    return Result.fail(f"获取邮件列表失败: {messages_result.message}")

                messages = messages_result.data.get('messages', [])
                logger.debug(f"第{int((time.time() - start_time) / retry_interval)}次尝试获取邮件...")

            logger.debug(f"成功获取邮件列表，共有 {len(messages)} 封邮件")

            latest_message = max(messages, key=lambda x: x.get('received_at', 0))
            if not latest_message.get('id'):
                return Result.fail("无法获取最新邮件ID")

            logger.debug(f"找到最新邮件，ID: {latest_message.get('id')}")

            detail_result = self.get_message_detail(target['id'], latest_message['id'])
            if not detail_result:
                return Result.fail(f"获取邮件详情失败: {detail_result.message}")

            logger.debug("成功获取邮件详情")
            logger.debug(f"邮件数据: {detail_result.data}")

            return Result.ok(detail_result.data)

        except Exception as e:
            logger.error(f"获取邮件内容时发生错误: {str(e)}")
            return Result.fail(str(e))

#配置管理类
class ConfigManager:
    """
    管理系统配置的工具类
    实现配置的双向绑定：
    1. 从.env文件读取配置
    2. 将UI中的更改写回.env文件
    """
    # 核心配置项列表 - 更新为.env文件中所有必要的配置项
    _CORE_CONFIG_KEYS = [
        'DOMAIN', 
        'API_KEY', 
        'MOE_MAIL_URL',
        'EMAIL', 
        'PASSWORD', 
        'COOKIES_STR'
    ]
    #获取所有核心配置项的键名
    @staticmethod
    def get_config_keys() -> list[str]:
        """获取所有核心配置项的键名"""
        return ConfigManager._CORE_CONFIG_KEYS
    
    #获取单个配置项的值
    @staticmethod
    @error_handler
    def get_config(key: str) -> Result[str]:
        """获取单个配置项的值
        
        先尝试从环境变量获取，如果不存在则从.env文件读取，
        如果都不存在则返回空字符串
        """
        try:
            # 1. 尝试从环境变量获取
            value = EnvManager.get(key, raise_error=False)
            if value:
                return Result.ok(value)
                
            # 2. 尝试从.env文件获取
            env_path = Utils.get_path('env')
            if env_path.exists():
                content = env_path.read_text(encoding='utf-8').splitlines()
                for line in content:
                    if '=' in line:
                        env_key, env_value = line.split('=', 1)
                        if env_key == key:
                            # 去除引号
                            env_value = env_value.strip().strip("'").strip('"')
                            return Result.ok(env_value)
            
            # 3. 如果都没有找到，直接返回空字符串
            return Result.ok("")
        except Exception as e:
            logger.error(f"获取配置项 {key} 失败: {e}")
            return Result.fail(f"获取配置项失败: {e}")

    @staticmethod
    @error_handler
    def load_config() -> Result[Dict[str, str]]:
        """加载当前系统配置
        
        首先尝试从环境变量和.env文件读取配置
        """
        config = {}
        
        # 获取配置键列表
        config_keys = ConfigManager.get_config_keys()
        
        # 1. 尝试从环境变量读取配置
        for key in config_keys:
            try:
                value = EnvManager.get(key, raise_error=False)
                if value:  # 只保存非空值
                    config[key] = value
                else:
                    config[key] = ""  # 如果环境变量中不存在，则设为空字符串
            except Exception as e:
                logger.warning(f"获取环境变量 {key} 失败: {e}")
                config[key] = ""  # 出现异常时设为空字符串
        
        # 2. 尝试读取.env文件中的所有配置项
        try:
            env_path = Utils.get_path('env')
            if env_path.exists():
                content = env_path.read_text(encoding='utf-8').splitlines()
                for line in content:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # 去除引号
                        value = value.strip().strip("'").strip('"')
                        # 更新配置值，确保.env文件的值优先级最高
                        config[key] = value
                        logger.debug(f"从.env文件读取配置项: {key}={value}")
                        
                        # 如果发现.env中有新的配置项不在核心配置列表中，动态添加
                        if key not in ConfigManager._CORE_CONFIG_KEYS:
                            ConfigManager._CORE_CONFIG_KEYS.append(key)
                            logger.debug(f"动态添加新的配置项到核心配置列表: {key}")
        except Exception as e:
            logger.warning(f"读取.env文件失败: {e}")
        
        return Result.ok(config)
    
    @staticmethod
    @error_handler
    def save_config(config: Dict[str, str]) -> Result[None]:
        """保存系统配置到.env文件"""
        # 1. 读取现有的.env文件内容，保留所有配置项
        try:
            env_path = Utils.get_path('env')
            env_config = {}
            
            if env_path.exists():
                content = env_path.read_text(encoding='utf-8').splitlines()
                for line in content:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # 保存所有现有配置项
                        env_config[key] = value.strip()
            
            # 2. 添加或更新所有配置项
            for key, value in config.items():
                env_config[key] = f'\'{value}\''
                # 同时更新内存中的环境变量
                os.environ[key] = value
                
                # 如果是新的配置项，添加到核心配置列表
                if key not in ConfigManager._CORE_CONFIG_KEYS:
                    ConfigManager._CORE_CONFIG_KEYS.append(key)
            
            # 3. 写回.env文件
            env_content = '\n'.join([f"{key}={value}" for key, value in env_config.items()]) + '\n'
            env_path.write_text(env_content, encoding='utf-8')
            logger.debug(f"已更新环境变量: {', '.join(config.keys())}")
            
            return Result.ok()
        except Exception as e:
            return Result.fail(f"保存配置失败: {e}")
    
    @staticmethod
    @error_handler
    def reset_to_default() -> Result[Dict[str, str]]:
        """重置为默认配置"""
        # 创建空配置 - 所有值都设为空字符串
        empty_config = {key: "" for key in ConfigManager.get_config_keys()}
        
        # 保存空配置到.env文件
        result = ConfigManager.save_config(empty_config)
        if not result.success:
            return Result.fail(f"重置配置失败: {result.message}")
        
        return Result.ok(empty_config)
        
    @staticmethod
    @error_handler
    def apply_config(config: Dict[str, str]) -> Result[None]:
        """仅应用配置到当前环境，不保存到文件"""
        try:
            # 仅更新内存中的环境变量
            for key, value in config.items():
                os.environ[key] = value
            
            return Result.ok(message="配置已应用到当前会话")
        except Exception as e:
            return Result.fail(f"应用配置失败: {e}")

if __name__ == "__main__":
    CursorManager().get_cookies()