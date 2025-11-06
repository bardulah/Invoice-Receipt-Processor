"""Database adapter using SQLAlchemy with SQLite"""
import os
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class Expense(Base):
    """Expense database model"""
    __tablename__ = 'expenses'

    id = Column(String(50), primary_key=True)
    date = Column(Date, nullable=False, index=True)
    vendor = Column(String(255), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    invoice_number = Column(String(100))
    tags = Column(Text)  # JSON string
    file_path = Column(String(500))
    processed_date = Column(DateTime, nullable=False)
    notes = Column(Text)

    # Multi-currency support
    currency = Column(String(3), default='USD')
    original_amount = Column(Float)
    original_currency = Column(String(3))
    converted_to_usd = Column(Boolean, default=False)

    # Duplicate detection
    file_hash = Column(String(64), index=True)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(String(50))

    # Image hashing
    image_hash_average = Column(String(64))
    image_hash_perceptual = Column(String(64))
    image_hash_difference = Column(String(64))

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        import json

        tags = []
        if self.tags:
            try:
                tags = json.loads(self.tags)
            except:
                tags = []

        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'vendor': self.vendor,
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'invoice_number': self.invoice_number,
            'tags': tags,
            'file_path': self.file_path,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'notes': self.notes,
            'currency': self.currency,
            'original_amount': self.original_amount,
            'original_currency': self.original_currency,
            'converted_to_usd': self.converted_to_usd,
            'file_hash': self.file_hash,
            'is_duplicate': self.is_duplicate,
            'duplicate_of': self.duplicate_of,
            'image_hash_average': self.image_hash_average,
            'image_hash_perceptual': self.image_hash_perceptual,
            'image_hash_difference': self.image_hash_difference
        }


