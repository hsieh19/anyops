from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
from typing import Optional

# Internal modules
from core import database as db
from core import ansible_mgr

app = FastAPI(title="Anyops Lite")
templates = Jinja2Templates(directory="templates")

# Middleware / Events
@app.on_event("startup")
async def startup():
    await db.init_db()

# --- Views ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

@app.get("/views/dashboard", response_class=HTMLResponse)
async def get_dashboard_view(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@app.get("/api/dashboard/stats", response_class=HTMLResponse)
async def get_dashboard_stats(request: Request):
    stats = await db.get_dashboard_stats()
    return templates.TemplateResponse(
        request=request, name="components/dashboard_stats.html", context={"stats": stats}
    )

@app.get("/api/dashboard/alerts", response_class=HTMLResponse)
async def get_dashboard_alerts(request: Request):
    alert_devices = await db.get_alert_devices()
    return templates.TemplateResponse(
        request=request, name="components/dashboard_alerts.html", context={"alert_devices": alert_devices}
    )

@app.get("/views/overview", response_class=HTMLResponse)
async def get_overview_view(request: Request, q: Optional[str] = None):
    """
    HTMX endpoint: Returns the hardware performance overview page with optional filter
    """
    devices = await db.get_all_devices(q)
    import random
    items = []
    for d in devices:
        items.append({
            "device": d,
            "cpu": random.randint(10, 95),
            "mem_total": random.choice([16, 32, 64, 128]),
            "mem_util": random.randint(20, 90),
            "disk_total": random.choice([250, 500, 1000]),
            "disk_util": random.randint(30, 85)
        })
    return templates.TemplateResponse(
        request=request, name="overview.html", context={"items": items, "q": q}
    )

@app.get("/views/devices", response_class=HTMLResponse)
async def get_devices_view(request: Request, q: Optional[str] = None):
    """
    HTMX endpoint: Returns the devices list view with optional filter
    """
    devices = await db.get_all_devices(q)
    return templates.TemplateResponse(
        request=request, name="devices.html", context={"devices": devices, "q": q}
    )

@app.get("/views/devices/new", response_class=HTMLResponse)
async def get_device_form_view(request: Request):
    credentials = await db.get_all_credentials()
    return templates.TemplateResponse(
        request=request, name="device_form.html", context={"credentials": credentials}
    )

@app.get("/views/devices/{device_id}/edit", response_class=HTMLResponse)
async def get_device_edit_view(request: Request, device_id: int):
    device = await db.get_device_by_id(device_id)
    credentials = await db.get_all_credentials()
    return templates.TemplateResponse(
        request=request, name="device_form.html", context={"device": device, "credentials": credentials}
    )

@app.get("/views/devices/{device_id}/detail", response_class=HTMLResponse)
async def get_device_detail_view(request: Request, device_id: int):
    device = await db.get_device_by_id(device_id)
    import random
    item = {
        "cpu": random.randint(10, 95),
        "mem_total": random.choice([16, 32, 64, 128]),
        "mem_util": random.randint(20, 90),
        "disk_total": random.choice([250, 500, 1000]),
        "disk_util": random.randint(30, 85)
    }
    return templates.TemplateResponse(
        request=request, name="device_detail.html", context={"device": device, "item": item}
    )

# --- Credentials Views ---
@app.get("/views/credentials", response_class=HTMLResponse)
async def get_credentials_view(request: Request, q: Optional[str] = None):
    """
    HTMX endpoint: Returns the credentials list view with optional filter
    """
    credentials = await db.get_all_credentials(q)
    return templates.TemplateResponse(
        request=request, name="credentials.html", context={"credentials": credentials, "q": q}
    )

@app.get("/views/credentials/new", response_class=HTMLResponse)
async def get_credential_form_view(request: Request):
    return templates.TemplateResponse(request=request, name="credential_form.html")

@app.get("/views/credentials/{cred_id}/edit", response_class=HTMLResponse)
async def get_credential_edit_view(request: Request, cred_id: int):
    """
    HTMX endpoint: Returns the credential modal pre-filled with data
    """
    credential = await db.get_credential_by_id(cred_id)
    return templates.TemplateResponse(
        request=request, name="credential_form.html", context={"credential": credential}
    )

# --- API Endpoints ---
@app.post("/api/devices", response_class=HTMLResponse)
async def create_device(
    request: Request,
    system_group: str = Form(...),
    device_code: str = Form(...),
    ip: str = Form(...),
    subnet_mask: str = Form("255.255.255.0"),
    gateway: str = Form(""),
    model: str = Form(""),
    location: str = Form(""),
    credential_id: Optional[int] = Form(None)
):
    await db.add_device(system_group, device_code, ip, subnet_mask, gateway, model, location, credential_id)
    devices = await db.get_all_devices()
    return templates.TemplateResponse(request=request, name="devices.html", context={"devices": devices})

@app.post("/api/devices/{device_id}", response_class=HTMLResponse)
async def update_device_endpoint(
    request: Request,
    device_id: int,
    system_group: str = Form(...),
    device_code: str = Form(...),
    ip: str = Form(...),
    subnet_mask: str = Form("255.255.255.0"),
    gateway: str = Form(""),
    model: str = Form(""),
    location: str = Form(""),
    credential_id: Optional[int] = Form(None)
):
    await db.update_device(device_id, system_group, device_code, ip, subnet_mask, gateway, model, location, credential_id)
    devices = await db.get_all_devices()
    return templates.TemplateResponse(request=request, name="devices.html", context={"devices": devices})

@app.delete("/api/devices/{device_id}", response_class=HTMLResponse)
async def delete_device_endpoint(request: Request, device_id: int):
    await db.delete_device(device_id)
    devices = await db.get_all_devices()
    return templates.TemplateResponse(request=request, name="devices.html", context={"devices": devices})

@app.post("/api/credentials", response_class=HTMLResponse)
async def create_credential(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    username: str = Form(...),
    password: Optional[str] = Form(None),
    private_key: Optional[str] = Form(None)
):
    await db.add_credential(name, type, username, password, private_key)
    credentials = await db.get_all_credentials()
    return templates.TemplateResponse(request=request, name="credentials.html", context={"credentials": credentials})

@app.post("/api/credentials/{cred_id}", response_class=HTMLResponse)
async def update_credential_endpoint(
    request: Request,
    cred_id: int,
    name: str = Form(...),
    type: str = Form(...),
    username: str = Form(...),
    password: Optional[str] = Form(None),
    private_key: Optional[str] = Form(None)
):
    await db.update_credential(cred_id, name, type, username, password, private_key)
    credentials = await db.get_all_credentials()
    return templates.TemplateResponse(request=request, name="credentials.html", context={"credentials": credentials})

@app.delete("/api/credentials/{cred_id}", response_class=HTMLResponse)
async def delete_credential_endpoint(request: Request, cred_id: int):
    await db.delete_credential(cred_id)
    credentials = await db.get_all_credentials()
    return templates.TemplateResponse(request=request, name="credentials.html", context={"credentials": credentials})

@app.post("/api/devices/{device_id}/backup", response_class=HTMLResponse)
async def trigger_backup(request: Request, device_id: int):
    async def task_wrapper():
        await ansible_mgr.run_playbook_async("backup_config.yml")
    asyncio.create_task(task_wrapper())
    return HTMLResponse(content="<span class='text-emerald-500 text-xs animate-pulse font-medium'>备份中...</span>")

@app.get("/views/tasks", response_class=HTMLResponse)
async def get_tasks_view(request: Request):
    return templates.TemplateResponse(request=request, name="placeholder.html", context={"title": "任务管理", "msg": "Ansible 任务流控开发中..."})

@app.get("/views/users", response_class=HTMLResponse)
async def get_users_view(request: Request):
    return templates.TemplateResponse(request=request, name="placeholder.html", context={"title": "用户管理", "msg": "用户权限系统开发中..."})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
