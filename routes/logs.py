from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from core import database as db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/views/logs", response_class=HTMLResponse)
async def get_logs_view(request: Request, q: Optional[str] = None, level: Optional[int] = None):
    """
    HTMX endpoint: Returns the logs list view
    """
    logs = await db.get_recent_logs(q=q, level=level)
    return templates.TemplateResponse(
        request=request, 
        name="logs.html", 
        context={"logs": logs, "q": q, "level": level}
    )

@router.get("/api/logs/table", response_class=HTMLResponse)
async def get_logs_table(request: Request, q: Optional[str] = None, level: Optional[int] = None):
    """
    局部刷新日志表格内容
    """
    logs = await db.get_recent_logs(q=q, level=level)
    return templates.TemplateResponse(
        request=request, 
        name="components/log_table_body.html", 
        context={"logs": logs}
    )
