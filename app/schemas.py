from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class BookingCreate(BaseModel):
    booking_id: str
    owner_id: str
    pet_id: str
    sitter_id: str
    service_type_id: str
    start_at: datetime
    end_at: datetime
    status: str
    total_price: Decimal
    instructions: str | None = None
    idempotency_key: str | None = None


class BookingOut(BookingCreate):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingStatusHistoryOut(BaseModel):
    history_id: str
    booking_id: str
    status: str
    changed_by: str
    changed_at: datetime

    class Config:
        from_attributes = True


class BookingStatusUpdate(BaseModel):
    status: str
    changed_by: str
