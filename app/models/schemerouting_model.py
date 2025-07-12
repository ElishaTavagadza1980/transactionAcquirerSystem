from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

class SchemeRouting(BaseModel):
    scheme: str
    routing: str
    created_at: Optional[str]= None
    updated_at: Optional[str]= None

    @field_validator("scheme")
    def validate_scheme(cls, v):
        valid_schemes = {"Visa", "MasterCard", "Amex", "Diners", "UnionPay", "JCB"}
        if v not in valid_schemes:
            raise ValueError(f"Scheme must be one of {valid_schemes}")
        return v

    @field_validator("routing")
    def validate_routing(cls, v):
        if v not in {"external", "internal"}:
            raise ValueError("Routing must be 'external' or 'internal'")
        return v
    
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
