# 导入版本信息
try:
    from version import __version__
except ImportError:
    __version__ = "未知版本"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = f"Cursor账号助手 v{__version__}"
BACKUP_DIR = "env_backups"
CONTENT_RATIO = 0.5  # 对半分

import os
import sys
import tkinter as tk
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import ttk
from typing import Dict, List, Tuple

# 尝试导入dotenv，如果失败提供备用方案
try:
    from dotenv import load_dotenv
except ImportError:
    # 备用方案：简单的dotenv加载函数
    def load_dotenv():
        try:
            env_file = '.env'
            if os.path.exists(env_file):
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                return True
        except Exception:
            pass
        return False

# 尝试导入loguru，如果失败提供备用日志记录机制
try:
    from loguru import logger
except ImportError:
    import logging
    # 配置基本日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    # 创建类似loguru的接口
    class LoguruLike:
        def __init__(self):
            self.logger = logging.getLogger("cursorHelper")
        
        def debug(self, msg, *args, **kwargs):
            self.logger.debug(msg, *args, **kwargs)
        
        def info(self, msg, *args, **kwargs):
            self.logger.info(msg, *args, **kwargs)
        
        def warning(self, msg, *args, **kwargs):
            self.logger.warning(msg, *args, **kwargs)
        
        def error(self, msg, *args, **kwargs):
            self.logger.error(msg, *args, **kwargs)
        
        def critical(self, msg, *args, **kwargs):
            self.logger.critical(msg, *args, **kwargs)
        
        def remove(self):
            pass
        
        def add(self, *args, **kwargs):
            return 1
            
    logger = LoguruLike()

# 尝试导入应用模块
try:
    from tab import ManageTab, RegisterTab, AboutTab, ConfigTab, UI
    from tab.logWindow import MAX_BUFFER_SIZE, UI_UPDATE_BATCH, MAX_TEXT_LENGTH
    from utils import Utils, Result, ConfigManager
except ImportError as e:
    # 如果导入失败，创建一个紧急错误弹窗
    def show_import_error(error):
        try:
            root = tk.Tk()
            root.withdraw()
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "模块导入错误", 
                f"程序启动失败，缺少必要模块:\n\n{error}\n\n请确保所有依赖已正确安装。"
            )
            root.destroy()
        except:
            pass
        sys.exit(1)
    
    show_import_error(str(e))

# 控制台模式设置
console_mode = "--console" in sys.argv


#窗口配置
@dataclass
class WindowConfig:
    width: int = WINDOW_WIDTH
    height: int = WINDOW_HEIGHT
    title: str = WINDOW_TITLE
    backup_dir: str = BACKUP_DIR
    env_vars: List[Tuple[str, str]] = field(default_factory=lambda: [
        ('EMAIL', '邮箱'), ('PASSWORD', '密码')
    ])
    buttons: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("生成账号", "generate_account"),
        ("全自动注册", "auto_register"),
        ("备份账号", "backup_account")
    ])

