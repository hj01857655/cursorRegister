import os
import sys
import shutil
import ctypes
import json
import uuid
import subprocess
import hashlib
from datetime import datetime
from loguru import logger
import time

class CursorResetter:
    def __init__(self):
        appdata = os.getenv('APPDATA')
        self.storage_file = os.path.join(appdata, 'Cursor', 'User', 'globalStorage', 'storage.json')
        self.backup_dir = os.path.join(appdata, 'Cursor', 'User', 'globalStorage', 'backups')
        self.updater_path = os.path.join(os.getenv('LOCALAPPDATA'), 'cursor-updater')

    def run_as_admin(self):
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([script] + sys.argv[1:])
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            if int(ret) > 32:
                sys.exit(0)
            return False
        except:
            return False

    def generate_ids(self):
        return {
            'machineId': f"auth0|user_{hashlib.sha256(os.urandom(32)).hexdigest()}",
            'macMachineId': hashlib.sha256(os.urandom(32)).hexdigest(),
            'devDeviceId': str(uuid.uuid4()),
            'sqmId': "{" + str(uuid.uuid4()).upper() + "}"
        }

    def kill_cursor(self):
        for name in ['Cursor', 'cursor']:
            try:
                subprocess.run(['taskkill', '/F', '/IM', f'{name}.exe'], capture_output=True, check=False)
            except:
                pass

    def backup_config(self):
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
            
            if not os.path.exists(self.storage_file):
                return

            backup_files = [(f, os.path.getctime(os.path.join(self.backup_dir, f))) 
                          for f in os.listdir(self.backup_dir) 
                          if f.startswith('storage.json.backup_')]
            
            for f, _ in sorted(backup_files, key=lambda x: x[1])[:-9]:
                os.remove(os.path.join(self.backup_dir, f))

            backup_path = os.path.join(self.backup_dir, 
                                     f"storage.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(self.storage_file, backup_path)
        except:
            pass

    def take_ownership(self, path):
        try:
            subprocess.run(['takeown', '/f', path], capture_output=True, check=True)
            subprocess.run(['icacls', path, '/grant', f'{os.getenv("USERNAME")}:F'], 
                         capture_output=True, check=True)
            return True
        except:
            return False

    def update_config(self, new_ids):
        try:
            if not os.path.exists(self.storage_file):
                return False

            if not self.take_ownership(self.storage_file):
                return False

            os.chmod(self.storage_file, 0o666)
            
            with open(self.storage_file, 'r+', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in new_ids.items():
                    config[f'telemetry.{key}'] = value
                f.seek(0)
                json.dump(config, f, indent=2)
                f.truncate()

            os.chmod(self.storage_file, 0o444)
            subprocess.run(['icacls', self.storage_file, '/inheritance:r', '/grant:r', 
                          f'{os.getenv("USERNAME")}:(R)'], capture_output=True)
            return True
        except:
            return False

    def disable_auto_update(self):
        try:
            # 如果路径存在，先检查是否为目录
            if os.path.exists(self.updater_path):
                if os.path.isdir(self.updater_path):
                    shutil.rmtree(self.updater_path)
                    with open(self.updater_path, 'w') as f:
                        pass
                else:
                    # 获取文件权限
                    mode = os.stat(self.updater_path).st_mode
                    # 检查是否为只读权限 (对所有用户)
                    if not (mode & 0o222):  # 检查是否没有写权限
                        return True  # 已经是只读状态，说明之前已禁用过
            else:
                with open(self.updater_path, 'w') as f:
                    pass

            os.chmod(self.updater_path, 0o444)
            subprocess.run(['icacls', self.updater_path, '/inheritance:r', '/grant:r',
                          f'{os.getenv("USERNAME")}:(R)', 'SYSTEM:(R)', 'Administrators:(R)'],
                         capture_output=True)
            return True
        except:
            return False

    def reset(self):
        try:
            if not self.run_as_admin():
                return False, "需要管理员权限"

            self.kill_cursor()
            self.backup_config()
            if not self.update_config(self.generate_ids()):
                return False, "更新配置文件失败"
            if not self.disable_auto_update():
                return False, "禁用自动更新失败"
            return True, "重置机器码成功，已禁用自动更新"
        except Exception as e:
            return False, f"重置失败: {str(e)}"

def main():
    resetter = CursorResetter()
    success, message = resetter.reset()
    if success:
        logger.success(message)
    else:
        logger.error(message)

if __name__ == "__main__":
    main()
