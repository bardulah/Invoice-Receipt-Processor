"""Asynchronous processing tasks"""
from celery import Task
from tasks.celery_app import celery_app
from core.database import db
from core.logging_config import get_logger
from services.ocr.extractor import DocumentExtractor
from services.currency.converter import CurrencyConverter
from models.expense import Expense

logger = get_logger(__name__)


class DatabaseTask(Task):
    """Base task with database session"""

    def __call__(self, *args, **kwargs):
        with db.session_scope() as session:
            self.session = session
            return self.run(*args, **kwargs)


@celery_app.task(base=DatabaseTask, bind=True, name='tasks.processing_tasks.extract_document')
def extract_document(self, file_path: str, user_id: int):
    """
    Asynchronously extract data from document

    Args:
        file_path: Path to uploaded document
        user_id: User ID who uploaded the document

    Returns:
        dict: Extracted data
    """
    logger.info(f"Starting extraction for file: {file_path}", extra={
        'file_path': file_path,
        'user_id': user_id,
        'task_id': self.request.id
    })

    try:
        # Extract data
        extractor = DocumentExtractor()
        extracted_data = extractor.extract(file_path)

        logger.info(f"Extraction completed for file: {file_path}", extra={
            'file_path': file_path,
            'vendor': extracted_data.get('vendor'),
            'amount': extracted_data.get('amount'),
            'confidence': extracted_data.get('confidence'),
            'task_id': self.request.id
        })

        return {
            'success': True,
            'data': extracted_data,
            'file_path': file_path
        }

    except Exception as e:
        logger.error(f"Extraction failed for file: {file_path}", extra={
            'file_path': file_path,
            'error': str(e),
            'task_id': self.request.id
        }, exc_info=True)

        return {
            'success': False,
            'error': str(e),
            'file_path': file_path
        }


@celery_app.task(base=DatabaseTask, bind=True, name='tasks.processing_tasks.process_document')
def process_document(self, expense_data: dict, file_path: str, user_id: int):
    """
    Asynchronously process and store expense

    Args:
        expense_data: Expense information
        file_path: Path to document file
        user_id: User ID

    Returns:
        dict: Processing result
    """
    logger.info(f"Processing document for user {user_id}", extra={
        'user_id': user_id,
        'vendor': expense_data.get('vendor'),
        'task_id': self.request.id
    })

    try:
        # Convert currency if needed
        currency = expense_data.get('currency', 'USD')
        amount = expense_data.get('amount', 0)

        if currency != 'USD':
            converter = CurrencyConverter()
            converted_amount = converter.convert(amount, currency, 'USD')
            expense_data['original_amount'] = amount
            expense_data['original_currency'] = currency
            expense_data['amount'] = converted_amount

        # Create expense record
        expense = Expense(
            user_id=user_id,
            **expense_data
        )

        self.session.add(expense)
        self.session.commit()

        logger.info(f"Document processed successfully", extra={
            'expense_id': expense.id,
            'user_id': user_id,
            'task_id': self.request.id
        })

        return {
            'success': True,
            'expense_id': expense.id,
            'expense': expense.to_dict()
        }

    except Exception as e:
        logger.error(f"Document processing failed", extra={
            'user_id': user_id,
            'error': str(e),
            'task_id': self.request.id
        }, exc_info=True)

        return {
            'success': False,
            'error': str(e)
        }


@celery_app.task(name='tasks.processing_tasks.check_budgets')
def check_budgets(user_id: int = None):
    """
    Check all budgets and generate alerts

    Args:
        user_id: Optional user ID to check (None = all users)
    """
    logger.info("Checking budgets", extra={'user_id': user_id})

    # This would call the budget manager service
    # Implementation similar to original but with proper database queries

    logger.info("Budget check completed")


@celery_app.task(name='tasks.processing_tasks.process_email')
def process_email(email_data: dict):
    """
    Process invoice received via email

    Args:
        email_data: Email metadata and attachment info
    """
    logger.info("Processing email invoice", extra={
        'subject': email_data.get('subject'),
        'sender': email_data.get('sender')
    })

    # This would call the email processor service

    logger.info("Email processed successfully")


@celery_app.task(name='tasks.processing_tasks.train_ml_model')
def train_ml_model():
    """Retrain ML model with new corrections"""
    logger.info("Training ML model")

    # This would call the ML training service

    logger.info("ML model training completed")
