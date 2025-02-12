import tkinter as tk
from tkinter import messagebox, ttk
from generate_cursor_account import generate_cursor_account
from reset_ID import CursorResetter
from update_auth import CursorAuthUpdater
from loguru import logger
from dotenv import load_dotenv
from configlog import LogSetup
import os

class CursorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cursor账号管理工具")
        
        # 设置窗口大小和位置
        window_width = 450
        window_height = 310  # 调整窗口高度
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)
        
        # 初始化UI组件
        self.email_entry = None
        self.password_entry = None
        self.cookie_entry = None
        self.env_labels = {}  # 存储环境变量标签的引用
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        # 创建主框架，最小化padding
        self.main_frame = ttk.Frame(self.root, padding="3")
        self.main_frame.pack(fill=tk.X)
        
        self.create_env_info_frame()  # 添加环境变量信息框
        self.create_account_info_frame()
        self.create_cookie_frame()
        self.create_button_frame()
        
    def create_env_info_frame(self):
        """创建环境变量信息框架"""
        env_frame = ttk.LabelFrame(self.main_frame, text="环境变量信息", padding="2")
        env_frame.pack(fill=tk.X, padx=2, pady=(2,1))
        
        # 显示域名
        ttk.Label(env_frame, text="域名:").grid(row=0, column=0, sticky=tk.W, padx=2, pady=1)
        self.env_labels['domain'] = ttk.Label(env_frame, text=os.getenv('DOMAIN', '未设置'))
        self.env_labels['domain'].grid(row=0, column=1, sticky=tk.W, padx=2, pady=1)
        
        # 显示邮箱
        ttk.Label(env_frame, text="邮箱:").grid(row=1, column=0, sticky=tk.W, padx=2, pady=1)
        self.env_labels['email'] = ttk.Label(env_frame, text=os.getenv('EMAIL', '未设置'))
        self.env_labels['email'].grid(row=1, column=1, sticky=tk.W, padx=2, pady=1)
        
        # 显示密码
        ttk.Label(env_frame, text="密码:").grid(row=2, column=0, sticky=tk.W, padx=2, pady=1)
        self.env_labels['password'] = ttk.Label(env_frame, text=os.getenv('PASSWORD', '未设置'))
        self.env_labels['password'].grid(row=2, column=1, sticky=tk.W, padx=2, pady=1)
        
        env_frame.columnconfigure(1, weight=1)
        
    def create_account_info_frame(self):
        """创建账号信息框架"""
        info_frame = ttk.LabelFrame(self.main_frame, text="账号信息", padding="2")
        info_frame.pack(fill=tk.X, padx=2, pady=(2,1))
        
        # 邮箱输入框
        ttk.Label(info_frame, text="邮箱:").grid(row=0, column=0, sticky=tk.W, padx=2, pady=1)
        self.email_entry = ttk.Entry(info_frame, width=40)
        self.email_entry.grid(row=0, column=1, sticky=tk.EW, padx=2, pady=1)
        
        # 密码输入框
        ttk.Label(info_frame, text="密码:").grid(row=1, column=0, sticky=tk.W, padx=2, pady=1)
        self.password_entry = ttk.Entry(info_frame, width=40)
        self.password_entry.grid(row=1, column=1, sticky=tk.EW, padx=2, pady=1)
        
        info_frame.columnconfigure(1, weight=1)
        
    def create_cookie_frame(self):
        """创建Cookie设置框架"""
        cookie_frame = ttk.LabelFrame(self.main_frame, text="Cookie设置", padding="2")
        cookie_frame.pack(fill=tk.X, padx=2, pady=1)
        
        # Cookie输入框
        ttk.Label(cookie_frame, text="Cookie:").grid(row=0, column=0, sticky=tk.W, padx=2, pady=1)
        self.cookie_entry = ttk.Entry(cookie_frame, width=40)
        self.cookie_entry.grid(row=0, column=1, sticky=tk.EW, padx=2, pady=1)
        
        # 设置初始值
        self.cookie_entry.insert(0, "WorkosCursorSessionToken")
        
        cookie_frame.columnconfigure(1, weight=1)
        
    def create_button_frame(self):
        """创建按钮框架"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X)
        
        # 定义按钮样式
        style = ttk.Style()
        style.configure('Custom.TButton', padding=(12, 5))  # 适中的按钮内边距
        
        # 创建一个容器框架并设置权重使按钮居中
        container = ttk.Frame(button_frame)
        container.pack(pady=(5, 6))
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(4, weight=1)
        
        # 使用grid布局来精确控制按钮位置
        ttk.Button(container, text="生成账号", command=self.generate_account, style='Custom.TButton').grid(row=0, column=1, padx=5)
        ttk.Button(container, text="重置ID", command=self.reset_ID, style='Custom.TButton').grid(row=0, column=2, padx=5)
        ttk.Button(container, text="更新账号信息", command=self.update_auth, style='Custom.TButton').grid(row=0, column=3, padx=5)
        
        # 添加 powered by kto 标签
        powered_label = ttk.Label(button_frame, text="powered by kto 仅供学习使用", font=('Arial', 11))
        powered_label.pack(pady=(0, 5))
        
    def refresh_env_vars(self):
        """刷新环境变量显示"""
        load_dotenv()  # 重新加载环境变量
        self.env_labels['domain'].config(text=os.getenv('DOMAIN', '未设置'))
        self.env_labels['email'].config(text=os.getenv('EMAIL', '未设置'))
        self.env_labels['password'].config(text=os.getenv('PASSWORD', '未设置'))
        
    def generate_account(self):
        """生成账号"""
        try:
            email, password = generate_cursor_account()
            self.email_entry.delete(0, tk.END)
            self.email_entry.insert(0, email)
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, password)
            logger.success("账号生成成功")
            self.refresh_env_vars()  # 刷新环境变量显示
        except Exception as e:
            logger.error(f"生成账号错误: {e}")
            messagebox.showerror("错误", f"生成账号错误: {e}")
            
    def reset_ID(self):
        """重置ID"""
        try:
            resetter = CursorResetter()
            if resetter.reset():
                logger.info("重置机器码完成")
                messagebox.showinfo("结果", "重置机器码完成")
                self.refresh_env_vars()  # 刷新环境变量显示
            else:
                logger.error("重置机器码失败")
                messagebox.showerror("错误", "重置机器码失败")
        except Exception as e:
            logger.error(f"重置ID错误: {e}")
            messagebox.showerror("错误", f"重置ID错误: {e}")
            
    def update_auth(self):
        """更新认证信息"""
        try:
            cookie_str = self.cookie_entry.get().strip()
            if not self.validate_cookie(cookie_str):
                return
                
            updater = CursorAuthUpdater()
            updater.update_with_cookie(cookie_str)
            logger.info("更新登录信息完成")
            messagebox.showinfo("结果", "更新登录信息完成")
            self.cookie_entry.delete(0, tk.END)
            self.refresh_env_vars()  # 刷新环境变量显示
        except ValueError as e:
            logger.error(f"Cookie格式错误: {e}")
            messagebox.showerror("错误", f"Cookie格式错误: {e}")
        except Exception as e:
            logger.error(f"更新登录信息失败: {e}")
            messagebox.showerror("错误", f"更新登录信息失败: {e}")
            
    def validate_cookie(self, cookie_str: str) -> bool:
        """验证Cookie字符串"""
        if not cookie_str:
            messagebox.showerror("错误", "请输入Cookie字符串")
            return False
            
        if "WorkosCursorSessionToken=" not in cookie_str:
            messagebox.showerror("错误", "Cookie字符串格式不正确，必须包含 WorkosCursorSessionToken")
            return False
            
        return True


def log_setup():
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
    log_config = LogSetup(config=config_dict)
def main():
    log_setup()
    root = tk.Tk()
    app = CursorApp(root)
    root.mainloop()

if __name__ == "__main__":
    load_dotenv()
    main()
