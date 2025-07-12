from supabase import create_client, Client
from app.models.merchant_model import Merchant, MerchantSettings
from starlette.config import Config
from typing import List, Optional
from fastapi import HTTPException
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MerchantSupabase:
    def __init__(self):
        try:
            config = Config(".env")
            db_url: str = config("SUPABASE_URL")
            db_key: str = config("SUPABASE_KEY")
            self.supabase: Client = create_client(db_url, db_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise

    def create_merchant(self, merchant: Merchant) -> dict:
        try:
            merchant_data = merchant.dict(exclude_unset=True)
            response = self.supabase.table("merchants").insert(merchant_data).execute()
            logger.info(f"Created merchant with merchant_id: {merchant.merchant_id}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to create merchant {merchant.merchant_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create merchant: {str(e)}")

    def get_merchants(self) -> List[dict]:
        try:
            response = self.supabase.table("merchants").select("*").order("created_at", desc=True).execute()
            logger.info(f"Retrieved {len(response.data)} merchants")
            logger.debug(f"Raw Supabase response: {json.dumps(response.data, indent=2)}")
            merchants = []
            for item in response.data:
                try:
                    merchant = Merchant(**item)
                    merchants.append(merchant.dict())
                except Exception as e:
                    logger.error(f"Failed to parse merchant data {item.get('merchant_id', 'unknown')}: {str(e)}")
                    continue
            return merchants
        except Exception as e:
            logger.error(f"Failed to retrieve merchants: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve merchants: {str(e)}")

    def get_merchant(self, merchant_id: str) -> Optional[dict]:
        try:
            response = self.supabase.table("merchants").select("*").eq("merchant_id", merchant_id).execute()
            logger.debug(f"Raw Supabase response for merchant_id {merchant_id}: {json.dumps(response.data, indent=2)}")
            if response.data:
                logger.info(f"Retrieved merchant with merchant_id: {merchant_id}")
                return response
            logger.info(f"Merchant not found with merchant_id: {merchant_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve merchant {merchant_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve merchant: {str(e)}")

    def update_merchant(self, merchant_id: str, updates: dict) -> dict:
        try:
            response = self.supabase.table("merchants").update(updates).eq("merchant_id", merchant_id).execute()
            if not response.data:
                logger.info(f"Merchant not found with merchant_id: {merchant_id}")
                raise HTTPException(status_code=404, detail="Merchant not found")
            logger.info(f"Updated merchant with merchant_id: {merchant_id}")
            return response.data[0]
        except HTTPException as e:
            raise
        except Exception as e:
            logger.error(f"Failed to update merchant {merchant_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update merchant: {str(e)}")

    def delete_merchant(self, merchant_id: str) -> dict:
        try:
            response = self.supabase.table("merchants").delete().eq("merchant_id", merchant_id).execute()
            if not response.data:
                logger.info(f"Merchant not found with merchant_id: {merchant_id}")
                raise HTTPException(status_code=404, detail="Merchant not found")
            logger.info(f"Deleted merchant with merchant_id: {merchant_id}")
            return response.data[0]
        except HTTPException as e:
            raise
        except Exception as e:
            logger.error(f"Failed to delete merchant {merchant_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete merchant: {str(e)}")

    def get_all_merchant_ids(self) -> List[dict]:
        response = self.supabase.table("merchants").select("merchant_id").execute()
        return response.data

    def save_settings(self, merchant_id: str, settings: dict) -> MerchantSettings:
        settings_data = MerchantSettings(**settings)
        existing = self.supabase.table("merchantsettings").select("*").eq("merchant_id", merchant_id).execute()

        if existing.data:
            self.supabase.table("merchantsettings").update(settings_data.__dict__).eq("merchant_id", merchant_id).execute()
        else:
            insert_data = {"merchant_id": merchant_id, **settings_data.__dict__}
            self.supabase.table("merchantsettings").insert(insert_data).execute()

        return settings_data

    def get_settings(self, merchant_id: str) -> Optional[MerchantSettings]:
        response = self.supabase.table("merchantsettings").select("*").eq("merchant_id", merchant_id).execute()
        if response.data:
            item = response.data[0]
            return response
        return None