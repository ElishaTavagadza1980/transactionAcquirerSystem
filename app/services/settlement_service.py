import csv
import os
from datetime import date, datetime
from ftplib import FTP_TLS
import logging
from typing import Optional, Dict
from fastapi import Depends
from app.data_access.transaction_supabase import dataGetacquiredtransactions
from app.data_access.merchant_supabase import MerchantSupabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SettlementService:
    def __init__(self, merchant_supabase: MerchantSupabase = Depends(MerchantSupabase)):
        self.merchant_supabase = merchant_supabase
        self.ftp_configs = {
            "merchant_ftp": {
                "host": os.getenv("MERCHANT_FTP_HOST", "ftp.merchant.com"),
                "port": int(os.getenv("MERCHANT_FTP_PORT", 21)),
                "username": os.getenv("MERCHANT_FTP_USERNAME", "merchant_user"),
                "password": os.getenv("MERCHANT_FTP_PASSWORD", "merchant_pass")
            },
            "visa_ftp": {
                "host": os.getenv("VISA_FTP_HOST", "ftp.visa.com"),
                "port": int(os.getenv("VISA_FTP_PORT", 21)),
                "username": os.getenv("VISA_FTP_USERNAME", "visa_user"),
                "password": os.getenv("VISA_FTP_PASSWORD", "visa_pass")
            },
            "mastercard_ftp": {
                "host": os.getenv("MASTERCARD_FTP_HOST", "ftp.mastercard.com"),
                "port": int(os.getenv("MASTERCARD_FTP_PORT", 21)),
                "username": os.getenv("MASTERCARD_FTP_USERNAME", "mastercard_user"),
                "password": os.getenv("MASTERCARD_FTP_PASSWORD", "mastercard_pass")
            }
        }

    async def generate_settlement_report(self, start_date: date, end_date: date, merchant_id: Optional[str] = None) -> str:
        try:
            logger.debug(f"Generating settlement report for {start_date} to {end_date}, merchant_id: {merchant_id}")
            transactions = dataGetacquiredtransactions(
                filter_by="de_42_card_acceptor_id" if merchant_id else None,
                search_term=merchant_id
            )
           
            filtered_transactions = [
                t for t in transactions
                if start_date <= datetime.fromisoformat(t["created_at"].replace("Z", "+00:00")).date() <= end_date
                and t["message_type_indicator"] == "0110" and t["status"] == "APPROVED"
            ]
            
            file_path = f"settlement_report_{start_date}_to_{end_date}.csv"

            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                headers = [
                    "Transaction Date", "Card Number (PAN)", "Retrieval Reference No", "Merchant Name / ID",
                    "Acquirer ID / Bank", "Issuer ID / Bank", "Transaction Type", "Transaction Currency",
                    "Transaction Amount", "Settlement Currency", "Settlement Amount", "Interchange Fee",
                    "Scheme Fee", "Other Fees", "Total Deducted Fees", "Net Settlement Amount",
                    "Merchant Category Code (MCC)", "Authorization Code", "Dispute Status", "Batch ID"
                ]
                writer.writerow(headers)

                for transaction in filtered_transactions:
                    merchant_data = self.merchant_supabase.get_merchant(transaction.get("de_42_card_acceptor_id", ""))
                    merchant = merchant_data.data[0] if merchant_data and merchant_data.data else {}
                    card_scheme = self._get_card_scheme(transaction.get("de_2_pan", ""))
                    
                   
                    transaction_amount = int(transaction.get("de_4_amount_transaction", 0)) / 100
                    interchange_fee = transaction_amount * 0.02  
                    scheme_fee = transaction_amount * 0.01       
                    other_fees = 0.50                           
                    total_deducted_fees = interchange_fee + scheme_fee + other_fees
                    net_settlement_amount = transaction_amount - total_deducted_fees

                    writer.writerow([
                        transaction.get("created_at", "").split("T")[0],
                        f"******{transaction.get('de_2_pan', '')[-4:]}" if transaction.get("de_2_pan") else "N/A",
                        transaction.get("de_37_retrieval_reference_number", "N/A"),
                        merchant.get("name", transaction.get("de_42_card_acceptor_id", "N/A")),
                        transaction.get("de_32_acquiring_institution_id", "N/A"),
                        transaction.get("de_33_forwarding_institution_id", "N/A"),
                        self._get_transaction_type(transaction.get("de_3_processing_code", "")),
                        transaction.get("de_49_currency_code_transaction", "N/A"),
                        transaction_amount,
                        transaction.get("de_49_currency_code_transaction", "USD"), 
                        net_settlement_amount,
                        interchange_fee,
                        scheme_fee,
                        other_fees,
                        total_deducted_fees,
                        net_settlement_amount,
                        transaction.get("de_18_merchant_type", "N/A"),
                        transaction.get("de_38_authorization_id_response", "N/A"),
                        transaction.get("dispute_status", "None"),
                        transaction.get("batch_id", "BATCH" + transaction.get("de_11_system_trace_audit_number", "000000"))
                    ])

            logger.info(f"Settlement report generated at {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error generating settlement report: {str(e)}")
            raise

    async def send_settlement_report(self, start_date: date, end_date: date, merchant_id: Optional[str] = None) -> Dict:
        try:
            file_path = await self.generate_settlement_report(start_date, end_date, merchant_id)
            results = {}
         
            if merchant_id:
                merchant_data = self.merchant_supabase.get_merchant(merchant_id)
                if merchant_data and merchant_data.data:
                    results["merchant"] = self._send_to_ftp(file_path, "merchant_ftp", f"/settlements/{merchant_id}/")
           
            transactions = dataGetacquiredtransactions(
                filter_by="de_42_card_acceptor_id" if merchant_id else None,
                search_term=merchant_id
            )
            schemes = set(self._get_card_scheme(t.get("de_2_pan", "")) for t in transactions)
            for scheme in schemes:
                if scheme in ["Visa", "MasterCard"]:
                    results[scheme] = self._send_to_ftp(file_path, f"{scheme.lower()}_ftp", f"/settlements/")

           
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up local file: {file_path}")

            return results
        except Exception as e:
            logger.error(f"Error sending settlement report: {str(e)}")
            raise

    def _send_to_ftp(self, file_path: str, ftp_config_key: str, remote_path: str) -> bool:
        try:
            ftp_config = self.ftp_configs[ftp_config_key]
            with FTP_TLS(ftp_config["host"], ftp_config["username"], ftp_config["password"]) as ftps:
                ftps.set_pasv(True)
                ftps.prot_p()  
                ftps.cwd(remote_path)
                with open(file_path, 'rb') as file:
                    remote_filename = os.path.basename(file_path)
                    ftps.storbinary(f'STOR {remote_filename}', file)
                logger.info(f"Successfully sent {file_path} to {ftp_config['host']}:{remote_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to send file to FTP {ftp_config_key}: {str(e)}")
            return False

    def _get_card_scheme(self, pan: str) -> str:
        pan = pan.strip()
        if pan.startswith("4"):
            return "Visa"
        elif pan.startswith(("51", "52", "53", "54", "55")):
            return "MasterCard"
        return "Unknown"

    def _get_transaction_type(self, processing_code: str) -> str:
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
        return txn_type_map.get(processing_code[:2], "Unknown")