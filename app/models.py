from typing import Optional
from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel


class Event(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_event_capacity_positive"),
        CheckConstraint("status IN ('Open', 'Closed')", name="ck_event_status"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    organizer: str = Field(min_length=1)
    status: str = Field(default="Open")


class Reservation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", index=True)
    student_name: str = Field(min_length=1)
    roll_number: str = Field(min_length=1)
    email: str
