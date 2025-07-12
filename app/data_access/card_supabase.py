from supabase import create_client, Client
from app.models.card_model import Card
from starlette.config import Config
from typing import List, Optional
from fastapi import HTTPException
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CardSupabase:
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

    def dataCreateCard(self, card: Card) -> dict:
        try:
            card_data = card.dict(exclude_unset=True)
            response = self.supabase.table("cards").insert(card_data).execute()
            logger.info(f"Created card with card_number: {card.card_number}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to create card {card.card_number}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create card: {str(e)}")

    def dataCreateCardsBulk(self, cards: List[dict]) -> List[dict]:
        try:
            # Truncate the table before inserting new batch
            self.supabase.table("cards").delete().neq("card_number", "0").execute()  # Workaround to truncate
            response = self.supabase.table("cards").insert(cards).execute()
            logger.info(f"Inserted {len(response.data)} cards in bulk")
            return response.data
        except Exception as e:
            logger.error(f"Error inserting cards in bulk: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to insert cards: {str(e)}")

    def dataGetCards(self) -> List[dict]:
        try:
            response = self.supabase.table("cards").select("*").order("received_at", desc=True).execute()
            logger.info(f"Retrieved {len(response.data)} cards")
            logger.debug(f"Raw Supabase response: {json.dumps(response.data, indent=2)}")
            cards = []
            for item in response.data:
                try:
                    card = Card(**item)
                    cards.append(card.dict())
                except Exception as e:
                    logger.error(f"Failed to parse card data {item.get('card_number', 'unknown')}: {str(e)}")
                    continue
            return cards
        except Exception as e:
            logger.error(f"Failed to retrieve cards: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve cards: {str(e)}")

    def dataGetCard(self, card_number: str) -> Optional[dict]:
        try:
            response = self.supabase.table("cards").select("*").eq("card_number", card_number).execute()
            logger.debug(f"Raw Supabase response for card_number {card_number}: {json.dumps(response.data, indent=2)}")
            if response.data:
                logger.info(f"Retrieved card with card_number: {card_number}")
                return Card(**response.data[0]).dict()
            logger.info(f"Card not found with card_number: {card_number}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve card {card_number}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve card: {str(e)}")

    def dataUpdateCard(self, card_number: str, updates: dict) -> dict:
        try:
            response = self.supabase.table("cards").update(updates).eq("card_number", card_number).execute()
            if not response.data:
                logger.info(f"Card not found with card_number: {card_number}")
                raise HTTPException(status_code=404, detail="Card not found")
            logger.info(f"Updated card with card_number: {card_number}")
            return response.data[0]
        except HTTPException as e:
            raise
        except Exception as e:
            logger.error(f"Failed to update card {card_number}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update card: {str(e)}")

    def dataDeleteCard(self, card_number: str) -> dict:
        try:
            response = self.supabase.table("cards").delete().eq("card_number", card_number).execute()
            if not response.data:
                logger.info(f"Card not found with card_number: {card_number}")
                raise HTTPException(status_code=404, detail="Card not found")
            logger.info(f"Deleted card with card_number: {card_number}")
            return response.data[0]
        except HTTPException as e:
            raise
        except Exception as e:
            logger.error(f"Failed to delete card {card_number}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete card: {str(e)}")

    def get_card_by_number(self, card_number: str) -> dict:
        try:
            response = self.supabase.table("cards").select("*").eq("card_number", card_number).execute()
            logger.debug(f"Raw Supabase response for card_number {card_number}: {json.dumps(response.data, indent=2)}")
            return {"data": [Card(**response.data[0]).dict()] if response.data else []}
        except Exception as e:
            logger.error(f"Failed to retrieve card by number {card_number}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve card: {str(e)}")

    def update_balance(self, card_number: str, amount: float) -> None:
        try:
            card = self.dataGetCard(card_number)
            if not card:
                logger.info(f"Card not found for balance update: {card_number}")
                raise HTTPException(status_code=404, detail="Card not found")
            new_balance = card.get("balance", 0.0) - amount
            if new_balance < 0:
                logger.warning(f"Insufficient balance for card {card_number}: {card.get('balance')} < {amount}")
                raise HTTPException(status_code=400, detail="Insufficient balance")
            updates = {"balance": new_balance}
            self.dataUpdateCard(card_number, updates)
            logger.info(f"Updated balance for card {card_number}: {new_balance}")
        except HTTPException as e:
            raise
        except Exception as e:
            logger.error(f"Failed to update balance for card {card_number}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update balance: {str(e)}")