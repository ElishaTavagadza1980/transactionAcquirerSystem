from fastapi import APIRouter, Form, Request,Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.schemerouting_service import SchemeRoutingService
from app.models.schemerouting_model import SchemeRouting
from fastapi import HTTPException
import logging
from app.utils import get_current_user

router = APIRouter(tags=["Scheme Routing"])

templates = Jinja2Templates(directory="app/view_templates")
logger = logging.getLogger(__name__)
service = SchemeRoutingService()

@router.get("/", response_class=HTMLResponse)
async def get_scheme_routings(request: Request, user=Depends(get_current_user), service: SchemeRoutingService = Depends(SchemeRoutingService)):
    if not user:
        logger.info("Unauthorized access to /schemerouting: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        routings = service.get_all_scheme_routings()
        logger.info(f"Rendering scheme routings page for user {user['username']}")
        return templates.TemplateResponse(
            "schemerouting/schemerouting.html",
            {"request": request, "routings": routings, "error": None, "user": user}
        )
    except Exception as e:
        logger.error(f"Error rendering scheme routings page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/create", response_class=HTMLResponse)
async def create_scheme_routing(request: Request, scheme: str = Form(...), routing: str = Form(...)):
    try:
        scheme_routing = SchemeRouting(scheme=scheme, routing=routing)
        service.create_scheme_routing(scheme_routing)
        routings = service.get_all_scheme_routings()
        return templates.TemplateResponse("schemerouting/schemerouting.html", {"request": request, "routings": routings, "error": None})
    except HTTPException as e:
        routings = service.get_all_scheme_routings()
        return templates.TemplateResponse("schemerouting/schemerouting.html", {"request": request, "routings": routings, "error": str(e.detail)})

@router.post("/update", response_class=HTMLResponse)
async def update_scheme_routing(request: Request, scheme: str = Form(...), routing: str = Form(...)):
    try:
        service.update_scheme_routing(scheme, routing)
        routings = service.get_all_scheme_routings()
        return templates.TemplateResponse("schemerouting/schemerouting.html", {"request": request, "routings": routings, "error": None})
    except HTTPException as e:
        routings = service.get_all_scheme_routings()
        return templates.TemplateResponse("schemerouting/schemerouting.html", {"request": request, "routings": routings, "error": str(e.detail)})

@router.get("/api/routing/{scheme}", response_model=SchemeRouting)
async def get_scheme_routing_api(scheme: str):
    return service.get_scheme_routing(scheme)
