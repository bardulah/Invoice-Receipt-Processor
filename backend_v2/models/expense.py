"""Expense model"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Expense(Base, TimestampMixin):
    """Expense record model"""

    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # Basic expense information
    vendor = Column(String(255), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    original_amount = Column(Float)
    original_currency = Column(String(3))
    date = Column(Date, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)

    # Additional details
    description = Column(Text)
    invoice_number = Column(String(100), index=True)
    notes = Column(Text)
    tags = Column(JSON)  # List of tags

    # File information
    file_path = Column(String(500))
    file_hash = Column(String(64), index=True)  # SHA-256 hash
    image_hashes = Column(JSON)  # Perceptual hashes

    # Processing metadata
    confidence_score = Column(Integer)  # OCR confidence 0-100
    ml_enhanced = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(Integer, ForeignKey('expenses.id'))

    # Extracted data
    raw_text = Column(Text)  # Original OCR text
    extraction_data = Column(JSON)  # Full extraction results

    # Relationships
    user = relationship('User', back_populates='expenses')
    duplicate_of = relationship('Expense', remote_side=[id], foreign_keys=[duplicate_of_id])

    def to_dict(self, include_raw=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'vendor': self.vendor,
            'amount': self.amount,
            'currency': self.currency,
            'date': self.date.isoformat() if self.date else None,
            'category': self.category,
            'description': self.description,
            'invoice_number': self.invoice_number,
            'notes': self.notes,
            'tags': self.tags,
            'file_path': self.file_path,
            'confidence_score': self.confidence_score,
            'ml_enhanced': self.ml_enhanced,
            'is_duplicate': self.is_duplicate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if self.original_amount and self.original_currency:
            data['original_amount'] = self.original_amount
            data['original_currency'] = self.original_currency

        if include_raw:
            data['raw_text'] = self.raw_text
            data['extraction_data'] = self.extraction_data

        return data

    def __repr__(self):
        return f'<Expense {self.vendor} ${self.amount} on {self.date}>'