#主窗口
class CursorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.config = WindowConfig()
        self.entries: Dict[str, ttk.Entry] = {}
        self.selected_mode = tk.StringVar(value="admin")

        self.root.title(self.config.title)
        UI.center_window(self.root, self.config.width, self.config.height)
        self.root.resizable(False, False)
        self.root.configure(bg=UI.COLORS['bg'])
        if os.name == 'nt':
            self.root.attributes('-alpha', 0.98)
            
        # 计算有效内容区域宽度（减去内边距）
        padding = 20  # 左右各10像素的padding
        self.effective_width = self.config.width - padding
        # 计算分隔位置
        self.sash_position = int(self.effective_width * CONTENT_RATIO)
        # 计算两侧面板宽度
        self.content_width = int(self.effective_width * CONTENT_RATIO)
        self.log_width = self.effective_width - self.content_width

        UI.setup_styles()
        self.setup_ui()
        
        # 窗口显示后立即设置分隔线位置
        self.root.update_idletasks()
        self.set_sash_position()
        
        # 绑定窗口大小变化和分隔线移动事件
        self.root.bind("<Configure>", self.on_window_configure)
        self.paned_window.bind("<ButtonRelease-1>", self.on_sash_moved)

    def set_sash_position(self):
        """设置分隔线位置"""
        try:
            self.paned_window.sashpos(0, self.sash_position)
        except:
            # 如果设置失败，可能是窗口还未完全初始化
            self.root.after(100, self.set_sash_position)
            
    def on_window_configure(self, event=None):
        """窗口配置改变时调用"""
        if event and event.widget == self.root:
            # 重新设置分隔线位置
            self.set_sash_position()
            
    def on_sash_moved(self, event=None):
        """用户移动分隔线后重置到预设位置"""
        self.root.after(10, self.set_sash_position)  # 短暂延迟后重置分隔线位置

    def setup_ui(self) -> None:
        self.main_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建分隔窗口
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # 左侧内容区域
        self.content_frame = ttk.Frame(self.paned_window, style='TFrame', width=self.content_width)
        
        # 强制框架保持固定宽度
        self.content_frame.pack_propagate(False)

        title_label = ttk.Label(
            self.content_frame,
            text=self.config.title,
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 6))

        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 2))

        register_tab = RegisterTab(
            notebook,
            env_vars=self.config.env_vars,
            buttons=self.config.buttons,
            entries=self.entries,
            selected_mode=self.selected_mode,
            button_commands={}
        )
        notebook.add(register_tab, text="账号注册")

        manage_tab = ManageTab(notebook)
        notebook.add(manage_tab, text="账号管理")
        
        config_tab = ConfigTab(notebook)
        notebook.add(config_tab, text="系统配置")

        about_tab = AboutTab(notebook)
        notebook.add(about_tab, text="关于")

        footer_frame = ttk.Frame(self.content_frame, style='TFrame')
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=6)

        footer = ttk.Label(
            footer_frame,
            text="POWERED BY Hj01857655 仅供学习使用",
            style='Footer.TLabel'
        )
        footer.pack(side=tk.LEFT)

        # 添加左侧内容区域
        self.paned_window.add(self.content_frame, weight=1)
        
        # 设置日志面板
        self.setup_log_panel()

    def setup_log_panel(self):
        # 右侧日志面板
        self.log_frame = ttk.Frame(self.paned_window, style='TFrame', width=self.log_width)
        # 强制框架保持固定宽度
        self.log_frame.pack_propagate(False)
        
        title_frame = ttk.Frame(self.log_frame, style='TFrame')
        title_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        log_title = ttk.Label(
            title_frame,
            text="操作日志",
            style='Title.TLabel'
        )
        log_title.pack(side=tk.LEFT, padx=5)
        
        # 设置调试模式默认开启
        self.show_debug = tk.BooleanVar(value=True)
        debug_checkbox = ttk.Checkbutton(
            title_frame,
            text="调试模式",
            variable=self.show_debug,
            style='TCheckbutton',
            command=self.refresh_logs
        )
        debug_checkbox.pack(side=tk.LEFT, padx=(5, 5))

        clear_button = ttk.Button(
            title_frame,
            text="清除日志",
            command=self.clear_logs,
            style='Custom.TButton',
            width=6
        )
        clear_button.pack(side=tk.RIGHT, padx=(0, 5))

        text_container = ttk.Frame(self.log_frame, style='TFrame')
        text_container.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            text_container,
            wrap=tk.WORD,
            width=25,
            font=UI.FONT,
            bg=UI.COLORS['card_bg'],
            fg=UI.COLORS['label_fg'],
            relief='flat',
            padx=5,
            pady=5
        )
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_text.configure(state='disabled')
        self.setup_log_tags()
        
        self.log_buffer = []
        self.pending_logs = []
        self.update_scheduled = False
        
        # 添加右侧日志面板
        self.paned_window.add(self.log_frame, weight=1)

    def setup_log_tags(self):
        log_colors = {
            'DEBUG': UI.COLORS['secondary'],
            'INFO': UI.COLORS['primary'],
            'WARNING': UI.COLORS['warning'],
            'ERROR': UI.COLORS['error'],
            'SUCCESS': UI.COLORS['success']
        }
        for level, color in log_colors.items():
            self.log_text.tag_configure(level, foreground=color)

    def refresh_logs(self):
        logs_to_display = list(self.log_buffer)
        if not logs_to_display:
            return

        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        show_debug = self.show_debug.get()

        for log in logs_to_display:
            if show_debug or log['level'] != 'DEBUG':
                log_line = f"[{log['timestamp']}] [{log['level']}] {log['message']}\n"
                self.log_text.insert(tk.END, log_line, log['level'])

        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def schedule_update(self):
        if not self.update_scheduled:
            self.update_scheduled = True
            self.root.after(UI_UPDATE_BATCH, self.batch_update)

    def batch_update(self):
        self.update_scheduled = False

        if not self.pending_logs:
            return
        logs_to_update = self.pending_logs[:]
        self.pending_logs.clear()

        if not logs_to_update:
            return

        show_debug = self.show_debug.get()

        current_length = float(self.log_text.index(tk.END))
        if current_length > MAX_TEXT_LENGTH:
            self.log_text.configure(state='normal')
            self.log_text.delete(1.0, f"{current_length - MAX_TEXT_LENGTH}.0")
            self.log_text.configure(state='disabled')

        self.log_text.configure(state='normal')
        for log in logs_to_update:
            if show_debug or log['level'] != 'DEBUG':
                log_line = f"[{log['timestamp']}] [{log['level']}] {log['message']}\n"
                self.log_text.insert(tk.END, log_line, log['level'])

        if float(self.log_text.yview()[1]) > 0.9:
            self.log_text.see(tk.END)

        self.log_text.configure(state='disabled')

    def clear_logs(self):
        self.log_buffer.clear()
        self.pending_logs.clear()
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        
    def add_log(self, message: str, level: str = "INFO"):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        level = level.upper()
        log_entry = {
            'message': message,
            'level': level,
            'timestamp': timestamp
        }

        self.log_buffer.append(log_entry)
        if len(self.log_buffer) > MAX_BUFFER_SIZE:
            self.log_buffer.pop(0)
            
        self.pending_logs.append(log_entry)
        self.schedule_update()


