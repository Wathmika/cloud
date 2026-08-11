from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func

from app.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, nullable=False, default="GBP")
    payment_token = Column(String, nullable=False)
    status = Column(String, nullable=False, default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())