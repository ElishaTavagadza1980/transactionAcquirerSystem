from app.data_access.card_supabase import CardSupabase
from app.models.card_model import Card
import logging
from typing import List, Optional
from fastapi import HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CardService:
    def __init__(self):
        self.card_supabase = CardSupabase()
        self.logger = logger

    def create_card(self, card: Card) -> dict:
        try:
            result = self.card_supabase.dataCreateCard(card)
            self.logger.info(f"Created card: {card.card_number}")
            return result
        except Exception as e:
            self.logger.error(f"Create error {card.card_number}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create card: {str(e)}")

    def create_cards_bulk(self, cards: List[Card]) -> List[dict]:
        try:
            card_dicts = [card.dict(exclude_unset=True) for card in cards]
            result = self.card_supabase.dataCreateCardsBulk(card_dicts)
            self.logger.info(f"Inserted {len(result)} cards in bulk")
            return result
        except Exception as e:
            self.logger.error(f"Error inserting cards in bulk: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to insert cards: {str(e)}")

    def get_cards(self) -> List[dict]:
        try:
            cards = self.card_supabase.dataGetCards()
            self.logger.info(f"Service retrieved {len(cards)} cards")
            return cards
        except Exception as e:
            self.logger.error(f"Error retrieving cards: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve cards: {str(e)}")

    def get_card(self, card_number: str) -> Optional[dict]:
        try:
            card = self.card_supabase.dataGetCard(card_number)
            if card:
                self.logger.info(f"Retrieved card: {card_number}")
                return card
            self.logger.info(f"Card not found: {card_number}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting card {card_number}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve card: {str(e)}")

    def update_card(self, card_number: str, updates: dict) -> dict:
        try:
            result = self.card_supabase.dataUpdateCard(card_number, updates)
            if result:
                self.logger.info(f"Updated card: {card_number}")
                return result
            raise HTTPException(status_code=404, detail="Card not found")
        except Exception as e:
            self.logger.error(f"Update error {card_number}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update card: {str(e)}")

    def delete_card(self, card_number: str) -> dict:
        try:
            result = self.card_supabase.dataDeleteCard(card_number)
            if result:
                self.logger.info(f"Deleted card: {card_number}")
                return result
            raise HTTPException(status_code=404, detail="Card not found")
        except Exception as e:
            self.logger.error(f"Delete error {card_number}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete card: {str(e)}")