from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, time, date


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: str


class UserCreate(UserBase):
    password: str
    is_admin: bool = False  # デフォルトはFalseだが、明示的に指定可能にする


class User(UserBase):
    id: int
    is_admin: bool
    is_active: bool

    class Config:
        orm_mode = True


class TimeSlotBase(BaseModel):
    date: date
    start_time: time
    end_time: time
    capacity: int = 2


class TimeSlotCreate(TimeSlotBase):
    pass


class TimeSlot(TimeSlotBase):
    id: int
    available_spots: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


class ReservationBase(BaseModel):
    slot_id: int


class ReservationCreate(ReservationBase):
    pass


class Reservation(ReservationBase):
    id: int
    patient_id: int
    daily_number: int
    qr_code_data: str
    is_confirmed: bool
    created_at: datetime

    class Config:
        orm_mode = True


class ReservationWithDetails(Reservation):
    patient: User
    time_slot: TimeSlot

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    is_admin: Optional[bool] = False