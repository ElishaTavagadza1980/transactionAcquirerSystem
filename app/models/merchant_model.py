from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from typing import Optional, List  # Add List to the imports


class Merchant(BaseModel):
    # Core Information
    merchant_id: str
    business_name: str
    legal_name: Optional[str] = None
    business_type: Optional[str] = None
    mcc: Optional[str] = None
    industry: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address_firstline: Optional[str] = None
    address_secondline: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    # KYC & Compliance
    kyc_status: str = "pending"
    kyc_type: Optional[str] = None
    id_proof_type: Optional[str] = None
    id_proof_number: Optional[str] = None
    business_registration_doc: Optional[str] = None
    gst_number: Optional[str] = None
    tin: Optional[str] = None
    aml_check_status: str = "pending"
    document_verification_status: Optional[str] = None
    
    # Bank & Settlement
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    settlement_currency: str = "INR"
    settlement_cycle: str = "T+1"
    
    # Risk & Underwriting
    risk_category: str = "medium"
    expected_monthly_volume: Optional[float] = None
    average_ticket_size: Optional[float] = None
    underwriter_comments: Optional[str] = None
    approval_status: str = "pending"
    approval_date: Optional[str] = None
    
    # Contract
    contract_signed: bool = False
    contract_signing_date: Optional[str] = None
    contract_url: Optional[str] = None
    
    # Technical Integration
    api_key: Optional[str] = None
    webhook_url: Optional[str] = None
    integration_type: Optional[str] = None
    pos_terminal_count: int = 0
    
    # Meta
    status: str = "Active"
    created_at: Optional[str]= None
    updated_at: Optional[str]= None

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_timestamp(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            # Try parsing both possible formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    datetime.strptime(value, fmt)
                    return value  # Return the original string if valid
                except ValueError:
                    continue
            raise ValueError("Timestamp must be in format 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DDTHH:MM:SS'")
        return value


class MerchantSettings(BaseModel):
    card_types: List[str]
    currencies: List[str]
    txn_types: List[str]
    interface_modes: List[str]
    
