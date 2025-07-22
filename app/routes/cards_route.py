from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.card_service import CardService
from app.models.card_model import Card
import logging
import csv
from io import StringIO
from typing import List
from datetime import datetime
from app.utils import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/view_templates")
card_service = CardService()

@router.get("/cards", response_class=HTMLResponse)
async def get_cards(request: Request, user=Depends(get_current_user), card_service: CardService = Depends(CardService)):
    if not user:
        logger.info("Unauthorized access to /cards: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        cards = card_service.get_cards()
        logger.info(f"Route retrieved {len(cards)} cards for user {user['username']}")
        template = "card/partials/card_list.html" if "HX-Request" in request.headers else "card/cards.html"
        return templates.TemplateResponse(
            template,
            {"request": request, "cards": cards or [], "user": user}
        )
    except Exception as e:
        logger.error(f"Error retrieving cards: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/cards/search", response_class=HTMLResponse)
def search_cards(request: Request, filter_field: str = Query(...), search_value: str = Query(None)):
    try:
        cards = card_service.get_cards()
        filtered_cards = cards
        if search_value:
            if filter_field == "card_number":
                filtered_cards = [c for c in cards if c.get("card_number") == search_value]
            elif filter_field == "card_holder_name":
                filtered_cards = [c for c in cards if search_value.lower() in c.get("card_holder_name", "").lower()]
            elif filter_field == "card_status":
                filtered_cards = [c for c in cards if c.get("card_status", "").lower() == search_value.lower()]
            else:
                filtered_cards = []
        logger.info(f"Search retrieved {len(filtered_cards)} cards for {filter_field}: {search_value}")
        return templates.TemplateResponse(
            "card/partials/card_list.html",
            {"request": request, "cards": filtered_cards}
        )
    except Exception as e:
        logger.error(f"Error searching cards: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/cards/addCard", response_class=HTMLResponse)
async def get_add_cards_page(request: Request, user=Depends(get_current_user)):
    if not user:
        logger.info("Unauthorized access to /cards/addCard: No valid user session")
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        logger.info(f"Rendering add cards page for user {user['username']}")
        return templates.TemplateResponse(
            "card/card_add.html",
            {"request": request, "user": user}
        )
    except Exception as e:
        logger.error(f"Error rendering add cards page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cards/bulk", response_class=HTMLResponse)
async def upload_cards_file(request: Request, file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.csv'):
            return HTMLResponse(
                content="""
                <div class='alert alert-danger' id='error-message'>Invalid file format. Please upload a CSV file.</div>
                <script>
                    var errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
                    document.getElementById('errorModalBody').innerText = 'Invalid file format. Please upload a CSV file.';
                    errorModal.show();
                </script>
                """,
                status_code=400
            )

        content = await file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_content))

        required_fields = ['card_number', 'card_type', 'expiry_date', 'card_holder_name', 'card_status']
        if not all(field in csv_reader.fieldnames for field in required_fields):
            missing = [field for field in required_fields if field not in csv_reader.fieldnames]
            error_message = f"Missing required fields in CSV: {', '.join(missing)}"
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

        cards = []
        batch_name = file.filename
        received_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for row in csv_reader:
            try:
                card_data = {
                    "card_number": row['card_number'],
                    "card_type": row['card_type'],
                    "expiry_date": row['expiry_date'],
                    "card_holder_name": row['card_holder_name'],
                    "card_status": row['card_status'],
                    "card_pin": row.get('card_pin'),
                    "balance": float(row.get('balance', 0.0)),
                    "cvv1": row.get('cvv1'),
                    "cvv2": row.get('cvv2'),
                    "icvv": row.get('icvv'),
                    "issue_date": row.get('issue_date'),
                    "service_code": row.get('service_code'),
                    "currency_code": row.get('currency_code'),
                    "received_at": received_at,
                    "batch_name": batch_name
                }
                card = Card(**card_data)
                cards.append(card)
            except Exception as e:
                logger.error(f"Invalid card data in row: {row}, error: {str(e)}")
                continue

        if not cards:
            return HTMLResponse(
                content="""
                <div class='alert alert-danger' id='error-message'>No valid cards found in the file.</div>
                <script>
                    var errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
                    document.getElementById('errorModalBody').innerText = 'No valid cards found in the file.';
                    errorModal.show();
                </script>
                """,
                status_code=400
            )

        card_service.create_cards_bulk(cards)
        return HTMLResponse(
            content=f"<div class='alert alert-success'>Successfully uploaded {len(cards)} cards from {batch_name}</div>"
        )
    except Exception as e:
        logger.error(f"Error uploading cards: {str(e)}")
        return HTMLResponse(
            content=f"""
            <div class='alert alert-danger' id='error-message'>Failed to upload cards: {str(e)}</div>
            <script>
                var errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
                document.getElementById('errorModalBody').innerText = 'Failed to upload cards: {str(e)}';
                errorModal.show();
            </script>
            """,
            status_code=500
        )