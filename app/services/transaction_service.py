import logging
from datetime import datetime, timezone
import random
import requests
from fastapi import Depends, HTTPException
from app.data_access.transaction_supabase import (
    dataAddTransaction,
    dataGetacquiredtransactions,
    dataGetacquiredtransactionsByRetrieval,
)
from app.data_access.card_supabase import CardSupabase
from app.data_access.merchant_supabase import MerchantSupabase
from app.services.schemerouting_service import SchemeRoutingService
from app.models.transaction_model import Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self, 
                 card_supabase: CardSupabase = Depends(CardSupabase), 
                 merchant_supabase: MerchantSupabase = Depends(MerchantSupabase),
                 scheme_routing_service: SchemeRoutingService = Depends(SchemeRoutingService)):
        self.card_supabase = card_supabase
        self.merchant_supabase = merchant_supabase
        self.scheme_routing_service = scheme_routing_service
        self.scheme_endpoints = {
            "Visa": "https://api.visa.com/transactions",
            "MasterCard": "https://api.mastercard.com/transactions"
        }

    def _validate_merchant_settings(self, transaction: Transaction) -> tuple[bool, str]:
        """Validate merchant existence and settings for the transaction."""
        merchant_id = transaction.de_42_card_acceptor_id
        
        # Store the 0100 request before validation
        if transaction.message_type_indicator == "0100":
            request_transaction = transaction.dict(exclude_unset=True)
            request_transaction['message_type_indicator'] = '0100'
            request_transaction['created_date'] = request_transaction.get('created_date', datetime.now(timezone.utc).isoformat() + 'Z')
            request_transaction['de_42_card_acceptor_id'] = request_transaction.get('de_42_card_acceptor_id', None)
            request_transaction['de_43_card_acceptor_name_location'] = request_transaction.get('de_43_card_acceptor_name_location', None)
            dataAddTransaction(Transaction(**request_transaction))

        # Check if merchant exists
        merchant_response = self.merchant_supabase.get_merchant(merchant_id)
        merchant_data = getattr(merchant_response, 'data', None)

        if not merchant_data or len(merchant_data) == 0:
            logger.warning(f"Merchant not found: {merchant_id}")
            transaction.de_39_response_code = "14"
            transaction.status = "DECLINED"
            transaction.status_reason = "Invalid card acceptor"
            response_transaction = transaction.dict(exclude_unset=True)
            response_transaction['message_type_indicator'] = '0110'
            response_transaction['created_date'] = response_transaction.get('created_date', datetime.now(timezone.utc).isoformat() + 'Z')
            response_transaction['de_11_system_trace_audit_number'] = response_transaction.get('de_11_system_trace_audit_number', None)
            response_transaction['de_42_card_acceptor_id'] = response_transaction.get('de_42_card_acceptor_id', None)
            response_transaction['de_43_card_acceptor_name_location'] = response_transaction.get('de_43_card_acceptor_name_location', None)
            dataAddTransaction(Transaction(**response_transaction))
            return False, "14"

        # Check if merchant is active
        if merchant_data[0]["status"] != "Active":
            logger.warning(f"Merchant is not active: {merchant_id}")
            transaction.de_39_response_code = "58"
            transaction.status = "DECLINED"
            transaction.status_reason = "Merchant is not active"
            response_transaction = transaction.dict(exclude_unset=True)
            response_transaction['message_type_indicator'] = '0110'
            response_transaction['created_date'] = response_transaction.get('created_date', datetime.now(timezone.utc).isoformat() + 'Z')
            response_transaction['de_11_system_trace_audit_number'] = response_transaction.get('de_11_system_trace_audit_number', None)
            response_transaction['de_42_card_acceptor_id'] = response_transaction.get('de_42_card_acceptor_id', None)
            response_transaction['de_43_card_acceptor_name_location'] = response_transaction.get('de_43_card_acceptor_name_location', None)
            dataAddTransaction(Transaction(**response_transaction))
            return False, "58"

        # Get merchant settings
        settings_response = self.merchant_supabase.get_settings(merchant_id)
        settings_data = getattr(settings_response, 'data', None)

        if not settings_data or len(settings_data) == 0:
            logger.warning(f"No settings found for merchant: {merchant_id}")
            transaction.de_39_response_code = "96"
            transaction.status = "DECLINED"
            transaction.status_reason = "System malfunction (no settings configured)"
            response_transaction = transaction.dict(exclude_unset=True)
            response_transaction['message_type_indicator'] = '0110'
            response_transaction['created_date'] = response_transaction.get('created_date', datetime.now(timezone.utc).isoformat() + 'Z')
            response_transaction['de_11_system_trace_audit_number'] = response_transaction.get('de_11_system_trace_audit_number', None)
            response_transaction['de_42_card_acceptor_id'] = response_transaction.get('de_42_card_acceptor_id', None)
            response_transaction['de_43_card_acceptor_name_location'] = response_transaction.get('de_43_card_acceptor_name_location', None)
            dataAddTransaction(Transaction(**response_transaction))
            return False, "96"

        settings = settings_data[0]

        # Validate card type
        card_scheme = self._get_card_scheme(transaction.de_2_pan)
        if card_scheme not in settings["card_types"]:
            logger.warning(f"Card type {card_scheme} not supported by merchant: {merchant_id}")
            transaction.de_39_response_code = "57"
            transaction.status = "DECLINED"
            transaction.status_reason = "Transaction not permitted on card"
            response_transaction = transaction.dict(exclude_unset=True)
            response_transaction['message_type_indicator'] = '0110'
            response_transaction['created_date'] = response_transaction.get('created_date', datetime.now(timezone.utc).isoformat() + 'Z')
            response_transaction['de_11_system_trace_audit_number'] = response_transaction.get('de_11_system_trace_audit_number', None)
            response_transaction['de_42_card_acceptor_id'] = response_transaction.get('de_42_card_acceptor_id', None)
            response_transaction['de_43_card_acceptor_name_location'] = response_transaction.get('de_43_card_acceptor_name_location', None)
            dataAddTransaction(Transaction(**response_transaction))
            return False, "57"

        # Validate currency
        if "All" not in settings["currencies"] and transaction.de_49_currency_code_transaction not in settings["currencies"]:
            logger.warning(f"Currency {transaction.de_49_currency_code_transaction} not supported by merchant: {merchant_id}")
            transaction.de_39_response_code = "57"
            transaction.status = "DECLINED"
            transaction.status_reason = "Transaction not permitted on card"
            response_transaction = transaction.dict(exclude_unset=True)
            response_transaction['message_type_indicator'] = '0110'
            response_transaction['created_date'] = response_transaction.get('created_date', datetime.now(timezone.utc).isoformat() + 'Z')
            response_transaction['de_11_system_trace_audit_number'] = response_transaction.get('de_11_system_trace_audit_number', None)
            response_transaction['de_42_card_acceptor_id'] = response_transaction.get('de_42_card_acceptor_id', None)
            response_transaction['de_43_card_acceptor_name_location'] = response_transaction.get('de_43_card_acceptor_name_location', None)
            dataAddTransaction(Transaction(**response_transaction))
            return False, "57"

        # Validate transaction type
        processing_code = transaction.de_3_processing_code[:2]
        txn_type_map = {
            "00": "Purchase",
            "01": "Cash Withdrawal",
            "09": "Purchase with Cashback",
            "20": "Refund",
            "28": "Pre-Authorization",
            "29": "Completion",
            "22": "Void",
            "17": "Balance Inquiry",
            "40": "Funds Transfer",
            "31": "Mini Statement",
            "50": "Cash Deposit",
            "51": "Cheque Deposit",
            "91": "PIN Change",
            "30": "Bill Payments",
            "39": "Mobile Recharge"
        }
        txn_type = txn_type_map.get(processing_code, "Unknown")
        if txn_type == "Unknown" or txn_type not in settings["txn_types"]:
            logger.warning(f"Transaction type {txn_type} not supported by merchant: {merchant_id}")
            transaction.de_39_response_code = "57"
            transaction.status = "DECLINED"
            transaction.status_reason = "Transaction not permitted on card"
            response_transaction = transaction.dict(exclude_unset=True)
            response_transaction['message_type_indicator'] = '0110'
            response_transaction['created_date'] = response_transaction.get('created_date', datetime.now(timezone.utc).isoformat() + 'Z')
            response_transaction['de_11_system_trace_audit_number'] = response_transaction.get('de_11_system_trace_audit_number', None)
            response_transaction['de_42_card_acceptor_id'] = response_transaction.get('de_42_card_acceptor_id', None)
            response_transaction['de_43_card_acceptor_name_location'] = response_transaction.get('de_43_card_acceptor_name_location', None)
            dataAddTransaction(Transaction(**response_transaction))
            return False, "57"

        # Validate interface mode
        pos_entry_mode = transaction.de_22_pos_entry_mode[:2]
        interface_mode_map = {
            "01": "Manual",
            "05": "POS Contact",
            "07": "POS Contactless",
            "80": "Ecommerce",
            "81": "Ecommerce",
            "91": "Ecommerce"
        }
        interface_mode = interface_mode_map.get(pos_entry_mode, "Unknown")
        if interface_mode == "Unknown" or interface_mode not in settings["interface_modes"]:
            logger.warning(f"Interface mode {interface_mode} not supported by merchant: {merchant_id}")
            transaction.de_39_response_code = "58"
            transaction.status = "DECLINED"
            transaction.status_reason = "Interface mode not supported by merchant"
            response_transaction = transaction.dict(exclude_unset=True)
            response_transaction['message_type_indicator'] = '0110'
            response_transaction['created_date'] = response_transaction.get('created_date', datetime.now(timezone.utc).isoformat() + 'Z')
            response_transaction['de_11_system_trace_audit_number'] = response_transaction.get('de_11_system_trace_audit_number', None)
            response_transaction['de_42_card_acceptor_id'] = response_transaction.get('de_42_card_acceptor_id', None)
            response_transaction['de_43_card_acceptor_name_location'] = response_transaction.get('de_43_card_acceptor_name_location', None)
            dataAddTransaction(Transaction(**response_transaction))
            return False, "58"

        return True, "00"

    def _validate_scheme_routing(self, card_scheme: str) -> str:
        """Check scheme routing configuration and return routing type."""
        try:
            scheme_routing = self.scheme_routing_service.get_scheme_routing(card_scheme)
            return scheme_routing.routing
        except HTTPException as e:
            if e.status_code == 404:
                logger.warning(f"No routing configuration found for scheme: {card_scheme}. Defaulting to internal processing.")
                return "internal"
            raise

    def process_transaction(self, transaction: Transaction):
        logger.debug(f"Processing transaction: {transaction.dict()}")
        
        # Validate merchant settings
        is_valid, response_code = self._validate_merchant_settings(transaction)
        if not is_valid:
            return transaction

        # Set response MTI to 0110 for 0100 requests
        if transaction.message_type_indicator == "0100":
            transaction.message_type_indicator = "0110"

        scheme = self._get_card_scheme(transaction.de_2_pan.strip())
        
        # Check scheme routing configuration
        routing = self._validate_scheme_routing(scheme)
        
        # Process based on routing configuration
        if routing == "internal":
            return self._stand_in_processing(transaction)
        
        # External routing: send to scheme and forward response
        try:
            # Ensure the transaction is sent as 0100 to the scheme
            transaction_to_send = transaction.dict(exclude_unset=True)
            transaction_to_send['message_type_indicator'] = '0100'
            
            response = requests.post(
                self.scheme_endpoints[scheme],
                json=transaction_to_send,
                timeout=10
            )
            scheme_response = response.json()
            
            # Update transaction with scheme response
            transaction.de_39_response_code = scheme_response.get("response_code", "05")
            transaction.status = scheme_response.get("status", "DECLINED")
            transaction.de_38_authorization_id_response = scheme_response.get("authorization_id", str(random.randint(100000, 999999)))
            transaction.message_type_indicator = "0110"
            
            # store the response transaction
            response_transaction = transaction.dict(exclude_unset=True)
            response_transaction['created_date'] = response_transaction.get('created_date', datetime.now(timezone.utc).isoformat() + 'Z')
            response_transaction['de_11_system_trace_audit_number'] = response_transaction.get('de_11_system_trace_audit_number', None)
            response_transaction['de_42_card_acceptor_id'] = response_transaction.get('de_42_card_acceptor_id', None)
            response_transaction['de_43_card_acceptor_name_location'] = response_transaction.get('de_43_card_acceptor_name_location', None)
            dataAddTransaction(Transaction(**response_transaction))
            
            logger.info(f"External scheme processing completed for {scheme}: Response Code {transaction.de_39_response_code}")
            return transaction

        except Exception as e:
            logger.warning(f"Scheme processing failed for {scheme}: {str(e)}. Falling back to stand-in processing.")
            return self._stand_in_processing(transaction)

    def _stand_in_processing(self, transaction: Transaction):
        logger.debug(f"Performing stand-in processing for transaction: {transaction.de_11_system_trace_audit_number}")
        if transaction.message_type_indicator == "0100":
            transaction.message_type_indicator = "0110"

        # card number
        card_number = transaction.de_2_pan.strip()
        logger.debug(f"Input PAN for card lookup: '{card_number}'")
        card_response = self.card_supabase.get_card_by_number(card_number)
        card_data = card_response.get('data', [])

        if not card_data or len(card_data) == 0:
            logger.warning(f"No card found for PAN: {card_number}")
            transaction.de_39_response_code = "55"
            transaction.status = "DECLINED"
            transaction.status_reason = "No card found for PAN"
        else:
            card_info = card_data[0] if isinstance(card_data, list) and card_data else card_data
            logger.debug(f"Card info retrieved: {card_info}")
            if card_info["card_status"] != "active":
                logger.warning(f"Card is not active: {card_number}")
                transaction.de_39_response_code = "54"
                transaction.status = "DECLINED"
                transaction.status_reason = "Card is not active"
            elif card_info["balance"] < (int(transaction.de_4_amount_transaction) / 100):
                logger.warning(f"Insufficient funds for PAN: {card_number}")
                transaction.de_39_response_code = "51"
                transaction.status = "DECLINED"
                transaction.status_reason = "Insufficient funds"
            elif transaction.de_49_currency_code_transaction != card_info["currency_code"]:
                logger.warning(f"Currency mismatch for PAN: {card_number}")
                transaction.de_39_response_code = "57"
                transaction.status = "DECLINED"
                transaction.status_reason = "Currency mismatch"
            elif transaction.de_22_pos_entry_mode.startswith("05") and transaction.de_55_icc_data and card_info["icvv"] != transaction.de_55_icc_data[-3:]:
                logger.warning(f"Invalid iCVV for chip transaction: {card_number}")
                transaction.de_39_response_code = "57"
                transaction.status = "DECLINED"
                transaction.status_reason = "Invalid iCVV for chip transaction"
            elif transaction.de_22_pos_entry_mode.startswith("90") and transaction.de_35_track2_data and card_info["cvv1"] != transaction.de_35_track2_data[-3:]:
                logger.warning(f"Invalid CVV1 for magnetic stripe transaction: {card_number}")
                transaction.de_39_response_code = "57"
                transaction.status = "DECLINED"
                transaction.status_reason = "Invalid CVV1"
            elif transaction.de_22_pos_entry_mode.startswith("02") and not self._validate_cvv2(transaction, card_info["cvv2"]):
                logger.warning(f"Invalid CVV2 for transaction: {card_number}")
                transaction.de_39_response_code = "57"
                transaction.status = "DECLINED"
                transaction.status_reason = "Invalid CVV2"
            elif not self._validate_service_code(transaction, card_info["service_code"]):
                logger.warning(f"Invalid service code for transaction: {card_number}")
                transaction.de_39_response_code = "57"
                transaction.status = "DECLINED"
                transaction.status_reason = "Invalid service code for transaction"
            elif transaction.de_52_pin_data and not self._validate_pin(transaction.de_52_pin_data, card_info["card_pin"]):
                logger.warning(f"Invalid PIN for transaction: {card_number}")
                transaction.de_39_response_code = "55"
                transaction.status = "DECLINED"
                transaction.status_reason = "Invalid PIN for transaction"
            else:
                transaction.de_39_response_code = "00"
                transaction.status = "APPROVED"
                amount = int(transaction.de_4_amount_transaction) / 100
                self.card_supabase.update_balance(card_number, amount)

        transaction.de_38_authorization_id_response = str(random.randint(100000, 999999))
        response_transaction = transaction.dict(exclude_unset=True)
        response_transaction['message_type_indicator'] = '0110'
        response_transaction['de_11_system_trace_audit_number'] = response_transaction.get('de_11_system_trace_audit_number', None)
        response_transaction['created_date'] = response_transaction.get('created_date', datetime.now(timezone.utc).isoformat() + 'Z')
        response_transaction['de_42_card_acceptor_id'] = response_transaction.get('de_42_card_acceptor_id', None)
        response_transaction['de_43_card_acceptor_name_location'] = response_transaction.get('de_43_card_acceptor_name_location', None)
        dataAddTransaction(Transaction(**response_transaction))
        logger.info(f"Stand-in processing completed: {transaction.status} (Response Code: {transaction.de_39_response_code})")
        return transaction

    def _get_card_scheme(self, pan: str) -> str:
        pan = pan.strip()
        if pan.startswith("4"):
            return "Visa"
        elif pan.startswith(("51", "52", "53", "54", "55")):
            return "MasterCard"
        elif pan.startswith("34") or pan.startswith("37"):
            return "Amex"
        elif pan.startswith("6011") or pan.startswith(("644", "645", "646", "647", "648", "649")) or pan.startswith("65"):
            return "Discover"
        elif pan.startswith("35"):
            return "JCB"
        elif pan.startswith(("36", "38", "39")):
            return "DinersClub"
        elif pan.startswith("62"):
            return "UnionPay"
        return "Unknown"

    def _should_stand_in(self, transaction: Transaction) -> bool:
        return transaction.de_22_pos_entry_mode.startswith("01")

    def _validate_cvv2(self, transaction: Transaction, cvv2: str) -> bool:
        provided_cvv2 = getattr(transaction, 'cvv2', None)
        return provided_cvv2 == cvv2 if provided_cvv2 else True

    def _validate_service_code(self, transaction: Transaction, service_code: str) -> bool:
        if not service_code:
            return False
        if len(service_code) > 0 and transaction.de_3_processing_code.startswith("00") and service_code[0] in ("1", "6"):
            return True
        return False

    def _validate_pin(self, pin_data: str, card_pin: str) -> bool:
        return pin_data == card_pin

    def get_transactions(self, filter_by: str = None, search_term: str = None):
        return dataGetacquiredtransactions(filter_by, search_term)

    def get_transaction_by_retrieval(self, retrieval_ref: str):
        return dataGetacquiredtransactionsByRetrieval(retrieval_ref)
    
    def get_transaction_statistics(self):
        transactions = self.get_transactions()
        
        total_amount = 0.0
        active_count = 0
        blocked_count = 0
        currency = "USD"  

        for txn in transactions:
            if txn.status == "APPROVED":
                total_amount += int(txn.de_4_amount_transaction) / 100.0
                active_count += 1
            else:
                blocked_count += 1

        return {
            "total_transactions": len(transactions),
            "total_amount": total_amount,
            "active_count": active_count,
            "blocked_count": blocked_count,
            "currency": currency
        }
