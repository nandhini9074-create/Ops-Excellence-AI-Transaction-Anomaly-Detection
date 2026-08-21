import uuid
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Float, Integer, ForeignKey, 
    DateTime, Date, Numeric, Boolean, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass

def generate_uuid():
    return str(uuid.uuid4())

class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mcc: Mapped[Optional[str]] = mapped_column(String(4))
    status: Mapped[str] = mapped_column(String(50), default='ACTIVE')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    outlets = relationship("Outlet", back_populates="merchant", cascade="all, delete-orphan")


class Outlet(Base):
    __tablename__ = "outlets"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_city: Mapped[Optional[str]] = mapped_column(String(100))
    location_country: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default='ACTIVE')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    merchant = relationship("Merchant", back_populates="outlets")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    outlet_id: Mapped[str] = mapped_column(ForeignKey("outlets.id", ondelete="CASCADE"), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    segment: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100))
    transaction_no: Mapped[Optional[str]] = mapped_column(String(100))
    group_id: Mapped[Optional[str]] = mapped_column(String(100))
    group_transaction_id: Mapped[Optional[str]] = mapped_column(String(100))
    payout_transaction_id: Mapped[Optional[str]] = mapped_column(String(100))
    outlet_id: Mapped[str] = mapped_column(ForeignKey("outlets.id"), nullable=False)
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    profile_id: Mapped[Optional[str]] = mapped_column(ForeignKey("profiles.id"))
    transaction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    posting_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    txn_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    created_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_updated_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    silver_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    transaction_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    card_scheme: Mapped[Optional[str]] = mapped_column(String(50))
    merchant_name: Mapped[Optional[str]] = mapped_column(String(255))
    outlet_name: Mapped[Optional[str]] = mapped_column(String(255))
    outlet_status: Mapped[Optional[str]] = mapped_column(String(50))


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    anomaly_id: Mapped[str] = mapped_column(String(100), nullable=False)
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    merchant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    outlet_id: Mapped[str] = mapped_column(ForeignKey("outlets.id"), nullable=False)
    outlet_name: Mapped[str] = mapped_column(String(255), nullable=False)
    anomaly_type: Mapped[str] = mapped_column(String(100), nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='OPEN')
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100))
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    user_typing: Mapped[Optional[str]] = mapped_column(Text)
    scheme: Mapped[Optional[str]] = mapped_column(String(50))
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    issue_id: Mapped[str] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    comments: Mapped[Optional[str]] = mapped_column(Text)
    user_typing: Mapped[Optional[str]] = mapped_column(Text)
    submitted_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Baseline(Base):
    __tablename__ = "baselines"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    outlet_id: Mapped[str] = mapped_column(ForeignKey("outlets.id", ondelete="CASCADE"), nullable=False)
    profile_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    analyzed_days: Mapped[int] = mapped_column(Integer, nullable=False)
    data_points_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[str] = mapped_column(String(10), default='true')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    run_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    anomalies_detected: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)


class MerchantWhitelist(Base):
    __tablename__ = "merchant_whitelists"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    outlet_id: Mapped[Optional[str]] = mapped_column(ForeignKey("outlets.id", ondelete="CASCADE"))
    false_positive_count: Mapped[int] = mapped_column(Integer, default=0)
    threshold_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    is_whitelisted: Mapped[str] = mapped_column(String(10), default='false')
    dormancy_suppressed_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
