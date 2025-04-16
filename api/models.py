from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Time
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    phone_number = Column(String)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # ユーザーが持つ予約のリレーション
    reservations = relationship("Reservation", back_populates="patient")


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True)
    start_time = Column(Time, index=True)
    end_time = Column(Time)
    capacity = Column(Integer, default=2)  # デフォルトは各枠2名まで
    available_spots = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    # このスロットに紐づく予約のリレーション
    reservations = relationship("Reservation", back_populates="time_slot")

    def __init__(self, date, start_time, end_time, capacity=2, **kwargs):
        super().__init__(date=date, start_time=start_time, end_time=end_time, 
                        capacity=capacity, available_spots=capacity, **kwargs)


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    slot_id = Column(Integer, ForeignKey("time_slots.id"))
    daily_number = Column(Integer, index=True)  # 日ごとの通し番号
    qr_code_data = Column(String, unique=True, index=True)
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # リレーション
    patient = relationship("User", back_populates="reservations")
    time_slot = relationship("TimeSlot", back_populates="reservations")