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

class CursorResetter:
    def __init__(self):
        appdata = os.getenv('APPDATA')
        self.storage_file = os.path.join(appdata, 'Cursor', 'User', 'globalStorage', 'storage.json')
        self.backup_dir = os.path.join(appdata, 'Cursor', 'User', 'globalStorage', 'backups')
        self.updater_path = os.path.join(os.getenv('LOCALAPPDATA'), 'cursor-updater')

    def print_banner(self):
        logger.info("""
    ██████╗██╗   ██╗██████╗ ███████╗ ██████╗ ██████╗ 
   ██╔════╝██║   ██║██╔══██╗██╔════╝██╔═══██╗██╔══██╗
   ██║     ██║   ██║██████╔╝███████╗██║   ██║██████╔╝
   ██║     ██║   ██║██╔══██╗╚════██║██║   ██║██╔══██╗
   ╚██████╗╚██████╔╝██║  ██║███████║╚██████╔╝██║  ██║
    ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝
    
================================
      Cursor ID 修改工具        
================================

[重要提示] 本工具仅支持 Cursor v0.44.11 及以下版本
[重要提示] 最新的 0.45.x 版本暂不支持
""")

    def run_as_admin(self):
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
                
            logger.info("正在请求管理员权限...")
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([script] + sys.argv[1:])
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            if int(ret) > 32:
                sys.exit(0)
            return False
        except Exception as e:
            logger.error(f"提权失败: {e}")
            return False

    def generate_ids(self):
        return {
            'machineId': f"auth0|user_{hashlib.sha256(os.urandom(32)).hexdigest()}",
            'macMachineId': hashlib.sha256(os.urandom(32)).hexdigest(),
            'devDeviceId': str(uuid.uuid4()),
            'sqmId': "{" + str(uuid.uuid4()).upper() + "}"
        }

    def kill_cursor(self):
        logger.info("检查 Cursor 进程...")
        for name in ['Cursor', 'cursor']:
            try:
                subprocess.run(['taskkill', '/F', '/IM', f'{name}.exe'], 
                             capture_output=True, check=False)
                logger.info(f"{name} 进程已处理")
            except Exception as e:
                logger.warning(f"处理进程出错: {e}")

    def backup_config(self):
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
            
            if not os.path.exists(self.storage_file):
                return

            # 清理旧备份
            backup_files = [(f, os.path.getctime(os.path.join(self.backup_dir, f))) 
                          for f in os.listdir(self.backup_dir) 
                          if f.startswith('storage.json.backup_')]
            
            for f, _ in sorted(backup_files, key=lambda x: x[1])[:-9]:  # 保留最新的10个
                os.remove(os.path.join(self.backup_dir, f))

            # 创建新备份
            backup_path = os.path.join(self.backup_dir, 
                                     f"storage.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(self.storage_file, backup_path)
            logger.info(f"配置已备份到: {backup_path}")
        except Exception as e:
            logger.error(f"备份失败: {e}")

    def take_ownership(self, path):
        try:
            subprocess.run(['takeown', '/f', path], capture_output=True, check=True)
            subprocess.run(['icacls', path, '/grant', f'{os.getenv("USERNAME")}:F'], 
                         capture_output=True, check=True)
            return True
        except Exception as e:
            logger.error(f"获取权限失败: {e}")
            return False

    def update_config(self, new_ids):
        try:
            if not os.path.exists(self.storage_file):
                logger.error("未找到配置文件，请先安装并运行一次 Cursor")
                return False

            if not self.take_ownership(self.storage_file):
                return False

            os.chmod(self.storage_file, 0o666)
            
            with open(self.storage_file, 'r+', encoding='utf-8') as f:
                config = json.load(f)
                
                # 显示旧ID
                logger.info("\n当前 ID:")
                for key in ['machineId', 'macMachineId', 'devDeviceId', 'sqmId']:
                    logger.info(f"[当前] {key}: {config.get(f'telemetry.{key}', '未设置')}")
                
                # 更新配置
                for key, value in new_ids.items():
                    config[f'telemetry.{key}'] = value
                
                f.seek(0)
                json.dump(config, f, indent=2)
                f.truncate()

            # 设置只读权限
            os.chmod(self.storage_file, 0o444)
            subprocess.run(['icacls', self.storage_file, '/inheritance:r', '/grant:r', 
                          f'{os.getenv("USERNAME")}:(R)'], capture_output=True)

            # 显示新ID
            logger.info("\n新生成的 ID:")
            for key, value in new_ids.items():
                logger.info(f"[新ID] {key}: {value}")

            return True
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False

    def disable_auto_update(self):
        try:
            if not os.path.exists(self.updater_path):
                with open(self.updater_path, 'w') as f:
                    pass
            
            if os.path.isdir(self.updater_path):
                shutil.rmtree(self.updater_path)
                with open(self.updater_path, 'w') as f:
                    pass

            os.chmod(self.updater_path, 0o444)
            subprocess.run(['icacls', self.updater_path, '/inheritance:r', '/grant:r',
                          f'{os.getenv("USERNAME")}:(R)', 'SYSTEM:(R)', 'Administrators:(R)'],
                         capture_output=True)
            logger.success("已禁用自动更新")
            return True
        except Exception as e:
            logger.error(f"禁用自动更新失败: {e}")
            return False

    def reset(self):
        try:
            if sys.platform.startswith('win'):
                os.system('chcp 65001 && cls')

            self.print_banner()

            if not self.run_as_admin():
                return False

            self.kill_cursor()
            self.backup_config()

            logger.info("正在生成新的 ID...")
            if not self.update_config(self.generate_ids()):
                return False

            logger.info("正在禁用自动更新功能...")
            if not self.disable_auto_update():
                logger.warning("自动更新禁用失败，但 ID 已更新成功")

            logger.info("\n================================")
            logger.info("  关注网站【KTOVOZ.com】一起交流更多Cursor技巧和AI知识  ")
            logger.info("================================\n")
            logger.info("请重启 Cursor 以应用新的配置\n")
            
            return True
        except Exception as e:
            logger.error(f"重置失败: {e}")
            return False

def main():
    resetter = CursorResetter()
    if resetter.reset():
        logger.info("重置机器码完成")
    else:
        logger.error("重置机器码失败")

if __name__ == "__main__":
    main()
