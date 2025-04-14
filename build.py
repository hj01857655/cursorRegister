import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from clean import clean_build_dirs


def check_requirements():
    required_packages = ['pyinstaller']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"正在安装 {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True, encoding='utf-8')


def build_executable():
    print("开始构建可执行文件...")

    clean_build_dirs()

    check_requirements()

    build_command = [sys.executable, '-m', 'PyInstaller', 'cursorHelper.spec', '--clean']
    try:
        subprocess.run(build_command, encoding='utf-8', check=True)
    except subprocess.CalledProcessError as e:
        print("构建失败！")
        return False
    except UnicodeDecodeError:
        try:
            subprocess.run(build_command, encoding='gbk', check=True)
        except subprocess.CalledProcessError as e:
            print("构建失败！")
            return False

    exe_path = Path('dist/cursorHelper.exe')
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

    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    zip_name = f"cursorHelper-Windows-{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(output_dir, zip_name)
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', 'dist')
    print(f"\n已创建压缩包：{zip_path}")


def main():
    print("=== Cursor Helper 打包工具 ===")
    if build_executable():
        # 暂时禁用压缩包创建
        # create_zip()
        print("\n注意：已临时禁用压缩包创建功能，仅生成exe文件")
    print("\n打包过程完成！")


if __name__ == '__main__':
    main()
