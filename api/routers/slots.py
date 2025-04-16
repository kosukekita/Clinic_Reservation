from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, time, timedelta
import calendar
from pydantic import BaseModel

from .. import models, schemas
from ..database import get_db
from .auth import get_admin_user, get_current_active_user

router = APIRouter()

# リクエストボディ用のモデルを定義
class BulkCreateSlotsRequest(BaseModel):
    days_of_week: List[int]
    start_hour: int = 17
    end_hour: int = 19
    slot_duration_minutes: int = 30
    capacity: int = 2

@router.post("/slots/", response_model=schemas.TimeSlot)
def create_slot(
    slot: schemas.TimeSlotCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_admin_user)
):
    """管理者が単一の予約枠を作成するエンドポイント"""
    db_slot = models.TimeSlot(
        date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        capacity=slot.capacity,
    )
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot


@router.post("/slots/bulk", response_model=List[schemas.TimeSlot])
def create_slots_bulk(
    start_date: datetime,
    end_date: datetime,
    data: BulkCreateSlotsRequest,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_admin_user)
):
    """管理者が複数の予約枠をまとめて作成するエンドポイント"""
    
    # 日付の範囲をチェック
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    # 曜日の値をチェック (0-6 の範囲内かどうか)
    for day in data.days_of_week:
        if day < 0 or day > 6:
            raise HTTPException(status_code=400, detail="Days of week must be between 0 and 6")
    
    created_slots = []
    current_date = start_date.date()
    end_date = end_date.date()
    
    while current_date <= end_date:
        # 選択された曜日かどうかチェック
        weekday = current_date.weekday()
        if weekday in data.days_of_week:
            # 指定された時間帯に指定間隔おきのスロットを作成
            for hour in range(data.start_hour, data.end_hour):
                for minute in [0, 30]:
                    if hour == data.end_hour and minute > 0:
                        continue
                    
                    start_time = time(hour, minute)
                    
                    # スロット時間（分）を計算
                    end_minute = (minute + data.slot_duration_minutes) % 60
                    end_hour = hour + (minute + data.slot_duration_minutes) // 60
                    end_time = time(end_hour, end_minute)
                    
                    # スロットが既に存在するかチェック
                    existing_slot = db.query(models.TimeSlot).filter(
                        models.TimeSlot.date == current_date,
                        models.TimeSlot.start_time == start_time
                    ).first()
                    
                    if not existing_slot:
                        # 新しいスロットを作成
                        db_slot = models.TimeSlot(
                            date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            capacity=data.capacity
                        )
                        db.add(db_slot)
                        created_slots.append(db_slot)
        
        # 翌日に進む
        current_date += timedelta(days=1)
    
    db.commit()
    
    # 作成したスロットを返す前にリフレッシュ
    for slot in created_slots:
        db.refresh(slot)
    
    return created_slots


@router.get("/slots/", response_model=List[schemas.TimeSlot])
def get_slots(
    start_date: datetime = None,
    end_date: datetime = None,
    available_only: bool = False,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """予約枠を取得するエンドポイント"""
    query = db.query(models.TimeSlot).filter(models.TimeSlot.is_active == True)
    
    # 開始日と終了日でフィルタリング
    if start_date:
        query = query.filter(models.TimeSlot.date >= start_date.date())
    if end_date:
        query = query.filter(models.TimeSlot.date <= end_date.date())
    
    # 空き枠のみ表示オプション
    if available_only:
        query = query.filter(models.TimeSlot.available_spots > 0)
    
    # 日付順に並べ替え
    query = query.order_by(models.TimeSlot.date, models.TimeSlot.start_time)
    
    return query.all()


@router.put("/slots/{slot_id}", response_model=schemas.TimeSlot)
def update_slot(
    slot_id: int,
    slot: schemas.TimeSlotCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_admin_user)
):
    """管理者が予約枠を更新するエンドポイント"""
    db_slot = db.query(models.TimeSlot).filter(models.TimeSlot.id == slot_id).first()
    if not db_slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    # 予約が既に入っている場合、容量の減少はできない
    if slot.capacity < db_slot.capacity - db_slot.available_spots:
        raise HTTPException(status_code=400, detail="Cannot reduce capacity below current reservations")
    
    # データ更新
    db_slot.date = slot.date
    db_slot.start_time = slot.start_time
    db_slot.end_time = slot.end_time
    
    # 容量が変更された場合、利用可能な枠も更新
    if slot.capacity != db_slot.capacity:
        taken_spots = db_slot.capacity - db_slot.available_spots
        db_slot.capacity = slot.capacity
        db_slot.available_spots = slot.capacity - taken_spots
    
    db.commit()
    db.refresh(db_slot)
    return db_slot


@router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_admin_user)
):
    """管理者が予約枠を削除するエンドポイント"""
    db_slot = db.query(models.TimeSlot).filter(models.TimeSlot.id == slot_id).first()
    if not db_slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    # 予約が入っている場合は削除できない
    if db_slot.capacity > db_slot.available_spots:
        raise HTTPException(status_code=400, detail="Cannot delete slot with existing reservations")
    
    db.delete(db_slot)
    db.commit()
    return None