import asyncio
import platform
import subprocess
from core import database as db

async def ping_device(ip: str) -> bool:
    """
    异步 Ping 一个 IP 地址，返回是否在线
    """
    # 根据操作系统选择参数 (Docker 容器通常是 Linux)
    param = '-c' if platform.system().lower() != 'windows' else '-n'
    command = ['ping', param, '1', '-W', '1', ip]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await process.wait()
        return process.returncode == 0
    except Exception:
        return False

async def start_background_scanner():
    """
    后台循环扫描任务
    """
    print("[SCANNER] Anyops Background Scanner Started...")
    while True:
        devices = await db.get_all_devices()
        print(f"[SCAN] Scanning {len(devices)} devices...")
        
        for d in devices:
            is_online = await ping_device(d['ip'])
            status_text = "在线" if is_online else "离线"
            
            # 只有当状态发生变化时才更新数据库，减少写入压力
            if d['status_online'] != status_text:
                await db.update_device_status(d['id'], status_text)
                print(f"[STATUS CHANGE] Device {d['device_code']} ({d['ip']}) is now {status_text}")
        
        # 每 60 秒扫一次
        await asyncio.sleep(60)
