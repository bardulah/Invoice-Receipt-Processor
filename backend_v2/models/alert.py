"""Alert model"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Alert(Base, TimestampMixin):
    """Budget alert model"""

    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    budget_id = Column(Integer, ForeignKey('budgets.id'), nullable=False, index=True)

    # Alert details
    threshold = Column(Integer, nullable=False)  # Percentage threshold
    percentage = Column(Float, nullable=False)  # Actual percentage at alert time
    spent = Column(Float, nullable=False)
    budget_amount = Column(Float, nullable=False)
    remaining = Column(Float, nullable=False)

    # Period information
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Alert metadata
    severity = Column(String(20), nullable=False)  # info, warning, error, critical
    message = Column(Text, nullable=False)

    # Status
    read = Column(Boolean, default=False, nullable=False)
    dismissed = Column(Boolean, default=False, nullable=False)
    read_at = Column(Date)
    dismissed_at = Column(Date)

    # Relationships
    budget = relationship('Budget', back_populates='alerts')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'budget_id': self.budget_id,
            'budget_name': self.budget.name if self.budget else None,
            'threshold': self.threshold,
            'percentage': self.percentage,
            'spent': self.spent,
            'budget_amount': self.budget_amount,
            'remaining': self.remaining,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'severity': self.severity,
            'message': self.message,
            'read': self.read,
            'dismissed': self.dismissed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Alert {self.severity} at {self.percentage}%>'
