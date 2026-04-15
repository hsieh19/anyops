from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core import database as db
from core.ssh_proxy import SSHProxy

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/views/ssh/{device_id}", response_class=HTMLResponse)
async def get_ssh_terminal_view(request: Request, device_id: int):
    device = await db.get_device_by_id(device_id)
    if not device:
        return HTMLResponse("Device not found", status_code=404)
    return templates.TemplateResponse(
        request=request, 
        name="ssh_terminal.html", 
        context={"device_id": device_id, "device_code": device['device_code'], "ip": device['ip']}
    )

@router.websocket("/ws/ssh/{device_id}")
async def websocket_ssh_endpoint(websocket: WebSocket, device_id: int):
    await websocket.accept()
    proxy = SSHProxy(websocket)
    
    # 尝试连接
    success = await proxy.connect(device_id)
    if not success:
        return

    try:
        # 进入双向转发循环
        await proxy.bridge()
    except WebSocketDisconnect:
        print(f"🔌 WebSocket Disconnected for Device: {device_id}")
    finally:
        proxy.close()
