from datetime import datetime
from decimal import Decimal

from app.schemas import BookingCreate, BookingStatusUpdate


def test_booking_create_required_fields():
    payload = BookingCreate(
        booking_id="b1",
        owner_id="o1",
        pet_id="p1",
        sitter_id="s1",
        service_type_id="t1",
        start_at=datetime(2026, 5, 1, 9, 0, 0),
        end_at=datetime(2026, 5, 1, 10, 0, 0),
        status="pending",
        total_price=Decimal("12.00"),
    )
    assert payload.booking_id == "b1"
    assert payload.instructions is None
    assert payload.total_price == Decimal("12.00")


def test_booking_status_update():
    upd = BookingStatusUpdate(status="completed", changed_by="sitter")
    assert upd.status == "completed"
    assert upd.changed_by == "sitter"
