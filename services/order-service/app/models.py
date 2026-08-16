from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean
from sqlalchemy.sql import func

from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_token = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tracking_number = Column(String, nullable=True)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())