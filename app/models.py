from sqlalchemy import Column, String, Text, DateTime, Numeric, ForeignKey

from .database import Base


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = {"schema": "booking"}

    booking_id = Column(String(36), primary_key=True)
    owner_id = Column(String(36), nullable=False)
    pet_id = Column(String(36), nullable=False)
    sitter_id = Column(String(36), nullable=False)
    service_type_id = Column(String(36), nullable=False)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    status = Column(String(32), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    instructions = Column(Text, nullable=True)
    idempotency_key = Column(String(128), unique=True, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"
    __table_args__ = {"schema": "booking"}

    history_id = Column(String(36), primary_key=True)
    booking_id = Column(String(36), ForeignKey("booking.bookings.booking_id"), nullable=False)
    status = Column(String(32), nullable=False)
    changed_by = Column(String(64), nullable=False)
    changed_at = Column(DateTime, nullable=False)


class BookingTimeSlot(Base):
    __tablename__ = "booking_time_slots"
    __table_args__ = {"schema": "booking"}

    booking_slot_id = Column(String(36), primary_key=True)
    booking_id = Column(String(36), ForeignKey("booking.bookings.booking_id"), nullable=False)
    sitter_slot_id = Column(String(36), nullable=True)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
