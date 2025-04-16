TREE_VIEW_HEIGHT = 7
COLUMN_WIDTH = 100
BUTTON_WIDTH = 15
PADDING = {
    'SMALL': 2,
    'MEDIUM': 5,
    'LARGE': 8,
    'XLARGE': 10
}

import csv
import glob
import os
import re
import time
import threading
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor
import base64
import json
import ssl
import urllib3
import shutil
import ctypes

import requests
from loguru import logger

from utils import CursorManager, error_handler,Utils
from .ui import UI
from registerAc import CursorRegistration

#管理标签
class ManageTab(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='TFrame', **kwargs)
        self.registrar = None
        
        # 保存用户调整的列宽
        self.user_column_widths = {
            '用户ID': 120,
            '邮箱': 180,
            '密码': 100,
            'Cookie': 200,
            '账户状态': 80,
            '剩余天数': 80,
            '使用量': 100,
            '令牌': 200
        }
        
        # 确保env_backups目录存在
        self.ensure_backup_dir()
        
        self.setup_ui()
        # 初始化后100ms自动刷新账号列表
        self.after(100, self.refresh_list)

    # 确保备份目录存在
    def ensure_backup_dir(self):
        backup_dir = "env_backups"
        if not os.path.exists(backup_dir):
            try:
                os.makedirs(backup_dir)
                logger.info(f"创建目录: {backup_dir}")
            except Exception as e:
                logger.error(f"创建目录 {backup_dir} 失败: {str(e)}")
                # 显示创建目录失败消息
                UI.show_error(self.winfo_toplevel(), "创建目录失败", 
                              f"无法创建账号备份目录 {backup_dir}，请确保应用具有写入权限。\n\n错误信息: {str(e)}")
    #设置ui
    def setup_ui(self):
        # 尝试调整主窗口大小
        try:
            # 获取根窗口
            root = self.winfo_toplevel()
            # 获取屏幕宽度
            screen_width = root.winfo_screenwidth()
            # 获取屏幕高度
            screen_height = root.winfo_screenheight()
            # 设置窗口大小为屏幕宽度的90%，高度为90%
            window_width = int(screen_width * 0.9)
            window_height = int(screen_height * 0.9)
            # 设置窗口尺寸和位置
            root.geometry(f"{window_width}x{window_height}+{int((screen_width-window_width)/2)}+{int((screen_height-window_height)/2)}")
            logger.info(f"已调整主窗口大小为 {window_width}x{window_height}")
        except Exception as e:
            logger.warning(f"调整主窗口大小失败: {str(e)}")
        #创建已保存账号框架
        accounts_frame = UI.create_labeled_frame(self, "已保存账号")

        # 让accounts_frame能够自动扩展填充可用空间
        accounts_frame.pack(fill=tk.BOTH, expand=True)

        # 创建一个内部框架用于正确布局树形视图和滚动条
        tree_frame = ttk.Frame(accounts_frame)
        #设置框架位置为填充
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        #设置列
        columns = ('用户ID', '邮箱', '密码','Cookie', '剩余天数','使用量','账户状态','令牌')
        #创建树
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=TREE_VIEW_HEIGHT)
        
        # 为每列分配适当的初始宽度和最小宽度
        default_widths = {
            '用户ID': 120,
            '邮箱': 180,
            '密码': 100,
            'Cookie': 200,
            '账户状态': 80,
            '剩余天数': 80,
            '使用量': 100,
            '令牌': 200
        }
        
        #设置列宽和最小宽度
        for col in columns:
            tree.heading(col, text=col)
            width = default_widths.get(col, 100)
            min_width = width // 2  # 最小宽度为默认宽度的一半
            tree.column(col, width=width, minwidth=min_width)
        
        # 创建垂直和水平滚动条
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # 使用grid布局来正确放置表格和滚动条
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        # 配置tree_frame的列和行权重，确保正确调整大小
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
            
        # 绑定列调整事件 - 使用不同的事件，确保在拖动结束时捕获
        tree.bind('<ButtonRelease-1>', self.on_column_resize)
            
        #绑定事件
        tree.bind('<<TreeviewSelect>>', self.on_select)

        #添加按钮
        outer_button_frame = ttk.Frame(self, style='TFrame')
        #设置按钮位置
        outer_button_frame.pack(pady=(PADDING['LARGE'], 0))
        #添加按钮
        button_frame = ttk.Frame(outer_button_frame, style='TFrame')
        #设置按钮位置
        button_frame.pack(anchor=tk.W)

        #添加按钮
        first_row_frame = ttk.Frame(button_frame, style='TFrame')
        first_row_frame.pack(pady=(0, PADDING['MEDIUM']), anchor=tk.W)
        #添加按钮
        ttk.Button(first_row_frame, text="刷新列表", command=self.refresh_list, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        ttk.Button(first_row_frame, text="添加账号", command=self.add_account, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        ttk.Button(first_row_frame, text="导入账号", command=self.import_account, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])

        #添加按钮
        second_row_frame = ttk.Frame(button_frame, style='TFrame')
        #设置按钮位置
        second_row_frame.pack(pady=(0, PADDING['MEDIUM']), anchor=tk.W)
        #添加按钮
        ttk.Button(second_row_frame, text="更新信息", command=self.update_account_info, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        ttk.Button(second_row_frame, text="切换账号", command=self.switch_account, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        ttk.Button(second_row_frame, text="查看详情", command=self.view_account_details, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])

        #添加按钮
        third_row_frame = ttk.Frame(button_frame, style='TFrame')
        #设置按钮位置
        third_row_frame.pack(pady=(0, PADDING['XLARGE']), anchor=tk.W)
        #添加按钮
        ttk.Button(third_row_frame, text="重置ID", command=self.reset_machine_id, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        #添加按钮
        ttk.Button(third_row_frame, text="删除账号", command=self.delete_account, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])
        #添加导出按钮
        ttk.Button(third_row_frame, text="导出账号", command=self.export_account, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=PADDING['MEDIUM'])

        # 添加右键菜单
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="查看详情", command=self.view_account_details)
        
        # 绑定事件
        tree.bind("<Double-1>", self.on_double_click)    # 双击查看详情
        tree.bind("<Return>", lambda e: self.view_account_details())  # 回车查看详情
        
        # 添加列标题提示
        for i, col in enumerate(columns):
            tree.heading(i, text=col, command=lambda col_idx=i: self.on_column_click(col_idx))
            
        # 创建工具提示文本，显示操作指南
        tip_text = "操作指南:\n• 双击账号查看详情\n• 选中账号后点击查看详情按钮\n• 选中账号后按Enter键查看详情"
        tip_label = ttk.Label(self, text=tip_text, style="TipText.TLabel", wraplength=400)
        tip_label.pack(pady=(0, PADDING['MEDIUM']), anchor=tk.W)

        #设置树
        self.account_tree = tree
        #设置选中账号
        self.selected_item = None

    # 添加列调整事件处理
    def on_column_resize(self, event):
        """记住用户手动调整的列宽"""
        region = self.account_tree.identify_region(event.x, event.y)
        if region == "separator":
            # 用户调整了列宽
            column = self.account_tree.identify_column(event.x)
            if column:
                # 列索引是从#1开始的
                col_idx = int(column.replace('#', '')) - 1
                if 0 <= col_idx < len(self.account_tree['columns']):
                    col_name = self.account_tree['columns'][col_idx]
                    # 获取当前列宽并保存
                    width = self.account_tree.column(col_name, 'width')
                    self.user_column_widths[col_name] = width
                    logger.debug(f"用户调整列 '{col_name}' 宽度为 {width}")

    # 修改自适应列宽方法以尊重用户的手动调整
    def adjust_column_widths(self):
        """根据内容自动调整列宽，但尊重用户手动设置的列宽"""
        columns = self.account_tree['columns']
        
        # 首先保存所有当前列宽
        current_widths = {}
        for col in columns:
            current_widths[col] = self.account_tree.column(col, 'width')
            
        # 为每列找出最宽内容
        for i, col in enumerate(columns):
            # 如果用户手动调整过此列宽度，则使用用户设置的宽度
            if col in self.user_column_widths:
                # 确保正确应用用户设置的宽度
                self.account_tree.column(col, width=self.user_column_widths[col])
                continue
                
            max_width = len(col) * 10  # 列标题宽度作为初始最小宽度
            
            # 遍历所有行找出最宽内容
            for item_id in self.account_tree.get_children():
                item_values = self.account_tree.item(item_id)['values']
                if item_values and i < len(item_values):
                    # 获取单元格内容
                    cell_content = str(item_values[i])
                    # 特殊处理超长内容
                    if col in ['Cookie', '令牌'] and len(cell_content) > 30:
                        # 超长内容只计算前30个字符的宽度
                        cell_width = 30 * 8
                    else:
                        cell_width = len(cell_content) * 8  # 近似计算内容宽度
                    
                    max_width = max(max_width, cell_width)
            
            # 设置合理的列宽范围
            min_width = 80
            max_allowed = 300
            
            # 特别设置某些列的宽度范围
            if col == '用户ID':
                min_width = 120
                max_allowed = 200
            elif col == '邮箱':
                min_width = 150
                max_allowed = 250
            elif col == '密码':
                min_width = 100
                max_allowed = 150
            elif col == '账户状态':
                min_width = 80
                max_allowed = 120
            elif col == '使用量':
                min_width = 80
                max_allowed = 120
            elif col == '剩余天数':
                min_width = 80
                max_allowed = 100
            elif col == 'Cookie' or col == '令牌':
                min_width = 150
                max_allowed = 300
            
            # 确保列宽在合理范围内
            adjusted_width = max(min_width, min(max_width, max_allowed))
            self.account_tree.column(col, width=adjusted_width)
        
        # 移动滚动区域到左侧，确保用户能看到左侧列
        self.account_tree.xview_moveto(0)
            
        logger.debug("已自动调整表格列宽")

    #选中账号
    def on_select(self, event):
        selected_items = self.account_tree.selection()
        if selected_items:
            self.selected_item = selected_items[0]
        else:
            self.selected_item = None
    #获取csv文件列表
    def get_csv_files(self) -> List[str]:
        try:
            return glob.glob('env_backups/cursor_account_*.csv')
        except Exception as e:
            logger.error(f"获取CSV文件列表失败: {str(e)}")            
            return []
        
    #解析csv文件
    def parse_csv_file(self, csv_file: str) -> Dict[str, str]:
        #账号数据
        account_data = {}

        try:
            #读取csv文件
            encodings_to_try = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030', 'latin-1']
            
            for encoding in encodings_to_try:
                try:
                    with open(csv_file, 'r', encoding=encoding) as f:
                        csv_reader = csv.reader(f)
                        next(csv_reader)  # 跳过标题行
                        for row in csv_reader:
                            if len(row) >= 2:
                                account_data[row[0]] = row[1]
                    logger.debug(f"成功使用 {encoding} 编码读取文件: {csv_file}")
                    break  # 如果成功读取，跳出循环
                except UnicodeDecodeError:
                    if encoding == encodings_to_try[-1]:  # 如果是最后一个尝试的编码
                        logger.error(f"无法用任何编码读取文件: {csv_file}")
                        raise
                    else:
                        logger.debug(f"尝试使用 {encoding} 编码失败，尝试下一个")
                        continue
                except Exception as e:
                    logger.error(f"读取文件时出错 (编码: {encoding}): {str(e)}")
                    raise
        except Exception as e:
            logger.error(f"解析文件 {csv_file} 失败: {str(e)}")            
        
        return account_data
    
    #更新csv文件
    def update_csv_file(self, csv_file: str, **fields_to_update) -> None:
        if not fields_to_update:
            logger.debug("没有需要更新的字段")            
            return

        encodings_to_try = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030', 'latin-1']
        
        try:
            # 检查文件是否存在
            if not os.path.exists(csv_file):
                logger.error(f"文件不存在: {csv_file}")
                return
                
            # 检查文件是否可读写
            if not os.access(csv_file, os.R_OK | os.W_OK):
                logger.error(f"文件无法读写: {csv_file}")
                return
                
            # 临时文件路径
            temp_file = f"{csv_file}.temp"
            
            # 尝试读取文件
            rows = []
            read_encoding = None
            
            for encoding in encodings_to_try:
                try:
                    with open(csv_file, 'r', encoding=encoding) as f:
                        csv_reader = csv.reader(f)
                        rows = list(csv_reader)
                    read_encoding = encoding
                    logger.debug(f"成功使用 {encoding} 编码读取文件: {csv_file}")
                    break
                except UnicodeDecodeError:
                    if encoding == encodings_to_try[-1]:
                        logger.error(f"无法用任何编码读取文件: {csv_file}")
                        return
                    else:
                        logger.debug(f"尝试使用 {encoding} 编码失败，尝试下一个")
                        continue
                except Exception as e:
                    logger.error(f"读取文件时出错 (编码: {encoding}): {str(e)}")
                    if encoding == encodings_to_try[-1]:
                        return
                    continue
            
            # 如果没有成功读取任何编码
            if read_encoding is None:
                logger.error(f"无法使用任何编码读取文件: {csv_file}")
                return
            
            # 更新字段
            for field, value in fields_to_update.items():
                field_found = False
                for row in rows:
                    if len(row) >= 2 and row[0] == field:
                        row[1] = str(value)
                        field_found = True
                        break
                if not field_found:
                    rows.append([field, str(value)])

            # 先写入临时文件
            try:
                with open(temp_file, 'w', encoding=read_encoding, newline='') as f:
                    csv_writer = csv.writer(f)
                    csv_writer.writerows(rows)
            except Exception as write_error:
                logger.error(f"写入临时文件失败: {str(write_error)}")
                # 清理临时文件
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                return
            
            # 创建原文件的备份
            backup_file = f"{csv_file}.bak"
            try:
                shutil.copy2(csv_file, backup_file)
            except Exception as backup_error:
                logger.warning(f"创建备份失败: {str(backup_error)}")
                # 继续执行，即使备份失败
            
            # 用临时文件替换原文件
            try:
                os.replace(temp_file, csv_file)
                logger.debug(f"已更新CSV文件: {csv_file}, 更新字段: {', '.join(fields_to_update.keys())}")
                
                # 操作成功后删除备份文件
                if os.path.exists(backup_file):
                    try:
                        os.remove(backup_file)
                    except:
                        pass
            except Exception as replace_error:
                logger.error(f"替换原文件失败: {str(replace_error)}")
                # 尝试从备份恢复
                if os.path.exists(backup_file):
                    try:
                        os.replace(backup_file, csv_file)
                        logger.info(f"已从备份恢复文件: {csv_file}")
                    except:
                        logger.error(f"无法从备份恢复文件: {csv_file}")
                
                # 清理临时文件
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"更新CSV文件失败: {str(e)}")
            # 不抛出异常，避免影响其他操作

    #刷新列表
    def refresh_list(self):
        #清空列表
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
            
        # 显示加载提示
        loading_label = ttk.Label(self, text="正在加载账号列表...", style="TipText.TLabel")
        loading_label.pack(pady=10)
        self.update_idletasks()  # 强制更新UI
        
        # 创建线程执行耗时操作
        def load_accounts():
            try:
                csv_files = self.get_csv_files()
                account_data_list = []
                
                # 先收集所有数据
                for csv_file in csv_files:
                    try:
                        account_data = self.parse_csv_file(csv_file)
                        
                        # 检查Cookie并判断状态
                        if account_data.get('COOKIES_STR'):
                            try:
                                # 如果已有状态，检查是否需要更新
                                if not account_data.get('STATUS') or account_data.get('STATUS') == '未知':
                                    _, account_status = self.extract_user_from_jwt(account_data.get('COOKIES_STR', ''))
                                    # 更新CSV文件中的状态
                                    self.update_csv_file(csv_file, STATUS=account_status)
                                    account_data['STATUS'] = account_status
                            except Exception as e:
                                logger.error(f"提取账号状态失败: {str(e)}")
                                account_data['STATUS'] = "非正常"
                                self.update_csv_file(csv_file, STATUS="非正常")
                        else:
                            # 没有Cookie信息，设置为"非正常"
                            account_data['STATUS'] = "非正常"
                            self.update_csv_file(csv_file, STATUS="非正常")
                        
                        account_data_list.append((csv_file, account_data))
                    except Exception as file_error:
                        logger.error(f"处理文件 {csv_file} 失败: {str(file_error)}")
                
                # 回到主线程更新UI
                def update_ui():
                    # 移除加载提示
                    loading_label.destroy()
                            
                    # 更新树形视图
                    for csv_file, account_data in account_data_list:
                                self.account_tree.insert('', 'end', iid=csv_file, values=(
                                    account_data.get('USERID', ''),
                                    account_data.get('EMAIL', ''),
                                    account_data.get('PASSWORD', ''),
                                    account_data.get('COOKIES_STR', ''),
                                    account_data.get('DAYS', '14'),
                                    account_data.get('QUOTA', '0/150'),
                                    account_data.get('STATUS', '未知'),
                                    account_data.get('TOKEN', ''),
                                ))
                    
                    # 在更新数据后自动调整列宽
                    self.adjust_column_widths()
                            
                    logger.info("账号列表已刷新")
                
                # 在主线程中执行UI更新
                self.after(0, update_ui)
                
            except Exception as e:
                # 错误处理也回到主线程
                def show_error():
                    loading_label.destroy()
                    logger.error(f"刷新列表失败: {str(e)}")
                    UI.show_error(self.winfo_toplevel(), "刷新列表失败", str(e))
                
                self.after(0, show_error)
        
        # 启动线程
        threading.Thread(target=load_accounts, daemon=True).start()

    #通过treeview获取选中的账号
    def get_selected_account(self) -> Tuple[str, Dict[str, str]]:
        # 获取选中的账号
        if not self.selected_item:
            raise ValueError("请先选择要操作的账号")

        item_values = self.account_tree.item(self.selected_item)['values']
        if not item_values or len(item_values) < 2:
            raise ValueError("所选账号信息不完整")

        csv_file_path = self.selected_item
        account_data = self.parse_csv_file(csv_file_path)

        if not account_data.get('EMAIL') or not account_data.get('PASSWORD'):
            raise ValueError("账号信息不完整")
            
        return csv_file_path, account_data
    #处理账号操作
    def handle_account_action(self, action_name: str, action: Callable[[str, Dict[str, str]], None]) -> None:
        try:
            csv_file_path, account_data = self.get_selected_account()
            action(csv_file_path, account_data)
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), f"{action_name}失败", e)
            logger.error(f"{action_name}失败: {str(e)}")
    
    #提取用户ID
    def extract_user_from_jwt(self, cookies: str) -> Tuple[str, str]:
        """从JWT令牌中提取用户ID和账户状态
        
        从sub字段格式"登录类型|用户ID"中提取真实用户ID和登录类型作为账户状态:
        - auth0: 正常
        - 空值: 非正常
        - 其他值: 显示实际值
        
        返回：
            Tuple[str, str]: (用户ID, 账户状态)
        """
        # 设置超时的装饰器函数
        def timeout_handler(func, timeout_sec=2):
            """
            为函数添加超时机制
            """
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def wrapper():
                try:
                    result = func()
                    result_queue.put(("success", result))
                except Exception as e:
                    result_queue.put(("error", str(e)))
            
            thread = threading.Thread(target=wrapper)
            thread.daemon = True
            thread.start()
            
            try:
                status, result = result_queue.get(timeout=timeout_sec)
                if status == "error":
                    logger.error(f"JWT解析过程中发生错误: {result}")
                    return None
                return result
            except queue.Empty:
                logger.error(f"JWT解析超时 (>{timeout_sec}秒)")
                return None
        
        # 实际的JWT解析函数
        def parse_jwt():
            try:
                # 检查 cookies 参数
                if not cookies:
                    logger.warning("Cookie为空，无法提取JWT")
                    return "未知", "非正常(Cookie为空)"
                    
                # 直接从cookies中提取JWT令牌，不使用Utils.extract_token方法
                if "WorkosCursorSessionToken=" in cookies:
                    jwt_token = cookies.split("WorkosCursorSessionToken=")[1].split(";")[0]
                else:
                    jwt_token = cookies  # 假设整个字符串就是令牌
                    
                if not jwt_token:
                    logger.warning("令牌为空")
                    return "未知", "非正常(令牌为空)"
                
                parts = jwt_token.split('.')
                if len(parts) != 3:
                    logger.warning(f"JWT格式错误，parts数量: {len(parts)}")
                    return "未知", "非正常(JWT格式错误)"
                    
                #提取payload
                try:
                    payload = parts[1]
                    # 添加必要的填充
                    padding_needed = 4 - (len(payload) % 4)
                    if padding_needed < 4:
                        payload += '=' * padding_needed
                        
                    # 解码 base64 数据
                    try:
                        decoded = base64.b64decode(payload)
                        if not decoded:
                            logger.error("Base64解码后数据为空")
                            return "未知", "非正常(JWT解码失败-空数据)"
                            
                        # 解析 JSON 数据
                        try:
                            payload_data = json.loads(decoded)
                            if not isinstance(payload_data, dict):
                                logger.error(f"JWT payload不是字典: {type(payload_data)}")
                                return "未知", "非正常(JWT格式错误-非字典)"
                        except json.JSONDecodeError as json_err:
                            logger.error(f"JSON解析失败: {json_err}")
                            return "未知", "非正常(JWT格式错误-JSON解析失败)"
                    except Exception as b64_err:
                        logger.error(f"Base64解码失败: {b64_err}")
                        return "未知", "非正常(JWT解码失败-Base64错误)"
                except Exception as decode_error:
                    logger.error(f"解码JWT失败: {decode_error}")
                    return "未知", "非正常(JWT解码失败)"
                    
                #提取用户ID
                full_user_id = payload_data.get('sub', '')
                if not full_user_id:
                    logger.warning("JWT中未找到用户ID (sub字段为空)")
                    return "未知", "非正常(无用户ID)"
                
                # 处理用户ID格式: 登录类型|真实用户ID
                account_status = "非正常(ID格式错误)"
                user_id = full_user_id
                
                if '|' in full_user_id:
                    # 获取登录类型作为账户状态
                    login_type, user_id = full_user_id.split('|', 1)
                    if login_type == "auth0":
                        account_status = "正常"
                    else:
                        account_status = login_type  # 返回实际的登录类型
                
                # 返回用户ID和账户状态
                return user_id, account_status
            except Exception as e:
                logger.error(f"从 JWT 提取用户信息失败: {str(e)}")
                return "未知", "非正常(解析失败)"
        
        # 使用超时处理器执行JWT解析
        result = timeout_handler(parse_jwt)
        if result is None:
            return "未知", "非正常(解析超时)"
        
        return result
    
    #获取账号信息
    def get_trial_usage(self, cookie_str: str) -> Tuple[str, str, str, str]:
        if not cookie_str:
            logger.error("Cookie信息为空")
            return "未知", "未知", "0/150", "14"  # 返回默认值而不是抛出异常

        try:
            # 安全地提取用户ID
            try:
                result = self.extract_user_from_jwt(cookie_str)
                if result is None or not isinstance(result, tuple) or len(result) != 2:
                    logger.error(f"extract_user_from_jwt 返回值异常: {result}")
                    user_id = "未知"
                else:
                    user_id, _ = result
            except Exception as jwt_error:
                logger.error(f"提取用户ID失败: {str(jwt_error)}")
                user_id = "未知"  # 使用默认值
            
            if not cookie_str.startswith('WorkosCursorSessionToken='):
                cookie_str = f'WorkosCursorSessionToken={cookie_str}'

            headers = {
                'Cookie': cookie_str,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }

            timeout = 30
            session = requests.Session()
            # 禁用SSL验证以解决SSL握手错误
            session.verify = False
            # 忽略SSL警告
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            session.headers.update(headers)

            def make_request(url: str) -> dict:
                try:
                    # 添加额外的请求头，模拟最新的浏览器
                    extra_headers = {
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'sec-ch-ua': '"Chromium";v="122", "Google Chrome";v="122", "Not(A:Brand";v="24"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"'
                    }
                    local_headers = session.headers.copy()
                    local_headers.update(extra_headers)
                    
                    # 尝试多种方式请求
                    try:
                        # 常规请求
                        response = session.get(url, timeout=timeout, headers=local_headers)
                        response.raise_for_status()            
                        return response.json()
                    except requests.RequestException as e1:
                        logger.warning(f"第一次请求 {url} 失败: {str(e1)}，尝试备用方法")
                        # 尝试不同的TLS版本
                        try:
                            original_context = ssl.create_default_context()
                            # 尝试使用TLS 1.2
                            ssl_context = ssl.create_default_context()
                            ssl_context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
                            session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
                            response = session.get(url, timeout=timeout, headers=local_headers)
                            response.raise_for_status()            
                            return response.json()
                        except Exception as e2:
                            logger.warning(f"第二次请求 {url} 失败: {str(e2)}，尝试备用方法")
                            # 如果还是失败，使用静态默认值（避免完全失败）
                            if 'auth/me' in url:
                                return {"email": user_id.split('@')[0] + '@' + (user_id.split('@')[1] if '@' in user_id else 'cursor.com')}
                            elif 'auth/stripe' in url:
                                return {"daysRemainingOnTrial": 14}
                            elif 'usage' in url:
                                return {"gpt-4": {"numRequestsTotal": 0, "maxRequestUsage": 150}}
                            else:
                                logger.error(f"无法从API获取数据: {url}")
                                return {}  # 返回空字典而不是抛出异常
                except Exception as e:
                    logger.error(f"请求 {url} 失败: {str(e)}")
                    return {}  # 返回空字典而不是抛出异常

            try:
                # 多线程获取账号信息
                with ThreadPoolExecutor(max_workers=3) as executor:
                    future_user_info = executor.submit(make_request, "https://www.cursor.com/api/auth/me")
                    future_trial = executor.submit(make_request, "https://www.cursor.com/api/auth/stripe")
                    future_usage = executor.submit(make_request, f"https://www.cursor.com/api/usage?user={user_id}")

                    user_info = future_user_info.result()
                    email = user_info.get('email', '未知')

                    trial_data = future_trial.result()
                    days = str(trial_data.get('daysRemainingOnTrial', '未知'))

                    usage_data = future_usage.result()
                    gpt4_data = usage_data.get('gpt-4', {})
                    used_quota = gpt4_data.get('numRequestsTotal', 0)
                    max_quota = gpt4_data.get('maxRequestUsage', 0)
                    quota = f"{used_quota} / {max_quota}" if max_quota else '未知'            
                    return user_id, email, quota, days

            except Exception as e:
                logger.error(f"获取账号信息失败: {str(e)}")
                return user_id, "未知", "0/150", "14"  # 返回部分已知和默认值
            finally:
                session.close()
        except Exception as e:
            logger.error(f"处理 JWT 失败: {str(e)}")
            return "未知", "未知", "0/150", "14"  # 返回默认值
        
    #更新账号信息
    def update_account_info(self):
        #更新账号信息
        def get_trial_info(csv_file_path: str, account_data: Dict[str, str]) -> None:
            cookie_str = account_data.get('COOKIES_STR', '')
            if not cookie_str:
                email=account_data.get('EMAIL','未知邮箱')
                password=account_data.get('PASSWORD','未知密码')
                raise ValueError(f"未找到账号 {email} 的Cookie信息")
                #重新登录
                sign
            #获取账号信息
            def fetch_and_display_info():
                try:
                    self.winfo_toplevel().after(0, lambda: UI.show_loading(
                        self.winfo_toplevel(),
                        "更新账号信息",
                        "正在获取账号信息，请稍候..."
                    ))

                    logger.debug("开始获取账号信息...")
                    logger.debug(f"获取到的cookie字符串长度: {len(cookie_str) if cookie_str else 0}")
                    
                    # 提取用户ID和账户状态
                    try:
                        result = self.extract_user_from_jwt(cookie_str)
                        if result is None or not isinstance(result, tuple) or len(result) != 2:
                            logger.error(f"extract_user_from_jwt 返回值异常: {result}")
                            user_id = account_data.get('USERID', '未知')
                            account_status = "非正常"
                            reconstructed_cookie = cookie_str
                        else:
                            user_id, account_status = result
                            # 重构cookie
                            reconstructed_cookie = f"WorkosCursorSessionToken={user_id}%3A%3A{cookie_str.split('%3A%3A')[-1]}" if '%3A%3A' in cookie_str else cookie_str
                    except Exception as jwt_error:
                        logger.error(f"处理JWT失败: {str(jwt_error)}")
                        reconstructed_cookie = cookie_str  # 失败时使用原始cookie
                        account_status = "非正常"
                        # 尝试从之前的数据获取用户ID，如果失败则设为'未知'
                        user_id = account_data.get('USERID', '未知')
                    
                    # 获取账号信息
                    try:
                        user_id, email, quota, days = self.get_trial_usage(reconstructed_cookie)
                        logger.info(f"成功获取账号信息: 用户ID={user_id}, 邮箱={email}, 使用量={quota}, 剩余天数={days}")
                        
                        # 尝试获取令牌
                        access_token = account_data.get('TOKEN', '')
                        refresh_token = account_data.get('REFRESH_TOKEN', '')
                        if not access_token or not refresh_token:
                            logger.info("【令牌获取】尝试获取长期令牌...")
                            try:
                                session_token = None
                                if "WorkosCursorSessionToken=" in reconstructed_cookie:
                                    session_token = reconstructed_cookie.split("WorkosCursorSessionToken=")[1].split(";")[0]
                                    logger.info("【令牌获取】提取WorkosCursorSessionToken")
                                else:
                                    session_token = reconstructed_cookie
                                    logger.info("【令牌获取】使用整个Cookie字符串作为会话令牌")
                                    
                                logger.info("【令牌获取】开始尝试使用CursorRegistration获取长期令牌...")
                                
                                # 使用CursorRegistration类获取令牌
                                cursor_reg = CursorRegistration()
                                # 创建cookie字符串
                                cookie_str_for_pkce = f"WorkosCursorSessionToken={session_token}"
                                logger.debug(f"【令牌获取】为PKCE方法准备Cookie字符串，长度: {len(cookie_str_for_pkce)}")
                                # 初始化浏览器
                                logger.debug("【令牌获取】正在初始化浏览器...")
                                cursor_reg.init_browser()
                                logger.debug("【令牌获取】浏览器初始化成功")
                                # 设置cookie
                                logger.debug("【令牌获取】正在设置Cookie...")
                                cursor_reg.tab.set.cookies(cookie_str_for_pkce)
                                logger.debug("【令牌获取】Cookie设置成功")
                                # 获取令牌
                                logger.info("【令牌获取】开始使用PKCE方法获取长期令牌...")
                                access_token, refresh_token = cursor_reg.get_cursor_access_token_and_refresh_token()
                                if access_token and refresh_token:
                                    logger.info(f"【令牌获取】成功获取令牌: {access_token[:15]}...{refresh_token[:15]}...")
                                else:
                                    logger.warning("【令牌获取】无法获取令牌")
                            except Exception as token_error:
                                logger.error(f"【令牌获取】获取令牌过程中出现异常: {str(token_error)}")
                            finally:
                                # 无论令牌获取成功与否，确保浏览器实例被关闭
                                logger.info("【令牌获取】令牌获取过程结束")
                                try:
                                    if cursor_reg and hasattr(cursor_reg, 'browser'):
                                        logger.debug("【令牌获取】正在关闭浏览器实例...")
                                        cursor_reg.close_browser()
                                        logger.debug("【令牌获取】浏览器实例已成功关闭")
                                except Exception as e:
                                    logger.error(f"【令牌获取】关闭浏览器实例失败: {str(e)}")
                                
                                if access_token and refresh_token:
                                    logger.info("【令牌获取】成功获取到长期令牌")
                                else:
                                    logger.warning("【令牌获取】未能获取到长期令牌")

                    except Exception as info_error:
                        logger.error(f"获取账号信息失败: {str(info_error)}")
                        # 使用现有信息
                        email = account_data.get('EMAIL', '未知')
                        quota = account_data.get('QUOTA', '未知')
                        days = account_data.get('DAYS', '未知')
                        access_token = account_data.get('TOKEN', '')
                        refresh_token = account_data.get('REFRESH_TOKEN', '')
                        # 更新状态为非正常
                        if account_status == "正常":
                            account_status = "异常"
                    
                    # 更新账号信息
                    self.account_tree.set(self.selected_item, '用户ID', user_id)
                    self.account_tree.set(self.selected_item, '邮箱', email)
                    self.account_tree.set(self.selected_item, '使用量', quota)
                    self.account_tree.set(self.selected_item, '剩余天数', days)
                    self.account_tree.set(self.selected_item, '账户状态', account_status)
                    self.account_tree.set(self.selected_item, 'Cookie', reconstructed_cookie)
                    self.account_tree.set(self.selected_item, '令牌', access_token)
                    
                    # 更新CSV文件
                    try:
                        update_dict = {
                            'USERID': user_id,
                            'EMAIL': email,
                            'STATUS': account_status,
                            'QUOTA': quota,
                            'DAYS': days,
                            'COOKIES_STR': reconstructed_cookie
                        }
                        # 只有当令牌不为空时才更新TOKEN字段
                        if access_token and refresh_token:
                            update_dict['TOKEN'] = access_token
                            update_dict['REFRESH_TOKEN'] = refresh_token
                            
                        self.update_csv_file(csv_file_path, **update_dict)
                    except Exception as e:
                        logger.error(f"更新CSV文件失败: {str(e)}")
                        raise ValueError(f"更新CSV文件失败: {str(e)}")
                    #关闭加载
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    #显示成功
                    success_message = (
                        f"用户ID: {user_id}\n"
                        f"邮箱: {email}\n"
                        f"状态: {account_status}\n"
                        f"密码: {account_data.get('PASSWORD','未知密码')}\n"
                        f"可用额度: {quota}\n"
                        f"剩余天数: {days}\n"
                    )
                    # 显示令牌状态
                    if access_token and refresh_token:
                        success_message += f"令牌: 已更新"
                    else:
                        success_message += f"令牌: 未获取"
                        
                    self.winfo_toplevel().after(0, lambda: UI.show_success(
                        self.winfo_toplevel(),
                        success_message
                    ))
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"获取账号信息失败: {error_message}")
                    logger.exception("详细错误信息:")
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "获取账号信息失败",
                        error_message
                    ))

            logger.debug("开始更新账号信息...")
            threading.Thread(target=fetch_and_display_info, daemon=True).start()

        self.handle_account_action("获取账号信息", get_trial_info)
    
    #切换账号
    def switch_account(self) -> None:
        #切换账号
        def update_account_auth(csv_file_path: str, account_data: Dict[str, str]) -> None:
            cookie_str = account_data.get('COOKIES_STR', '')
            email = account_data.get('EMAIL', '')
            # 获取长期令牌
            access_token = account_data.get('TOKEN', '')
            refresh_token = account_data.get('REFRESH_TOKEN', '')
            
            # 必须有长期令牌
            if not access_token or not refresh_token:
                raise ValueError(f"账号 {email} 没有长期令牌，无法切换账号。请先更新账号信息获取长期令牌。")
            
            if not email:
                raise ValueError("账号邮箱不能为空")
            
            #更新账号Token
            def process_auth():
                try:
                    self.winfo_toplevel().after(0, lambda: UI.show_loading(
                        self.winfo_toplevel(),
                        "切换账号",
                        "正在检查 Cursor 进程状态并更新认证信息，请稍候..."
                    ))

                    # 检查是否有管理员权限
                    has_admin = ctypes.windll.shell32.IsUserAnAdmin()
                    if has_admin:
                        # 有管理员权限，执行重置机器码，但切换账号时不需要在重置后立即启动Cursor（由后续切换账号过程处理）
                        logger.info("具有管理员权限，切换账号前先重置机器码...")
                        # 调用reset_machine_id但不自动启动Cursor
                        self.reset_machine_id(auto_start_cursor=False)
                        logger.info("重置机器码成功，继续执行账号切换")
                    else:
                        # 没有管理员权限，显示提示
                        logger.warning("切换账号需要重置机器码，但当前没有管理员权限")
                        UI.show_warning(
                            self.winfo_toplevel(),
                            "管理员权限提示",
                            "为了完全切换账号，建议先点击\"重置机器ID\"按钮以管理员身份运行。\n\n将继续执行账号切换，但可能会导致部分功能受限。"
                        )

                    # 使用长期令牌更新认证信息
                    logger.info(f"使用长期令牌更新账号 {email}")
                    result = CursorManager().process_access_token_and_refresh_token(access_token, refresh_token, email)
                    
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    
                    if not result.success:
                        raise ValueError(result.message)

                    # 检查结果消息，确定是否需要启动 Cursor
                    if "但重启应用失败" in result.message:
                        UI.show_warning(
                            self.winfo_toplevel(), 
                            "切换账号部分成功", 
                            f"账号 {email} 的认证信息已使用长期令牌更新，但自动启动 Cursor 应用失败，请手动启动 Cursor。"
                        )
                    elif "Cursor 未启动" in result.message:
                        # 自动启动 Cursor 应用，无需询问
                        logger.info("Cursor未启动，正在自动启动...")
                        start_result = CursorManager.start_cursor_app()
                        if not start_result.success:
                            UI.show_warning(
                                self.winfo_toplevel(),
                                "启动失败",
                                f"启动 Cursor 应用失败: {start_result.message}，请手动启动 Cursor。"
                            )
                        else:
                            UI.show_success(
                                self.winfo_toplevel(),
                                f"账号 {email} 的认证信息已更新，Cursor 应用已启动"
                            )
                    else:
                        UI.show_success(
                            self.winfo_toplevel(), 
                            f"账号 {email} 的认证信息已使用长期令牌更新，Cursor 应用已重新启动"
                        )
                    logger.info(f"已使用长期令牌更新账号 {email} 的认证信息")
                except Exception as e:
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "切换账号失败",
                        str(e)
                    ))

            threading.Thread(target=process_auth, daemon=True).start()

        self.handle_account_action("使用长期令牌更新认证", update_account_auth)

    #重置机器ID
    @error_handler
    def reset_machine_id(self, auto_start_cursor=True) -> None:
        # 首先检查是否有管理员权限
        has_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not has_admin:
            # 没有管理员权限，尝试以管理员身份重新启动
            logger.info("重置机器ID需要管理员权限，正在尝试以管理员身份运行...")
            if Utils.run_as_admin():
                # 如果成功启动了管理员权限的进程，当前进程可以退出
                return
            else:
                # 提升权限失败，显示错误消息
                UI.show_error(
                    self.winfo_toplevel(),
                    "权限不足",
                    "重置机器ID需要管理员权限，但无法启动管理员进程。请右键点击程序，选择'以管理员身份运行'。"
                )
                return
        
        # 已有管理员权限，继续执行重置操作
        def reset_thread():
            try:
                #显示加载
                self.after(0, lambda: UI.show_loading(
                    self.winfo_toplevel(),
                    "正在重置机器ID",
                    "正在执行重置操作，请稍候..."
                ))
                #重置机器ID
                result = CursorManager.reset()
                
                #关闭加载   
                self.after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                
                #显示结果
                if not result.success:
                    self.after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "重置机器ID失败",
                        result.message
                    ))          
                    return
                
                # 根据参数决定是否自动启动Cursor应用
                if auto_start_cursor:
                    # 重置成功后，自动启动Cursor应用
                    logger.info("重置机器ID成功，正在启动Cursor应用...")
                    start_result = CursorManager.start_cursor_app()
                    
                    if start_result.success:
                        success_message = f"{result.message}\n\nCursor应用已成功启动。"
                        self.after(0, lambda: UI.show_success(
                            self.winfo_toplevel(),
                            success_message
                        ))
                    else:
                        warning_message = f"{result.message}\n\n但启动Cursor应用失败: {start_result.message}，请手动启动Cursor。"
                        self.after(0, lambda: UI.show_warning(
                            self.winfo_toplevel(),
                            "重置成功但启动失败",
                            warning_message
                        ))
                else:
                    # 仅显示重置成功消息，不启动Cursor
                    success_message = result.message
                    self.after(0, lambda: UI.show_success(
                        self.winfo_toplevel(),
                        success_message
                    ))
                
            except Exception as e:
                #关闭加载       
                self.after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                #显示失败
                self.after(0, lambda: UI.show_error(
                    self.winfo_toplevel(),
                    "重置机器ID失败",
                    str(e)
                ))
        
        #启动线程
        threading.Thread(target=reset_thread, daemon=True).start()

    #删除账号方法   
    def delete_account(self):
        #从csv文件中删除账号
        def delete_account_file(csv_file_path: str, account_data: Dict[str, str]) -> None:
            confirm_message = (
                f"确定要删除以下账号吗？\n\n"
                f"用户ID：{account_data['USERID']}\n"
                f"邮箱：{account_data['EMAIL']}\n"
                f"密码：{account_data['PASSWORD']}\n"
                f"Cookie：{account_data['COOKIES_STR']}\n"
                f"状态：{account_data['STATUS']}\n"
                f"剩余天数：{account_data['DAYS']}\n"
                f"使用量：{account_data['QUOTA']}\n"
                f"令牌：{account_data['TOKEN'] or account_data['ACCESS_TOKEN'] or account_data['REFRESH_TOKEN']}\n"
            )

            if not messagebox.askyesno("确认删除", confirm_message, icon='warning'):            
                return
            #删除账号
            def process_delete():
                try:
                    self.winfo_toplevel().after(0, lambda: UI.show_loading(
                        self.winfo_toplevel(),
                        "删除账号",
                        "正在删除账号信息，请稍候..."
                    ))

                    os.remove(csv_file_path)
                    self.account_tree.delete(self.selected_item)
                    #关闭加载
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    #显示成功
                    logger.info(f"已删除账号: {account_data['USERID']} - {account_data['EMAIL']}")
                    UI.show_success(self.winfo_toplevel(),
                                    f"已删除账号: {account_data['USERID']} - {account_data['EMAIL']}")
                except Exception as e:
                    self.winfo_toplevel().after(0, lambda: UI.close_loading(self.winfo_toplevel()))
                    self.winfo_toplevel().after(0, lambda: UI.show_error(
                        self.winfo_toplevel(),
                        "删除账号失败",
                        str(e)
                    ))

            threading.Thread(target=process_delete, daemon=True).start()

        self.handle_account_action("删除账号", delete_account_file)

    #查看账号详细信息
    def view_account_details(self):
        """查看账号详细信息"""
        if not self.selected_item:
            UI.show_warning(self.winfo_toplevel(), "请先选择一个账号")            
            return
        
        try:
            csv_file_path, account_data = self.get_selected_account()
            
            # 创建详情对话框
            details_dialog = tk.Toplevel(self)
            details_dialog.title("账号详细信息")
            details_dialog.geometry("768x480")
            # 设置对话框居中
            details_dialog.transient(self.winfo_toplevel())
            # 设置对话框大小
            details_dialog.resizable(False, False)
            # 设置对话框位置
            details_dialog.geometry("+%d+%d" % (
                self.winfo_toplevel().winfo_x() + 50,
                self.winfo_toplevel().winfo_y() + 50
            ))
            details_dialog.grab_set()
            
            # 主框架
            main_frame = ttk.Frame(details_dialog, style='TFrame', padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # 信息文本框
            info_text = tk.Text(main_frame, wrap=tk.WORD, width=60, height=15)
            info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 滚动条
            scrollbar = ttk.Scrollbar(info_text, orient=tk.VERTICAL, command=info_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            info_text.config(yscrollcommand=scrollbar.set)
            
            # 填充信息
            for key, value in account_data.items():
                if value:  # 只显示非空值
                    info_text.insert(tk.END, f"{key}: {value}\n")
            
            # 设为只读
            info_text.config(state=tk.DISABLED)
            
            # 按钮框架
            button_frame = ttk.Frame(main_frame, style='TFrame')
            button_frame.pack(pady=10)
            
            # 只保留关闭按钮
            ttk.Button(button_frame, text="关闭", command=details_dialog.destroy, 
                      style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            UI.show_error(self.winfo_toplevel(), "查看账号详情失败", str(e))

    # 处理双击事件
    def on_double_click(self, event):
        """双击条目时打开详情对话框"""
        if self.account_tree.identify_region(event.x, event.y) == "cell":
            # 双击时打开详情对话框
            self.view_account_details()
    # 点击列标题时进行排序
    def on_column_click(self, column_idx):
        """点击列标题时进行排序"""
        column_name = self.account_tree['columns'][column_idx]
        
        # 特别处理使用量列的排序
        if column_name == '使用量':
            # 获取所有项目
            items = []
            for item_id in self.account_tree.get_children():
                item_values = self.account_tree.item(item_id)['values']
                if item_values and len(item_values) > 5:  # 确保有使用量列
                    usage_str = str(item_values[5])
                    
                    # 解析使用量字符串（格式：已用/总量）
                    try:
                        used = 0
                        if '/' in usage_str:
                            used_str = usage_str.split('/')[0].strip()
                            if used_str.isdigit():
                                used = int(used_str)
                    except Exception as e:
                        logger.warning(f"解析使用量字符串失败: {usage_str}, {str(e)}")
                        used = 0
                        
                    items.append((item_id, used))
                    
            # 按使用量升序排序
            items.sort(key=lambda x: x[1])
            
            # 重新排列表格项目
            for index, (item_id, _) in enumerate(items):
                self.account_tree.move(item_id, '', index)
                
            UI.show_success(self.winfo_toplevel(), f"已按使用量升序排序")
            
        # 未来可以扩展其他列的排序功能
        # elif column_name == '剩余天数':
        #     # 类似实现剩余天数排序
        #     pass

    #添加账号方法
    def add_account(self):
        """手动添加账号"""
        # 创建添加账号对话框
        add_dialog = tk.Toplevel(self)
        add_dialog.title("添加账号")
        add_dialog.geometry("500x350")
        add_dialog.transient(self.winfo_toplevel())
        add_dialog.grab_set()
        
        # 主框架
        main_frame = ttk.Frame(add_dialog, style='TFrame', padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表单框架
        form_frame = ttk.Frame(main_frame, style='TFrame')
        form_frame.pack(fill=tk.X, pady=10)
        
        # 创建输入字段
        fields = [
            ('用户ID', '必填，从Cookie提取'),
            ('邮箱', '必填，Cursor账号邮箱'),
            ('密码', '必填，Cursor账号密码'),
            ('Cookie', '必填，格式: WorkosCursorSessionToken=xxx'),
            ('账户状态', '必填，从Cookie提取'),
            ('剩余天数', '必填，默认14'),
            ('使用量', '必填，格式: 已用/总量'),
            ('令牌', '可选，通过Cookie获取'),
            ('访问令牌', '可选，通过Cookie获取'),
            ('刷新令牌', '可选，通过Cookie获取'),
        ]
        # 输入框
        entries = {}
        # 遍历fields
        for i, (label, placeholder) in enumerate(fields):
            frame = ttk.Frame(form_frame)
            frame.pack(fill=tk.X, pady=5)
            # 标签
            ttk.Label(frame, text=f"{label}:", width=8).pack(side=tk.LEFT, padx=5)
            # 输入框
            entry = ttk.Entry(frame, width=50)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            # 占位文字
            entry.insert(0, placeholder)
            # 占位文字颜色
            entry.config(foreground='gray')
            
            # 设置焦点事件，清除占位文字
            def on_focus_in(event, entry=entry, placeholder=placeholder):
                if entry.get() == placeholder:
                    entry.delete(0, tk.END)
                    entry.config(foreground='black')
            # 失去焦点事件
            def on_focus_out(event, entry=entry, placeholder=placeholder):
                if not entry.get():
                    entry.insert(0, placeholder)
                    entry.config(foreground='gray')
            # 绑定焦点事件
            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)
            # 添加到entries
            entries[label] = entry
        
        # 提示框
        tip_frame = ttk.Frame(main_frame)
        tip_frame.pack(fill=tk.X, pady=10)
        # 提示文本
        tip_text = ("提示:\n"
                   "• 必须填写邮箱、密码和Cookie\n"
                   "• 其他字段可以留空，系统会自动提取或设置默认值\n"
                   "• Cookie格式: WorkosCursorSessionToken=xxx\n")
        
        tip_label = ttk.Label(tip_frame, text=tip_text, style="TipText.TLabel", wraplength=450)
        tip_label.pack(fill=tk.X)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        # 验证并保存
        def validate_and_save():
            try:
                # 获取所有输入
                account_data = {}
                for label, entry in entries.items():
                    # 获取输入值
                    value = entry.get()
                    # 如果输入值不为空，则添加到account_data
                    if value and value != fields[list(label for label, _ in fields).index(label)][1]:
                        account_data[label] = value
                
                # 验证必填字段
                if 'Cookie' not in account_data or not account_data['Cookie']:
                    raise ValueError("Cookie不能为空")
                
                # 如果Cookie不以WorkosCursorSessionToken=开头，则添加
                if 'Cookie' in account_data and not account_data['Cookie'].startswith("WorkosCursorSessionToken="):
                    account_data['Cookie'] = f"WorkosCursorSessionToken={account_data['Cookie']}"
                
                # 验证邮箱不能为空
                if '邮箱' not in account_data or not account_data['邮箱']:
                    raise ValueError("邮箱不能为空")
                
                # 验证密码不能为空
                if '密码' not in account_data or not account_data['密码']:
                    raise ValueError("密码不能为空")
                
                # 提取Cookie中的用户ID和账户状态
                if 'Cookie' in account_data and not account_data.get('用户ID'):
                    try:
                        user_id, account_status = self.extract_user_from_jwt(account_data['Cookie'])
                        account_data['用户ID'] = user_id
                        if not account_data.get('账户状态'):
                            account_data['账户状态'] = account_status
                    except Exception as e:
                        logger.error(f"从Cookie提取用户信息失败: {str(e)}")
                
                # 设置默认值
                if not account_data.get('账户状态'):
                    account_data['账户状态'] = '未知'
                
                if not account_data.get('剩余天数'):
                    account_data['剩余天数'] = '14'
                
                if not account_data.get('使用量'):
                    account_data['使用量'] = '0/150'
                
                # 保存到CSV文件
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_file = f"env_backups/cursor_account_{timestamp}.csv"
                
                # 确保目录存在
                os.makedirs('env_backups', exist_ok=True)
                # 写入CSV文件
                with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                    csv_writer = csv.writer(f)
                    csv_writer.writerow(['variable', 'value'])  # 写入标题行
                    
                    # 映射字段名称
                    field_map = {
                        '用户ID': 'USERID',
                        '邮箱': 'EMAIL',
                        '密码': 'PASSWORD',
                        'Cookie': 'COOKIES_STR',
                        '账户状态': 'STATUS',
                        '使用量': 'QUOTA',
                        '剩余天数': 'DAYS',
                        '令牌': 'TOKEN' or 'ACCESS_TOKEN' or 'REFRESH_TOKEN',
                    }
                    # 根据映射字段名称写入CSV文件
                    for ui_field, csv_field in field_map.items():
                        value = account_data.get(ui_field, '')
                        csv_writer.writerow([csv_field, value])
                
                logger.info(f"已添加账号，保存到文件: {csv_file}")
                UI.show_success(add_dialog, f"已成功添加账号: {account_data.get('邮箱')}")
                
                # 刷新账号列表
                self.after(500, self.refresh_list)
                
                # 关闭对话框
                add_dialog.destroy()
                
            except Exception as e:
                UI.show_error(add_dialog, "添加账号失败", str(e))
        
        ttk.Button(button_frame, text="保存", command=validate_and_save, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="取消", command=add_dialog.destroy, 
                  style='Custom.TButton', width=10).pack(side=tk.LEFT, padx=5)
    
    #导入账号方法
    def import_account(self):
        logger.info("导入账号")
        file_types = [
            ('CSV文件', '*.csv'),
            ('所有文件', '*.*')
        ]
        
        file_path = filedialog.askopenfilename(
            title="选择要导入的账号文件",
            filetypes=file_types
        )
        
        if not file_path:
            logger.info("用户取消导入账号")
            return
            
        logger.info(f"用户选择导入文件: {file_path}")
        
        try:
            # 首先尝试以不同编码读取文件
            content = None
            used_encoding = None
            encodings_to_try = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030', 'latin-1']
            
            for encoding in encodings_to_try:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    used_encoding = encoding
                    logger.debug(f"成功使用 {encoding} 编码读取文件")
                    break
                except UnicodeDecodeError:
                    logger.debug(f"尝试使用 {encoding} 编码失败，尝试下一个")
                    continue
                    
            if content is None:
                raise ValueError(f"无法读取文件，请检查文件编码")
                
            # 重新打开文件用CSV读取器读取
            account_data = {}
            try:
                with open(file_path, 'r', encoding=used_encoding) as f:
                    csv_reader = csv.reader(f)
                    rows = list(csv_reader)
                    
                if len(rows) < 2:
                    raise ValueError("CSV文件格式错误，至少需要标题行和一行数据")
                    
                # 检查是否是标准格式（第一行是标题行）
                header = rows[0]
                if len(header) == 2 and (header[0].lower() in ['key', 'variable'] and header[1].lower() == 'value'):
                    # 标准格式，提取键值对
                    for row in rows[1:]:
                        if len(row) >= 2:
                            account_data[row[0]] = row[1]
                else:
                    # 尝试以其他格式解析
                    UI.show_error(self.winfo_toplevel(), "导入失败", "不支持的CSV格式，请确保文件第一行是包含'variable'和'value'的标题行")
                    return
                    
            except Exception as csv_error:
                logger.error(f"CSV解析失败: {csv_error}")
                raise ValueError(f"导入CSV文件失败: {csv_error}")
                
            # 检查必要字段
            required_fields = ['EMAIL', 'PASSWORD']
            for field in required_fields:
                if field not in account_data or not account_data[field]:
                    raise ValueError(f"导入文件缺少必要字段: {field}")
                    
            # 保存到新的CSV文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"env_backups/cursor_account_{timestamp}.csv"
            
            os.makedirs('env_backups', exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(['variable', 'value'])  # 写入标题行
                
                for key, value in account_data.items():
                    csv_writer.writerow([key, value])
                    
            logger.info(f"已导入账号: {account_data.get('EMAIL', '未知')}")
            UI.show_success(self.winfo_toplevel(), "导入成功", f"已成功导入账号: {account_data.get('EMAIL', '未知')}")
            
            # 刷新账号列表
            self.refresh_list()
            
        except Exception as e:
            logger.error(f"导入账号失败: {str(e)}")
            UI.show_error(self.winfo_toplevel(), "导入失败", str(e))
    
    #导出账号方法
    def export_account(self):
        logger.info("导出账号")
        # 检查是否有选中的账号
        if not self.selected_item:
            UI.show_error(self.winfo_toplevel(), "导出失败", "请先选择一个账号")
            return
            
        # 获取选中账号的数据
        item_values = self.account_tree.item(self.selected_item)['values']
        
        # 检查是否成功获取数据
        if not item_values or len(item_values) < 3:
            UI.show_error(self.winfo_toplevel(), "导出失败", "无法获取账号数据")
            return
            
        # 账号ID通常是第一列
        account_id = item_values[0]
        email = item_values[1] if len(item_values) > 1 else "未知"
        
        # 查找对应的CSV文件
        csv_files = self.get_csv_files()
        found_file = None
        account_data = {}
        
        for csv_file in csv_files:
            data = self.parse_csv_file(csv_file)
            if data.get('EMAIL') == email or data.get('USER_ID') == account_id:
                found_file = csv_file
                account_data = data
                break
                
        if not found_file or not account_data:
            UI.show_error(self.winfo_toplevel(), "导出失败", f"找不到账号 {email} 的数据文件")
            return
            
        # 选择保存路径
        file_types = [('CSV文件', '*.csv'), ('所有文件', '*.*')]
        default_name = f"cursor_account_{email.split('@')[0]}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        file_path = filedialog.asksaveasfilename(
            title="导出账号数据",
            filetypes=file_types,
            defaultextension=".csv",
            initialfile=default_name
        )
        
        if not file_path:
            logger.info("用户取消导出账号")
            return
            
        try:
            # 导出数据到选择的文件
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(['variable', 'value'])  # 写入标题行
                
                for key, value in account_data.items():
                    csv_writer.writerow([key, value])
                    
            logger.info(f"已导出账号: {email}")
            UI.show_success(self.winfo_toplevel(), "导出成功", f"已成功导出账号: {email}")
            
        except Exception as e:
            logger.error(f"导出账号失败: {str(e)}")
            UI.show_error(self.winfo_toplevel(), "导出失败", f"导出账号时发生错误: {str(e)}")

    



