from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.config import settings
from app.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": settings.app_title},
    )