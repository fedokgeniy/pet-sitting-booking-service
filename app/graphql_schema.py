import strawberry
from typing import List, Optional
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.orm import Session
from .database import get_db
from .models import Booking

@strawberry.type
class BookingType:
    booking_id: str
    owner_id: str
    pet_id: str
    sitter_id: str
    service_type_id: str
    status: str
    total_price: float
    instructions: Optional[str]

@strawberry.type
class Query:
    @strawberry.field
    def bookings(self, info) -> List[BookingType]:
        db: Session = info.context["db"]
        rows = db.query(Booking).order_by(Booking.created_at.desc()).all()
        return [BookingType(
            booking_id=r.booking_id,
            owner_id=r.owner_id,
            pet_id=r.pet_id,
            sitter_id=r.sitter_id,
            service_type_id=r.service_type_id,
            status=r.status,
            total_price=float(r.total_price),
            instructions=r.instructions,
        ) for r in rows]

schema = strawberry.Schema(query=Query)