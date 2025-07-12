from supabase import create_client, Client
from app.models.schemerouting_model import SchemeRouting
from starlette.config import Config
from typing import List, Optional
from fastapi import HTTPException
import logging

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

def dataAddSchemeRouting(scheme_routing: SchemeRouting) -> dict:
    try:
        data = scheme_routing.dict(exclude_unset=True, exclude={"id"})
        response = supabase.table("scheme_routing").insert(data).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        logger.error(f"Insert failed for scheme {scheme_routing.scheme}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Insert failed: {str(e)}")

def dataGetSchemeRouting(scheme: str) -> Optional[dict]:
    try:
        response = supabase.table("scheme_routing").select("*").eq("scheme", scheme.strip()).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Retrieve failed for scheme {scheme}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Retrieve failed: {str(e)}")

def dataGetAllSchemeRoutings() -> List[dict]:
    try:
        response = supabase.table("scheme_routing").select("*").execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Retrieve all failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Retrieve all failed: {str(e)}")

def dataUpdateSchemeRouting(scheme: str, scheme_routing: SchemeRouting) -> dict:
    try:
        data = scheme_routing.dict(exclude_unset=True, exclude={"id"})
        response = supabase.table("scheme_routing").update(data).eq("scheme", scheme.strip()).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail=f"No routing found for scheme {scheme}")
        return response.data[0]
    except Exception as e:
        logger.error(f"Update failed for scheme {scheme}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
