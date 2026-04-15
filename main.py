import uvicorn
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Internal modules
from core import database as db
from core import scanner
from core import log_collector

# Import routers
from routes import dashboard, devices, credentials, ssh, logs

app = FastAPI(title="Anyops Lite")

# Templates for the main entry point
templates = Jinja2Templates(directory="templates")

# Middleware / Events
@app.on_event("startup")
async def startup():
    await db.init_db()
    # 异步启动后台扫描器
    asyncio.create_task(scanner.start_background_scanner())
    # 异步启动 Syslog 日志采集器
    asyncio.create_task(log_collector.start_syslog_server())

# --- Basic Routes ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

# --- Placeholder Routes (Coming Soon) ---
@app.get("/views/tasks", response_class=HTMLResponse)
async def get_tasks_view(request: Request):
    return templates.TemplateResponse(request=request, name="placeholder.html", context={"title": "任务管理", "msg": "Ansible 任务流控开发中..."})

@app.get("/views/users", response_class=HTMLResponse)
async def get_users_view(request: Request):
    return templates.TemplateResponse(request=request, name="placeholder.html", context={"title": "用户管理", "msg": "用户权限系统开发中..."})

# --- Include Routers ---
app.include_router(dashboard.router)
app.include_router(devices.router)
app.include_router(credentials.router)
app.include_router(ssh.router)
app.include_router(logs.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
