"""Budget model"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Budget(Base, TimestampMixin):
    """Budget model"""

    __tablename__ = 'budgets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # Budget details
    name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    period = Column(String(50), nullable=False)  # monthly, quarterly, yearly, custom
    category = Column(String(100), index=True)
    vendor = Column(String(255), index=True)

    # Date range
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)

    # Settings
    alert_thresholds = Column(JSON)  # [50, 75, 90, 100]
    rollover_unused = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship('User', back_populates='budgets')
    alerts = relationship('Alert', back_populates='budget', cascade='all, delete-orphan')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'amount': self.amount,
            'period': self.period,
            'category': self.category,
            'vendor': self.vendor,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'alert_thresholds': self.alert_thresholds,
            'rollover_unused': self.rollover_unused,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Budget {self.name} ${self.amount}>'
