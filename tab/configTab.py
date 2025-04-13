import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict

from loguru import logger

from utils import ConfigManager, Result, Utils
from .ui import UI

PADDING = 10
ENTRY_WIDTH = 50
BUTTON_WIDTH = 15

class ConfigTab(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.entries = {}
        self.config_frame = None
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        # 创建配置框架
        self.config_frame = UI.create_labeled_frame(self, "系统配置")
        
        # 核心配置项 - 只保留域名、API密钥和邮箱服务地址
        self.core_config_items = [
            ('DOMAIN', '域名', '默认域名，用于生成邮箱和注册'),
            ('API_KEY', 'API密钥', '邮箱服务的API密钥'),
            ('MOE_MAIL_URL', '邮箱服务地址', '邮箱服务的URL地址')
        ]
        
        # 动态加载配置项
        self.initialize_config_entries()
        
        # 按钮框架
        button_frame = ttk.Frame(self.config_frame, style='TFrame')
        button_frame.grid(row=len(self.core_config_items) + 1, column=0, columnspan=2, pady=PADDING*2)
        
        # 保存按钮
        save_button = ttk.Button(
            button_frame,
            text="保存配置",
            command=self.save_config,
            style='Custom.TButton',
            width=BUTTON_WIDTH
        )
        save_button.pack(side=tk.LEFT, padx=PADDING)
        
        # 重置按钮
        reset_button = ttk.Button(
            button_frame,
            text="恢复默认",
            command=self.reset_config,
            style='Custom.TButton',
            width=BUTTON_WIDTH
        )
        reset_button.pack(side=tk.LEFT, padx=PADDING)
        
        # 应用按钮
        apply_button = ttk.Button(
            button_frame,
            text="应用配置",
            command=self.apply_config,
            style='Custom.TButton',
            width=BUTTON_WIDTH
        )
        apply_button.pack(side=tk.LEFT, padx=PADDING)
        
        # 添加查看.env文件按钮框架
        view_env_frame = ttk.Frame(self, style='TFrame')
        view_env_frame.pack(pady=(15, 0), fill=tk.X)
        
        # 添加查看.env文件按钮
        view_env_button = ttk.Button(
            view_env_frame,
            text="查看.env文件",
            command=self.view_env_file,
            style='Custom.TButton',
            width=BUTTON_WIDTH
        )
        view_env_button.pack(side=tk.LEFT, padx=PADDING)
        
        # 添加提示文本
        env_hint_label = ttk.Label(
            view_env_frame,
            text="点击查看完整的.env文件内容，包括所有配置项",
            style='Footer.TLabel'
        )
        env_hint_label.pack(side=tk.LEFT, padx=PADDING)
    
    def initialize_config_entries(self):
        """初始化配置项输入框"""
        # 先清空现有项
        for widget in self.config_frame.winfo_children():
            if isinstance(widget, ttk.Frame) and widget.winfo_children() and isinstance(widget.winfo_children()[0], ttk.Label):
                widget.destroy()
        
        self.entries = {}  # 重置entries字典
        
        # 添加核心配置项
        for row, (var_name, label_text, tooltip) in enumerate(self.core_config_items):
            self.add_config_entry(row, var_name, label_text, tooltip)
    
    def add_config_entry(self, row, var_name, label_text, tooltip=None):
        """添加一个配置项输入框"""
        # 创建标签
        label = ttk.Label(self.config_frame, text=f"{label_text}:", style='TLabel')
        label.grid(row=row, column=0, sticky='w', padx=PADDING, pady=(PADDING, 0))
        
        # 创建输入框
        entry = ttk.Entry(self.config_frame, width=ENTRY_WIDTH)
        entry.grid(row=row, column=1, sticky='we', padx=PADDING, pady=(PADDING, 0))
        
        # 保存到字典中
        self.entries[var_name] = entry
        
        # 添加提示信息（如果有）
        if tooltip:
            UI.create_tooltip(entry, tooltip)
    
    def load_config(self):
        """加载配置到界面"""
        try:
            # 通过ConfigManager加载配置
            result = ConfigManager.load_config()
            if not result.success:
                logger.error(f"加载配置失败: {result.message}")
                UI.show_error(self.winfo_toplevel(), "加载配置失败", result.message)
                return
                
            config = result.data
            
            # 检查是否有新的配置项在.env中但不在UI中
            env_keys = set(config.keys())
            ui_keys = set(key for key, _, _ in self.core_config_items)
            
            # 如果有新的配置项，需要更新core_config_items并重新初始化UI
            # 但只添加非账号相关的配置项（不添加EMAIL、PASSWORD、COOKIES_STR）
            new_config_keys = env_keys - ui_keys
            account_keys = {'EMAIL', 'PASSWORD', 'COOKIES_STR'}
            if new_config_keys - account_keys:
                for key in new_config_keys:
                    if key not in account_keys:
                        # 添加新的配置项到core_config_items
                        self.core_config_items.append((key, key, f'{key}配置项'))
                # 重新初始化UI
                self.initialize_config_entries()
            
            # 更新所有输入框的值
            for key, entry in self.entries.items():
                entry.delete(0, tk.END)
                entry.insert(0, config.get(key, ""))
                
            logger.debug(f"配置已加载到界面，共 {len(self.entries)} 项")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            UI.show_error(self.winfo_toplevel(), "加载配置失败", str(e))
    
    def get_current_config(self) -> Dict[str, str]:
        """获取当前界面上的配置"""
        config = {}
        for key, entry in self.entries.items():
            config[key] = entry.get().strip()
        
        # 获取完整的配置，包括账号相关配置
        full_config = ConfigManager.load_config()
        if full_config.success:
            # 保留原有的EMAIL、PASSWORD、COOKIES_STR配置
            for key in ['EMAIL', 'PASSWORD', 'COOKIES_STR']:
                if key in full_config.data and key not in config:
                    config[key] = full_config.data[key]
        
        return config
    
    def save_config(self):
        """保存配置"""
        config = self.get_current_config()
        try:
            # 通过ConfigManager保存配置
            result = ConfigManager.save_config(config)
            
            if result.success:
                logger.info("配置已保存到.env文件")
                UI.show_success(self.winfo_toplevel(), "配置已保存")
            else:
                logger.error(f"保存配置失败: {result.message}")
                UI.show_error(self.winfo_toplevel(), "保存配置失败", result.message)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            UI.show_error(self.winfo_toplevel(), "保存配置失败", str(e))
    
    def reset_config(self):
        """重置为默认配置"""
        if messagebox.askyesno("确认重置", "确定要恢复默认配置吗？当前配置将被覆盖。"):
            try:
                # 获取当前账号配置
                current_config = ConfigManager.load_config()
                account_config = {}
                if current_config.success:
                    for key in ['EMAIL', 'PASSWORD', 'COOKIES_STR']:
                        if key in current_config.data:
                            account_config[key] = current_config.data[key]
                
                # 通过ConfigManager重置配置
                result = ConfigManager.reset_to_default()
                
                if result.success:
                    # 如果有账号配置，还原它们
                    if account_config:
                        ConfigManager.save_config(account_config)
                    
                    logger.info("已重置为默认配置")
                    self.load_config()  # 重新加载配置到界面
                    UI.show_success(self.winfo_toplevel(), "已重置为默认配置")
                else:
                    logger.error(f"重置配置失败: {result.message}")
                    UI.show_error(self.winfo_toplevel(), "重置配置失败", result.message)
            except Exception as e:
                logger.error(f"重置配置失败: {e}")
                UI.show_error(self.winfo_toplevel(), "重置配置失败", str(e))
    
    def apply_config(self):
        """应用配置到当前会话，但不保存到文件"""
        config = self.get_current_config()
        
        try:
            # 通过ConfigManager应用配置
            result = ConfigManager.apply_config(config)
            
            if result.success:
                logger.info("配置已应用到当前会话")
                UI.show_success(self.winfo_toplevel(), "配置已应用到当前会话")
            else:
                logger.error(f"应用配置失败: {result.message}")
                UI.show_error(self.winfo_toplevel(), "应用配置失败", result.message)
        except Exception as e:
            logger.error(f"应用配置失败: {e}")
            UI.show_error(self.winfo_toplevel(), "应用配置失败", str(e))
    
    def view_env_file(self):
        """查看.env文件内容"""
        try:
            # 获取.env文件路径
            env_path = Utils.get_path('env')
            if not env_path.exists():
                UI.show_warning(self.winfo_toplevel(), ".env文件不存在")
                return
            
            # 读取.env文件内容
            env_content = env_path.read_text(encoding='utf-8')
            
            # 创建一个新窗口显示.env文件内容
            env_window = tk.Toplevel(self.winfo_toplevel())
            env_window.title(".env文件内容")
            env_window.geometry("600x400")
            UI.center_window(env_window, 600, 400)
            env_window.resizable(True, True)
            env_window.transient(self.winfo_toplevel())
            env_window.grab_set()
            
            # 添加一个滚动文本框
            text_frame = ttk.Frame(env_window, style='TFrame')
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 添加标题
            title_label = ttk.Label(
                text_frame, 
                text=f".env文件位置: {env_path}",
                style="Footer.TLabel"
            )
            title_label.pack(side=tk.TOP, pady=(0, 5), anchor='w')
            
            # 添加编辑模式开关
            edit_var = tk.BooleanVar(value=False)
            
            def toggle_edit_mode():
                edit_mode = edit_var.get()
                if edit_mode:
                    text_box.config(state=tk.NORMAL)
                    save_button.config(state=tk.NORMAL)
                else:
                    text_box.config(state=tk.DISABLED)
                    save_button.config(state=tk.DISABLED)
            
            edit_frame = ttk.Frame(text_frame, style='TFrame')
            edit_frame.pack(side=tk.TOP, pady=(0, 5), fill=tk.X)
            
            edit_check = ttk.Checkbutton(
                edit_frame,
                text="启用编辑模式",
                variable=edit_var,
                command=toggle_edit_mode,
                style='TCheckbutton'
            )
            edit_check.pack(side=tk.LEFT)
            
            edit_warning = ttk.Label(
                edit_frame,
                text="警告: 直接编辑可能会导致配置出错，请谨慎操作",
                style="Footer.TLabel",
                foreground=UI.COLORS['error']
            )
            edit_warning.pack(side=tk.LEFT, padx=10)
            
            # 添加滚动文本框
            text_box = scrolledtext.ScrolledText(
                text_frame,
                wrap=tk.WORD,
                width=70,
                height=20,
                font=("Consolas", 10)
            )
            text_box.pack(fill=tk.BOTH, expand=True)
            text_box.insert(tk.END, env_content)
            text_box.config(state=tk.DISABLED)  # 设为只读
            
            # 添加一个按钮框架
            button_frame = ttk.Frame(env_window, style='TFrame')
            button_frame.pack(fill=tk.X, pady=10)
            
            # 添加保存修改按钮
            def save_changes():
                try:
                    modified_content = text_box.get(1.0, tk.END)
                    env_path.write_text(modified_content, encoding='utf-8')
                    
                    # 刷新系统配置
                    self.load_config()
                    
                    UI.show_success(env_window, "保存成功")
                    logger.info("已保存修改后的.env文件")
                    
                    # 保存后关闭编辑模式
                    edit_var.set(False)
                    toggle_edit_mode()
                except Exception as e:
                    logger.error(f"保存.env文件失败: {e}")
                    UI.show_error(env_window, "保存失败", str(e))
            
            save_button = ttk.Button(
                button_frame,
                text="保存修改",
                command=save_changes,
                style='Custom.TButton',
                width=BUTTON_WIDTH,
                state=tk.DISABLED  # 初始状态为禁用
            )
            save_button.pack(side=tk.LEFT, padx=10)
            
            # 添加刷新按钮
            def refresh_content():
                try:
                    new_content = env_path.read_text(encoding='utf-8')
                    
                    # 保存当前的编辑状态
                    was_editing = edit_var.get()
                    
                    # 临时启用编辑，刷新内容
                    text_box.config(state=tk.NORMAL)
                    text_box.delete(1.0, tk.END)
                    text_box.insert(tk.END, new_content)
                    
                    # 恢复之前的编辑状态
                    if not was_editing:
                        text_box.config(state=tk.DISABLED)
                    
                    UI.show_success(env_window, "刷新成功")
                except Exception as e:
                    logger.error(f"刷新.env文件内容失败: {e}")
                    UI.show_error(env_window, "刷新失败", str(e))
            
            refresh_button = ttk.Button(
                button_frame,
                text="刷新",
                command=refresh_content,
                style='Custom.TButton',
                width=BUTTON_WIDTH
            )
            refresh_button.pack(side=tk.LEFT, padx=10)
            
            # 添加关闭按钮
            close_button = ttk.Button(
                button_frame,
                text="关闭",
                command=env_window.destroy,
                style='Custom.TButton',
                width=BUTTON_WIDTH
            )
            close_button.pack(side=tk.RIGHT, padx=10)
            
            # 添加应用配置按钮
            def apply_env_config():
                try:
                    # 先保存当前内容
                    if edit_var.get():
                        save_changes()
                    
                    # 重新加载配置并应用
                    self.load_config()
                    self.apply_config()
                    
                    UI.show_success(env_window, "配置已应用")
                except Exception as e:
                    logger.error(f"应用配置失败: {e}")
                    UI.show_error(env_window, "应用配置失败", str(e))
            
            apply_button = ttk.Button(
                button_frame,
                text="应用配置",
                command=apply_env_config,
                style='Custom.TButton',
                width=BUTTON_WIDTH
            )
            apply_button.pack(side=tk.RIGHT, padx=10)
            
            logger.debug("已打开.env文件查看窗口")
            
        except Exception as e:
            logger.error(f"查看.env文件失败: {e}")
            UI.show_error(self.winfo_toplevel(), "查看.env文件失败", str(e)) 