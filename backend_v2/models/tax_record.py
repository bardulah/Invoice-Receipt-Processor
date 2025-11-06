"""Tax record model"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class TaxRecord(Base, TimestampMixin):
    """Tax reporting record model"""

    __tablename__ = 'tax_records'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    expense_id = Column(Integer, ForeignKey('expenses.id'), nullable=False, index=True)

    # Tax classification
    tax_year = Column(Integer, nullable=False, index=True)
    irs_category = Column(String(100), nullable=False)
    form_type = Column(String(50))  # Schedule C, Form 4562, etc.
    form_line = Column(String(20))

    # Deduction information
    deductible = Column(Boolean, default=True, nullable=False)
    deduction_percentage = Column(Integer, default=100)  # 100% or 50% for meals
    deductible_amount = Column(Float, nullable=False)

    # Additional tax metadata
    metadata = Column(JSON)  # Any additional tax-specific data

    # Relationships
    user = relationship('User')
    expense = relationship('Expense')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expense_id': self.expense_id,
            'tax_year': self.tax_year,
            'irs_category': self.irs_category,
            'form_type': self.form_type,
            'form_line': self.form_line,
            'deductible': self.deductible,
            'deduction_percentage': self.deduction_percentage,
            'deductible_amount': self.deductible_amount,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<TaxRecord {self.irs_category} ${self.deductible_amount}>'
