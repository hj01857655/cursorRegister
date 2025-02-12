import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, Optional
from generate_cursor_account import generate_cursor_account
from reset_ID import CursorResetter
from update_auth import CursorAuthUpdater
from loguru import logger
from dotenv import load_dotenv
from configlog import LogSetup
import os

class CursorApp:
    def __init__(self, root: tk.Tk) -> None:
        """初始化Cursor账号管理工具应用

        Args:
            root (tk.Tk): 主窗口实例
        """
        self.root = root
        self.root.title("Cursor账号管理工具")
        self._configure_window()
        self._init_variables()
        self.setup_ui()

    def _configure_window(self) -> None:
        """配置窗口大小和位置"""
        window_width = 450
        window_height = 360
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)

    def _init_variables(self) -> None:
        """初始化类变量"""
        self.email_entry: Optional[ttk.Entry] = None
        self.password_entry: Optional[ttk.Entry] = None
        self.cookie_entry: Optional[ttk.Entry] = None
        self.env_labels: Dict[str, ttk.Label] = {}
        self._create_styles()

    def _create_styles(self) -> None:
        """创建自定义样式"""
        style = ttk.Style()
        style.configure('Custom.TButton', padding=(12, 5))
        style.configure('Info.TLabel', font=('Arial', 11))

    def setup_ui(self) -> None:
        """设置UI界面"""
        self.main_frame = ttk.Frame(self.root, padding="3")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_frames()

    def _create_frames(self) -> None:
        """创建所有UI框架"""
        self.create_env_info_frame()
        self.create_account_info_frame()
        self.create_cookie_frame()
        self.create_button_frame()

    def create_env_info_frame(self) -> None:
        """创建环境变量信息框架"""
        env_frame = ttk.LabelFrame(self.main_frame, text="环境变量信息", padding="5")
        env_frame.pack(fill=tk.X, padx=5, pady=(5,2))

        env_vars = [
            ('domain', '域名'),
            ('email', '邮箱'),
            ('password', '密码')
        ]

        for row, (var_name, label_text) in enumerate(env_vars):
            ttk.Label(env_frame, text=f"{label_text}:").grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2
            )
            self.env_labels[var_name] = ttk.Label(
                env_frame, 
                text=os.getenv(var_name.upper(), '未设置')
            )
            self.env_labels[var_name].grid(
                row=row, column=1, sticky=tk.W, padx=5, pady=2
            )

        env_frame.columnconfigure(1, weight=1)

    def create_account_info_frame(self) -> None:
        """创建账号信息框架"""
        info_frame = ttk.LabelFrame(self.main_frame, text="账号信息", padding="5")
        info_frame.pack(fill=tk.X, padx=5, pady=2)

        # 创建输入框
        fields = [
            ('email_entry', '邮箱'),
            ('password_entry', '密码')
        ]

        for row, (field_name, label_text) in enumerate(fields):
            ttk.Label(info_frame, text=f"{label_text}:").grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2
            )
            entry = ttk.Entry(info_frame, width=40)
            entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=2)
            setattr(self, field_name, entry)

        info_frame.columnconfigure(1, weight=1)

    def create_cookie_frame(self) -> None:
        """创建Cookie设置框架"""
        cookie_frame = ttk.LabelFrame(self.main_frame, text="Cookie设置", padding="5")
        cookie_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(cookie_frame, text="Cookie:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.cookie_entry = ttk.Entry(cookie_frame, width=40)
        self.cookie_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        self.cookie_entry.insert(0, "WorkosCursorSessionToken")

        cookie_frame.columnconfigure(1, weight=1)

    def create_button_frame(self) -> None:
        """创建按钮框架"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=5)

        buttons = [
            ("生成账号", self.generate_account),
            ("重置ID", self.reset_ID),
            ("更新账号信息", self.update_auth)
        ]

        container = ttk.Frame(button_frame)
        container.pack(pady=5)

        for col, (text, command) in enumerate(buttons):
            ttk.Button(
                container,
                text=text,
                command=command,
                style='Custom.TButton'
            ).grid(row=0, column=col, padx=5)

        ttk.Label(
            button_frame,
            text="powered by kto 仅供学习使用",
            style='Info.TLabel'
        ).pack(pady=5)

    def refresh_env_vars(self) -> None:
        """刷新环境变量显示"""
        load_dotenv()
        for var_name, label in self.env_labels.items():
            label.config(text=os.getenv(var_name.upper(), '未设置'))

    def generate_account(self) -> None:
        """生成账号"""
        try:
            email, password = generate_cursor_account()
            self._update_entry_values(email, password)
            logger.success("账号生成成功")
            self.refresh_env_vars()
        except Exception as e:
            self._handle_error("生成账号错误", e)

    def _update_entry_values(self, email: str, password: str) -> None:
        """更新输入框的值"""
        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, email)
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, password)

    def reset_ID(self) -> None:
        """重置ID"""
        try:
            resetter = CursorResetter()
            if resetter.reset():
                self._show_success("重置机器码完成")
                self.refresh_env_vars()
            else:
                raise Exception("重置失败")
        except Exception as e:
            self._handle_error("重置ID错误", e)

    def update_auth(self) -> None:
        """更新认证信息"""
        try:
            cookie_str = self.cookie_entry.get().strip()
            if not self._validate_cookie(cookie_str):
                return

            updater = CursorAuthUpdater()
            updater.update_with_cookie(cookie_str)
            self._show_success("更新登录信息完成")
            self.cookie_entry.delete(0, tk.END)
            self.refresh_env_vars()
        except Exception as e:
            self._handle_error("更新登录信息失败", e)

    def _validate_cookie(self, cookie_str: str) -> bool:
        """验证Cookie字符串

        Args:
            cookie_str (str): Cookie字符串

        Returns:
            bool: 验证是否通过
        """
        if not cookie_str:
            messagebox.showerror("错误", "请输入Cookie字符串")
            return False

        if "WorkosCursorSessionToken=" not in cookie_str:
            messagebox.showerror("错误", "Cookie字符串格式不正确，必须包含 WorkosCursorSessionToken")
            return False

        return True

    def _handle_error(self, title: str, error: Exception) -> None:
        """统一错误处理

        Args:
            title (str): 错误标题
            error (Exception): 错误异常
        """
        logger.error(f"{title}: {error}")
        messagebox.showerror("错误", f"{title}: {error}")

    def _show_success(self, message: str) -> None:
        """显示成功消息

        Args:
            message (str): 成功消息
        """
        logger.info(message)
        messagebox.showinfo("结果", message)

def setup_logging() -> None:
    """设置日志配置"""
    config_dict = {
        '日志路径': './cursorRegister_log',
        '日志级别': 'DEBUG',
        '颜色化': '开启',
        '日志轮转': '10 MB',
        '日志保留时间': '14 days',
        '压缩方式': 'gz',
        '控制台模式': '关闭',
        '记录日志': '开启'
    }
    LogSetup(config=config_dict)

def main() -> None:
    """主程序入口"""
    load_dotenv()
    setup_logging()
    root = tk.Tk()
    app = CursorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
