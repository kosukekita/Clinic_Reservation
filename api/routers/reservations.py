from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import uuid
from datetime import datetime, date

from .. import models, schemas
from ..database import get_db
from .auth import get_current_active_user, get_admin_user

router = APIRouter()


def generate_qr_code_data():
    """ユニークなQRコードデータを生成"""
    return str(uuid.uuid4())


def get_daily_number(db: Session, reservation_date: date):
    """その日の予約番号を取得（連番）"""
    # その日の最大の番号を取得
    max_number = db.query(func.max(models.Reservation.daily_number))\
        .join(models.TimeSlot)\
        .filter(models.TimeSlot.date == reservation_date)\
        .scalar()
    
    if max_number is None:
        return 1
    else:
        return max_number + 1


@router.post("/reservations/", response_model=schemas.Reservation)
def create_reservation(
    reservation: schemas.ReservationCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """患者が予約を作成するエンドポイント"""
    # スロットが存在するか確認
    slot = db.query(models.TimeSlot).filter(models.TimeSlot.id == reservation.slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    
    # スロットが有効か確認
    if not slot.is_active:
        raise HTTPException(status_code=400, detail="This time slot is not available")
    
    # 空き枠があるか確認
    if slot.available_spots <= 0:
        raise HTTPException(status_code=400, detail="No available spots in this time slot")
    
    # 同じ日に既に予約を持っているか確認
    existing_reservation = db.query(models.Reservation)\
        .join(models.TimeSlot)\
        .filter(
            models.TimeSlot.date == slot.date,
            models.Reservation.patient_id == current_user.id
        ).first()
    
    if existing_reservation:
        raise HTTPException(status_code=400, detail="You already have a reservation for this day")
    
    # QRコードデータを生成
    qr_code_data = generate_qr_code_data()
    
    # 日ごとの番号を取得
    daily_number = get_daily_number(db, slot.date)
    
    # 予約を作成
    db_reservation = models.Reservation(
        patient_id=current_user.id,
        slot_id=reservation.slot_id,
        daily_number=daily_number,
        qr_code_data=qr_code_data
    )
    
    # スロットの空き枠を更新
    slot.available_spots -= 1
    
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    
    return db_reservation


@router.get("/reservations/", response_model=List[schemas.ReservationWithDetails])
def get_my_reservations(
    include_past: bool = False,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """患者が自分の予約一覧を取得するエンドポイント"""
    query = db.query(models.Reservation)\
        .filter(models.Reservation.patient_id == current_user.id)\
        .join(models.TimeSlot)
    
    # 過去の予約を含めるかどうか
    if not include_past:
        today = datetime.now().date()
        query = query.filter(models.TimeSlot.date >= today)
    
    # 日付順にソート
    query = query.order_by(models.TimeSlot.date, models.TimeSlot.start_time)
    
    return query.all()


@router.get("/reservations/admin", response_model=List[schemas.ReservationWithDetails])
def get_all_reservations(
    date: date = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_admin_user)
):
    """管理者が全予約を取得するエンドポイント"""
    query = db.query(models.Reservation).join(models.TimeSlot)
    
    # 特定の日付でフィルタリング
    if date:
        query = query.filter(models.TimeSlot.date == date)
    
    # 日付順にソート
    query = query.order_by(models.TimeSlot.date, models.TimeSlot.start_time, models.Reservation.daily_number)
    
    return query.all()


@router.get("/reservations/{qr_code}", response_model=schemas.ReservationWithDetails)
def verify_reservation(
    qr_code: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """QRコードで予約を確認するエンドポイント"""
    # QRコードで予約を検索
    reservation = db.query(models.Reservation)\
        .filter(models.Reservation.qr_code_data == qr_code)\
        .first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return reservation


@router.put("/reservations/{qr_code}/confirm", response_model=schemas.Reservation)
def confirm_reservation(
    qr_code: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_admin_user)
):
    """管理者が予約を確認済みにするエンドポイント"""
    # QRコードで予約を検索
    reservation = db.query(models.Reservation)\
        .filter(models.Reservation.qr_code_data == qr_code)\
        .first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # 既に確認済みかチェック
    if reservation.is_confirmed:
        raise HTTPException(status_code=400, detail="Reservation already confirmed")
    
    # 確認済みにする
    reservation.is_confirmed = True
    db.commit()
    db.refresh(reservation)
    
    return reservation


@router.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """予約をキャンセルするエンドポイント"""
    # 予約を検索
    reservation = db.query(models.Reservation)\
        .filter(models.Reservation.id == reservation_id)\
        .first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # 自分の予約かどうかチェック（管理者は全ての予約をキャンセル可能）
    if reservation.patient_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this reservation")
    
    # 既に確認済みの場合はキャンセル不可
    if reservation.is_confirmed:
        raise HTTPException(status_code=400, detail="Cannot cancel a confirmed reservation")
    
    # 予約枠の利用可能数を更新
    slot = db.query(models.TimeSlot).filter(models.TimeSlot.id == reservation.slot_id).first()
    if slot:
        slot.available_spots += 1
    
    # 予約を削除
    db.delete(reservation)
    db.commit()
    
    return None