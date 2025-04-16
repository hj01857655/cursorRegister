"""
打包脚本 - 生成带版本号的EXE文件
"""

import os
import sys
import subprocess
import shutil
from version import __version__

# 配置信息
APP_NAME = "CursorHelper"
MAIN_SCRIPT = "main.py"
ICON_FILE = None  # 如果有图标文件，请指定路径，例如 "assets/icon.ico"

# 清理旧的构建文件
def clean_old_build():
    """清理旧的构建文件"""
    print("清理旧的构建文件...")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    for file in os.listdir("."):
        if file.endswith(".spec"):
            os.remove(file)
    print("清理完成")

# 检查依赖
def check_dependencies():
    """检查必要的依赖是否已安装"""
    try:
        import PyInstaller
        print("PyInstaller 已安装")
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    try:
        import win32api
        print("pywin32 已安装")
    except ImportError:
        print("正在安装 pywin32...")
        subprocess.call([sys.executable, "-m", "pip", "install", "pywin32"])

# 打包应用
def build_app():
    """使用PyInstaller打包应用"""
    print(f"开始打包 {APP_NAME} v{__version__}...")
    
    # 基本命令参数
    cmd = [
        "pyinstaller",
        f"--name={APP_NAME}-v{__version__}",
        "--onefile",                        # 打包成单个可执行文件
        "--windowed",                       # 使用GUI模式，没有控制台窗口
        "--clean",                          # 清理临时文件
        "--version-file=version_info.txt",  # 使用版本信息文件
        "--add-data=.env.example;.",        # 添加示例配置文件
        "--add-data=turnstilePatch;turnstilePatch",  # 添加turnstilePatch目录
        "--add-data=assets;assets",         # 添加assets目录
        "--add-data=LICENSE;.",             # 添加LICENSE文件
        "--add-data=README.md;.",           # 添加README文件
        "--add-data=README_EN.md;.",        # 添加英文README文件
    ]
    
    # 添加图标参数（如果有）
    if ICON_FILE and os.path.exists(ICON_FILE):
        cmd.append(f"--icon={ICON_FILE}")
    
    # 添加主脚本
    cmd.append(MAIN_SCRIPT)
    
    # 执行打包命令
    print("执行命令: " + " ".join(cmd))
    result = subprocess.call(cmd)
    
    if result == 0:
        print(f"打包完成! 可执行文件位于: dist/{APP_NAME}-v{__version__}/{APP_NAME}-v{__version__}.exe")
    else:
        print("打包过程中出现错误!")

if __name__ == "__main__":
    print("=" * 50)
    print(f"开始构建 {APP_NAME} v{__version__}")
    print("=" * 50)
    
    check_dependencies()
    clean_old_build()
    build_app()
    
    print("=" * 50)
    print("构建过程完成")
    print("=" * 50)
