from datetime import datetime

from sqlalchemy.orm import Session

from .database import Base, engine, ensure_schema
from .logging_config import get_logger
from .models import Booking, BookingStatusHistory, BookingTimeSlot

logger = get_logger(__name__)


def create_schema_and_tables() -> None:
    logger.info("Creating schema 'booking' and its tables")
    ensure_schema("booking")
    Base.metadata.create_all(
        bind=engine,
        tables=[
            Booking.__table__,
            BookingStatusHistory.__table__,
            BookingTimeSlot.__table__,
        ],
    )
    logger.info("Schema 'booking' is ready")


def seed_stub_data() -> None:
    logger.info("Seeding stub data for booking service")
    with Session(engine) as session:
        if session.query(Booking).first():
            logger.info("Stub data already present, skip seeding")
            return

        booking1 = Booking(
            booking_id="88888888-8888-8888-8888-888888888881",
            owner_id="99999999-9999-9999-9999-999999999991",
            pet_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1",
            sitter_id="11111111-1111-1111-1111-111111111111",
            service_type_id="33333333-3333-3333-3333-333333333331",
            start_at=datetime(2026, 5, 1, 9, 0, 0),
            end_at=datetime(2026, 5, 1, 10, 0, 0),
            status="confirmed",
            total_price=12.00,
            instructions="Walk Rex in the park",
            idempotency_key="idem-book-1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        booking2 = Booking(
            booking_id="88888888-8888-8888-8888-888888888882",
            owner_id="99999999-9999-9999-9999-999999999992",
            pet_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2",
            sitter_id="22222222-2222-2222-2222-222222222222",
            service_type_id="33333333-3333-3333-3333-333333333332",
            start_at=datetime(2026, 5, 1, 10, 0, 0),
            end_at=datetime(2026, 5, 1, 18, 0, 0),
            status="pending",
            total_price=45.00,
            instructions="Feed Luna at noon",
            idempotency_key="idem-book-2",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session.add_all([booking1, booking2])
        session.flush()

        session.add_all([
            BookingStatusHistory(
                history_id="99999999-aaaa-aaaa-aaaa-aaaaaaaaaaa1",
                booking_id=booking1.booking_id,
                status="created",
                changed_by="owner",
                changed_at=datetime.utcnow(),
            ),
            BookingStatusHistory(
                history_id="99999999-aaaa-aaaa-aaaa-aaaaaaaaaaa2",
                booking_id=booking1.booking_id,
                status="confirmed",
                changed_by="sitter",
                changed_at=datetime.utcnow(),
            ),
            BookingTimeSlot(
                booking_slot_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1",
                booking_id=booking1.booking_id,
                sitter_slot_id="66666666-6666-6666-6666-666666666661",
                start_at=datetime(2026, 5, 1, 9, 0, 0),
                end_at=datetime(2026, 5, 1, 10, 0, 0),
            ),
            BookingTimeSlot(
                booking_slot_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2",
                booking_id=booking2.booking_id,
                sitter_slot_id="66666666-6666-6666-6666-666666666662",
                start_at=datetime(2026, 5, 1, 10, 0, 0),
                end_at=datetime(2026, 5, 1, 18, 0, 0),
            ),
        ])

        session.commit()
        logger.info("Stub data seeded successfully")
