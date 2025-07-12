from pydantic import BaseModel, Field
from typing import Optional

class Card(BaseModel):
    card_number: str = Field(..., pattern=r'^\d{12,19}$')
    card_type: str
    expiry_date: str = Field(..., pattern=r'^[0-1][0-9]/[0-9]{2}$')
    card_holder_name: str
    card_status: str = Field(..., pattern=r'^(active|inactive|blocked)$')
    card_pin: Optional[str] = Field(None, pattern=r'^\d{4,16}$')
    balance: float = 0.0
    cvv1: Optional[str] = Field(None, pattern=r'^\d{3}$')
    cvv2: Optional[str] = Field(None, pattern=r'^\d{3}$')
    icvv: Optional[str] = Field(None, pattern=r'^\d{3}$')
    issue_date: Optional[str] = Field(None, pattern=r'^[0-1][0-9]/[0-9]{2}$')
    service_code: Optional[str] = Field(None, pattern=r'^\d{3}$')
    currency_code: Optional[str] = Field(None, pattern=r'^\d{3}$')
    received_at: Optional[str] = None
    batch_name: Optional[str] = None