class DatabaseAdapter:
    """SQLite database adapter with same interface as ExpenseCategorizer"""

    def __init__(self, data_folder: str, db_name: str = 'expenses.db'):
        """Initialize database connection"""
        self.data_folder = data_folder
        self.db_path = os.path.join(data_folder, db_name)

        # Create engine - use StaticPool for SQLite to allow multiple threads
        self.engine = create_engine(
            f'sqlite:///{self.db_path}',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            echo=False
        )

        # Create tables
        Base.metadata.create_all(self.engine)

        # Create session factory
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)

        # Cache for vendor history
        self._vendor_history_cache = None

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope for database operations"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def build_vendor_history(self) -> Dict:
        """Build vendor-to-category mapping from history"""
        if self._vendor_history_cache is not None:
            return self._vendor_history_cache

        history = defaultdict(lambda: defaultdict(int))

        with self.session_scope() as session:
            expenses = session.query(Expense).all()
            for expense in expenses:
                vendor = expense.vendor.lower()
                category = expense.category
                if vendor and category:
                    history[vendor][category] += 1

        self._vendor_history_cache = history
        return history

    def invalidate_vendor_cache(self):
        """Invalidate vendor history cache"""
        self._vendor_history_cache = None

    def add_expense(self, expense_data: Dict) -> str:
        """Add new expense record"""
        import json

        # Generate unique ID
        expense_id = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # Parse date
        date_str = expense_data.get('date')
        if isinstance(date_str, str):
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                date_obj = datetime.now().date()
        else:
            date_obj = datetime.now().date()

        # Parse processed_date
        processed_date_str = expense_data.get('processed_date')
        if isinstance(processed_date_str, str):
            try:
                processed_date = datetime.fromisoformat(processed_date_str)
            except ValueError:
                processed_date = datetime.now()
        else:
            processed_date = datetime.now()

        # Serialize tags
        tags = expense_data.get('tags', [])
        tags_json = json.dumps(tags) if tags else None

        # Create expense record
        expense = Expense(
            id=expense_id,
            date=date_obj,
            vendor=expense_data.get('vendor', 'Unknown'),
            amount=float(expense_data.get('amount', 0)),
            category=expense_data.get('category', 'Miscellaneous'),
            description=expense_data.get('description'),
            invoice_number=expense_data.get('invoice_number'),
            tags=tags_json,
            file_path=expense_data.get('file_path'),
            processed_date=processed_date,
            notes=expense_data.get('notes'),
            currency=expense_data.get('currency', 'USD'),
            original_amount=expense_data.get('original_amount'),
            original_currency=expense_data.get('original_currency'),
            converted_to_usd=expense_data.get('converted_to_usd', False),
            file_hash=expense_data.get('file_hash'),
            is_duplicate=expense_data.get('is_duplicate', False),
            duplicate_of=expense_data.get('duplicate_of'),
            image_hash_average=expense_data.get('image_hash_average'),
            image_hash_perceptual=expense_data.get('image_hash_perceptual'),
            image_hash_difference=expense_data.get('image_hash_difference')
        )

        with self.session_scope() as session:
            session.add(expense)

        # Invalidate cache
        self.invalidate_vendor_cache()

        return expense_id

    def get_expenses(self, category: Optional[str] = None, vendor: Optional[str] = None,
                    start_date: Optional[str] = None, end_date: Optional[str] = None,
                    search: Optional[str] = None) -> List[Dict]:
        """Get expenses with optional filters"""
        with self.session_scope() as session:
            query = session.query(Expense)

            # Filter by category
            if category:
                query = query.filter(Expense.category == category)

            # Filter by vendor
            if vendor:
                query = query.filter(Expense.vendor.like(f'%{vendor}%'))

            # Filter by date range
            if start_date:
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d').date()
                    query = query.filter(Expense.date >= start)
                except ValueError:
                    pass

            if end_date:
                try:
                    end = datetime.strptime(end_date, '%Y-%m-%d').date()
                    query = query.filter(Expense.date <= end)
                except ValueError:
                    pass

            # Search
            if search:
                search_pattern = f'%{search}%'
                query = query.filter(
                    (Expense.vendor.like(search_pattern)) |
                    (Expense.category.like(search_pattern)) |
                    (Expense.description.like(search_pattern)) |
                    (Expense.notes.like(search_pattern))
                )

            # Sort by date (newest first)
            query = query.order_by(Expense.date.desc())

            expenses = query.all()
            return [e.to_dict() for e in expenses]

    def get_statistics(self) -> Dict:
        """Get expense statistics"""
        with self.session_scope() as session:
            expenses = session.query(Expense).all()

            if not expenses:
                return {
                    'total_expenses': 0,
                    'total_amount': 0,
                    'by_category': {},
                    'by_vendor': {},
                    'by_month': {},
                    'recent_expenses': []
                }

            total_amount = sum(e.amount for e in expenses)

            # By category
            by_category = defaultdict(lambda: {'count': 0, 'total': 0})
            for expense in expenses:
                cat = expense.category or 'Uncategorized'
                by_category[cat]['count'] += 1
                by_category[cat]['total'] += expense.amount

            # By vendor
            by_vendor = defaultdict(lambda: {'count': 0, 'total': 0})
            for expense in expenses:
                vendor = expense.vendor or 'Unknown'
                by_vendor[vendor]['count'] += 1
                by_vendor[vendor]['total'] += expense.amount

            # By month
            by_month = defaultdict(lambda: {'count': 0, 'total': 0})
            for expense in expenses:
                if expense.date:
                    month_key = expense.date.strftime('%Y-%m')
                    by_month[month_key]['count'] += 1
                    by_month[month_key]['total'] += expense.amount

            # Recent expenses
            recent = session.query(Expense).order_by(Expense.processed_date.desc()).limit(10).all()
            recent_dicts = [e.to_dict() for e in recent]

            return {
                'total_expenses': len(expenses),
                'total_amount': total_amount,
                'by_category': dict(by_category),
                'by_vendor': dict(sorted(by_vendor.items(), key=lambda x: x[1]['total'], reverse=True)[:10]),
                'by_month': dict(sorted(by_month.items(), reverse=True)),
                'recent_expenses': recent_dicts
            }

    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        # Return predefined categories (same as categorizer)
        return [
            'Office Supplies', 'Software & Services', 'Travel',
            'Meals & Entertainment', 'Utilities', 'Marketing',
            'Equipment', 'Professional Services', 'Insurance',
            'Rent & Lease', 'Shipping', 'Maintenance', 'Training',
            'Miscellaneous'
        ]

    def get_all_vendors(self) -> List[str]:
        """Get all unique vendors"""
        with self.session_scope() as session:
            vendors = session.query(Expense.vendor).distinct().all()
            return sorted([v[0] for v in vendors if v[0]])

    def get_expense_by_id(self, expense_id: str) -> Optional[Dict]:
        """Get a single expense by ID"""
        with self.session_scope() as session:
            expense = session.query(Expense).filter(Expense.id == expense_id).first()
            return expense.to_dict() if expense else None

    def update_expense(self, expense_id: str, updates: Dict) -> bool:
        """Update an expense"""
        with self.session_scope() as session:
            expense = session.query(Expense).filter(Expense.id == expense_id).first()
            if not expense:
                return False

            # Update fields
            for key, value in updates.items():
                if hasattr(expense, key):
                    if key == 'date' and isinstance(value, str):
                        try:
                            value = datetime.strptime(value, '%Y-%m-%d').date()
                        except ValueError:
                            continue
                    setattr(expense, key, value)

            self.invalidate_vendor_cache()
            return True

    def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense"""
        with self.session_scope() as session:
            expense = session.query(Expense).filter(Expense.id == expense_id).first()
            if not expense:
                return False

            session.delete(expense)
            self.invalidate_vendor_cache()
            return True

    # Compatibility property for existing code
    @property
    def expenses(self) -> List[Dict]:
        """Get all expenses (for compatibility with old code)"""
        return self.get_expenses()

    @property
    def vendor_history(self) -> Dict:
        """Get vendor history (for compatibility)"""
        return self.build_vendor_history()
