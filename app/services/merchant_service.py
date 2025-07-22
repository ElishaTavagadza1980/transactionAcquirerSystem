from app.data_access.merchant_supabase import MerchantSupabase
from app.models.merchant_model import Merchant, MerchantSettings

import logging
from typing import List, Optional
from fastapi import HTTPException
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MerchantService:
    def __init__(self):
        self.logger = logger
        self.data_access = MerchantSupabase()

    def get_merchants(self) -> List[dict]:
        try:
            merchants = self.data_access.get_merchants()
            self.logger.info(f"Service retrieved {len(merchants)} merchants")
            return merchants
        except Exception as e:
            self.logger.error(f"Error retrieving merchants: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve merchants: {str(e)}")

    def search_merchants(self, filter_field: str, search_value: str = None) -> List[dict]:
        try:
            all_merchants = self.data_access.get_merchants()
            self.logger.debug(f"Raw merchants data: {json.dumps(all_merchants, indent=2)}")
            filtered_merchants = all_merchants

            if search_value:
                if filter_field == "merchant_id":
                    filtered_merchants = [m for m in filtered_merchants if m.get("merchant_id") == search_value]
                elif filter_field == "business_name":
                    filtered_merchants = [m for m in filtered_merchants if search_value.lower() in m.get("business_name", "").lower()]
                elif filter_field == "status":
                    filtered_merchants = [m for m in filtered_merchants if m.get("status", "").lower() == search_value.lower()]
                else:
                    filtered_merchants = []

            # Validate using Pydantic
            valid_merchants = []
            for merchant in filtered_merchants:
                try:
                    Merchant(**merchant)
                    valid_merchants.append(merchant)
                except Exception as e:
                    self.logger.error(f"Invalid merchant data: {str(e)}")
                    continue

            self.logger.info(f"{len(valid_merchants)} merchants matched {filter_field}='{search_value}'")
            return valid_merchants
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to search merchants: {str(e)}")

    def get_merchant(self, merchant_id: str) -> Optional[dict]:
        try:
            merchant = self.data_access.get_merchant(merchant_id)
            if merchant and merchant.data:
                self.logger.info(f"Retrieved merchant: {merchant_id}")
                return merchant.data[0]
            self.logger.info(f"Merchant not found: {merchant_id}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting merchant {merchant_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve merchant: {str(e)}")

    def create_merchant(self, merchant: Merchant) -> dict:
        try:
            result = self.data_access.create_merchant(merchant)
            if result:
                self.logger.info(f"Created merchant: {merchant.merchant_id}")
                return result
            raise HTTPException(status_code=500, detail="Failed to create merchant")
        except Exception as e:
            self.logger.error(f"Create error {merchant.merchant_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create merchant: {str(e)}")

    def update_merchant(self, merchant_id: str, updates: dict) -> dict:
        try:
            result = self.data_access.update_merchant(merchant_id, updates)
            if result:
                self.logger.info(f"Updated merchant: {merchant_id}")
                return result
            raise HTTPException(status_code=404, detail="Merchant not found")
        except Exception as e:
            self.logger.error(f"Update error {merchant_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update merchant: {str(e)}")

    def delete_merchant(self, merchant_id: str) -> dict:
        try:
            result = self.data_access.delete_merchant(merchant_id)
            if result:
                self.logger.info(f"Deleted merchant: {merchant_id}")
                return result
            raise HTTPException(status_code=404, detail="Merchant not found")
        except Exception as e:
            self.logger.error(f"Delete error {merchant_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete merchant: {str(e)}")

    def get_all_merchant_ids(self) -> List[dict]:
        try:
            return self.data_access.get_all_merchant_ids()
        except Exception as e:
            self.logger.error(f"Failed to fetch merchants for config: {str(e)}")
            raise HTTPException(status_code=500, detail="Error fetching merchants")

    def save_settings(self, merchant_id: str, settings: dict) -> MerchantSettings:
        try:
            validated_settings = MerchantSettings(**settings)
            result = self.data_access.save_settings(merchant_id, validated_settings.dict())
            self.logger.info(f"Settings saved for merchant_id: {merchant_id}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to save settings for {merchant_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error saving settings")

    def get_settings(self, merchant_id: str) -> Optional[MerchantSettings]:
        try:
            result = self.data_access.get_settings(merchant_id)
            if result and result.data:
                item = result.data[0]
                self.logger.debug(f"Retrieved settings for {merchant_id}: {json.dumps(item, indent=2)}")
                return MerchantSettings(**item)
            self.logger.info(f"No settings found for {merchant_id}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get settings for {merchant_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving settings")
