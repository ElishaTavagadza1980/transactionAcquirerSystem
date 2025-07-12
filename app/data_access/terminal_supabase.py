from supabase import create_client, Client
from app.models.terminal_model import Terminal
from starlette.config import Config
from typing import List, Optional
from fastapi import HTTPException
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    config = Config(".env")
    db_url: str = config("SUPABASE_URL")
    db_key: str = config("SUPABASE_KEY")
    supabase: Client = create_client(db_url, db_key)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    raise

def dataCreateTerminal(terminal: Terminal) -> dict:
    try:
        terminal_data = terminal.dict(exclude_unset=True)
        response = supabase.table("terminals").insert(terminal_data).execute()
        logger.info(f"Created terminal with terminal_id: {terminal.terminal_id}")
        return response.data[0] if response.data else {}
    except Exception as e:
        logger.error(f"Failed to create terminal {terminal.terminal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create terminal: {str(e)}")

def dataGetTerminals() -> List[dict]:
    try:
        response = supabase.table("terminals").select("*").order("created_at", desc=True).execute()
        logger.info(f"Retrieved {len(response.data)} terminals")
        logger.debug(f"Raw Supabase response: {json.dumps(response.data, indent=2)}")
        terminals = []
        for item in response.data:
            try:
                terminal = Terminal(**item)
                terminals.append(terminal.dict())
            except Exception as e:
                logger.error(f"Failed to parse terminal data {item.get('terminal_id', 'unknown')}: {str(e)}")
                continue
        return terminals
    except Exception as e:
        logger.error(f"Failed to retrieve terminals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve terminals: {str(e)}")

def dataGetTerminal(terminal_id: str) -> Optional[dict]:
    try:
        response = supabase.table("terminals").select("*").eq("terminal_id", terminal_id).execute()
        logger.debug(f"Raw Supabase response for terminal_id {terminal_id}: {json.dumps(response.data, indent=2)}")
        if response.data:
            logger.info(f"Retrieved terminal with terminal_id: {terminal_id}")
            return Terminal(**response.data[0]).dict()
        logger.info(f"Terminal not found with terminal_id: {terminal_id}")
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve terminal {terminal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve terminal: {str(e)}")

def dataUpdateTerminal(terminal_id: str, updates: dict) -> dict:
    try:
        response = supabase.table("terminals").update(updates).eq("terminal_id", terminal_id).execute()
        if not response.data:
            logger.info(f"Terminal not found with terminal_id: {terminal_id}")
            raise HTTPException(status_code=404, detail="Terminal not found")
        logger.info(f"Updated terminal with terminal_id: {terminal_id}")
        return response.data[0]
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Failed to update terminal {terminal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update terminal: {str(e)}")

def dataDeleteTerminal(terminal_id: str) -> dict:
    try:
        response = supabase.table("terminals").delete().eq("terminal_id", terminal_id).execute()
        if not response.data:
            logger.info(f"Terminal not found with terminal_id: {terminal_id}")
            raise HTTPException(status_code=404, detail="Terminal not found")
        logger.info(f"Deleted terminal with terminal_id: {terminal_id}")
        return response.data[0]
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Failed to delete terminal {terminal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete terminal: {str(e)}")

def get_all_terminals():
    response = supabase.table("terminals").select("terminal_id").execute()
    return response.data