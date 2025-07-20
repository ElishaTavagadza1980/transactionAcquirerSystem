from fastapi import APIRouter, Query, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.data_access.transaction_supabase import (
    dataGetacquiredtransactions,
    dataGetTransaction,
    dataGetacquiredtransactionsByRetrieval,
)
from app.services.transaction_service import TransactionService
from app.models.transaction_model import Transaction
from datetime import datetime

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/view_templates")

@router.get("/", response_class=HTMLResponse)
def get_home_page(request: Request, transaction_service: TransactionService = Depends(TransactionService)):
    try:
        logger.debug("Fetching transaction statistics for home page")
        stats = transaction_service.get_transaction_statistics()
        return templates.TemplateResponse(
            "home.html",
            {"request": request, "stats": stats}
        )
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal service error")

@router.get("/acquiredtransactions", response_class=HTMLResponse)
def get_acquiredtransactions(request: Request, filterBy: str = Query(None), searchTerm: str = Query(None)):
    try:
        acquiredtransactions = dataGetacquiredtransactions(filter_by=filterBy, search_term=searchTerm)
        logger.info(f"Retrieved {len(acquiredtransactions)} acquiredtransactions for display")
        if "HX-Request" in request.headers:
            return templates.TemplateResponse(
                "transaction/partials/transaction_list.html",
                {"request": request, "acquiredtransactions": acquiredtransactions or []}
            )
        return templates.TemplateResponse(
            "transaction/acquiredtransactions.html",
            {"request": request, "acquiredtransactions": acquiredtransactions or []}
        )
    except Exception as e:
        logger.error(f"Error retrieving acquiredtransactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal service error")

@router.get("/transaction/{systemTraceAuditNumber}")
def get_transaction(systemTraceAuditNumber: str):
    try:
        transaction = dataGetTransaction(systemTraceAuditNumber)
        if transaction:
            return transaction
        raise HTTPException(status_code=404, detail="Transaction not found")
    except Exception as e:
        logger.error(f"Error retrieving transaction {systemTraceAuditNumber}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal service error")

@router.get("/by-retrieval/{retrievalReferenceNumber}", response_class=HTMLResponse)
def get_acquiredtransactions_by_retrieval(request: Request, retrievalReferenceNumber: str, mti: str = Query("0100")):
    try:
        logger.info(f"Fetching acquired transaction for retrieval reference: {retrievalReferenceNumber} with MTI: {mti}")
        # Fetch transactions for the given retrieval reference and MTI
        acquiredtransactions = dataGetacquiredtransactionsByRetrieval(retrievalReferenceNumber, mti)
        logger.info(f"Retrieved {len(acquiredtransactions)} transactions with MTI {mti}")
        
        # Assume only one transaction per MTI, take the first if available
        transaction = acquiredtransactions[0] if acquiredtransactions else None
        
        return templates.TemplateResponse(
            "transaction/partials/mti_content.html",
            {"request": request, "transaction": transaction}
        )
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error retrieving acquired transaction for retrieval reference {retrievalReferenceNumber}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal service error")

@router.post("/acquiredtransactions")
def process_transaction_endpoint(
    transaction: Transaction,
    request: Request,
    transaction_service: TransactionService = Depends(TransactionService)
):
    try:
        logger.info(f"Processing transaction with systemTraceAuditNumber: {transaction.de_11_system_trace_audit_number}")
        result = transaction_service.process_transaction(transaction)
        if request.headers.get("Accept") == "application/json":
            return JSONResponse(content={
                 "response_code": result.de_39_response_code,
                "authorization_id": result.de_38_authorization_id_response or "N/A",
                "retrieval_reference_number": result.de_37_retrieval_reference_number,
                "system_trace_audit_number": result.de_11_system_trace_audit_number,
                "card_number": result.de_2_pan,
                "amount": result.de_4_amount_transaction,
                "currency_code": result.de_49_currency_code_transaction
            })
        return HTMLResponse(content=f"""
            <div class="alert alert-{'success' if result.status == 'APPROVED' else (result.status_reason or 'Transaction Declined').replace(' ', '-')}" >
            <h4>Transaction Response (0110)</h4>
            <p><strong>Status:</strong> {result.status}</p>
            <p><strong>Response Code:</strong> {result.de_39_response_code}</p>
            <p><strong>Authorization ID:</strong> {result.de_38_authorization_id_response or 'N/A'}</p>
            <p><strong>Retrieval Reference Number:</strong> {result.de_37_retrieval_reference_number}</p>
            <p><strong>System Trace Audit Number:</strong> {result.de_11_system_trace_audit_number}</p>
            <p><strong>Card Number:</strong> {result.de_2_pan}</p>
            <p><strong>Amount:</strong> {result.de_4_amount_transaction}</p>
        </div>
        """)
    except HTTPException as e:
        logger.error(f"HTTP error processing transaction: {str(e)}")
        raise
    except Exception as e:
        logger.exception("Unexpected error processing transaction")
        raise HTTPException(status_code=500, detail=f"Failed to process transaction: {str(e)}")

@router.get("/test", response_class=HTMLResponse)
def get_test_transaction_form(request: Request):
    try:
        logger.info("Rendering test transaction form")
        return templates.TemplateResponse(
            "transaction/test_transaction.html",
            {"request": request, "now": datetime.now()}
        )
    except Exception as e:
        logger.error(f"Error rendering test transaction form: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal service error")
    

@router.get("/transaction-statistics")
def get_transaction_stats_over_time():
    try:
        from app.data_access.transaction_supabase import dataGetTransactionStatsOverTime
        stats = dataGetTransactionStatsOverTime()
        return stats
    except Exception as e:
        logger.error(f"Error in /api/transaction-statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")
