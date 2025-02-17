import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

def clean_build_dirs():
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已清理 {dir_name} 目录")

def check_requirements():
    required_packages = ['pyinstaller']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"正在安装 {package}...")
            subprocess.run(['pip', 'install', package], check=True, encoding='utf-8')

def build_executable():
    print("开始构建可执行文件...")
    
    clean_build_dirs()
    
    check_requirements()
    
    build_command = ['pyinstaller', 'cursorRegister.spec', '--clean']
    try:
        result = subprocess.run(build_command, capture_output=True, text=True, encoding='utf-8')
    except UnicodeDecodeError:
        result = subprocess.run(build_command, capture_output=True, text=True, encoding='gbk')
    
    if result.returncode != 0:
        print("构建失败！")
        print("错误信息：")
        print(result.stderr)
        return False
    
    exe_path = Path('dist/cursorRegister.exe')
    if not exe_path.exists():
        print("构建失败：未找到输出文件！")
        return False
    
    file_size = exe_path.stat().st_size / (1024 * 1024)
    print(f"\n构建成功！")
    print(f"输出文件：{exe_path.absolute()}")
    print(f"文件大小：{file_size:.2f} MB")
    
    if os.path.exists('turnstilePatch'):
        shutil.copytree('turnstilePatch', 'dist/turnstilePatch', dirs_exist_ok=True)
        print("已复制 turnstilePatch 目录")
    
    if os.path.exists('.env.example'):
        shutil.copy('.env.example', 'dist/.env.example')
        print("已复制 .env.example 文件")
    
    return True

def create_zip():
    if not os.path.exists('dist'):
        print("dist 目录不存在，无法创建压缩包")
        return
    
    zip_name = f"cursorRegister-Windows-{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    shutil.make_archive(zip_name.replace('.zip', ''), 'zip', 'dist')
    print(f"\n已创建压缩包：{zip_name}")

def main():
    print("=== Cursor Register 打包工具 ===")
    if build_executable():
        create_zip()
    print("\n打包过程完成！")

if __name__ == '__main__':
    main() 