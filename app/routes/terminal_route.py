from fastapi import APIRouter, Request, HTTPException, Form, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.services.terminal_service import TerminalService
from app.models.terminal_model import Terminal
import logging
from typing import Optional
from datetime import datetime
from app.utils import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/view_templates")
terminal_service = TerminalService()

@router.get("/terminals", response_class=HTMLResponse)
async def get_terminals(request: Request, user=Depends(get_current_user), terminal_service: TerminalService = Depends(TerminalService)):
    if not user:
        logger.info("Unauthorized access to /terminals: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        terminals = terminal_service.get_terminals()
        logger.info(f"Route retrieved {len(terminals)} terminals for user {user['username']}")
        template = "terminal/partials/terminal_list.html" if "HX-Request" in request.headers else "terminal/terminals.html"
        return templates.TemplateResponse(
            template,
            {"request": request, "terminals": terminals or [], "user": user}
        )
    except Exception as e:
        logger.error(f"Error retrieving terminals: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/terminals/search", response_class=HTMLResponse)
def search_terminals(request: Request, filter_field: str = Query(...), search_value: str = Query(None)):
    try:
        terminals = terminal_service.search_terminals(filter_field, search_value)
        logger.info(f"Search retrieved {len(terminals)} terminals for {filter_field}: {search_value}")
        return templates.TemplateResponse(
            "terminal/partials/terminal_list.html",
            {"request": request, "terminals": terminals}
        )
    except Exception as e:
        logger.error(f"Error searching terminals: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/terminals/addTerminal", response_class=HTMLResponse)
async def get_add_terminal_page(request: Request, user=Depends(get_current_user)):
    if not user:
        logger.info("Unauthorized access to /terminals/addTerminal: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        logger.info(f"Rendering add terminal page for user {user['username']}")
        return templates.TemplateResponse(
            "terminal/terminal_add.html",
            {"request": request, "user": user}
        )
    except Exception as e:
        logger.error(f"Error rendering add terminal page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/terminal", response_class=HTMLResponse)
def create_terminal(
    request: Request,
    terminal_id: str = Form(...),
    merchant_id: str = Form(...),
    terminal_serial_number: str = Form(...),
    terminal_type: Optional[str] = Form(None),
    terminal_model: Optional[str] = Form(None),
    terminal_brand: Optional[str] = Form(None),
    firmware_version: Optional[str] = Form(None),
    status: Optional[str] = Form("inactive"),
    location_id: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    connectivity_type: Optional[str] = Form(None),
):
    logger.info(f"Received POST request with terminal_id: {terminal_id}")
    try:
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        terminal = Terminal(
            terminal_id=terminal_id,
            merchant_id=merchant_id,
            terminal_serial_number=terminal_serial_number,
            terminal_type=terminal_type,
            terminal_model=terminal_model,
            terminal_brand=terminal_brand,
            firmware_version=firmware_version,
            status=status,
            location_id=location_id,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            connectivity_type=connectivity_type,            
            created_at=current_timestamp,
        )

        terminal_service.create_terminal(terminal)
        terminals = terminal_service.get_terminals()

        return HTMLResponse(
            content="<div class='alert alert-success'>Terminal added successfully</div>"
        )
    except HTTPException as http_exc:
        if "foreign key constraint" in str(http_exc.detail) and "fk_merchant" in str(http_exc.detail):
            error_message = f"The Merchant ID ({merchant_id}) does not exist. Please use a valid Merchant ID."
            return HTMLResponse(
                content=f"""
                <div class='alert alert-danger' id='error-message'>{error_message}</div>
                <script>
                    var errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
                    document.getElementById('errorModalBody').innerText = '{error_message}';
                    errorModal.show();
                </script>
                """,
                status_code=400
            )
        logger.error(f"Error creating terminal: {str(http_exc)}")
        return HTMLResponse(
            content=f"""
            <div class='alert alert-danger' id='error-message'>Failed to create terminal: {str(http_exc.detail)}</div>
            <script>
                var errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
                document.getElementById('errorModalBody').innerText = 'Failed to create terminal: {str(http_exc.detail)}';
                errorModal.show();
            </script>
            """,
            status_code=http_exc.status_code
        )
    except Exception as e:
        logger.error(f"Error creating terminal: {str(e)}")
        return HTMLResponse(
            content=f"""
            <div class='alert alert-danger' id='error-message'>Failed to create terminal: {str(e)}</div>
            <script>
                var errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
                document.getElementById('errorModalBody').innerText = 'Failed to create terminal: {str(e)}';
                errorModal.show();
            </script>
            """,
            status_code=500
        )

@router.get("/terminals/editTerminal", response_class=HTMLResponse)
async def get_edit_terminal_page(request: Request, user=Depends(get_current_user)):
    if not user:
        logger.info("Unauthorized access to /terminals/editTerminal: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        logger.info(f"Rendering edit terminal page for user {user['username']}")
        return templates.TemplateResponse(
            "terminal/terminal_edit_search.html",
            {"request": request, "terminals": [], "user": user}
        )
    except Exception as e:
        logger.error(f"Error rendering edit terminal page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/terminals/editTerminal/search", response_class=HTMLResponse)
def search_terminals_for_edit(request: Request, filter_field: str = Query(...), search_value: str = Query(None)):
    try:
        if not search_value or search_value.strip() == "":
            logger.info("Search value is empty, returning no terminals")
            return templates.TemplateResponse(
                "terminal/partials/terminal_edit.html",
                {"request": request, "terminals": [], "message": "Please enter a search value"}
            )
        terminals = terminal_service.search_terminals(filter_field, search_value)
        logger.info(f"Search retrieved {len(terminals)} terminals for edit {filter_field}: {search_value}")
        return templates.TemplateResponse(
            "terminal/partials/terminal_edit.html",
            {"request": request, "terminals": terminals}
        )
    except Exception as e:
        logger.error(f"Error searching terminals for edit: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/terminals/editTerminal/{terminal_id}", response_class=HTMLResponse)
def get_edit_terminal_form(request: Request, terminal_id: str):
    try:
        terminal = terminal_service.get_terminal(terminal_id)
        if terminal:
            return templates.TemplateResponse(
                "terminal/partials/terminal_update.html",
                {"request": request, "terminals": [terminal]}
            )
        raise HTTPException(status_code=404, detail="Terminal not found")
    except Exception as e:
        logger.error(f"Error retrieving terminal {terminal_id} for edit form: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/terminal/{terminal_id}", response_class=HTMLResponse)
def get_terminal(request: Request, terminal_id: str):
    try:
        terminal = terminal_service.get_terminal(terminal_id)
        if terminal:
            return templates.TemplateResponse(
                "terminal/partials/terminal_edit.html",
                {"request": request, "terminals": [terminal]}
            )
        raise HTTPException(status_code=404, detail="Terminal not found")
    except Exception as e:
        logger.error(f"Error retrieving terminal {terminal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/terminal/{terminal_id}", response_class=HTMLResponse)
def update_terminal(
    request: Request,
    terminal_id: str,
    merchant_id: str = Form(...),
    terminal_serial_number: str = Form(...),
    terminal_type: Optional[str] = Form(None),
    terminal_model: Optional[str] = Form(None),
    terminal_brand: Optional[str] = Form(None),
    firmware_version: Optional[str] = Form(None),
    status: Optional[str] = Form("inactive"),
    location_id: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    connectivity_type: Optional[str] = Form(None),
):
    try:
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"Updating terminal: {terminal_id}")
        updates = {
            "merchant_id": merchant_id,
            "terminal_serial_number": terminal_serial_number,
            "terminal_type": terminal_type,
            "terminal_model": terminal_model,
            "terminal_brand": terminal_brand,
            "firmware_version": firmware_version,
            "status": status,
            "location_id": location_id,
            "city": city,
            "state": state,
            "postal_code": postal_code,
            "country": country,
            "connectivity_type": connectivity_type,
            "updated_at": current_timestamp,
        }
        updated_terminal = terminal_service.update_terminal(terminal_id, updates)
        terminal = terminal_service.get_terminal(terminal_id)
        return templates.TemplateResponse(
            "terminal/partials/terminal_edit.html",
            {"request": request, "terminals": [terminal]}
        )
    except HTTPException as http_exc:
        if "foreign key constraint" in str(http_exc.detail) and "fk_merchant" in str(http_exc.detail):
            error_message = f"The Merchant ID ({merchant_id}) does not exist. Please use a valid Merchant ID."
            return HTMLResponse(
                content=f"""
                <div class='alert alert-danger' id='error-message'>{error_message}</div>
                <script>
                    var errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
                    document.getElementById('errorModalBody').innerText = '{error_message}';
                    errorModal.show();
                </script>
                """,
                status_code=400
            )
        logger.error(f"Error updating terminal: {str(http_exc)}")
        raise
    except Exception as e:
        logger.error(f"Error updating terminal {terminal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update terminal: {str(e)}")

@router.delete("/terminal/{terminal_id}", response_class=HTMLResponse)
def delete_terminal(request: Request, terminal_id: str):
    try:
        terminal_service.delete_terminal(terminal_id)
        terminals = terminal_service.get_terminals()
        return templates.TemplateResponse(
            "terminal/partials/terminal_list.html",
            {"request": request, "terminals": terminals, "success_message": "Terminal deleted successfully"}
        )
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error deleting terminal {terminal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete terminal: {str(e)}")