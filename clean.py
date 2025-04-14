import os
import shutil
import glob


def clean_build_dirs():
    dirs_to_clean = ['build', 'dist', 'output']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已清理 {dir_name} 目录")


def clean_cache_files():
    # 排除虚拟环境目录
    exclude_dirs = ['.venv', 'venv', 'env', 'ENV']
    
    # 清理所有__pycache__目录（排除虚拟环境）
    for pycache_dir in glob.glob("**/__pycache__", recursive=True):
        # 检查路径是否包含排除目录
        if not any(exclude_dir in pycache_dir.split(os.sep) for exclude_dir in exclude_dirs):
            if os.path.exists(pycache_dir):
                shutil.rmtree(pycache_dir)
                print(f"已清理 {pycache_dir} 目录")
    
    # 清理所有.pyc、.pyo和.pyd文件（排除虚拟环境）
    for pattern in ["**/*.pyc", "**/*.pyo", "**/*.pyd"]:
        for pyc_file in glob.glob(pattern, recursive=True):
            # 检查路径是否包含排除目录
            if not any(exclude_dir in pyc_file.split(os.sep) for exclude_dir in exclude_dirs):
                try:
                    os.remove(pyc_file)
                    print(f"已删除 {pyc_file}")
                except (PermissionError, FileNotFoundError) as e:
                    print(f"无法删除 {pyc_file}: {str(e)}")


def clean_log_files():
    # 清理日志文件目录
    log_dirs = ['cursorHelper_log']
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            shutil.rmtree(log_dir)
            print(f"已清理 {log_dir} 目录")
    
    # 清理单个日志文件
    for log_file in glob.glob("**/*.log", recursive=True):
        # 排除虚拟环境中的日志文件
        if not any(exclude_dir in log_file.split(os.sep) for exclude_dir in ['.venv', 'venv', 'env', 'ENV']):
            try:
                os.remove(log_file)
                print(f"已删除 {log_file}")
            except (PermissionError, FileNotFoundError) as e:
                print(f"无法删除 {log_file}: {str(e)}")


def main():
    print("=== cursorHelper 清理工具 ===")
    print("\n清理构建目录...")
    clean_build_dirs()
    
    print("\n清理缓存文件...")
    clean_cache_files()
    
    print("\n清理日志文件...")
    clean_log_files()
    
    print("\n清理完成！项目已恢复干净状态。")


if __name__ == '__main__':
    main()
