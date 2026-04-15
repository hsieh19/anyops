import aiosqlite
import os
import random
from core import security

DB_PATH = "anyops.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Create Credentials Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL, -- 'password' or 'key'
                username TEXT,
                password TEXT,
                private_key TEXT
            )
        """)

        # Create Devices Table with credential_id
        await db.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_group TEXT NOT NULL,
                device_code TEXT NOT NULL,
                ip TEXT NOT NULL,
                subnet_mask TEXT,
                gateway TEXT,
                model TEXT,
                vendor TEXT, -- Vendor/Brand (Huawei, Cisco, etc.)
                location TEXT,
                status_online TEXT DEFAULT '未知',
                status_health TEXT DEFAULT '未知',
                last_cpu INTEGER DEFAULT 0,
                last_mem INTEGER DEFAULT 0,
                last_disk INTEGER DEFAULT 0,
                last_sync_time TEXT,
                credential_id INTEGER,
                FOREIGN KEY (credential_id) REFERENCES credentials(id)
            )
        """)

        # Create Device Logs Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS device_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER,
                ip TEXT NOT NULL,
                level INTEGER DEFAULT 6, -- Syslog Level (0-7)
                facility INTEGER DEFAULT 16,
                timestamp TEXT,
                module TEXT,
                message TEXT,
                raw_text TEXT,
                FOREIGN KEY (device_id) REFERENCES devices(id)
            )
        """)
        
        await db.commit()

async def get_all_devices(q: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        sql = """
            SELECT d.*, c.name as credential_name 
            FROM devices d 
            LEFT JOIN credentials c ON d.credential_id = c.id
        """
        params = []
        if q:
            sql += " WHERE d.device_code LIKE ? OR d.ip LIKE ? OR d.system_group LIKE ? OR d.model LIKE ?"
            like_q = f"%{q}%"
            params = [like_q, like_q, like_q, like_q]
            
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_device_by_id(device_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT d.*, c.name as credential_name 
            FROM devices d 
            LEFT JOIN credentials c ON d.credential_id = c.id
            WHERE d.id = ?
        """, (device_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def add_device(system_group: str, device_code: str, ip: str, subnet_mask: str, gateway: str, model: str, vendor: str, location: str, credential_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO devices (system_group, device_code, ip, subnet_mask, gateway, model, vendor, location, credential_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (system_group, device_code, ip, subnet_mask, gateway, model, vendor, location, credential_id)
        )
        await db.commit()

async def update_device(device_id: int, system_group: str, device_code: str, ip: str, subnet_mask: str, gateway: str, model: str, vendor: str, location: str, credential_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE devices SET system_group=?, device_code=?, ip=?, subnet_mask=?, gateway=?, model=?, vendor=?, location=?, credential_id=? WHERE id=?",
            (system_group, device_code, ip, subnet_mask, gateway, model, vendor, location, credential_id, device_id)
        )
        await db.commit()

async def delete_device(device_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        await db.commit()

async def update_device_status(device_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        health = "Healthy" if status == "在线" else "Warning"
        await db.execute(
            "UPDATE devices SET status_online=?, status_health=? WHERE id=?", 
            (status, health, device_id)
        )
        await db.commit()

async def update_device_performance(device_id: int, cpu: int, mem: int, disk: int):
    async with aiosqlite.connect(DB_PATH) as db:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            "UPDATE devices SET last_cpu=?, last_mem=?, last_disk=?, last_sync_time=? WHERE id=?",
            (cpu, mem, disk, now, device_id)
        )
        await db.commit()

async def get_device_execution_context(device_id: int):
    """
    获取设备及其完整解密凭据，用于运维任务执行
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT d.*, c.type as cred_type, c.username, c.password, c.private_key
            FROM devices d 
            LEFT JOIN credentials c ON d.credential_id = c.id
            WHERE d.id = ?
        """, (device_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            # 转换为字典并解密敏感字段
            data = dict(row)
            if data.get('password'):
                data['password'] = security.decrypt(data['password'])
            if data.get('private_key'):
                data['private_key'] = security.decrypt(data['private_key'])
            return data

# Credential CRUD
async def get_all_credentials(q: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        sql = "SELECT * FROM credentials"
        params = []
        if q:
            sql += " WHERE name LIKE ? OR username LIKE ?"
            like_q = f"%{q}%"
            params = [like_q, like_q]
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def add_credential(name: str, cred_type: str, username: str, password: str = None, private_key: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        # 加密敏感字段
        enc_password = security.encrypt(password) if password else None
        enc_key = security.encrypt(private_key) if private_key else None
        
        await db.execute(
            "INSERT INTO credentials (name, type, username, password, private_key) VALUES (?, ?, ?, ?, ?)",
            (name, cred_type, username, enc_password, enc_key)
        )
        await db.commit()

async def delete_credential(cred_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM credentials WHERE id = ?", (cred_id,))
        await db.commit()

async def get_credential_by_id(cred_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM credentials WHERE id = ?", (cred_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_credential(cred_id: int, name: str, cred_type: str, username: str, password: str = None, private_key: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        # 加密敏感字段
        enc_password = security.encrypt(password) if password else None
        enc_key = security.encrypt(private_key) if private_key else None

        await db.execute(
            "UPDATE credentials SET name=?, type=?, username=?, password=?, private_key=? WHERE id=?",
            (name, cred_type, username, enc_password, enc_key, cred_id)
        )
        await db.commit()

# Dashboard logic
async def get_dashboard_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM devices") as cur:
            total_devices = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM devices WHERE status_online = '在线'") as cur:
            online_devices = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM devices WHERE status_health != 'Healthy'") as cur:
            alerts = (await cur.fetchone())[0]
        return {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "alerts": alerts,
            "avg_cpu": random.randint(30, 75)
        }

async def get_alert_devices():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM devices WHERE status_online != '在线' OR status_health != 'Healthy' LIMIT 10") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

# --- Logging Logic ---
async def save_device_log(ip: str, level: int, facility: int, module: str, message: str, raw_text: str):
    """
    保存一条设备日志，并尝试关联已知设备列表
    """
    async with aiosqlite.connect(DB_PATH) as db:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 尝试查出设备 ID
        async with db.execute("SELECT id FROM devices WHERE ip = ?", (ip,)) as cursor:
            row = await cursor.fetchone()
            device_id = row[0] if row else None
            
        await db.execute("""
            INSERT INTO device_logs (device_id, ip, level, facility, timestamp, module, message, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (device_id, ip, level, facility, now, module, message, raw_text))
        await db.commit()

async def get_recent_logs(q: str = None, level: int = None, limit: int = 50):
    """
    获取最近的系统日志，支持关键字过滤和级别过滤
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        sql = "SELECT l.*, d.device_code FROM device_logs l LEFT JOIN devices d ON l.device_id = d.id"
        params = []
        where_clauses = []
        
        if q:
            where_clauses.append("(l.message LIKE ? OR l.ip LIKE ? OR l.module LIKE ?)")
            like_q = f"%{q}%"
            params.extend([like_q, like_q, like_q])
        
        if level is not None:
            where_clauses.append("l.level <= ?")
            params.append(level)
            
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
            
        sql += " ORDER BY l.id DESC LIMIT ?"
        params.append(limit)
        
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
