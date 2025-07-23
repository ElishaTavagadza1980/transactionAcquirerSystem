from supabase import create_client, Client
from app.models.transaction_model import Transaction
from starlette.config import Config
from typing import List, Optional
from fastapi import HTTPException
from datetime import datetime
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    config = Config(".env")
    db_url: str = config("SUPABASE_URL")
    db_key: str = config("SUPABASE_KEY")
    supabase: Client = create_client(db_url, db_key)
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    raise

def dataAddTransaction(transaction: Transaction) -> dict:
    try:
        transaction_data = transaction.dict(exclude_unset=True)
        response = supabase.table("acquiredtransactions").insert(transaction_data).execute()
        logger.info(f"Inserted transaction with systemTraceAuditNumber: {transaction.de_11_system_trace_audit_number}")
        return response.data[0] if response.data else {}
    except Exception as e:
        logger.error(f"Failed to insert transaction {transaction.de_11_system_trace_audit_number}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to insert transaction: {str(e)}")

def dataGetacquiredtransactions(filter_by: Optional[str] = None, search_term: Optional[str] = None) -> List[dict]:
    try:
        query = supabase.table("acquiredtransactions").select("*").eq("message_type_indicator", "0110")
        if filter_by and search_term:
            column_map = {
                "de_37_retrieval_reference_number": "de_37_retrieval_reference_number",
                "de_41_card_acceptor_terminal_id": "de_41_card_acceptor_terminal_id",
                "de_42_card_acceptor_id": "de_42_card_acceptor_id",
                "de_18_merchant_type": "de_18_merchant_type",
                "de_11_system_trace_audit_number": "de_11_system_trace_audit_number"
            }
            if filter_by in column_map:
                query = query.eq(column_map[filter_by], search_term.strip())
        response = query.execute()
        return [Transaction(**item).dict() for item in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Failed to retrieve acquiredtransactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transactions: {str(e)}")

def dataGetTransaction(systemTraceAuditNumber: str) -> Optional[dict]:
    try:
        response = supabase.table("acquiredtransactions").select("*").eq(
            "de_11_system_trace_audit_number", systemTraceAuditNumber.strip()
        ).execute()
        if response.data:
            return Transaction(**response.data[0]).dict()
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve transaction {systemTraceAuditNumber}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transaction: {str(e)}")

def dataGetacquiredtransactionsByRetrieval(retrievalReferenceNumber: str, mti: Optional[str] = None) -> List[dict]:
    try:
        query = supabase.table("acquiredtransactions").select("*").eq(
            "de_37_retrieval_reference_number", retrievalReferenceNumber.strip()
        )
        if mti:
            query = query.eq("message_type_indicator", mti)
        response = query.execute()
        logger.info(f"Supabase response for retrieval reference {retrievalReferenceNumber} and MTI {mti}: {response.data}")
        return [Transaction(**item).dict() for item in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Failed to retrieve acquiredtransactions for retrieval reference {retrievalReferenceNumber}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transactions by retrieval: {str(e)}")
    
def dataGetTransactionStatsOverTime() -> dict:
    try:
        # Get all 0110 transactions (responses)
        response = supabase.table("acquiredtransactions").select("created_at", "status").eq("message_type_indicator", "0110").execute()

        if not response.data:
            return {"labels": [], "totalTransactions": [], "approvedTransactions": [], "declinedTransactions": []}

        # Count transactions per day
        date_counts = defaultdict(int)
        approved_counts = defaultdict(int)
        declined_counts = defaultdict(int)

        for row in response.data:
            # Parse and normalize date
            dt = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
            date_counts[date_str] += 1
            
            # Categorize by status
            if row["status"] == "APPROVED":
                approved_counts[date_str] += 1
            else:
                declined_counts[date_str] += 1

        # Sort by date
        sorted_dates = sorted(date_counts.keys())
        labels = sorted_dates
        total_transactions = [date_counts[date] for date in sorted_dates]
        approved_transactions = [approved_counts[date] for date in sorted_dates]
        declined_transactions = [declined_counts[date] for date in sorted_dates]

        return {
            "labels": labels,
            "totalTransactions": total_transactions,
            "approvedTransactions": approved_transactions,
            "declinedTransactions": declined_transactions
        }

    except Exception as e:
        logger.error(f"Failed to get transaction statistics over time: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch transaction chart data")

