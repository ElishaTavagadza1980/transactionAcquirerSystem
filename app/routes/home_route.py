from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging
from app.services.transaction_service import TransactionService
from app.utils import get_current_user

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="app/view_templates")

@router.get("/home", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_current_user), transaction_service: TransactionService = Depends(TransactionService)):
    if not user:
        logger.info("Unauthorized access to /home: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        # Temporarily disabled until implemented
        # stats = transaction_service.get_transaction_statistics()
        stats = {
            "total_transactions": 0,
            "total_amount": 0.0,
            "active_count": 0,
            "blocked_count": 0,
            "currency": "USD"
        }
        logger.info(f"Rendering home page for user {user['username']}")
        return templates.TemplateResponse("home.html", {"request": request, "stats": stats, "user": user})
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}")
        return templates.TemplateResponse("home.html", {
            "request": request,
            "stats": {"total_transactions": 0, "total_amount": 0.0, "active_count": 0, "blocked_count": 0, "currency": "USD"},
            "user": user
        })
