import asyncio
from fastapi import APIRouter, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from core import database as db
from core import ansible_mgr

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/views/devices", response_class=HTMLResponse)
async def get_devices_view(request: Request, q: Optional[str] = None):
    devices = await db.get_all_devices(q)
    return templates.TemplateResponse(
        request=request, name="devices.html", context={"devices": devices, "q": q}
    )

@router.get("/views/devices/new", response_class=HTMLResponse)
async def get_device_form_view(request: Request):
    credentials = await db.get_all_credentials()
    return templates.TemplateResponse(
        request=request, name="device_form.html", context={"credentials": credentials}
    )

@router.get("/views/devices/{device_id}/edit", response_class=HTMLResponse)
async def get_device_edit_view(request: Request, device_id: int):
    device = await db.get_device_by_id(device_id)
    credentials = await db.get_all_credentials()
    return templates.TemplateResponse(
        request=request, name="device_form.html", context={"device": device, "credentials": credentials}
    )

@router.get("/views/devices/{device_id}/detail", response_class=HTMLResponse)
async def get_device_detail_view(request: Request, device_id: int):
    device = await db.get_device_by_id(device_id)
    return templates.TemplateResponse(
        request=request, name="device_detail.html", context={"device": device}
    )

@router.post("/api/devices", response_class=HTMLResponse)
async def create_device(
    request: Request,
    system_group: str = Form(...),
    device_code: str = Form(...),
    ip: str = Form(...),
    subnet_mask: str = Form("255.255.255.0"),
    gateway: str = Form(""),
    model: str = Form(""),
    vendor: str = Form("Other"),
    location: str = Form(""),
    credential_id: Optional[int] = Form(None)
):
    await db.add_device(system_group, device_code, ip, subnet_mask, gateway, model, vendor, location, credential_id)
    devices = await db.get_all_devices()
    return templates.TemplateResponse(request=request, name="devices.html", context={"devices": devices})

@router.post("/api/devices/{device_id}", response_class=HTMLResponse)
async def update_device_endpoint(
    request: Request,
    device_id: int,
    system_group: str = Form(...),
    device_code: str = Form(...),
    ip: str = Form(...),
    subnet_mask: str = Form("255.255.255.0"),
    gateway: str = Form(""),
    model: str = Form(""),
    vendor: str = Form("Other"),
    location: str = Form(""),
    credential_id: Optional[int] = Form(None)
):
    await db.update_device(device_id, system_group, device_code, ip, subnet_mask, gateway, model, vendor, location, credential_id)
    devices = await db.get_all_devices()
    return templates.TemplateResponse(request=request, name="devices.html", context={"devices": devices})

@router.delete("/api/devices/{device_id}", response_class=HTMLResponse)
async def delete_device_endpoint(request: Request, device_id: int):
    await db.delete_device(device_id)
    devices = await db.get_all_devices()
    return templates.TemplateResponse(request=request, name="devices.html", context={"devices": devices})

@router.post("/api/devices/{device_id}/backup", response_class=HTMLResponse)
async def trigger_backup(request: Request, device_id: int):
    async def task_wrapper():
        await ansible_mgr.run_playbook_async("backup_config.yml")
    asyncio.create_task(task_wrapper())
    return HTMLResponse(content="<span class='text-emerald-500 text-xs animate-pulse font-medium'>备份中...</span>")

@router.post("/api/devices/{device_id}/sync", response_class=HTMLResponse)
async def trigger_sync(request: Request, device_id: int):
    asyncio.create_task(ansible_mgr.collect_device_metrics_real(device_id))
    return HTMLResponse(content="<span class='text-blue-500 text-xs animate-pulse font-medium'>采集指标中...</span>")
