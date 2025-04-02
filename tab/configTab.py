import os
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Dict, Optional
import sqlite3

from loguru import logger
from .ui import UI
from database import create_cursor_database

class ConfigTab(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        # 确保数据库存在
        create_cursor_database()
        self.setup_ui()
        self.load_env_vars()

    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建环境变量列表
        list_frame = UI.create_labeled_frame(main_frame, "环境变量配置")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 创建表格
        columns = ('变量名', '值', '来源')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)

        # 设置列
        for col in columns:
            self.tree.heading(col, text=col)
            if col == '来源':
                self.tree.column(col, width=100)
            else:
                self.tree.column(col, width=150)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 布局
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建按钮框架
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # 添加按钮
        ttk.Button(button_frame, text="添加变量", command=self.add_var,
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="编辑变量", command=self.edit_var,
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除变量", command=self.delete_var,
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存更改", command=self.save_changes,
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="同步配置", command=self.sync_config,
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)

        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.selected_item = None

    def load_env_vars(self):
        """从.env文件和数据库加载环境变量"""
        try:
            # 清空现有项
            for item in self.tree.get_children():
                self.tree.delete(item)

            # 从数据库加载配置
            self.load_from_database()

            # 从.env文件加载配置
            self.load_from_env_file()

            logger.info("已加载环境变量配置")
        except Exception as e:
            logger.error(f"加载环境变量失败: {str(e)}")
            UI.show_error(self.winfo_toplevel(), "加载失败", str(e))

    def load_from_database(self):
        """从数据库加载配置"""
        try:
            conn = sqlite3.connect('cursor.db')
            cursor = conn.cursor()
            
            # 获取所有配置
            cursor.execute('''
                SELECT domain, api_key, moe_mail_url, cookie_str 
                FROM configurations 
                ORDER BY created_at DESC 
                LIMIT 1
            ''')
            config = cursor.fetchone()
            
            if config:
                domain, api_key, moe_mail_url, cookie_str = config
                logger.debug(f"从数据库加载配置: domain={domain}, "
                           f"api_key={api_key}, "
                           f"moe_mail_url={moe_mail_url}, "
                           f"cookie_str={cookie_str}")
                
                if api_key:
                    self.tree.insert('', 'end', values=('API_KEY', api_key, f'数据库({domain})'))
                if moe_mail_url:
                    self.tree.insert('', 'end', values=('MOE_MAIL_URL', moe_mail_url, f'数据库({domain})'))
                if cookie_str:
                    self.tree.insert('', 'end', values=('COOKIES_STR', cookie_str, f'数据库({domain})'))
            else:
                logger.warning("数据库中没有找到配置记录")
            
            conn.close()
        except Exception as e:
            logger.error(f"从数据库加载配置失败: {str(e)}")

    def load_from_env_file(self):
        """从.env文件加载配置"""
        try:
            env_path = Path('.env')
            if not env_path.exists():
                logger.warning("未找到.env文件")
                return

            # 收集所有配置
            configs = {}

            # 从系统环境变量加载
            for key in ['DOMAIN', 'EMAIL', 'PASSWORD', 'API_KEY', 'MOE_MAIL_URL', 'COOKIES_STR']:
                if value := os.getenv(key):
                    # 检查是否已存在
                    exists = False
                    for item in self.tree.get_children():
                        if self.tree.item(item)['values'][0] == key:
                            exists = True
                            break
                    if not exists:
                        self.tree.insert('', 'end', values=(key, value, '环境变量'))
                        logger.debug(f"从环境变量加载: {key} = {value}")
                        configs[key] = value

            # 从.env文件加载
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip("'\"")
                            # 检查是否已存在
                            exists = False
                            for item in self.tree.get_children():
                                if self.tree.item(item)['values'][0] == key:
                                    exists = True
                                    break
                            if not exists:
                                self.tree.insert('', 'end', values=(key, value, '环境文件'))
                                logger.debug(f"从.env文件加载: {key} = {value}")
                                configs[key] = value
                        except ValueError:
                            continue

            # 同步到数据库
            if configs:
                logger.info(f"同步环境变量到数据库: {configs}")
                self.update_database_config(configs)

        except Exception as e:
            logger.error(f"从.env文件加载配置失败: {str(e)}")

    def save_changes(self):
        """保存环境变量到.env文件和数据库"""
        try:
            # 保存到.env文件
            env_path = Path('.env')
            env_vars = {}

            # 收集所有环境变量
            for item in self.tree.get_children():
                key, value, source = self.tree.item(item)['values']
                env_vars[key] = value

            # 写入.env文件
            with open(env_path, 'w', encoding='utf-8') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}='{value}'\n")

            # 更新系统环境变量
            for key, value in env_vars.items():
                os.environ[key] = value

            # 更新数据库配置
            self.update_database_config(env_vars)

            logger.info("已保存环境变量配置")
            UI.show_success(self.winfo_toplevel(), "环境变量已更新")
        except Exception as e:
            logger.error(f"保存环境变量失败: {str(e)}")
            UI.show_error(self.winfo_toplevel(), "保存失败", str(e))

    def update_database_config(self, env_vars: Dict[str, str]):
        """更新数据库配置表"""
        try:
            conn = sqlite3.connect('cursor.db')
            cursor = conn.cursor()

            # 获取当前域名
            cursor.execute('SELECT domain FROM configurations ORDER BY created_at DESC LIMIT 1')
            result = cursor.fetchone()
            current_domain = result[0] if result else None
            logger.debug(f"当前域名: {current_domain}")

            # 准备配置值
            domain = env_vars.get('DOMAIN', 'default')
            api_key = env_vars.get('API_KEY')
            moe_mail_url = env_vars.get('MOE_MAIL_URL', '')  # 使用空字符串而不是 None
            cookie_str = env_vars.get('COOKIES_STR')

            logger.debug(f"准备更新配置: domain={domain}, api_key={api_key}, "
                        f"moe_mail_url={moe_mail_url}, cookie_str={cookie_str}")

            # 如果没有配置记录，创建新记录
            if not current_domain:
                logger.info("没有找到现有配置，创建新记录")
                cursor.execute('''
                    INSERT INTO configurations (
                        domain, api_key, moe_mail_url, cookie_str, 
                        created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (domain, api_key, moe_mail_url, cookie_str))
                logger.debug(f"插入新配置: domain={domain}, "
                           f"api_key={api_key}, "
                           f"moe_mail_url={moe_mail_url}")
            else:
                # 更新现有配置
                logger.info(f"更新现有配置，域名: {current_domain}")
                cursor.execute('''
                    UPDATE configurations 
                    SET api_key = ?, 
                        moe_mail_url = ?, 
                        cookie_str = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE domain = ?
                ''', (api_key, moe_mail_url, cookie_str, current_domain))
                logger.debug(f"更新配置: api_key={api_key}, "
                           f"moe_mail_url={moe_mail_url}, "
                           f"cookie_str={cookie_str}")

            conn.commit()
            logger.debug("已更新数据库配置")

            # 验证更新
            cursor.execute('SELECT * FROM configurations ORDER BY created_at DESC LIMIT 1')
            updated_config = cursor.fetchone()
            logger.info(f"更新后的配置: {updated_config}")

        except Exception as e:
            logger.error(f"更新数据库配置失败: {str(e)}")
            raise
        finally:
            conn.close()

    def sync_config(self):
        """同步配置到数据库"""
        try:
            # 获取所有配置
            configs = {}
            for item in self.tree.get_children():
                key, value, source = self.tree.item(item)['values']
                configs[key] = value
                logger.debug(f"收集到配置: {key} = {value} (来源: {source})")

            logger.info(f"准备同步的配置: {configs}")

            # 更新数据库
            self.update_database_config(configs)
            
            # 重新加载配置
            self.load_env_vars()
            
            UI.show_success(self.winfo_toplevel(), "配置已同步到数据库")
        except Exception as e:
            logger.error(f"同步配置失败: {str(e)}")
            UI.show_error(self.winfo_toplevel(), "同步失败", str(e))

    def add_var(self):
        """添加新的环境变量"""
        dialog = EnvVarDialog(self.winfo_toplevel())
        if dialog.result:
            key, value = dialog.result
            self.tree.insert('', 'end', values=(key, value, '手动添加'))
            logger.debug(f"已添加环境变量: {key}")
            # 同步到数据库
            self.sync_config()

    def edit_var(self):
        """编辑选中的环境变量"""
        if not self.selected_item:
            UI.show_error(self.winfo_toplevel(), "编辑失败", "请先选择要编辑的变量")
            return

        key, value, source = self.tree.item(self.selected_item)['values']
        dialog = EnvVarDialog(self.winfo_toplevel(), key, value)
        if dialog.result:
            new_key, new_value = dialog.result
            self.tree.item(self.selected_item, values=(new_key, new_value, source))
            logger.debug(f"已更新环境变量: {key} -> {new_key}")
            # 同步到数据库
            self.sync_config()

    def delete_var(self):
        """删除选中的环境变量"""
        if not self.selected_item:
            UI.show_error(self.winfo_toplevel(), "删除失败", "请先选择要删除的变量")
            return

        key, value, source = self.tree.item(self.selected_item)['values']
        if messagebox.askyesno("确认删除", f"确定要删除环境变量 {key} 吗？"):
            self.tree.delete(self.selected_item)
            logger.debug(f"已删除环境变量: {key}")
            # 同步到数据库
            self.sync_config()

    def on_select(self, event):
        """处理选择事件"""
        selected_items = self.tree.selection()
        if selected_items:
            self.selected_item = selected_items[0]
        else:
            self.selected_item = None

class EnvVarDialog:
    def __init__(self, parent, key: str = "", value: str = ""):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("环境变量")
        self.dialog.geometry("300x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 创建输入框
        ttk.Label(self.dialog, text="变量名:").pack(pady=5)
        self.key_entry = ttk.Entry(self.dialog)
        self.key_entry.insert(0, key)
        self.key_entry.pack(pady=5)

        ttk.Label(self.dialog, text="值:").pack(pady=5)
        self.value_entry = ttk.Entry(self.dialog)
        self.value_entry.insert(0, value)
        self.value_entry.pack(pady=5)

        # 创建按钮
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="确定", command=self.confirm,
                  style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel,
                  style='Custom.TButton').pack(side=tk.LEFT, padx=5)

        # 等待对话框关闭
        self.dialog.wait_window()

    def confirm(self):
        """确认输入"""
        key = self.key_entry.get().strip()
        value = self.value_entry.get().strip()
        
        if not key:
            UI.show_error(self.dialog, "输入错误", "变量名不能为空")
            return

        self.result = (key, value)
        self.dialog.destroy()

    def cancel(self):
        """取消输入"""
        self.dialog.destroy() 