def setup_basic_logging() -> None:
    """设置基本日志系统，不包含GUI部分"""
    logger.remove()

    # 设置日志记录
    console_sink = logger.add(sys.stderr, colorize=True, level="INFO", enqueue=True)
    file_sink = logger.add(
        sink=Path("./cursorHelper_log") / "{time:YYYY-MM-DD}.log",
        rotation="1 day", 
        encoding="utf-8", 
        enqueue=True,
        retention="10 days",
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
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

def setup_gui_logging(app) -> None:
    """设置GUI日志系统"""
    def gui_sink(message):
        record = message.record
        level = record["level"].name
        text = record["message"]
        app.add_log(text, level)

    logger.add(
        sink=gui_sink,
        format="{message}",
        level="DEBUG",
        enqueue=True
    )

def main() -> None:
    root = None
    try:
        # 设置基本日志系统
        try:
            setup_basic_logging()
            logger.info(f"Cursor账号助手 v{__version__} 程序开始启动...")
        except Exception as log_error:
            # 日志设置失败不应该阻止程序启动
            print(f"日志设置失败: {log_error}")
        
        # 确保备份目录存在
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            logger.debug("备份目录检查完成")
        except Exception as dir_error:
            logger.warning(f"创建备份目录失败: {dir_error}")
        
        # 简化环境变量处理 - 使用最简单的方式加载
        try:
            load_dotenv()
            logger.debug("环境变量加载完成")
        except Exception as e:
            logger.warning(f"加载环境变量出错 (不影响基本功能): {str(e)}")
        
        # 主窗口创建和初始化
        try:
            logger.debug("准备创建主窗口...")
            root = tk.Tk()
            
            # 设置异常处理
            def report_callback_exception(exc, val, tb):
                import traceback
                err_msg = ''.join(traceback.format_exception(exc, val, tb))
                logger.error(f"未捕获的Tkinter异常: {err_msg}")
                try:
                    UI.show_error(root, "操作出错", f"{str(val)}\n请查看日志获取详细信息。")
                except:
                    messagebox.showerror("错误", f"操作出错: {str(val)}")
            
            root.report_callback_exception = report_callback_exception
            
            logger.debug("主窗口创建成功")
            
            # 设置窗口属性以确保可见
            root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+100+100")  # 设置窗口大小和位置
            root.lift()  # 将窗口提升到最前
            root.attributes('-topmost', True)  # 设置窗口置顶
            root.update()  # 强制窗口更新
            root.attributes('-topmost', False)  # 取消窗口置顶
            
            # 进一步确保窗口可见
            root.deiconify()  # 确保窗口不是最小化的
            
            logger.debug("初始化应用组件...")
            app = CursorApp(root)
            logger.debug("应用组件初始化完成")
            
            # 再次确保窗口更新和可见
            root.after(100, lambda: root.focus_force())  # 在短暂延时后强制获取焦点
            
            # 设置GUI日志系统
            logger.debug("设置GUI日志系统...")
            setup_gui_logging(app)
            logger.debug("GUI日志系统设置完成")
            
            logger.info("应用启动成功，进入主循环")
            root.mainloop()
        except Exception as gui_error:
            logger.error(f"GUI初始化失败: {gui_error}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            
            # 尝试显示一个基本的错误窗口
            if root:
                try:
                    root.withdraw()  # 隐藏主窗口
                    import tkinter.messagebox as messagebox
                    messagebox.showerror("启动错误", f"程序启动失败: {str(gui_error)}\n\n请检查日志文件获取详细信息。")
                except:
                    pass  # 如果连错误窗口都无法显示，只能放弃了
            
            sys.exit(1)  # 退出程序
            
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        
        if root:
            try:
                UI.show_error(root, "程序启动失败", str(e))
            except:
                pass  # 如果UI也无法初始化，至少我们记录了日志

# 在.env.example自动复制功能分离为独立函数
def copy_env_example_if_needed():
    try:
        from utils import Utils
        
        # 环境变量文件路径
        env_path = Utils.get_path('env')
        base_path = Utils.get_path('base')
        env_example_path = base_path / '.env.example'
        
        # 检查并创建.env文件
        if not env_path.exists() and env_example_path.exists():
            import shutil
            shutil.copy(env_example_path, env_path)
            logger.info("已从.env.example创建.env文件，请在配置中填写相关信息")
            return True
    except Exception as e:
        logger.error(f"处理环境变量文件时出错: {str(e)}")
    return False

if __name__ == "__main__":
    # 设置应用程序异常处理器
    def global_exception_handler(exctype, value, traceback):
        try:
            import traceback as tb_module
            error_msg = ''.join(tb_module.format_exception(exctype, value, traceback))
            
            # 尝试记录到日志
            try:
                logger.error(f"未捕获的异常: {error_msg}")
            except:
                pass
            
            # 显示错误消息框
            try:
                import tkinter.messagebox as messagebox
                messagebox.showerror("程序错误", f"发生未处理的错误:\n{value}\n\n详细信息已记录到日志文件。")
            except:
                # 如果无法显示GUI消息，输出到控制台
                print(f"严重错误: {error_msg}")
        except:
            # 如果异常处理器本身出现问题，使用系统默认处理
            sys.__excepthook__(exctype, value, traceback)
    
    # 设置全局异常处理器
    sys.excepthook = global_exception_handler
    
    # 先尝试复制环境变量文件
    copy_env_example_if_needed()
    # 然后启动主程序
    main()
