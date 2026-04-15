from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core import database as db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/views/dashboard", response_class=HTMLResponse)
async def get_dashboard_view(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@router.get("/api/dashboard/stats", response_class=HTMLResponse)
async def get_dashboard_stats(request: Request):
    stats = await db.get_dashboard_stats()
    return templates.TemplateResponse(
        request=request, name="components/dashboard_stats.html", context={"stats": stats}
    )

@router.get("/api/dashboard/alerts", response_class=HTMLResponse)
async def get_dashboard_alerts(request: Request):
    alert_devices = await db.get_alert_devices()
    return templates.TemplateResponse(
        request=request, name="components/dashboard_alerts.html", context={"alert_devices": alert_devices}
    )

@router.get("/views/overview", response_class=HTMLResponse)
async def get_overview_view(request: Request, q: str = None):
    devices = await db.get_all_devices(q)
    return templates.TemplateResponse(
        request=request, name="overview.html", context={"devices": devices, "q": q}
    )
