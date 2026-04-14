import aiosqlite
import os
import random

DB_PATH = "anyops.db"

async def init_db():
    if not os.path.exists(DB_PATH):
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
                    location TEXT,
                    status_online TEXT DEFAULT '在线',
                    status_health TEXT DEFAULT 'Healthy',
                    credential_id INTEGER,
                    FOREIGN KEY (credential_id) REFERENCES credentials(id)
                )
            """)
            
            # Seed Initial Data
            # Credentials
            await db.execute(
                "INSERT INTO credentials (name, type, username, password) VALUES (?, ?, ?, ?)",
                ("华为通用凭据", "password", "admin", "Admin@123")
            )
            await db.execute(
                "INSERT INTO credentials (name, type, username, password) VALUES (?, ?, ?, ?)",
                ("核心设备RSA密钥", "key", "root", "********")
            )
            
            # Devices
            await db.executemany(
                "INSERT INTO devices (system_group, device_code, ip, subnet_mask, gateway, model, location, status_online, status_health, credential_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    ("核心网络组", "Core-SW-01", "192.168.10.1", "255.255.255.0", "192.168.10.254", "Huawei CE6800", "A栋 核心机房", "在线", "Healthy", 1),
                    ("汇聚网络组", "Dist-RT-02", "192.168.20.1", "255.255.255.0", "192.168.20.254", "Ruijie N18000", "B栋 汇聚弱电井", "离线", "Warning", 1),
                    ("接入网络组", "Acc-SW-03", "192.168.30.12", "255.255.255.128", "192.168.30.126", "Huawei S5720", "C栋 3楼配线间", "在线", "Healthy", 2),
                ]
            )
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
            return await cursor.fetchall()

async def get_device_by_id(device_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT d.*, c.name as credential_name 
            FROM devices d 
            LEFT JOIN credentials c ON d.credential_id = c.id
            WHERE d.id = ?
        """, (device_id,)) as cursor:
            return await cursor.fetchone()

async def add_device(system_group: str, device_code: str, ip: str, subnet_mask: str, gateway: str, model: str, location: str, credential_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO devices (system_group, device_code, ip, subnet_mask, gateway, model, location, credential_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (system_group, device_code, ip, subnet_mask, gateway, model, location, credential_id)
        )
        await db.commit()

async def update_device(device_id: int, system_group: str, device_code: str, ip: str, subnet_mask: str, gateway: str, model: str, location: str, credential_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE devices SET system_group=?, device_code=?, ip=?, subnet_mask=?, gateway=?, model=?, location=?, credential_id=? WHERE id=?",
            (system_group, device_code, ip, subnet_mask, gateway, model, location, credential_id, device_id)
        )
        await db.commit()

async def delete_device(device_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        await db.commit()

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
            return await cursor.fetchall()

async def add_credential(name: str, cred_type: str, username: str, password: str = None, private_key: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO credentials (name, type, username, password, private_key) VALUES (?, ?, ?, ?, ?)",
            (name, cred_type, username, password, private_key)
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
            return await cursor.fetchone()

async def update_credential(cred_id: int, name: str, cred_type: str, username: str, password: str = None, private_key: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE credentials SET name=?, type=?, username=?, password=?, private_key=? WHERE id=?",
            (name, cred_type, username, password, private_key, cred_id)
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
            return await cursor.fetchall()
