from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from app.data_access.transaction_supabase import dataGetacquiredtransactions
from app.data_access.merchant_supabase import MerchantSupabase
from app.services.settlement_service import SettlementService
import logging
from datetime import datetime, date
from typing import Optional
import os
from app.utils import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/view_templates")

@router.get("/", response_class=HTMLResponse)
async def get_settlement_page(request: Request, user=Depends(get_current_user), start_date: Optional[date] = None, end_date: Optional[date] = None):
    if not user:
        logger.info("Unauthorized access to /settlement: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        logger.debug(f"Rendering settlement page for user {user['username']}")
        return templates.TemplateResponse(
            "settlement/settlement.html",
            {
                "request": request,
                "start_date": start_date or date.today(),
                "end_date": end_date or date.today(),
                "user": user
            }
        )
    except Exception as e:
        logger.error(f"Error rendering settlement page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/generate")
async def generate_settlement_report(
    request: Request,
    start_date: date,
    end_date: date,
    merchant_id: Optional[str] = None,
    settlement_service: SettlementService = Depends(SettlementService)
):
    try:
        logger.info(f"Generating settlement report for {start_date} to {end_date}, merchant_id: {merchant_id}")
        file_path = await settlement_service.generate_settlement_report(start_date, end_date, merchant_id)
        try:
            with open(file_path, "rb") as file:
                content = file.read()
            headers = {
                "Content-Disposition": f'attachment; filename="settlement_report_{start_date}_to_{end_date}.csv"',
                "Content-Type": "text/csv"
            }
            return Response(content=content, headers=headers)
        finally:         
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up local file: {file_path}")
    except Exception as e:
        logger.error(f"Error generating settlement report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate settlement report")

@router.post("/send")
async def send_settlement_report(
    start_date: date,
    end_date: date,
    merchant_id: Optional[str] = None,
    settlement_service: SettlementService = Depends(SettlementService)
):
    try:
        logger.info(f"Sending settlement report for {start_date} to {end_date}, merchant_id: {merchant_id}")
        result = await settlement_service.send_settlement_report(start_date, end_date, merchant_id)
        return {"message": "Settlement report sent successfully", "details": result}
    except Exception as e:
        logger.error(f"Error sending settlement report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send settlement report")