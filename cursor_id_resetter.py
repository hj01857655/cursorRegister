import os
import uuid
import hashlib
from pathlib import Path
from loguru import logger
from cursor_utils import Utils, error_handler, Result

def generate_ids() -> dict:
    return {
        f'telemetry.{key}': value for key, value in {
            'machineId': f"auth0|user_{hashlib.sha256(os.urandom(32)).hexdigest()}",
            'macMachineId': hashlib.sha256(os.urandom(32)).hexdigest(),
            'devDeviceId': str(uuid.uuid4()),
            'sqmId': "{" + str(uuid.uuid4()).upper() + "}"
        }.items()
    }

@error_handler
def reset() -> Result:
    if not Utils.run_as_admin():
        return Result.fail("需要管理员权限")

    if not (result := Utils.kill_process(['Cursor', 'cursor'])):
        return result

    cursor_path = Utils.get_path('cursor')
    storage_file = cursor_path / 'storage.json'
    backup_dir = cursor_path / 'backups'

    if not (result := Utils.backup_file(storage_file, backup_dir, 'storage.json.backup')):
        return result

    if not (result := Utils.update_json_file(storage_file, generate_ids())):
        return Result.fail("更新配置文件失败")

    try:
        updater_path = Path(os.getenv('LOCALAPPDATA')) / 'cursor-updater'
        
  
        if updater_path.is_dir():
            try:
                import shutil
                shutil.rmtree(updater_path)
            except Exception as e:
                logger.warning(f"删除cursor-updater文件夹失败: {e}")
        
        if not updater_path.exists():
            updater_path.touch(exist_ok=True)
            Utils.manage_file_permissions(updater_path)
        else:
            try:
                Utils.manage_file_permissions(updater_path)
            except PermissionError:
               
                pass
            
        return Result.ok(message="重置机器码成功，已禁用自动更新")
    except Exception as e:
        return Result.fail(f"禁用自动更新失败: {e}")

if __name__ == "__main__":
    if result := reset():
        logger.success(result.message)
    else:
        logger.error(result.message) 