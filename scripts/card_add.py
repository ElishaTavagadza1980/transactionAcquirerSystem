import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apscheduler.schedulers.blocking import BlockingScheduler
from app.services.card_service import CardService
from app.models.card_model import Card
import csv
import logging
from datetime import datetime, timezone
from typing import List

# Configure logging to file with timestamp
log_file = f'card_batch_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CardBatchProcessor:
    def __init__(self):
        try:
            logger.debug("Initializing CardBatchProcessor")
            self.card_service = CardService()
            self.batch_dir = os.getenv("BATCH_DIR", "./batches")
            logger.debug(f"Batch directory set to: {self.batch_dir}")
            os.makedirs(self.batch_dir, exist_ok=True)
            logger.info("Batch directory created or verified")
        except Exception as e:
            logger.error(f"Failed to initialize CardBatchProcessor: {str(e)}")
            raise

    def process_batch(self):
        logger.info("Starting batch processing")
        try:
            if not os.path.exists(self.batch_dir):
                logger.error(f"Batch directory {self.batch_dir} does not exist")
                return
            for filename in os.listdir(self.batch_dir):
                if not filename.endswith('.csv'):
                    logger.info(f"Skipping non-CSV file: {filename}")
                    continue
                file_path = os.path.join(self.batch_dir, filename)
                cards = []
                received_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + "Z"
                batch_size = 1000
                logger.debug(f"Processing file: {file_path}")
                with open(file_path, 'r') as file:
                    csv_reader = csv.DictReader(file)
                    required_fields = ['card_number', 'card_type', 'expiry_date', 'card_holder_name', 'card_status']
                    if not all(field in csv_reader.fieldnames for field in required_fields):
                        logger.error(f"Missing required fields in {filename}")
                        continue
                    for i, row in enumerate(csv_reader):
                        try:
                            card_data = {
                                "card_number": row['card_number'],
                                "card_type": row['card_type'],
                                "expiry_date": row['expiry_date'],
                                "card_holder_name": row['card_holder_name'],
                                "card_status": row['card_status'],
                                "card_pin": row.get('card_pin'),
                                "balance": float(row.get('balance', 0.0)),
                                "cvv1": row.get('cvv1'),
                                "cvv2": row.get('cvv2'),
                                "icvv": row.get('icvv'),
                                "issue_date": row.get('issue_date'),
                                "service_code": row.get('service_code'),
                                "currency_code": row.get('currency_code'),
                                "received_at": received_at,
                                "batch_name": filename
                            }
                            card = Card(**card_data)
                            cards.append(card)
                            if len(cards) >= batch_size:
                                self.card_service.create_cards_bulk(cards)
                                logger.info(f"Processed batch of {len(cards)} cards from {filename}")
                                cards = []
                        except Exception as e:
                            logger.error(f"Invalid card data in {filename}, row {i+2}: {row}, error: {str(e)}")
                            continue
                    if cards:
                        self.card_service.create_cards_bulk(cards)
                        logger.info(f"Processed final batch of {len(cards)} cards from {filename}")
                os.rename(file_path, os.path.join(self.batch_dir, f"processed_{filename}"))
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")

def main():
    logger.info("Starting card batch processor application")
    try:
        scheduler = BlockingScheduler()
        processor = CardBatchProcessor()
        scheduler.add_job(processor.process_batch, 'interval', hours=2)
        logger.info("Scheduler initialized with 2-hour interval")
        scheduler.start()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()