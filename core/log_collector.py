import asyncio
import re
from core import database as db

# --- Syslog Header Regex ---
# 匹配标准的 Syslog 优先级 <PRI> 和后续内容
# 例如: <189>Apr 14 17:10:01 192.168.1.1 %%01IFNET/4/LINK_UP(l): Interface GigabitEthernet0/0/1 is UP.
SYSLOG_RE = re.compile(r'^<(\d+)>(.*)$')

class SyslogProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport
        print(f"[LOG] Syslog Server listening for network logs...")

    def datagram_received(self, data, addr):
        try:
            raw_msg = data.decode(errors='replace').strip()
            ip = addr[0]
            asyncio.create_task(self.process_log(ip, raw_msg))
        except Exception as e:
            print(f"[RECV ERROR] Error receiving syslog: {e}")

    async def process_log(self, ip: str, raw_msg: str):
        """解析并存储日志"""
        match = SYSLOG_RE.match(raw_msg)
        if not match:
            # 非标准格式记录原样
            await db.save_device_log(ip, 6, 16, "UNKNOWN", raw_msg, raw_msg)
            return

        pri = int(match.group(1))
        content = match.group(2)
        
        level = pri % 8
        facility = pri // 8
        
        # 针对网络设备（华为/思科等常见格式）提取 Module
        # 常见格式 %%01MODULE/LEVEL/DIGEST: MESSAGE
        module = "SYSTEM"
        msg_body = content
        
        vendor_match = re.search(r'%%(\d+)([A-Z0-9]+)/(\d+)/', content)
        if vendor_match:
            module = vendor_match.group(2)
            # 也可以从 vendor_match.group(3) 更新 level
            msg_parts = content.split(':', 1)
            msg_body = msg_parts[1].strip() if len(msg_parts) > 1 else content
        
        await db.save_device_log(ip, level, facility, module, msg_body, raw_msg)
        
        if level <= 2:
            print(f"[CRITICAL LOG] from {ip}: {msg_body}")

async def start_syslog_server(host="0.0.0.0", port=514):
    """
    启动异步 UDP 日志服务器
    注意：在 Linux 上监听 514 端口可能需要 sudo 权限
    """
    loop = asyncio.get_running_loop()
    try:
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: SyslogProtocol(),
            local_addr=(host, port)
        )
    except PermissionError:
        print(f"[WARNING] Permission denied for port {port}. Trying 1514 instead...")
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: SyslogProtocol(),
            local_addr=(host, 1514)
        )
