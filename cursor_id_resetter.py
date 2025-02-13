import os
import uuid
import hashlib
from pathlib import Path
from loguru import logger
from cursor_utils import (
    PathManager, FileManager, ProcessManager, 
    error_handler, Result
)

class CursorResetter:
    def __init__(self):
        cursor_path = PathManager.get_cursor_path()
        self.storage_file = cursor_path / 'storage.json'
        self.backup_dir = cursor_path / 'backups'
        self.updater_path = Path(os.getenv('LOCALAPPDATA')) / 'cursor-updater'

    def generate_ids(self) -> dict:
        return {
            f'telemetry.{key}': value for key, value in {
                'machineId': f"auth0|user_{hashlib.sha256(os.urandom(32)).hexdigest()}",
                'macMachineId': hashlib.sha256(os.urandom(32)).hexdigest(),
                'devDeviceId': str(uuid.uuid4()),
                'sqmId': "{" + str(uuid.uuid4()).upper() + "}"
            }.items()
        }

    def disable_auto_update(self) -> Result:
        try:
            if self.updater_path.exists():
                if self.updater_path.is_dir():
                    self.updater_path.unlink(missing_ok=True)
                    self.updater_path.touch()
                elif self.updater_path.stat().st_mode & 0o222:
                    self.updater_path.touch()
                else:
                    return Result.ok()
            else:
                self.updater_path.touch()

            FileManager.set_read_only(self.updater_path)
            return Result.ok()
        except Exception as e:
            return Result.fail(f"禁用自动更新失败: {e}")

    @error_handler
    def reset(self) -> Result:
        if not ProcessManager.run_as_admin():
            return Result.fail("需要管理员权限")

        kill_result = ProcessManager.kill_process(['Cursor', 'cursor'])
        if not kill_result:
            return kill_result

        backup_result = FileManager.backup_file(
            self.storage_file, self.backup_dir, 'storage.json.backup'
        )
        if not backup_result:
            return backup_result
        
        update_result = FileManager.update_json_file(
            self.storage_file, self.generate_ids(), make_read_only=True
        )
        if not update_result:
            return Result.fail("更新配置文件失败")
            
        disable_result = self.disable_auto_update()
        if not disable_result:
            return Result.fail("禁用自动更新失败")
            
        return Result.ok(message="重置机器码成功，已禁用自动更新")

def main():
    resetter = CursorResetter()
    result = resetter.reset()
    if result:
        logger.success(result.message)
    else:
        logger.error(result.message)

if __name__ == "__main__":
    main() 