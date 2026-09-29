from typing import Any, Literal, Optional
from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel


class EventCreate(SQLModel):
    title: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    organizer: str = Field(min_length=1)
    status: Literal["Open", "Closed"] = "Open"

    @field_validator("title", "venue", "organizer")
    @classmethod
    def require_non_whitespace(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field must not be empty")
        return value


class EventUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1)
    venue: Optional[str] = Field(default=None, min_length=1)
    capacity: Optional[int] = Field(default=None, gt=0)
    organizer: Optional[str] = Field(default=None, min_length=1)
    status: Optional[Literal["Open", "Closed"]] = None

    @field_validator(
        "title", "venue", "capacity", "organizer", "status", mode="before"
    )
    @classmethod
    def reject_explicit_null(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("Updated fields cannot be null")
        return value

    @field_validator("title", "venue", "organizer")
    @classmethod
    def require_non_whitespace(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("This field must not be empty")
        return value


class ReservationCreate(SQLModel):
    student_name: str = Field(min_length=1)
    roll_number: str = Field(min_length=1)
    email: EmailStr

    @field_validator("student_name", "roll_number")
    @classmethod
    def require_non_whitespace(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field must not be empty")
        return value


class ReservationRead(SQLModel):
    id: int
    event_id: int
    student_name: str
    roll_number: str
    email: EmailStr


class Availability(SQLModel):
    capacity: int
    booked: int
    remaining: int
