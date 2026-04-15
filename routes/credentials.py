from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from core import database as db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/views/credentials", response_class=HTMLResponse)
async def get_credentials_view(request: Request, q: Optional[str] = None):
    credentials = await db.get_all_credentials(q)
    return templates.TemplateResponse(
        request=request, name="credentials.html", context={"credentials": credentials, "q": q}
    )

@router.get("/views/credentials/new", response_class=HTMLResponse)
async def get_credential_form_view(request: Request):
    return templates.TemplateResponse(request=request, name="credential_form.html")

@router.get("/views/credentials/{cred_id}/edit", response_class=HTMLResponse)
async def get_credential_edit_view(request: Request, cred_id: int):
    credential = await db.get_credential_by_id(cred_id)
    return templates.TemplateResponse(
        request=request, name="credential_form.html", context={"credential": credential}
    )

@router.post("/api/credentials", response_class=HTMLResponse)
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

@router.post("/api/credentials/{cred_id}", response_class=HTMLResponse)
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

@router.delete("/api/credentials/{cred_id}", response_class=HTMLResponse)
async def delete_credential_endpoint(request: Request, cred_id: int):
    await db.delete_credential(cred_id)
    credentials = await db.get_all_credentials()
    return templates.TemplateResponse(request=request, name="credentials.html", context={"credentials": credentials})
