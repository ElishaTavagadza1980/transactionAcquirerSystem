from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

class Terminal(BaseModel):
    terminal_id: str
    merchant_id: str
    terminal_serial_number: str
    terminal_type: Optional[str] = None
    terminal_model: Optional[str] = None
    terminal_brand: Optional[str] = None
    firmware_version: Optional[str] = None
    status: Optional[str] = "inactive"
    location_id: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    connectivity_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

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

