from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

from app.services.transaction_service import TransactionService

# Initialize router
router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Assume templates are passed via app (configured in main.py)
templates = Jinja2Templates(directory="app/view_templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, transaction_service: TransactionService = Depends(TransactionService)):
    try:
        stats = transaction_service.get_transaction_statistics()
        return templates.TemplateResponse("home.html", {"request": request, "stats": stats})
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}")
        # Return default stats to prevent template crash
        return templates.TemplateResponse("home.html", {"request": request, "stats": {"total_transactions": 0, "total_amount": 0.0, "active_count": 0, "blocked_count": 0, "currency": "USD"}})