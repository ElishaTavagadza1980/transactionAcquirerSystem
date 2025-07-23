from fastapi import APIRouter, Request, HTTPException, Form, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.services.merchant_service import MerchantService
from app.models.merchant_model import Merchant
import logging
from typing import Optional
from datetime import datetime
from app.utils import get_current_user


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()
templates = Jinja2Templates(directory="app/view_templates")
merchant_service = MerchantService()



@router.get("/merchants", response_class=HTMLResponse)
async def get_merchants(request: Request, user=Depends(get_current_user), merchant_service: MerchantService = Depends(MerchantService)):
    if not user:
        logger.info("Unauthorized access to /merchants: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        merchants = merchant_service.get_merchants()
        logger.info(f"Route retrieved {len(merchants)} merchants for user {user['username']}")
        template = "merchant/partials/merchant_list.html" if "HX-Request" in request.headers else "merchant/merchants.html"
        return templates.TemplateResponse(
            template,
            {"request": request, "merchants": merchants or [], "user": user}
        )
    except Exception as e:
        logger.error(f"Error retrieving merchants: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/merchants/search", response_class=HTMLResponse)
def search_merchants(request: Request, filter_field: str = Query(...), search_value: str = Query(None)):
    try:
        merchants = merchant_service.search_merchants(filter_field, search_value)
        logger.info(f"Search retrieved {len(merchants)} merchants for {filter_field}: {search_value}")
        return templates.TemplateResponse(
            "merchant/partials/merchant_list.html",
            {"request": request, "merchants": merchants}
        )
    except Exception as e:
        logger.error(f"Error searching merchants: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/merchants/addMerchant", response_class=HTMLResponse)
async def get_add_merchant_page(request: Request, user=Depends(get_current_user)):
    if not user:
        logger.info("Unauthorized access to /merchants/addMerchant: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        logger.info(f"Rendering add merchant page for user {user['username']}")
        return templates.TemplateResponse(
            "merchant/merchant_add.html",
            {"request": request, "user": user}
        )
    except Exception as e:
        logger.error(f"Error rendering add merchant page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/merchant", response_class=HTMLResponse)
def create_merchant(  
    request: Request,
    merchant_id: str = Form(...),
    business_name: str = Form(...),
    legal_name: Optional[str] = Form(None),
    business_type: Optional[str] = Form(None),
    mcc: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    website_url: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    address_firstline: Optional[str] = Form(None),
    address_secondline: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    kyc_status: str = Form("pending"),
    kyc_type: Optional[str] = Form(None),
    id_proof_type: Optional[str] = Form(None),
    id_proof_number: Optional[str] = Form(None),
    business_registration_doc: Optional[str] = Form(None),
    gst_number: Optional[str] = Form(None),
    tin: Optional[str] = Form(None),
    aml_check_status: str = Form("pending"),
    document_verification_status: Optional[str] = Form(None),
    bank_account_name: Optional[str] = Form(None),
    bank_account_number: Optional[str] = Form(None),
    ifsc_code: Optional[str] = Form(None),
    bank_name: Optional[str] = Form(None),
    settlement_currency: str = Form("INR"),
    settlement_cycle: str = Form("T+1"),
    risk_category: str = Form("medium"),
    expected_monthly_volume: Optional[float] = Form(None),
    average_ticket_size: Optional[float] = Form(None),
    underwriter_comments: Optional[str] = Form(None),
    approval_status: str = Form("pending"),
    approval_date: Optional[str] = Form(None),
    contract_signed: bool = Form(False),
    contract_signing_date: Optional[str] = Form(None),
    contract_url: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    webhook_url: Optional[str] = Form(None),
    integration_type: Optional[str] = Form(None),
    pos_terminal_count: int = Form(0),
    status: str = Form("Active"),
):
    logger.info(f"Received POST request with merchant_id: {merchant_id}")
    try:
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        merchant = Merchant(
            merchant_id=merchant_id,
            business_name=business_name,
            legal_name=legal_name,
            business_type=business_type,
            mcc=mcc,
            industry=industry,
            website_url=website_url,
            contact_email=contact_email,
            contact_phone=contact_phone,
            address_firstline=address_firstline,
            address_secondline=address_secondline,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            kyc_status=kyc_status,
            kyc_type=kyc_type,
            id_proof_type=id_proof_type,
            id_proof_number=id_proof_number,
            business_registration_doc=business_registration_doc,
            gst_number=gst_number,
            tin=tin,
            aml_check_status=aml_check_status,
            document_verification_status=document_verification_status,
            bank_account_name=bank_account_name,
            bank_account_number=bank_account_number,
            ifsc_code=ifsc_code,
            bank_name=bank_name,
            settlement_currency=settlement_currency,
            settlement_cycle=settlement_cycle,
            risk_category=risk_category,
            expected_monthly_volume=expected_monthly_volume,
            average_ticket_size=average_ticket_size,
            underwriter_comments=underwriter_comments,
            approval_status=approval_status,
            approval_date=approval_date,
            contract_signed=contract_signed,
            contract_signing_date=contract_signing_date,
            contract_url=contract_url,
            api_key=api_key,
            webhook_url=webhook_url,
            integration_type=integration_type,
            pos_terminal_count=pos_terminal_count,
            status=status,
            created_at=current_timestamp,
        )

        merchant_service.create_merchant(merchant)
        merchants = merchant_service.get_merchants()

        return HTMLResponse(
            content="<div class='alert alert-success'>Merchant added successfully</div>"
        )

    except Exception as e:
        logger.error(f"Error creating merchant: {str(e)}")
        return HTMLResponse(
            content=f"<div class='alert alert-danger'>Failed to create merchant: {str(e)}</div>",
            status_code=500
        )


@router.get("/merchants/manageMerchant/editMerchant", response_class=HTMLResponse)
async def get_edit_merchant_page(request: Request, user=Depends(get_current_user)):
    if not user:
        logger.info("Unauthorized access to /merchants/manageMerchant/editMerchant: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        logger.info(f"Rendering edit merchant page for user {user['username']}")
        return templates.TemplateResponse(
            "merchant/merchant_edit_search.html",
            {"request": request, "merchants": [], "user": user}
        )
    except Exception as e:
        logger.error(f"Error rendering edit merchant page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/merchants/manageMerchant/editMerchant/search", response_class=HTMLResponse)
def search_merchants_for_edit(request: Request, filter_field: str = Query(...), search_value: str = Query(None)):
    try:
        if not search_value or search_value.strip() == "":
            logger.info("Search value is empty, returning no merchants")
            return templates.TemplateResponse(
                "merchant/partials/merchant_edit.html",
                {"request": request, "merchants": [], "message": "Please enter a search value"}
            )
        merchants = merchant_service.search_merchants(filter_field, search_value)
        logger.info(f"Search retrieved {len(merchants)} merchants for edit {filter_field}: {search_value}")
        return templates.TemplateResponse(
            "merchant/partials/merchant_edit.html",
            {"request": request, "merchants": merchants}
        )
    except Exception as e:
        logger.error(f"Error searching merchants for edit: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/merchants/manageMerchant/edit/{merchant_id}", response_class=HTMLResponse)
def get_edit_merchant_form(request: Request, merchant_id: str):
    try:
        merchant = merchant_service.get_merchant(merchant_id)
        if merchant:
            return templates.TemplateResponse(
                "merchant/partials/merchant_update.html",
                {"request": request, "merchants": [merchant]}
            )
        raise HTTPException(status_code=404, detail="Merchant not found")
    except Exception as e:
        logger.error(f"Error retrieving merchant {merchant_id} for edit form: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/merchant/{merchant_id}", response_class=HTMLResponse)
def get_merchant(request: Request, merchant_id: str):
    try:
        merchant = merchant_service.get_merchant(merchant_id)
        if merchant:
            return templates.TemplateResponse(
                "merchant/partials/merchant_edit.html",
                {"request": request, "merchants": [merchant]}
            )
        raise HTTPException(status_code=404, detail="Merchant not found")
    except Exception as e:
        logger.error(f"Error retrieving merchant {merchant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/merchant/{merchant_id}", response_class=HTMLResponse)
def update_merchant(
    request: Request,
    merchant_id: str,
    business_name: str = Form(...),
    legal_name: Optional[str] = Form(None),
    business_type: Optional[str] = Form(None),
    mcc: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    website_url: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    address_firstline: Optional[str] = Form(None),
    address_secondline: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    kyc_status: str = Form("pending"),
    kyc_type: Optional[str] = Form(None),
    id_proof_type: Optional[str] = Form(None),
    id_proof_number: Optional[str] = Form(None),
    business_registration_doc: Optional[str] = Form(None),
    gst_number: Optional[str] = Form(None),
    tin: Optional[str] = Form(None),
    aml_check_status: str = Form("pending"),
    document_verification_status: Optional[str] = Form(None),
    bank_account_name: Optional[str] = Form(None),
    bank_account_number: Optional[str] = Form(None),
    ifsc_code: Optional[str] = Form(None),
    bank_name: Optional[str] = Form(None),
    settlement_currency: str = Form("INR"),
    settlement_cycle: str = Form("T+1"),
    risk_category: str = Form("medium"),
    expected_monthly_volume: Optional[float] = Form(None),
    average_ticket_size: Optional[float] = Form(None),
    underwriter_comments: Optional[str] = Form(None),
    approval_status: str = Form("pending"),
    approval_date: Optional[str] = Form(None),
    contract_signed: bool = Form(False),
    contract_signing_date: Optional[str] = Form(None),
    contract_url: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    webhook_url: Optional[str] = Form(None),
    integration_type: Optional[str] = Form(None),
    pos_terminal_count: int = Form(0),
    status: str = Form("Active"),
    
):
    try:
        # Generate current timestamp in YYYY-MM-DD HH:MM:SS format
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"Updating merchant: {merchant_id}")
        updates = {
            "business_name": business_name,
            "legal_name": legal_name,
            "business_type": business_type,
            "mcc": mcc,
            "industry": industry,
            "website_url": website_url,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "address_firstline": address_firstline,
            "address_secondline": address_secondline,
            "city": city,
            "state": state,
            "postal_code": postal_code,
            "country": country,
            "kyc_status": kyc_status,
            "kyc_type": kyc_type,
            "id_proof_type": id_proof_type,
            "id_proof_number": id_proof_number,
            "business_registration_doc": business_registration_doc,
            "gst_number": gst_number,
            "tin": tin,
            "aml_check_status": aml_check_status,
            "document_verification_status": document_verification_status,
            "bank_account_name": bank_account_name,
            "bank_account_number": bank_account_number,
            "ifsc_code": ifsc_code,
            "bank_name": bank_name,
            "settlement_currency": settlement_currency,
            "settlement_cycle": settlement_cycle,
            "risk_category": risk_category,
            "expected_monthly_volume": expected_monthly_volume,
            "average_ticket_size": average_ticket_size,
            "underwriter_comments": underwriter_comments,
            "approval_status": approval_status,
            "approval_date": approval_date,
            "contract_signed": contract_signed,
            "contract_signing_date": contract_signing_date,
            "contract_url": contract_url,
            "api_key": api_key,
            "webhook_url": webhook_url,
            "integration_type": integration_type,
            "pos_terminal_count": pos_terminal_count,
            "status": status,       
            "updated_at":current_timestamp,     
        }
        updated_merchant = merchant_service.update_merchant(merchant_id, updates)
        merchant = merchant_service.get_merchant(merchant_id)
        return templates.TemplateResponse(
            "merchant/partials/merchant_edit.html",
            {"request": request, "merchants": [merchant]}
        )
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error updating merchant {merchant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update merchant: {str(e)}")

@router.delete("/merchant/{merchant_id}", response_class=HTMLResponse)
def delete_merchant(request: Request, merchant_id: str):
    try:
        merchant_service.delete_merchant(merchant_id)
        merchants = merchant_service.get_merchants()
        return templates.TemplateResponse(
            "merchant/partials/merchant_list.html",
            {"request": request, "merchants": merchants, "success_message": "Merchant deleted successfully"}
        )
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error deleting merchant {merchant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete merchant: {str(e)}")
    


@router.get("/merchants/manageMerchant/configureMerchantSettings", response_class=HTMLResponse)
async def config_page(request: Request, user=Depends(get_current_user), merchant_service: MerchantService = Depends(MerchantService)):
    if not user:
        logger.info("Unauthorized access to /merchants/manageMerchant/configureMerchantSettings: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        merchants = merchant_service.get_all_merchant_ids()
        logger.info(f"Rendering configure merchant settings page for user {user['username']}")
        return templates.TemplateResponse(
            "merchant/merchant_config_settings.html",
            {"request": request, "merchants": merchants, "user": user}
        )
    except Exception as e:
        logger.error(f"Error rendering configure merchant settings page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/save-settings")
async def save_merchant_settings(request: Request):
    data = await request.json()
    merchant_id = data.get("merchant_id")
    if not merchant_id:
        return JSONResponse(content={"error": "Merchant ID required"}, status_code=400)

    settings = merchant_service.save_settings(merchant_id, data)
    return JSONResponse(content={"status": "Saved", "settings": settings.__dict__})


@router.get("/get-settings/{merchant_id}")
def get_settings(merchant_id: str):
    settings = merchant_service.get_settings(merchant_id)
    if settings:
        return JSONResponse(content=settings.__dict__)
    return JSONResponse(content={"message": "No settings found."}, status_code=404)
