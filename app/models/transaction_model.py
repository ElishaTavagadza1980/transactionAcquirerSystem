from pydantic import BaseModel
from typing import Optional

class Transaction(BaseModel):
    message_type_indicator: str
    de_2_pan: str
    de_3_processing_code: str
    de_4_amount_transaction: str
    de_5_amount_settlement: Optional[int] = None
    de_7_transmission_date_time: str
    de_11_system_trace_audit_number: str
    de_12_local_transaction_time: str
    de_13_local_transaction_date: str
    de_14_expiration_date: str
    de_18_merchant_type: str
    de_19_acquiring_institution_country_code: str
    de_22_pos_entry_mode: str
    de_23_pan_sequence_number: Optional[str] = None
    de_25_pos_condition_code: str
    de_32_acquiring_institution_id: str
    de_33_forwarding_institution_id: Optional[str] = None
    de_35_track2_data: Optional[str] = None
    de_37_retrieval_reference_number: str
    de_38_authorization_id_response: Optional[str] = None
    de_39_response_code: Optional[str] = None
    de_41_card_acceptor_terminal_id: str
    de_42_card_acceptor_id: str
    de_43_card_acceptor_name_location: str
    de_49_currency_code_transaction: str
    de_52_pin_data: Optional[str] = None
    de_55_icc_data: Optional[str] = None
    status: Optional[str] = None
    created_at: str = None
    status_reason: Optional[str] = None