import uuid
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .init_db import create_schema_and_tables, seed_stub_data
from .logging_config import configure_logging, get_logger
from .models import Booking, BookingStatusHistory
from .schemas import BookingCreate, BookingOut, BookingStatusHistoryOut, BookingStatusUpdate
from .service_bus import publish_booking_event
from strawberry.fastapi import GraphQLRouter
from .graphql_schema import schema
from .database import get_db

async def get_context(db: Session = Depends(get_db)):
    return {"db": db}

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Booking Service")

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

@app.on_event("startup")
def startup() -> None:
    logger.info("Booking service is starting up")
    create_schema_and_tables()
    logger.info("Booking service startup completed")


@app.get("/health")
def health():
    logger.debug("Health check requested")
    return {"service": "booking_service", "status": "ok"}


@app.post("/init-db")
def init_db():
    logger.info("Manual /init-db invoked")
    create_schema_and_tables()
    return {"status": "ok", "schema": "booking"}


@app.post("/seed")
def seed():
    logger.info("Manual /seed invoked")
    seed_stub_data()
    return {"status": "ok", "schema": "booking", "message": "stub data inserted"}


#@app.get("/bookings", response_model=list[BookingOut])
#def get_bookings(db: Session = Depends(get_db)):
 #   logger.info("GET /bookings")
  #  return db.query(Booking).order_by(Booking.created_at.desc()).all()


@app.get("/bookings/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: str, db: Session = Depends(get_db)):
    logger.info("GET /bookings/%s", booking_id)
    item = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not item:
        logger.warning("Booking not found: %s", booking_id)
        raise HTTPException(status_code=404, detail="Booking not found")
    return item


@app.post("/bookings", response_model=BookingOut)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    logger.info("POST /bookings booking_id=%s sitter_id=%s", payload.booking_id, payload.sitter_id)
    try:
        item = Booking(
            booking_id=payload.booking_id,
            owner_id=payload.owner_id,
            pet_id=payload.pet_id,
            sitter_id=payload.sitter_id,
            service_type_id=payload.service_type_id,
            start_at=payload.start_at,
            end_at=payload.end_at,
            status=payload.status,
            total_price=payload.total_price,
            instructions=payload.instructions,
            idempotency_key=payload.idempotency_key,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        logger.info("Booking created: %s", item.booking_id)
        return item
    except Exception as ex:
        logger.exception("Failed to create booking: %s", ex)
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/booking-status-history", response_model=list[BookingStatusHistoryOut])
def get_status_history(db: Session = Depends(get_db)):
    logger.info("GET /booking-status-history")
    return db.query(BookingStatusHistory).order_by(BookingStatusHistory.changed_at.desc()).all()


@app.post("/bookings/{booking_id}/status", response_model=BookingOut)
def update_booking_status(booking_id: str, payload: BookingStatusUpdate, db: Session = Depends(get_db)):
    logger.info(
        "POST /bookings/%s/status status=%s changed_by=%s",
        booking_id, payload.status, payload.changed_by,
    )
    try:
        item = db.query(Booking).filter(Booking.booking_id == booking_id).first()
        if not item:
            logger.warning("Booking not found for status update: %s", booking_id)
            raise HTTPException(status_code=404, detail="Booking not found")

        item.status = payload.status
        item.updated_at = datetime.utcnow()

        history = BookingStatusHistory(
            history_id=str(uuid.uuid4()),
            booking_id=item.booking_id,
            status=payload.status,
            changed_by=payload.changed_by,
            changed_at=datetime.utcnow(),
        )
        db.add(history)
        db.commit()
        db.refresh(item)
        logger.debug("Booking %s status committed", booking_id)

        if payload.status in ("completed", "cancelled"):
            publish_booking_event(
                event_type=f"Booking{payload.status.capitalize()}",
                payload={
                    "booking_id": item.booking_id,
                    "owner_id": item.owner_id,
                    "pet_id": item.pet_id,
                    "sitter_id": item.sitter_id,
                    "service_type_id": item.service_type_id,
                    "status": item.status,
                    "start_at": item.start_at.isoformat(),
                    "end_at": item.end_at.isoformat(),
                },
            )
            logger.info("Event published for booking %s", booking_id)

        return item

    except HTTPException:
        raise
    except Exception as ex:
        logger.exception("Booking status update failed: %s", ex)
        raise HTTPException(status_code=500, detail=str(ex))
