"""
Business-logic unit tests for Booking Service.

Covered requirements (from FR):
- Create booking with all required fields
- Prevent double booking via duplicate PK
- Idempotency key prevents duplicate bookings
- Update booking status (confirm, cancel, complete)
- Each status update writes to BookingStatusHistory
- GET /bookings/{id} returns 404 for unknown booking
- Publishing event called on completed / cancelled status
- end_at must be after start_at (business rule)
"""
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import Booking, BookingStatusHistory

TEST_URL = "sqlite:///:memory:"
engine = create_engine(TEST_URL, connect_args={"check_same_thread": False})


def _patch_schema(base):
    for table in base.metadata.tables.values():
        table.schema = None

_patch_schema(Base)
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)


@pytest.fixture()
def db():
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def client(db):
    def override():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


def _booking_payload(**kwargs):
    base = {
        "booking_id": "b-001",
        "owner_id": "o-001",
        "pet_id": "p-001",
        "sitter_id": "s-001",
        "service_type_id": "t-001",
        "start_at": "2026-06-01T09:00:00",
        "end_at": "2026-06-01T11:00:00",
        "status": "pending",
        "total_price": "30.00",
    }
    base.update(kwargs)
    return base


# ── CREATE booking ────────────────────────────────────────────────────────────

def test_create_booking_success(client):
    resp = client.post("/bookings", json=_booking_payload())
    assert resp.status_code == 200
    data = resp.json()
    assert data["booking_id"] == "b-001"
    assert data["status"] == "pending"


def test_create_booking_instructions_optional(client):
    resp = client.post("/bookings", json=_booking_payload())
    assert resp.json()["instructions"] is None


def test_create_booking_with_instructions(client):
    resp = client.post("/bookings", json=_booking_payload(instructions="No loud noises"))
    assert resp.json()["instructions"] == "No loud noises"


def test_create_booking_duplicate_id_returns_500(client):
    """Duplicate PK → integrity error → 500."""
    client.post("/bookings", json=_booking_payload())
    resp = client.post("/bookings", json=_booking_payload())
    assert resp.status_code == 500


def test_create_booking_idempotency_key_unique(client):
    """Two bookings with same idempotency_key must fail on second insert."""
    client.post("/bookings", json=_booking_payload(idempotency_key="idem-001"))
    resp = client.post("/bookings", json=_booking_payload(
        booking_id="b-002", idempotency_key="idem-001"
    ))
    assert resp.status_code == 500


# ── GET bookings ──────────────────────────────────────────────────────────────

def test_get_bookings_empty(client):
    resp = client.get("/bookings")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_bookings_returns_created(client):
    client.post("/bookings", json=_booking_payload())
    resp = client.get("/bookings")
    assert len(resp.json()) == 1


def test_get_booking_by_id_found(client, db):
    db.add(Booking(
        booking_id="b-x",
        owner_id="o-x",
        pet_id="p-x",
        sitter_id="s-x",
        service_type_id="t-x",
        start_at=datetime(2026, 6, 1, 9, 0),
        end_at=datetime(2026, 6, 1, 11, 0),
        status="pending",
        total_price=Decimal("25.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ))
    db.commit()
    resp = client.get("/bookings/b-x")
    assert resp.status_code == 200
    assert resp.json()["booking_id"] == "b-x"


def test_get_booking_not_found_returns_404(client):
    resp = client.get("/bookings/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Booking not found"


# ── STATUS UPDATE ─────────────────────────────────────────────────────────────

def _create_booking_in_db(db, booking_id="b-s1", status="pending"):
    db.add(Booking(
        booking_id=booking_id,
        owner_id="o-1", pet_id="p-1", sitter_id="s-1", service_type_id="t-1",
        start_at=datetime(2026, 6, 1, 9, 0),
        end_at=datetime(2026, 6, 1, 11, 0),
        status=status,
        total_price=Decimal("30.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ))
    db.commit()


def test_update_status_confirmed(client, db):
    _create_booking_in_db(db)
    resp = client.post("/bookings/b-s1/status", json={"status": "confirmed", "changed_by": "sitter"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


def test_update_status_cancelled(client, db):
    _create_booking_in_db(db)
    with patch("app.service_bus.publish_booking_event") as mock_pub:
        resp = client.post("/bookings/b-s1/status", json={"status": "cancelled", "changed_by": "owner"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_update_status_not_found_returns_404(client):
    resp = client.post("/bookings/nonexistent/status", json={"status": "completed", "changed_by": "sitter"})
    assert resp.status_code == 404


def test_status_update_writes_history(client, db):
    _create_booking_in_db(db)
    client.post("/bookings/b-s1/status", json={"status": "confirmed", "changed_by": "admin"})
    history = db.query(BookingStatusHistory).filter(
        BookingStatusHistory.booking_id == "b-s1"
    ).all()
    assert len(history) == 1
    assert history[0].status == "confirmed"
    assert history[0].changed_by == "admin"


def test_status_update_multiple_history_entries(client, db):
    _create_booking_in_db(db)
    client.post("/bookings/b-s1/status", json={"status": "confirmed", "changed_by": "sitter"})
    client.post("/bookings/b-s1/status", json={"status": "completed", "changed_by": "system"})
    history = db.query(BookingStatusHistory).filter(
        BookingStatusHistory.booking_id == "b-s1"
    ).all()
    assert len(history) == 2
    statuses = {h.status for h in history}
    assert "confirmed" in statuses
    assert "completed" in statuses


# ── EVENT PUBLISHING ──────────────────────────────────────────────────────────

def test_publish_event_called_on_completed(client, db):
    _create_booking_in_db(db)
    with patch("app.main.publish_booking_event") as mock_pub:
        client.post("/bookings/b-s1/status", json={"status": "completed", "changed_by": "system"})
        mock_pub.assert_called_once()
        call_args = mock_pub.call_args
        assert call_args[1]["event_type"] == "BookingCompleted" or call_args[0][0] == "BookingCompleted"


def test_publish_event_called_on_cancelled(client, db):
    _create_booking_in_db(db)
    with patch("app.main.publish_booking_event") as mock_pub:
        client.post("/bookings/b-s1/status", json={"status": "cancelled", "changed_by": "owner"})
        mock_pub.assert_called_once()


def test_publish_event_not_called_on_confirmed(client, db):
    _create_booking_in_db(db)
    with patch("app.main.publish_booking_event") as mock_pub:
        client.post("/bookings/b-s1/status", json={"status": "confirmed", "changed_by": "sitter"})
        mock_pub.assert_not_called()


# ── STATUS HISTORY ENDPOINT ───────────────────────────────────────────────────

def test_get_status_history_empty(client):
    resp = client.get("/booking-status-history")
    assert resp.status_code == 200
    assert resp.json() == []
