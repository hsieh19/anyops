import paramiko
import asyncio
import threading
from fastapi import WebSocket
from core import database as db

class SSHProxy:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.ssh_client = None
        self.channel = None

    async def connect(self, device_id: int):
        device = await db.get_device_execution_context(device_id)
        if not device:
            await self.websocket.send_text("❌ Device not found.")
            return False

        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 建立 SSH 连接
            self.ssh_client.connect(
                hostname=device['ip'],
                username=device['username'] or "admin",
                password=device['password'],
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            # 打开交互式 Shell
            self.channel = self.ssh_client.invoke_shell(term='xterm')
            self.channel.settimeout(0.0)
            
            return True
        except Exception as e:
            await self.websocket.send_text(f"❌ SSH Connection failed: {str(e)}")
            return False

    async def bridge(self):
        """双向桥接逻辑"""
        if not self.channel:
            return

        # 启动接收线程（从设备读到浏览器）
        loop = asyncio.get_event_loop()
        stop_event = asyncio.Event()

        async def from_device():
            while not stop_event.is_set():
                if self.channel.recv_ready():
                    data = self.channel.recv(1024).decode(errors='replace')
                    await self.websocket.send_text(data)
                await asyncio.sleep(0.01)

        async def from_browser():
            try:
                while not stop_event.is_set():
                    data = await self.websocket.receive_text()
                    if self.channel:
                        self.channel.send(data)
            except Exception:
                stop_event.set()

        # 并发执行
        await asyncio.gather(from_device(), from_browser())

    def close(self):
        if self.channel:
            self.channel.close()
        if self.ssh_client:
            self.ssh_client.close()
