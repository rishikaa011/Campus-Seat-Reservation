from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, Any, cast
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import func
from sqlmodel import Session, select
from .database import create_db_and_tables, get_session
from .models import Event, Reservation
from .schemas import (
    Availability,
    EventCreate,
    EventUpdate,
    ReservationCreate,
    ReservationRead,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_db_and_tables()
    yield


app = FastAPI(
    title="Campus Event Seat Reservation API",
    version="1.0.0",
    description="Manage campus events and student seat reservations.",
    lifespan=lifespan,
)
SessionDep = Annotated[Session, Depends(get_session)]


def get_event_or_404(event_id: int, session: Session) -> Event:
    event = session.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


def booked_count(event_id: int, session: Session) -> int:
    count = session.exec(
        select(func.count())
        .select_from(Reservation)
        .where(Reservation.event_id == event_id)
    ).one()
    return int(count)


@app.post(
    "/events",
    response_model=Event,
    status_code=status.HTTP_201_CREATED,
    tags=["Events"],
)
def create_event(event: EventCreate, session: SessionDep) -> Event:
    db_event = Event.model_validate(event)
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event


@app.get("/events", response_model=list[Event], tags=["Events"])
def list_events(session: SessionDep) -> list[Event]:
    return list(session.exec(select(Event).order_by(cast(Any, Event.id))).all())


@app.get("/events/{event_id}", response_model=Event, tags=["Events"])
def get_event(event_id: int, session: SessionDep) -> Event:
    return get_event_or_404(event_id, session)


@app.put("/events/{event_id}", response_model=Event, tags=["Events"])
def update_event(
    event_id: int, event_update: EventUpdate, session: SessionDep
) -> Event:
    event = get_event_or_404(event_id, session)
    update_data = event_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=422, detail="Provide at least one field to update"
        )

    new_capacity = update_data.get("capacity", event.capacity)
    if new_capacity < booked_count(event_id, session):
        raise HTTPException(
            status_code=409,
            detail="Capacity cannot be lower than the number of booked seats",
        )

    event.sqlmodel_update(update_data)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@app.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Events"],
)
def delete_event(event_id: int, session: SessionDep) -> None:
    event = get_event_or_404(event_id, session)
    reservations = session.exec(
        select(Reservation).where(Reservation.event_id == event_id)
    ).all()
    for reservation in reservations:
        session.delete(reservation)
    session.delete(event)
    session.commit()


@app.post(
    "/events/{event_id}/reserve",
    response_model=ReservationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Reservations"],
)
def create_reservation(
    event_id: int, reservation: ReservationCreate, session: SessionDep
) -> Reservation:
    event = get_event_or_404(event_id, session)
    if event.status != "Open":
        raise HTTPException(status_code=409, detail="This event is closed")
    if booked_count(event_id, session) >= event.capacity:
        raise HTTPException(status_code=409, detail="This event is full")

    db_reservation = Reservation.model_validate(
        reservation, update={"event_id": event_id}
    )
    session.add(db_reservation)
    session.commit()
    session.refresh(db_reservation)
    return db_reservation


@app.get(
    "/events/{event_id}/reservations",
    response_model=list[ReservationRead],
    tags=["Reservations"],
)
def list_reservations(event_id: int, session: SessionDep) -> list[Reservation]:
    get_event_or_404(event_id, session)
    return list(
        session.exec(
            select(Reservation)
            .where(Reservation.event_id == event_id)
            .order_by(cast(Any, Reservation.id))
        ).all()
    )


@app.delete(
    "/reservations/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Reservations"],
)
def delete_reservation(reservation_id: int, session: SessionDep) -> None:
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    session.delete(reservation)
    session.commit()


@app.get(
    "/events/{event_id}/availability",
    response_model=Availability,
    tags=["Reservations"],
)
def get_availability(event_id: int, session: SessionDep) -> Availability:
    event = get_event_or_404(event_id, session)
    booked = booked_count(event_id, session)
    return Availability(
        capacity=event.capacity,
        booked=booked,
        remaining=event.capacity - booked,
    )
