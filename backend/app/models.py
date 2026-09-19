from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    matricule: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Permit(Base):
    __tablename__ = "permits"
    id: Mapped[int] = mapped_column(primary_key=True)
    permit_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    permit_date: Mapped[date] = mapped_column(Date, default=date.today)
    site: Mapped[str] = mapped_column(String(180), default="AGIL Gaz Radès")
    work_location: Mapped[str] = mapped_column(String(255))
    contractor: Mapped[str] = mapped_column(String(180))
    responsible_person: Mapped[str] = mapped_column(String(180))
    work_description: Mapped[str] = mapped_column(Text)
    work_types: Mapped[list] = mapped_column(JSON, default=list)
    other_work_type: Mapped[str | None] = mapped_column(String(180), nullable=True)
    safety_checks: Mapped[list] = mapped_column(JSON, default=list)
    gas_measurement: Mapped[dict] = mapped_column(JSON, default=dict)
    hot_work_checks: Mapped[list] = mapped_column(JSON, default=list)
    planned_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval: Mapped[dict] = mapped_column(JSON, default=dict)
    closure_checks: Mapped[list] = mapped_column(JSON, default=list)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    creator: Mapped[User] = relationship()
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="permit", cascade="all, delete-orphan", order_by="AuditLog.created_at")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    permit_id: Mapped[int] = mapped_column(ForeignKey("permits.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_name: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(80))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    permit: Mapped[Permit] = relationship(back_populates="audit_logs")

