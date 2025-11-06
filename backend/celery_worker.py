"""Celery worker configuration for async tasks"""
from celery import Celery
import os

# Create Celery app
celery_app = Celery(
    'invoice_processor',
    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # Soft limit at 4 minutes
    result_expires=3600,  # Results expire after 1 hour
)


@celery_app.task(bind=True, name='tasks.extract_document')
def extract_document(self, file_path, file_id):
    """
    Asynchronously extract data from document

    Args:
        file_path: Path to uploaded document
        file_id: File identifier

    Returns:
        dict: Extracted data with success status
    """
    import traceback
    from extractor import DocumentExtractor
    from ml_extractor import MLExtractor
    from currency_manager import CurrencyManager
    from duplicate_detector import DuplicateDetector
    from db import DatabaseAdapter

    # Update task state to show progress
    self.update_state(state='PROCESSING', meta={'status': 'Extracting text from document...'})

    try:
        # Initialize components
        extractor = DocumentExtractor()
        ml_extractor = MLExtractor('data')
        currency_manager = CurrencyManager('data')
        db = DatabaseAdapter('data')
        duplicate_detector = DuplicateDetector(db)

        # Extract data from document (original)
        self.update_state(state='PROCESSING', meta={'status': 'Running OCR...'})
        extracted_data = extractor.extract(file_path)

        # Enhance with ML if available
        if len(ml_extractor.training_data) > 0:
            self.update_state(state='PROCESSING', meta={'status': 'Applying ML enhancements...'})
            extracted_data = ml_extractor.enhance_extraction(
                extracted_data,
                extracted_data.get('raw_text', '')
            )

        # Detect and extract currency
        self.update_state(state='PROCESSING', meta={'status': 'Detecting currency...'})
        amount_with_currency = currency_manager.extract_amount_with_currency(
            extracted_data.get('raw_text', '')
        )

        if amount_with_currency[0] > 0:
            extracted_data['amount'] = amount_with_currency[0]
            extracted_data['currency'] = amount_with_currency[1]
            extracted_data['currency_confidence'] = amount_with_currency[2]
        else:
            extracted_data['currency'] = 'USD'
            extracted_data['currency_confidence'] = 50

        # Check for duplicates
        self.update_state(state='PROCESSING', meta={'status': 'Checking for duplicates...'})
        is_duplicate, duplicate_info, confidence = duplicate_detector.check_duplicate(
            file_path,
            extracted_data
        )

        extracted_data['is_potential_duplicate'] = is_duplicate
        if is_duplicate:
            extracted_data['duplicate_info'] = {
                'type': duplicate_info['type'],
                'confidence': confidence,
                'existing_expense': duplicate_info.get('expense', {}).get('id', 'Unknown')
            }

        # Calculate file hash for future duplicate detection
        file_hash = duplicate_detector.calculate_file_hash(file_path)
        extracted_data['file_hash'] = file_hash

        # Calculate image hash if possible
        image_hashes = duplicate_detector.calculate_image_hash(file_path)
        if image_hashes:
            extracted_data['image_hash_average'] = image_hashes.get('average')
            extracted_data['image_hash_perceptual'] = image_hashes.get('perceptual')
            extracted_data['image_hash_difference'] = image_hashes.get('difference')

        self.update_state(state='PROCESSING', meta={'status': 'Finalizing...'})

        return {
            'success': True,
            'data': extracted_data,
            'file_id': file_id
        }

    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()

        return {
            'success': False,
            'error': error_msg,
            'trace': error_trace,
            'file_id': file_id
        }


@celery_app.task(bind=True, name='tasks.process_document')
def process_document(self, expense_data, file_path, file_id, original_extraction=None):
    """
    Asynchronously process and store expense

    Args:
        expense_data: Expense information
        file_path: Path to document file
        file_id: File identifier
        original_extraction: Original extraction for ML training

    Returns:
        dict: Processing result
    """
    import traceback
    from datetime import datetime
    from file_manager import FileManager
    from ml_extractor import MLExtractor
    from currency_manager import CurrencyManager
    from budget_manager import BudgetManager
    from db import DatabaseAdapter

    self.update_state(state='PROCESSING', meta={'status': 'Processing document...'})

    try:
        # Initialize components
        file_manager = FileManager('processed')
        ml_extractor = MLExtractor('data')
        currency_manager = CurrencyManager('data')
        db = DatabaseAdapter('data')
        budget_manager = BudgetManager('data', db)

        # Learn from corrections if user modified extracted data
        if original_extraction:
            self.update_state(state='PROCESSING', meta={'status': 'Learning from corrections...'})
            raw_text = original_extraction.get('raw_text', '')
            ml_extractor.add_correction(raw_text, original_extraction, expense_data)

        # Handle currency conversion to base currency
        self.update_state(state='PROCESSING', meta={'status': 'Converting currency...'})
        currency = expense_data.get('currency', 'USD')
        amount = expense_data.get('amount', 0)

        if currency != 'USD':
            converted_amount = currency_manager.convert_to_base(amount, currency)
            expense_data['original_amount'] = amount
            expense_data['original_currency'] = currency
            expense_data['amount'] = converted_amount
            expense_data['converted_to_usd'] = True
        else:
            expense_data['currency'] = 'USD'

        # Generate new filename and organize file
        self.update_state(state='PROCESSING', meta={'status': 'Organizing file...'})
        new_filename = file_manager.generate_filename(expense_data)
        final_path = file_manager.organize_file(file_path, expense_data, new_filename)

        # Store expense record in database
        self.update_state(state='PROCESSING', meta={'status': 'Saving to database...'})
        expense_data['file_path'] = final_path
        expense_data['processed_date'] = datetime.now().isoformat()
        expense_id = db.add_expense(expense_data)

        # Check budgets after adding expense
        self.update_state(state='PROCESSING', meta={'status': 'Checking budgets...'})
        budget_check = budget_manager.check_all_budgets()

        result = {
            'success': True,
            'expense_id': expense_id,
            'final_path': final_path,
            'filename': new_filename,
            'file_id': file_id
        }

        # Include budget alerts if any were triggered
        if budget_check['new_alerts']:
            result['budget_alerts'] = budget_check['new_alerts']

        return result

    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()

        return {
            'success': False,
            'error': error_msg,
            'trace': error_trace,
            'file_id': file_id
        }


if __name__ == '__main__':
    celery_app.start()
